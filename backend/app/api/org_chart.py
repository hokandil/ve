"""Org Chart API routes"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas import OrgChartResponse, CreateConnectionRequest, UpdatePositionsRequest, VEConnectionResponse
from app.core.database import get_supabase_admin
from app.core.security import get_current_customer_id

router = APIRouter()

@router.get("", response_model=OrgChartResponse)
async def get_org_chart(customer_id: str = Depends(get_current_customer_id)):
    """Get customer's org chart (VEs and connections)"""
    supabase = get_supabase_admin()
    
    # Get VEs
    ves_response = supabase.table("customer_ves").select("*, ve_details:virtual_employees(*)").eq("customer_id", customer_id).execute()
    
    # Get connections
    connections_response = supabase.table("ve_connections").select("*").eq("customer_id", customer_id).execute()
    
    return OrgChartResponse(
        ves=ves_response.data,
        connections=connections_response.data
    )

@router.put("/positions")
async def update_positions(request: UpdatePositionsRequest, customer_id: str = Depends(get_current_customer_id)):
    """Update VE positions on org chart"""
    supabase = get_supabase_admin()
    
    for position in request.positions:
        supabase.table("customer_ves").update({
            "position_x": position["position_x"],
            "position_y": position["position_y"]
        }).eq("id", position["ve_id"]).eq("customer_id", customer_id).execute()
    
    return {"message": "Positions updated successfully"}

@router.post("/connections", response_model=VEConnectionResponse, status_code=201)
async def create_connection(request: CreateConnectionRequest, customer_id: str = Depends(get_current_customer_id)):
    """Create connection between two VEs"""
    supabase = get_supabase_admin()
    
    connection_data = {
        "customer_id": customer_id,
        "from_ve_id": request.from_ve_id,
        "to_ve_id": request.to_ve_id,
        "connection_type": request.connection_type
    }
    
    response = supabase.table("ve_connections").insert(connection_data).execute()
    return VEConnectionResponse(**response.data[0])

@router.delete("/connections/{connection_id}")
async def delete_connection(connection_id: str, customer_id: str = Depends(get_current_customer_id)):
    """Delete a connection"""
    supabase = get_supabase_admin()
    supabase.table("ve_connections").delete().eq("id", connection_id).eq("customer_id", customer_id).execute()
    return {"message": "Connection deleted successfully"}
