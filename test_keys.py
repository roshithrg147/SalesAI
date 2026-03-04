import os
from google import genai
from config import setup_logger

logger = setup_logger("test_keys")

os.environ['GOOGLE_API_KEY'] = 'A'
os.environ['GEMINI_API_KEY'] = 'B'

logger.info("Initializing client...")
client = genai.Client(api_key='C')
logger.info(f"Client initialized with api_key: {getattr(client, 'api_key', 'unknown')}")
