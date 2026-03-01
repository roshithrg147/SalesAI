from playwright.sync_api import sync_playwright

# Initialize the Gemini Client
# Make sure you have export GOOGLE_API_KEY='your-key-here' in your terminal
# client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

def login_and_save():
    with sync_playwright() as p:
        context = p.chromium.launch_persistant_context(
            user_data_dir="./ig_session",
            headless=False
        )
        
        page = context.new_page()
        page.goto("https://www.instagram.com/accounts/login/")
        
        print("ACTION REQUIRED: Log in to Instagram in the browser window")
        print("Once you see your inbox, come back here and press Enter...")
        input()
        
        context.close()

if __name__ == "__main__":
    login_and_save()