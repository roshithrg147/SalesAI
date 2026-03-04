import os
from google import genai
from google.genai import types
from config import setup_logger

logger = setup_logger("test_veo")

api_key = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

logger.info("Listing files...")
files = list(client.files.list())
if not files:
    logger.warning("No files found on Gemini.")
    exit(1)

f1 = files[-1]
logger.info(f"Using file: {f1.name} URI: {f1.uri}")

try:
    source = types.GenerateVideosSource(
        image=f1
    )
    logger.info("Source Image Assigned directly to File object")
except Exception as e:
    logger.error(f"Cannot assign File directly to source.image: {e}")

try:
    ref = types.VideoGenerationReferenceImage(
        reference_type="ASSET",
        image=f1
    )
    logger.info("Reference Assigned directly to File object")
except Exception as e:
    logger.error(f"Cannot assign File directly to reference.image: {e}")
