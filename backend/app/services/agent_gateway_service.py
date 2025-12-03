"""
Agent Gateway Service
Handles interactions with KAgent deployments via Agent Gateway
"""
import logging
import httpx
import json
from typing import Dict, Any, Optional, AsyncGenerator
from app.core.config import settings

logger = logging.getLogger(__name__)

class AgentGatewayService:
    """Service for routing messages to KAgent deployments via Agent Gateway"""
    
    def __init__(self):
        self.base_url = settings.AGENT_GATEWAY_URL
        self.auth_token = settings.AGENT_GATEWAY_AUTH_TOKEN
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.auth_token}"},
            timeout=10.0
        )
        logger.info("AgentGatewayService initialized for Agent Gateway routing")
    
    async def create_customer_route(
        self,
        customer_id: str,
        agent_type: str,
        customer_ve_id: str
    ) -> Dict[str, Any]:
        """
        Grant customer access to agent via Agent Gateway (called when customer hires agent)
        
        Args:
            customer_id: Customer UUID
            agent_type: Agent type (e.g., "wellness")
            customer_ve_id: Customer VE UUID
        
        Returns:
            Route info dict
        """
        from app.services.gateway_config_service import get_gateway_config_service
        
        gateway_config = get_gateway_config_service()
        
        # Grant customer access via TrafficPolicy
        policy_info = gateway_config.grant_customer_access(agent_type, customer_id)
        
        logger.info(
            f"Granted customer {customer_id} access to agent {agent_type} via Agent Gateway"
        )
        
        return {
            "route_path": f"/agents/{agent_type}",
            "agent_type": agent_type,
            "customer_id": customer_id,
            "customer_ve_id": customer_ve_id,
            "policy_info": policy_info,
            "status": "active"
        }
    
    async def get_customer_agents_context(self, customer_id: str, current_agent_type: Optional[str] = None) -> str:
        """
        Get formatted agent context for a customer to inject into prompts
        
        Args:
            customer_id: Customer UUID
            current_agent_type: Current agent type (for filtering)
            
        Returns:
            Formatted string with available agents and tools
        """
        from app.services.customer_agent_service import CustomerAgentService
        from app.core.database import get_supabase_admin
        
        supabase = get_supabase_admin()
        customer_agent_service = CustomerAgentService(supabase)
        
        agents = await customer_agent_service.get_customer_agents(customer_id, current_agent_type)
        return customer_agent_service.format_agent_context(agents)
    
    async def invoke_agent_stream(
        self,
        customer_id: str,
        agent_type: str,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        permissions: Optional[list] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Invoke agent and stream events as they arrive (SSE)
        
        Yields:
            Dict events: {"type": "thought"|"action"|"result"|"message", "content": str}
        """
        logger.info(f"Streaming agent {agent_type} for customer {customer_id}")
        
        # Get agent context (filtered by current agent's role)
        agent_context = await self.get_customer_agents_context(customer_id, agent_type)
        
        # Use Agent Gateway with A2A protocol
        if settings.ENVIRONMENT == "development":
            gateway_url = "http://localhost:8080"
        else:
            gateway_url = "http://agent-gateway.kgateway-system.svc.cluster.local:8080"

        context_id = session_id or f"ctx-{customer_id}"
        message_id = f"msg-{customer_id}-{hash(message)}"

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Host": f"{agent_type}.local",
            "X-Customer-ID": customer_id
        }

        # Inject agent context into message
        enhanced_message = f"{agent_context}\n\nUser Request: {message}"

        payload = {
            "jsonrpc": "2.0",
            "method": "message/stream",
            "params": {
                "message": {
                    "kind": "message",
                    "messageId": message_id,
                    "role": "user",
                    "parts": [{"kind": "text", "text": enhanced_message}],
                    "contextId": context_id,
                    "metadata": {"displaySource": "user"}
                },
                "metadata": {}
            },
            "id": f"req-{customer_id}"
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{gateway_url}/",
                    json=payload,
                    headers=headers
                ) as response:
                    
                    if response.status_code != 200:
                        error_body = await response.aread()
                        logger.error(f"Agent Gateway error {response.status_code}: {error_body.decode('utf-8', errors='ignore')[:500]}")
                        yield {"type": "error", "content": f"Gateway error: {response.status_code}"}
                        return
                    
                    # Parse SSE stream
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                
                                if "result" in data:
                                    result = data["result"]
                                    
                                    # Extract message from status update
                                    if "status" in result and "message" in result["status"]:
                                        msg = result["status"]["message"]
                                        if msg.get("role") == "agent" and "parts" in msg:
                                            for part in msg["parts"]:
                                                if part.get("kind") == "text":
                                                    yield {"type": "message", "content": part.get("text", "")}
                                    
                                    # Extract artifact update
                                    elif "artifact" in result and "parts" in result["artifact"]:
                                        for part in result["artifact"]["parts"]:
                                            if part.get("kind") == "text":
                                                yield {"type": "artifact", "content": part.get("text", "")}
                                    
                                    # Check if final
                                    if result.get("final") == True:
                                        break
                                        
                            except json.JSONDecodeError:
                                continue
                                
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Agent Gateway: {e}")
            yield {"type": "error", "content": "Agent Gateway unavailable"}
        except Exception as e:
            logger.error(f"Error streaming from agent: {e}")
            yield {"type": "error", "content": str(e)}
    
    async def invoke_agent(
        self,
        customer_id: str,
        agent_type: str,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        permissions: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Invoke a KAgent deployment via Agent Gateway using A2A protocol
        
        Args:
            customer_id: Customer UUID
            agent_type: Agent type (e.g., "wellness")
            message: User message
            session_id: Optional session ID
            user_id: Optional user ID
            permissions: Optional permissions list
        
        Returns:
            Agent response
        """
        logger.info(f"Invoking agent {agent_type} via Agent Gateway for customer {customer_id}")
        
        # Use Agent Gateway with A2A protocol
        if settings.ENVIRONMENT == "development":
            # Local development: use port-forward to Agent Gateway
            gateway_url = "http://localhost:8080"
            logger.info(f"Dev Mode: Connecting to Agent Gateway at {gateway_url}")
        else:
            # Production: use cluster DNS
            gateway_url = "http://agent-gateway.kgateway-system.svc.cluster.local:8080"

        # Agent Gateway routes based on Host header
        agent_path = "/"
        
        # Generate context ID for this conversation
        context_id = session_id or f"ctx-{customer_id}"
        message_id = f"msg-{customer_id}-{hash(message)}"

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",  # A2A uses SSE
            "Host": f"{agent_type}.local",  # For Gateway routing to correct agent
            "X-Customer-ID": customer_id  # For RBAC via TrafficPolicy
        }

        # A2A message/stream request format
        payload = {
            "jsonrpc": "2.0",
            "method": "message/stream",
            "params": {
                "message": {
                    "kind": "message",
                    "messageId": message_id,
                    "role": "user",
                    "parts": [
                        {
                            "kind": "text",
                            "text": message
                        }
                    ],
                    "contextId": context_id,
                    "metadata": {
                        "displaySource": "user"
                    }
                },
                "metadata": {}
            },
            "id": f"req-{customer_id}"
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # A2A uses Server-Sent Events (streaming)
                async with client.stream(
                    "POST",
                    f"{gateway_url}{agent_path}",
                    json=payload,
                    headers=headers
                ) as response:
                    
                    if response.status_code != 200:
                        error_body = await response.aread()
                        logger.error(
                            f"Agent Gateway returned {response.status_code} for agent '{agent_type}'\n"
                            f"URL: {gateway_url}{agent_path}\n"
                            f"Host Header: {agent_type}.local\n"
                            f"Customer ID: {customer_id}\n"
                            f"Response Body: {error_body.decode('utf-8', errors='ignore')[:500]}"
                        )
                        agent_message = f"I apologize, but I'm currently experiencing technical difficulties. (Gateway error: {response.status_code})"
                    else:
                        # Parse SSE stream
                        agent_message = ""
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                try:
                                    data = json.loads(line[6:])  # Remove "data: " prefix
                                    
                                    # Extract message from task_status_update or task_artifact_update
                                    if "result" in data:
                                        result = data["result"]
                                        
                                        # Check for agent message in status update
                                        if "status" in result and "message" in result["status"]:
                                            msg = result["status"]["message"]
                                            if msg.get("role") == "agent" and "parts" in msg:
                                                for part in msg["parts"]:
                                                    if part.get("kind") == "text":
                                                        agent_message = part.get("text", "")
                                        
                                        # Check for artifact update
                                        elif "artifact" in result and "parts" in result["artifact"]:
                                            for part in result["artifact"]["parts"]:
                                                if part.get("kind") == "text":
                                                    agent_message = part.get("text", "")
                                        
                                        # Check if task is completed
                                        if result.get("final") == True:
                                            break
                                            
                                except json.JSONDecodeError:
                                    continue
                        
                        if not agent_message:
                            agent_message = "No response from agent"
                            
                        logger.info(f"Agent response: {agent_message[:100]}...")
                    
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Agent Gateway at {gateway_url}: {e}")
            agent_message = f"I apologize, but I'm currently unavailable. Please ensure the Agent Gateway is reachable. (Connection error)"
                
        except Exception as e:
            logger.error(f"Error calling Agent Gateway for {agent_type}: {e}")
            agent_message = f"I apologize, but I encountered an error: {str(e)[:100]}"
        
        # Prepare response
        response_data = {
            "message": agent_message,
            "agent_type": agent_type,
            "customer_id": customer_id
        }
        
        # SECURITY: Scan response for leakage
        from app.security.leakage_detector import leakage_detector
        
        alerts = leakage_detector.scan(
            content=agent_message,
            customer_id=customer_id,
            metadata={"agent_type": agent_type, "session_id": session_id}
        )
        
        if any(alert.severity in ["high", "critical"] for alert in alerts):
            logger.critical(
                f"BLOCKED LEAKAGE: Agent {agent_type} attempted to leak data to {customer_id}"
            )
            # Redact or block response
            response_data["message"] = "[SECURITY REDACTED] - Potential data leakage detected."
            response_data["blocked"] = True
            
        return response_data
    
    async def revoke_customer_access(self, agent_type: str, customer_id: str) -> bool:
        """Revoke customer access to agent (called when customer unhires agent)"""
        from app.services.gateway_config_service import get_gateway_config_service
        
        gateway_config = get_gateway_config_service()
        policy_info = gateway_config.revoke_customer_access(agent_type, customer_id)
        
        logger.info(f"Revoked customer {customer_id} access to agent {agent_type}")
        return policy_info.get("status") in ["revoked", "not_found"]
    
    async def delete_route(self, agent_type: str) -> bool:
        """Delete agent route (called when admin deletes agent from platform)"""
        from app.services.gateway_config_service import get_gateway_config_service
        
        gateway_config = get_gateway_config_service()
        return gateway_config.delete_agent_route(agent_type)

agent_gateway_service = AgentGatewayService()
