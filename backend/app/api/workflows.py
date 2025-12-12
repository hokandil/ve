"""
Workflow Status API Endpoints
Provides endpoints for querying Temporal workflow status and progress
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from ..core.security import get_current_user
from ..core.temporal_client import get_temporal_client
from temporalio.client import WorkflowExecutionStatus
import logging

router = APIRouter(prefix="/api/workflows", tags=["workflows"])
logger = logging.getLogger(__name__)


@router.get("/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the current status of a workflow execution.
    
    Returns:
        - status: running, completed, failed, cancelled, terminated
        - start_time: when workflow started
        - close_time: when workflow ended (if completed)
        - run_id: unique run identifier
    """
    try:
        client = await get_temporal_client()
        
        # Get workflow handle
        handle = client.get_workflow_handle(workflow_id)
        
        # Describe workflow
        description = await handle.describe()
        
        # Map Temporal status to our status
        status_map = {
            WorkflowExecutionStatus.RUNNING: "running",
            WorkflowExecutionStatus.COMPLETED: "completed",
            WorkflowExecutionStatus.FAILED: "failed",
            WorkflowExecutionStatus.CANCELED: "cancelled",
            WorkflowExecutionStatus.TERMINATED: "terminated",
            WorkflowExecutionStatus.CONTINUED_AS_NEW: "running",
            WorkflowExecutionStatus.TIMED_OUT: "failed"
        }
        
        return {
            "workflow_id": workflow_id,
            "run_id": description.run_id,
            "status": status_map.get(description.status, "unknown"),
            "workflow_type": description.workflow_type,
            "start_time": description.start_time.isoformat() if description.start_time else None,
            "close_time": description.close_time.isoformat() if description.close_time else None,
            "execution_time_seconds": (
                (description.close_time - description.start_time).total_seconds()
                if description.close_time and description.start_time
                else None
            )
        }
        
    except Exception as e:
        logger.error(f"Failed to get workflow status for {workflow_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")


@router.get("/{workflow_id}/result")
async def get_workflow_result(
    workflow_id: str,
    user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the result of a completed workflow.
    
    Returns the workflow's return value if completed, or error if failed.
    """
    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        
        # Check if workflow is complete
        description = await handle.describe()
        
        if description.status == WorkflowExecutionStatus.RUNNING:
            raise HTTPException(status_code=400, detail="Workflow is still running")
        
        if description.status == WorkflowExecutionStatus.COMPLETED:
            # Get result
            result = await handle.result()
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "result": result
            }
        else:
            # Workflow failed or was cancelled
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": "Workflow did not complete successfully"
            }
            
    except Exception as e:
        logger.error(f"Failed to get workflow result for {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str,
    user = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Cancel a running workflow.
    """
    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        
        # Cancel the workflow
        await handle.cancel()
        
        return {
            "workflow_id": workflow_id,
            "status": "cancelled",
            "message": "Workflow cancellation requested"
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/terminate")
async def terminate_workflow(
    workflow_id: str,
    reason: Optional[str] = "Terminated by user",
    user = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Terminate a running workflow (forceful stop).
    """
    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        
        # Terminate the workflow
        await handle.terminate(reason=reason)
        
        return {
            "workflow_id": workflow_id,
            "status": "terminated",
            "message": f"Workflow terminated: {reason}"
        }
        
    except Exception as e:
        logger.error(f"Failed to terminate workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/history")
async def get_workflow_history(
    workflow_id: str,
    user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the event history of a workflow execution.
    Useful for debugging and understanding workflow execution.
    """
    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        
        # Fetch workflow history
        history = await handle.fetch_history()
        
        # Convert history events to dict
        events = []
        async for event in history:
            events.append({
                "event_id": event.event_id,
                "event_type": event.event_type.name,
                "event_time": event.event_time.isoformat() if event.event_time else None
            })
        
        return {
            "workflow_id": workflow_id,
            "event_count": len(events),
            "events": events[:50]  # Limit to last 50 events
        }
        
    except Exception as e:
        logger.error(f"Failed to get workflow history for {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Query endpoints for specific workflow types
@router.get("/campaign/{workflow_id}/progress")
async def get_campaign_progress(
    workflow_id: str,
    user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Query progress of a ProductLaunchCampaignWorkflow.
    Uses Temporal's query feature.
    """
    try:
        from app.temporal.workflows import ProductLaunchCampaignWorkflow
        
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        
        # Query workflow progress
        progress = await handle.query(ProductLaunchCampaignWorkflow.get_progress)
        
        return {
            "workflow_id": workflow_id,
            "progress": progress
        }
        
    except Exception as e:
        logger.error(f"Failed to query campaign progress for {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaign/{workflow_id}/pause")
async def pause_campaign(
    workflow_id: str,
    user = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Pause a running campaign workflow.
    """
    try:
        from app.temporal.workflows import ProductLaunchCampaignWorkflow
        
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        
        # Send pause signal
        await handle.signal(ProductLaunchCampaignWorkflow.pause_campaign)
        
        return {
            "workflow_id": workflow_id,
            "status": "paused",
            "message": "Campaign paused successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to pause campaign {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaign/{workflow_id}/resume")
async def resume_campaign(
    workflow_id: str,
    user = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Resume a paused campaign workflow.
    """
    try:
        from app.temporal.workflows import ProductLaunchCampaignWorkflow
        
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        
        # Send resume signal
        await handle.signal(ProductLaunchCampaignWorkflow.resume_campaign)
        
        return {
            "workflow_id": workflow_id,
            "status": "resumed",
            "message": "Campaign resumed successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to resume campaign {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaign/{workflow_id}/update-strategy")
async def update_campaign_strategy(
    workflow_id: str,
    new_strategy: str,
    user = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Update the strategy of a running campaign.
    """
    try:
        from app.temporal.workflows import ProductLaunchCampaignWorkflow
        
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        
        # Send update signal
        await handle.signal(ProductLaunchCampaignWorkflow.update_strategy, new_strategy)
        
        return {
            "workflow_id": workflow_id,
            "status": "updated",
            "message": "Campaign strategy updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to update campaign strategy for {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
