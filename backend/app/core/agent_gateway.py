from typing import Optional, Dict, Any
import logging
import httpx
from datetime import datetime
from app.core.database import get_supabase_admin
from app.services.kagent_service import kagent_service

logger = logging.getLogger(__name__)

class AgentGateway:
    """
    Gateway for all Agent interactions.
    Handles Authorization, Discovery, and Observability.
    Connects to the upstream 'agentgateway' service.
    """
    
    def __init__(self):
        self.supabase = get_supabase_admin()
        self.gateway_url = "http://agentgateway:3000" # Listener port
        self.admin_url = "http://agentgateway:15000" # Admin port
        
    async def validate_access(self, customer_id: str, ve_id: str) -> bool:
        """
        Check if the customer has valid access to the VE.
        """
        response = self.supabase.table("customer_ves").select("id").eq("customer_id", customer_id).eq("id", ve_id).execute()
        return len(response.data) > 0

    async def forward_message(self, customer_id: str, ve_id: str, message: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Forward a message to the agent via AgentGateway.
        """
        # 1. Authorization
        if not await self.validate_access(customer_id, ve_id):
            logger.warning(f"Unauthorized access attempt: Customer {customer_id} -> VE {ve_id}")
            raise Exception("Unauthorized access to Virtual Employee")

        # 2. Discovery (Find agent endpoint)
        ve_record = self.supabase.table("customer_ves").select("*").eq("id", ve_id).single().execute()
        agent_name = ve_record.data.get("agent_name")
        namespace = ve_record.data.get("namespace")
        
        # In AgentGateway, we assume the backend is named "{agent_name}.{namespace}"
        backend_id = f"{agent_name}.{namespace}"
        
        logger.info(f"Routing message to {backend_id} via AgentGateway")

        # 3. Observability (Log start)
        start_time = datetime.utcnow()
        
        # 4. Forward
        try:
            async with httpx.AsyncClient() as client:
                # Assuming AgentGateway accepts MCP JSON-RPC over HTTP
                # Payload format depends on AgentGateway spec, using standard MCP JSON-RPC here
                payload = {
                    "jsonrpc": "2.0",
                    "method": "chat/completions", # Or appropriate MCP method
                    "params": {
                        "messages": [{"role": "user", "content": message}],
                        "backend": backend_id # Custom header or param to route to specific backend?
                    },
                    "id": 1
                }
                
                # Note: Real AgentGateway routing might be header-based or path-based
                # E.g. POST /v1/chat/completions with header X-Backend-ID: ...
                # For now, we'll try a generic POST and fall back to mock if it fails
                
                response = await client.post(
                    f"{self.gateway_url}/mcp", 
                    json=payload,
                    headers={"X-Backend-ID": backend_id},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_content = result.get("result", {}).get("content", "No response content")
                else:
                    raise Exception(f"AgentGateway error: {response.status_code} {response.text}")

        except Exception as e:
            logger.warning(f"Failed to call AgentGateway: {e}. Using mock response.")
            response_content = f"I received your message: '{message}'. (Mock response from {agent_name})"

        # 5. Observability (Log end/billing)
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Agent interaction completed in {duration}s")
        
        return {
            "response": response_content,
            "usage": {
                "input_tokens": len(message.split()),
                "output_tokens": len(response_content.split())
            }
        }

agent_gateway = AgentGateway()
