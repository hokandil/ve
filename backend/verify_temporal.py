"""
Verify Temporal Integration
"""
import asyncio
import sys
import os
import logging

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from app.core.config import settings
from app.services.orchestrator import route_request_to_orchestrator
from app.temporal.worker import run_worker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify():
    print("1. Starting Worker in background...")
    # In a real test we'd run this in a separate process, 
    # but for this script we'll just try to connect client first to check connectivity.
    
    try:
        from app.core.temporal_client import get_temporal_client
        client = await get_temporal_client()
        print("   Connected to Temporal Server successfully.")
    except Exception as e:
        print(f"   FAILED to connect to Temporal Server: {e}")
        print("   Please ensure Temporal Server is running (e.g., 'temporal server start-dev').")
        return

    print("\n2. Triggering Orchestrator Workflow...")
    try:
        result = await route_request_to_orchestrator(
            customer_id="test-customer",
            task_description="Test task for Temporal",
            context={"source": "verification_script"}
        )
        print(f"   Workflow started! Workflow ID: {result.get('workflow_id')}")
        print(f"   Task ID: {result.get('task_id')}")
    except Exception as e:
        print(f"   FAILED to trigger workflow: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
