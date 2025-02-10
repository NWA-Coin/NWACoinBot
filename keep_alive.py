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

def find_available_port(start_port=3000, max_attempts=5):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(2)
            sock.bind(('0.0.0.0', port))
            sock.close()
            logger.info(f"Found available port: {port}")
            return port
        except socket.error as e:
            logger.warning(f"Port {port} is not available: {str(e)}")
        finally:
            try:
                sock.close()
            except:
                pass
    return None

def verify_server_running(port):
    """Verify server is actually responding with improved reliability"""
    try:
        logger.info(f"Starting server verification on port {port}")
        addresses = ['127.0.0.1', 'localhost', '0.0.0.0']
        timeout = 10  # Increased timeout for better reliability
        max_retries = 5
        retry_delay = 2

        for attempt in range(max_retries):
            logger.info(f"Verification attempt {attempt + 1}/{max_retries}")

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

            if attempt < max_retries - 1:
                logger.info(f"Waiting {retry_delay}s before next verification attempt")
                time.sleep(retry_delay)

        logger.error("Server verification failed after all attempts")
        return False
    except Exception as e:
        logger.error(f"Server verification error: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        return False

def run(port):
    """Run the Flask app with enhanced reliability"""
    try:
        logger.info(f"Starting Flask server on port {port}")

        # Enhanced Flask configuration
        app.config.update(
            ENV='production',
            DEBUG=False,
            TESTING=False,
            PROPAGATE_EXCEPTIONS=True,
            SERVER_NAME=None,  # Allow all hostnames
            PREFERRED_URL_SCHEME='http'
        )

        logger.info("Flask configuration set")
        logger.info("Starting Flask application...")

        try:
            app.run(
                host='0.0.0.0',
                port=port,
                debug=False,
                use_reloader=False,
                threaded=True
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
    """Start the keep-alive server with improved reliability"""
    try:
        # Find an available port
        port = find_available_port()
        if port is None:
            logger.error("No available ports found")
            return None

        logger.info("Creating server thread")
        server = Thread(target=lambda: run(port), daemon=True)
        server.start()
        logger.info("Keep-alive server thread started")

        # Wait for server initialization
        startup_wait = 10
        logger.info(f"Waiting {startup_wait}s for server initialization...")
        time.sleep(startup_wait)

        # Verify server is running
        if server.is_alive():
            logger.info("Server thread is alive, verifying connection...")
            if verify_server_running(port):
                logger.info("Keep-alive server started and verified successfully")
                return port
            else:
                logger.error("Server thread is alive but not responding")
                return None
        else:
            logger.error("Server thread failed to start")
            return None

    except Exception as e:
        logger.error(f"Failed to start keep-alive server: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        return None

if __name__ == "__main__":
    keep_alive()