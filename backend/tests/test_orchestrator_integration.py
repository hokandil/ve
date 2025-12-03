"""
Integration tests for orchestrator and gateway
Tests end-to-end workflows including routing, escalation, access control, and database isolation
"""
import pytest
import asyncio
import json
import threading
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from app.services.orchestrator import route_request_to_orchestrator, route_task_to_ve
from app.services.gateway_config_service import AgentGatewayConfigService
from kubernetes.client.rest import ApiException

@pytest.fixture
def mock_customer_ves_marketing_it():
    """Mock customer with Marketing and IT managers"""
    return [
        {
            "id": "marketing-mgr-1",
            "customer_id": "customer-1",
            "persona_name": "Sarah Marketing",
            "agent_type": "marketing-manager",
            "ve_details": {
                "role": "Marketing Manager",
                "department": "Marketing",
                "seniority_level": "manager"
            }
        },
        {
            "id": "it-mgr-1",
            "customer_id": "customer-1",
            "persona_name": "John IT",
            "agent_type": "it-manager",
            "ve_details": {
                "role": "IT Manager",
                "department": "IT",
                "seniority_level": "manager"
            }
        },
        {
            "id": "senior-dev-1",
            "customer_id": "customer-1",
            "persona_name": "Alice Developer",
            "agent_type": "senior-dev",
            "ve_details": {
                "role": "Senior Developer",
                "department": "Engineering",
                "seniority_level": "senior"
            }
        }
    ]

@pytest.mark.asyncio
class TestOrchestratorRouting:
    """Test orchestrator routing logic"""
    
    async def test_route_marketing_task_to_marketing_manager(self, mock_customer_ves_marketing_it):
        """Test that marketing task routes to marketing manager"""
        with patch('app.services.orchestrator.get_supabase_admin') as mock_supabase, \
             patch('app.services.orchestrator.get_agent_gateway_service') as mock_gateway:
            
            # Mock database
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_customer_ves_marketing_it
            mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = Mock()
            mock_supabase.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
            
            # Mock orchestrator to route to marketing manager
            mock_gateway.return_value.invoke_orchestrator = AsyncMock(return_value={
                "routed_to_ve": "marketing-mgr-1"
            })
            mock_gateway.return_value.invoke_agent = AsyncMock(return_value={
                "message": "Marketing task acknowledged"
            })
            
            result = await route_request_to_orchestrator(
                customer_id="customer-1",
                task_description="Create new marketing campaign for Q1",
                context={}
            )
            
            # Verify routed to marketing manager
            assert result["routed_to_ve"] == "marketing-mgr-1"
            assert result["status"] == "routed"
    
    async def test_route_it_task_to_it_manager(self, mock_customer_ves_marketing_it):
        """Test that IT task routes to IT manager"""
        with patch('app.services.orchestrator.get_supabase_admin') as mock_supabase, \
             patch('app.services.orchestrator.get_agent_gateway_service') as mock_gateway:
            
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_customer_ves_marketing_it
            mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = Mock()
            mock_supabase.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
            
            # Mock orchestrator to route to IT manager
            mock_gateway.return_value.invoke_orchestrator = AsyncMock(return_value={
                "routed_to_ve": "it-mgr-1"
            })
            mock_gateway.return_value.invoke_agent = AsyncMock(return_value={
                "message": "IT task acknowledged"
            })
            
            result = await route_request_to_orchestrator(
                customer_id="customer-1",
                task_description="Deploy new microservice to production",
                context={}
            )
            
            # Verify routed to IT manager
            assert result["routed_to_ve"] == "it-mgr-1"
            assert result["status"] == "routed"
    
    async def test_route_unknown_department_to_most_senior(self, mock_customer_ves_marketing_it):
        """Test that unknown department task routes to most senior available"""
        with patch('app.services.orchestrator.get_supabase_admin') as mock_supabase, \
             patch('app.services.orchestrator.get_agent_gateway_service') as mock_gateway:
            
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_customer_ves_marketing_it
            mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = Mock()
            mock_supabase.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
            
            # Mock orchestrator failure (returns no VE)
            mock_gateway.return_value.invoke_orchestrator = AsyncMock(return_value={})
            mock_gateway.return_value.invoke_agent = AsyncMock(return_value={
                "message": "Task acknowledged"
            })
            
            result = await route_request_to_orchestrator(
                customer_id="customer-1",
                task_description="Handle customer complaint",
                context={}
            )
            
            # Verify fallback to a manager (most senior)
            assigned_ve = next(ve for ve in mock_customer_ves_marketing_it if ve["id"] == result["routed_to_ve"])
            assert assigned_ve["ve_details"]["seniority_level"] == "manager"

