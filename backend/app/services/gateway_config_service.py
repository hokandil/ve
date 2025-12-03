"""
HTTPRoute and TrafficPolicy Management Service
Manages Kubernetes HTTPRoute and TrafficPolicy resources for Agent Gateway
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)

def log_security_event(event_type: str, agent_type: str, customer_id: Optional[str] = None, 
                       details: Optional[Dict[str, Any]] = None, success: bool = True):
    """Log structured security events for RBAC operations"""
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "agent_type": agent_type,
        "customer_id": customer_id,
        "success": success,
        "details": details or {}
    }
    
    log_msg = f"RBAC Event: {event_type} | Agent: {agent_type}"
    if customer_id:
        log_msg += f" | Customer: {customer_id}"
    
    if success:
        logger.info(log_msg, extra={"security_event": event})
    else:
        logger.error(log_msg, extra={"security_event": event})

class AgentGatewayConfigService:
    """Service for managing Agent Gateway configuration (HTTPRoutes and TrafficPolicies)"""
    
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
        agent_namespace: str = "agents-system"
    ) -> Dict[str, Any]:
        """
        Create HTTPRoute for an agent (called when admin imports agent)
        Also creates a default-deny TrafficPolicy to ensure security.
        
        Args:
            agent_type: Agent type (e.g., "wellness")
            agent_namespace: Namespace where agent service is deployed
            
        Returns:
            Route info dict
        """
        if not self.k8s_available:
            logger.warning("Kubernetes not available, skipping HTTPRoute creation")
            return {"status": "skipped", "reason": "k8s_unavailable"}
        
        route_name = f"agent-{agent_type}"
        
        # HTTPRoute manifest with hostname-based routing
        httproute = {
            "apiVersion": "gateway.networking.k8s.io/v1",
            "kind": "HTTPRoute",
            "metadata": {
                "name": route_name,
                "namespace": agent_namespace,  # Create route in same namespace as agent
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
                "hostnames": [f"{agent_type}.local"],
                "rules": [
                    {
                        "backendRefs": [
                            {
                                "name": agent_type,
                                "namespace": agent_namespace,
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
                namespace=agent_namespace,  # Use agent_namespace
                plural="httproutes",
                body=httproute
            )
            
            log_security_event(
                event_type="route_created",
                agent_type=agent_type,
                details={"route_name": route_name, "namespace": agent_namespace}
            )
            logger.info(f"Created HTTPRoute {route_name} for agent {agent_type} in {agent_namespace}")
            
            # Create Default Deny TrafficPolicy
            policy_name = f"rbac-{agent_type}"
            policy = {
                "apiVersion": "gateway.kgateway.dev/v1alpha1",
                "kind": "TrafficPolicy",
                "metadata": {
                    "name": policy_name,
                    "namespace": agent_namespace,  # Use agent_namespace
                    "labels": {
                        "app": "ve-platform",
                        "agent-type": agent_type
                    },
                    "annotations": {
                        "allowed_customers": "[]"
                    }
                },
                "spec": {
                    "targetRefs": [
                        {
                            "group": "gateway.networking.k8s.io",
                            "kind": "HTTPRoute",
                            "name": route_name
                        }
                    ],
                    "rbac": {
                        "policy": {
                            "matchExpressions": [
                                # Deny all by requiring a header that will never match
                                "request.headers['X-Customer-ID'] == 'deny-all-default'"
                            ]
                        }
                    }
                }
            }
            
            try:
                self.custom_api.create_namespaced_custom_object(
                    group="gateway.kgateway.dev",
                    version="v1alpha1",
                    namespace=agent_namespace,
                    plural="trafficpolicies",
                    body=policy
                )
                log_security_event(
                    event_type="policy_created",
                    agent_type=agent_type,
                    details={
                        "policy_name": policy_name,
                        "mode": "deny_all",
                        "allowed_customers": []
                    }
                )
                logger.info(f"Created default-deny TrafficPolicy {policy_name}")
            except ApiException as e:
                if e.status == 409:
                    logger.info(f"TrafficPolicy {policy_name} already exists")
                else:
                    logger.error(f"Failed to create TrafficPolicy: {e}")
                    # We continue, but log error. Ideally we should rollback HTTPRoute.
            
            return {
                "route_name": route_name,
                "agent_type": agent_type,
                "gateway": f"{self.gateway_name}.{self.gateway_namespace}",
                "backend": f"{agent_type}.{agent_namespace}:8080",
                "hostname": f"{agent_type}.local",
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
        
    def grant_customer_access(
        self,
        agent_type: str,
        customer_id: str,
        agent_namespace: str = "kagent"
    ) -> Dict[str, Any]:
        """
        Grant a customer access to an agent via TrafficPolicy
        
        Args:
            agent_type: Agent type
            customer_id: Customer UUID
            agent_namespace: Namespace where agent/policy resides
            
        Returns:
            Status dict
        """
        if not self.k8s_available:
            logger.warning("Kubernetes not available, skipping access grant")
            return {"status": "skipped"}
        
        policy_name = f"rbac-{agent_type}"
        
        try:
            logger.info(f"Attempting to grant access for customer {customer_id} to agent {agent_type} (Policy: {policy_name})")
            
            # Get existing policy
            policy = self.custom_api.get_namespaced_custom_object(
                group="gateway.kgateway.dev",
                version="v1alpha1",
                namespace=agent_namespace,
                plural="trafficpolicies",
                name=policy_name
            )
            
            # Add customer to allowed list
            annotations = policy.get("metadata", {}).get("annotations", {})
            if not annotations:
                if "metadata" not in policy:
                    policy["metadata"] = {}
                if "annotations" not in policy["metadata"]:
                    policy["metadata"]["annotations"] = {}
                annotations = policy["metadata"]["annotations"]
            
            existing_customers_str = annotations.get("allowed_customers", "[]")
            try:
                existing_customers = json.loads(existing_customers_str)
            except:
                existing_customers = []

            if customer_id not in existing_customers:
                existing_customers.append(customer_id)
                logger.info(f"Added customer {customer_id} to policy. Total: {len(existing_customers)}")
            else:
                logger.info(f"Customer {customer_id} already in policy {policy_name}")
            
            # Update CEL expression
            cel_expr = self._build_cel_expression(existing_customers)
            
            # Update policy spec
            if "spec" not in policy:
                policy["spec"] = {}
            if "rbac" not in policy["spec"]:
                policy["spec"]["rbac"] = {}
            if "policy" not in policy["spec"]["rbac"]:
                policy["spec"]["rbac"]["policy"] = {}
                
            policy["spec"]["rbac"]["policy"]["matchExpressions"] = [cel_expr]
            policy["metadata"]["annotations"]["allowed_customers"] = json.dumps(existing_customers)
            
            # Use strategic merge patch to avoid race conditions
            patch_body = {
                "metadata": {
                    "annotations": {
                        "allowed_customers": json.dumps(existing_customers)
                    }
                },
                "spec": {
                    "rbac": {
                        "policy": {
                            "matchExpressions": [cel_expr]
                        }
                    }
                }
            }
            
            # Patch policy with merge patch for concurrent safety
            self.custom_api.patch_namespaced_custom_object(
                group="gateway.kgateway.dev",
                version="v1alpha1",
                namespace=agent_namespace,
                plural="trafficpolicies",
                name=policy_name,
                body=patch_body,
                _content_type='application/merge-patch+json'  # Forces merge patch
            )
            
            log_security_event(
                event_type="access_granted",
                agent_type=agent_type,
                customer_id=customer_id,
                details={
                    "policy_name": policy_name,
                    "total_customers": len(existing_customers)
                }
            )
            logger.info(f"Updated TrafficPolicy {policy_name} to allow customer {customer_id}")
            
            return {
                "policy_name": policy_name,
                "customer_id": customer_id,
                "agent_type": agent_type,
                "status": "granted"
            }
            
        except ApiException as e:
            log_security_event(
                event_type="access_grant_failed",
                agent_type=agent_type,
                customer_id=customer_id,
                details={"error": str(e), "policy_name": policy_name},
                success=False
            )
            logger.error(f"Failed to grant access: {e}")
            raise

    def revoke_customer_access(
        self,
        agent_type: str,
        customer_id: str,
        agent_namespace: str = "kagent"
    ) -> Dict[str, Any]:
        """
        Revoke a customer's access to an agent
        
        Args:
            agent_type: Agent type
            customer_id: Customer UUID
            agent_namespace: Namespace where agent/policy resides
            
        Returns:
            Status dict
        """
        if not self.k8s_available:
            return {"status": "skipped"}
            
        policy_name = f"rbac-{agent_type}"
        
        try:
            logger.info(f"Attempting to revoke access for customer {customer_id} from agent {agent_type} (Policy: {policy_name})")
            
            policy = self.custom_api.get_namespaced_custom_object(
                group="gateway.kgateway.dev",
                version="v1alpha1",
                namespace=agent_namespace,
                plural="trafficpolicies",
                name=policy_name
            )
            
            # Remove customer from allowed list
            annotations = policy.get("metadata", {}).get("annotations", {})
            if not annotations:
                if "metadata" not in policy:
                    policy["metadata"] = {}
                if "annotations" not in policy["metadata"]:
                    policy["metadata"]["annotations"] = {}
                annotations = policy["metadata"]["annotations"]
            
            existing_customers_str = annotations.get("allowed_customers", "[]")
            try:
                existing_customers = json.loads(existing_customers_str)
            except:
                existing_customers = []

            if customer_id in existing_customers:
                existing_customers.remove(customer_id)
                logger.info(f"Removed customer {customer_id} from policy. Remaining: {existing_customers}")
            else:
                logger.warning(f"Customer {customer_id} not found in policy {policy_name}")
            
            if len(existing_customers) == 0:
                # No more customers, revert to deny-all (DO NOT DELETE POLICY)
                logger.info(f"No customers left, reverting {policy_name} to deny-all")
                
                # Update CEL expression to deny all
                policy["spec"]["rbac"]["policy"]["matchExpressions"] = ["request.headers['X-Customer-ID'] == 'deny-all-default'"]
                policy["metadata"]["annotations"]["allowed_customers"] = "[]"
                
                # Use merge patch for concurrent safety
                patch_body = {
                    "metadata": {
                        "annotations": {
                            "allowed_customers": "[]"
                        }
                    },
                    "spec": {
                        "rbac": {
                            "policy": {
                                "matchExpressions": ["request.headers['X-Customer-ID'] == 'deny-all-default'"]
                            }
                        }
                    }
                }
                
                self.custom_api.patch_namespaced_custom_object(
                    group="gateway.kgateway.dev",
                    version="v1alpha1",
                    namespace=agent_namespace,
                    plural="trafficpolicies",
                    name=policy_name,
                    body=patch_body,
                    _content_type='application/merge-patch+json'
                )
                
                log_security_event(
                    event_type="access_revoked",
                    agent_type=agent_type,
                    customer_id=customer_id,
                    details={
                        "policy_name": policy_name,
                        "total_customers": 0,
                        "reverted_to_deny_all": True
                    }
                )
                logger.info(f"Updated TrafficPolicy {policy_name} to deny-all")
            else:
                # Update CEL expression
                cel_expr = self._build_cel_expression(existing_customers)
                policy["spec"]["rbac"]["policy"]["matchExpressions"] = [cel_expr]
                policy["metadata"]["annotations"]["allowed_customers"] = json.dumps(existing_customers)
                
                # Use merge patch for concurrent safety
                patch_body = {
                    "metadata": {
                        "annotations": {
                            "allowed_customers": json.dumps(existing_customers)
                        }
                    },
                    "spec": {
                        "rbac": {
                            "policy": {
                                "matchExpressions": [cel_expr]
                            }
                        }
                    }
                }
                
                self.custom_api.patch_namespaced_custom_object(
                    group="gateway.kgateway.dev",
                    version="v1alpha1",
                    namespace=agent_namespace,
                    plural="trafficpolicies",
                    name=policy_name,
                    body=patch_body,
                    _content_type='application/merge-patch+json'
                )
                
                log_security_event(
                    event_type="access_revoked",
                    agent_type=agent_type,
                    customer_id=customer_id,
                    details={
                        "policy_name": policy_name,
                        "total_customers": len(existing_customers),
                        "remaining_customers": existing_customers
                    }
                )
                logger.info(f"Updated TrafficPolicy {policy_name} to revoke access from customer {customer_id}")
            
            return {
                "policy_name": policy_name,
                "customer_id": customer_id,
                "agent_type": agent_type,
                "status": "revoked"
            }
            
        except ApiException as e:
            if e.status == 404:
                logger.info(f"TrafficPolicy {policy_name} not found (already deleted)")
                return {"status": "not_found"}
            else:
                log_security_event(
                    event_type="access_revoke_failed",
                    agent_type=agent_type,
                    customer_id=customer_id,
                    details={"error": str(e), "policy_name": policy_name},
                    success=False
                )
                logger.error(f"Failed to revoke access: {e}\nBody: {e.body}")
                raise
    
    def delete_agent_route(
        self,
        agent_type: str,
        agent_namespace: str = "kagent"
    ) -> bool:
        """
        Delete HTTPRoute for an agent (called when admin deletes agent)
        Also deletes associated TrafficPolicy
        
        Args:
            agent_type: Agent type
            
        Returns:
            True if deleted successfully
        """
        if not self.k8s_available:
            logger.warning("Kubernetes not available, skipping HTTPRoute deletion")
            return False
        
        route_name = f"agent-{agent_type}"
        policy_name = f"rbac-{agent_type}"
        
        # DELETE PROTECTION: Check if customers still have access
        try:
            policy = self.custom_api.get_namespaced_custom_object(
                group="gateway.kgateway.dev",
                version="v1alpha1",
                namespace=agent_namespace,
                plural="trafficpolicies",
                name=policy_name
            )
            
            # Get allowed_customers list
            annotations = policy.get("metadata", {}).get("annotations", {})
            allowed_customers_str = annotations.get("allowed_customers", "[]")
            
            try:
                allowed_customers = json.loads(allowed_customers_str)
            except:
                allowed_customers = []
            
            # PROTECTION: Fail if customers still have access
            if len(allowed_customers) > 0:
                log_security_event(
                    event_type="route_delete_blocked",
                    agent_type=agent_type,
                    details={
                        "reason": "Customers still have access",
                        "allowed_customers_count": len(allowed_customers),
                        "customers": allowed_customers
                    },
                    success=False
                )
                logger.error(
                    f"Cannot delete route {route_name}: "
                    f"{len(allowed_customers)} customers still have access"
                )
                raise Exception(
                    f"Cannot delete agent {agent_type}: "
                    f"{len(allowed_customers)} customers still have active access. "
                    f"Revoke access first."
                )
            
            logger.info(f"Delete protection check passed for {agent_type} (0 customers)")
            
        except ApiException as e:
            if e.status != 404:
                logger.error(f"Failed to check delete protection: {e}")
                raise
            # If policy doesn't exist (404), it's safe to delete the route
        
        # Delete TrafficPolicy first
        try:
            self.custom_api.delete_namespaced_custom_object(
                group="gateway.kgateway.dev",
                version="v1alpha1",
                namespace=agent_namespace,
                plural="trafficpolicies",
                name=policy_name
            )
            
            log_security_event(
                event_type="policy_deleted",
                agent_type=agent_type,
                details={"policy_name": policy_name}
            )
            logger.info(f"Deleted TrafficPolicy {policy_name}")
        except ApiException as e:
            if e.status != 404:
                logger.error(f"Failed to delete TrafficPolicy: {e}")
        
        # Delete HTTPRoute
        try:
            self.custom_api.delete_namespaced_custom_object(
                group="gateway.networking.k8s.io",
                version="v1",
                namespace=self.routes_namespace,
                plural="httproutes",
                name=route_name
            )
            
            
            log_security_event(
                event_type="route_deleted",
                agent_type=agent_type,
                details={"route_name": route_name}
            )
            logger.info(f"Deleted HTTPRoute {route_name}")
            return True
            
        except ApiException as e:
            if e.status == 404:
                logger.info(f"HTTPRoute {route_name} not found (already deleted)")
                return True
            else:
                log_security_event(
                    event_type="route_delete_failed",
                    agent_type=agent_type,
                    details={"error": str(e), "route_name": route_name},
                    success=False
                )
                logger.error(f"Failed to delete HTTPRoute: {e}")
                return False
    
    def _build_cel_expression(self, customer_ids: List[str]) -> str:
        """
        Build CEL expression to allow specific customers
        
        Args:
            customer_ids: List of customer UUIDs
            
        Returns:
            CEL expression string
        """
        # CEL expression: request.headers['X-Customer-ID'] in ['id1', 'id2', ...]
        customer_list = ", ".join([f"'{cid}'" for cid in customer_ids])
        return f"request.headers['X-Customer-ID'] in [{customer_list}]"
    
    def list_agent_routes(self, namespace: str = "kagent") -> list:
        """List all agent HTTPRoutes"""
        if not self.k8s_available:
            return []
        
        try:
            routes = self.custom_api.list_namespaced_custom_object(
                group="gateway.networking.k8s.io",
                version="v1",
                namespace=namespace,
                plural="httproutes",
                label_selector="app=ve-platform"
            )
            
            return routes.get("items", [])
            
        except ApiException as e:
            logger.error(f"Failed to list HTTPRoutes: {e}")
            return []

# Singleton instance
_gateway_config_service = None

def get_gateway_config_service() -> AgentGatewayConfigService:
    """Get or create Agent Gateway config service singleton"""
    global _gateway_config_service
    if _gateway_config_service is None:
        _gateway_config_service = AgentGatewayConfigService()
    return _gateway_config_service
