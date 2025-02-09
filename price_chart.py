# Set up matplotlib with Agg backend first
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta
import logging
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import time
import aiohttp
import asyncio

# Set up logging with more detailed format
logger = logging.getLogger('discord_bot')
logger.setLevel(logging.DEBUG)  # Ensure debug messages are logged
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

async def get_lux_price_history():
    """Get LUX price history from CoinGecko asynchronously."""
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching LUX price data (attempt {attempt + 1}/{max_retries})")

            # Use CoinGecko API v3 endpoint with contract address for LUX token
            url = "https://api.coingecko.com/api/v3/coins/lux-token/market_chart"
            params = {
                "vs_currency": "usd",
                "days": "30",
                "interval": "daily",
                "precision": "full"  # Get full precision for small numbers
            }

            logger.info(f"Making API request to: {url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    logger.info(f"API Response Status: {response.status}")
                    logger.debug(f"API Response Headers: {response.headers}")

                    if response.status == 429:
                        logger.warning("Rate limited by CoinGecko API")
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                            logger.info(f"Waiting {wait_time} seconds before retry")
                            await asyncio.sleep(wait_time)
                            continue
                        logger.error("Max retries reached for rate limit")
                        return await generate_mock_data()

                    if response.status != 200:
                        logger.error(f"API Error {response.status}: {await response.text()}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            continue
                        return await generate_mock_data()

                    data = await response.json()
                    logger.debug(f"Raw API response: {data}")

                    if not data or 'prices' not in data:
                        logger.error(f"Invalid API response format: {data}")
                        return await generate_mock_data()

                    # Extract price data points with enhanced logging
                    prices = [p[1] for p in data['prices']]
                    dates = [datetime.fromtimestamp(p[0]/1000) for p in data['prices']]

                    if not prices or not dates:
                        logger.error("Empty price data received")
                        return await generate_mock_data()

                    logger.info(f"Successfully fetched {len(prices)} price points")
                    logger.info(f"Price range: ${min(prices):.8f} - ${max(prices):.8f}")
                    logger.info(f"Date range: {dates[0]} - {dates[-1]}")
                    return dates, prices

        except asyncio.TimeoutError:
            logger.error(f"Timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            return await generate_mock_data()

        except Exception as e:
            logger.error(f"Unexpected error in get_lux_price_history: {str(e)}")
            logger.exception("Full traceback:")
            return await generate_mock_data()

    logger.error("All attempts failed")
    return await generate_mock_data()

async def generate_mock_data():
    """Generate realistic mock price data asynchronously."""
    try:
        logger.warning("Using mock price data")
        days = 30
        initial_price = 0.015  # NWA entry price
        final_price = 0.00001  # Current crashed price

        dates = [datetime.now() - timedelta(days=x) for x in range(days)]
        dates.reverse()  # Make dates go forward

        # Generate exponential decay with volatility
        decay = (final_price / initial_price) ** (1/days)
        base_prices = [initial_price * (decay ** i) for i in range(days)]

        # Add realistic volatility
        volatility = 0.15  # 15% daily volatility
        prices = []
        for base_price in base_prices:
            # Add random walk with downward bias
            change = np.random.normal(-0.02, volatility)
            price = base_price * (1 + change)
            price = max(0.00000001, price)  # Ensure price doesn't go negative
            prices.append(price)

        logger.info(f"Generated mock data: ${prices[0]:.8f} -> ${prices[-1]:.8f}")
        return dates, prices

    except Exception as e:
        logger.error(f"Error generating mock data: {str(e)}")
        # Return absolute fallback data
        dates = [datetime.now() - timedelta(days=x) for x in range(30)]
        prices = [0.015 * (0.9 ** x) for x in range(30)]  # Simple geometric decay
        return dates, prices

def create_price_chart():
    """Create a price chart with savage roast overlay."""
    try:
        logger.info("Starting price chart creation")

        # Get price data
        logger.debug("Setting up asyncio event loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info("Fetching price data")
        dates, prices = loop.run_until_complete(get_lux_price_history())
        loop.close()
        logger.debug("Closed asyncio loop")

        if not dates or not prices:
            logger.error("Failed to get price data - dates or prices is empty")
            return None

        # Calculate crash percentage
        entry_price = 0.015  # NWA entry price
        current_price = prices[-1]
        crash_percent = ((entry_price - current_price) / entry_price) * 100
        price_in_cents = current_price * 100
        logger.info(f"Calculated crash: {crash_percent:.2f}%, current price: {price_in_cents:.4f}¢")

        # Create chart with dark theme
        logger.debug("Creating matplotlib figure")
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 6), facecolor='#2F3136')

        # Plot price line with gradient color based on crash severity
        color = 'red' if crash_percent > 50 else 'orange'
        ax.plot(dates, prices, color=color, linewidth=2)

        # Customize chart
        title = f"LUX/USD Price Chart\nCurrent: {price_in_cents:.4f}¢\nDown {crash_percent:.1f}% since NWA Entry"
        ax.set_title(title, color='white', size=14, pad=20)
        ax.set_xlabel("Date", color='white', size=12)
        ax.set_ylabel("Price (USD)", color='white', size=12)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x*100:.4f}¢"))

        # Customize grid and ticks
        ax.grid(True, alpha=0.2)
        plt.xticks(rotation=45, color='white')
        plt.yticks(color='white')

        # Add NWA entry line
        ax.axhline(y=entry_price, color='yellow', linestyle='--', alpha=0.5,
                  label=f'NWA Entry: {entry_price*100:.4f}¢')
        ax.legend(facecolor='#2F3136', edgecolor='white')

        # Ensure the figure has a tight layout
        plt.tight_layout()

        # Save base chart
        temp_chart = "temp_chart.png"
        logger.debug(f"Saving temporary chart to {temp_chart}")
        plt.savefig(temp_chart, bbox_inches='tight', dpi=300,
                   facecolor='#2F3136', edgecolor='none')
        plt.close()

        if not os.path.exists(temp_chart):
            logger.error("Failed to save temporary chart file")
            return None

        logger.debug("Opening temporary chart for adding text overlay")
        # Add roast overlay
        img = Image.open(temp_chart)
        draw = ImageDraw.Draw(img)

        # Generate roast based on crash percentage
        if crash_percent >= 90:
            roast = f"DOWN {crash_percent:.1f}%! ({price_in_cents:.4f}¢) COMPLETE RUGPULL! 💀"
        elif crash_percent >= 70:
            roast = f"DUMPED {crash_percent:.1f}%! ({price_in_cents:.4f}¢) TINO IN SHAMBLES! 🖕"
        elif crash_percent >= 50:
            roast = f"CRASHING {crash_percent:.1f}%! ({price_in_cents:.4f}¢) NWA WINS AGAIN! 🔥"
        else:
            roast = f"DUMPING {crash_percent:.1f}%! ({price_in_cents:.4f}¢) TINO'S REPUTATION! 💸"

        logger.debug(f"Generated roast text: {roast}")

        # Configure text rendering
        font = ImageFont.load_default()
        text_color = 'white'
        outline_color = 'black'
        outline_width = 2
        text_pos = (20, 20)

        # Draw text with outline for better visibility
        logger.debug("Adding text overlay to chart")
        for dx in range(-outline_width, outline_width+1):
            for dy in range(-outline_width, outline_width+1):
                if dx != 0 or dy != 0:
                    draw.text((text_pos[0]+dx, text_pos[1]+dy),
                            roast, font=font, fill=outline_color)

        # Draw main text
        draw.text(text_pos, roast, font=font, fill=text_color)

        # Save final chart with timestamp
        final_path = f"price_chart_{int(datetime.now().timestamp())}.png"
        logger.debug(f"Saving final chart to {final_path}")
        img.save(final_path, quality=95)

        if not os.path.exists(final_path):
            logger.error("Failed to save final chart file")
            return None

        # Clean up temporary file
        try:
            logger.debug(f"Cleaning up temporary file: {temp_chart}")
            os.remove(temp_chart)
        except Exception as e:
            logger.warning(f"Failed to remove temp chart: {str(e)}")

        logger.info(f"Successfully created price chart: {final_path}")
        return final_path

    except Exception as e:
        logger.error(f"Error creating price chart: {str(e)}")
        logger.exception("Full traceback:")
        return None