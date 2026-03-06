# HypeMind Engineering Log

**Purpose**: This log tracks historical failures, root causes, fixes, and key insights to create an episodic memory for the agentic system.

**Reflective Loop Requirement**: Before starting any task, read AGENTS.md and the last 3 entries of this log.

---

## [2026-03-07] - Optimized Playwright Docker Execution

- **Error**: Playwright crashed in Docker/Lambda because it looked for the browser executable in the dynamic user cache (`/home/sbx_user...`) instead of a globally accessible path, and lacked necessary container sandbox flags.
- **Root Cause**: The Dockerfile installed Chromium without system dependencies and didn't set global read/execute permissions. Python scripts launched Playwright without specifying the explicit `executable_path` and required Lambda flags (`--disable-dev-shm-usage`, `--single-process`).
- **Fix**:
  - Updated `Dockerfile` to use `playwright install chromium` (omitting `--with-deps` since they were manually installed via system packages in Step 2) and `chmod -R 755 /ms-playwright`.
  - Centralized `PLAYWRIGHT_EXEC_PATH` in `config.py` using a dynamic `glob` search (`/ms-playwright/chromium-*/chrome-linux64/chrome`) to automatically handle Chromium version upgrades.
  - Updated all Python scripts to use `executable_path` and the required Lambda Chromium arguments during `launch_persistent_context`.
- **Key Insight**: When deploying Playwright to AWS Lambda or strict Docker containers, always decouple the browser binary from the user cache. Install it globally with custom-controlled system dependencies, enforce `755` permissions, and explicitly pass the container-safe sandbox arguments. Use dynamic path resolution (`glob`) rather than hardcoding binary version folders.

## [2026-03-06] - Instagram Video Posting Timeout (Success Dialog)

- **Error**: `Timeout 60000ms exceeded` waiting for `Your post has been shared.`
- **Root Cause**: Instagram now processes all video uploads as Reels and changed the success confirmation dialog text from "Your post has been shared." to "Your reel has been shared."
- **Fix**: Updated `SUCCESS_MSG` selector in `ig_poster.py` to use a regex `re.compile("Your post has been shared.|Your reel has been shared.", re.IGNORECASE)` to catch both image and video success dialogs.
- **Key Insight**: Hardcoded UI strings are prone to breaking during A/B testing or feature shifts (like the transition of all videos to Reels). When checking for success states, use flexible regexes or check for the presence of the modal itself.

## [2026-03-06] - Instagram Playwright Fix & Cleanup Completed

- **Root Cause & Fix**: Instagram changed the core DOM representations for direct messages, breaking classic tag link navigation (`a[href^='/direct/t/']`). Upgraded the locators to crawl up to generic `div[role='button']:has(span[title])` structural wrappers and isolated the `text='Unread'` marker to re-enable scraping functionality.
- **DynamoDB ValidationException**: Fixed a defect where the table's partition key (`inquiry_id`) was strictly expected, but the agent logging script passed `id`.
- **Housekeeping**: Eliminated legacy raw DOM dumps and parsing trial scripts to restore a clean root repository structure. Promoted Playwright experiments to a dedicated `tests/` directory.## [2026-03-06] - DM Scraper Thread Timeout

- **Error**: `Timeout 5000ms exceeded.` while waiting for `div[role='listitem']` (THREAD_LINKS) selector to become visible.
- **Root Cause**: Instagram's DOM structure was updated, rendering `div[role='listitem']` invalid/missing for thread items. Additionally, 5 seconds is too short a timeout for Inbox rendering.
- **Fix**: Replaced the brittle `THREAD_LINKS` selector with the reliable relative URL attribute `a[href^='/direct/t/']`. Increased the selector timeout to 15 seconds. Initially tried `svg[aria-label='Direct']` as a visual marker for `INBOX_NAV`, but that also proved fragile to responsive DOM states (failed with another timeout). Reverted `INBOX_NAV` to wait for the primary structural DOM block: `section[role='main']`.
- **Key Insight**: Rely on fundamental routing/links (`href`) where possible instead of UI pseudo-roles (`role="listitem"`) on dynamic SPA platforms like Instagram. Increase timeouts to account for variable network conditions. Never use `networkidle` on modern SPAs. While waiting for specific visual elements (SVGs) is generally better than network parsing, high-level core structural elements (like global structural `role="main"`) are the most robust indicators that an SPA page architecture has fully resolved its state.

## [2026-03-05] - Instagram Video Posting Timeout

- **Error**: `Locator.click: Timeout 30000ms exceeded.` on the "Next" button during video upload.
- **Root Cause**: The Playwright automation was trying to interact with an element that wasn't fully loaded, visible, or uniquely identifiable at that stage of the IG video upload flow.
- **Fix**: Implemented more robust waiting strategies for the UI flow elements.
- **Key Insight**: Instagram DOM changes frequently. Automation must rely on robust selectors (ARIA roles, specific attributes) rather than brittle paths, and explicitly wait for state changes before interactions.

## [2026-03-03] - Veo API Missing Argument

- **Error**: `generate_videos` method received an unexpected keyword argument `source_images`.
- **Root Cause**: Breaking API change or incorrect initial documentation assumption regarding the Veo API client for Gemini.
- **Fix**: Updated the API call to pass images using the `source` parameter with a `GenerateVideosSource` object instead of `source_images`.
- **Key Insight**: When wrapping external beta APIs (like Veo), expect breaking signature changes. Always verify arguments against the latest SDK types.

## [2026-03-03] - Gemini API GCP Billing Error

- **Error**: `FAILED_PRECONDITION` - `models/veo-2.0-generate-001` requires Google Cloud Platform billing to be enabled.
- **Root Cause**: Reached the limits of the free tier or attempted to use a model that mandates an active billing account on the GCP project linked to the API key.
- **Fix**: Required manual intervention by the human user to activate billing on the GCP console for the project.
- **Key Insight**: AI resource usage bounds must be anticipated. Graceful fallbacks or clear alert logging (rather than silent crashes) should be implemented for billing/quota errors.

## [2026-03-02] - Boto3 ModuleNotFoundError

- **Error**: `ModuleNotFoundError: No module named 'boto3'`
- **Root Cause**: A new dependency (`boto3`) was introduced to the codebase for AWS migration, but the environment was not updated.
- **Fix**: Ran `pip install boto3` locally.
- **Key Insight**: Any import additions to Python files must be accompanied by an update to dependency lists and instructions for the environment setup.
