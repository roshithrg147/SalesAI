import os
from google import genai
import logging

logging.basicConfig(level=logging.INFO)

os.environ['GOOGLE_API_KEY'] = 'A'
os.environ['GEMINI_API_KEY'] = 'B'

print("Initializing client...")
client = genai.Client(api_key='C')
print("Client initialized with api_key:", getattr(client, 'api_key', 'unknown'))
