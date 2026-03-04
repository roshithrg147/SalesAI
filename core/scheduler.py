# ==========================================
# Developer: Mr. R.
# Project:   HypeMind
# ==========================================

import time
import schedule
import os
from datetime import datetime
from content.post_generator import draft_post
from instagram.ig_poster import upload_post

def run_posting_job():
    print(f"[{datetime.now()}] Starting daily posting job...")
    image_path, data = draft_post()
    if data and "caption" in data:
        print(f"\nDrafted post for S3 image (Local temp: {image_path}):")
        if data.get("close_match"):
            print("[WARNING] AI used a 'Close Match' for this product. Verify catalog accuracy.")
        print(data["caption"])
        print("\nUploading to Instagram...")
        upload_post(image_path, data["caption"])
        
        # Cleanup temporary file after successful upload
        try:
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
                print(f"Cleaned up temporary image: {image_path}")
        except Exception as e:
            print(f"Failed to clean up {image_path}: {e}")
    else:
        print("Failed to draft post. Skipping upload.")
        if image_path and os.path.exists(image_path):
             os.remove(image_path)

def start_scheduler():
    print("Starting scheduler. Scheduled to post every day at 10:00 AM.")
    
    # Run once immediately so we know it works, or comment this out for strictly 10 AM
    # run_posting_job()
    
    schedule.every().day.at("10:00").do(run_posting_job)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    start_scheduler()
