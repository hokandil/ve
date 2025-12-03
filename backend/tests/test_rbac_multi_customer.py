import json
import pytest
from unittest.mock import MagicMock, patch
from app.services.gateway_config_service import AgentGatewayConfigService

@pytest.fixture
def mock_k8s_api():
    with patch("kubernetes.client.CustomObjectsApi") as mock_api:
        yield mock_api.return_value

@pytest.fixture
def gateway_service(mock_k8s_api):
    # Patch config loading to avoid errors if no kubeconfig
    with patch("kubernetes.config.load_kube_config"), \
         patch("kubernetes.config.load_incluster_config"):
        service = AgentGatewayConfigService()
        service.custom_api = mock_k8s_api
        service.k8s_available = True
        return service

def test_multi_customer_rbac_flow(gateway_service, mock_k8s_api):
    """
    Test the complete flow of multi-customer access:
    1. Create agent route (Deny All)
    2. Customer A hires (Allow A)
    3. Customer B hires (Allow A and B)
    4. Customer A unhires (Allow B)
    5. Customer B unhires (Deny All)
    """
    agent_type = "wellness"
    customer_a = "cust-a-uuid"
    customer_b = "cust-b-uuid"
    policy_name = f"rbac-{agent_type}"

    # --- Step 1: Create Agent Route (Deny All) ---
    gateway_service.create_agent_route(agent_type)
    
    # Verify TrafficPolicy created with deny-all
    mock_k8s_api.create_namespaced_custom_object.assert_called()
    call_args = mock_k8s_api.create_namespaced_custom_object.call_args_list[-1]
    _, kwargs = call_args
    policy_body = kwargs['body']
    
    assert policy_body['kind'] == 'TrafficPolicy'
    assert policy_body['metadata']['name'] == policy_name
    # Verify deny-all expression
    match_expr = policy_body['spec']['rbac']['policy']['matchExpressions'][0]
    assert "deny-all-default" in match_expr
    assert policy_body['metadata']['annotations']['allowed_customers'] == "[]"

    # --- Step 2: Customer A Hires (Allow A) ---
    # Mock get_namespaced_custom_object to return the policy we just "created"
    mock_k8s_api.get_namespaced_custom_object.return_value = policy_body
    
    gateway_service.grant_customer_access(agent_type, customer_a)
    
    # Verify patch called with Customer A
    mock_k8s_api.patch_namespaced_custom_object.assert_called()
    patch_call = mock_k8s_api.patch_namespaced_custom_object.call_args_list[-1]
    _, patch_kwargs = patch_call
    patch_body = patch_kwargs['body']
    
    allowed = json.loads(patch_body['metadata']['annotations']['allowed_customers'])
    assert customer_a in allowed
    assert len(allowed) == 1
    
    # Verify CEL expression
    cel_expr = patch_body['spec']['rbac']['policy']['matchExpressions'][0]
    assert f"request.headers['X-Customer-ID'] == '{customer_a}'" in cel_expr or \
           f"request.headers['X-Customer-ID'] in ['{customer_a}']" in cel_expr

    # Update our mock "state"
    mock_k8s_api.get_namespaced_custom_object.return_value = patch_body

    # --- Step 3: Customer B Hires (Allow A and B) ---
    gateway_service.grant_customer_access(agent_type, customer_b)
    
    patch_call = mock_k8s_api.patch_namespaced_custom_object.call_args_list[-1]
    _, patch_kwargs = patch_call
    patch_body = patch_kwargs['body']
    
    allowed = json.loads(patch_body['metadata']['annotations']['allowed_customers'])
    assert customer_a in allowed
    assert customer_b in allowed
    assert len(allowed) == 2
    
    # Verify CEL expression contains both
    cel_expr = patch_body['spec']['rbac']['policy']['matchExpressions'][0]
    assert customer_a in cel_expr
    assert customer_b in cel_expr
    assert "in [" in cel_expr # Should use 'in' operator for multiple

    # Update mock state
    mock_k8s_api.get_namespaced_custom_object.return_value = patch_body

    # --- Step 4: Customer A Unhires (Allow B) ---
    gateway_service.revoke_customer_access(agent_type, customer_a)
    
    patch_call = mock_k8s_api.patch_namespaced_custom_object.call_args_list[-1]
    _, patch_kwargs = patch_call
    patch_body = patch_kwargs['body']
    
    allowed = json.loads(patch_body['metadata']['annotations']['allowed_customers'])
    assert customer_a not in allowed
    assert customer_b in allowed
    assert len(allowed) == 1
    
    # Update mock state
    mock_k8s_api.get_namespaced_custom_object.return_value = patch_body

    # --- Step 5: Customer B Unhires (Revert to Deny All) ---
    gateway_service.revoke_customer_access(agent_type, customer_b)
    
    patch_call = mock_k8s_api.patch_namespaced_custom_object.call_args_list[-1]
    _, patch_kwargs = patch_call
    patch_body = patch_kwargs['body']
    
    allowed = json.loads(patch_body['metadata']['annotations']['allowed_customers'])
    assert len(allowed) == 0
    
    # Verify reverted to deny-all
    cel_expr = patch_body['spec']['rbac']['policy']['matchExpressions'][0]
    assert "deny-all-default" in cel_expr
