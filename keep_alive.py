import os
import logging
import time
import socket
import requests
from flask import Flask
from threading import Thread

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

def find_available_port(start_port=3000, max_attempts=5):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('0.0.0.0', port))
            sock.close()
            logger.info(f"Found available port: {port}")
            return port
        except socket.error:
            logger.warning(f"Port {port} is not available")
            continue
    return None

def run_flask(port):
    """Run the Flask app"""
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Error starting Flask: {str(e)}")
        return False

def keep_alive():
    """Start the keep-alive server"""
    try:
        # Find an available port
        port = find_available_port()
        if not port:
            logger.error("No available ports found")
            return None

        # Start Flask in a separate thread
        server = Thread(target=lambda: run_flask(port), daemon=True)
        server.start()
        logger.info(f"Started keep-alive server on port {port}")

        # Give the server time to start
        time.sleep(2)

        # Verify server is running
        try:
            response = requests.get(f'http://0.0.0.0:{port}/')
            if response.status_code == 200:
                logger.info("Keep-alive server verified")
                return port
        except Exception as e:
            logger.error(f"Failed to verify server: {str(e)}")
            return None

    except Exception as e:
        logger.error(f"Error in keep_alive: {str(e)}")
        return None

if __name__ == "__main__":
    keep_alive()