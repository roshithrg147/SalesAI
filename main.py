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
from playwright.sync_api import sync_playwright

from config import Config, logger

def sync_session_from_s3():
    """Download and extract the session folder from S3 if it exists."""
    s3_client = boto3.client('s3')
    zip_path = "/tmp/ig_session.zip"
    
    try:
        logger.info(f"Attempting to sync session from S3 ({Config.S3_BUCKET}/ig_session.zip)...")
        s3_client.download_file(Config.S3_BUCKET, 'ig_session.zip', zip_path)
        
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

def sync_session_to_s3():
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
        s3_client.upload_file(f"{zip_path}.zip", Config.S3_BUCKET, "ig_session.zip")
        logger.info("Session state pushed to S3 successfully.")
        
        # Cleanup
        os.remove(f"{zip_path}.zip")
    except Exception as e:
        logger.error(f"Failed to sync session to S3: {e}")

def login_and_save():
    logger.info("Starting login session builder...")
    # Standardize sync
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
        
    # Standardize sync output
    sync_session_to_s3()

def dm_polling_loop():
    """Background loop that continuously checks for new Instagram DMs."""
    logger.info("Starting DM Polling Loop background thread...")
    
    # Import here to avoid circular dependencies
    from instagram.dm_scraper import run_dm_scraper
    
    while True:
        try:
            logger.info("Polling for new Instagram DMs...")
            run_dm_scraper()
        except Exception as e:
            logger.error(f"Error in DM polling loop: {e}", exc_info=True)
            
        time.sleep(Config.POLL_INTERVAL_SECONDS)

def run_app():
    logger.info("Pulling latest state from S3 before launching runners...")
    sync_session_from_s3()

    # Start the background DM polling thread
    dm_thread = threading.Thread(target=dm_polling_loop, daemon=True)
    dm_thread.start()
    
    # Start the scheduler on the main thread
    from core.scheduler import start_scheduler
    start_scheduler()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        logger.info(f"Executing command: {command}")
        
        if command == "login":
            login_and_save()
        elif command == "post-now":
            sync_session_from_s3()
            from core.scheduler import run_posting_job
            run_posting_job()
            sync_session_to_s3()
        elif command == "schedule" or command == "run":
            run_app()
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
            else:
                 logger.error("Failed to generate or download the video ad.")
            sync_session_to_s3()
        else:
            logger.error(f"Unknown command: {command}")
            print("Usage: python3 main.py [login|post-now|run|generate-video|post-video|generate-ad]")
    else:
        print("Usage: python3 main.py [login|post-now|run|generate-video|post-video|generate-ad]")
        print("Running login by default...")
        login_and_save()