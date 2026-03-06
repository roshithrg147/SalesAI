# ==========================================
# Developer: Mr. R.
# Project:   HypeMind
# ==========================================

import os
import time
import random
from google import genai
from google.genai import types
from google.genai import errors

from config import Config, setup_logger
from content.video_generator import get_valid_images_from_s3

logger = setup_logger("content.gemini_video_ad")

import tempfile

def generate_video_ad(output_filename="video/ad_video.mp4"):
    logger.info("Starting Gemini Video Advertisement Generation...")
    
    # Ensure video directory exists
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    
    api_key = Config.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment. Please set it.")

    # Force the SDK to use the passed GEMINI API key instead of an env GOOGLE_API_KEY
    if 'GOOGLE_API_KEY' in os.environ:
        del os.environ['GOOGLE_API_KEY']
        
    client = genai.Client(api_key=api_key)
        
    with tempfile.TemporaryDirectory() as temp_dir:
        # Fetch exactly 3 random images from S3 into this TemporaryDirectory
        downloaded_img_paths = get_valid_images_from_s3(required_count=3, download_dir=temp_dir)
        
        if len(downloaded_img_paths) < 3:
            logger.error("Not enough images found in S3. Requires at least 3.")
            return None
        uploaded_files = []
        
        max_retries = 3
        base_wait = 5
        
        for attempt in range(max_retries):
            try:
                # The developer API requires uploaded file objects for image, not raw bytes
                image_references = []
                for img_path in downloaded_img_paths:
                    logger.info(f"Uploading {img_path} to Gemini...")
                    uploaded_file = client.files.upload(file=img_path)
                    uploaded_files.append(uploaded_file)
                    
                    # Wait for processing if necessary
                    while uploaded_file.state.name == "PROCESSING":
                        time.sleep(2)
                        uploaded_file = client.files.get(name=uploaded_file.name)
                        
                    image_references.append(
                        types.VideoGenerationReferenceImage(
                            reference_type="ASSET",
                            image=uploaded_file
                        )
                    )

                # Wait briefly before API call (best practice)
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
                        config=types.GenerateVideosConfig(
                             person_generation="ALLOW_ADULT",
                             aspect_ratio="9:16",
                             reference_images=image_references
                        )
                     )
                except errors.APIError as api_err:
                     logger.warning(f"Veo API failed (Billing/Quota limits?): {api_err}")
                     logger.info("Falling back to local static video generation...")
                     from content.video_generator import generate_promotional_video
                     generate_promotional_video(output_filename=output_filename, duration=10)
                     return output_filename
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
                # Clean up uploaded images from Gemini
                logger.info("Cleaning up uploaded files from Gemini...")
                for f in uploaded_files:
                    try:
                        client.files.delete(name=f.name)
                    except Exception as e:
                        logger.warning(f"Failed to delete {f.name}: {e}")
                # Empty array for next loop iteration
                uploaded_files = []

if __name__ == "__main__":
    generate_video_ad()
