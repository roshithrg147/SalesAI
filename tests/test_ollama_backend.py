import os
import sys

# Add the project root to path so we can import
sys.path.append(os.path.abspath(os.getcwd()))

# Set the environment variable for this run
os.environ["AI_BACKEND"] = "OLLAMA"
os.environ["S3_BUCKET_NAME"] = "dummy" # Required by config.py
os.environ["GOOGLE_API_KEY"] = "dummy" # Required by config.py

from ai.brain import process_message

test_msg = "How much for the black hoodie?"
print(f"Testing message: {test_msg}")
decision = process_message(test_msg)
print("\n--- AGENT DECISION ---")
print(decision.model_dump_json(indent=2))
