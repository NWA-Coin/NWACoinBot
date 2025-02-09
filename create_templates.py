from PIL import Image, ImageDraw, ImageFont
import os
import logging

# Set up logging
logger = logging.getLogger('discord_bot')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def create_placeholder_image(filename, text, width=800, height=600):
    """Create a basic placeholder image with text."""
    try:
        # Create directory if it doesn't exist
        if not os.path.exists("meme_templates"):
            logger.info("Creating meme_templates directory")
            os.makedirs("meme_templates")

        # Create an image with a dark gray background
        logger.debug(f"Creating image: {filename} ({width}x{height})")
        img = Image.new('RGB', (width, height), color='#2C2F33')  # Discord-like dark theme
        draw = ImageDraw.Draw(img)

        # Add a simple gradient effect
        logger.debug("Adding gradient effect")
        for y in range(height):
            alpha = int(255 * (1 - y/height))
            draw.line([(0, y), (width, y)], fill=(255, 255, 255, alpha))

        # Try to load a better font, fall back to default if needed
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
            logger.debug("Loaded DejaVuSans-Bold font")
        except Exception as e:
            logger.warning(f"Failed to load custom font: {str(e)}. Using default.")
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

        logger.debug("Adding text with outline")
        # Draw text outline
        for adj in range(-outline_width, outline_width+1):
            for adj2 in range(-outline_width, outline_width+1):
                if adj != 0 or adj2 != 0:
                    draw.text((text_x+adj, text_y+adj2), text, font=font, fill=outline_color)

        # Draw main text
        draw.text((text_x, text_y), text, font=font, fill=text_color)

        # Save the image with high quality
        output_path = f"meme_templates/{filename}"
        logger.info(f"Saving image to: {output_path}")
        img.save(output_path, quality=95)

        # Verify file was created successfully
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(f"Successfully created {filename} (size: {file_size} bytes)")
            return True
        else:
            logger.error(f"Failed to verify creation of {filename}")
            return False

    except Exception as e:
        logger.error(f"Error creating placeholder image {filename}: {str(e)}")
        logger.exception("Full traceback:")
        return False

def main():
    # Create placeholder images for each template with descriptive text
    templates = [
        ("nick_laughing.jpg", "Nick Laughing at LUX Chart 📉", 800, 600),
        ("nick_pointing.jpg", "Nick Pointing at Scam Exposure 👆", 800, 600),
        ("nick_malding.jpg", "Nick Exposing LUX Rugpull 🗑️", 800, 600),
        ("ice_waiting.jpg", "Ice Poseidon Waiting for Recovery ⚰️", 800, 600)
    ]

    success_count = 0
    for filename, text, width, height in templates:
        if create_placeholder_image(filename, text, width, height):
            success_count += 1
        else:
            logger.error(f"Failed to create template: {filename}")

    logger.info(f"Template creation complete. Successfully created {success_count}/{len(templates)} templates.")

if __name__ == "__main__":
    main()