import random
from PIL import Image, ImageDraw, ImageFont
import io
import os
import requests

# Predefined roast templates remain unchanged
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
    """Fetch live $LUX token data from CoinGecko."""
    try:
        # Using CoinGecko API to get LUX token data
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "lux-pad",  # Updated CoinGecko ID for LUX token
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        response = requests.get(url, params=params)
        data = response.json()

        if "lux-pad" in data:
            price = data["lux-pad"]["usd"]
            change_24h = data["lux-pad"].get("usd_24h_change", 0)
            # Format with fallbacks for None values
            price_str = f"${price:.8f}" if price is not None else "Unknown"
            change_str = f" ({change_24h:+.2f}%)" if change_24h is not None else ""
            return f"{price_str}{change_str}"
        return "Price: TBA 📊"
    except Exception as e:
        print(f"Error fetching price: {str(e)}")
        return "Chart Loading... 📈"

def create_meme_image(text):
    """Create a meme image with the given text and live $LUX data."""
    # Create a new image with a dark background
    width = 1200  # Increased width
    height = 800  # Increased height
    image = Image.new('RGB', (width, height), color='#1a1a1a')
    draw = ImageDraw.Draw(image)

    # Draw chart grid
    for i in range(0, width, 50):
        draw.line([(i, 0), (i, height)], fill='#2a2a2a', width=1)
    for i in range(0, height, 50):
        draw.line([(0, i), (width, i)], fill='#2a2a2a', width=1)

    # Draw a mock price chart (downward trend)
    points = []
    x_step = width / 20
    current_y = height * 0.3
    for i in range(21):
        x = i * x_step
        current_y += random.uniform(5, 15)
        if current_y > height * 0.8:
            current_y = height * 0.8
        points.append((x, current_y))

    # Draw the price line
    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill='#ff4444', width=4)

    # Get live price data
    price_text = get_lux_price_data()

    # Try to use a very large font, fallback to default if not available
    try:
        # Try system fonts first
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        title_font = ImageFont.truetype(font_path, 80)  # Larger font for price
        text_font = ImageFont.truetype(font_path, 60)   # Larger font for roast
    except:
        title_font = text_font = ImageFont.load_default()

    # Draw price at the top
    price_bbox = draw.textbbox((0, 0), f"$LUX: {price_text}", font=title_font)
    price_width = price_bbox[2] - price_bbox[0]
    x = (width - price_width) // 2

    # Draw price text with outline
    y = 50
    outline_color = 'black'
    for dx, dy in [(-3,-3), (-3,3), (3,-3), (3,3)]:
        draw.text((x + dx, y + dy), f"$LUX: {price_text}", font=title_font, fill=outline_color)
    draw.text((x, y), f"$LUX: {price_text}", font=title_font, fill='#ff4444')

    # Add the roast text
    words = text.split()
    lines = []
    current_line = []
    max_line_length = 30  # Limit characters per line

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
    text_start_y = height - (len(lines) * 80) - 50  # More space between lines

    # Draw semi-transparent background for text
    text_box_height = len(lines) * 80 + 40
    text_box = Image.new('RGBA', (width, text_box_height), (0, 0, 0, 180))
    image.paste(text_box, (0, text_start_y - 20), text_box)

    # Draw each line of text
    y = text_start_y
    for line in lines:
        # Get line width for centering
        line_bbox = draw.textbbox((0, 0), line, font=text_font)
        line_width = line_bbox[2] - line_bbox[0]
        x = (width - line_width) // 2

        # Draw outline for visibility
        for dx, dy in [(-3,-3), (-3,3), (3,-3), (3,3)]:
            draw.text((x + dx, y + dy), line, font=text_font, fill='black')

        # Draw main text
        draw.text((x, y), line, font=text_font, fill='white')
        y += 80  # Increased line spacing

    # Convert to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr