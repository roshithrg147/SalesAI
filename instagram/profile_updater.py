import sys
import time
from playwright.sync_api import sync_playwright
from config import Config, setup_logger

logger = setup_logger("instagram.profile_updater")

def update_aesthetic():
    """
    Automates the aesthetic enforcement:
    1. Sets bio to a 'lowercase living' style
    2. Optimizes display name for SEO
    """
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=Config.IG_SESSION_DIR,
            executable_path=Config.PLAYWRIGHT_EXEC_PATH,
            headless=False,
            args=["--disable-notifications", "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--single-process"]
        )
        
        page = context.new_page()
        logger.info("Loading Edit Profile page...")
        page.goto("https://www.instagram.com/accounts/edit/")
        
        try:
            # Wait for the editable inputs
            page.wait_for_timeout(5000)
            
            # Display Name Update
            # Instagram often uses placeholder='Name'
            name_input = page.get_by_placeholder("Name", exact=False).first
            if name_input.count() > 0:
                name_input.fill("Roshith | Streetwear & Jackets")
                logger.info("Filled Name.")
            else:
                logger.warning("Could not find Name input.")

            # Bio Update
            bio_input = page.get_by_placeholder("Bio", exact=False).first
            if bio_input.count() > 0:
                bio_input.fill("urban industrial wear. \\nworldwide shipping 🌍\\nlink below to shop.")
                logger.info("Filled Bio.")
            else:
                bio_box = page.get_by_role("textbox", name="Bio")
                if bio_box.count() > 0:
                    bio_box.fill("urban industrial wear. \\nworldwide shipping 🌍\\nlink below to shop.")
                    logger.info("Filled Bio via role.")
                else:
                    logger.warning("Could not find Bio input.")
            
            # Save Profile
            save_button = page.get_by_role("button", name="Submit").first
            if save_button.count() > 0:
                save_button.click()
                logger.info("Profile updated successfully with new aesthetic!")
            else:
                logger.warning("Could not find Save button.")
                
            page.wait_for_timeout(3000)
            
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            page.screenshot(path="aesthetic_error.png")
            logger.info("Screenshot saved to aesthetic_error.png")
            
        context.close()

if __name__ == "__main__":
    update_aesthetic()
