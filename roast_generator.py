import random
from PIL import Image, ImageDraw, ImageFont
import io
import os
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import emoji

# Roast templates remain unchanged
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
    "$LUX devs must be using carrier pigeons for communication! 🐦"
]

def generate_roast():
    """Generate a random roast from predefined templates."""
    return random.choice(ROAST_TEMPLATES)

def get_lux_price_data():
    """Fetch live $LUX token data with retries."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # Get current price with 24h change
        current_url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "luxor",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_last_updated_at": "true"
        }

        response = requests.get(current_url, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Error fetching price: {response.status_code}")
            return None

        data = response.json()

        if "luxor" not in data:
            print("No Luxor data in response")
            return None

        lux_data = data["luxor"]
        current_price = lux_data.get("usd", 0)
        price_change = lux_data.get("usd_24h_change", 0)
        volume = lux_data.get("usd_24h_vol", 0)

        # Get historical data for chart
        history_url = f"https://api.coingecko.com/api/v3/coins/luxor/market_chart"
        history_params = {
            "vs_currency": "usd",
            "days": "7",
            "interval": "hourly"
        }

        history_response = requests.get(history_url, params=history_params, headers=headers, timeout=10)
        if history_response.status_code != 200:
            print(f"Error fetching history: {history_response.status_code}")
            return None

        history_data = history_response.json()

        if "prices" not in history_data:
            print("No price history in response")
            return None

        # Process and filter price history
        price_history = []
        for timestamp, price in history_data["prices"]:
            if price > 0:  # Filter out zero prices
                dt = datetime.fromtimestamp(timestamp/1000)
                price_history.append((dt, price))

        if not price_history:
            print("No valid price history points")
            return None

        return {
            "current_price": current_price,
            "price_change": price_change,
            "volume": volume,
            "price_str": f"${current_price:.8f}" if current_price < 0.01 else f"${current_price:.4f}",
            "change_str": f"{price_change:+.2f}%" if price_change else "N/A",
            "volume_str": f"${volume:,.2f}" if volume else "N/A",
            "history": price_history,
            "last_updated": datetime.fromtimestamp(lux_data.get("last_updated_at", 0))
        }

    except Exception as e:
        print(f"Error fetching price data: {str(e)}")
        return None

def create_meme_image(text):
    """Create a meme image with the given text and price chart."""
    width = 1200
    height = 800

    try:
        # Create base image
        image = Image.new('RGB', (width, height), color='#1a1a1a')
        draw = ImageDraw.Draw(image)

        # Get price data
        price_data = get_lux_price_data()

        if price_data and price_data["history"]:
            # Set up matplotlib for chart
            plt.clf()
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(10, 4))
            fig.patch.set_facecolor('#1a1a1a')
            ax.set_facecolor('#1a1a1a')

            # Extract data for plotting
            dates = [point[0] for point in price_data["history"]]
            prices = [point[1] for point in price_data["history"]]

            # Create the main price line
            ax.plot(dates, prices, color='#ff4444', linewidth=2, label='Price')

            # Add gradient fill
            ax.fill_between(dates, prices, min(prices), color='#ff4444', alpha=0.1)

            # Customize grid and ticks
            ax.grid(True, color='#333333', linestyle='--', alpha=0.3)
            ax.tick_params(axis='both', colors='#888888', labelsize=8)

            # Format axes
            ax.yaxis.set_major_formatter(plt.FuncFormatter(
                lambda x, p: f'${x:.8f}' if x < 0.01 else f'${x:.4f}'
            ))
            ax.xaxis.set_major_formatter(plt.DateFormatter('%b %d %H:%M'))
            plt.xticks(rotation=45)

            # Add title with last updated time
            update_time = price_data["last_updated"].strftime("%Y-%m-%d %H:%M UTC")
            plt.title(f"$LUX Price Chart (Updated: {update_time})", 
                     color='#888888', pad=10, fontsize=10)

            # Save chart to bytes
            chart_bytes = io.BytesIO()
            plt.savefig(chart_bytes, format='png', dpi=100, bbox_inches='tight',
                       facecolor='#1a1a1a', edgecolor='none')
            plt.close()

            # Add chart to image
            chart_bytes.seek(0)
            chart_img = Image.open(chart_bytes)
            chart_img = chart_img.resize((width - 100, 300), Image.Resampling.LANCZOS)
            image.paste(chart_img, (50, 150))

        # Add price and stats at the top
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)

        if price_data:
            stats = f"$LUX: {price_data['price_str']} ({price_data['change_str']}) | Vol: {price_data['volume_str']}"
        else:
            stats = "$LUX: Price Unavailable 📉"

        # Convert emojis in text
        stats = emoji.emojize(stats, language='alias')
        text = emoji.emojize(text, language='alias')

        # Draw stats
        bbox = draw.textbbox((0, 0), stats, font=title_font)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x, 50), stats, font=title_font, fill='#ff4444')

        # Draw roast text at bottom
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)

        # Split text into lines
        words = text.split()
        lines = []
        current_line = []
        max_width = width - 200

        for word in words:
            current_line.append(word)
            line = ' '.join(current_line)
            bbox = draw.textbbox((0, 0), line, font=text_font)
            if bbox[2] - bbox[0] > max_width:
                if len(current_line) > 1:
                    lines.append(' '.join(current_line[:-1]))
                    current_line = [word]
                else:
                    lines.append(word)
                    current_line = []

        if current_line:
            lines.append(' '.join(current_line))

        # Draw text
        y = 500  # Start below chart
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=text_font)
            x = (width - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), line, font=text_font, fill='white')
            y += 60

        # Convert to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

    except Exception as e:
        print(f"Error creating meme image: {str(e)}")
        # Create error image
        error_image = Image.new('RGB', (width, height), color='#1a1a1a')
        draw = ImageDraw.Draw(error_image)
        error_text = "Failed to generate meme 😢"
        try:
            error_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        except:
            error_font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), error_text, font=error_font)
        x = (width - (bbox[2] - bbox[0])) // 2
        y = height // 2
        draw.text((x, y), error_text, font=error_font, fill='#ff4444')

        error_bytes = io.BytesIO()
        error_image.save(error_bytes, format='PNG')
        error_bytes.seek(0)
        return error_bytes