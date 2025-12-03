"""
Background worker to process tasks
Can be run as: python -m app.workers.task_worker
"""
import asyncio
import os
from supabase import create_client
from app.services.mock_orchestrator import MockOrchestratorService

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

async def listen_for_tasks():
    """Listen for new tasks and process them"""
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    orchestrator = MockOrchestratorService(supabase)
    
    print("🤖 Mock Orchestrator Worker started...")
    print("Listening for new tasks...")
    
    while True:
        try:
            # Poll for pending tasks
            result = supabase.table("tasks").select("*").eq("status", "pending").execute()
            
            if result.data:
                for task in result.data:
                    print(f"📋 Processing task: {task['id']} - {task['title']}")
                    # Process task in background
                    asyncio.create_task(orchestrator.process_task(task['id'], task))
            
            # Wait before next poll
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"❌ Error in worker: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(listen_for_tasks())
