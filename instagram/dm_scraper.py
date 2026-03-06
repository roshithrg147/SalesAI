# ==========================================
# Developer: Mr. R.
# Project:   HypeMind
# ==========================================

import os
import time
import uuid
import re
import boto3
from datetime import datetime
from playwright.sync_api import sync_playwright

from config import Config, setup_logger
from ai.brain import process_message

logger = setup_logger("instagram.dm_scraper")

SELECTORS = {
    "INBOX_URL": "https://www.instagram.com/direct/inbox/",
    "INBOX_NAV": "svg[aria-label='Direct'], svg[aria-label='Messages'], svg[aria-label='Messenger'], section[role='main']",
    "NOT_NOW_BTN": "Not Now|Not now",
    "THREAD_LINKS": "div[role='button']:has(span[title])",
    # Note: MESSAGE_INPUT etc. remain here but we've mostly been debugging THREAD_LINKS and INBOX_NAV
    "MESSAGE_INPUT": "div[role='textbox']",
    "SEND_BUTTON": "div[role='button']:has-text('Send')",
    "MESSAGE_TEXTS": "div[dir='auto']"
}

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

def log_inquiry_to_dynamodb(message_text, intent, response_text):
    """
    Logs the processed inquiry to the AWS DynamoDB table for auditing and analytics.
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(Config.INQUIRIES_TABLE)
        
        item = {
            'inquiry_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'message_text': message_text,
            'intent': intent,
            'response_text': response_text if response_text else "FLAGGED_FOR_HUMAN"
        }
        table.put_item(Item=item)
        logger.info(f"Successfully logged inquiry {item['inquiry_id']} to DynamoDB.")
    except Exception as e:
        # We don't want a DB logging failure to crash the whole application loop
        logger.error(f"Failed to log inquiry to DynamoDB: {e}", exc_info=True)

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
                executable_path=Config.PLAYWRIGHT_EXEC_PATH,
                headless=Config.PLAYWRIGHT_HEADLESS,
                args=["--disable-notifications", "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--single-process"]
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(Config.PLAYWRIGHT_TIMEOUT)

            logger.info("Navigating to Instagram Direct Inbox...")
            page.goto(SELECTORS["INBOX_URL"])
            
            # Wait a moment to see if we get redirected to the login page
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
            if "login" in page.url:
                logger.error("Redirected to login page. Session cookies are missing or expired. Please run 'python3 main.py login' to re-authenticate.")
                return
            
            # Dismiss potential "Turn on Notifications" or "Save Login Info" modals
            not_now_btn = page.get_by_text(re.compile(SELECTORS["NOT_NOW_BTN"], re.IGNORECASE))
            if safe_click(page, not_now_btn, timeout=3000):
                 logger.info("Dismissing 'Not now' popup / interstitial.")
                 page.wait_for_timeout(6000) # give it time to navigate or close modal
                
            # Now we must strictly wait for the main interface layout indicating the inbox is loaded
            page.wait_for_selector(SELECTORS["INBOX_NAV"], state="visible", timeout=15000)
            
            
            logger.info("Scanning recent threads for unreplied messages...")
            processed_count = 0
            
            for cycle_i in range(Config.MAX_DMS_PER_CYCLE):
                # Wait for the inbox list to be visible before locating threads
                page.wait_for_selector(SELECTORS["THREAD_LINKS"], state="visible", timeout=15000)
                all_threads = page.locator(SELECTORS["THREAD_LINKS"])
                count = all_threads.count()
                
                if count == 0:
                    logger.info("No DMs found in inbox. Polling cycle complete.")
                    break
                    
                found_unreplied = False
                
                # We check the top 15 threads maximum so we don't scan too far back
                scan_limit = min(count, 15)
                logger.debug(f"Cycle {cycle_i + 1}: Found {count} threads. Scanning top {scan_limit}...")
                
                for thread_idx in range(scan_limit):
                    thread = all_threads.nth(thread_idx)
                    try:
                        # Wait slightly if the text isn't fully rendered yet
                        thread.wait_for(state="visible", timeout=1000)
                        text = thread.inner_text()
                        logger.debug(f"Thread {thread_idx} text preview: '{text.replace(os.linesep, ' ')}'")
                    except Exception as e:
                        logger.debug(f"Skipping thread {thread_idx} due to read error: {e}")
                        continue
                        
                    # Ignore "Notes" feature which appears as a list item at the top
                    if "Your note" in text or "Ask friends anything" in text:
                        logger.debug(f"Skipping thread {thread_idx}: It's a 'Note' not a DM.")
                        continue
                        
                    # 1. Check if the thread has an unread indicator (usually a blue dot)
                    # Instagram uses span classes or aria-labels for "Unread", but in the new layout it actually has an invisible element with text='Unread'
                    unread_text_matches = thread.locator("text='Unread'").count() > 0
                    unread_aria_matches = thread.locator("xpath=.//*[contains(@aria-label, 'Unread')]").count() > 0
                    is_unread_indicator = unread_text_matches or unread_aria_matches
                    
                    # 2. Check if we already replied to this thread
                    # Usually indicated by "You:" or "You sent" in the preview text
                    replied_heuristics = ["You:", "You sent", "Sent"]
                    is_replied = any(h in text for h in replied_heuristics)
                    
                    if is_replied and not is_unread_indicator:
                        logger.debug(f"Skipping thread {thread_idx}: Appears replied to.")
                        continue
                        
                    # Let's consider it unreplied if it has an unread indicator OR it doesn't look like we sent the last message
                    found_unreplied = True
                    logger.info(f"==> Found active/unreplied message at thread index {thread_idx}.")
                    safe_click(page, thread)
                    break # Break out of scanning loop and process this thread
                    
                if not found_unreplied:
                    logger.info("No unreplied messages found among top threads. Polling cycle complete.")
                    break
                    
                processed_count += 1
                
                # Wait for the message history window to load
                message_input = page.locator(SELECTORS["MESSAGE_INPUT"])
                message_input.wait_for(state="visible")
                
                # Scrape the latest messages
                messages = page.locator(SELECTORS["MESSAGE_TEXTS"]).all_inner_texts()
                if not messages:
                    logger.warning("Clicked thread but could not extract message text.")
                    page.goto(SELECTORS["INBOX_URL"])
                    page.wait_for_timeout(2000)
                    page.wait_for_selector(SELECTORS["INBOX_NAV"], state="visible", timeout=15000)
                    continue
                    
                latest_msg_text = messages[-1]
                logger.info(f"Latest incoming message: '{latest_msg_text}'")
                
                # Pass to SalesAI Brain
                logger.info("Querying SalesAI Brain...")
                agent_decision = process_message(latest_msg_text)
                
                # Immediately log transaction to AWS
                log_inquiry_to_dynamodb(
                    message_text=latest_msg_text,
                    intent=agent_decision.intent,
                    response_text=agent_decision.response_text
                )
                
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
                page.goto(SELECTORS["INBOX_URL"])
                page.wait_for_timeout(2000)
                page.wait_for_selector(SELECTORS["INBOX_NAV"], state="visible", timeout=15000)

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
