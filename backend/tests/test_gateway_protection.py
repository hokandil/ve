"""
Test suite for gateway config service fixes:
- Delete protection
- Concurrent access safety
"""
import pytest
import json
import threading
from unittest.mock import Mock, patch, MagicMock
from kubernetes.client.rest import ApiException
from app.services.gateway_config_service import AgentGatewayConfigService

@pytest.fixture
def mock_k8s_service():
    """Mock Kubernetes service"""
    service = AgentGatewayConfigService()
    service.k8s_available = True
    service.custom_api = Mock()
    return service

@pytest.fixture
def mock_policy_no_customers():
    """Mock policy with no customers"""
    return {
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

@pytest.fixture
def mock_policy_with_customers():
    """Mock policy with customers"""
    return {
        "metadata": {
            "annotations": {
                "allowed_customers": json.dumps(["customer-1", "customer-2"])
            }
        },
        "spec": {
            "rbac": {
                "policy": {
                    "matchExpressions": ["request.headers['X-Customer-ID'] in ['customer-1', 'customer-2']"]
                }
            }
        }
    }

class TestDeleteProtection:
    """Test delete protection for agent routes"""
    
    def test_delete_with_no_customers_succeeds(self, mock_k8s_service, mock_policy_no_customers):
        """Test that deletion succeeds when no customers have access"""
        # Mock policy fetch
        mock_k8s_service.custom_api.get_namespaced_custom_object.return_value = mock_policy_no_customers
        
        # Mock successful deletion
        mock_k8s_service.custom_api.delete_namespaced_custom_object.return_value = {}
        
        result = mock_k8s_service.delete_agent_route(
            agent_type="test-agent",
            agent_namespace="kagent"
        )
        
        # Verify deletion succeeded
        assert result is True
        
        # Verify policy was checked
        mock_k8s_service.custom_api.get_namespaced_custom_object.assert_called_once()
        
        # Verify deletion was attempted
        assert mock_k8s_service.custom_api.delete_namespaced_custom_object.call_count == 2  # Policy + Route
    
    def test_delete_with_customers_fails(self, mock_k8s_service, mock_policy_with_customers):
        """Test that deletion fails when customers still have access"""
        # Mock policy fetch
        mock_k8s_service.custom_api.get_namespaced_custom_object.return_value = mock_policy_with_customers
        
        # Attempt deletion
        with pytest.raises(Exception) as exc_info:
            mock_k8s_service.delete_agent_route(
                agent_type="test-agent",
                agent_namespace="kagent"
            )
        
        # Verify error message
        assert "customers still have active access" in str(exc_info.value)
        assert "Revoke access first" in str(exc_info.value)
        
        # Verify deletion was NOT attempted
        mock_k8s_service.custom_api.delete_namespaced_custom_object.assert_not_called()
    
    def test_delete_with_policy_not_found(self, mock_k8s_service):
        """Test that deletion succeeds if policy doesn't exist (404)"""
        # Mock 404 error on policy fetch
        api_exception = ApiException(status=404)
        mock_k8s_service.custom_api.get_namespaced_custom_object.side_effect = api_exception
        
        # Mock successful route deletion
        mock_k8s_service.custom_api.delete_namespaced_custom_object.return_value = {}
        
        result = mock_k8s_service.delete_agent_route(
            agent_type="test-agent",
            agent_namespace="kagent"
        )
        
        # Verify deletion succeeded (policy doesn't exist, so safe to delete route)
        assert result is True
    
    def test_delete_error_message_includes_customer_count(self, mock_k8s_service):
        """Test that error message includes customer count"""
        policy_with_3_customers = {
            "metadata": {
                "annotations": {
                    "allowed_customers": json.dumps(["cust-1", "cust-2", "cust-3"])
                }
            }
        }
        
        mock_k8s_service.custom_api.get_namespaced_custom_object.return_value = policy_with_3_customers
        
        with pytest.raises(Exception) as exc_info:
            mock_k8s_service.delete_agent_route(
                agent_type="test-agent",
                agent_namespace="kagent"
            )
        
        # Verify error message includes count
        assert "3 customers" in str(exc_info.value)

class TestConcurrentAccessSafety:
    """Test concurrent access safety using merge patch"""
    
    def test_grant_access_uses_merge_patch(self, mock_k8s_service, mock_policy_no_customers):
        """Test that grant_customer_access uses merge patch"""
        # Mock policy fetch
        mock_k8s_service.custom_api.get_namespaced_custom_object.return_value = mock_policy_no_customers
        
        # Mock successful patch
        mock_k8s_service.custom_api.patch_namespaced_custom_object.return_value = {}
        
        mock_k8s_service.grant_customer_access(
            agent_type="test-agent",
            customer_id="customer-1",
            agent_namespace="kagent"
        )
        
        # Verify patch was called with merge-patch content type
        patch_call = mock_k8s_service.custom_api.patch_namespaced_custom_object.call_args
        assert patch_call.kwargs.get("_content_type") == "application/merge-patch+json"
        
        # Verify patch body structure
        patch_body = patch_call.args[6]  # body argument
        assert "metadata" in patch_body
        assert "spec" in patch_body
        assert "annotations" in patch_body["metadata"]
        assert "allowed_customers" in patch_body["metadata"]["annotations"]
    
    def test_revoke_access_uses_merge_patch(self, mock_k8s_service, mock_policy_with_customers):
        """Test that revoke_customer_access uses merge patch"""
        # Mock policy fetch
        mock_k8s_service.custom_api.get_namespaced_custom_object.return_value = mock_policy_with_customers
        
        # Mock successful patch
        mock_k8s_service.custom_api.patch_namespaced_custom_object.return_value = {}
        
        mock_k8s_service.revoke_customer_access(
            agent_type="test-agent",
            customer_id="customer-1",
            agent_namespace="kagent"
        )
        
        # Verify patch was called with merge-patch content type
        patch_call = mock_k8s_service.custom_api.patch_namespaced_custom_object.call_args
        assert patch_call.kwargs.get("_content_type") == "application/merge-patch+json"
    
    def test_concurrent_grant_access_simulation(self, mock_k8s_service):
        """Test simulated concurrent grant_customer_access calls"""
        # Track all patch calls
        patch_calls = []
        
        def mock_patch(*args, **kwargs):
            patch_calls.append(kwargs.get("body"))
            return {}
        
        mock_k8s_service.custom_api.patch_namespaced_custom_object = mock_patch
        
        # Mock policy fetch to return different states
        call_count = [0]
        def mock_get(*args, **kwargs):
            call_count[0] += 1
            # Simulate different customers being added
            existing = [f"customer-{i}" for i in range(call_count[0])]
            return {
                "metadata": {
                    "annotations": {
                        "allowed_customers": json.dumps(existing)
                    }
                },
                "spec": {
                    "rbac": {
                        "policy": {
                            "matchExpressions": []
                        }
                    }
                }
            }
        
        mock_k8s_service.custom_api.get_namespaced_custom_object = mock_get
        
        # Simulate 5 concurrent calls
        threads = []
        for i in range(5):
            t = threading.Thread(
                target=mock_k8s_service.grant_customer_access,
                args=("test-agent", f"concurrent-customer-{i}", "kagent")
            )
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Verify all 5 patch calls were made
        assert len(patch_calls) == 5
        
        # Verify each patch has the merge-patch structure
        for patch_body in patch_calls:
            assert "metadata" in patch_body
            assert "spec" in patch_body
    
    def test_merge_patch_body_structure(self, mock_k8s_service, mock_policy_no_customers):
        """Test that merge patch body has correct structure"""
        mock_k8s_service.custom_api.get_namespaced_custom_object.return_value = mock_policy_no_customers
        mock_k8s_service.custom_api.patch_namespaced_custom_object.return_value = {}
        
        mock_k8s_service.grant_customer_access(
            agent_type="test-agent",
            customer_id="new-customer",
            agent_namespace="kagent"
        )
        
        patch_call = mock_k8s_service.custom_api.patch_namespaced_custom_object.call_args
        patch_body = patch_call.args[6]
        
        # Verify structure
        assert patch_body["metadata"]["annotations"]["allowed_customers"] == json.dumps(["new-customer"])
        assert "matchExpressions" in patch_body["spec"]["rbac"]["policy"]
        assert len(patch_body["spec"]["rbac"]["policy"]["matchExpressions"]) == 1

class TestIntegrationScenarios:
    """Integration tests for complete workflows"""
    
    def test_hire_then_delete_workflow(self, mock_k8s_service):
        """Test: Hire agent, try delete (should fail), unhire, delete (should succeed)"""
        # Setup
        policy_state = {"customers": []}
        
        def mock_get(*args, **kwargs):
            return {
                "metadata": {
                    "annotations": {
                        "allowed_customers": json.dumps(policy_state["customers"])
                    }
                },
                "spec": {
                    "rbac": {
                        "policy": {
                            "matchExpressions": []
                        }
                    }
                }
            }
        
        def mock_patch(*args, **kwargs):
            # Update state from patch body
            body = kwargs.get("body") or args[6]
            new_customers_str = body["metadata"]["annotations"]["allowed_customers"]
            policy_state["customers"] = json.loads(new_customers_str)
            return {}
        
        mock_k8s_service.custom_api.get_namespaced_custom_object = mock_get
        mock_k8s_service.custom_api.patch_namespaced_custom_object = mock_patch
        mock_k8s_service.custom_api.delete_namespaced_custom_object = Mock(return_value={})
        
        # Step 1: Hire agent (grant access)
        mock_k8s_service.grant_customer_access("test-agent", "customer-1", "kagent")
        assert len(policy_state["customers"]) == 1
        
        # Step 2: Try to delete (should fail)
        with pytest.raises(Exception) as exc_info:
            mock_k8s_service.delete_agent_route("test-agent", "kagent")
        assert "Revoke access first" in str(exc_info.value)
        
        # Step 3: Unhire agent (revoke access)
        mock_k8s_service.revoke_customer_access("test-agent", "customer-1", "kagent")
        assert len(policy_state["customers"]) == 0
        
        # Step 4: Delete (should succeed)
        result = mock_k8s_service.delete_agent_route("test-agent", "kagent")
        assert result is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
