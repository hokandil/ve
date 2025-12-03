"""
HTTPRoute Management Service
Manages Kubernetes HTTPRoute resources for routing to KAgent deployments via Agent Gateway
"""
import logging
from typing import Dict, Any, Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)

class HTTPRouteService:
    """Service for managing HTTPRoute resources for agent routing"""
    
    def __init__(self):
        try:
            # Try in-cluster config first
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes config")
        except:
            # Fall back to kubeconfig for local development
            try:
                config.load_kube_config()
                logger.info("Loaded kubeconfig for local development")
            except Exception as e:
                logger.warning(f"Could not load Kubernetes config: {e}")
                self.k8s_available = False
                return
        
        self.custom_api = client.CustomObjectsApi()
        self.k8s_available = True
        self.gateway_namespace = "kgateway-system"
        self.gateway_name = "agent-gateway"
        self.routes_namespace = "default"  # HTTPRoutes in default namespace
        
    def create_agent_route(
        self,
        agent_type: str,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create HTTPRoute for an agent type
        
        Args:
            agent_type: Agent type (e.g., "marketing-manager")
            customer_id: Optional customer ID for customer-specific routes
            
        Returns:
            Route info dict
        """
        if not self.k8s_available:
            logger.warning("Kubernetes not available, skipping HTTPRoute creation")
            return {"status": "skipped", "reason": "k8s_unavailable"}
        
        route_name = f"agent-{agent_type}"
        if customer_id:
            route_name = f"agent-{agent_type}-{customer_id[:8]}"
        
        # HTTPRoute manifest
        httproute = {
            "apiVersion": "gateway.networking.k8s.io/v1",
            "kind": "HTTPRoute",
            "metadata": {
                "name": route_name,
                "namespace": self.routes_namespace,
                "labels": {
                    "app": "ve-platform",
                    "agent-type": agent_type
                }
            },
            "spec": {
                "parentRefs": [
                    {
                        "name": self.gateway_name,
                        "namespace": self.gateway_namespace
                    }
                ],
                "rules": [
                    {
                        "matches": [
                            {
                                "path": {
                                    "type": "PathPrefix",
                                    "value": f"/agents/{agent_type}"
                                }
                            }
                        ],
                        "backendRefs": [
                            {
                                "name": agent_type,
                                "namespace": "default",
                                "port": 8080
                            }
                        ]
                    }
                ]
            }
        }
        
        try:
            # Create HTTPRoute
            self.custom_api.create_namespaced_custom_object(
                group="gateway.networking.k8s.io",
                version="v1",
                namespace=self.routes_namespace,
                plural="httproutes",
                body=httproute
            )
            
            logger.info(f"Created HTTPRoute {route_name} for agent {agent_type}")
            
            return {
                "route_name": route_name,
                "agent_type": agent_type,
                "gateway": f"{self.gateway_name}.{self.gateway_namespace}",
                "backend": f"{agent_type}.agents-system:8080",
                "path": f"/agents/{agent_type}",
                "status": "created"
            }
            
        except ApiException as e:
            if e.status == 409:
                logger.info(f"HTTPRoute {route_name} already exists")
                return {
                    "route_name": route_name,
                    "status": "exists"
                }
            else:
                logger.error(f"Failed to create HTTPRoute: {e}")
                raise
    
    def delete_agent_route(
        self,
        agent_type: str,
        customer_id: Optional[str] = None
    ) -> bool:
        """
        Delete HTTPRoute for an agent type
        
        Args:
            agent_type: Agent type
            customer_id: Optional customer ID
            
        Returns:
            True if deleted successfully
        """
        if not self.k8s_available:
            logger.warning("Kubernetes not available, skipping HTTPRoute deletion")
            return False
        
        route_name = f"agent-{agent_type}"
        if customer_id:
            route_name = f"agent-{agent_type}-{customer_id[:8]}"
        
        try:
            self.custom_api.delete_namespaced_custom_object(
                group="gateway.networking.k8s.io",
                version="v1",
                namespace=self.routes_namespace,
                plural="httproutes",
                name=route_name
            )
            
            logger.info(f"Deleted HTTPRoute {route_name}")
            return True
            
        except ApiException as e:
            if e.status == 404:
                logger.info(f"HTTPRoute {route_name} not found (already deleted)")
                return True
            else:
                logger.error(f"Failed to delete HTTPRoute: {e}")
                return False
    
    def list_agent_routes(self) -> list:
        """List all agent HTTPRoutes"""
        if not self.k8s_available:
            return []
        
        try:
            routes = self.custom_api.list_namespaced_custom_object(
                group="gateway.networking.k8s.io",
                version="v1",
                namespace=self.routes_namespace,
                plural="httproutes",
                label_selector="app=ve-platform"
            )
            
            return routes.get("items", [])
            
        except ApiException as e:
            logger.error(f"Failed to list HTTPRoutes: {e}")
            return []

# Singleton instance
_httproute_service = None

def get_httproute_service() -> HTTPRouteService:
    """Get or create HTTPRoute service singleton"""
    global _httproute_service
    if _httproute_service is None:
        _httproute_service = HTTPRouteService()
    return _httproute_service