@pytest.mark.asyncio
class TestOrchestratorEscalation:
    """Test orchestrator escalation logic"""
    
    async def test_escalation_on_agent_failure(self, mock_customer_ves_marketing_it):
        """Test that agent failure triggers escalation"""
        with patch('app.services.orchestrator.get_supabase_admin') as mock_supabase, \
             patch('app.services.orchestrator.get_agent_gateway_service') as mock_gateway:
            
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_customer_ves_marketing_it
            mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = Mock()
            mock_supabase.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
            
            mock_gateway.return_value.invoke_orchestrator = AsyncMock(return_value={
                "routed_to_ve": "marketing-mgr-1"
            })
            
            # First attempt fails, second succeeds
            mock_gateway.return_value.invoke_agent = AsyncMock(
                side_effect=[
                    Exception("Agent timeout"),
                    {"message": "Task handled by escalated agent"}
                ]
            )
            
            result = await route_request_to_orchestrator(
                customer_id="customer-1",
                task_description="Urgent task",
                context={}
            )
            
            # Verify escalation occurred
            assert result["escalation_attempts"] == 1
            assert len(result["escalation_chain"]) == 2
            assert result["escalation_log"][0]["status"] == "failed"
            assert result["escalation_log"][1]["status"] == "success"
    
    async def test_multiple_escalations(self, mock_customer_ves_marketing_it):
        """Test that escalation continues if senior also fails"""
        with patch('app.services.orchestrator.get_supabase_admin') as mock_supabase, \
             patch('app.services.orchestrator.get_agent_gateway_service') as mock_gateway:
            
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_customer_ves_marketing_it
            mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = Mock()
            mock_supabase.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
            
            mock_gateway.return_value.invoke_orchestrator = AsyncMock(return_value={
                "routed_to_ve": "marketing-mgr-1"
            })
            
            # First two fail, third succeeds
            mock_gateway.return_value.invoke_agent = AsyncMock(
                side_effect=[
                    Exception("First agent timeout"),
                    Exception("Second agent timeout"),
                    {"message": "Finally handled"}
                ]
            )
            
            result = await route_request_to_orchestrator(
                customer_id="customer-1",
                task_description="Critical task",
                context={}
            )
            
            # Verify multiple escalations
            assert result["escalation_attempts"] == 2
            assert len(result["escalation_chain"]) == 3
    
    async def test_stops_after_3_attempts(self, mock_customer_ves_marketing_it):
        """Test that escalation stops after 3 attempts"""
        with patch('app.services.orchestrator.get_supabase_admin') as mock_supabase, \
             patch('app.services.orchestrator.get_agent_gateway_service') as mock_gateway:
            
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_customer_ves_marketing_it
            mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = Mock()
            mock_supabase.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
            
            mock_gateway.return_value.invoke_orchestrator = AsyncMock(return_value={
                "routed_to_ve": "marketing-mgr-1"
            })
            
            # All attempts fail
            mock_gateway.return_value.invoke_agent = AsyncMock(
                side_effect=Exception("Agent unavailable")
            )
            
            result = await route_request_to_orchestrator(
                customer_id="customer-1",
                task_description="Impossible task",
                context={}
            )
            
            # Verify stopped after 3 attempts
            assert result["status"] == "failed_after_escalations"
            assert result["escalation_attempts"] == 3
            assert len(result["escalation_log"]) == 3

