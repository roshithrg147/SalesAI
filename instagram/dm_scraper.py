# ==========================================
# Developer: Mr. R.
# Project:   HypeMind
# ==========================================

import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

from config import Config, setup_logger
from ai.brain import process_message

logger = setup_logger("instagram.dm_scraper")

def run_dm_scraper():
    """
    Playwright scraper that logs into the Instagram Direct Inbox, reads the 
    top unread messages, sends them to SalesAI, and replies if an intent is found.
    """
    with sync_playwright() as p:
        try:
            logger.info("Launching Playwright for DM Scraper...")
            context = p.chromium.launch_persistent_context(
                user_data_dir=Config.IG_SESSION_DIR,
                headless=Config.PLAYWRIGHT_HEADLESS,
                args=["--disable-notifications"]
            )
            page = context.new_page()
            page.set_default_timeout(Config.PLAYWRIGHT_TIMEOUT)

            logger.info("Navigating to Instagram Direct Inbox...")
            page.goto("https://www.instagram.com/direct/inbox/")
            
            # Wait for inbox container to load
            page.wait_for_selector("div[role='main']", state="visible")
            
            # Find any unread message threads.
            # Instagram often denotes unread status via specific ARIA attributes or blue dot indicators.
            # NOTE: We look for elements containing "Unread" in their aria-label or specific span classes.
            # This is a generic robust selector looking for links in the inbox container.
            unread_threads = page.locator("a[href^='/direct/t/']").filter(has_text="Unread")
            
            count = unread_threads.count()
            if count == 0:
                logger.info("No unread DMs found. Polling cycle complete.")
                return

            logger.info(f"Found {count} unread DM thread(s).")
            
            # We process up to MAX_DMS_PER_CYCLE per cycle to prevent high-volume backlogs
            max_to_process = min(count, Config.MAX_DMS_PER_CYCLE)
            logger.info(f"Processing up to {max_to_process} thread(s) this cycle.")
            
            for i in range(max_to_process):
                # Re-query unread threads because DOM is dynamic and changes after navigating
                unread_threads = page.locator("a[href^='/direct/t/']").filter(has_text="Unread")
                if unread_threads.count() == 0:
                    break
                    
                thread_to_read = unread_threads.first
                thread_to_read.click()
                
                # Wait for the message history window to load
                message_input = page.locator("div[aria-label='Message']")
                message_input.wait_for(state="visible")
                
                # Scrape the latest messages
                messages = page.locator("div[dir='auto']").all_inner_texts()
                if not messages:
                    logger.warning("Clicked thread but could not extract message text.")
                    page.goto("https://www.instagram.com/direct/inbox/")
                    page.wait_for_selector("div[role='main']", state="visible")
                    continue
                    
                latest_msg_text = messages[-1]
                logger.info(f"Latest incoming message: '{latest_msg_text}'")
                
                # Pass to SalesAI Brain
                logger.info("Querying SalesAI Brain...")
                agent_decision = process_message(latest_msg_text)
                
                if agent_decision.needs_human:
                    logger.warning(f"SalesAI flagged thread for human intervention. Intent: {agent_decision.intent}")
                    # We skip replying so a human can take over
                elif agent_decision.response_text:
                    logger.info(f"SalesAI Decision: {agent_decision.intent}. Replying...")
                    message_input.fill(agent_decision.response_text)
                    message_input.press("Enter")
                    logger.info("Message sent successfully.")
                    time.sleep(2)
                    
                # Navigate back to inbox for the next iteration
                page.goto("https://www.instagram.com/direct/inbox/")
                page.wait_for_selector("div[role='main']", state="visible")

        except Exception as e:
            logger.error(f"Error during DM scraping automation: {e}", exc_info=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"failure_dm_scraper_{timestamp}.png"
            if 'page' in locals():
                page.screenshot(path=screenshot_path)
                logger.error(f"UI state saved to {screenshot_path} for debugging.")
        finally:
            if 'context' in locals():
                context.close()
                logger.info("DM Scraper session closed.")
