import logging
import asyncio
import time
import psutil
import os
from datetime import datetime, timedelta
import signal
import sys
import gc

logger = logging.getLogger('discord_bot')

class BotSupervisor:
    def __init__(self):
        self.last_heartbeat = datetime.now()
        self.is_running = True
        self.consecutive_failures = 0
        self.MAX_FAILURES = 5  # Increased for more retry attempts
        self.HEARTBEAT_INTERVAL = 15  # Reduced for quicker detection
        self.RESTART_COOLDOWN = 60  # Reduced cooldown for faster recovery
        self.last_restart = datetime.now()
        self.process = psutil.Process(os.getpid())
        self.memory_threshold = 85  # Memory threshold percentage

    async def monitor(self, bot):
        """Monitor bot's health and manage reconnection."""
        logger.info("Starting bot supervisor monitoring")

        while self.is_running:
            try:
                await asyncio.sleep(self.HEARTBEAT_INTERVAL)

                # Check bot connection
                if bot.is_closed():
                    logger.warning("Bot connection is closed")
                    await self.handle_disconnection(bot)
                else:
                    self.consecutive_failures = 0
                    self.last_heartbeat = datetime.now()
                    logger.info("Bot heartbeat: Connection healthy")

                # Proactive memory management
                memory_percent = self.process.memory_percent()
                if memory_percent > self.memory_threshold:
                    logger.warning(f"High memory usage: {memory_percent:.1f}%")
                    self.cleanup_resources()

            except Exception as e:
                logger.error(f"Error in supervisor monitoring: {str(e)}")
                await asyncio.sleep(5)

    async def handle_disconnection(self, bot):
        """Handle bot disconnection with progressive backoff."""
        self.consecutive_failures += 1

        # Check restart cooldown
        time_since_restart = (datetime.now() - self.last_restart).total_seconds()
        if time_since_restart < self.RESTART_COOLDOWN:
            logger.info(f"Waiting for restart cooldown: {self.RESTART_COOLDOWN - time_since_restart:.0f}s remaining")
            await asyncio.sleep(15)  # Reduced wait time
            return

        if self.consecutive_failures > self.MAX_FAILURES:
            logger.critical("Maximum consecutive failures reached!")
            await self.emergency_restart(bot)
            return

        # Progressive backoff with maximum cap
        delay = min(15 * (2 ** (self.consecutive_failures - 1)), 120)  # Max 2 minutes
        logger.info(f"Attempting reconnection in {delay} seconds (attempt {self.consecutive_failures})")

        await asyncio.sleep(delay)

        if bot.is_closed():
            try:
                logger.info("Initiating reconnection sequence")
                await bot.close()  # Ensure clean shutdown
                self.cleanup_resources()  # Clean up before restart
                await bot.start(bot.http.token, reconnect=True)
                self.last_restart = datetime.now()
                logger.info("Bot successfully reconnected")
            except Exception as e:
                logger.error(f"Failed to reconnect: {str(e)}")

    async def emergency_restart(self, bot):
        """Emergency restart procedure for critical failures."""
        logger.warning("Initiating emergency restart procedure")

        try:
            # Aggressive cleanup
            self.cleanup_resources()
            gc.collect()  # Force garbage collection

            await bot.close()
            logger.info("Bot connection closed for emergency restart")

            # Reduced cooldown for emergency restart
            await asyncio.sleep(30)

            # Reset failure counter and update restart time
            self.consecutive_failures = 0
            self.last_restart = datetime.now()

            # Attempt restart
            await bot.start(bot.http.token, reconnect=True)
            logger.info("Emergency restart completed successfully")

        except Exception as e:
            logger.critical(f"Emergency restart failed: {str(e)}")
            # Let the process manager handle restart
            sys.exit(1)

    def cleanup_resources(self):
        """Clean up system resources."""
        try:
            # Force garbage collection
            gc.collect()

            # Close any remaining connections
            for conn in self.process.connections():
                try:
                    conn.close()
                except:
                    pass

            logger.info("Resource cleanup completed")
        except Exception as e:
            logger.error(f"Error during resource cleanup: {str(e)}")

    def stop(self):
        """Stop the supervisor."""
        self.is_running = False
        self.cleanup_resources()
        logger.info("Bot supervisor stopped")

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)