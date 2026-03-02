import sys
import threading
import time
from playwright.sync_api import sync_playwright

def login_and_save():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir="./ig_session",
            headless=False
        )
        
        page = context.new_page()
        page.goto("https://www.instagram.com/accounts/login/")
        
        print("ACTION REQUIRED: Log in to Instagram in the browser window")
        print("Once you see your inbox, come back here and press Enter...")
        input()
        
        context.close()

def dm_polling_loop():
    """Mock background loop that continuously checks for new Instagram DMs."""
    print("Starting DM Polling Loop background thread...")
    while True:
        # In a real scenario, this would use Playwright to read inbox and brain.py to reply
        # print("Polling for new Instagram DMs...")
        time.sleep(300) # Poll every 5 minutes

def run_app():
    # Start the background DM polling thread
    dm_thread = threading.Thread(target=dm_polling_loop, daemon=True)
    dm_thread.start()
    
    # Start the scheduler on the main thread
    from scheduler import start_scheduler
    start_scheduler()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "login":
            login_and_save()
        elif command == "post-now":
            from scheduler import run_posting_job
            run_posting_job()
        elif command == "schedule" or command == "run":
            run_app()
        elif command == "generate-video":
            from video_generator import generate_promotional_video
            generate_promotional_video()
        elif command == "post-video":
            from ig_poster import upload_post
            caption = "Check out our latest collection! 🧥🔥 Shop now at the link in our bio. #StreetwearIndia #Fashion #NewArrivals"
            upload_post("promo_video.mp4", caption)
        elif command == "generate-ad":
            from gemini_video_ad import generate_video_ad
            from ig_poster import upload_post
            video_file = generate_video_ad("video/ad_video.mp4")
            if video_file:
                 caption = "Elevate your streetwear game. 🌟 Crisp, clean, and built for the city. Tap the link in our bio! #StreetwearIndia #Luxurystreetwear #OOTD #FreshDrops"
                 print(f"Video {video_file} complete. Automatically posting to Instagram...")
                 upload_post(video_file, caption)
            else:
                 print("Failed to generate or download the video ad.")
        else:
            print(f"Unknown command: {command}")
            print("Usage: python3 main.py [login|post-now|run|generate-video|post-video|generate-ad]")
    else:
        print("Usage: python3 main.py [login|post-now|run|generate-video|post-video|generate-ad]")
        print("Running login by default...")
        login_and_save()