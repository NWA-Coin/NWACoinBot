from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder_image(filename, text):
    """Create a basic placeholder image with text."""
    # Create directory if it doesn't exist
    if not os.path.exists("meme_templates"):
        os.makedirs("meme_templates")
        
    # Create a 400x300 image with a gray background
    img = Image.new('RGB', (400, 300), color='gray')
    draw = ImageDraw.Draw(img)
    
    # Add text to the image
    font = ImageFont.load_default()
    draw.text((10, 150), text, fill='white', font=font)
    
    # Save the image
    img.save(f"meme_templates/{filename}")

def main():
    # Create placeholder images for each template
    templates = [
        ("nick_laughing.jpg", "Nick Laughing Template"),
        ("nick_pointing.jpg", "Nick Pointing Template"),
        ("nick_malding.jpg", "Nick Malding Template"),
        ("ice_waiting.jpg", "Ice Waiting Template")
    ]
    
    for filename, text in templates:
        create_placeholder_image(filename, text)
        print(f"Created {filename}")

if __name__ == "__main__":
    main()
