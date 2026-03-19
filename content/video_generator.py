# ==========================================
# Developer: Mr. R.
# Project:   HypeMind
# ==========================================

import os
import random
from moviepy import ImageSequenceClip
from db.database import get_product_context

import tempfile
import uuid
import time
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from config import Config, setup_logger
from core.state_manager import get_posting_state, save_posting_state

logger = setup_logger("content.video_generator")

def get_valid_images_from_s3(required_count=15, download_dir=None):
    bucket_name = Config.S3_BUCKET
    s3_client = boto3.client('s3')
    
    try:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = s3_client.list_objects_v2(Bucket=bucket_name)
                break
            except (ClientError, BotoCoreError) as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"S3 list_objects_v2 failed (attempt {attempt+1}/{max_retries}): {e}. Retrying...")
                time.sleep(2 ** attempt)
                
        if 'Contents' not in response:
            logger.error(f"S3 Bucket {bucket_name} is empty or inaccessible.")
            return []
            
        all_files = [obj['Key'] for obj in response['Contents']]
    except Exception as e:
        logger.error(f"Failed to list objects in S3 bucket {bucket_name}: {e}")
        return []

    # Filter for jpegs and exclude duplicates
    unique_files = [f for f in all_files if f.endswith(".jpg") and "(" not in f]
    
    if not unique_files:
        logger.warning(f"No valid images found in S3 bucket {bucket_name}")
        return []
    
    temp_dir = download_dir if download_dir else tempfile.gettempdir()
    os.makedirs(temp_dir, exist_ok=True)
    
    # Implement tracking to avoid repeats for video generation
    state = get_posting_state()
    used_images = state.get("used_images_videos", [])
    
    available_files = [f for f in unique_files if f not in used_images]
    
    selected_keys = []
    
    while len(selected_keys) < required_count:
        if not available_files:
            logger.info("All images have been used for videos! Resetting the tracked list.")
            state["used_images_videos"] = []
            available_files = [f for f in unique_files if f not in selected_keys]
            if not available_files:
                break # No unique files at all
                
        img = random.choice(available_files)
        selected_keys.append(img)
        available_files.remove(img)
        
    # Mark as used and save state
    state.setdefault("used_images_videos", []).extend(selected_keys)
    save_posting_state(state)
    downloaded_paths = []
    
    for key in selected_keys:
        temp_img_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{os.path.basename(key)}")
        try:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    s3_client.download_file(bucket_name, key, temp_img_path)
                    break
                except (ClientError, BotoCoreError) as e:
                    if attempt == max_retries - 1:
                        raise e
                    logger.warning(f"S3 download failed (attempt {attempt+1}/{max_retries}): {e}. Retrying...")
                    time.sleep(2 ** attempt)
            downloaded_paths.append(temp_img_path)
        except Exception as e:
            logger.error(f"Failed to download {key} from S3: {e}")
            
    return downloaded_paths

def generate_promotional_video(output_filename="promo_video.mp4", duration=30):
    logger.info(f"Starting video generation. Target duration: {duration}s")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        time_per_image = 2
        required_images = duration // time_per_image
        
        image_paths = get_valid_images_from_s3(required_count=required_images, download_dir=temp_dir)
        
        if not image_paths:
            logger.warning("No valid images found to generate a video.")
            return
        
        # Randomize images to make it dynamic
        random.shuffle(image_paths)
        
        # Determine how many images we need. Let's showcase each image for 2 seconds.
        time_per_image = 2
        required_images = duration // time_per_image
        
        # If we have less images than required, we'll loop them
        selected_images = []
        while len(selected_images) < required_images:
            selected_images.extend(image_paths)
        
        # Trim to exact required number of images
        selected_images = selected_images[:required_images]
        
        logger.info(f"Selected {len(selected_images)} images for the video.")
        
        # Load all images using PIL, resize them to 1080x1080 to ensure uniform size as required by MoviePy
        import numpy as np
        from PIL import Image

        logger.info("Resizing images to uniform size (1080x1080)...")
        target_size = (1080, 1080)
        image_arrays = []
        
        for img_path in selected_images:
            try:
                with Image.open(img_path) as img:
                    # Convert to RGB to avoid issues with RGBA/grayscale
                    img = img.convert("RGB")
                    # Resize image
                    img_resized = img.resize(target_size, Image.Resampling.LANCZOS)
                    image_arrays.append(np.array(img_resized))
            except Exception as e:
                logger.error(f"Error processing {img_path}: {e}")

        if not image_arrays:
            logger.error("No valid images could be processed.")
            return

        fps = 1 / time_per_image
        clip = ImageSequenceClip(image_arrays, fps=fps)
        
        # Save the result to a file
        logger.info(f"Exporting video to {output_filename}...")
        try:
            clip.write_videofile(
                output_filename, 
                fps=24, 
                codec="libx264", 
                audio=False,
                ffmpeg_params=['-pix_fmt', 'yuv420p']
            )
            logger.info("Video generation complete!")
        except Exception as e:
             logger.error(f"Failed to generate video: {e}")
        # The finally block is handled implicitly by `with TemporaryDirectory()` when the context exits.
        # This guarantees 100% ephemeral space cleanup even during unhandled exceptions.

if __name__ == "__main__":
    generate_promotional_video()
