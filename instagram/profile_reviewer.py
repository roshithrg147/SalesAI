import sys
import os
import json
from playwright.sync_api import sync_playwright
from google import genai
from db.database import get_product_context
from config import setup_logger

logger = setup_logger("instagram.profile_reviewer")

def extract_profile_data(username: str) -> dict:
    profile_data = {"username": username}
    
    with sync_playwright() as p:
        # Launch with existing session
        context = p.chromium.launch_persistent_context(
            user_data_dir="./ig_session",
            headless=False,
            args=["--disable-notifications"]
        )
        
        page = context.new_page()
        logger.info(f"Loading profile for @{username}...")
        page.goto(f"https://www.instagram.com/{username}/")
        
        # Wait for either the profile header to load or a "Page not found" indicator.
        # usually 3 header elements: posts, followers, following
        try:
            # We wait for the main role representing the user profile page.
            page.wait_for_selector('header', timeout=10000)
            page.wait_for_timeout(3000) # give it a moment to stabilize
        except Exception as e:
            logger.error(f"Could not load profile or header not found: {e}")
            page.screenshot(path="profile_error.png")
            context.close()
            return None

        # Try to extract the display name
        try:
            # Usually an h2 or span in the header
            # Let's try to get all text in the header section and we'll pass the raw text to the LLM
            header_text = page.locator("header").inner_text()
            profile_data["raw_header_text"] = header_text
        except Exception:
            profile_data["raw_header_text"] = "Not found"
            
        logger.info("Scraping completed.")
        context.close()
        
    return profile_data

def review_profile(profile_data: dict):
    if not profile_data:
        logger.warning("No profile data to review.")
        return

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment.")

    client = genai.Client(api_key=api_key)
    product_context = get_product_context()
    
    system_instruction = """
### ROLE
You are the "SalesAI Director," the lead strategist for a streetwear brand. 

### PERSPECTIVES
You are evaluating an Instagram profile to see if it's optimized for sales and conversions.
Analyze the provided raw scraped text from the Instagram profile header.
Review the profile against the following best practices:
1. Clear Value Proposition in the bio.
2. Strong Call to Action (CTA).
3. Contact Info or a Link present.
4. Professional tone suitable for a streetwear brand.

### OUTPUT STRUCTURE
Provide a concise, professional review in Markdown format.
Include:
- **Current Stats**: Briefly summarize the followers, following, and posts based on the raw text.
- **Bio Analysis**: Quote the bio if found, and analyze its strengths and weaknesses.
- **Sales Readiness Score**: Rate out of 10.
- **Recommendations**: 3-5 actionable steps to improve the profile for sales conversions.
"""

    prompt = f"""
{system_instruction}

Here is the context of what products we sell:
{product_context}

Here is the scraped raw text from the Instagram header for @{profile_data['username']}:
---
{profile_data.get('raw_header_text', 'No data')}
---

Please provide your review.
"""

    logger.info("Sending profile data to Gemini for review...")
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt]
        )
        logger.info("\n--- PROFILE REVIEW ---\n")
        logger.info(response.text)
        
        # Optionally save to file
        report_filename = f"{profile_data['username']}_review.md"
        with open(report_filename, "w") as f:
            f.write(response.text)
        logger.info(f"\nReview saved to {report_filename}")
        
    except Exception as e:
        logger.error(f"Error generating review: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        username = sys.argv[1]
        data = extract_profile_data(username)
        review_profile(data)
    else:
        logger.error("Usage: python3 profile_reviewer.py <instagram_username>")
