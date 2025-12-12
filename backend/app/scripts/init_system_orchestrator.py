
import asyncio
import logging
from app.services.gateway_config_service import get_gateway_config_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_system_orchestrator():
    logger.info("Initializing System Orchestrator configuration in Agent Gateway...")
    
    service = get_gateway_config_service()
    agent_type = "system-orchestrator"
    
    # 1. Create Route
    print(f"Creating route for {agent_type} in kagent namespace...")
    result = service.create_agent_route(agent_type=agent_type, agent_namespace="kagent")
    print(f"Route creation result: {result}")
    
    # 2. Update TrafficPolicy to Allow All (System Service)
    # We manually patch the policy because grant_customer_access is for specific customers
    print(f"Updating TrafficPolicy to allow global access for {agent_type}...")
    
    if not service.k8s_available:
        print("⚠️ Kubernetes not available. Skipping Policy Patch (Mock Mode assumed valid).")
        return

    policy_name = f"rbac-{agent_type}"
    agent_namespace = "kagent" # Use existing kagent namespace

    try:
        # Get existing policy
        policy = service.custom_api.get_namespaced_custom_object(
            group="gateway.kgateway.dev",
            version="v1alpha1",
            namespace=agent_namespace,
            plural="trafficpolicies",
            name=policy_name
        )
        
        # Modify it to allow all
        if "spec" not in policy: policy["spec"] = {}
        if "rbac" not in policy["spec"]: policy["spec"]["rbac"] = {}
        if "policy" not in policy["spec"]["rbac"]: policy["spec"]["rbac"]["policy"] = {}
        
        # Allow any authenticated request
        policy["spec"]["rbac"]["policy"]["matchExpressions"] = ["request.headers['X-Customer-ID'].size() > 0"]
        
        # Update annotation
        if "metadata" not in policy: policy["metadata"] = {}
        if "annotations" not in policy["metadata"]: policy["metadata"]["annotations"] = {}
        policy["metadata"]["annotations"]["allowed_customers"] = "ALL_SYSTEM"
        
        # Replace (PUT)
        service.custom_api.replace_namespaced_custom_object(
            group="gateway.kgateway.dev",
            version="v1alpha1",
            namespace=agent_namespace,
            plural="trafficpolicies",
            name=policy_name,
            body=policy
        )
        print(f"✅ Successfully updated {policy_name} to allow all customers.")
        
    except Exception as e:
        print(f"❌ Failed to update TrafficPolicy: {e}")

if __name__ == "__main__":
    asyncio.run(init_system_orchestrator())
