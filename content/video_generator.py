# ==========================================
# Developer: Mr. R.
# Project:   HypeMind
# ==========================================

import os
import random
from moviepy import ImageSequenceClip
from db.database import get_product_context

def get_valid_images(img_dir="Img-20260301T182942Z-1-001/Img"):
    if not os.path.exists(img_dir):
        print(f"Directory {img_dir} does not exist.")
        return []
    
    all_files = os.listdir(img_dir)
    # Filter out duplicate labels
    return [os.path.join(img_dir, f) for f in all_files if f.endswith(".jpg") and "(" not in f]

def generate_promotional_video(output_filename="promo_video.mp4", duration=30):
    print(f"Starting video generation. Target duration: {duration}s")
    
    image_paths = get_valid_images()
    
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

if __name__ == "__main__":
    generate_promotional_video()
