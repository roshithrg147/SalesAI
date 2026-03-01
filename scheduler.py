import time
import schedule
import os
from datetime import datetime
from post_generator import draft_post
from ig_poster import upload_post

def run_posting_job():
    print(f"[{datetime.now()}] Starting daily posting job...")
    image_path, data = draft_post()
    if data and "caption" in data:
        print(f"\nDrafted post for {image_path}:")
        print(data["caption"])
        print("\nUploading to Instagram...")
        upload_post(image_path, data["caption"])
    else:
        print("Failed to draft post. Skipping upload.")

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
