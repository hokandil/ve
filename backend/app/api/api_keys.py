"""API Key Management API routes"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.core.security import get_current_customer_id
from app.services.api_key_service import get_api_key_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class CreateAPIKeyRequest(BaseModel):
    name: str
    key_type: str = "agent"  # "agent" or "service"
    metadata: Optional[Dict[str, Any]] = None


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_type: str
    is_active: bool
    created_at: str
    last_used_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    plain_key: Optional[str] = None  # Only returned on creation


@router.post("", response_model=APIKeyResponse, status_code=201)
async def create_api_key(
    request: CreateAPIKeyRequest,
    customer_id: str = Depends(get_current_customer_id)
):
    """
    Create a new API key for agent authentication
    The plain key is only shown once - store it securely!
    """
    try:
        api_key_service = get_api_key_service()
        
        result = await api_key_service.create_api_key(
            customer_id=customer_id,
            name=request.name,
            key_type=request.key_type,
            metadata=request.metadata
        )
        
        return APIKeyResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to create API key")


@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    customer_id: str = Depends(get_current_customer_id)
):
    """List all API keys for the customer"""
    try:
        api_key_service = get_api_key_service()
        keys = await api_key_service.list_api_keys(customer_id)
        
        return [APIKeyResponse(**key) for key in keys]
        
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to list API keys")


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    customer_id: str = Depends(get_current_customer_id)
):
    """Revoke an API key"""
    try:
        api_key_service = get_api_key_service()
        success = await api_key_service.revoke_api_key(key_id, customer_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return {"message": "API key revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke API key")
