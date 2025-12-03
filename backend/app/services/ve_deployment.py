"""
VE Deployment Service
Handles deployment of VEs to Kubernetes using KAgent
"""
import logging
import yaml
from typing import Dict, Any
from app.core.config import settings
from app.services.kubernetes_service import get_kubernetes_service

logger = logging.getLogger(__name__)

async def deploy_ve_to_kubernetes(
    customer_id: str,
    customer_ve_id: str,
    ve_template: Dict[str, Any],
    namespace: str,
    agent_name: str
) -> bool:
    """
    Deploy a VE to Kubernetes as a KAgent Agent resource
    
    Args:
        customer_id: Customer UUID
        customer_ve_id: Customer VE UUID
        ve_template: VE template from marketplace
        namespace: IGNORED (Always uses 'agents-system')
        agent_name: Agent name in Kubernetes
    
    Returns:
        bool: True if deployment successful
    """
    try:
        # Get Kubernetes service
        k8s_service = get_kubernetes_service()
        
        # Always use shared namespace
        shared_namespace = "agents-system"
        
        # Ensure shared namespace exists
        await k8s_service.ensure_shared_namespace()
        
        # Create ServiceAccount for this customer
        sa_name = await k8s_service.create_customer_service_account(customer_id, shared_namespace)
        
        # Create KAgent manifest
        agent_manifest = create_kagent_manifest(
            agent_name=agent_name,
            namespace=shared_namespace,
            ve_template=ve_template,
            customer_id=customer_id,
            customer_ve_id=customer_ve_id,
            service_account_name=sa_name
        )
        
        # Deploy agent to Kubernetes
        success = await k8s_service.deploy_agent(
            namespace=shared_namespace,
            agent_name=agent_name,
            agent_manifest=agent_manifest
        )
        
        if success:
            logger.info(f"Successfully deployed agent {agent_name} to namespace {shared_namespace}")
            
            # Apply Network Policy for isolation
            await k8s_service.create_agent_network_policy(
                agent_name=agent_name,
                customer_id=customer_id,
                namespace=shared_namespace
            )
            
            # Create HTTPRoute for the agent
            route_manifest = create_http_route_manifest(
                agent_name=agent_name,
                namespace=shared_namespace,
                customer_id=customer_id
            )
            
            # Apply HTTPRoute
            route_success = await k8s_service.apply_http_route(
                namespace=shared_namespace,
                route_name=f"{agent_name}-route",
                route_manifest=route_manifest
            )
            
            if not route_success:
                logger.warning(f"Failed to create HTTPRoute for agent {agent_name}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to deploy VE to Kubernetes: {e}")
        raise

def create_kagent_manifest(
    agent_name: str,
    namespace: str,
    ve_template: Dict[str, Any],
    customer_id: str,
    customer_ve_id: str,
    service_account_name: str
) -> Dict[str, Any]:
    """
    Create KAgent manifest for VE deployment
    """
    return {
        "apiVersion": "kagent.dev/v1alpha2",
        "kind": "Agent",
        "metadata": {
            "name": agent_name,
            "namespace": namespace,
            "labels": {
                "customer_id": customer_id,
                "customer_ve_id": customer_ve_id,
                "ve_type": ve_template["role"].lower().replace(" ", "-"),
                "department": ve_template["department"],
                "seniority": ve_template["seniority_level"]
            }
        },
        "spec": {
            "type": "Declarative",
            "serviceAccountName": service_account_name,
            "declarative": {
                "systemMessage": f"You are a {ve_template['role']} for Customer {customer_id}. {ve_template.get('description', '')}",
                "model": "gpt-4",  # Default model, can be parameterized
                "tools": []  # Add tools if defined in template
            }
        }
    }

def create_http_route_manifest(
    agent_name: str,
    namespace: str,
    customer_id: str
) -> Dict[str, Any]:
    """
    Create HTTPRoute manifest for exposing the agent
    """
    return {
        "apiVersion": "gateway.networking.k8s.io/v1",
        "kind": "HTTPRoute",
        "metadata": {
            "name": f"{agent_name}-route",
            "namespace": namespace,
            "labels": {
                "customer_id": customer_id,
                "agent_name": agent_name
            }
        },
        "spec": {
            "parentRefs": [
                {
                    "name": "kgateway",  # Assuming standard gateway name
                    "namespace": "kgateway-system"
                }
            ],
            "rules": [
                {
                    "matches": [
                        {
                            "path": {
                                "type": "PathPrefix",
                                "value": f"/agents/{customer_id}/{agent_name}"
                            }
                        }
                    ],
                    "backendRefs": [
                        {
                            "name": agent_name,
                            "port": 8080
                        }
                    ]
                }
            ]
        }
    }
