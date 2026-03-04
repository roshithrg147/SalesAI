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

def log_inquiry_to_dynamodb(message_text, intent, response_text):
    """
    Logs the processed inquiry to the AWS DynamoDB table for auditing and analytics.
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(Config.INQUIRIES_TABLE)
        
        item = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'message_text': message_text,
            'intent': intent,
            'response_text': response_text if response_text else "FLAGGED_FOR_HUMAN"
        }
        table.put_item(Item=item)
        logger.info(f"Successfully logged inquiry {item['id']} to DynamoDB.")
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
                headless=Config.PLAYWRIGHT_HEADLESS,
                args=["--disable-notifications"]
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(Config.PLAYWRIGHT_TIMEOUT)

            logger.info("Navigating to Instagram Direct Inbox...")
            page.goto("https://www.instagram.com/direct/inbox/")
            
            # Wait a moment to see if we get redirected to the login page
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
            if "login" in page.url:
                logger.error("Redirected to login page. Session cookies are missing or expired. Please run 'python3 main.py login' to re-authenticate.")
                return
            
            # Instagram often intercepts the inbox route with a 'Save Your Login Info?' 
            # or 'Turn on Notifications' interstitial page/modal.
            try:
                page.locator("nav, text=Not Now, text=Not now").first.wait_for(state="visible", timeout=30000)
            except Exception:
                # Try to proceed anyway
                pass
                
            # Dismiss potential "Turn on Notifications" or "Save Login Info" modals
            try:
                not_now_btn = page.get_by_text(re.compile(r"Not now", re.IGNORECASE))
                if not_now_btn.count() > 0 and not_now_btn.first.is_visible(timeout=3000):
                    logger.info("Dismissing 'Not now' popup / interstitial.")
                    not_now_btn.first.click()
                    page.wait_for_timeout(3000) # give it time to navigate or close modal
            except Exception:
                pass
                
            # Now we must strictly wait for the main interface layout indicating the inbox is loaded
            page.wait_for_selector("nav, [role='navigation'], a[href='/']", state="visible")
            
            
            logger.info("Scanning recent threads for unreplied messages...")
            processed_count = 0
            
            for cycle_i in range(Config.MAX_DMS_PER_CYCLE):
                # Always requery the threads as navigating back to inbox refreshes the DOM
                all_threads = page.locator("a[href^='/direct/t/']")
                count = all_threads.count()
                
                if count == 0:
                    logger.info("No DMs found in inbox. Polling cycle complete.")
                    break
                    
                found_unreplied = False
                
                # We check the top 15 threads maximum so we don't scan too far back
                scan_limit = min(count, 15)
                
                for thread_idx in range(scan_limit):
                    thread = all_threads.nth(thread_idx)
                    try:
                        # Wait slightly if the text isn't fully rendered yet
                        thread.wait_for(state="visible", timeout=1000)
                        text = thread.inner_text()
                    except Exception:
                        continue
                        
                    # Check if we already replied to this thread
                    # Usually indicated by "You:" or "You sent" in the preview text
                    if "You:" in text or "You sent" in text:
                        continue
                    
                    found_unreplied = True
                    logger.info(f"Found unreplied message at thread index {thread_idx}.")
                    thread.click()
                    break # Break out of scanning loop and process this thread
                    
                if not found_unreplied:
                    logger.info("No unreplied messages found among top threads. Polling cycle complete.")
                    break
                    
                processed_count += 1
                
                # Wait for the message history window to load
                message_input = page.locator("div[aria-label='Message']")
                message_input.wait_for(state="visible")
                
                # Scrape the latest messages
                messages = page.locator("div[dir='auto']").all_inner_texts()
                if not messages:
                    logger.warning("Clicked thread but could not extract message text.")
                    page.goto("https://www.instagram.com/direct/inbox/")
                    page.wait_for_timeout(2000)
                    page.wait_for_selector("nav, [role='navigation'], a[href='/']", state="visible")
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
                page.goto("https://www.instagram.com/direct/inbox/")
                page.wait_for_timeout(2000)
                page.wait_for_selector("nav, [role='navigation'], a[href='/']", state="visible")

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
