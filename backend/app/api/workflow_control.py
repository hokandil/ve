"""
API endpoints for workflow control using signals and queries
"""
from fastapi import APIRouter, Depends, HTTPException
from app.core.temporal_client import get_temporal_client
from app.api.auth import get_current_user
from temporalio.client import WorkflowHandle
from typing import Dict, Any

router = APIRouter(prefix="/workflows/control", tags=["workflow-control"])


@router.post("/{workflow_id}/pause")
async def pause_workflow(
    workflow_id: str,
    user = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Pause an IntelligentDelegationWorkflow using signals.
    The workflow will pause before the next delegation decision.
    """
    try:
        client = await get_temporal_client()
        handle: WorkflowHandle = client.get_workflow_handle(workflow_id)
        
        # Send pause signal
        await handle.signal("pause_delegation")
        
        return {
            "status": "success",
            "message": f"Pause signal sent to workflow {workflow_id}",
            "workflow_id": workflow_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause workflow: {str(e)}")


@router.post("/{workflow_id}/resume")
async def resume_workflow(
    workflow_id: str,
    user = Depends(get_current_user)
) -> Dict[str, str]:
    """Resume a paused IntelligentDelegationWorkflow"""
    try:
        client = await get_temporal_client()
        handle: WorkflowHandle = client.get_workflow_handle(workflow_id)
        
        # Send resume signal
        await handle.signal("resume_delegation")
        
        return {
            "status": "success",
            "message": f"Resume signal sent to workflow {workflow_id}",
            "workflow_id": workflow_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume workflow: {str(e)}")


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str,
    user = Depends(get_current_user)
) -> Dict[str, str]:
    """Cancel an IntelligentDelegationWorkflow"""
    try:
        client = await get_temporal_client()
        handle: WorkflowHandle = client.get_workflow_handle(workflow_id)
        
        # Send cancel signal
        await handle.signal("cancel_delegation")
        
        return {
            "status": "success",
            "message": f"Cancel signal sent to workflow {workflow_id}",
            "workflow_id": workflow_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel workflow: {str(e)}")


@router.get("/{workflow_id}/delegation-status")
async def get_delegation_status(
    workflow_id: str,
    user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Query the current delegation status of a workflow.
    Returns detailed information about delegation chain and decisions.
    """
    try:
        client = await get_temporal_client()
        handle: WorkflowHandle = client.get_workflow_handle(workflow_id)
        
        # Query delegation status
        status = await handle.query("get_delegation_status")
        
        return {
            "workflow_id": workflow_id,
            "delegation_status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query workflow: {str(e)}")


@router.get("/{workflow_id}/delegation-chain")
async def get_delegation_chain(
    workflow_id: str,
    user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get the full delegation chain for a workflow"""
    try:
        client = await get_temporal_client()
        handle: WorkflowHandle = client.get_workflow_handle(workflow_id)
        
        # Query delegation chain
        chain = await handle.query("get_delegation_chain")
        
        return {
            "workflow_id": workflow_id,
            "delegation_chain": chain,
            "chain_length": len(chain) if chain else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query workflow: {str(e)}")
