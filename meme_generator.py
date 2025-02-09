import os
import random
from datetime import datetime
import logging
from price_chart import create_price_chart, get_lux_price_history
from PIL import Image, ImageDraw, ImageFont
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot')

def generate_meme():
    """Generate a price chart meme with savage roast overlay."""
    try:
        logger.info("Starting price chart meme generation")

        # Generate chart HTML
        chart_path = create_price_chart()
        if not chart_path:
            logger.error("Failed to generate chart HTML")
            return None

        # Set up Chrome options for headless screenshot
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1280,720")
        chrome_options.add_argument("--force-device-scale-factor=1")

        # Use the Nix-installed Chrome and ChromeDriver
        chrome_binary = "/nix/store/chromium/bin/chromium"
        chrome_options.binary_location = chrome_binary

        try:
            logger.info("Initializing Chrome WebDriver")
            # Use ChromeDriver from Nix store
            service = Service(executable_path="/nix/store/chromedriver/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Successfully initialized Chrome WebDriver")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {str(e)}")
            return None

        try:
            # Load the chart HTML
            file_url = f"file://{os.path.abspath(chart_path)}"
            logger.info(f"Loading chart HTML from: {file_url}")
            driver.get(file_url)

            # Wait for TradingView widget to load (maximum 20 seconds)
            logger.info("Waiting for TradingView widget to load")
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, "tradingview_chart"))
                )
                # Additional wait for chart to render
                time.sleep(5)
                logger.info("TradingView widget loaded successfully")
            except Exception as e:
                logger.error(f"Timeout waiting for chart to load: {str(e)}")
                return None

            # Take screenshot
            screenshot_path = f"chart_screenshot_{int(datetime.now().timestamp())}.png"
            logger.info(f"Taking screenshot: {screenshot_path}")
            driver.save_screenshot(screenshot_path)

            # Clean up HTML file
            try:
                os.remove(chart_path)
                logger.info(f"Cleaned up chart HTML: {chart_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up chart HTML: {str(e)}")

            # Load screenshot and add text overlay
            img = Image.open(screenshot_path)
            draw = ImageDraw.Draw(img)

            # Load custom font or fallback to default
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
                logger.info("Loaded custom font successfully")
            except Exception as e:
                logger.warning(f"Failed to load custom font: {str(e)}. Using default.")
                font = ImageFont.load_default()

            # Get current price and crash percentage for roast
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            dates, prices = loop.run_until_complete(get_lux_price_history())
            loop.close()

            if dates and prices:
                entry_price = 0.015  # NWA entry price
                current_price = prices[-1]
                crash_percent = ((entry_price - current_price) / entry_price) * 100
                price_in_cents = current_price * 100

                if crash_percent >= 90:
                    roast = f"DOWN {crash_percent:.1f}%! ({price_in_cents:.4f}¢) COMPLETE RUGPULL! 💀"
                elif crash_percent >= 70:
                    roast = f"DUMPED {crash_percent:.1f}%! ({price_in_cents:.4f}¢) TINO IN SHAMBLES! 🖕"
                elif crash_percent >= 50:
                    roast = f"CRASHING {crash_percent:.1f}%! ({price_in_cents:.4f}¢) NWA WINS AGAIN! 🔥"
                else:
                    roast = f"DUMPING {crash_percent:.1f}%! ({price_in_cents:.4f}¢) TINO'S REPUTATION! 💸"
            else:
                roast = "LUX IS DEAD! COMPLETE RUGPULL! 💀"

            # Add text with outline
            text_color = 'white'
            outline_color = 'black'
            outline_width = 2
            text_pos = (20, 20)

            # Draw outline
            for dx in range(-outline_width, outline_width+1):
                for dy in range(-outline_width, outline_width+1):
                    if dx != 0 or dy != 0:
                        draw.text((text_pos[0]+dx, text_pos[1]+dy),
                                roast, font=font, fill=outline_color)

            # Draw main text
            draw.text(text_pos, roast, font=font, fill=text_color)

            # Save final meme
            final_path = f"price_meme_{int(datetime.now().timestamp())}.png"
            img.save(final_path, quality=95)

            # Clean up screenshot
            try:
                os.remove(screenshot_path)
                logger.info(f"Cleaned up screenshot: {screenshot_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up screenshot: {str(e)}")

            logger.info(f"Successfully generated meme: {final_path}")
            return final_path

        finally:
            driver.quit()
            logger.info("Chrome WebDriver closed")

    except Exception as e:
        logger.error(f"Error generating meme: {str(e)}")
        logger.exception("Full traceback:")
        return None