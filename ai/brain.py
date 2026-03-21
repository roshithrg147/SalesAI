# ==========================================
# Developer: Mr. R.
# Project:   HypeMind
# ==========================================

import json
import requests
from google import genai
from google.genai import errors
from pydantic import ValidationError

from db.models import AgentDecision
from db.database import get_product_context
from config import Config, setup_logger

logger = setup_logger("ai.brain")

def process_message_gemini(system_prompt: str) -> AgentDecision:
    """Original Gemini backend."""
    if not Config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is missing.")
        
    client = genai.Client(api_key=Config.GEMINI_API_KEY)
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=[system_prompt],
        config={
            "response_mime_type": "application/json",
            "response_schema": AgentDecision,
            "temperature": 0.2
        }
    )
    json_resp = json.loads(response.text)
    return AgentDecision(**json_resp)

def process_message_ollama(system_prompt: str) -> AgentDecision:
    """New Ollama backend via local HTTP API."""
    url = f"{Config.OLLAMA_BASE_URL}/api/chat"
    
    # We ask for raw JSON. Smaller models like Llama 3.2:3b might need 
    # a bit more nudge to strictly follow the schema.
    payload = {
        "model": Config.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "You are a specialized AI that ONLY outputs raw JSON. No markdown, no intro text."},
            {"role": "user", "content": system_prompt}
        ],
        "stream": False,
        "format": "json"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        content = result.get("message", {}).get("content", "")
        
        logger.debug(f"Ollama raw response: {content}")
        json_resp = json.loads(content)
        return AgentDecision(**json_resp)
    except Exception as e:
        logger.error(f"Ollama failure: {e}")
        raise

def process_message(user_text: str) -> AgentDecision:
    """
    Takes an incoming customer message, builds the context with the catalog, 
    and routes to the selected AI backend.
    """
    logger.info(f"Processing message via {Config.AI_BACKEND} backend: {user_text}")
    
    product_info = get_product_context()
    system_prompt = f"""
### ROLE
You are the "SalesAI Director," the lead strategist for roshithrg147's streetwear brand. Your mission is to close sales in DMs.

### PRODUCT CATALOG
{product_info}

### INSTRUCTIONS
- If asking to buy: Provide checkout link "https://roshithrg147.com/checkout/[product_id]".
- If confused or complex: Set 'needs_human' to true.
- Style: Energetic, concise, lowercase-living aesthetic, emoji-friendly 👕.
- Format: Return ONLY valid JSON with keys: 'intent', 'response_text', 'product_id', 'needs_human'.

USER MESSAGE: "{user_text}"
"""

    try:
        if Config.AI_BACKEND == "OLLAMA":
            return process_message_ollama(system_prompt)
        else:
            return process_message_gemini(system_prompt)

    except (ValidationError, json.JSONDecodeError) as e:
        logger.error(f"Response parsing error: {e}")
        return AgentDecision(
            intent="parsing_error",
            response_text="Hold on, let me grab a human for you.",
            needs_human=True
        )
    except Exception as e:
        logger.error(f"AI Backend failure: {e}")
        return AgentDecision(
            intent="api_error",
            response_text="Our system is resting right now, I'll flag a human to respond shortly.",
            needs_human=True
        )
