from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from ..core.security import get_current_user
from ..core.database import get_supabase_admin
from ..services.task_service import TaskService

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

from app.schemas import TaskCreate, TaskUpdate, CommentCreate

@router.post("")
async def create_task(
    task: TaskCreate,
    user = Depends(get_current_user)
):
    """Create a new task"""
    supabase = get_supabase_admin()
    service = TaskService(supabase)
    
    result = await service.create_task(
        customer_id=user["id"],
        title=task.title,
        description=task.description,
        assigned_to_ve=task.assigned_to_ve,
        priority=task.priority,
        due_date=task.due_date
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create task")
        
    # If assigned to a VE, route it via Agent Gateway
    if task.assigned_to_ve:
        try:
            # 1. Get VE details to find agent_type
            ve_response = supabase.table("customer_ves")\
                .select("agent_type, persona_name")\
                .eq("id", task.assigned_to_ve)\
                .single()\
                .execute()
            
            if ve_response.data:
                ve_data = ve_response.data
                agent_type = ve_data.get("agent_type")
                persona_name = ve_data.get("persona_name", "Virtual Employee")
                
                if agent_type:
                    # 2. Invoke agent
                    from app.services.agent_gateway_service import agent_gateway_service
                    
                    # Format task as a message
                    prompt = f"New Task Assigned: {task.title}\n\nDescription: {task.description}\n\nPriority: {task.priority}\nDue Date: {task.due_date}"
                    
                    agent_response = await agent_gateway_service.invoke_agent(
                        customer_id=user["id"],
                        agent_type=agent_type,
                        message=prompt,
                        user_id=user["id"]
                    )
                    
                    # 3. Add agent response as a comment
                    if agent_response and "message" in agent_response:
                        await service.add_comment(
                            task_id=result["id"],
                            customer_id=user["id"],
                            content=agent_response["message"],
                            author_type="ve"  # Mark as VE comment
                        )
        except Exception as e:
            # Log error but don't fail the task creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to route task to VE: {e}")
    else:
        # If NOT assigned to a VE, let the Orchestrator handle it
        try:
            from app.services.orchestrator import route_request_to_orchestrator
            
            # Run orchestrator routing in background or await it
            # For better UX in this demo, we await it to ensure it's routed when the user checks
            await route_request_to_orchestrator(
                customer_id=user["id"],
                task_description=f"Title: {task.title}\nDescription: {task.description}\nPriority: {task.priority}",
                context={
                    "task_id": result["id"],
                    "priority": task.priority,
                    "due_date": str(task.due_date) if task.due_date else None
                },
                task_id=result["id"]
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to invoke orchestrator: {e}")
    
    return result

@router.get("")
async def get_tasks(
    status: Optional[str] = None,
    assigned_to_ve: Optional[str] = None,
    user = Depends(get_current_user)
):
    """Get tasks with optional filters"""
    supabase = get_supabase_admin()
    service = TaskService(supabase)
    
    tasks = await service.get_tasks(
        customer_id=user["id"],
        status=status,
        assigned_to_ve=assigned_to_ve
    )
    
    return tasks

@router.patch("/{task_id}")
async def update_task(
    task_id: str,
    updates: TaskUpdate,
    user = Depends(get_current_user)
):
    """Update a task"""
    supabase = get_supabase_admin()
    service = TaskService(supabase)
    
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    
    result = await service.update_task(
        task_id=task_id,
        customer_id=user["id"],
        updates=update_data
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return result

@router.post("/{task_id}/comments")
async def add_comment(
    task_id: str,
    comment: CommentCreate,
    user = Depends(get_current_user)
):
    """Add a comment to a task"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from ..core.security import get_current_user
from ..core.database import get_supabase_admin
from ..services.task_service import TaskService

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

from app.schemas import TaskCreate, TaskUpdate, CommentCreate

@router.post("")
async def create_task(
    task: TaskCreate,
    user = Depends(get_current_user)
):
    """Create a new task"""
    supabase = get_supabase_admin()
    service = TaskService(supabase)
    
    result = await service.create_task(
        customer_id=user["id"],
        title=task.title,
        description=task.description,
        assigned_to_ve=task.assigned_to_ve,
        priority=task.priority,
        due_date=task.due_date
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create task")
        
    # If assigned to a VE, route it via Agent Gateway
    if task.assigned_to_ve:
        try:
            # 1. Get VE details to find agent_type
            ve_response = supabase.table("customer_ves")\
                .select("agent_type, persona_name")\
                .eq("id", task.assigned_to_ve)\
                .single()\
                .execute()
            
            if ve_response.data:
                ve_data = ve_response.data
                agent_type = ve_data.get("agent_type")
                persona_name = ve_data.get("persona_name", "Virtual Employee")
                
                if agent_type:
                    # 2. Invoke agent
                    from app.services.agent_gateway_service import agent_gateway_service
                    
                    # Format task as a message
                    prompt = f"New Task Assigned: {task.title}\n\nDescription: {task.description}\n\nPriority: {task.priority}\nDue Date: {task.due_date}"
                    
                    agent_response = await agent_gateway_service.invoke_agent(
                        customer_id=user["id"],
                        agent_type=agent_type,
                        message=prompt,
                        user_id=user["id"]
                    )
                    
                    # 3. Add agent response as a comment
                    if agent_response and "message" in agent_response:
                        await service.add_comment(
                            task_id=result["id"],
                            customer_id=user["id"],
                            content=agent_response["message"],
                            author_type="ve"  # Mark as VE comment
                        )
        except Exception as e:
            # Log error but don't fail the task creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to route task to VE: {e}")
    else:
        # If NOT assigned to a VE, let the Orchestrator handle it
        try:
            from app.services.orchestrator import route_request_to_orchestrator
            
            # Run orchestrator routing in background or await it
            # For better UX in this demo, we await it to ensure it's routed when the user checks
            await route_request_to_orchestrator(
                customer_id=user["id"],
                task_description=f"Title: {task.title}\nDescription: {task.description}\nPriority: {task.priority}",
                context={
                    "task_id": result["id"],
                    "priority": task.priority,
                    "due_date": str(task.due_date) if task.due_date else None
                },
                task_id=result["id"]
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to invoke orchestrator: {e}")
    
    return result

@router.get("")
async def get_tasks(
    status: Optional[str] = None,
    assigned_to_ve: Optional[str] = None,
    user = Depends(get_current_user)
):
    """Get tasks with optional filters"""
    supabase = get_supabase_admin()
    service = TaskService(supabase)
    
    tasks = await service.get_tasks(
        customer_id=user["id"],
        status=status,
        assigned_to_ve=assigned_to_ve
    )
    
    return tasks

@router.patch("/{task_id}")
async def update_task(
    task_id: str,
    updates: TaskUpdate,
    user = Depends(get_current_user)
):
    """Update a task"""
    supabase = get_supabase_admin()
    service = TaskService(supabase)
    
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    
    result = await service.update_task(
        task_id=task_id,
        customer_id=user["id"],
        updates=update_data
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return result

@router.post("/{task_id}/comments")
async def add_comment(
    task_id: str,
    comment: CommentCreate,
    user = Depends(get_current_user)
):
    """Add a comment to a task"""
    supabase = get_supabase_admin()
    service = TaskService(supabase)
    
    result = await service.add_comment(
        task_id=task_id,
        customer_id=user["id"],
        content=comment.content,
        author_type="customer"
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to add comment")
    
    return result

@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    user = Depends(get_current_user)
):
    """Delete a task"""
    supabase = get_supabase_admin()
    service = TaskService(supabase)
    
    result = await service.delete_task(
        task_id=task_id,
        customer_id=user["id"]
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return None
