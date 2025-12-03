"""VE Context API routes"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.core.database import get_supabase_admin
from app.core.security import get_current_customer_id
from app.services.ve_context_service import get_ve_context_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class AddLearningRequest(BaseModel):
    customer_ve_id: str
    lesson: str
    category: str = "general"
    metadata: Optional[Dict[str, Any]] = None


class ShareLearningRequest(BaseModel):
    lesson: str
    category: str = "shared"


@router.get("/{customer_ve_id}")
async def get_ve_context(
    customer_ve_id: str,
    customer_id: str = Depends(get_current_customer_id)
):
    """Get VE context/memory"""
    try:
        # Verify VE belongs to customer
        supabase = get_supabase_admin()
        ve_response = supabase.table("customer_ves")\
            .select("id")\
            .eq("id", customer_ve_id)\
            .eq("customer_id", customer_id)\
            .execute()
        
        if not ve_response.data:
            raise HTTPException(status_code=404, detail="VE not found")
        
        context_service = get_ve_context_service()
        context = await context_service.get_context(customer_ve_id)
        
        return {"customer_ve_id": customer_ve_id, "context": context or {}}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get VE context: {e}")
        raise HTTPException(status_code=500, detail="Failed to get context")


@router.get("/{customer_ve_id}/learnings")
async def get_ve_learnings(
    customer_ve_id: str,
    category: Optional[str] = None,
    customer_id: str = Depends(get_current_customer_id)
):
    """Get VE learnings, optionally filtered by category"""
    try:
        # Verify VE belongs to customer
        supabase = get_supabase_admin()
        ve_response = supabase.table("customer_ves")\
            .select("id")\
            .eq("id", customer_ve_id)\
            .eq("customer_id", customer_id)\
            .execute()
        
        if not ve_response.data:
            raise HTTPException(status_code=404, detail="VE not found")
        
        context_service = get_ve_context_service()
        learnings = await context_service.get_learnings(customer_ve_id, category)
        
        return {"customer_ve_id": customer_ve_id, "learnings": learnings}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get VE learnings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get learnings")


@router.post("/{customer_ve_id}/learnings")
async def add_ve_learning(
    customer_ve_id: str,
    request: AddLearningRequest,
    customer_id: str = Depends(get_current_customer_id)
):
    """Add a learning to VE memory (for manual corrections/improvements)"""
    try:
        # Verify VE belongs to customer
        supabase = get_supabase_admin()
        ve_response = supabase.table("customer_ves")\
            .select("id")\
            .eq("id", customer_ve_id)\
            .eq("customer_id", customer_id)\
            .execute()
        
        if not ve_response.data:
            raise HTTPException(status_code=404, detail="VE not found")
        
        context_service = get_ve_context_service()
        success = await context_service.add_learning(
            customer_ve_id=customer_ve_id,
            lesson=request.lesson,
            category=request.category,
            metadata=request.metadata
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add learning")
        
        return {"message": "Learning added successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add VE learning: {e}")
        raise HTTPException(status_code=500, detail="Failed to add learning")


@router.post("/learnings/share")
async def share_learning(
    request: ShareLearningRequest,
    customer_id: str = Depends(get_current_customer_id)
):
    """Share a learning across all customer VEs"""
    try:
        context_service = get_ve_context_service()
        count = await context_service.share_learning_across_ves(
            customer_id=customer_id,
            lesson=request.lesson,
            category=request.category
        )
        
        return {
            "message": f"Learning shared across {count} VEs",
            "ves_updated": count
        }
        
    except Exception as e:
        logger.error(f"Failed to share learning: {e}")
        raise HTTPException(status_code=500, detail="Failed to share learning")
