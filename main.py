# ==========================================
# Developer: Mr. R.
# Project:   HypeMind
# ==========================================

import sys
import threading
import time
from playwright.sync_api import sync_playwright

from config import Config, logger

def login_and_save():
    logger.info("Starting login session builder...")
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
        logger.info("Login session saved successfully.")

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
            from core.scheduler import run_posting_job
            run_posting_job()
        elif command == "schedule" or command == "run":
            run_app()
        elif command == "generate-video":
            from content.video_generator import generate_promotional_video
            generate_promotional_video()
        elif command == "post-video":
            import os
            from instagram.ig_poster import upload_post
            caption = "Check out our latest collection! 🧥🔥 Shop now at the link in our bio. #StreetwearIndia #Fashion #NewArrivals"
            upload_post("promo_video.mp4", caption)
            if os.path.exists("promo_video.mp4"):
                os.remove("promo_video.mp4")
                logger.info("Cleaned up promo_video.mp4")
        elif command == "generate-ad":
            import os
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
        else:
            logger.error(f"Unknown command: {command}")
            print("Usage: python3 main.py [login|post-now|run|generate-video|post-video|generate-ad]")
    else:
        print("Usage: python3 main.py [login|post-now|run|generate-video|post-video|generate-ad]")
        print("Running login by default...")
        login_and_save()