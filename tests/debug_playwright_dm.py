import os
import sys
import time
from playwright.sync_api import sync_playwright
from config import Config, setup_logger

logger = setup_logger("test_dm_scraper")

def safe_click(page, locator, timeout=3000, retries=2):
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
                logger.warning(f"Failed to click {locator}: {e}")
    return False

def run_test():
    with sync_playwright() as p:
        try:
            logger.info("Launching Chrome...")
            context = p.chromium.launch_persistent_context(
                user_data_dir=Config.IG_SESSION_DIR,
                executable_path=Config.PLAYWRIGHT_EXEC_PATH,
                headless=Config.PLAYWRIGHT_HEADLESS,
                args=["--disable-notifications", "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--single-process"]
            )
            page = context.new_page()
            page.set_default_timeout(15000)
            
            logger.info("Navigating to Inbox...")
            page.goto("https://www.instagram.com/direct/inbox/")
            page.wait_for_load_state("domcontentloaded")
            
            # Wait for any potential "Not Now" modals
            try:
                not_now = page.locator("text=/Not Now|Not now/i").first
                if safe_click(page, not_now, timeout=6000):
                    logger.info("Dismissed Not Now")
                    page.wait_for_timeout(3000)
            except Exception as e:
                pass
                
            logger.info("Waiting for inbox layout to stabilize (10 seconds)...")
            page.wait_for_timeout(10000)
            
            logger.info("--- DOM DIAGNOSTICS ---")
            
            # 1. Analyze SVGs
            svgs = page.locator("svg").all()
            labels = []
            for svg in svgs:
                label = svg.get_attribute("aria-label")
                if label:
                    labels.append(label)
            logger.info(f"SVG Aria-Labels present on page: {set(labels)}")
            
            # 2. Analyze Roles
            roles = ["navigation", "main", "tablist", "list"]
            for role in roles:
                count = page.locator(f"[role='{role}']").count()
                logger.info(f"Elements with role='{role}': {count}")
                
            # 3. Analyze Threads
            # 2. Search for the thread structure using the exact classes discovered
            thread_class_str = ".html-div.xdj266r.x14z9mp.xat24cr.x1lziwak.xexx8yu.xyri2b.x18d9i69.x1c1uobl.x9f619.xjbqb8w.x78zum5.x15mokao.x1ga7v0g.x16uus16.xbiv7yw.x1uhb9sk.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.xdt5ytf.xqjyukv.x1qjc9v5.x1oa3qoh.x1nhvcw1"
            threads_class = page.locator(f"div{thread_class_str}")
            logger.info(f"Threads found using class selector: {threads_class.count()}")
            
            # 3. Search for thread structure using role='button'
            threads_button = page.locator("div[role='button']").filter(has=page.locator("span[title]"))
            thread_count = threads_button.count()
            logger.info(f"Threads found using div[role='button']:has(span[title]) selector: {thread_count}")
            
            for i in range(min(thread_count, 5)):
                text = threads_button.nth(i).inner_text().replace('\n', ' | ')
                unread_count = threads_button.nth(i).locator("text='Unread'").count()
                unread_dot = threads_button.nth(i).locator("xpath=.//*[contains(@aria-label, 'Unread') or contains(@class, 'x1i10hfl')]").count()
                logger.info(f"  Thread {i}: '{text}' (Has 'Unread' text: {unread_count > 0}, Has Unread aria-label: {unread_dot > 0})")
            
            thread_links_a = page.locator("a[href^='/direct/t/']").count()
            logger.info(f"Thread links matching a[href^='/direct/t/']: {thread_links_a}")
            
            thread_links_div = page.locator("div[role='listitem']").count()
            logger.info(f"Thread links matching div[role='listitem']: {thread_links_div}")
            
            logger.info("-----------------------")
            logger.info("Test complete. Please review the output above to determine the best selectors.")
            
        except Exception as e:
            logger.error(f"Test failed with error: {e}")
        finally:
            if 'context' in locals():
                context.close()

if __name__ == "__main__":
    run_test()
