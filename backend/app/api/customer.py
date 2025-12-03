"""
Customer API routes for managing hired VEs and interactions
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import uuid
from pydantic import BaseModel
from datetime import datetime
import logging

from app.schemas import (
    CustomerVEResponse,
    HireVERequest,
    VirtualEmployeeResponse
)
from app.core.database import get_supabase_admin
from app.core.security import get_current_customer_id
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/ves", response_model=List[CustomerVEResponse])
async def list_customer_ves(
    customer_id: str = Depends(get_current_customer_id)
):
    """List all VEs hired by the current customer"""
    supabase = get_supabase_admin()
    
    try:
        # Get customer VEs
        response = supabase.table("customer_ves").select("*").eq("customer_id", customer_id).execute()
        
        ves = []
        for item in response.data:
            # Fetch details from marketplace_agents (virtual_employees)
            ve_details = None
            if item.get("marketplace_agent_id"):
                ve_res = supabase.table("virtual_employees").select("*").eq("id", item["marketplace_agent_id"]).execute()
                if ve_res.data:
                    ve_details = VirtualEmployeeResponse(**ve_res.data[0])
            
            ves.append(CustomerVEResponse(
                **item,
                ve_details=ve_details
            ))
            
        return ves
        
    except Exception as e:
        logger.error(f"Error listing customer VEs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ves", response_model=CustomerVEResponse, status_code=201)
async def hire_ve(
    request: HireVERequest,
    customer_id: str = Depends(get_current_customer_id)
):
    """Hire a VE from the marketplace - creates route to shared agent"""
    supabase = get_supabase_admin()
    
    try:
        # Get Marketplace Agent template
        ve_response = supabase.table("virtual_employees").select("*").eq("id", request.marketplace_agent_id).execute()
        if not ve_response.data:
            raise HTTPException(status_code=404, detail="Marketplace Agent not found")
        
        ve_template = ve_response.data[0]
        
        # Generate persona details if not provided
        persona_name = request.persona_name or ve_template["name"]
        
        # Get customer info for email domain
        customer_response = supabase.table("customers").select("company_name").eq("id", customer_id).execute()
        company_name = customer_response.data[0]["company_name"] if customer_response.data else "company"
        company_slug = company_name.lower().replace(" ", "")
        
        persona_email = request.persona_email or f"{persona_name.lower().replace(' ', '.')}@{company_slug}.veworkforce.io"
        
        # Create customer VE record
        customer_ve_id = str(uuid.uuid4())
        
        
        # NEW APPROACH: Create route to SHARED agent (not per-customer deployment)
        from app.services.agent_gateway_service import agent_gateway_service
        
        # Use the agent's source_agent_id which is the KAgent deployment name
        # If not available, fall back to deriving from role
        agent_type = ve_template.get("source_agent_id") or ve_template["role"].lower().replace(" ", "-")
        
        logger.info(f"Creating route for customer {customer_id} to KAgent {agent_type}")
        
        # Create route to shared agent
        route_info = await agent_gateway_service.create_customer_route(
            customer_id=customer_id,
            agent_type=agent_type,
            customer_ve_id=customer_ve_id
        )
        
        # Store customer VE data
        customer_ve_data = {
            "id": customer_ve_id,
            "customer_id": customer_id,
            "marketplace_agent_id": request.marketplace_agent_id,
            "agent_type": agent_type,  # NEW: agent type instead of agent_name
            "agent_gateway_route": route_info["route_path"],  # e.g., /agents/customer-123/marketing-manager
            "persona_name": persona_name,
            "persona_email": persona_email,
            "status": "active",
            "hired_at": datetime.utcnow().isoformat()
        }
        
        insert_response = supabase.table("customer_ves").insert(customer_ve_data).execute()
        
        if not insert_response.data:
             raise HTTPException(status_code=500, detail="Failed to hire VE")
        
        # Fetch the inserted record to return
        new_ve = insert_response.data[0]
        
        # Return with details
        return CustomerVEResponse(
            **new_ve,
            ve_details=VirtualEmployeeResponse(**ve_template)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error hiring VE: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/ves/{ve_id}", status_code=204)
async def unhire_ve(
    ve_id: str,
    customer_id: str = Depends(get_current_customer_id)
):
    """Unhire a VE (revoke access and delete record)"""
    supabase = get_supabase_admin()
    
    try:
        # 1. Get VE details
        ve_record = supabase.table("customer_ves").select("*").eq("id", ve_id).eq("customer_id", customer_id).execute()
        if not ve_record.data:
            raise HTTPException(status_code=404, detail="VE not found")
            
        ve_data = ve_record.data[0]
            
        # 2. Revoke customer access in Agent Gateway
        try:
            from app.services.agent_gateway_service import agent_gateway_service
            
            # We need agent_type. 
            agent_type = ve_data.get("agent_type")
            
            if agent_type:
                await agent_gateway_service.revoke_customer_access(agent_type, customer_id)
        except Exception as e:
            # Log error but continue with unhiring (best effort)
            # This is crucial if the route/policy was already deleted manually
            logger.error(f"Error revoking access in gateway (ignoring): {e}")
        
        # 3. Delete record
        delete_response = supabase.table("customer_ves").delete().eq("id", ve_id).eq("customer_id", customer_id).execute()
        
        if not delete_response.data:
             # It might have been deleted already, or failed. 
             # But if we are here, we verified it existed at step 1.
             # Let's assume success if we get here to avoid blocking the user.
             pass
             
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unhiring VE: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class UpdateVERequest(BaseModel):
    persona_name: Optional[str] = None
    # Add other editable fields here if needed

@router.patch("/ves/{ve_id}", response_model=CustomerVEResponse)
async def update_ve(
    ve_id: str,
    request: UpdateVERequest,
    customer_id: str = Depends(get_current_customer_id)
):
    """Update a hired VE's details (e.g. custom name)"""
    supabase = get_supabase_admin()
    
    try:
        # 1. Verify ownership
        ve_record = supabase.table("customer_ves").select("*").eq("id", ve_id).eq("customer_id", customer_id).execute()
        if not ve_record.data:
            raise HTTPException(status_code=404, detail="VE not found")
            
        # 2. Update fields
        update_data = {}
        if request.persona_name:
            update_data["persona_name"] = request.persona_name
            
        if not update_data:
            return CustomerVEResponse(
                **ve_record.data[0],
                ve_details=None # Fetching details again is expensive/complex here, client usually has them or reloads
            )
            
        # 3. Execute update
        response = supabase.table("customer_ves").update(update_data).eq("id", ve_id).execute()
        
        if not response.data:
             raise HTTPException(status_code=500, detail="Failed to update VE")
             
        updated_ve = response.data[0]
        
        # 4. Fetch details to return complete object (consistent with list/get)
        ve_details = None
        if updated_ve.get("marketplace_agent_id"):
            ve_res = supabase.table("virtual_employees").select("*").eq("id", updated_ve["marketplace_agent_id"]).execute()
            if ve_res.data:
                ve_details = VirtualEmployeeResponse(**ve_res.data[0])
                
        return CustomerVEResponse(
            **updated_ve,
            ve_details=ve_details
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating VE: {e}")
        raise HTTPException(status_code=500, detail=str(e))
