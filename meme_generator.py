import os
import random
from PIL import Image, ImageDraw, ImageFont
import requests
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger('discord_bot')

# Meme templates with savage NWA content
MEME_TEMPLATES = [
    {
        "image": "nick_laughing.jpg",
        "default_text": "When Tino's mom finds out LUX dumped harder than her OnlyFans! 🤣💀",
        "text_position": (10, 10)
    },
    {
        "image": "nick_pointing.jpg", 
        "default_text": "NWA spotting another Tino rugpull incoming! Watch this fraud run! 👆🏃",
        "text_position": (10, 10)
    },
    {
        "image": "nick_malding.jpg",
        "default_text": "Tino when Nick exposes his bitchass on stream again! 🤡🖕",
        "text_position": (10, 10)
    },
    {
        "image": "ice_waiting.jpg",
        "default_text": "Ice's community waiting for LUX to not be complete dogshit (impossible) ❌💩",
        "text_position": (10, 10)
    }
]

def get_lux_price():
    """Get current LUX price from CoinGecko."""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "lux-protocol",
            "vs_currencies": "usd"
        }
        response = requests.get(url, params=params)
        data = response.json()
        price = data.get("lux-protocol", {}).get("usd", 0)
        return price
    except Exception as e:
        logger.error(f"Error fetching LUX price: {str(e)}")
        return 0

def generate_text_only_meme():
    """Generate a text-only meme when images are unavailable."""
    template = random.choice(MEME_TEMPLATES)
    price = get_lux_price()

    if price == 0:
        return f"{template['default_text']}\nLUX = $0 (REKT AF like Tino's reputation) 🗑️💀"
    else:
        return f"{template['default_text']}\nLUX = ${price:.8f} (Another L for this fraud) 🖕🤡"

def generate_meme():
    """Generate a meme with current LUX price."""
    try:
        # Get current price
        price = get_lux_price()

        # Check if meme templates directory exists
        if not os.path.exists("meme_templates"):
            logger.warning("Meme templates directory not found")
            return None

        # Select random template
        template = random.choice(MEME_TEMPLATES)
        image_path = os.path.join("meme_templates", template["image"])

        # If image template isn't available, return text-only meme
        if not os.path.exists(image_path):
            logger.warning(f"Template image not found: {image_path}")
            return generate_text_only_meme()

        # Try to load font
        try:
            font = ImageFont.load_default()
        except Exception as e:
            logger.error(f"Error loading font: {str(e)}")
            return generate_text_only_meme()

        # Create meme
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)

        # Generate price-based text with savage messages
        if price == 0:
            text = f"{template['default_text']}\nLUX = $0 (REKT AF like Tino's reputation) 🗑️💀"
        else:
            text = f"{template['default_text']}\nLUX = ${price:.8f} (Another L for this fraud) 🖕🤡"

        # Add text to image
        x, y = template["text_position"]
        draw.text((x, y), text, font=font, fill='white', stroke_width=2, stroke_fill='black')

        # Save temporary file
        temp_path = f"temp_meme_{datetime.now().timestamp()}.png"
        img.save(temp_path)
        return temp_path

    except Exception as e:
        logger.error(f"Error generating meme: {str(e)}")
        return generate_text_only_meme()