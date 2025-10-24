import asyncio
import logging
import signal

from ..services.queue_service import queue_service
from ..database.connection import init_db

logger = logging.getLogger(__name__)

class TestExecutorWorker:
    """Background worker for processing test execution queue."""
    
    def __init__(self, max_concurrent: int = 1, poll_interval: int = 5):
        self.max_concurrent = max_concurrent
        self.poll_interval = poll_interval
        self.running = False
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    # PUBLIC_INTERFACE
    async def start(self):
        """
        Start the worker to process the execution queue.
        
        This method runs indefinitely, polling the queue for new items
        and executing them as background tasks.
        """
        logger.info("Starting test executor worker...")
        self.running = True
        
        # Initialize database
        init_db()
        
        while self.running:
            try:
                # Process queue items
                await queue_service.process_queue(
                    user_id="system",  # System user for worker executions
                    max_concurrent=self.max_concurrent
                )
                
                # Wait before next poll
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                await asyncio.sleep(self.poll_interval)
        
        logger.info("Test executor worker stopped")
    
    # PUBLIC_INTERFACE
    def stop(self):
        """Stop the worker."""
        self.running = False

# PUBLIC_INTERFACE
async def run_worker():
    """
    Entry point for running the test executor worker.
    
    This function can be called from a separate process or container
    to run the background worker.
    """
    worker = TestExecutorWorker()
    await worker.start()

if __name__ == "__main__":
    # Allow running worker directly
    asyncio.run(run_worker())
