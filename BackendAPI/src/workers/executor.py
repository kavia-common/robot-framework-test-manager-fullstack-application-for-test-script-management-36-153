"""
Background worker for processing test execution queue.
"""

import asyncio

from src.database.session import SessionLocal
from src.services.queue_service import queue_service
from src.services.execution_service import execution_service
from src.utils.logging import get_logger
from src.config import settings

logger = get_logger(__name__)


class QueueExecutor:
    """Background worker for executing queued test cases."""
    
    def __init__(self):
        """Initialize the queue executor."""
        self.running = False
        self.max_concurrent = settings.max_concurrent_executions
        self.active_executions = []
    
    async def start(self):
        """Start the queue executor."""
        self.running = True
        logger.info("Queue executor started")
        
        while self.running:
            try:
                await self._process_queue()
                await asyncio.sleep(5)  # Poll every 5 seconds
            except Exception as e:
                logger.error(f"Error in queue executor: {str(e)}")
                await asyncio.sleep(10)  # Back off on error
    
    async def stop(self):
        """Stop the queue executor."""
        self.running = False
        logger.info("Queue executor stopped")
    
    async def _process_queue(self):
        """Process queued items."""
        if len(self.active_executions) >= self.max_concurrent:
            # Max concurrent executions reached
            return
        
        db = SessionLocal()
        try:
            # Get next item from queue
            item = queue_service.get_next_item(db)
            
            if item:
                logger.info(f"Processing queue item {item.id} for case {item.case_id}")
                
                # Start execution
                task = asyncio.create_task(
                    self._execute_queued_item(item.id, item.case_id)
                )
                self.active_executions.append(task)
                
                # Clean up completed tasks
                self.active_executions = [
                    t for t in self.active_executions if not t.done()
                ]
        finally:
            db.close()
    
    async def _execute_queued_item(self, item_id: str, case_id: str):
        """Execute a queued test case."""
        db = SessionLocal()
        try:
            # Execute test case
            run_id = await execution_service.execute_test_case(db, case_id, "system")
            
            # Wait for execution to complete (simplified)
            await asyncio.sleep(5)  # TODO: Implement proper completion check
            
            # Mark queue item as completed
            queue_service.complete_queue_item(db, item_id, run_id, success=True)
            
            logger.info(f"Completed queue item {item_id}")
            
        except Exception as e:
            logger.error(f"Failed to execute queue item {item_id}: {str(e)}")
            queue_service.complete_queue_item(db, item_id, "", success=False)
        finally:
            db.close()


# PUBLIC_INTERFACE
async def run_queue_executor():
    """
    Run the queue executor.
    
    This function should be run as a background task or separate process.
    """
    executor = QueueExecutor()
    await executor.start()


if __name__ == "__main__":
    # Run executor standalone
    asyncio.run(run_queue_executor())
