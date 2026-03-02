# ==========================================
# Developer: Mr. R.
# Project:   HypeMind
# ==========================================

import os
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

from config import Config, setup_logger

logger = setup_logger("instagram.ig_poster")

def upload_post(image_path, caption):
    with sync_playwright() as p:
        try:
            # We use standard bundled Chromium now instead of host Chrome per CTO audit
            context = p.chromium.launch_persistent_context(
                user_data_dir=Config.IG_SESSION_DIR,
                headless=Config.PLAYWRIGHT_HEADLESS,
                args=["--disable-notifications"]
            )
            page = context.new_page()
            
            # Set default explicit timeout for all page operations
            page.set_default_timeout(Config.PLAYWRIGHT_TIMEOUT)

            logger.info("Opening Instagram...")
            page.goto("https://www.instagram.com/")
            
            # Use explicit selectors instead of random sleep
            page.wait_for_selector("nav", state="visible") 
            
            logger.info(f"Starting post process for {image_path}...")
            
            # 1. Click "New post" (Create)
            try:
                page.get_by_role("link", name=re.compile(r"New post|Create", re.IGNORECASE)).click()
            except:
                page.locator("svg[aria-label='New post'], svg[aria-label='Create']").first.click()
            
            # Wait for modal to appear
            page.wait_for_selector("div[role='dialog']", state="visible")
            
            # Instagram sometimes shows a menu (Post, Story, Reel, Live) before the modal
            try:
                post_menu = page.get_by_role("menuitem", name="Post")
                if post_menu.count() > 0 and post_menu.is_visible(timeout=3000):
                    post_menu.click()
            except:
                pass
            
            logger.info(f"Resolving absolute path for {image_path}")
            abs_image_path = os.path.abspath(image_path)
            if not os.path.exists(abs_image_path):
                raise FileNotFoundError(f"File not found: {abs_image_path}")

            # 2. Upload file
            file_input = page.locator("input[type='file']")
            if file_input.count() > 0:
                logger.info("Using direct input file upload.")
                file_input.first.set_input_files(abs_image_path)
            else:
                logger.info("Using expect_file_chooser upload.")
                with page.expect_file_chooser() as fc_info:
                    page.get_by_role("button", name=re.compile(r"Select from computer|Select files", re.IGNORECASE)).click()
                file_chooser = fc_info.value
                file_chooser.set_files(abs_image_path)
                
            # Wait until image preview renders in the modal (Next button appears)
            page.get_by_role("button", name="Next").wait_for(state="visible")
            
            # Check for video reels popup: "Video posts are now shared as Reels."
            try:
                ok_btn = page.get_by_role("button", name="OK", exact=True)
                if ok_btn.count() > 0 and ok_btn.first.is_visible(timeout=2000):
                    logger.info("Dismissing Video to Reels OK popup.")
                    ok_btn.first.click()
            except Exception:
                pass

            
            # 3. Click "Next" (Crop screen)
            next_btn = page.get_by_role("button", name="Next")
            next_btn.click()
            
            # Wait for filter screen to load and Next to be interactable again
            # We can check a UI indicator of the filter screen, or just wait for network idle
            page.wait_for_load_state("networkidle")
            
            # 4. Click "Next" (Filter screen)
            page.get_by_role("button", name="Next").click()
            
            # Wait for the caption input area to exist
            caption_input = page.locator("div[aria-label='Write a caption...']")
            caption_placeholder = page.get_by_placeholder("Write a caption...")
            
            try:
                caption_input.wait_for(state="visible", timeout=5000)
                caption_target = caption_input
            except:
                caption_placeholder.wait_for(state="visible", timeout=5000)
                caption_target = caption_placeholder

            # 5. Type caption
            caption_target.fill(caption)
            logger.info("Caption inserted.")
            
            # 6. Click "Share"
            page.get_by_role("button", name="Share", exact=True).click()
            
            # Wait for success message
            logger.info("Waiting for post to upload to Instagram servers...")
            page.get_by_text("Your post has been shared.").wait_for(state="visible", timeout=60000)
            logger.info("Post shared successfully!")
            
        except Exception as e:
            logger.error(f"Error during Instagram automation flow: {e}", exc_info=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"failure_ig_poster_{timestamp}.png"
            # Fallback screenshot handler
            if 'page' in locals():
                page.screenshot(path=screenshot_path)
                logger.error(f"UI state saved to {screenshot_path} for debugging.")
        finally:
            if 'context' in locals():
                context.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        upload_post(sys.argv[1], " ".join(sys.argv[2:]))
    else:
        logger.error("Usage: python3 ig_poster.py <path_to_image> <caption_text>")
