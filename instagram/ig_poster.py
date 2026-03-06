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

SELECTORS = {
    "INBOX_NAV": "svg[aria-label='Direct'], svg[aria-label='Messages'], svg[aria-label='Messenger'], section[role='main']",
    "NEW_POST_LINK": "New post|Create",
    "NEW_POST_SVG": "svg[aria-label='New post'], svg[aria-label='Create']",
    "DIALOG": "div[role='dialog']",
    "POST_MENU": "Post",
    "FILE_INPUT": "input[type='file']",
    "SELECT_FILE_BTN": "Select from computer|Select files",
    "NEXT_BTN": "Next",
    "OK_BTN": "OK",
    "CAPTION_INPUT": "div[aria-label='Write a caption...']",
    "CAPTION_PLACEHOLDER": "Write a caption...",
    "SHARE_BTN": "Share",
    "SUCCESS_MSG": "Your post has been shared.|Your reel has been shared."
}

def safe_click(page, locator, timeout=3000, retries=2, optional=False):
    for attempt in range(retries):
        try:
            if isinstance(locator, str):
                el = page.locator(locator).first
            else:
                el = locator.first
            el.wait_for(state="visible", timeout=timeout)
            el.click()
            return True
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                if not optional:
                    logger.warning(f"Failed to click {locator}: {e}")
    return False

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
            
            # Wait for DOM to parse and specific Inbox icon to load
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_selector(SELECTORS["INBOX_NAV"], state="visible", timeout=15000) 
            
            logger.info(f"Starting post process for {image_path}...")
            
            # 1. Click "New post" (Create)
            if not safe_click(page, page.get_by_role("link", name=re.compile(SELECTORS["NEW_POST_LINK"], re.IGNORECASE))):
                logger.info("Fallback: clicking SVG icon for New Post.")
                safe_click(page, SELECTORS["NEW_POST_SVG"])
            
            # Wait for modal to appear
            page.wait_for_selector(SELECTORS["DIALOG"], state="visible")
            
            # Instagram sometimes shows a menu (Post, Story, Reel, Live) before the modal
            post_menu = page.get_by_role("menuitem", name=SELECTORS["POST_MENU"])
            safe_click(page, post_menu, optional=True, retries=1)
            
            logger.info(f"Resolving absolute path for {image_path}")
            abs_image_path = os.path.abspath(image_path)
            if not os.path.exists(abs_image_path):
                raise FileNotFoundError(f"File not found: {abs_image_path}")

            # 2. Upload file
            file_input = page.locator(SELECTORS["FILE_INPUT"])
            if file_input.count() > 0:
                logger.info("Using direct input file upload.")
                file_input.first.set_input_files(abs_image_path)
            else:
                logger.info("Using expect_file_chooser upload.")
                with page.expect_file_chooser() as fc_info:
                    safe_click(page, page.get_by_role("button", name=re.compile(SELECTORS["SELECT_FILE_BTN"], re.IGNORECASE)))
                file_chooser = fc_info.value
                file_chooser.set_files(abs_image_path)
                
            # Wait until image preview renders in the modal (Next button appears)
            page.get_by_role("button", name=SELECTORS["NEXT_BTN"]).wait_for(state="visible", timeout=90000)
            
            # Check for video reels popup: "Video posts are now shared as Reels."
            ok_btn = page.get_by_role("button", name=SELECTORS["OK_BTN"], exact=True)
            safe_click(page, ok_btn, timeout=2000, optional=True, retries=1)
            
            # 3. Click "Next" (Crop screen)
            next_btn = page.get_by_role("button", name=SELECTORS["NEXT_BTN"])
            safe_click(page, next_btn)
            
            # Wait for filter screen to load and Next to be interactable again
            page.get_by_role("button", name=SELECTORS["NEXT_BTN"]).wait_for(state="visible", timeout=90000)
            
            # 4. Click "Next" (Filter screen)
            safe_click(page, page.get_by_role("button", name=SELECTORS["NEXT_BTN"]))
            
            # Wait for the caption input area to exist
            caption_input = page.locator(SELECTORS["CAPTION_INPUT"])
            caption_placeholder = page.get_by_placeholder(SELECTORS["CAPTION_PLACEHOLDER"])
            
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
            safe_click(page, page.get_by_role("button", name=SELECTORS["SHARE_BTN"], exact=True))
            
            # Wait for success message
            logger.info("Waiting for post to upload to Instagram servers...")
            page.get_by_text(re.compile(SELECTORS["SUCCESS_MSG"], re.IGNORECASE)).wait_for(state="visible", timeout=60000)
            logger.info("Post shared successfully!")
            
        except Exception as e:
            logger.error(f"Error during Instagram automation flow: {e}", exc_info=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"failure_ig_poster_{timestamp}.png"
            # Fallback screenshot handler
            if 'page' in locals():
                page.screenshot(path=screenshot_path, full_page=True)
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
