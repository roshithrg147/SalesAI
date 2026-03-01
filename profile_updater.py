import sys
import time
from playwright.sync_api import sync_playwright

def update_aesthetic():
    """
    Automates the aesthetic enforcement:
    1. Sets bio to a 'lowercase living' style
    2. Optimizes display name for SEO
    """
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir="./ig_session",
            headless=False,
            args=["--disable-notifications"]
        )
        
        page = context.new_page()
        print("Loading Edit Profile page...")
        page.goto("https://www.instagram.com/accounts/edit/")
        
        try:
            # Wait for the editable inputs
            page.wait_for_timeout(5000)
            
            # Display Name Update
            # Instagram often uses placeholder='Name'
            name_input = page.get_by_placeholder("Name", exact=False).first
            if name_input.count() > 0:
                name_input.fill("Roshith | Streetwear & Jackets")
                print("Filled Name.")
            else:
                print("Could not find Name input.")

            # Bio Update
            bio_input = page.get_by_placeholder("Bio", exact=False).first
            if bio_input.count() > 0:
                bio_input.fill("urban industrial wear. \\nworldwide shipping 🌍\\nlink below to shop.")
                print("Filled Bio.")
            else:
                bio_box = page.get_by_role("textbox", name="Bio")
                if bio_box.count() > 0:
                    bio_box.fill("urban industrial wear. \\nworldwide shipping 🌍\\nlink below to shop.")
                    print("Filled Bio via role.")
                else:
                    print("Could not find Bio input.")
            
            # Save Profile
            save_button = page.get_by_role("button", name="Submit").first
            if save_button.count() > 0:
                save_button.click()
                print("Profile updated successfully with new aesthetic!")
            else:
                print("Could not find Save button.")
                
            page.wait_for_timeout(3000)
            
        except Exception as e:
            print(f"Error updating profile: {e}")
            page.screenshot(path="aesthetic_error.png")
            print("Screenshot saved to aesthetic_error.png")
            
        context.close()

if __name__ == "__main__":
    update_aesthetic()
