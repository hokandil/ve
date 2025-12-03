"""
Mock Orchestrator Service
Simulates VE responses for testing without AI costs
"""
import asyncio
import random
from datetime import datetime
from typing import Dict, Any
from .base import BaseService

class MockOrchestratorService(BaseService):
    """Mock service to simulate VE task processing"""
    
    async def process_task(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """Simulate VE processing a task"""
        try:
            # Simulate work delay
            await asyncio.sleep(5)
            
            # Update task to in_progress
            self.supabase.table("tasks").update({
                "status": "in_progress",
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", task_id).execute()
            
            # Simulate more work
            await asyncio.sleep(10)
            
            # Add a comment
            comment_responses = [
                "I'm working on this task now. Will have it completed shortly.",
                "Making good progress on this. Should be done soon!",
                "I've started analyzing the requirements. Looking good so far.",
                "Working through this systematically. Updates coming soon.",
            ]
            
            self.supabase.table("task_comments").insert({
                "task_id": task_id,
                "customer_id": task_data["customer_id"],
                "content": random.choice(comment_responses),
                "author_type": "ve",
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            # Simulate final work
            await asyncio.sleep(5)
            
            # Complete the task
            completion_messages = [
                "Task completed successfully! Please review.",
                "All done! Let me know if you need any changes.",
                "Finished! Everything should be working as expected.",
                "Completed as requested. Ready for your review.",
            ]
            
            self.supabase.table("tasks").update({
                "status": "review",
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", task_id).execute()
            
            self.supabase.table("task_comments").insert({
                "task_id": task_id,
                "customer_id": task_data["customer_id"],
                "content": random.choice(completion_messages),
                "author_type": "ve",
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
        except Exception as e:
            self._handle_error(e, "MockOrchestratorService.process_task")
