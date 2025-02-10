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
    """Verify server is actually responding"""
    try:
        for _ in range(3):  # Try up to 3 times
            try:
                response = requests.get(f'http://0.0.0.0:{port}/', timeout=5)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                time.sleep(1)
        return False
    except Exception as e:
        logger.error(f"Error verifying server: {str(e)}")
        return False

def wait_for_port_release(port, timeout=30):
    """Wait for port to be released"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('0.0.0.0', port))
            sock.close()
            return True
        except socket.error:
            logger.info(f"Port {port} still in use, waiting...")
            time.sleep(2)
        finally:
            sock.close()
    return False

def run():
    """Run the Flask app"""
    try:
        # Use a different port to avoid conflicts
        port = int(os.environ.get('PORT', '8090'))
        logger.info(f"Starting keep-alive server on port {port}")

        # Wait for port to be released
        if not wait_for_port_release(port):
            logger.error(f"Port {port} could not be released")
            return False

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

        # Give the server more time to start
        time.sleep(5)  # Increased from 2 to 5 seconds

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
        logger.exception("Full traceback:")
        return False

if __name__ == "__main__":
    keep_alive()