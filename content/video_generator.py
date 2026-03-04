# ==========================================
# Developer: Mr. R.
# Project:   HypeMind
# ==========================================

import os
import random
from moviepy import ImageSequenceClip
from db.database import get_product_context

import tempfile
import uuid
import boto3
from config import Config

def get_valid_images_from_s3(required_count=15):
    bucket_name = Config.S3_BUCKET
    s3_client = boto3.client('s3')
    
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' not in response:
            print(f"S3 Bucket {bucket_name} is empty or inaccessible.")
            return []
            
        all_files = [obj['Key'] for obj in response['Contents']]
    except Exception as e:
        print(f"Failed to list objects in S3 bucket {bucket_name}: {e}")
        return []

    # Filter for jpegs and exclude duplicates
    unique_files = [f for f in all_files if f.endswith(".jpg") and "(" not in f]
    
    if not unique_files:
        print(f"No valid images found in S3 bucket {bucket_name}")
        return []
    
    # Download to standard ephemeral storage
    temp_dir = os.path.join(tempfile.gettempdir(), "hypemind_video")
    os.makedirs(temp_dir, exist_ok=True)
    
    selected_keys = random.sample(unique_files, min(len(unique_files), required_count))
    downloaded_paths = []
    
    for key in selected_keys:
        temp_img_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{os.path.basename(key)}")
        try:
            s3_client.download_file(bucket_name, key, temp_img_path)
            downloaded_paths.append(temp_img_path)
        except Exception as e:
            print(f"Failed to download {key} from S3: {e}")
            
    return downloaded_paths

def generate_promotional_video(output_filename="promo_video.mp4", duration=30):
    print(f"Starting video generation. Target duration: {duration}s")
    
    time_per_image = 2
    required_images = duration // time_per_image
    
    image_paths = get_valid_images_from_s3(required_count=required_images)
    
    if not image_paths:
        print("No valid images found to generate a video.")
        return
    
    # Randomize images to make it dynamic
    random.shuffle(image_paths)
    
    # Determine how many images we need. Let's showcase each image for 2 seconds.
    time_per_image = 2
    required_images = duration // time_per_image
    
    # If we have less images than required, we'll loop them
    selected_images = []
    while len(selected_images) < required_images:
        selected_images.extend(image_paths)
    
    # Trim to exact required number of images
    selected_images = selected_images[:required_images]
    
    print(f"Selected {len(selected_images)} images for the video.")
    
    # Load all images using PIL, resize them to 1080x1080 to ensure uniform size as required by MoviePy
    import numpy as np
    from PIL import Image

    print("Resizing images to uniform size (1080x1080)...")
    target_size = (1080, 1080)
    image_arrays = []
    
    for img_path in selected_images:
        try:
            with Image.open(img_path) as img:
                # Convert to RGB to avoid issues with RGBA/grayscale
                img = img.convert("RGB")
                # Resize image
                img_resized = img.resize(target_size, Image.Resampling.LANCZOS)
                image_arrays.append(np.array(img_resized))
        except Exception as e:
            print(f"Error processing {img_path}: {e}")

    if not image_arrays:
        print("No valid images could be processed.")
        return

    fps = 1 / time_per_image
    clip = ImageSequenceClip(image_arrays, fps=fps)
    
    # Save the result to a file
    print(f"Exporting video to {output_filename}...")
    try:
        clip.write_videofile(
            output_filename, 
            fps=24, 
            codec="libx264", 
            audio=False,
            ffmpeg_params=['-pix_fmt', 'yuv420p']
        )
        print("Video generation complete!")
    except Exception as e:
        print(f"Failed to generate video: {e}")
    finally:
        # Cleanup temporary images
        for img_path in image_paths:
            try:
                if os.path.exists(img_path):
                    os.remove(img_path)
            except Exception as e:
                print(f"Failed to clean up {img_path}: {e}")

if __name__ == "__main__":
    generate_promotional_video()
