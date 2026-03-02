# ==========================================
# Developer: Mr. R.
# Project:   HypeMind
# ==========================================

import os
import time
import random
from google import genai
from google.genai import types

from config import Config, setup_logger
logger = setup_logger("content.gemini_video_ad")

def generate_video_ad(output_filename="video/ad_video.mp4"):
    logger.info("Starting Gemini Video Advertisement Generation...")
    
    # Ensure video directory exists
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    
    api_key = Config.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment. Please set it.")

    client = genai.Client(api_key=api_key)
    
    img_dir = Config.IMG_DIR
    if not os.path.exists(img_dir):
        logger.error(f"Directory {img_dir} does not exist.")
        return None
        
    all_files = [f for f in os.listdir(img_dir) if f.endswith(".jpg") and "(" not in f]
    
    if len(all_files) < 3:
        logger.error("Not enough images found. Requires at least 3.")
        return None
        
    # Select exactly 3 random images
    selected_images = random.sample(all_files, 3)
    uploaded_files = []
    
    max_retries = 3
    base_wait = 5
    
    for attempt in range(max_retries):
        try:
            # Upload the selected images
            logger.info(f"Uploading 3 images to Gemini (Attempt {attempt+1}/{max_retries})...")
            for img in selected_images:
                img_path = os.path.join(img_dir, img)
                logger.info(f"  Uploading: {img}")
                uploaded_file = client.files.upload(file=img_path)
                uploaded_files.append(uploaded_file)
                
            # Wait briefly for files to be processed by Gemini (best practice)
            time.sleep(3)
            
            prompt = """
            [Role/Persona]: Act as an expert advertisement filmmaker and cinematic director.
            [Context]: I have uploaded high-quality static product images of Streetwear Clothing.
            [Objective]: Generate a 5-10 second, high-end commercial video ad aimed at social media (TikTok/Instagram Reels). The video should feel premium, engaging, and persuasive (luxurious, cozy).
            [Instructions]:
            Motion: Animate the scene with a slow, smooth, cinematic camera dolly-in.
            Product Focus: The streetwear should remain in crisp, sharp focus while the background has a gentle parallax, soft-focus effect.
            Details: Add subtle, realistic environmental motion (e.g. dramatic lighting shifts, floating dust particles, fabric gently moving in a soft breeze).
            Lighting: Use bright, high-contrast studio lighting with warm golden hour tones to make the product look premium.
            Composition: 9:16 vertical format, close-up shot of the product as the main subject.
            Style: 4k, hyper-realistic, professional advertising aesthetic, slow motion.
            """
            
            logger.info("Sending generation request to Veo (Wait... this might take a couple of minutes)...")
            # Ensure we use a model that supports video generation (Veo)
            # We must use generate_videos method
            try:
                 operation = client.models.generate_videos(
                    model='veo-2.0-generate-001',
                    prompt=prompt,
                    source_images=uploaded_files,
                    config=types.GenerateVideosConfig(
                         person_generation="ALLOW_ADULT",
                         aspect_ratio="9:16",
                         output_mime_type="video/mp4"
                    )
                 )
            except AttributeError:
                 logger.warning("Your google-genai client does not seem to support `generate_videos` directly.")
                 logger.warning("Attempting generation using standard generate_content (this might fail if model isn't designed for it).")
                 # Fallback attempt
                 response = client.models.generate_content(
                    model='veo-2.0-generate-001',
                    contents=uploaded_files + [prompt]
                 )
                 logger.info(f"Fallback response: {response.text}")
                 return None
                 
            # Wait for the operation to complete
            while not operation.done:
                 logger.info("Waiting for generation to complete...")
                 time.sleep(10)
                 operation = client.operations.get(operation=operation)
                 
            if operation.error:
                 logger.error(f"Generation failed: {operation.error}")
                 raise ValueError("Generation error from API")
                 
            logger.info("Video generated! Downloading...")
            # Get the generated video payload
            generated_video_url = operation.response.generated_videos[0].video.uri
            
            import urllib.request
            urllib.request.urlretrieve(generated_video_url, output_filename)
            
            logger.info(f"Video saved as {output_filename}")
            return output_filename
            
        except Exception as e:
            logger.error(f"Error generating video ad: {e}")
            if attempt < max_retries - 1:
                sleep_time = base_wait * (2 ** attempt)
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error("Max retries exceeded. Video Ad generation failed.")
                return None
            
        finally:
            # Clean up uploaded images
            logger.info("Cleaning up uploaded files...")
            for f in uploaded_files:
                try:
                    client.files.delete(name=f.name)
                except Exception as e:
                    logger.warning(f"Failed to delete {f.name}: {e}")
            # Empty array for next loop iteration
            uploaded_files = []

if __name__ == "__main__":
    generate_video_ad()
