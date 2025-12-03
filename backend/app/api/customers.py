"""Customer API routes"""
from fastapi import APIRouter, Depends, HTTPException
from app.schemas import CustomerResponse
from app.core.database import get_supabase_admin
from app.core.security import get_current_customer_id

router = APIRouter()

@router.get("/me", response_model=CustomerResponse)
async def get_current_customer(customer_id: str = Depends(get_current_customer_id)):
    """Get current customer information"""
    supabase = get_supabase_admin()
    response = supabase.table("customers").select("*").eq("id", customer_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerResponse(**response.data[0])
