
import asyncio
import logging
import uuid
import json
import time
from datetime import datetime
from app.services.orchestrator import route_request_to_orchestrator
from app.core.database import get_supabase_admin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_e2e_test():
    supabase = get_supabase_admin()
    
    # 1. Get a test customer
    # We'll pick the first customer/user we find or create a dummy one if needed
    # For this test, we assume a customer exists from previous setup
    res = supabase.table("customers").select("id").limit(1).execute()
    if not res.data:
        logger.error("❌ No customers found in DB. Please create a customer first.")
        return

    customer_id = res.data[0]['id']
    logger.info(f"Using Customer ID: {customer_id}")

    # 2. Define a complex task that triggers Orchestrator
    task_description = "Create a comprehensive social media marketing strategy for our new AI coffee machine launch next month."
    
    logger.info(f"🚀 Starting E2E Test with Task: '{task_description}'")

    # 3. Inject Task (Trigger Workflow)
    # We use route_request_to_orchestrator which starts the Temporal workflow
    context = {
        "source": "e2e_test_script",
        "priority": "high",
        "test_run_id": str(uuid.uuid4())
    }
    
    try:
        # This creates the task record and starts the workflow
        result = await route_request_to_orchestrator(
            customer_id=customer_id,
            task_description=task_description,
            context=context
        )
        task_id = result.get("task_id")
        logger.info(f"✅ Workflow started. Task ID: {task_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to start workflow: {e}")
        return

    # 4. Monitor Progress
    logger.info("👀 Monitoring task progress for up to 60 seconds...")
    
    start_time = time.time()
    last_phase = None
    
    while time.time() - start_time < 60:
        # Fetch task status
        task_res = supabase.table("tasks").select("*").eq("id", task_id).execute()
        if not task_res.data:
            logger.error("Task disappeared!")
            break
            
        task = task_res.data[0]
        status = task.get("status")
        phase = task.get("current_phase")
        metadata = task.get("metadata", {})
        
        # Check for meaningful updates
        if phase != last_phase:
            logger.info(f"🔄 Phase update: {last_phase} -> {phase} (Status: {status})")
            last_phase = phase

        if status == "failed":
            logger.error(f"❌ Task failed! Reason: {metadata.get('error')}")
            break
            
        # Success Criteria 1: Routing determined
        if task.get("assigned_to_ve"):
            logger.info(f"✅ Routing Success! Assigned to VE: {task['assigned_to_ve']}")
            
        # Success Criteria 2: Plan created
        if phase == "planning" and metadata.get("latest_plan_id"):
            plan_id = metadata["latest_plan_id"]
            logger.info(f"✅ Planning Success! Plan ID: {plan_id}")
            
            # Fetch the plan to verify content
            plan_res = supabase.table("task_plans").select("*").eq("id", plan_id).execute()
            if plan_res.data:
                plan = plan_res.data[0]
                logger.info(f"📄 Plan Summary: {plan.get('resources')}") # using 'resources' field as proxy for content check
            
            # If we reached planning, the test is largely successful for the Orchestrator part
            logger.info("🎉 E2E Test Passed: Orchestrator routed and Agent planned the task.")
            break
            
        await asyncio.sleep(2)

    if time.time() - start_time >= 60:
        logger.warning("⚠️ Test timed out waiting for planning completion.")

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
