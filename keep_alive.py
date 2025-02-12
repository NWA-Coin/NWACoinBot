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
    logger.info("Received request to keep-alive endpoint")
    return "Bot is alive!"

def verify_server(port):
    """Test if server is responding"""
    logger.info("Starting server verification...")
    time.sleep(2)  # Wait for server to start

    try:
        # First check if port is actually in use
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('0.0.0.0', port))
        sock.close()

        if result != 0:
            logger.error(f"Port {port} is not in use!")
            return False

        logger.info(f"Port {port} is in use, testing HTTP response...")
        try:
            response = requests.get(f'http://0.0.0.0:{port}/', timeout=5)
            logger.info(f"Server test response: {response.status_code}")
            return response.status_code == 200
        except requests.RequestException as e:
            logger.error(f"HTTP request failed: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Server test failed: {str(e)}")
        return False

def keep_alive():
    """Start the keep-alive server and return the port"""
    try:
        # Get port from environment variable, default to 3000 if not set
        # Railway will automatically set PORT environment variable
        port = int(os.environ.get('PORT', 3000))
        logger.info(f"Starting keep-alive server on port {port}...")

        def run_flask():
            # Disable Flask's default logging to avoid noise
            import logging
            logging.getLogger('werkzeug').setLevel(logging.ERROR)
            app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

        # Start Flask in a daemon thread
        server = Thread(target=run_flask)
        server.daemon = True
        server.start()

        # Verify server started properly
        if verify_server(port):
            logger.info(f"Keep-alive server started successfully on port {port}")
            return port
        else:
            logger.error("Failed to verify keep-alive server")
            return None

    except Exception as e:
        logger.error(f"Failed to start keep-alive server: {str(e)}")
        return None

if __name__ == "__main__":
    keep_alive()