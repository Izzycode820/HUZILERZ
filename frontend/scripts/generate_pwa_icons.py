from PIL import Image
import os
import shutil

# Paths
source_path = "C:/Users/chomo/.gemini/antigravity/brain/70def3c4-4ddf-4263-987c-df0d62b9cee4/huzilaz_app_icon_1767819778082.png"
output_dir = "c:/S.T.E.V.E/V2/HUZILERZ/frontend/public/icons"

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Define sizes
sizes = {
    "icon-512x512.png": (512, 512),
    "icon-192x192.png": (192, 192),
    "apple-touch-icon.png": (180, 180)
}

try:
    # Open source image
    with Image.open(source_path) as img:
        print(f"Opened source image: {source_path}")
        
        for filename, size in sizes.items():
            # Resize
            resized_img = img.resize(size, Image.Resampling.LANCZOS)
            
            # Save
            output_path = os.path.join(output_dir, filename)
            resized_img.save(output_path)
            print(f"Generated {filename} ({size[0]}x{size[1]})")

    print("✅ All icons generated successfully!")

except Exception as e:
    print(f"❌ Error generating icons: {str(e)}")
