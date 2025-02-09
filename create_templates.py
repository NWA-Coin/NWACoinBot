from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder_image(filename, text, width=800, height=600):
    """Create a basic placeholder image with text."""
    # Create directory if it doesn't exist
    if not os.path.exists("meme_templates"):
        os.makedirs("meme_templates")

    # Create an image with a dark gray background
    img = Image.new('RGB', (width, height), color='#2C2F33')  # Discord-like dark theme
    draw = ImageDraw.Draw(img)

    # Add a simple gradient effect
    for y in range(height):
        alpha = int(255 * (1 - y/height))
        draw.line([(0, y), (width, y)], fill=(255, 255, 255, alpha))

    # Add text to the image
    font = ImageFont.load_default()
    # Calculate text position for center alignment
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2

    # Add text with outline for better visibility
    outline_color = 'black'
    text_color = 'white'
    outline_width = 2

    # Draw text outline
    for adj in range(-outline_width, outline_width+1):
        for adj2 in range(-outline_width, outline_width+1):
            if adj != 0 or adj2 != 0:
                draw.text((text_x+adj, text_y+adj2), text, font=font, fill=outline_color)

    # Draw main text
    draw.text((text_x, text_y), text, font=font, fill=text_color)

    # Save the image with high quality
    img.save(f"meme_templates/{filename}", quality=95)

def main():
    # Create placeholder images for each template with descriptive text
    templates = [
        ("nick_laughing.jpg", "Nick Laughing at LUX Chart 📉"),
        ("nick_pointing.jpg", "Nick Pointing at Scam Exposure 👆"),
        ("nick_malding.jpg", "Nick Exposing LUX Rugpull 🗑️"),
        ("ice_waiting.jpg", "Ice Poseidon Waiting for Recovery ⚰️")
    ]

    for filename, text in templates:
        create_placeholder_image(filename, text)
        print(f"Created {filename}")

if __name__ == "__main__":
    main()