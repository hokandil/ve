"""
Tool Registry Service
Manages tool access based on customer permissions
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry of available tools with permission management"""
    
    def __init__(self):
        self.tools = {
            "analytics": {
                "name": "Analytics Tool",
                "description": "Access analytics and metrics",
                "required_permission": "read_analytics"
            },
            "content_writer": {
                "name": "Content Writer",
                "description": "Generate marketing content",
                "required_permission": "write_content"
            },
            "seo_tools": {
                "name": "SEO Tools",
                "description": "SEO analysis and optimization",
                "required_permission": "read_analytics"
            },
            "email_sender": {
                "name": "Email Sender",
                "description": "Send emails",
                "required_permission": "send_email"
            }
        }
    
    def get_available_tools(self, permissions: List[str]) -> Dict[str, Any]:
        """
        Get tools available based on permissions
        
        Args:
            permissions: List of permission strings
        
        Returns:
            Dict of available tools
        """
        available = {}
        
        for tool_id, tool_info in self.tools.items():
            required_perm = tool_info["required_permission"]
            
            if required_perm in permissions:
                available[tool_id] = tool_info
        
        return available


# Singleton instance
_tool_registry = None


def get_tool_registry() -> ToolRegistry:
    """Get or create tool registry singleton"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


def get_tools_for_customer(
    customer_id: str,
    permissions: List[str]
) -> Dict[str, Any]:
    """
    Get tools available for a customer based on their permissions
    
    Args:
        customer_id: Customer UUID
        permissions: List of permission strings
    
    Returns:
        Dict of available tools
    """
    registry = get_tool_registry()
    tools = registry.get_available_tools(permissions)
    
    logger.info(
        f"Customer {customer_id} has access to {len(tools)} tools: "
        f"{list(tools.keys())}"
    )
    
    return tools
