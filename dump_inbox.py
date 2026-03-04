import sys
import logging
from playwright.sync_api import sync_playwright
import json

def dump_inbox_threads():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir="/tmp/ig_session",
            headless=True,
            args=["--disable-notifications"]
        )
        page = context.new_page()
        page.goto("https://www.instagram.com/direct/inbox/")
        page.wait_for_selector("nav, [role='navigation'], a[href='/']", state="visible")
        page.wait_for_timeout(3000)
        
        threads = page.locator("a[href^='/direct/t/']").all()
        results = []
        for i, t in enumerate(threads):
            html = t.evaluate("el => el.outerHTML")
            text = t.inner_text()
            aria_label = t.evaluate("el => el.getAttribute('aria-label')")
            results.append({"index": i, "text": text, "aria_label": aria_label, "html": html})
            
        with open("inbox_dump.json", "w") as f:
            json.dump(results, f, indent=2)
            
        print(f"Dumped {len(results)} threads to inbox_dump.json")
        context.close()

if __name__ == "__main__":
    dump_inbox_threads()
