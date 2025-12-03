from typing import List, Dict, Any, Optional
import logging
from kubernetes import client, config
from app.core.config import settings
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class KAgentService:
    """
    Service to interact with the KAgent source of truth (Kubernetes CRDs).
    Supports v1alpha2 API version.
    """
    
    def __init__(self):
        self.k8s_api = None
        self.cache = {}
        self.cache_ttl = timedelta(minutes=5)
        
        try:
            # Try to load in-cluster config first, then local kubeconfig
            try:
                config.load_incluster_config()
            except:
                config.load_kube_config()
            
            self.k8s_api = client.CustomObjectsApi()
            logger.info("Successfully connected to Kubernetes API")
        except Exception as e:
            logger.warning(f"Failed to connect to Kubernetes API: {e}. Using mock data.")
            self.k8s_api = None
        
    def _get_cache(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.cache_ttl:
                return value
        return None
    
    def _set_cache(self, key: str, value: Any):
        """Set cache value with timestamp"""
        self.cache[key] = (value, datetime.now())
    
    async def list_agents(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all available agents from KAgent (Kubernetes CRDs).
        Uses v1alpha2 API version.
        """
        cache_key = f"agents_{namespace or 'all'}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        if not self.k8s_api:
            return self._get_mock_agents()

        try:
            # List 'agents.kagent.dev' resources (v1alpha2)
            if namespace:
                response = self.k8s_api.list_namespaced_custom_object(
                    group="kagent.dev",
                    version="v1alpha2",
                    namespace=namespace,
                    plural="agents"
                )
            else:
                response = self.k8s_api.list_cluster_custom_object(
                    group="kagent.dev",
                    version="v1alpha2",
                    plural="agents"
                )
            
            agents = []
            for item in response.get("items", []):
                spec = item.get("spec", {})
                metadata = item.get("metadata", {})
                
                # Parse tools from spec
                tools = []
                for tool in spec.get("tools", []):
                    if tool.get("type") == "McpServer":
                        mcp_server = tool.get("mcpServer", {})
                        tool_names = tool.get("toolNames", [])
                        tools.extend(tool_names)
                
                agents.append({
                    "id": metadata.get("name"),
                    "name": metadata.get("name"),
                    "namespace": metadata.get("namespace", "default"),
                    "description": spec.get("description", ""),
                    "version": str(metadata.get("generation", 1)),
                    "type": spec.get("type", "Declarative"),
                    "tools": tools,
                    "labels": metadata.get("labels", {}),
                    "annotations": metadata.get("annotations", {}),
                    "created_at": metadata.get("creationTimestamp"),
                })
            
            self._set_cache(cache_key, agents)
            return agents
            
        except Exception as e:
            logger.error(f"Error listing KAgent agents from K8s: {e}")
            return self._get_mock_agents() 

    async def get_agent(self, agent_id: str, namespace: str = "kagent") -> Optional[Dict[str, Any]]:
        """
        Get details of a specific agent.
        """
        if not self.k8s_api:
            agents = await self.list_agents()
            for agent in agents:
                if agent["id"] == agent_id:
                    return agent
            return None
        
        try:
            response = self.k8s_api.get_namespaced_custom_object(
                group="kagent.dev",
                version="v1alpha2",
                namespace=namespace,
                plural="agents",
                name=agent_id
            )
            
            spec = response.get("spec", {})
            metadata = response.get("metadata", {})
            
            # Parse tools
            tools = []
            for tool in spec.get("tools", []):
                if tool.get("type") == "McpServer":
                    tool_names = tool.get("toolNames", [])
                    tools.extend(tool_names)
            
            return {
                "id": metadata.get("name"),
                "name": metadata.get("name"),
                "namespace": metadata.get("namespace", "default"),
                "description": spec.get("description", ""),
                "version": str(metadata.get("generation", 1)),
                "type": spec.get("type", "Declarative"),
                "tools": tools,
                "labels": metadata.get("labels", {}),
                "annotations": metadata.get("annotations", {}),
                "created_at": metadata.get("creationTimestamp"),
                "spec": spec  # Include full spec for detailed view
            }
            
        except Exception as e:
            logger.error(f"Error getting agent {agent_id}: {e}")
            return None

    async def list_mcps(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all available MCP servers from KAgent.
        """
        cache_key = f"mcps_{namespace or 'all'}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        if not self.k8s_api:
            return self._get_mock_mcps()
        
        try:
            # List 'mcpservers.kagent.dev' resources
            if namespace:
                response = self.k8s_api.list_namespaced_custom_object(
                    group="kagent.dev",
                    version="v1alpha2",
                    namespace=namespace,
                    plural="mcpservers"
                )
            else:
                response = self.k8s_api.list_cluster_custom_object(
                    group="kagent.dev",
                    version="v1alpha2",
                    plural="mcpservers"
                )
            
            mcps = []
            for item in response.get("items", []):
                spec = item.get("spec", {})
                metadata = item.get("metadata", {})
                
                mcps.append({
                    "id": metadata.get("name"),
                    "name": metadata.get("name"),
                    "namespace": metadata.get("namespace", "default"),
                    "description": spec.get("description", ""),
                    "url": spec.get("url", ""),
                    "tools": spec.get("tools", []),
                    "created_at": metadata.get("creationTimestamp"),
                })
            
            self._set_cache(cache_key, mcps)
            return mcps
            
        except Exception as e:
            logger.error(f"Error listing MCP servers from K8s: {e}")
            return self._get_mock_mcps()

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools from all MCP servers.
        """
        cache_key = "tools_all"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        mcps = await self.list_mcps()
        
        tools = []
        for mcp in mcps:
            for tool in mcp.get("tools", []):
                tools.append({
                    "name": tool if isinstance(tool, str) else tool.get("name"),
                    "description": tool.get("description", "") if isinstance(tool, dict) else "",
                    "mcp_server": mcp["name"],
                    "type": "mcp"
                })
        
        self._set_cache(cache_key, tools)
        return tools

    def _get_mock_agents(self) -> List[Dict[str, Any]]:
        """Return mock agents for dev/testing"""
        return [
            {
                "id": "hr-assistant",
                "name": "hr-assistant",
                "namespace": "default",
                "description": "Helps with HR tasks including onboarding and FAQ",
                "version": "1",
                "type": "Declarative",
                "tools": ["email-sender", "calendar-manager"],
                "labels": {"department": "hr", "seniority": "mid"},
                "annotations": {},
                "created_at": "2025-11-26T00:00:00Z"
            },
            {
                "id": "devops-engineer",
                "name": "devops-engineer",
                "namespace": "default",
                "description": "Manages deployment pipelines and infrastructure",
                "version": "1",
                "type": "Declarative",
                "tools": ["kubectl", "aws-cli"],
                "labels": {"department": "engineering", "seniority": "senior"},
                "annotations": {},
                "created_at": "2025-11-26T00:00:00Z"
            },
            {
                "id": "sales-rep",
                "name": "sales-rep",
                "namespace": "default",
                "description": "Outbound sales and lead qualification specialist",
                "version": "1",
                "type": "Declarative",
                "tools": ["hubspot", "gmail"],
                "labels": {"department": "sales", "seniority": "mid"},
                "annotations": {},
                "created_at": "2025-11-26T00:00:00Z"
            }
        ]
    
    def _get_mock_mcps(self) -> List[Dict[str, Any]]:
        """Return mock MCP servers for dev/testing"""
        return [
            {
                "id": "email-mcp",
                "name": "email-mcp",
                "namespace": "default",
                "description": "Email sending and management",
                "url": "http://email-mcp:8080",
                "tools": ["send_email", "read_inbox", "search_emails"],
                "created_at": "2025-11-26T00:00:00Z"
            },
            {
                "id": "calendar-mcp",
                "name": "calendar-mcp",
                "namespace": "default",
                "description": "Calendar management",
                "url": "http://calendar-mcp:8080",
                "tools": ["create_event", "list_events", "delete_event"],
                "created_at": "2025-11-26T00:00:00Z"
            },
            {
                "id": "kubectl-mcp",
                "name": "kubectl-mcp",
                "namespace": "default",
                "description": "Kubernetes CLI wrapper",
                "url": "http://kubectl-mcp:8080",
                "tools": ["kubectl_get", "kubectl_apply", "kubectl_delete"],
                "created_at": "2025-11-26T00:00:00Z"
            }
        ]

kagent_service = KAgentService()
