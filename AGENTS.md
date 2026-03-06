# HypeMind Operating Manual

## High-Level Architecture

HypeMind is an automated agentic system designed to manage an Instagram presence, answer DMs, and post content. It is built to run both locally and in an AWS serverless environment.

## Core Commands

The system is operated via the `main.py` entry point.

- `python3 main.py login`: Starts a local Playwright session to authenticate to Instagram. Saves the session locally and syncs it to S3.
- `python3 main.py scrape-dms`: Executes the DM scraping flow. It pulls the session from S3, reads unread messages, uses AI to formulate responses, replies, and pushes the updated session back to S3.
- `python3 main.py post-now`: Executes the scheduled content posting flow.
- `python3 main.py generate-video`: Generates a promotional video using local assets.
- `python3 main.py post-video`: Posts the `promo_video.mp4` to Instagram and cleans up the file.
- `python3 main.py generate-ad`: Generates a video ad using the Gemini/Veo API and automatically posts it to Instagram.

## State Management Rules

### 1. S3 (Session & Assets)

- **Session State**: The Instagram session (cookies/local storage) is the most critical piece of state. It is zipped and synced to an S3 bucket (`Config.S3_BUCKET`, default: `hypemind-assets`) under the key `ig_session.zip`.
- **Pre-execution**: Before any browser action, `sync_session_from_s3()` MUST be called to pull the latest state into `/tmp/ig_session`.
- **Post-execution**: After any browser action, `sync_session_to_s3()` MUST be called to persist the updated cookies back to S3.
- **Assets**: Images and other assets should be managed via S3, aligning with the AWS migration.

### 2. DynamoDB (Locks & Data)

- **Concurrency Locks**: `Config.LOCKS_TABLE` is used to prevent concurrent executions of the same flow (e.g., `dm_scraper_lock`, `scheduled_poster_lock`). Uses conditional writes.
- **Data Storage**: `Config.PRODUCTS_TABLE` and `Config.INQUIRIES_TABLE` store system state regarding inventory and customer interactions.

### 3. Tmp Storage (`/tmp`)

- **Ephemeral Nature**: The `/tmp` directory is used for temporary processing (e.g., extracting `ig_session.zip`, storing generated videos before upload).
- **AWS Lambda Constraint**: In AWS Lambda, `/tmp` is the _only_ writable filesystem. The `IG_SESSION_DIR` must point to `/tmp/ig_session` in production.
- **Cleanup**: Ephemeral files (like generated videos) should be cleaned up immediately after use to prevent storage limits being reached in Lambda.

### 4. General Principles

- **Idempotency**: All flows should be designed to be idempotent where possible.
- **Distributed Locks**: Always wrap top-level executions in distributed locks using `acquire_lock()` and `release_lock()`.
