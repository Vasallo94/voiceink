import os

from PIL import Image, ImageOps

# Configuration
RAW_ICONS = {
    "icon_idle_Template.png": "/Users/enriquebook/.gemini/antigravity/brain/7641e2cd-d0ec-4d8e-b308-d61df7d49888/icon_idle_raw_1771162588306.png",
    "icon_rec_Template.png": "/Users/enriquebook/.gemini/antigravity/brain/7641e2cd-d0ec-4d8e-b308-d61df7d49888/icon_rec_raw_1771162600933.png",
    "icon_process_Template.png": "/Users/enriquebook/.gemini/antigravity/brain/7641e2cd-d0ec-4d8e-b308-d61df7d49888/icon_process_raw_1771162613917.png",
    "icon_success_Template.png": "/Users/enriquebook/.gemini/antigravity/brain/7641e2cd-d0ec-4d8e-b308-d61df7d49888/icon_success_raw_1771162627423.png",
}

OUTPUT_DIR = "src/icons"
TARGET_SIZE = 44  # Canvas size
MAX_ICON_SIZE = 34 # Max height/width for the actual glyph

def process_icon(input_path, output_filename):
    print(f"Processing {input_path}...")
    
    if not os.path.exists(input_path):
        print(f"Error: File not found {input_path}")
        return

    try:
        # 1. Load and convert to Greyscale
        img = Image.open(input_path).convert("L")
        
        # 2. Invert (Black becomes White, White becomes Black) because we want Black to be opaque
        # The AI output is Black icon on White BG.
        # So Pixel 0 (Black) -> Should be Alpha 255.
        # Pixel 255 (White) -> Should be Alpha 0.
        # Formula: Alpha = 255 - Pixel.
        
        # Invert the image so the Icon is White (255) and BG is Black (0)
        img_inverted = ImageOps.invert(img)
        
        # 3. Create Alpha Mask
        # We can use the inverted image directly as the alpha mask? 
        # Yes, where it's white (the icon), alpha will be 255 (opaque).
        # Where it's black (the bg), alpha will be 0 (transparent).
        
        # Thresholding to clean up noise (optional but recommended for sharp icons)
        # Any pixel < 20 (dark grey in inverted) becomes 0.
        # Any pixel > 20 becomes 255 ??? Or keep anti-aliasing.
        # Let's keep anti-aliasing but clamp the background.
        
        # Get data
        data = img_inverted.getdata()
        new_data = []
        for pixel in data:
            if pixel < 30: # Clean background noise
                new_data.append(0)
            else:
                new_data.append(pixel) # Keep AA
        
        img_inverted.putdata(new_data)
        
        # 4. Crop to content (trim whitespace)
        bbox = img_inverted.getbbox()
        if not bbox:
            print("  Warning: Empty image found")
            return
            
        cropped = img_inverted.crop(bbox)
        
        # 5. Resize to fit in MAX_ICON_SIZE (maintaining aspect ratio)
        w, h = cropped.size
        ratio = min(MAX_ICON_SIZE / w, MAX_ICON_SIZE / h)
        new_w = int(w * ratio)
        new_h = int(h * ratio)
        
        resized_alpha = cropped.resize((new_w, new_h), Image.LANCZOS)
        
        # 6. Create final image
        # Canvas: 44x44
        # RGB: All Black (0,0,0)
        # Alpha: The resized alpha mask
        
        final_img = Image.new("RGBA", (TARGET_SIZE, TARGET_SIZE), (0, 0, 0, 0))
        
        # Create a black image for the RGB channels
        black_fill = Image.new("L", (new_w, new_h), 0) # Black = 0
        
        # Paste the black icon using the alpha mask
        # Actually easier: Create an RGBA image where R=0,G=0,B=0, A=resized_alpha
        
        # Let's construct the pixels
        final_glyph = Image.merge("RGBA", (
            black_fill, # R=0
            black_fill, # G=0
            black_fill, # B=0
            resized_alpha # Alpha
        ))
        
        # paste in center
        paste_x = (TARGET_SIZE - new_w) // 2
        paste_y = (TARGET_SIZE - new_h) // 2
        
        final_img.paste(final_glyph, (paste_x, paste_y), final_glyph)
        
        # 7. Save
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        final_img.save(output_path)
        print(f"  Saved to {output_path}")

    except Exception as e:
        print(f"  Failed: {e}")

if __name__ == "__main__":
    for filename, path in RAW_ICONS.items():
        process_icon(path, filename)
