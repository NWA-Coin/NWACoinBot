from flask import Flask
from threading import Thread
import logging
import time
import os
import socket
import requests

# Set up logging with more detailed format
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

def verify_server_running(port):
    """Verify server is actually responding using localhost"""
    try:
        for _ in range(3):  # Try up to 3 times
            try:
                response = requests.get(f'http://127.0.0.1:{port}/', timeout=5)
                if response.status_code == 200:
                    logger.info("Server verification successful")
                    return True
            except requests.RequestException as e:
                logger.warning(f"Verification attempt failed: {str(e)}")
                time.sleep(1)
        return False
    except Exception as e:
        logger.error(f"Error verifying server: {str(e)}")
        return False

def run():
    """Run the Flask app"""
    try:
        port = int(os.environ.get('PORT', '8090'))
        logger.info(f"Starting keep-alive server on port {port}")

        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        return False

def keep_alive():
    """Start the keep-alive server in a daemon thread"""
    try:
        server = Thread(target=run, daemon=True, name="KeepAliveServer")
        server.start()

        # Give the server time to start
        time.sleep(2)

        # Verify server started successfully
        port = int(os.environ.get('PORT', '8090'))
        if server.is_alive() and verify_server_running(port):
            logger.info("Keep-alive server started successfully")
            return True
        else:
            logger.error("Keep-alive server failed to start")
            return False

    except Exception as e:
        logger.error(f"Failed to start keep-alive server: {str(e)}")
        return False

if __name__ == "__main__":
    keep_alive()