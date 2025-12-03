from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from app.core.database import get_supabase_admin
from app.core.config import settings
import hmac
import hashlib

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

class TokenUsageRecord(BaseModel):
    customer_id: str
    agent_id: str
    route_id: str
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    model: str
    operation: str
    timestamp: datetime

class UsageWebhookPayload(BaseModel):
    records: List[TokenUsageRecord]

async def verify_webhook_signature(request: Request):
    """
    Verify the webhook signature from Agent Gateway.
    """
    # In a real scenario, we would verify the signature using a shared secret
    # For now, we'll skip strict verification or use a simple header check
    # signature = request.headers.get("X-Hub-Signature-256")
    # if not signature:
    #     raise HTTPException(status_code=401, detail="Missing signature")
    pass

@router.post("/agent-gateway/usage")
async def handle_usage_webhook(
    payload: UsageWebhookPayload,
    request: Request
    # _ = Depends(verify_webhook_signature)
):
    """
    Receive token usage data from Agent Gateway.
    """
    supabase = get_supabase_admin()
    
    records_to_insert = []
    for record in payload.records:
        # Calculate cost based on model (simplified)
        cost = 0.0
        if "gpt-4" in record.model:
            cost = (record.prompt_tokens * 0.03 + record.completion_tokens * 0.06) / 1000
        else:
            # Default to GPT-3.5 pricing
            cost = (record.total_tokens * 0.002) / 1000
            
        records_to_insert.append({
            "customer_id": record.customer_id,
            "ve_id": record.agent_id, # Mapping agent_id to ve_id
            "route_id": record.route_id,
            "total_tokens": record.total_tokens,
            "prompt_tokens": record.prompt_tokens,
            "completion_tokens": record.completion_tokens,
            "model": record.model,
            "operation": record.operation,
            "cost": cost,
            "timestamp": record.timestamp.isoformat()
        })
    
    if records_to_insert:
        result = supabase.table("token_usage").insert(records_to_insert).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to store usage data")
            
    return {"status": "success", "processed": len(records_to_insert)}
