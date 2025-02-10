from flask import Flask
from threading import Thread
import logging
import time
from datetime import datetime
import socket
import requests
import asyncio

app = Flask(__name__)
logger = logging.getLogger('discord_bot')

@app.route('/')
def home():
    """Endpoint to respond to keep-alive pings"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Keep-alive ping received at {current_time}")
    return "Bot is alive!"

def is_port_available(port):
    """Check if a port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
            return True
    except:
        return False

def run():
    """Run the Flask app in a separate thread"""
    try:
        if not is_port_available(8081):
            logger.warning("Port 8081 is busy, waiting...")
            return False

        logger.info("Starting Flask server on port 8081")
        app.run(
            host='0.0.0.0',
            port=8081,
            threaded=True,
            debug=False,
            use_reloader=False
        )
        return True
    except Exception as e:
        logger.error(f"Flask server error: {str(e)}")
        return False

async def self_ping():
    """Periodically ping the server to keep it alive"""
    while True:
        try:
            logger.debug("Self-ping attempt...")
            requests.get('http://127.0.0.1:8081/', timeout=5)
            logger.debug("Self-ping successful")
        except Exception as e:
            logger.warning(f"Self-ping failed: {str(e)}")
        await asyncio.sleep(30)  # Ping every 30 seconds

def keep_alive():
    """Start the keep-alive server with enhanced reliability"""
    MAX_RETRIES = 5
    RETRY_DELAY = 5

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Starting keep-alive server (attempt {attempt + 1}/{MAX_RETRIES})")

            # Ensure port is available
            if not is_port_available(8081):
                logger.warning("Port 8081 is busy, waiting...")
                time.sleep(RETRY_DELAY)
                continue

            # Start server thread
            server = Thread(target=run)
            server.daemon = True
            server.start()

            # Wait for server initialization
            for _ in range(10):  # Try for 10 seconds
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect(('127.0.0.1', 8081))
                        logger.info("Keep-alive server started successfully")

                        # Start self-ping loop in a separate thread
                        ping_thread = Thread(target=lambda: asyncio.run(self_ping()))
                        ping_thread.daemon = True
                        ping_thread.start()

                        return True
                except:
                    time.sleep(1)
                    continue

            logger.error("Server failed to start within timeout")

        except Exception as e:
            logger.error(f"Error starting keep-alive server: {str(e)}")

        if attempt < MAX_RETRIES - 1:
            logger.info("Retrying server start...")
            time.sleep(RETRY_DELAY)

    logger.error("Failed to start keep-alive server after all retries")
    return False