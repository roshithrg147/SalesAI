import json
import boto3
from botocore.exceptions import ClientError
from config import Config, setup_logger

logger = setup_logger("core.state_manager")

STATE_FILE_KEY = "posting_state.json"

def get_posting_state() -> dict:
    """
    Downloads and parses the posting state JSON from S3.
    Returns a dict with 'used_images_posts' and 'used_images_videos'.
    If it doesn't exist, returns default state.
    """
    s3_client = boto3.client('s3')
    bucket_name = Config.S3_BUCKET
    
    default_state = {
        "used_images_posts": [],
        "used_images_videos": []
    }
    
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=STATE_FILE_KEY)
        state_data = response['Body'].read().decode('utf-8')
        state = json.loads(state_data)
        
        # Ensure keys exist
        if "used_images_posts" not in state:
            state["used_images_posts"] = []
        if "used_images_videos" not in state:
            state["used_images_videos"] = []
            
        return state
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.info("Posting state file not found in S3. Starting fresh.")
        else:
            logger.warning(f"Error retrieving posting state: {e}. Using default.")
        return default_state
    except Exception as e:
        logger.error(f"Unexpected error loading state: {e}")
        return default_state

def save_posting_state(state: dict) -> bool:
    """
    Uploads the updated posting state JSON to S3.
    """
    s3_client = boto3.client('s3')
    bucket_name = Config.S3_BUCKET
    
    try:
        state_data = json.dumps(state, indent=4)
        s3_client.put_object(
            Bucket=bucket_name, 
            Key=STATE_FILE_KEY, 
            Body=state_data.encode('utf-8'),
            ContentType='application/json'
        )
        logger.info("Successfully updated posting state in S3.")
        return True
    except Exception as e:
        logger.error(f"Failed to save posting state to S3: {e}")
        return False
