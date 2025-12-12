"""
Production-ready Temporal Worker with auto-reload and resilience
"""
import asyncio
import logging
import sys
import os
from temporalio.client import Client
from temporalio.worker import Worker
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.temporal.workflows import (
    OrchestratorWorkflow,
    IntelligentDelegationWorkflow
)
from app.temporal.activities import (
    get_customer_ves_activity,
    analyze_routing_activity,
    invoke_agent_activity,
    analyze_and_decide_delegation_activity,
    update_task_status_activity,
    save_task_result_activity,
    create_task_plan_activity
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global worker instance
worker_instance = None
should_restart = False

class CodeChangeHandler(FileSystemEventHandler):
    """Watch for Python file changes and trigger worker restart"""
    
    def on_modified(self, event):
        global should_restart
        if event.src_path.endswith('.py'):
            logger.info(f"Code change detected: {event.src_path}")
            should_restart = True

async def run_worker():
    """Run the Temporal worker with all workflows and activities"""
    global worker_instance
    
    try:
        # Connect to Temporal
        logger.info("Connecting to Temporal Server at localhost:7233...")
        client = await Client.connect("localhost:7233")
        logger.info("Connected to Temporal Server.")
        
        # Create worker
        logger.info("Starting Temporal Worker on queue 'campaign-queue'...")
        worker_instance = Worker(
            client,
            task_queue="campaign-queue",
            workflows=[
                OrchestratorWorkflow,
                IntelligentDelegationWorkflow
            ],
            activities=[
                get_customer_ves_activity,
                analyze_routing_activity,
                invoke_agent_activity,
                analyze_and_decide_delegation_activity,
                update_task_status_activity,
                save_task_result_activity,
                create_task_plan_activity
            ],
        )
        
        logger.info("✅ Temporal worker started successfully")
        logger.info("📊 Polling for tasks on task queue: campaign-queue")
        logger.info("🔄 Auto-reload enabled - watching for code changes...")
        
        # Run worker
        await worker_instance.run()
        
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
        raise

async def main_with_autoreload():
    """Main function with auto-reload capability"""
    global should_restart
    
    # Set up file watcher for auto-reload
    watch_paths = [
        os.path.join(os.path.dirname(__file__), '..', 'temporal'),
        os.path.join(os.path.dirname(__file__), '..', 'schemas.py'),
        os.path.join(os.path.dirname(__file__), '..', 'services'),
    ]
    
    observer = Observer()
    handler = CodeChangeHandler()
    
    for path in watch_paths:
        if os.path.exists(path):
            observer.schedule(handler, path, recursive=True)
            logger.info(f"Watching for changes in: {path}")
    
    observer.start()
    
    try:
        while True:
            should_restart = False
            
            # Run worker
            worker_task = asyncio.create_task(run_worker())
            
            # Wait for either completion or restart signal
            while not should_restart:
                if worker_task.done():
                    # Worker stopped, check for errors
                    try:
                        await worker_task
                    except Exception as e:
                        logger.error(f"Worker crashed: {e}")
                        logger.info("Restarting worker in 5 seconds...")
                        await asyncio.sleep(5)
                    break
                await asyncio.sleep(0.5)
            
            if should_restart:
                logger.info("🔄 Code change detected - restarting worker...")
                # Cancel current worker
                if not worker_task.done():
                    worker_task.cancel()
                    try:
                        await worker_task
                    except asyncio.CancelledError:
                        pass
                
                # Wait a bit for file system to settle
                await asyncio.sleep(2)
                logger.info("♻️  Reloading worker with new code...")
                
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
    finally:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    # Check if auto-reload is enabled
    auto_reload = os.getenv("WORKER_AUTO_RELOAD", "true").lower() == "true"
    
    if auto_reload:
        logger.info("🚀 Starting worker with AUTO-RELOAD enabled")
        asyncio.run(main_with_autoreload())
    else:
        logger.info("🚀 Starting worker (auto-reload disabled)")
        asyncio.run(run_worker())
