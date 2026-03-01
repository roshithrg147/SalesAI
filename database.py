import json

def get_product_context():
    # Loads the product list from your JSON file
    with open('products.json', 'r') as f:
        data = json.load(f)
    
    context = "Available Products:\n"
    for category, items in data.items():
        for item in items:
            context += f"- {item['name']} ({item['id']}): ${item['price']}. Sizes: {', '.join(item['sizes'])}. Stock: {item['stock']}\n"
    return context