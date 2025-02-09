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
    """Fetch live $LUX token data and 7-day historical data."""
    try:
        # Get current price data
        current_url = "https://api.coingecko.com/api/v3/simple/price"
        current_params = {
            "ids": "luxor",
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        current_response = requests.get(current_url, params=current_params, timeout=10)
        current_data = current_response.json()

        # Get 7-day historical data
        history_url = "https://api.coingecko.com/api/v3/coins/luxor/market_chart"
        history_params = {
            "vs_currency": "usd",
            "days": "7",
            "interval": "daily"
        }
        history_response = requests.get(history_url, params=history_params, timeout=10)
        history_data = history_response.json()

        if "luxor" in current_data and "prices" in history_data:
            current_price = current_data["luxor"]["usd"]
            price_points = [p for p in history_data["prices"] if p[1] > 0]  # Filter out invalid prices

            if not price_points:  # If no valid prices found
                return None

            # Calculate percentage change
            start_price = price_points[0][1]
            if start_price == 0:  # Avoid division by zero
                change_7d = 0
            else:
                change_7d = ((current_price - start_price) / start_price) * 100

            return {
                "price": current_price,
                "price_str": f"${current_price:.8f}" if current_price < 0.01 else f"${current_price:.6f}",
                "change_7d": change_7d,
                "change_str": f" (7d: {change_7d:+.1f}%)",
                "history": price_points
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

    # Draw subtle grid
    for i in range(0, width, 50):
        draw.line([(i, 0), (i, height)], fill='#222222', width=1)
    for i in range(0, height, 50):
        draw.line([(0, i), (width, i)], fill='#222222', width=1)

    # Get price data
    price_data = get_lux_price_data()

    if price_data and price_data.get("history"):
        # Get min and max prices for scaling
        prices = [point[1] for point in price_data["history"]]
        min_price = min(prices)
        max_price = max(prices)

        if min_price == max_price:  # Handle flat price line
            min_price *= 0.99
            max_price *= 1.01

        price_range = max_price - min_price

        # Add padding to price range
        padding = price_range * 0.1
        min_price -= padding
        max_price += padding
        price_range = max_price - min_price

        # Setup chart area
        chart_area = {
            'left': width * 0.15,    # Increased left margin
            'right': width * 0.85,   # Decreased right margin
            'top': height * 0.2,
            'bottom': height * 0.6   # Reduced bottom to make room for text
        }

        chart_width = chart_area['right'] - chart_area['left']
        chart_height = chart_area['bottom'] - chart_area['top']

        # Draw price labels on Y-axis
        price_steps = 5
        for i in range(price_steps + 1):
            price = min_price + (price_range * (i / price_steps))
            y = chart_area['bottom'] - (i / price_steps) * chart_height
            price_label = f"${price:.8f}" if price < 0.01 else f"${price:.6f}"

            # Draw dotted line
            dash_length = 5
            x = chart_area['left']
            while x < chart_area['right']:
                draw.line([(x, y), (x + dash_length, y)], fill='#333333', width=1)
                x += dash_length * 2

            # Draw price label
            label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            label_bbox = draw.textbbox((0, 0), price_label, font=label_font)
            label_width = label_bbox[2] - label_bbox[0]
            draw.text((chart_area['left'] - label_width - 10, y - 6), 
                     price_label, font=label_font, fill='#888888')

        # Plot data points
        points = []
        history = price_data["history"]
        for i, (timestamp, price) in enumerate(history):
            x = chart_area['left'] + (i / (len(history) - 1)) * chart_width
            y = chart_area['bottom'] - ((price - min_price) / price_range) * chart_height
            points.append((x, y))

            # Draw point
            circle_radius = 4
            draw.ellipse([(x - circle_radius - 1, y - circle_radius - 1),
                         (x + circle_radius + 1, y + circle_radius + 1)],
                        fill='white')
            draw.ellipse([(x - circle_radius, y - circle_radius),
                         (x + circle_radius, y + circle_radius)],
                        fill='#ff4444')

            # Draw price label above point
            price_label = f"${price:.8f}" if price < 0.01 else f"${price:.6f}"
            label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            label_bbox = draw.textbbox((0, 0), price_label, font=label_font)
            label_width = label_bbox[2] - label_bbox[0]
            label_x = x - label_width/2
            label_y = y - 20

            draw.text((label_x, label_y), price_label, font=label_font, fill='#888888')

        # Draw lines between points
        if len(points) > 1:
            draw.line(points, fill='#ff4444', width=2)

        # Draw X-axis labels (dates)
        for i, (timestamp, _) in enumerate(history):
            x = chart_area['left'] + (i / (len(history) - 1)) * chart_width
            label = "Now" if i == len(history) - 1 else f"{len(history) - 1 - i}d"

            label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            label_bbox = draw.textbbox((0, 0), label, font=label_font)
            label_width = label_bbox[2] - label_bbox[0]
            label_x = x - label_width/2
            label_y = chart_area['bottom'] + 10

            draw.text((label_x, label_y), label, font=label_font, fill='#888888')

    else:
        # Draw "No Data Available" message
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        message = "Price data unavailable"
        bbox = draw.textbbox((0, 0), message, font=font)
        message_width = bbox[2] - bbox[0]
        x = (width - message_width) // 2
        y = height // 2
        draw.text((x, y), message, font=font, fill='#ff4444')

    # Draw header with current price
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    except:
        title_font = ImageFont.load_default()

    if price_data:
        price_text = f"$LUX: {price_data['price_str']}{price_data['change_str']}"
    else:
        price_text = "$LUX: Price Unavailable 📉"

    bbox = draw.textbbox((0, 0), price_text, font=title_font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    y = 40
    draw.text((x, y), price_text, font=title_font, fill='#ff4444')

    # Draw roast text at the bottom
    words = text.split()
    lines = []
    current_line = []
    max_line_length = 50

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

    # Draw text with semi-transparent background
    text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    text_start_y = height - (len(lines) * 40) - 40
    text_box_height = len(lines) * 40 + 40
    text_box = Image.new('RGBA', (width, text_box_height), (0, 0, 0, 180))
    image.paste(text_box, (0, text_start_y - 20), text_box)

    # Draw each line of text
    y = text_start_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=text_font)
        line_width = bbox[2] - bbox[0]
        x = (width - line_width) // 2
        draw.text((x, y), line, font=text_font, fill='white')
        y += 40

    # Convert to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr