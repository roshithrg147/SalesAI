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
        else:
            print(f"Unknown command: {command}")
            print("Usage: python3 main.py [login|post-now|run]")
    else:
        print("Usage: python3 main.py [login|post-now|run]")
        print("Running login by default...")
        login_and_save()