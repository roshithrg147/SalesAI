# ==========================================
# Developer: Mr. R.
# Project:   HypeMind
# ==========================================

import time
import schedule
import os
import tempfile
from datetime import datetime
from content.post_generator import draft_post
from instagram.ig_poster import upload_post
from config import setup_logger

logger = setup_logger("core.scheduler")

def run_posting_job():
    logger.info(f"[{datetime.now()}] Starting daily posting job...")
    with tempfile.TemporaryDirectory() as temp_dir:
        image_path, data = draft_post(download_dir=temp_dir)
        if data and "caption" in data:
            logger.info(f"Drafted post for S3 image (Local temp: {image_path}):")
            if data.get("close_match"):
                logger.warning("[WARNING] AI used a 'Close Match' for this product. Verify catalog accuracy.")
            logger.info(data["caption"])
            logger.info("Uploading to Instagram...")
            upload_post(image_path, data["caption"])
            # Cleanup is completely handled by the TemporaryDirectory context
        else:
            logger.error("Failed to draft post. Skipping upload.")

def start_scheduler():
    logger.info("Starting scheduler. Scheduled to post every day at 10:00 AM.")
    
    # Run once immediately so we know it works, or comment this out for strictly 10 AM
    # run_posting_job()
    
    schedule.every().day.at("10:00").do(run_posting_job)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    start_scheduler()
