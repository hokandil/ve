"""Billing API routes"""
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta
from app.schemas import BillingUsageResponse, SubscriptionResponse, TokenUsageResponse
from app.core.database import get_supabase_admin
from app.core.security import get_current_customer_id
from typing import List

router = APIRouter()

@router.get("/usage", response_model=BillingUsageResponse)
async def get_billing_usage(
    days: int = Query(30, ge=1, le=365),
    customer_id: str = Depends(get_current_customer_id)
):
    """Get token usage and billing information"""
    supabase = get_supabase_admin()
    
    period_start = datetime.utcnow() - timedelta(days=days)
    period_end = datetime.utcnow()
    
    # Get token usage
    response = supabase.table("token_usage").select("*").eq("customer_id", customer_id).gte("timestamp", period_start.isoformat()).execute()
    
    total_tokens = sum(item["total_tokens"] for item in response.data)
    total_cost = sum(item["cost"] for item in response.data)
    
    # Group by VE
    usage_by_ve = {}
    for item in response.data:
        ve_id = item.get("ve_id", "orchestrator")
        if ve_id not in usage_by_ve:
            usage_by_ve[ve_id] = {"tokens": 0, "cost": 0}
        usage_by_ve[ve_id]["tokens"] += item["total_tokens"]
        usage_by_ve[ve_id]["cost"] += item["cost"]
    
    # Group by operation
    usage_by_operation = {}
    for item in response.data:
        operation = item["operation"]
        if operation not in usage_by_operation:
            usage_by_operation[operation] = {"tokens": 0, "cost": 0}
        usage_by_operation[operation]["tokens"] += item["total_tokens"]
        usage_by_operation[operation]["cost"] += item["cost"]
    
    return BillingUsageResponse(
        total_tokens=total_tokens,
        total_cost=total_cost,
        period_start=period_start,
        period_end=period_end,
        usage_by_ve=[{"ve_id": k, **v} for k, v in usage_by_ve.items()],
        usage_by_operation=[{"operation": k, **v} for k, v in usage_by_operation.items()]
    )

@router.get("/usage/breakdown", response_model=List[TokenUsageResponse])
async def get_usage_breakdown(
    days: int = Query(30, ge=1, le=365),
    customer_id: str = Depends(get_current_customer_id)
):
    """Get detailed token usage breakdown"""
    supabase = get_supabase_admin()
    
    period_start = datetime.utcnow() - timedelta(days=days)
    
    response = supabase.table("token_usage").select("*").eq("customer_id", customer_id).gte("timestamp", period_start.isoformat()).order("timestamp", desc=True).execute()
    
    return [TokenUsageResponse(**item) for item in response.data]

@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription_info(customer_id: str = Depends(get_current_customer_id)):
    """Get subscription information"""
    supabase = get_supabase_admin()
    
    # Get customer info
    customer_response = supabase.table("customers").select("*").eq("id", customer_id).execute()
    customer = customer_response.data[0]
    
    # Get hired VEs
    ves_response = supabase.table("customer_ves").select("*, ve_details:virtual_employees(pricing_monthly)").eq("customer_id", customer_id).execute()
    
    monthly_ve_cost = sum(ve["ve_details"]["pricing_monthly"] for ve in ves_response.data if ve.get("ve_details"))
    
    # Estimate token cost (last 30 days average)
    period_start = datetime.utcnow() - timedelta(days=30)
    token_response = supabase.table("token_usage").select("cost").eq("customer_id", customer_id).gte("timestamp", period_start.isoformat()).execute()
    
    estimated_token_cost = sum(item["cost"] for item in token_response.data)
    
    return SubscriptionResponse(
        customer_id=customer_id,
        subscription_tier=customer["subscription_tier"],
        subscription_status=customer["subscription_status"],
        monthly_ve_cost=monthly_ve_cost,
        estimated_token_cost=estimated_token_cost,
        total_estimated_cost=monthly_ve_cost + estimated_token_cost,
        hired_ves_count=len(ves_response.data)
    )
