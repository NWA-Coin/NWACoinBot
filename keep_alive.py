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

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            s.close()  # Explicitly close the socket
            return False
        except socket.error:
            return True

def verify_server_running(port):
    """Verify server is actually responding using localhost"""
    try:
        logger.info(f"Verifying server on port {port}")
        for attempt in range(1, 6):  # 5 attempts
            try:
                logger.info(f"Verification attempt {attempt}/5")
                response = requests.get(f'http://127.0.0.1:{port}/', timeout=10)
                if response.status_code == 200:
                    logger.info("Server verification successful")
                    return True
            except requests.RequestException as e:
                logger.warning(f"Verification attempt {attempt} failed: {str(e)}")
                if attempt < 5:
                    time.sleep(2)  # Wait before retry
        logger.error("Server verification failed after all attempts")
        return False
    except Exception as e:
        logger.error(f"Error verifying server: {str(e)}")
        logger.exception("Full traceback:")
        return False

def run():
    """Run the Flask app"""
    try:
        port = int(os.environ.get('PORT', '8090'))

        # Check if port is already in use
        if is_port_in_use(port):
            logger.error(f"Port {port} is already in use")
            return False

        logger.info(f"Starting keep-alive server on port {port}")

        # Basic Flask configuration
        app.config['SERVER_NAME'] = f'0.0.0.0:{port}'

        # Explicitly bind to all interfaces with enhanced configuration
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True,
            processes=1
        )
        return True
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        logger.exception("Full traceback:")
        return False

def keep_alive():
    """Start the keep-alive server in a daemon thread"""
    try:
        # Check if port is available before starting
        port = int(os.environ.get('PORT', '8090'))
        if is_port_in_use(port):
            logger.error(f"Port {port} is already in use")
            return False

        # Create and start server thread
        server = Thread(target=run, daemon=True, name="KeepAliveServer")
        server.start()
        logger.info("Keep-alive server thread started")

        # Give more time for server startup and initialization
        time.sleep(10)  # Increased wait time further

        # Verify server started successfully
        if server.is_alive() and verify_server_running(port):
            logger.info("Keep-alive server started successfully")
            return True
        else:
            logger.error("Keep-alive server failed to start properly")
            return False

    except Exception as e:
        logger.error(f"Failed to start keep-alive server: {str(e)}")
        logger.exception("Full traceback:")
        return False

if __name__ == "__main__":
    keep_alive()