import os
import logging
import time
import socket
import requests
from flask import Flask
from threading import Thread

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot')

app = Flask(__name__)

@app.route('/')
def home():
    """Simple endpoint to respond to keep-alive pings"""
    return "Bot is alive!"

def verify_server():
    """Test if server is responding"""
    time.sleep(2)  # Wait for server to start
    try:
        response = requests.get('http://0.0.0.0:8000')
        logger.info(f"Server test response: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Server test failed: {str(e)}")
        return False

def keep_alive():
    """Start the keep-alive server and return the port"""
    try:
        logger.info("Starting keep-alive server on port 8000...")

        # Start Flask in a daemon thread
        server = Thread(target=lambda: app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False))
        server.daemon = True
        server.start()

        # Verify server started properly
        if verify_server():
            logger.info("Keep-alive server started successfully on port 8000")
            return 8000
        else:
            logger.error("Failed to verify keep-alive server")
            return None

    except Exception as e:
        logger.error(f"Failed to start keep-alive server: {str(e)}")
        return None

if __name__ == "__main__":
    keep_alive()