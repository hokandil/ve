"""
Customer Agent Service
Provides dynamic discovery of customer's hired agents for delegation
"""
import logging
from typing import List, Dict, Any, Optional
from .base import BaseService
from .kagent_service import KAgentService

logger = logging.getLogger(__name__)

class CustomerAgentService(BaseService):
    """Service for discovering customer's hired agents and their capabilities"""
    
    def __init__(self, supabase):
        super().__init__(supabase)
        self.kagent_service = KAgentService()
    
    async def get_customer_agents(self, customer_id: str, current_agent_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all agents hired by a specific customer with their tools/capabilities,
        filtered by delegation rules relative to the current agent.
        
        Args:
            customer_id: Customer UUID
            current_agent_type: The agent type of the requester (for filtering)
            
        Returns:
            List of agent info dicts with tools
        """
        try:
            # 1. Get customer's hired agents
            response = self.supabase.table("customer_ves")\
                .select("id, persona_name, agent_type, ve_details:virtual_employees(role, department, seniority_level)")\
                .eq("customer_id", customer_id)\
                .execute()
            
            if not response.data:
                logger.info(f"No hired agents found for customer {customer_id}")
                return []
            
            all_agents = response.data
            
            # 2. Determine current agent's role/dept if provided
            current_agent = None
            if current_agent_type:
                for agent in all_agents:
                    if agent.get("agent_type") == current_agent_type:
                        current_agent = agent
                        break
            
            # 3. Filter agents based on rules
            allowed_agents = []
            
            for ve in all_agents:
                # Don't delegate to self
                if ve.get("agent_type") == current_agent_type:
                    continue
                    
                target_role = ve.get("ve_details", {}).get("role", "").lower()
                target_dept = ve.get("ve_details", {}).get("department", "").lower()
                target_seniority = ve.get("ve_details", {}).get("seniority_level", "").lower()
                
                # If we know who is asking, apply rules
                if current_agent:
                    my_role = current_agent.get("ve_details", {}).get("role", "").lower()
                    my_dept = current_agent.get("ve_details", {}).get("department", "").lower()
                    my_seniority = current_agent.get("ve_details", {}).get("seniority_level", "").lower()
                    
                    # Rule 1: Same Department
                    if my_dept == target_dept:
                        # Manager can delegate to anyone in dept
                        if "manager" in my_role or "manager" in my_seniority:
                            pass # Allowed
                        # Senior can delegate to Junior
                        elif "senior" in my_seniority and "junior" in target_seniority:
                            pass # Allowed
                        # Junior cannot delegate (or only to peers? User said "shouldn't delegate to upper level")
                        # Assuming Junior -> Junior is okay, but Junior -> Senior/Manager is NOT.
                        elif "junior" in my_seniority and ("senior" in target_seniority or "manager" in target_seniority):
                            continue # Blocked
                        else:
                            # Default: Allow peer delegation if not explicitly blocked
                            pass
                            
                    # Rule 2: Cross Department
                    else:
                        # Can only delegate to a Manager of another department
                        if "manager" in target_role or "manager" in target_seniority:
                            pass # Allowed
                        else:
                            continue # Blocked: Cannot delegate to non-manager in other dept
                
                # Add to allowed list
                agent_type = ve.get("agent_type")
                if not agent_type:
                    continue

                # Get agent details from KAgent (includes tools)
                agent_details = await self.kagent_service.get_agent(agent_type, namespace="kagent")
                
                tools = []
                if agent_details:
                    tools = agent_details.get("tools", [])
                
                allowed_agents.append({
                    "id": ve["id"],  # customer_ve_id
                    "name": ve["persona_name"],
                    "agent_type": agent_type,
                    "role": ve.get("ve_details", {}).get("role", "Unknown"),
                    "department": ve.get("ve_details", {}).get("department", "Unknown"),
                    "tools": tools
                })
            
            logger.info(f"Found {len(allowed_agents)} allowed delegation targets for {current_agent_type}")
            return allowed_agents
            
        except Exception as e:
            logger.error(f"Error fetching customer agents: {e}", exc_info=True)
            return []
    
    def format_agent_context(self, agents: List[Dict[str, Any]]) -> str:
        """
        Format agent list as context string for injection into agent prompts
        
        Args:
            agents: List of agent dicts from get_customer_agents
            
        Returns:
            Formatted string for agent context
        """
        if not agents:
            return "Your Team: No other agents available."
        
        context_lines = ["Your Team (Hired Agents):"]
        for agent in agents:
            tools_str = ", ".join(agent["tools"]) if agent["tools"] else "no tools"
            context_lines.append(
                f"- {agent['name']} (ID: {agent['id']}, Role: {agent['role']}, Tools: {tools_str})"
            )
        
        context_lines.append("")
        context_lines.append("If you need a tool you don't have, use delegate_to_agent(agent_id, task_description).")
        context_lines.append("Example: If asked about Kubernetes but you lack kubectl, delegate to the DevOps agent.")
        
        return "\n".join(context_lines)
