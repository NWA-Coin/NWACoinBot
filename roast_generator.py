import random
from PIL import Image, ImageDraw, ImageFont
import io
import os
import requests

# Predefined roast templates
ROAST_TEMPLATES = [
    "Lux coin is so slow, Internet Explorer feels fast in comparison! 🐌",
    "Lux's market cap is like my dating life - constantly disappointing! 📉",
    "Lux coin is more unstable than my coffee addiction before morning meetings! ☕",
    "Lux's blockchain is like a maze - even the developers got lost in it! 🌀",
    "Lux coin has more forks than a restaurant supply store! 🍴",
    "Lux's white paper has more plot twists than a soap opera! 📺",
    "Lux coin is so volatile, roller coasters look stable! 🎢",
    "Investing in Lux is like trying to catch falling knives... blindfolded! 🔪",
    "Lux's roadmap is more mysterious than Area 51! 👽",
    "Lux coin has more red flags than a flag factory during Valentine's Day! ❤️",
    "$LUX's trading volume is lower than my self-esteem after a breakup! 💔",
    "$LUX chart looks like a heart monitor during a horror movie marathon! 📈",
    "$LUX token holders are so desperate, they're applying at McDonald's! 🍔",
    "$LUX's marketing team must be using Internet Explorer on Windows 95! 🖥️",
    "$LUX is so worthless, even LUNA holders feel better about themselves! 🌕",
    "$LUX's liquidity is drier than my DMs on a dating app! 💦",
    "$LUX team promises updates slower than George R.R. Martin writes books! 📚",
    "$LUX token is more useless than a screen door on a submarine! 🚢",
    "$LUX's market analysis looks like a toddler's crayon masterpiece! 🖍️",
    "$LUX devs must be using carrier pigeons for communication! 🐦",
    "$LUX's smart contracts are dumber than a bag of rocks! 🪨",
    "$LUX holders need more copium than a failed NFT project! 🎨",
    "$LUX's security is about as robust as a chocolate teapot! ☕",
    "$LUX chart resembles my EKG after seeing my portfolio! 💀",
    "$LUX staking rewards are smaller than an ant's lunch! 🐜"
]

def generate_roast():
    """Generate a random roast from predefined templates."""
    return random.choice(ROAST_TEMPLATES)

def get_lux_price_data():
    """Fetch live $LUX token data."""
    try:
        # Use CoinGecko API for LUX price data
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "luxor",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_7d_change": "true"
        }
        response = requests.get(url, params=params)
        data = response.json()

        if "luxor" in data:
            price = data["luxor"]["usd"]
            change_7d = data["luxor"].get("usd_7d_change", -95.0)  # Default to -95% if not available

            # Format price with appropriate decimals
            if price < 0.01:
                price_str = f"${price:.8f}"
            else:
                price_str = f"${price:.6f}"

            change_str = f" (7d: {change_7d:+.1f}%)"

            return {
                "price": price,
                "price_str": price_str,
                "change_7d": change_7d,
                "change_str": change_str
            }
        return None
    except Exception as e:
        print(f"Error fetching price: {str(e)}")
        return None

def create_meme_image(text):
    """Create a meme image with the given text and live $LUX data."""
    width = 1200
    height = 800
    image = Image.new('RGB', (width, height), color='#1a1a1a')
    draw = ImageDraw.Draw(image)

    # Draw chart grid (more subtle)
    for i in range(0, width, 50):
        draw.line([(i, 0), (i, height)], fill='#222222', width=1)
    for i in range(0, height, 50):
        draw.line([(0, i), (width, i)], fill='#222222', width=1)

    # Get live price data
    price_data = get_lux_price_data()

    # Draw a dramatic straight-down trend
    points = []
    x_step = width / 20

    if price_data and price_data["change_7d"]:
        # Calculate start and end y-coordinates for the line
        start_y = height * 0.1  # Start at 10% from top
        end_y = height * 0.9    # End at 90% from top

        # Generate points for a nearly straight line down with slight variation
        for i in range(21):
            x = i * x_step
            progress = i / 20.0

            # Add very minimal noise for a mostly straight line
            noise = random.uniform(-10, 10) if i > 0 and i < 20 else 0
            y = start_y + (end_y - start_y) * progress + noise

            points.append((x, y))
    else:
        # Fallback to a dramatic straight down trend
        for i in range(21):
            x = i * x_step
            y = height * (i / 20.0)
            points.append((x, y))

    # Draw price trend with enhanced visuals
    if len(points) > 1:
        # Draw shadow with higher opacity
        shadow_points = points + [(points[-1][0], height), (points[0][0], height)]
        draw.polygon(shadow_points, fill='#ff000044')

        # Draw multiple lines for glow effect
        for offset in range(3):
            draw.line(points, fill='#ff2222', width=4-offset)

        # Add time markers
        draw.text((10, height - 30), "7d ago", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16), fill='#888888')
        draw.text((width - 60, height - 30), "now", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16), fill='#888888')

    try:
        # Try system fonts first with smaller sizes
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        title_font = ImageFont.truetype(font_path, 48)  # Reduced from 60
        text_font = ImageFont.truetype(font_path, 32)   # Reduced from 40
    except:
        title_font = text_font = ImageFont.load_default()

    # Draw price with enhanced formatting
    if price_data:
        price_text = f"$LUX: {price_data['price_str']}{price_data['change_str']}"
    else:
        price_text = "$LUX: Price Unavailable 📉"

    price_bbox = draw.textbbox((0, 0), price_text, font=title_font)
    price_width = price_bbox[2] - price_bbox[0]
    x = (width - price_width) // 2

    # Draw price text with thicker outline
    y = 40  # Moved up slightly
    outline_color = 'black'
    for dx, dy in [(-2,-2), (-2,2), (2,-2), (2,2)]:
        draw.text((x + dx, y + dy), price_text, font=title_font, fill=outline_color)
    draw.text((x, y), price_text, font=title_font, fill='#ff4444')

    # Format roast text with smaller font
    words = text.split()
    lines = []
    current_line = []
    max_line_length = 50  # Increased due to smaller font

    for word in words:
        current_line.append(word)
        if len(' '.join(current_line)) > max_line_length:
            if len(current_line) > 1:
                lines.append(' '.join(current_line[:-1]))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []

    if current_line:
        lines.append(' '.join(current_line))

    # Draw text with improved visibility
    text_start_y = height - (len(lines) * 45) - 50  # Reduced spacing between lines

    # Draw semi-transparent background for text
    text_box_height = len(lines) * 45 + 40
    text_box = Image.new('RGBA', (width, text_box_height), (0, 0, 0, 180))
    image.paste(text_box, (0, text_start_y - 20), text_box)

    # Draw each line of text
    y = text_start_y
    for line in lines:
        line_bbox = draw.textbbox((0, 0), line, font=text_font)
        line_width = line_bbox[2] - line_bbox[0]
        x = (width - line_width) // 2

        # Draw outline for visibility
        for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:  # Thinner outline
            draw.text((x + dx, y + dy), line, font=text_font, fill='black')

        # Draw main text
        draw.text((x, y), line, font=text_font, fill='white')
        y += 45  # Reduced from 60

    # Convert to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr