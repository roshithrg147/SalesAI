import json
import os

def get_product_context():
    # Loads the product list from your JSON file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'products.json')
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    context = "Available Products:\n"
    for category, items in data.items():
        for item in items:
            context += f"- {item['name']} ({item['id']}): ${item['price']}. Sizes: {', '.join(item['sizes'])}. Stock: {item['stock']}\n"
    return context
