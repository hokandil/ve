"""Virtual Employees API routes"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas import CustomerVEResponse, HireVERequest
from app.core.database import get_supabase_admin
from app.core.security import get_current_customer_id
import uuid

router = APIRouter()

@router.get("", response_model=List[CustomerVEResponse])
async def list_customer_ves(customer_id: str = Depends(get_current_customer_id)):
    """List all VEs hired by customer"""
    supabase = get_supabase_admin()
    response = supabase.table("customer_ves").select("*, ve_details:virtual_employees(*)").eq("customer_id", customer_id).execute()
    return [CustomerVEResponse(**item) for item in response.data]

@router.post("/hire", response_model=CustomerVEResponse)
async def hire_ve(request: HireVERequest, customer_id: str = Depends(get_current_customer_id)):
    """Hire a VE for the customer - uses Service Role to bypass RLS"""
    supabase = get_supabase_admin()
    
    # Get VE details
    ve_response = supabase.table("virtual_employees").select("*").eq("id", request.ve_id).execute()
    if not ve_response.data:
        raise HTTPException(status_code=404, detail="VE not found")
    
    ve = ve_response.data[0]
    
    # Generate persona details if not provided
    persona_name = request.persona_name or ve["name"]
    persona_email = request.persona_email or f"{ve['name'].lower().replace(' ', '.')}@company.veworkforce.io"
    agent_name = f"{ve['role'].lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}"
    namespace = f"customer-{customer_id}"
    
    # Create customer_ve record
    customer_ve_data = {
        "customer_id": customer_id,
        "ve_id": request.ve_id,
        "persona_name": persona_name,
        "persona_email": persona_email,
        "status": "deploying",  # Start as deploying
        "namespace": namespace,
        "agent_name": agent_name,
        "position_x": request.position_x,
        "position_y": request.position_y
    }
    
    insert_response = supabase.table("customer_ves").insert(customer_ve_data).execute()
    
    if not insert_response.data:
        raise HTTPException(status_code=500, detail="Failed to hire VE")
    
    customer_ve_id = insert_response.data[0]["id"]
    
    # Deploy to Kubernetes
    try:
        from app.services.ve_deployment import deploy_ve_to_kubernetes
        
        await deploy_ve_to_kubernetes(
            customer_id=customer_id,
            customer_ve_id=customer_ve_id,
            ve_template=ve,
            namespace=namespace,
            agent_name=agent_name
        )
        
        # Update status to active
        supabase.table("customer_ves").update({"status": "active"}).eq("id", customer_ve_id).execute()
        
    except Exception as e:
        # Log error but don't fail the request, background worker can retry or user can see status
        print(f"Failed to deploy VE: {e}")
        supabase.table("customer_ves").update({"status": "error"}).eq("id", customer_ve_id).execute()
    
    # Get the full record with VE details
    response = supabase.table("customer_ves").select("*, ve_details:virtual_employees(*)").eq("id", customer_ve_id).execute()
    
    return CustomerVEResponse(**response.data[0])

@router.get("/{customer_ve_id}", response_model=CustomerVEResponse)
async def get_customer_ve(customer_ve_id: str, customer_id: str = Depends(get_current_customer_id)):
    """Get specific customer VE"""
    supabase = get_supabase_admin()
    response = supabase.table("customer_ves").select("*, ve_details:virtual_employees(*)").eq("id", customer_ve_id).eq("customer_id", customer_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="VE not found")
    return CustomerVEResponse(**response.data[0])

@router.delete("/{customer_ve_id}")
async def delete_customer_ve(customer_ve_id: str, customer_id: str = Depends(get_current_customer_id)):
    """Remove a VE from customer's team"""
    supabase = get_supabase_admin()
    
    # Get VE details first to know agent name
    ve_response = supabase.table("customer_ves").select("*").eq("id", customer_ve_id).eq("customer_id", customer_id).execute()
    
    if ve_response.data:
        ve = ve_response.data[0]
        
        # Delete from Kubernetes
        try:
            from app.services.kubernetes_service import get_kubernetes_service
            k8s = get_kubernetes_service()
            await k8s.delete_agent(ve["namespace"], ve["agent_name"])
        except Exception as e:
            print(f"Failed to delete agent from K8s: {e}")
    
    # Delete from database
    supabase.table("customer_ves").delete().eq("id", customer_ve_id).eq("customer_id", customer_id).execute()
    return {"message": "VE removed successfully"}
