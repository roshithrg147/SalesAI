# SalesAI Director: Streetwear Social Media & Sales Agent

Welcome to **SalesAI**, your AI-powered lead strategist for streetwear social media and direct message sales.

This project leverages the **Gemini 2.5 Flash API** to generate high-converting Instagram posts, and **Playwright** to automate their publication on your account. The AI acts as your "SalesAI Director," possessing dual identities tailored to distinct tasks.

## 🚀 Key Features

### 1. The Dual-Role Agent Architecture

The core logic resides in `brain.py` and `post_generator.py`, where the AI receives sophisticated instructions:

- **Sales Agent (DM Mode):** Answers customer DMs regarding price, sizing, and stock using a Ground Truth JSON catalog (`products.json`). Focuses on converting inquiries via checkout URLs and flags complex human interactions.
- **Content Creator (Post Mode):** Analyzes raw product images to generate viral Instagram captions following the 'AIDA' (Attention, Interest, Desire, Action) framework, specific hashtags, and the brand's energetic, emoji-friendly voice.

### 2. Instagram Automation

Built natively with Playwright (`ig_poster.py`), the program logs into Instagram, saves the session securely in an `ig_session` directory, and drives the browser UI to upload images, write captions, and publish posts—entirely hands-free.

### 3. Automated Daily Publishing Loop

The `scheduler.py` runs an infinite loop that drafts a post (random image + Gemini caption) and publishes it via Playwright once every 24 hours.

## 🛠 Prerequisites

1.  **Python 3.8+**
2.  **Google Gemini API Key**: Set as an environment variable (`export GOOGLE_API_KEY='your-key-here'`).
3.  **Playwright Browsers**: Ensure Playwright is installed (`pip install playwright` and `playwright install`).
4.  **Product Data**: Make sure the `products.json` file is populated (via `generate_db.py`) and images exist in `Img-20260301T182942Z-1-001/Img`.

## 🎮 How to Use

The application uses `main.py` as the unified entry point. You must **always authenticate first** before attempting to post.

### Step 1: Login (Required once)

Launch a visible browser window where you can manually log into your Instagram account. Your session data will be saved so you won't have to log in again.

```bash
python3 main.py login
```

_(After logging in, press Enter in the terminal to save the session)._

### Step 2: Instant Test Post

Run a single generation and upload cycle to verify the Playwright flow and Gemini captions.

```bash
python3 main.py post-now
```

### Step 3: Start the Daily Scheduler

Launch the background job that will continuously run a post generation and upload cycle every 24 hours. This terminal must be left open (or run in a background daemon like `screen` or `tmux`).

```bash
python3 main.py schedule
```

## 🔒 Safety & Guardrails

- **Prompt Injection Defense:** The agent is instructed to block attempts to access admin features or change instructions.
- **No Hallucinations:** The agent is explicitly told to rely _only_ on the provided `products.json` data and to flag humans for missing stock.
