import logging
import asyncio
import time
import psutil
import os
from datetime import datetime, timedelta
import signal
import sys

logger = logging.getLogger('discord_bot')

class BotSupervisor:
    def __init__(self):
        self.last_heartbeat = datetime.now()
        self.is_running = True
        self.consecutive_failures = 0
        self.MAX_FAILURES = 3
        self.HEARTBEAT_INTERVAL = 30  # seconds
        self.RESTART_COOLDOWN = 300   # 5 minutes
        self.last_restart = datetime.now()
        self.process = psutil.Process(os.getpid())

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
                    # Reset failure counter on successful connection
                    self.consecutive_failures = 0
                    self.last_heartbeat = datetime.now()
                    logger.info("Bot heartbeat: Connection healthy")

                # Monitor memory usage
                memory_percent = self.process.memory_percent()
                if memory_percent > 90:  # Alert if memory usage is high
                    logger.warning(f"High memory usage detected: {memory_percent:.1f}%")
                    if memory_percent > 95:  # Force garbage collection if critical
                        logger.warning("Critical memory usage - forcing garbage collection")
                        import gc
                        gc.collect()

            except Exception as e:
                logger.error(f"Error in supervisor monitoring: {str(e)}")
                await asyncio.sleep(5)

    async def handle_disconnection(self, bot):
        """Handle bot disconnection with progressive backoff."""
        self.consecutive_failures += 1

        # Check if enough time has passed since last restart
        time_since_restart = (datetime.now() - self.last_restart).total_seconds()
        if time_since_restart < self.RESTART_COOLDOWN:
            logger.info(f"Waiting for restart cooldown: {self.RESTART_COOLDOWN - time_since_restart:.0f}s remaining")
            await asyncio.sleep(30)
            return

        if self.consecutive_failures > self.MAX_FAILURES:
            logger.critical("Maximum consecutive failures reached!")
            await self.emergency_restart(bot)
            return

        delay = min(30 * (2 ** (self.consecutive_failures - 1)), 300)  # Max 5 minutes
        logger.info(f"Attempting reconnection in {delay} seconds (attempt {self.consecutive_failures})")

        await asyncio.sleep(delay)

        if bot.is_closed():
            try:
                logger.info("Initiating reconnection sequence")
                await bot.close()  # Ensure clean shutdown
                await bot.start(bot.http.token, reconnect=True)
                self.last_restart = datetime.now()
                logger.info("Bot successfully reconnected")
            except Exception as e:
                logger.error(f"Failed to reconnect: {str(e)}")

    async def emergency_restart(self, bot):
        """Emergency restart procedure for critical failures."""
        logger.warning("Initiating emergency restart procedure")

        try:
            # Cleanup resources
            self.cleanup_resources()

            await bot.close()
            logger.info("Bot connection closed for emergency restart")

            # Wait for cooldown period
            await asyncio.sleep(self.RESTART_COOLDOWN)

            # Reset failure counter and update restart time
            self.consecutive_failures = 0
            self.last_restart = datetime.now()

            # Force garbage collection before restart
            import gc
            gc.collect()

            # Attempt restart
            await bot.start(bot.http.token, reconnect=True)
            logger.info("Emergency restart completed successfully")

        except Exception as e:
            logger.critical(f"Emergency restart failed: {str(e)}")
            sys.exit(1)  # Exit for external process manager to handle

    def cleanup_resources(self):
        """Clean up system resources."""
        try:
            # Force garbage collection
            import gc
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