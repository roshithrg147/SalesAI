# HypeMind: Streetwear Social Media & Sales Agent

Welcome to **HypeMind**, your fully automated, AI-powered lead strategist for streetwear social media and direct message (DM) sales.

HypeMind acts as an autonomous social media manager and sales representative. It leverages cutting-edge Large Language Models (Gemini 2.5 Flash / Veo APIs) to generate high-converting content and handle customer interactions, while utilizing headless browser automation (Playwright) to interface directly with Instagram. Under the hood, it uses AWS cloud-native services for session persistence and analytics logging.

---

## 🚀 Key Features

- **Autonomous DM Sales Agent**: Continuously polls the Instagram inbox, reads customer inquiries, and uses AI to determine intent. It can autonomously reply with product sizing, pricing, and checkout links based on the product catalog, or flag complex issues for a human.
- **Intelligent Content Creation**: Analyzes raw product images to generate viral captions following marketing frameworks (e.g., AIDA).
- **Video Ad Generation**: Compiles static images into promotional marketing videos or utilizes the Veo API to generate cinematic 5-10 second video ads.
- **Automated Publishing**: Handles the complete Instagram upload flow (Posts/Reels) headlessly, including UI navigation and media uploading.
- **Cloud-Native Session Persistence**: Zips and syncs the Playwright browser session state (cookies and local storage) to an AWS S3 bucket, allowing the bot to run on ephemeral instances (like EC2 or containers) without requiring repeated manual logins.
- **Analytics Logging**: Logs all customer interactions and AI-determined intents to AWS DynamoDB for auditing and sales analytics.

---

## 🛠 Tech Stack

HypeMind is built using a modern, robust Python stack designed for automation and AI integration:

- **Core Language:** Python 3.8+
- **AI / LLM:**
  - `google-genai` (Gemini 2.5 Flash) for intent routing, DM replies, and caption generation.
  - Veo APIs for cinematic video generation.
- **Browser Automation:** `playwright` (Chromium) for navigating the Instagram web interface, reading DMs, and uploading media.
- **Cloud Infrastructure (AWS):** `boto3`
  - **Amazon S3:** Used for storing and syncing the `ig_session.zip` to maintain authentication states across runs.
  - **Amazon DynamoDB:** Used for logging interactions and intents from the DM Scraping agent.
- **Data Validation:** `pydantic` for enforcing strict structured JSON outputs from the Gemini models.
- **Background Jobs:** `schedule` for managing background posting tasks and polling intervals.
- **Media Processing:** `moviepy`, `Pillow`, `numpy` for stitching and generating promotional video assets.

---

## 🏗 Architecture & Workflow Overview

The application is structured into specific operational domains:

1.  `config.py`: Centralized configuration, logging setup, and environment variable management (`.env`).
2.  `db/`: Manages the Ground Truth JSON product catalog and database connections.
3.  `ai/brain.py`: The core intelligence layer. It uses Gemini Structured Outputs (via Pydantic's `AgentDecision` schema) to strictly route customer intent based on the catalog context.
4.  `instagram/`: The automation layer. Contains robust Playwright scripts to scrape DMs (`dm_scraper.py`) and upload posts (`ig_poster.py`). Includes error recovery and UI screenshotting on failure.
5.  `content/`: Pipelines for media processing, generating static image posts, and Veo cinematic ads.
6.  `core/`: Contains the task `scheduler.py` for cron-like operational loops.

### Operational Workflow

1.  **Initialization (`main.py run`)**: The orchestrator boots up. It first reaches out to AWS S3 to download and extract the persistent `ig_session` to authenticate Playwright.
2.  **Background Threads Start**:
    - **Main Thread (Scheduler):** Checks for scheduled tasks (e.g., posting a daily generated video at 10:00 AM).
    - **Daemon Thread (DM Poller):** Wakes up every few minutes (configurable via `POLL_INTERVAL_SECONDS`) and triggers the `dm_scraper`.
3.  **The DM Scraping Loop**:
    - Playwright launches headlessly and navigates to the Instagram Direct Inbox.
    - It identifies unread threads and extracts the latest messages.
    - The message is passed to `ai/brain.py`.
    - Gemini analyzes the intent. If it's a sales question (price, size), it formulates a reply.
    - The interaction is logged to AWS DynamoDB.
    - Playwright types the reply into the chat and hits send. It then navigates back to the inbox to process the next thread.
4.  **Session Teardown**: After operations, or if manually triggered, the session directory is re-zipped and pushed back to AWS S3 (`sync_session_to_s3`) to ensure cookies remain fresh.

---

## ⚙️ Setup & Configuration

### Prerequisites

1.  Python 3.8+
2.  AWS Account with configured CLI credentials (`~/.aws/credentials`).
3.  Google Gemini API Key.

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser engines
playwright install chromium
```

### Environment Variables (`.env`)

Create a `.env` file in the root directory:

```env
# Required API Keys
GEMINI_API_KEY=your_gemini_api_key

# AWS Configuration Override (Optional, defaults are provided)
S3_BUCKET_NAME=hypemind-assets
DYNAMODB_PRODUCTS=HypeMindProducts
DYNAMODB_INQUIRIES=HypeMindInquiries

# Application Settings
IMG_DIR=/path/to/your/raw/images
LOGGING_LEVEL=INFO
POLL_INTERVAL_SECONDS=300

# Playwright Settings
PLAYWRIGHT_HEADLESS=True
PLAYWRIGHT_TIMEOUT=30000
```

---

## 🎮 Usage Guide

The application uses `main.py` as the unified command-line orchestrator.

### 1. Initial Authentication (Required Once)

Before running headlessly, you must authenticate the bot with Instagram manually. This saves the session state.

```bash
python3 main.py login
```

A visible browser window will open. Log into your Instagram account. Once you see your inbox, return to the terminal and press `Enter`. This will save your session locally and upload it to AWS S3.

### 2. Run the Autonomous Daemon

Starts the automated scheduler (for posts) AND the background DM scraper loop (polling the inbox).

```bash
python3 main.py run
```

### 3. Manual Triggers

You can force the agent to execute specific actions independently of the schedule:

- `python3 main.py post-now`: Drafts a post from a random image in the `IMG_DIR` and uploads it immediately.
- `python3 main.py generate-video`: Compiles static images into a `promo_video.mp4`.
- `python3 main.py post-video`: Generates a promotional video, uploads it to Instagram with an AI caption, and then deletes the local video file.
- `python3 main.py generate-ad`: Uses Veo to generate a high-end cinematic ad, auto-posts it, and performs cleanup.

---

## 🔒 Security & Guardrails

- **Prompt Injection Defense:** The `ai/brain.py` system prompts are hardened to reject attempts that divert the AI from its primary sales function.
- **Structured AI Outputs:** By enforcing strict schemas (Pydantic), the system prevents AI hallucinations and malformed responses from breaking the automation loop.
- **State Recovery:** If a UI element cannot be found due to Instagram layout updates or network issues, Playwright immediately takes a DOM screenshot (`failure_*.png`) before safely shutting down that execution context, allowing developers to debug headlessly.
- **AWS Least Privilege:** Ensure your AWS IAM entity only has the exact required permissions (S3 Read/Write for `hypemind-assets`, DynamoDB PutItem for `HypeMindInquiries`).
