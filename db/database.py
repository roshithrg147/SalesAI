# ==========================================
# Developer: Mr. R.
# Project:   HypeMind
# ==========================================

import json
from config import Config, setup_logger

logger = setup_logger("db.database")

def get_product_context(filter_category=None):
    """
    Loads the product list from JSON.
    Optionally filters by category to save LLM context window tokens.
    """
    try:
        with open(Config.PRODUCTS_JSON_PATH, 'r') as f:
            data = json.load(f)
            
        context = "Available Products:\n"
        for category, items in data.items():
            if filter_category and category != filter_category:
                continue
                
            for item in items:
                context += f"- {item['name']} ({item['id']}): ${item['price']}. Sizes: {', '.join(item['sizes'])}. Stock: {item['stock']}\n"
                
        return context
    except Exception as e:
        logger.error(f"Failed to load products database: {e}")
        return "Warning: Product context unavailable."
