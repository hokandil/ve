from typing import List, Optional, Dict, Any
from datetime import datetime
from .base import BaseService

class TaskService(BaseService):
    """Service for task operations"""
    
    async def create_task(
        self,
        customer_id: str,
        title: str,
        description: str,
        assigned_to_ve: Optional[str] = None,
        priority: str = "medium",
        due_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a new task"""
        try:
            task_data = {
                "customer_id": customer_id,
                "title": title,
                "description": description,
                "assigned_to_ve": assigned_to_ve,
                "priority": priority,
                "due_date": due_date.isoformat() if due_date else None,
                "status": "pending",
                "created_by_user": True
            }
            
            result = self.supabase.table("tasks").insert(task_data).execute()
            created_task = result.data[0] if result.data else None
            
            if created_task:
                # Enqueue task for processing
                from app.services.redis_queue_service import get_redis_queue_service
                redis_queue = await get_redis_queue_service()
                
                await redis_queue.enqueue_task(
                    task_id=created_task["id"],
                    customer_id=customer_id,
                    task_data={
                        "title": title,
                        "description": description,
                        "assigned_to_ve": assigned_to_ve,
                        "priority": priority
                    },
                    priority=priority
                )
            
            return created_task
        except Exception as e:
            self._handle_error(e, "TaskService.create_task")
    
    async def get_tasks(
        self,
        customer_id: str,
        status: Optional[str] = None,
        assigned_to_ve: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get tasks with optional filters"""
        try:
            query = self.supabase.table("tasks").select("*").eq("customer_id", customer_id)
            
            if status:
                query = query.eq("status", status)
            if assigned_to_ve:
                query = query.eq("assigned_to_ve", assigned_to_ve)
            
            result = query.order("created_at", desc=True).execute()
            return result.data
        except Exception as e:
            self._handle_error(e, "TaskService.get_tasks")
    
    async def update_task(
        self,
        task_id: str,
        customer_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a task"""
        try:
            result = (
                self.supabase.table("tasks")
                .update(updates)
                .eq("id", task_id)
                .eq("customer_id", customer_id)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            self._handle_error(e, "TaskService.update_task")
    
    async def add_comment(
        self,
        task_id: str,
        customer_id: str,
        content: str,
        author_type: str = "user"
    ) -> Dict[str, Any]:
        """Add a comment to a task"""
        try:
            comment_data = {
                "task_id": task_id,
                "customer_id": customer_id,
                "content": content,
                "author_type": author_type,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("task_comments").insert(comment_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self._handle_error(e, "TaskService.add_comment")

    async def get_comments(self, task_id: str, customer_id: str) -> List[Dict[str, Any]]:
        """Get comments for a task"""
        try:
            result = (
                self.supabase.table("task_comments")
                .select("*")
                .eq("task_id", task_id)
                .eq("customer_id", customer_id)
                .order("created_at", desc=False)
                .execute()
            )
            return result.data
        except Exception as e:
            self._handle_error(e, "TaskService.get_comments")

    async def delete_task(self, task_id: str, customer_id: str) -> bool:
        """Delete a task"""
        try:
            # Verify ownership
            check = self.supabase.table("tasks").select("id").eq("id", task_id).eq("customer_id", customer_id).execute()
            if not check.data:
                return False
                
            # Delete task (cascade should handle comments if configured, otherwise might need manual cleanup)
            # Assuming cascade delete is set up in DB for comments
            result = self.supabase.table("tasks").delete().eq("id", task_id).eq("customer_id", customer_id).execute()
            return True
        except Exception as e:
            self._handle_error(e, "TaskService.delete_task")
            return False

    async def provide_feedback(self, task_id: str, customer_id: str, feedback: str) -> bool:
        """Provide user feedback to a running task workflow"""
        
        # 1. Add feedback as a comment
        await self.add_comment(task_id, customer_id, feedback, "customer")
        
        # 2. Add feedback to task metadata (for persistence context)
        response = self.supabase.table("tasks").select("metadata").eq("id", task_id).single().execute()
        if response.data:
            metadata = response.data.get("metadata") or {}
            feedback_history = metadata.get("feedback_history", [])
            feedback_history.append({
                "message": feedback,
                "timestamp": datetime.utcnow().isoformat()
            })
            metadata["feedback_history"] = feedback_history
            
            # Reset waiting status if currently waiting
            update_data = {"metadata": metadata}
            # Note: We let the workflow update the status back to 'in_progress', 
            # but we canoptimistically set it to "processing_feedback" here if we wanted.
            
            self.supabase.table("tasks").update(update_data).eq("id", task_id).execute()
            
        # 3. Signal Temporal Workflow
        try:
            from app.core.temporal_client import get_temporal_client
            client = await get_temporal_client()
            connection = await client.get_service_client() # Verify connection
            
            # Send signal to the workflow
            # Note: We need to know the workflow ID. Convention: f"intelligent-delegation-{task_id}"
            workflow_id = f"intelligent-delegation-{task_id}"
            
            handle = client.get_workflow_handle(workflow_id)
            await handle.signal("provide_feedback", feedback)
            
            return True
        except Exception as e:
            # If workflow not found or error, just log it. The comment is saved anyway.
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to signal workflow for task {task_id}: {e}")
            return False

    async def approve_plan(self, task_id: str, customer_id: str) -> bool:
        """Approve the proposed execution plan for a task"""
        
        # 1. Update Plan Status in DB
        # Find the latest draft plan
        try:
            plan_res = self.supabase.table("task_plans").select("id").eq("task_id", task_id).eq("status", "draft").order("created_at", desc=True).limit(1).execute()
            
            if plan_res.data:
                plan_id = plan_res.data[0]["id"]
                self.supabase.table("task_plans").update({"status": "approved"}).eq("id", plan_id).execute()
                
            # 2. Signal Workflow
            from app.core.temporal_client import get_temporal_client
            client = await get_temporal_client()
            workflow_id = f"intelligent-delegation-{task_id}"
            
            handle = client.get_workflow_handle(workflow_id)
            await handle.signal("approve_plan")
            
            return True
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to signal approve_plan for task {task_id}: {e}")
            return False

    async def get_task_plan(self, task_id: str, customer_id: str) -> Dict[str, Any]:
        """Get the latest plan for a task"""
        try:
            # Check ownership via task
            task_check = self.supabase.table("tasks").select("id").eq("id", task_id).eq("customer_id", customer_id).execute()
            if not task_check.data:
                return None
                
            # specific plan
            result = (
                self.supabase.table("task_plans")
                .select("*")
                .eq("task_id", task_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            self._handle_error(e, "TaskService.get_task_plan")
