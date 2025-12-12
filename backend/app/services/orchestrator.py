"""
Orchestrator Service
Routes customer requests to appropriate VEs via Temporal Workflows
"""
import logging
import uuid
from typing import Dict, Any, Optional
from app.core.database import get_supabase_admin
from app.core.temporal_client import get_temporal_client
from app.temporal.workflows import OrchestratorWorkflow

logger = logging.getLogger(__name__)

async def route_request_to_orchestrator(
    customer_id: str,
    task_description: str,
    context: Dict[str, Any],
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Route a customer request through the shared orchestrator using Temporal.
    """
    try:
        supabase = get_supabase_admin()
        
        # Create task in database if not provided
        if not task_id:
            task_id = str(uuid.uuid4())
            task_data = {
                "id": task_id,
                "customer_id": customer_id,
                "title": task_description[:255],
                "description": task_description,
                "created_by_user": True,
                "status": "pending"
            }
            supabase.table("tasks").insert(task_data).execute()
        
        # Start Temporal Workflow
        client = await get_temporal_client()
        
        workflow_id = f"orchestrator-{task_id}"
        
        await client.start_workflow(
            OrchestratorWorkflow.run,
            args=[{
                "customer_id": customer_id,
                "task_description": task_description,
                "task_id": task_id,
                "context": context
            }],
            id=workflow_id,
            task_queue="campaign-queue"
        )
        
        logger.info(f"Started OrchestratorWorkflow {workflow_id} for task {task_id}")
        
        return {
            "task_id": task_id,
            "workflow_id": workflow_id,
            "status": "pending",
            "message": "Task routing started via Temporal"
        }
        
    except Exception as e:
        logger.error(f"Failed to start orchestrator workflow: {e}")
        # Update task status to failed
        if task_id:
            supabase.table("tasks").update({
                "status": "failed",
                "metadata": {"failure_reason": str(e)}
            }).eq("id", task_id).execute()
        raise

async def route_task_to_ve(
    customer_id: str,
    task_id: str,
    ve_id: str,
    task_description: str
) -> bool:
    """
    Route a specific task directly to a specific VE via Temporal.
    Uses DirectAssignmentWorkflow for simple, direct routing.
    """
    try:
        from app.temporal.workflows import DirectAssignmentWorkflow
        
        client = await get_temporal_client()
        
        workflow_id = f"direct-assignment-{task_id}"
        
        await client.start_workflow(
            DirectAssignmentWorkflow.run,
            args=[{
                "customer_id": customer_id,
                "task_id": task_id,
                "ve_id": ve_id,
                "task_description": task_description
            }],
            id=workflow_id,
            task_queue="campaign-queue"
        )
        
        logger.info(f"Started DirectAssignmentWorkflow {workflow_id} for task {task_id}")
        return True
        
    except Exception as e:
        logger.error(f"route_task_to_ve failed: {e}")
        return False
