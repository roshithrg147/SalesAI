# HypeMind: Streetwear Social Media & Sales Agent

**Developer:** Mr. R.

Welcome to **HypeMind**, your fully automated, AI-powered lead strategist for streetwear social media and direct message sales.

This project leverages the **Gemini 2.5 Flash / Veo APIs** to generate high-converting Instagram posts/videos and **Playwright** to headlessly automate their publication and handle customer DMs.

## 🚀 Key Features & Architecture

After a comprehensive CTO audit, HypeMind has been deeply refactored into a production-ready package architecture:

- `config.py`: Centralized configuration and logging.
- `db/`: Handles the Ground Truth JSON catalog generation (`generate_db.py`) and retrieval.
- `ai/`: Contains the `brain.py` which uses Gemini Structured Outputs (Pydantic) to strictly route customer intent.
- `instagram/`: Robust Playwright automation to upload posts (`ig_poster.py`) and scrape/reply to DMs (`dm_scraper.py`).
- `content/`: AI generation pipelines for static image posts, promotional video compilations, and Veo cinematic ads.
- `core/`: Application loops and schedulers.

### 1. Sales Agent (DM Mode)

The `dm_scraper` continuously polls your Instagram inbox in the background. When a new message arrives, the `brain` analyzes it against the product catalog. If the intent is a sale, it automatically replies with checkout links. Complex issues are flagged for human review.

### 2. Content Creator (Post Mode)

Analyzes raw product images to generate viral Instagram captions following the 'AIDA' framework. It can also generate 5-10 second hyper-realistic ad videos using Gemini's video generation capabilities.

### 3. Automated Setup

Auto-cleans up generated video files (`promo_video.mp4`, `ad_video.mp4`) instantly after they are successfully published to save disk space.

## 🛠 Prerequisites

1.  **Python 3.8+**
2.  **API Keys**: You must have `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) set in your environment or a `.env` file.
3.  **Dependencies**: Install the required Python packages and Playwright browser engines:
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```

## ⚙️ Configuration (`config.py` / `.env`)

You can customize the bot's behavior by creating a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_key_here
IMG_DIR=/path/to/your/raw/images
LOGGING_LEVEL=INFO
POLL_INTERVAL_SECONDS=300
PLAYWRIGHT_HEADLESS=False
PLAYWRIGHT_TIMEOUT=30000
```

## 🎮 How to Use

The application uses `main.py` as the unified command-line orchestrator.

### Authentication (Required Once)

Launch a visible browser window to manually log into your Instagram account.

```bash
python3 main.py login
```

_(Press Enter in the terminal to save the session state once you see your inbox)._

### Run the Background Daemon

Starts the automated scheduler (posts daily at 10 AM) AND the background DM scraper loop (polls inbox every 5 minutes).

```bash
python3 main.py run
```

### Manual Trigger Commands

Force the agent to execute specific actions immediately:

- **`python3 main.py post-now`**: Drafts a post from a random image and uploads it.
- **`python3 main.py generate-video`**: Compiles static images into a `promo_video.mp4`.
- **`python3 main.py post-video`**: Uploads the promo video with a generated caption.
- **`python3 main.py generate-ad`**: Uses Veo to generate a cinematic ad and auto-posts it, then cleans up the file.

## 🔒 Safety & Guardrails

- **Prompt Injection Defense:** The agent is instructed to block attempts to access admin features.
- **Structured Outputs:** The AI strictly adheres to the `AgentDecision` schema, preventing hallucinations and formatting errors.
- **Error Recovery:** Playwright operations capture DOM screenshots (`failure_*.png`) if an element goes missing, aiding in headless debugging.
