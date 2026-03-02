import os
import time
from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=os.path.abspath("./ig_session"),
            headless=True,
            args=["--disable-notifications"]
        )
        page = context.new_page()
        page.goto("https://www.instagram.com/")
        page.wait_for_timeout(5000)
        
        print("Clicking New post")
        try:
            page.get_by_role("link", name="New post").click()
        except:
            page.locator("svg[aria-label='New post']").first.click()
            
        page.wait_for_timeout(2000)
        try:
            page.get_by_role("menuitem", name="Post").click(timeout=2000)
            page.wait_for_timeout(2000)
        except:
            pass
            
        print("Uploading file...")
        image_path = os.path.abspath("promo_video.mp4")
        
        file_input = page.locator("input[type='file']")
        print(f"File inputs found: {file_input.count()}")
        
        if file_input.count() > 0:
            print("Using set_input_files")
            file_input.first.set_input_files(image_path)
        else:
            print("Using expect_file_chooser")
            with page.expect_file_chooser() as fc_info:
                page.get_by_role("button", name="Select from computer").click()
            fc_info.value.set_files(image_path)
            
        page.wait_for_timeout(5000)
        
        # Take a screenshot to see if it advanced from the initial modal
        page.screenshot(path="test_screenshot.png")
        print("Took screenshot")
        context.close()

if __name__ == "__main__":
    test()
