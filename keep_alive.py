import os
import logging
import time
import socket
import requests
from flask import Flask
from threading import Thread
import traceback

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
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Set socket options for immediate reuse
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', port))
        return False
    except socket.error:
        logger.error(f"Port {port} is already in use")
        return True
    finally:
        sock.close()

def verify_server_running(port):
    """Verify server is actually responding by trying multiple addresses"""
    try:
        logger.info(f"Starting server verification on port {port}")
        addresses = ['127.0.0.1', 'localhost', '0.0.0.0']
        timeout = 5  # Increased timeout for better reliability

        for attempt in range(3):  # 3 attempts max
            logger.info(f"Verification attempt {attempt + 1}/3")

            for addr in addresses:
                try:
                    url = f'http://{addr}:{port}/'
                    logger.info(f"Trying to connect to {url}")
                    response = requests.get(url, timeout=timeout)

                    if response.status_code == 200:
                        logger.info(f"Server verification successful at {url}")
                        return True
                except requests.RequestException as e:
                    logger.warning(f"Failed to connect to {url}: {str(e)}")
                    continue

            if attempt < 2:  # Don't sleep on last attempt
                logger.info("Waiting before next verification attempt")
                time.sleep(2)

        logger.error("Server verification failed after all attempts")
        return False
    except Exception as e:
        logger.error(f"Server verification error: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        return False

def run():
    """Run the Flask app with detailed logging and error handling"""
    try:
        port = 8080

        if is_port_in_use(port):
            logger.error(f"Port {port} is already in use")
            return False

        logger.info(f"Starting Flask server on port {port}")

        # Basic Flask configuration
        app.config.update(
            ENV='production',
            DEBUG=False,
            TESTING=False,
            PROPAGATE_EXCEPTIONS=True
        )

        # More detailed logging for Flask startup
        logger.info("Flask configuration set")
        logger.info("Starting Flask application...")

        try:
            app.run(
                host='0.0.0.0',
                port=port,
                debug=False,
                use_reloader=False
            )
        except Exception as e:
            logger.error(f"Failed to start Flask server: {str(e)}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            return False

    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        return False

def keep_alive():
    """Start the keep-alive server in a daemon thread with improved reliability"""
    try:
        if is_port_in_use(8080):
            logger.error("Port 8080 is already in use")
            return False

        logger.info("Creating server thread")
        server = Thread(target=run, daemon=True)
        server.start()
        logger.info("Keep-alive server thread started")

        # Increased wait time for server startup
        logger.info("Waiting for server initialization...")
        time.sleep(5)  # Increased from 3 to 5 seconds

        # Verify server is running with improved logging
        if server.is_alive():
            logger.info("Server thread is alive, verifying connection...")
            if verify_server_running(8080):
                logger.info("Keep-alive server started and verified successfully")
                return True
            else:
                logger.error("Server thread is alive but not responding")
                return False
        else:
            logger.error("Server thread failed to start")
            return False

    except Exception as e:
        logger.error(f"Failed to start keep-alive server: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    keep_alive()