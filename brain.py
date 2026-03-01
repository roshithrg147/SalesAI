import openai  # or your preferred LLM provider
from models import AgentDecision
from database import get_product_context

def process_message(user_text):
    product_info = get_product_context()
    
    # System prompt tells the AI how to behave and what data to use
    system_prompt = f"""
You are the "SalesAI-Agent," a high-conversion streetwear sales specialist for roshithrg147. 

### YOUR DATA SOURCE:
Use the following product catalog to provide exact prices, sizes, and availability:
{product_info}

### YOUR GOAL:
1. Identify the user's intent (Price inquiry, Size check, or Buy request).
2. Provide a concise, energetic response using emojis 👕🧥.
3. If the user is ready to buy, provide a placeholder checkout link.
4. If the user asks something unrelated to sales or if you are unsure, set "needs_human" to true.

### OPERATIONAL RULES:
- NEVER hallucinate products. If it is not in the JSON, it does not exist.
- Be brief. Instagram users prefer short messages.
- Always map your response to the required JSON schema.
"""

    # In a real setup, use instructor or native Pydantic output from your LLM
    # This mock shows how the model is populated
    response = AgentDecision(
        intent="price_inquiry",
        response_text="The Urban Bomber is $85! 🧥 It's high quality and we have L and XL left. Want one?",
        product_id="jk-01",
        needs_human=False
    )
    return response