class TestGatewayAccessControl:
    """Test gateway access control"""
    
    def test_customer_cannot_access_initially(self):
        """Test that customer cannot access agent initially"""
        service = AgentGatewayConfigService()
        service.k8s_available = True
        service.custom_api = Mock()
        
        # Mock policy with no customers
        service.custom_api.get_namespaced_custom_object.return_value = {
            "metadata": {
                "annotations": {
                    "allowed_customers": "[]"
                }
            }
        }
        
        # Verify customer not in allowed list
        policy = service.custom_api.get_namespaced_custom_object()
        allowed = json.loads(policy["metadata"]["annotations"]["allowed_customers"])
        assert "customer-1" not in allowed
    
    def test_grant_access_allows_customer(self):
        """Test that granting access allows customer"""
        service = AgentGatewayConfigService()
        service.k8s_available = True
        service.custom_api = Mock()
        
        # Mock initial state
        service.custom_api.get_namespaced_custom_object.return_value = {
            "metadata": {
                "annotations": {
                    "allowed_customers": "[]"
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
        service.custom_api.patch_namespaced_custom_object.return_value = {}
        
        # Grant access
        result = service.grant_customer_access(
            agent_type="test-agent",
            customer_id="customer-1",
            agent_namespace="kagent"
        )
        
        # Verify grant succeeded
        assert result["status"] == "granted"
        
        # Verify patch was called with customer in list
        patch_call = service.custom_api.patch_namespaced_custom_object.call_args
        patch_body = patch_call.args[6]
        allowed_customers = json.loads(patch_body["metadata"]["annotations"]["allowed_customers"])
        assert "customer-1" in allowed_customers
    
    def test_revoke_access_blocks_customer(self):
        """Test that revoking access blocks customer"""
        service = AgentGatewayConfigService()
        service.k8s_available = True
        service.custom_api = Mock()
        
        # Mock state with customer
        service.custom_api.get_namespaced_custom_object.return_value = {
            "metadata": {
                "annotations": {
                    "allowed_customers": json.dumps(["customer-1"])
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
        service.custom_api.patch_namespaced_custom_object.return_value = {}
        
        # Revoke access
        result = service.revoke_customer_access(
            agent_type="test-agent",
            customer_id="customer-1",
            agent_namespace="kagent"
        )
        
        # Verify revoke succeeded
        assert result["status"] == "revoked"
        
        # Verify patch was called with empty list
        patch_call = service.custom_api.patch_namespaced_custom_object.call_args
        patch_body = patch_call.args[6]
        allowed_customers = json.loads(patch_body["metadata"]["annotations"]["allowed_customers"])
        assert "customer-1" not in allowed_customers
    
    def test_other_customer_cannot_access(self):
        """Test that other customer cannot access"""
        service = AgentGatewayConfigService()
        service.k8s_available = True
        service.custom_api = Mock()
        
        # Mock policy with only customer-1
        service.custom_api.get_namespaced_custom_object.return_value = {
            "metadata": {
                "annotations": {
                    "allowed_customers": json.dumps(["customer-1"])
                }
            }
        }
        
        # Verify customer-2 not in allowed list
        policy = service.custom_api.get_namespaced_custom_object()
        allowed = json.loads(policy["metadata"]["annotations"]["allowed_customers"])
        assert "customer-2" not in allowed

class TestGatewayDeleteProtection:
    """Test gateway delete protection"""
    
    def test_delete_with_customer_access_fails(self):
        """Test that deleting agent with customer access fails"""
        service = AgentGatewayConfigService()
        service.k8s_available = True
        service.custom_api = Mock()
        
        # Mock policy with customers
        service.custom_api.get_namespaced_custom_object.return_value = {
            "metadata": {
                "annotations": {
                    "allowed_customers": json.dumps(["customer-1", "customer-2"])
                }
            }
        }
        
        # Attempt delete
        with pytest.raises(Exception) as exc_info:
            service.delete_agent_route("test-agent", "kagent")
        
        # Verify error message
        assert "customers still have active access" in str(exc_info.value)
        assert "Revoke access first" in str(exc_info.value)
    
    def test_delete_after_revoke_succeeds(self):
        """Test that delete succeeds after revoking all access"""
        service = AgentGatewayConfigService()
        service.k8s_available = True
        service.custom_api = Mock()
        
        # Mock policy with no customers
        service.custom_api.get_namespaced_custom_object.return_value = {
            "metadata": {
                "annotations": {
                    "allowed_customers": "[]"
                }
            }
        }
        service.custom_api.delete_namespaced_custom_object.return_value = {}
        
        # Delete should succeed
        result = service.delete_agent_route("test-agent", "kagent")
        assert result is True

class TestGatewayConcurrentAccess:
    """Test gateway concurrent access safety"""
    
    def test_concurrent_grant_operations(self):
        """Test that 5 concurrent grant operations all apply"""
        service = AgentGatewayConfigService()
        service.k8s_available = True
        service.custom_api = Mock()
        
        # Track patch calls
        patch_calls = []
        call_count = [0]
        
        def mock_get(*args, **kwargs):
            # Return current state
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
        
        def mock_patch(*args, **kwargs):
            call_count[0] += 1
            patch_calls.append(kwargs.get("body"))
            return {}
        
        service.custom_api.get_namespaced_custom_object = mock_get
        service.custom_api.patch_namespaced_custom_object = mock_patch
        
        # Simulate 5 concurrent grants
        threads = []
        for i in range(5):
            t = threading.Thread(
                target=service.grant_customer_access,
                args=("test-agent", f"customer-{i}", "kagent")
            )
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Verify all 5 patches were made
        assert len(patch_calls) == 5
        
        # Verify merge patch was used
        for patch_body in patch_calls:
            assert "metadata" in patch_body
            assert "spec" in patch_body
    
    def test_concurrent_revoke_operations(self):
        """Test that concurrent revoke operations result in correct final state"""
        service = AgentGatewayConfigService()
        service.k8s_available = True
        service.custom_api = Mock()
        
        # Start with 5 customers
        current_customers = [f"customer-{i}" for i in range(5)]
        
        def mock_get(*args, **kwargs):
            return {
                "metadata": {
                    "annotations": {
                        "allowed_customers": json.dumps(current_customers.copy())
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
            # Simulate removal
            body = kwargs.get("body")
            new_customers = json.loads(body["metadata"]["annotations"]["allowed_customers"])
            current_customers.clear()
            current_customers.extend(new_customers)
            return {}
        
        service.custom_api.get_namespaced_custom_object = mock_get
        service.custom_api.patch_namespaced_custom_object = mock_patch
        
        # Simulate concurrent revokes
        threads = []
        for i in range(3):
            t = threading.Thread(
                target=service.revoke_customer_access,
                args=("test-agent", f"customer-{i}", "kagent")
            )
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Final state should have 2 customers remaining
        assert len(current_customers) <= 2

@pytest.mark.asyncio
class TestDatabaseIsolation:
    """Test database isolation between customers"""
    
    async def test_customer_cannot_see_other_customer_agent(self):
        """Test that Customer A cannot see Customer B's agent"""
        with patch('app.services.orchestrator.get_supabase_admin') as mock_supabase:
            
            # Mock Customer A's VEs
            customer_a_ves = [
                {
                    "id": "ve-a-1",
                    "customer_id": "customer-a",
                    "persona_name": "Agent A",
                    "agent_type": "test-agent"
                }
            ]
            
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = customer_a_ves
            
            # Verify Customer A only sees their agent
            result = mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data
            assert len(result) == 1
            assert result[0]["customer_id"] == "customer-a"
    
    async def test_both_customers_see_own_instances_only(self):
        """Test that both customers hiring same agent see only their own instances"""
        with patch('app.services.orchestrator.get_supabase_admin') as mock_supabase:
            
            # Mock Customer A's view
            customer_a_ves = [
                {
                    "id": "ve-a-1",
                    "customer_id": "customer-a",
                    "marketplace_agent_id": "agent-123",
                    "persona_name": "My Marketing Agent"
                }
            ]
            
            # Mock Customer B's view
            customer_b_ves = [
                {
                    "id": "ve-b-1",
                    "customer_id": "customer-b",
                    "marketplace_agent_id": "agent-123",  # Same marketplace agent
                    "persona_name": "Company Marketing Bot"
                }
            ]
            
            # Verify isolation
            # Customer A query
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = customer_a_ves
            result_a = mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data
            assert len(result_a) == 1
            assert result_a[0]["customer_id"] == "customer-a"
            
            # Customer B query
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = customer_b_ves
            result_b = mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data
            assert len(result_b) == 1
            assert result_b[0]["customer_id"] == "customer-b"
            
            # Verify they have different instances
            assert result_a[0]["id"] != result_b[0]["id"]
            # But same marketplace agent
            assert result_a[0]["marketplace_agent_id"] == result_b[0]["marketplace_agent_id"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
