# ==========================================
# Developer: Mr. R.
# Project:   HypeMind
# ==========================================

import sys
import threading
import time
import os
import shutil
import zipfile
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from playwright.sync_api import sync_playwright

from config import Config, logger

def acquire_lock(lock_name: str, timeout_seconds: int = 600) -> bool:
    """
    Implements a distributed lock using DynamoDB conditional writes to prevent concurrent execution.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(Config.LOCKS_TABLE)
    now = int(time.time())
    expires_at = now + timeout_seconds

    try:
        table.put_item(
            Item={
                'id': lock_name,
                'expires_at': expires_at
            },
            ConditionExpression='attribute_not_exists(id) OR expires_at < :now',
            ExpressionAttributeValues={':now': now}
        )
        logger.info(f"Lock '{lock_name}' acquired successfully.")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.warning(f"Lock '{lock_name}' is currently held by another worker.")
            return False
        logger.error(f"Error acquiring lock '{lock_name}': {e}")
        raise

def release_lock(lock_name: str) -> None:
    """Releases the distributed lock."""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(Config.LOCKS_TABLE)
    try:
        table.delete_item(Key={'id': lock_name})
        logger.info(f"Lock '{lock_name}' released successfully.")
    except Exception as e:
        logger.error(f"Error releasing lock '{lock_name}': {e}")

def sync_session_from_s3() -> None:
    """Download and extract the session folder from S3 if it exists."""
    s3_client = boto3.client('s3')
    zip_path = "/tmp/ig_session.zip"
    
    try:
        logger.info(f"Attempting to sync session from S3 ({Config.S3_BUCKET}/ig_session.zip)...")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                s3_client.download_file(Config.S3_BUCKET, 'ig_session.zip', zip_path)
                break
            except (ClientError, BotoCoreError) as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"S3 download failed (attempt {attempt+1}/{max_retries}): {e}. Retrying...")
                time.sleep(2 ** attempt)
        
        # Ensure target dir exists and is clear from previous runs
        if os.path.exists(Config.IG_SESSION_DIR):
            shutil.rmtree(Config.IG_SESSION_DIR)
        os.makedirs(Config.IG_SESSION_DIR, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(Config.IG_SESSION_DIR)
            
        logger.info(f"Session extracted successfully to {Config.IG_SESSION_DIR}")
        os.remove(zip_path)
    except Exception as e:
        logger.warning(f"Could not load session from S3 (Expected on first run or if file missing): {e}")

def sync_session_to_s3() -> None:
    """Zip up the session folder and push it to AWS S3 to persist the cookies."""
    if not os.path.exists(Config.IG_SESSION_DIR):
        logger.error(f"Cannot save session to S3; {Config.IG_SESSION_DIR} does not exist.")
        return
        
    s3_client = boto3.client('s3')
    zip_path = "/tmp/ig_session_upload" # shutil.make_archive adds .zip automatically
    
    try:
        logger.info("Zipping current session folder...")
        shutil.make_archive(zip_path, 'zip', Config.IG_SESSION_DIR)
        
        logger.info(f"Uploading session to S3 ({Config.S3_BUCKET}/ig_session.zip)...")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                s3_client.upload_file(f"{zip_path}.zip", Config.S3_BUCKET, "ig_session.zip")
                break
            except (ClientError, BotoCoreError) as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"S3 upload failed (attempt {attempt+1}/{max_retries}): {e}. Retrying...")
                time.sleep(2 ** attempt)
        logger.info("Session state pushed to S3 successfully.")
        
        # Cleanup
        os.remove(f"{zip_path}.zip")
    except Exception as e:
        logger.error(f"Failed to sync session to S3: {e}")

def scrape_dms() -> None:
    """Executes the DM scraping flow, protected by a distributed lock."""
    lock_name = "dm_scraper_lock"
    if not acquire_lock(lock_name, timeout_seconds=300):
        logger.info("DM Scraper already running in another instance. Exiting.")
        return
        
    try:
        sync_session_from_s3()
        # Import inside function to avoid circular dependencies
        from instagram.dm_scraper import run_dm_scraper
        run_dm_scraper()
    finally:
        sync_session_to_s3()
        release_lock(lock_name)

def post_scheduled_content() -> None:
    """Executes the content posting flow, protected by a distributed lock."""
    lock_name = "scheduled_poster_lock"
    if not acquire_lock(lock_name, timeout_seconds=600):
        logger.info("Scheduled poster already running in another instance. Exiting.")
        return
        
    try:
        sync_session_from_s3()
        from core.scheduler import run_posting_job
        run_posting_job()
    finally:
        sync_session_to_s3()
        release_lock(lock_name)

def lambda_handler(event, context) -> dict:
    """
    AWS Lambda entry point. Standardized for event-driven execution.
    """
    logger.info(f"Received Lambda event: {event}")
    action = event.get('action')

    if action == 'scrape_dms':
        scrape_dms()
        return {"statusCode": 200, "body": "DM scraping successful"}
    elif action == 'post_scheduled':
        post_scheduled_content()
        return {"statusCode": 200, "body": "Scheduled posting successful"}
    else:
        logger.error(f"Unknown or missing action in event: {action}")
        return {"statusCode": 400, "body": "Unknown action"}


def login_and_save() -> None:
    """CLI tool for local authentication and session setup."""
    logger.info("Starting login session builder...")
    sync_session_from_s3()
    
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=Config.IG_SESSION_DIR,
            headless=False
        )
        
        page = context.new_page()
        page.goto("https://www.instagram.com/accounts/login/")
        
        logger.info("ACTION REQUIRED: Log in to Instagram in the browser window")
        logger.info("Once you see your inbox, come back here and press Enter...")
        input()
        
        context.close()
        logger.info("Login session saved successfully locally.")
        
    sync_session_to_s3()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        logger.info(f"Executing command: {command}")
        
        if command == "login":
            login_and_save()
        elif command == "scrape-dms":
            scrape_dms()
        elif command == "post-now":
            post_scheduled_content()
        elif command == "generate-video":
            from content.video_generator import generate_promotional_video
            generate_promotional_video()
        elif command == "post-video":
            sync_session_from_s3()
            from instagram.ig_poster import upload_post
            caption = "Check out our latest collection! 🧥🔥 Shop now at the link in our bio. #StreetwearIndia #Fashion #NewArrivals"
            upload_post("promo_video.mp4", caption)
            if os.path.exists("promo_video.mp4"):
                os.remove("promo_video.mp4")
                logger.info("Cleaned up promo_video.mp4")
            sync_session_to_s3()
        elif command == "generate-ad":
            sync_session_from_s3()
            from content.gemini_video_ad import generate_video_ad
            from instagram.ig_poster import upload_post
            video_file = generate_video_ad("video/ad_video.mp4")
            if video_file:
                 caption = "Elevate your streetwear game. 🌟 Crisp, clean, and built for the city. Tap the link in our bio! #StreetwearIndia #Luxurystreetwear #OOTD #FreshDrops"
                 logger.info(f"Video {video_file} complete. Automatically posting to Instagram...")
                 upload_post(video_file, caption)
                 if os.path.exists(video_file):
                     os.remove(video_file)
                     logger.info(f"Cleaned up {video_file}")
            sync_session_to_s3()
        else:
            logger.error(f"Unknown command: {command}")
            logger.info("Usage: python3 main.py [login|scrape-dms|post-now|generate-video|post-video|generate-ad]")
    else:
        logger.info("Usage: python3 main.py [login|scrape-dms|post-now|generate-video|post-video|generate-ad]")