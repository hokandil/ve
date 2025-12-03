"""Orchestrator API routes"""
from fastapi import APIRouter, Depends
from app.schemas import OrchestratorRequest, OrchestratorResponse
from app.core.security import get_current_customer_id
from app.services.orchestrator import route_request_to_orchestrator

router = APIRouter()

@router.post("/route", response_model=OrchestratorResponse)
async def route_to_orchestrator(
    request: OrchestratorRequest,
    customer_id: str = Depends(get_current_customer_id)
):
    """Route a request through the orchestrator"""
    result = await route_request_to_orchestrator(
        customer_id=customer_id,
        task_description=request.task_description,
        context=request.context or {}
    )
    return result
