"""
Kubernetes Service
Handles Kubernetes cluster operations for VE deployment and management
"""
import logging
from typing import Dict, Any, Optional, List
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import yaml

from app.core.config import settings

logger = logging.getLogger(__name__)


class KubernetesService:
    """Service for managing Kubernetes resources"""
    
    def __init__(self):
        """Initialize Kubernetes client"""
        try:
            # Try to load in-cluster config first (for production)
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes config")
        except config.ConfigException:
            try:
                # Fall back to kubeconfig (for development)
                config.load_kube_config()
                logger.info("Loaded kubeconfig")
            except config.ConfigException:
                logger.warning("Could not load Kubernetes config - K8s operations will be simulated")
                self.enabled = False
                return
        
        self.enabled = True
        self.core_v1 = client.CoreV1Api()
        self.custom_api = client.CustomObjectsApi()
        self.apps_v1 = client.AppsV1Api()
    
    async def ensure_shared_namespace(self) -> bool:
        """
        Ensure the shared 'agents-system' namespace exists
        """
        if not self.enabled:
            return True
            
        namespace_name = "agents-system"
        
        try:
            try:
                self.core_v1.read_namespace(name=namespace_name)
                return True
            except ApiException as e:
                if e.status != 404:
                    raise
            
            namespace = client.V1Namespace(
                metadata=client.V1ObjectMeta(
                    name=namespace_name,
                    labels={"managed_by": "ve-saas-platform"}
                )
            )
            
            self.core_v1.create_namespace(body=namespace)
            logger.info(f"Created shared namespace {namespace_name}")
            return True
            
        except ApiException as e:
            logger.error(f"Failed to create shared namespace: {e}")
            raise

    async def create_customer_service_account(self, customer_id: str, namespace: str = "agents-system") -> str:
        """
        Create a ServiceAccount for a customer's agents
        """
        if not self.enabled:
            return f"sa-{customer_id}"
            
        sa_name = f"sa-{customer_id}"
        
        try:
            sa = client.V1ServiceAccount(
                metadata=client.V1ObjectMeta(
                    name=sa_name,
                    namespace=namespace,
                    labels={"customer_id": customer_id}
                )
            )
            
            try:
                self.core_v1.create_namespaced_service_account(namespace=namespace, body=sa)
                logger.info(f"Created ServiceAccount {sa_name}")
            except ApiException as e:
                if e.status != 409:
                    raise
                    
            return sa_name
            
        except ApiException as e:
            logger.error(f"Failed to create ServiceAccount: {e}")
            raise

    async def create_agent_network_policy(self, agent_name: str, customer_id: str, namespace: str = "agents-system") -> None:
        """
        Create NetworkPolicy to isolate the agent pod
        - Allow Egress to Internet (for tools)
        - Allow Ingress from Gateway
        - Deny Ingress/Egress to other agents
        """
        if not self.enabled:
            return

        policy_name = f"np-{agent_name}"
        
        policy = client.V1NetworkPolicy(
            metadata=client.V1ObjectMeta(
                name=policy_name,
                namespace=namespace,
                labels={"agent": agent_name, "customer_id": customer_id}
            ),
            spec=client.V1NetworkPolicySpec(
                pod_selector=client.V1LabelSelector(
                    match_labels={"app": agent_name}
                ),
                policy_types=["Ingress", "Egress"],
                ingress=[
                    # Allow traffic from Agent Gateway
                    client.V1NetworkPolicyIngressRule(
                        from_=[
                            client.V1NetworkPolicyPeer(
                                namespace_selector=client.V1LabelSelector(
                                    match_labels={"kubernetes.io/metadata.name": "kgateway-system"}
                                )
                            )
                        ]
                    )
                ],
                egress=[
                    # Allow DNS
                    client.V1NetworkPolicyEgressRule(
                        to=[
                            client.V1NetworkPolicyPeer(
                                namespace_selector=client.V1LabelSelector(
                                    match_labels={"kubernetes.io/metadata.name": "kube-system"}
                                )
                            )
                        ],
                        ports=[
                            client.V1NetworkPolicyPort(protocol="UDP", port=53),
                            client.V1NetworkPolicyPort(protocol="TCP", port=53)
                        ]
                    ),
                    # Allow Internet Access (0.0.0.0/0)
                    client.V1NetworkPolicyEgressRule(
                        to=[client.V1NetworkPolicyPeer(ip_block=client.V1IPBlock(cidr="0.0.0.0/0"))]
                    )
                ]
            )
        )

        try:
            # Using networking_v1_api for NetworkPolicies
            networking_v1 = client.NetworkingV1Api()
            try:
                networking_v1.create_namespaced_network_policy(namespace=namespace, body=policy)
                logger.info(f"Created NetworkPolicy {policy_name}")
            except ApiException as e:
                if e.status == 409:
                    networking_v1.patch_namespaced_network_policy(name=policy_name, namespace=namespace, body=policy)
                else:
                    raise
        except ApiException as e:
            logger.error(f"Failed to create NetworkPolicy: {e}")
            # Don't raise, as this is a security enhancement, not a blocker for deployment logic flow
            # (In strict mode we should raise)
    
    async def deploy_agent(
        self,
        namespace: str,
        agent_name: str,
        agent_manifest: Dict[str, Any]
    ) -> bool:
        """
        Deploy a KAgent Agent resource to Kubernetes
        
        Args:
            namespace: Kubernetes namespace
            agent_name: Name of the agent
            agent_manifest: KAgent manifest dictionary
            
        Returns:
            bool: True if deployment successful
        """
        if not self.enabled:
            logger.info(f"K8s disabled - would deploy agent {agent_name} to {namespace}")
            logger.debug(f"Manifest: {yaml.dump(agent_manifest)}")
            return True
        
        try:
            # Create the KAgent Agent custom resource
            self.custom_api.create_namespaced_custom_object(
                group="kagent.dev",
                version="v1alpha2",
                namespace=namespace,
                plural="agents",
                body=agent_manifest
            )
            
            logger.info(f"Deployed agent {agent_name} to namespace {namespace}")
            return True
            
        except ApiException as e:
            if e.status == 409:
                logger.warning(f"Agent {agent_name} already exists, updating...")
                return await self.update_agent(namespace, agent_name, agent_manifest)
            else:
                logger.error(f"Failed to deploy agent: {e}")
                raise
    
    async def update_agent(
        self,
        namespace: str,
        agent_name: str,
        agent_manifest: Dict[str, Any]
    ) -> bool:
        """Update an existing agent"""
        if not self.enabled:
            logger.info(f"K8s disabled - would update agent {agent_name}")
            return True
        
        try:
            self.custom_api.patch_namespaced_custom_object(
                group="kagent.dev",
                version="v1alpha2",
                namespace=namespace,
                plural="agents",
                name=agent_name,
                body=agent_manifest
            )
            
            logger.info(f"Updated agent {agent_name} in namespace {namespace}")
            return True
            
        except ApiException as e:
            logger.error(f"Failed to update agent: {e}")
            raise
    
    async def delete_agent(self, namespace: str, agent_name: str) -> bool:
        """Delete an agent from Kubernetes"""
        if not self.enabled:
            logger.info(f"K8s disabled - would delete agent {agent_name}")
            return True
        
        try:
            self.custom_api.delete_namespaced_custom_object(
                group="kagent.dev",
                version="v1alpha2",
                namespace=namespace,
                plural="agents",
                name=agent_name
            )
            
            logger.info(f"Deleted agent {agent_name} from namespace {namespace}")
            return True
            
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"Agent {agent_name} not found")
                return True
            else:
                logger.error(f"Failed to delete agent: {e}")
                raise
    
    async def get_agent_status(
        self,
        namespace: str,
        agent_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get the status of an agent"""
        if not self.enabled:
            return {"status": "simulated", "ready": True}
        
        try:
            agent = self.custom_api.get_namespaced_custom_object(
                group="kagent.dev",
                version="v1alpha2",
                namespace=namespace,
                plural="agents",
                name=agent_name
            )
            
            return agent.get("status", {})
            
        except ApiException as e:
            if e.status == 404:
                return None
            else:
                logger.error(f"Failed to get agent status: {e}")
                raise
    
    async def list_agents_in_namespace(self, namespace: str) -> List[Dict[str, Any]]:
        """List all agents in a namespace"""
        if not self.enabled:
            return []
        
        try:
            agents = self.custom_api.list_namespaced_custom_object(
                group="kagent.dev",
                version="v1alpha2",
                namespace=namespace,
                plural="agents"
            )
            
            return agents.get("items", [])
            
        except ApiException as e:
            logger.error(f"Failed to list agents: {e}")
            return []
    
    async def delete_customer_namespace(self, customer_id: str) -> bool:
        """Delete a customer's namespace and all resources"""
        if not self.enabled:
            logger.info(f"K8s disabled - would delete namespace for customer {customer_id}")
            return True
        
        namespace_name = f"{settings.K8S_NAMESPACE_PREFIX}{customer_id}"
        
        try:
            self.core_v1.delete_namespace(name=namespace_name)
            logger.info(f"Deleted namespace {namespace_name}")
            return True
            
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"Namespace {namespace_name} not found")
                return True
            else:
                logger.error(f"Failed to delete namespace: {e}")
                raise

    async def apply_http_route(
        self,
        namespace: str,
        route_name: str,
        route_manifest: Dict[str, Any]
    ) -> bool:
        """
        Apply an HTTPRoute resource (create or update)
        
        Args:
            namespace: Kubernetes namespace
            route_name: Name of the route
            route_manifest: HTTPRoute manifest dictionary
            
        Returns:
            bool: True if successful
        """
        if not self.enabled:
            logger.info(f"K8s disabled - would apply HTTPRoute {route_name} to {namespace}")
            return True
        
        try:
            # Try to create first
            self.custom_api.create_namespaced_custom_object(
                group="gateway.networking.k8s.io",
                version="v1",
                namespace=namespace,
                plural="httproutes",
                body=route_manifest
            )
            logger.info(f"Created HTTPRoute {route_name} in namespace {namespace}")
            return True
            
        except ApiException as e:
            if e.status == 409:
                # Already exists, update it
                try:
                    # Get resource version for optimistic locking (optional but good practice)
                    # For now just patch
                    self.custom_api.patch_namespaced_custom_object(
                        group="gateway.networking.k8s.io",
                        version="v1",
                        namespace=namespace,
                        plural="httproutes",
                        name=route_name,
                        body=route_manifest
                    )
                    logger.info(f"Updated HTTPRoute {route_name} in namespace {namespace}")
                    return True
                except ApiException as update_error:
                    logger.error(f"Failed to update HTTPRoute: {update_error}")
                    raise
            elif e.status == 404:
                 # Gateway API CRDs might not be installed
                 logger.warning(f"Failed to create HTTPRoute: {e}. Gateway API CRDs might be missing.")
                 return False
            else:
                logger.error(f"Failed to create HTTPRoute: {e}")
                raise


# Singleton instance
_k8s_service = None


def get_kubernetes_service() -> KubernetesService:
    """Get or create Kubernetes service singleton"""
    global _k8s_service
    if _k8s_service is None:
        _k8s_service = KubernetesService()
    return _k8s_service
