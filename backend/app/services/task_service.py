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
