"""
VE Marketplace API routes
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from app.schemas import (
    VirtualEmployeeResponse,
    VirtualEmployeeListResponse,
    VirtualEmployeeCreate,
    VirtualEmployeeUpdate,
    HireVERequest,
    CustomerVEResponse,
    SeniorityLevel,
    VEStatus
)
from app.core.database import get_supabase_admin
from app.core.security import get_current_customer_id
from app.services.ve_deployment import deploy_ve_to_kubernetes
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()
from app.services.kagent_service import kagent_service
from app.services.agent_registry_service import agent_registry_service
from app.core.cache import cache_response

@router.get("/kagent/agents")
async def list_kagent_agents():
    """List available agents from KAgent source"""
    return await kagent_service.list_agents()

@router.get("/registry/agents")
async def list_registry_agents():
    """List available agents from upstream Agent Registry"""
    return await agent_registry_service.list_artifacts()


@router.get("/ves", response_model=VirtualEmployeeListResponse)
@cache_response(ttl=300, key_prefix="marketplace_ves")  # Cache for 5 minutes
async def list_marketplace_ves(
    department: Optional[str] = None,
    seniority_level: Optional[SeniorityLevel] = None,
    status: Optional[VEStatus] = VEStatus.STABLE,
    source: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """List available VEs in marketplace"""
    supabase = get_supabase_admin()
    
    try:
        # Build query
        query = supabase.table("virtual_employees").select("*", count="exact")
        
        # Apply filters
        if department:
            query = query.eq("department", department)
        if seniority_level:
            query = query.eq("seniority_level", seniority_level.value if hasattr(seniority_level, 'value') else seniority_level)
        if status:
            query = query.eq("status", status.value if hasattr(status, 'value') else status)
        if source:
            query = query.eq("source", source)
        
        # Pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)
        
        response = query.execute()
        
        return VirtualEmployeeListResponse(
            items=[VirtualEmployeeResponse(**item) for item in response.data],
            total=response.count or 0,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error listing marketplace VEs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ves", response_model=VirtualEmployeeResponse, status_code=201)
async def create_marketplace_ve(ve_data: VirtualEmployeeCreate):
    """Publish a new VE to the marketplace"""
    supabase = get_supabase_admin()
    
    try:
        data = ve_data.model_dump()
        ve_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        data["id"] = ve_id
        data["created_at"] = now
        data["updated_at"] = now
        
        response = supabase.table("virtual_employees").insert(data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create VE")
            
        return VirtualEmployeeResponse(**response.data[0])
        
    except Exception as e:
        logger.error(f"Error creating marketplace VE: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ves/{ve_id}", response_model=VirtualEmployeeResponse)
async def get_marketplace_ve(ve_id: str):
    """Get detailed information about a marketplace VE"""
    supabase = get_supabase_admin()
    
    try:
        response = supabase.table("virtual_employees").select("*").eq("id", ve_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="VE not found")
        
        return VirtualEmployeeResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting VE {ve_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/admin/agents/{ve_id}", response_model=VirtualEmployeeResponse)
async def update_marketplace_metadata(ve_id: str, metadata: VirtualEmployeeUpdate):
    """Update marketplace metadata for an agent"""
    supabase = get_supabase_admin()
    
    try:
        check_response = supabase.table("virtual_employees").select("id").eq("id", ve_id).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="VE not found")
        
        update_data = metadata.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        response = supabase.table("virtual_employees").update(update_data).eq("id", ve_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to update metadata")
        
        return VirtualEmployeeResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating metadata for VE {ve_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/agents/{ve_id}/publish")
async def publish_agent(ve_id: str):
    """Publish an agent to the marketplace"""
    supabase = get_supabase_admin()
    
    try:
        check_response = supabase.table("virtual_employees").select("id").eq("id", ve_id).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="VE not found")
        
        response = supabase.table("virtual_employees").update({
            "status": "stable",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", ve_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to publish agent")
        
        return {"success": True, "message": "Agent published successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing agent {ve_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/agents/{ve_id}/unpublish")
async def unpublish_agent(ve_id: str):
    """Unpublish an agent from the marketplace"""
    supabase = get_supabase_admin()
    
    try:
        check_response = supabase.table("virtual_employees").select("id").eq("id", ve_id).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="VE not found")
        
        response = supabase.table("virtual_employees").update({
            "status": "draft",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", ve_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to unpublish agent")
        
        return {"success": True, "message": "Agent unpublished successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unpublishing agent {ve_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/agents/{ve_id}")
async def delete_marketplace_agent(ve_id: str):
    """Delete an agent from the marketplace"""
    supabase = get_supabase_admin()
    
    try:
        check_response = supabase.table("virtual_employees").select("id").eq("id", ve_id).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="VE not found")
        
        response = supabase.table("virtual_employees").delete().eq("id", ve_id).execute()
        
        return {"success": True, "message": "Agent deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent {ve_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
