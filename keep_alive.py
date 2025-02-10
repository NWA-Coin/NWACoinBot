from flask import Flask
from threading import Thread
import logging
import time
import os
import socket

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

def run():
    """Run the Flask app"""
    try:
        # Use a different port to avoid conflicts
        port = int(os.environ.get('PORT', '8090'))
        logger.info(f"Starting keep-alive server on port {port}")

        # Check if port is already in use
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('0.0.0.0', port))
            sock.close()
        except socket.error:
            logger.warning(f"Port {port} is already in use, attempting to use it anyway")

        app.run(
            host='0.0.0.0',  # Required for external access
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True    # Enable threading for better concurrent handling
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        logger.exception("Full traceback:")
        return False

def keep_alive():
    """Start the keep-alive server in a daemon thread"""
    try:
        # Create and configure server thread
        server = Thread(target=run, daemon=True, name="KeepAliveServer")
        server.start()

        # Give the server time to start
        time.sleep(2)

        # Verify server started successfully
        if server.is_alive():
            logger.info("Keep-alive server started successfully")
            return True
        else:
            logger.error("Keep-alive server failed to start")
            return False

    except Exception as e:
        logger.error(f"Failed to start keep-alive server: {str(e)}")
        logger.exception("Full traceback:")
        return False

if __name__ == "__main__":
    keep_alive()