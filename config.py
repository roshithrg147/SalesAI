# ==========================================
# Developer: Mr. R.
# Project:   HypeMind
# ==========================================

import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Central Configuration
class Config:
    # API Keys
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or GOOGLE_API_KEY
    
    # AWS Settings
    S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "hypemind-assets")
    PRODUCTS_TABLE = os.environ.get("DYNAMODB_PRODUCTS", "HypeMindProducts")
    INQUIRIES_TABLE = os.environ.get("DYNAMODB_INQUIRIES", "HypeMindInquiries")
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    IMG_DIR = os.environ.get("IMG_DIR", os.path.join(BASE_DIR, "/home/norwing/Pictures/Download/Img-20260302T042252Z-1-001"))
    
    # SECURITY NOTE: In AWS/production (Lambda/EC2), IG_SESSION_DIR is synced using S3 zip extraction.
    # It must be mounted to a writable location like /tmp/ig_session
    IG_SESSION_DIR = os.environ.get("IG_SESSION_DIR", "/tmp/ig_session")
    
    DB_DIR = os.path.join(BASE_DIR, 'db')
    PRODUCTS_JSON_PATH = os.path.join(DB_DIR, 'products.json')
    
    # App Settings
    LOGGING_LEVEL = os.environ.get("LOGGING_LEVEL", "INFO")
    POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "300"))
    MAX_DMS_PER_CYCLE = int(os.environ.get("MAX_DMS_PER_CYCLE", "5"))
    
    # Playwright Settings
    PLAYWRIGHT_HEADLESS = os.environ.get("PLAYWRIGHT_HEADLESS", "False").lower() in ('true', '1', 't')
    PLAYWRIGHT_TIMEOUT = int(os.environ.get("PLAYWRIGHT_TIMEOUT", "60000"))

# Central Logger Setup
def setup_logger(name):
    logger = logging.getLogger(name)
    level = getattr(logging, Config.LOGGING_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if setup_logger is called multiple times
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
    return logger

logger = setup_logger("HypeMind")
