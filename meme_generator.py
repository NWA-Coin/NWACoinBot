import os
import random
from PIL import Image, ImageDraw, ImageFont
import requests
from datetime import datetime
import logging

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot')

# Chart-focused roast templates with more aggressive NWA content
MEME_TEMPLATES = [
    {
        "image": "nick_laughing.jpg",
        "default_text": "LUX chart looking like Tino's mom's OF subscriber count... straight down! 📉💦",
        "price_text": lambda price: f"Another -99% day at ${price:.8f}! NWA KEEPS WINNING! 🔥",
        "text_position": (10, 10)
    },
    {
        "image": "nick_pointing.jpg", 
        "default_text": "Pointing at the exact moment Tino rugged his bitchass coin! Chart's dead! 👆💀",
        "price_text": lambda price: f"${price:.8f}? Even shitcoins perform better! NGMI! 🤡",
        "text_position": (10, 10)
    },
    {
        "image": "nick_malding.jpg",
        "default_text": "When you zoom out and LUX chart is just one big rugpull! Complete disaster! 📉🗑️",
        "price_text": lambda price: f"Down to ${price:.8f}! Time for more copium! 😭",
        "text_position": (10, 10)
    },
    {
        "image": "ice_waiting.jpg",
        "default_text": "Still waiting for that V-shaped recovery! Chart's flatter than Tino's brain! ⚰️🧠",
        "price_text": lambda price: f"${price:.8f} and still dropping! Pure fucking garbage! 💩",
        "text_position": (10, 10)
    }
]

# Chart-focused fallback roasts
CHART_ROASTS = [
    "Chart's looking like Tino's credibility... non-existent! 📉💀",
    "More red candles than Tino's mom's OF studio! Complete bloodbath! 🕯️💦",
    "LUX chart sponsored by gravity... straight to fucking zero! ⬇️🗑️",
    "Even SafeMoon had better price action! Pure fucking dogshit! 🐕💩",
    "Chart's dead like Tino's trading career! NWA stays winning! 🏆😭"
]

def get_lux_price():
    """Get current LUX price from CoinGecko."""
    try:
        # For testing, return a mock price that's significantly lower than entry
        # This ensures we can test the meme generation with realistic crash percentages
        test_price = 0.00015  # 99% crash from 0.015
        logger.info(f"Using test price: ${test_price:.8f}")
        return test_price

        # TODO: Uncomment below for production use
        # url = "https://api.coingecko.com/api/v3/simple/price"
        # params = {
        #     "ids": "lux-protocol",
        #     "vs_currencies": "usd"
        # }
        # response = requests.get(url, params=params)
        # data = response.json()
        # price = data.get("lux-protocol", {}).get("usd", 0)
        # return price
    except Exception as e:
        logger.error(f"Error fetching LUX price: {str(e)}")
        return 0

def generate_text_only_meme():
    """Generate a text-only meme focused on chart roasts."""
    logger.info("Generating text-only meme")
    price = get_lux_price()
    entry_price = 0.015  # NWA entry price when they started attacking

    # Pick a random chart roast
    base_roast = random.choice(CHART_ROASTS)
    logger.info(f"Selected base roast: {base_roast}")

    if price == 0:
        price_text = "LUX = $0 (COMPLETELY FUCKING DEAD) 💀🪦"
        crash_percent = 100
    else:
        price_text = f"Down to ${price:.8f} and still dropping! 📉"
        crash_percent = ((entry_price - price) / entry_price) * 100

    text = f"{base_roast}\n{price_text}\n"
    text += f"NWA dumped it {crash_percent:.1f}%! Get fucked Tino! 🖕😭"

    logger.info(f"Generated text-only meme:\n{text}")
    return text

def generate_meme():
    """Generate a meme about LUX's chart performance."""
    try:
        logger.info("Starting meme generation")

        # Get current price
        price = get_lux_price()
        entry_price = 0.015  # NWA entry price when they started attacking

        # Check if meme templates directory exists
        if not os.path.exists("meme_templates"):
            logger.warning("Meme templates directory not found")
            return generate_text_only_meme()

        # Select random template
        template = random.choice(MEME_TEMPLATES)
        logger.info(f"Selected template: {template['image']}")

        image_path = os.path.join("meme_templates", template["image"])
        logger.info(f"Using image path: {image_path}")

        # If image template isn't available, return text-only meme
        if not os.path.exists(image_path):
            logger.warning(f"Template image not found: {image_path}")
            return generate_text_only_meme()

        # Try to load font
        try:
            font = ImageFont.load_default()
            logger.info("Loaded default font successfully")
        except Exception as e:
            logger.error(f"Error loading font: {str(e)}")
            return generate_text_only_meme()

        # Create meme
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        logger.info(f"Opened image: {image_path} with size {img.size}")

        # Calculate crash percentage
        crash_percent = 100 if price == 0 else ((entry_price - price) / entry_price) * 100
        logger.info(f"Calculated crash percentage: {crash_percent:.1f}%")

        # Generate price-based text with savage chart-focused messages
        if price == 0:
            text = (f"{template['default_text']}\n"
                   f"LUX = $0 (Chart's flatter than Tino's OF income!) 🗑️💀\n"
                   f"NWA dumped it {crash_percent:.1f}%! Complete destruction! 💀")
        else:
            text = (f"{template['default_text']}\n"
                   f"{template['price_text'](price)}\n"
                   f"NWA dumped it {crash_percent:.1f}%! Chart's in the dirt! 📉")

        logger.info(f"Generated overlay text:\n{text}")

        # Add text to image with black outline for better visibility
        x, y = template["text_position"]
        draw.text((x, y), text, font=font, fill='white', stroke_width=2, stroke_fill='black')
        logger.info(f"Added text at position ({x}, {y})")

        # Save temporary file
        temp_path = f"temp_meme_{datetime.now().timestamp()}.png"
        img.save(temp_path)
        logger.info(f"Saved meme to: {temp_path}")
        return temp_path

    except Exception as e:
        logger.error(f"Error generating meme: {str(e)}")
        return generate_text_only_meme()