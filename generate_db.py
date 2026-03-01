import os
import json
from google import genai

def main():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("GOOGLE_API_KEY not found in environment. Please set it.")
        return

    client = genai.Client(api_key=api_key)
    
    img_dir = "Img-20260301T182942Z-1-001/Img"
    all_files = os.listdir(img_dir)
    # Filter out duplicate labels like (1), (2)
    unique_files = [f for f in all_files if f.endswith(".jpg") and "(" not in f]
    unique_files.sort()
    
    print(f"Found {len(unique_files)} unique images.")
    
    files_to_upload = [os.path.join(img_dir, f) for f in unique_files]
    uploaded_files = []
    
    print("Uploading images to Gemini...")
    for f in files_to_upload:
        try:
            uploaded_file = client.files.upload(file=f)
            uploaded_files.append(uploaded_file)
        except Exception as e:
            print(f"Failed to upload {f}: {e}")
            
    print("Generating product catalog JSON...")
    
    prompt = """
    You are an expert cataloger. I have provided you with several images of clothing items.
    Extract the product information from all the images and return a JSON object with this exact structure:
    {
      "t-shirts": [
        {"id": "ts-01", "name": "...", "price": 25, "sizes": ["S", "M", "L"], "stock": 15}
      ],
      "jackets": [
        {"id": "jk-01", "name": "...", "price": 85, "sizes": ["L", "XL"], "stock": 2}
      ],
      "other_categories": []
    }
    Make sure to:
    1. Invent an appropriate short name for each unique item based on its design/color if not explicitly written.
    2. Extract price if visible in the image, otherwise guess a reasonable price (e.g. 20-50 for t-shirts, 50-100 for jackets).
    3. Include common sizes ["S", "M", "L", "XL"] as appropriate.
    4. Invent a stock number between 5 and 50.
    5. Generate unique IDs for each item (e.g., ts-01, ts-02... jk-01, jk-02...).
    6. Combine identical designs into a single product if it appears in multiple images, or treat each image's item as a unique product.
    ONLY output valid JSON. Do not include markdown codeblocks or extra text.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=uploaded_files + [prompt],
        )
        
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
            
        print("Writing to products.json...")
        with open('products.json', 'w') as f:
            f.write(text)
        print("Successfully generated products.json")
    except Exception as e:
        print(f"Error generating JSON: {e}")

if __name__ == "__main__":
    main()
