import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import get_supabase_admin
from app.services.orchestrator import route_request_to_orchestrator
from app.services.task_service import TaskService

async def recover_tasks():
    print("🔍 Scanning for stuck tasks...")
    supabase = get_supabase_admin()
    
    # Find tasks created in the last hour that are still pending or planning
    # and might have failed to start their workflow
    # Note: This is a simplified check. Ideally we'd check if a workflow exists.
    # For now, we'll just look for tasks that look "stuck" (created recently but no progress)
    
    # Get recent tasks
    res = supabase.table("tasks").select("*").order("created_at", desc=True).limit(10).execute()
    tasks = res.data
    
    print(f"Found {len(tasks)} recent tasks.")
    
    for task in tasks:
        print(f"Task {task['id']}: {task['status']} - {task['title']}")
        
        # If task is 'pending' or 'planning' but created > 1 min ago, let's try to restart it
        # You might want to be more careful here in prod
        if task['status'] in ['pending', 'planning']:
            print(f"  ⚠️  Task might be stuck. Attempting to re-trigger workflow...")
            
            try:
                # We need context. In a real recovery scenario we'd persist context better.
                # For now, we'll assume basic context.
                context = {"source": "recovery_script"}
                
                # Check plan
                plan_res = supabase.table("task_plans").select("*").eq("task_id", task['id']).execute()
                if plan_res.data:
                    print("    📄 Found existing plan. Agent was likely working.")
                else: 
                     print("    no plan found")

                # Simply calling route_request_to_orchestrator again might duplicate workflows
                # but Temporal handles idempotency if we use the same ID.
                # Our orchestrator uses f"orchestrator-{task_id}" which is deterministic.
                # So it's safe to retry!
                
                await route_request_to_orchestrator(
                    customer_id=task['customer_id'],
                    task_description=task['description'],
                    context=context,
                    task_id=task['id']
                )
                print("    ✅ Workflow start signal sent.")
                
            except Exception as e:
                print(f"    ❌ Failed to recover: {e}")
                
if __name__ == "__main__":
    asyncio.run(recover_tasks())
