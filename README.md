# HypeMind: Streetwear Social Media & Sales Agent

Welcome to **HypeMind**, your fully automated, AI-powered lead strategist for streetwear social media and direct message (DM) sales.

HypeMind has evolved into a hardened, cloud-native **Event-Driven Serverless Application**. It leverages cutting-edge Large Language Models (Gemini 2.5 Flash / Veo APIs) to generate high-converting content and handle customer interactions, while utilizing headless browser automation (Playwright) to interface directly with Instagram. Under the hood, it operates on AWS Lambda for infinite scaling, utilizing AWS native services for session persistence, distributed locking, and analytics logging.

---

## 🚀 Key Features

- **Autonomous DM Sales Agent**: Reads customer inquiries and uses AI to determine intent. It can autonomously reply with product sizing, pricing, and checkout links based on the product catalog, or flag complex issues for a human.
- **Intelligent Content Creation**: Analyzes raw product images to generate viral captions following marketing frameworks (e.g., AIDA).
- **Video Ad Generation**: Compiles static images into promotional marketing videos or utilizes the Veo API to generate cinematic 5-10 second video ads.
- **Automated Publishing**: Handles the complete Instagram upload flow (Posts/Reels) headlessly, including UI navigation and media uploading.
- **Cloud-Native Session Persistence**: Zips and syncs the Playwright browser session state (cookies and local storage) to an AWS S3 bucket, allowing the bot to run on ephemeral Lambda instances without requiring repeated manual logins.
- **Analytics Logging**: Logs all customer interactions and AI-determined intents to AWS DynamoDB for auditing and sales analytics.

---

## 🛠 Tech Stack

HypeMind is built using a modern, robust Python stack designed for automation and AI integration in a serverless environment:

- **Core Language:** Python 3.8+
- **AI / LLM:**
  - `google-genai` (Gemini 2.5 Flash) for intent routing, DM replies, and caption generation.
  - Veo APIs for cinematic video generation.
- **Browser Automation:** `playwright` (Chromium) utilizing a **Page Object Model (POM)** approach for centralized UI selectors, making browser interactions highly resilient.
- **Cloud Infrastructure (AWS):** `boto3`
  - **AWS Lambda & EventBridge**: Powers the event-driven execution architecture.
  - **Amazon S3:** Used for storing and syncing the `ig_session.zip` to maintain authentication states across runs.
  - **Amazon DynamoDB:** Used for logging interactions, plus serving as the backbone for our distributed concurrent **LocksTable**.
- **Data Validation & Caching:**
  - `pydantic` for enforcing strict structured JSON outputs from Gemini.
  - `cachetools` (`TTLCache`) for heavily minimizing DynamoDB reads and preventing Full Table Scans.
- **Media Processing:** `moviepy`, `Pillow`, `numpy` for stitching and generating promotional video assets.

---

## 🏗 Architecture & Workflow Overview

HypeMind operates as an **Event-Driven Serverless Application**.

1.  **AWS Lambda Handler (`main.lambda_handler`)**: The application is triggered by incoming JSON payload events (e.g., `{"action": "scrape_dms"}` or `{"action": "post_scheduled"}`) fired by **AWS EventBridge** cron rules.
2.  **Distributed Locking**: Before taking action, HypeMind queries DynamoDB (`config.LOCKS_TABLE`) to acquire an ephemeral distributed lock (`acquire_lock`). This prevents Lambda container overlaps, race conditions, and `ig_session.zip` state corruption.
3.  **State Hydration**: The Lambda container syncs the Playwright `ig_session.zip` from S3 directly into its ephemeral storage.
4.  **Execution Loop**:
    - The core operation runs (e.g., reading unread threads via `dm_scraper` or crafting content).
    - Data passes back and forth to Gemini (`ai/brain.py`) to fulfill tasks while validating structured responses.
5.  **Session Teardown**: The updated session cookies are zipped and persisted back to S3, and the DynamoDB lock is cleanly released.

---

## ⚙️ Setup & Configuration

### Prerequisites

1.  Python 3.8+
2.  AWS Account with configured credentials and required permissions (Lambda, S3, DynamoDB, EventBridge).
3.  Google Gemini API Key.

### Environment Setup

Ensure you install all core dependencies (including `boto3` for AWS integrations):

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables (`.env` or AWS Lambda Environment)

```env
# Required API Keys
GEMINI_API_KEY=your_gemini_api_key

# AWS Configuration
S3_BUCKET_NAME=hypemind-assets
DYNAMODB_PRODUCTS=HypeMindProducts
DYNAMODB_INQUIRIES=HypeMindInquiries
DYNAMODB_LOCKS=HypeMindLocks

# Playwright Settings
PLAYWRIGHT_HEADLESS=True
PLAYWRIGHT_TIMEOUT=60000
```

---

## 🎮 Usage Guide & Deployment

### 1. Initial Authentication (Required Once Locally)

Before deploying to AWS, you must authenticate the bot with Instagram manually to capture the initial cookie state.

```bash
python3 main.py login
```

A visible browser window will open. Log into your Instagram account. Once in your inbox, return to the terminal and press `Enter`. This will save your session locally and upload it to AWS S3.

### 2. Lambda Deployment & Invocation

HypeMind is designed to run on AWS Lambda triggers.

- **Configure EventBridge Rules**: Create AWS EventBridge schedules to trigger your Lambda function based on your desired cadence.
- **Expected Payload Formats**:
  - DM Polling: `{"action": "scrape_dms"}`
  - Scheduled Posting: `{"action": "post_scheduled"}`

### 3. Local Cloud Testing (Manual Triggers)

You can force the orchestrator to execute actions manually locally passing standard CLI arguments:

- `python3 main.py scrape-dms`: Executes the DM scraping cycle.
- `python3 main.py post-now`: Drafts and uploads a post utilizing images and AI copy.
- `python3 main.py generate-video`: Compiles static images into a `promo_video.mp4`.
- `python3 main.py post-video`: Generates a promo video and uploads it.
- `python3 main.py generate-ad`: Generates a Veo ad and posts it to Instagram.

---

## 🔒 Security, Guardrails & Production Readiness

HypeMind has undergone rigorous scaling and production refactoring to ensure safe, continuous execution.

- **Resource Management (Ephemeral Storage)**: All media processing pipelines (video rendering, downloads) strictly utilize Python's `tempfile.TemporaryDirectory`. This guarantees flawless ephemeral storage cleanup when the Lambda context closes, eliminating memory/storage leaks.
- **Resilience Layer**: Interfacing with the web and external APIs can be flaky. Playwright UI interactions are heavily shielded via a robust Page Object Model, and both Playwright queries and AWS `boto3` API calls implement strict **exponential backoff and retry logic**.
- **Centralized Logging & Observability**: All `print()` calls have been replaced by a unified system `logger`. This ensures AWS CloudWatch cleanly aggregates execution data, completely avoiding API or session token leakage.
- **Prompt Injection Defense:** The `ai/brain.py` directives are fortified to aggressively reject attempts that divert the AI from its primary streetwear sales function, utilizing deterministic temperatures and graceful fallback responses for quota limits.
