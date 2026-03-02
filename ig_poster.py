import os
import time
from playwright.sync_api import sync_playwright

def upload_post(image_path, caption):
    with sync_playwright() as p:
        # Launch with existing session, preferring system chrome for H.264 codec support
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir="./ig_session",
                headless=False,
                channel="chrome",
                args=[
                    "--disable-notifications", 
                    "--disable-gpu", 
                    "--disable-dev-shm-usage", 
                    "--disable-software-rasterizer"
                ]
            )
        except Exception as e:
            print(f"Warning: Could not launch system Chrome ({e}). Trying fallback to Playwright Chromium...")
            context = p.chromium.launch_persistent_context(
                user_data_dir="./ig_session",
                headless=False,
                args=["--disable-notifications"]
            )
        
        page = context.new_page()
        page.goto("https://www.instagram.com/")
        page.wait_for_timeout(5000) # Wait for feed to load
        
        print(f"Starting post process for {image_path}...")
        
        try:
            # 1. Click "New post" (Create)
            try:
                page.get_by_role("link", name="New post").click()
            except:
                # Fallback to general svg if role fails
                page.locator("svg[aria-label='New post']").first.click()
            
            page.wait_for_timeout(2000)
            
            # Instagram sometimes shows a menu (Post, Story, Reel, Live). 
            # If so, click "Post". We try this, but ignore if not present.
            try:
                page.get_by_role("menuitem", name="Post").click(timeout=2000)
                page.wait_for_timeout(2000)
            except:
                pass
            
            print(f"Resolving absolute path for {image_path}")
            abs_image_path = os.path.abspath(image_path)
            if not os.path.exists(abs_image_path):
                raise FileNotFoundError(f"File not found: {abs_image_path}")

            # 2. Upload file
            file_input = page.locator("input[type='file']")
            if file_input.count() > 0:
                print("Using direct input file upload.")
                file_input.first.set_input_files(abs_image_path)
            else:
                print("Using expect_file_chooser upload.")
                with page.expect_file_chooser() as fc_info:
                    # Try clicking "Select from computer"
                    page.get_by_role("button", name="Select from computer").click()
                file_chooser = fc_info.value
                file_chooser.set_files(abs_image_path)
                
            page.wait_for_timeout(4000)
            
            # Check for video reels popup: "Video posts are now shared as Reels."
            try:
                ok_btn = page.get_by_role("button", name="OK", exact=True)
                if ok_btn.count() > 0 and ok_btn.first.is_visible():
                    print("Dismissing Video to Reels OK popup.")
                    ok_btn.first.click()
                    page.wait_for_timeout(2000)
            except Exception as e:
                pass

            
            # 3. Click "Next" (Crop screen)
            page.get_by_role("button", name="Next").click()
            page.wait_for_timeout(2000)
            
            # 4. Click "Next" (Filter screen)
            page.get_by_role("button", name="Next").click()
            page.wait_for_timeout(2000)
            
            # 5. Type caption
            # Often it's a contenteditable div with aria-label="Write a caption..."
            caption_input = page.locator("div[aria-label='Write a caption...']")
            if caption_input.count() > 0:
                caption_input.fill(caption)
            else:
                page.get_by_placeholder("Write a caption...").fill(caption)
                
            page.wait_for_timeout(1000)
            
            # 6. Click "Share"
            page.get_by_role("button", name="Share", exact=True).click()
            
            # Wait for success message
            print("Waiting for post to upload...")
            page.get_by_text("Your post has been shared.").wait_for(timeout=50000)
            print("Post shared successfully!")
            
        except Exception as e:
            print(f"Error during Instagram automation: {e}")
            page.screenshot(path="error_screenshot.png")
            print("Screenshot saved to error_screenshot.png for debugging.")
            
        finally:
            # Brief pause so user can see completion if they are watching
            page.wait_for_timeout(3000)
            context.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        upload_post(sys.argv[1], " ".join(sys.argv[2:]))
    else:
        print("Usage: python3 ig_poster.py <path_to_image> <caption_text>")
