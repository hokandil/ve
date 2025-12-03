"""
Test suite for orchestrator escalation logic
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.orchestrator import route_request_to_orchestrator, build_escalation_chain

@pytest.fixture
def mock_ves():
    """Mock VE data with different seniority levels"""
    return [
        {
            "id": "manager-1",
            "persona_name": "Marketing Manager",
            "agent_type": "marketing-manager",
            "ve_details": {
                "role": "Marketing Manager",
                "department": "Marketing",
                "seniority_level": "manager"
            }
        },
        {
            "id": "senior-1",
            "persona_name": "Senior Developer",
            "agent_type": "senior-dev",
            "ve_details": {
                "role": "Senior Developer",
                "department": "Engineering",
                "seniority_level": "senior"
            }
        },
        {
            "id": "junior-1",
            "persona_name": "Junior Analyst",
            "agent_type": "junior-analyst",
            "ve_details": {
                "role": "Junior Analyst",
                "department": "Analytics",
                "seniority_level": "junior"
            }
        }
    ]

class TestEscalationChain:
    """Test escalation chain building"""
    
    def test_build_escalation_chain_orders_by_seniority(self, mock_ves):
        """Test that escalation chain is ordered manager -> senior -> junior"""
        chain = build_escalation_chain(mock_ves)
        
        assert len(chain) == 3
        assert chain[0]["ve_details"]["seniority_level"] == "manager"
        assert chain[1]["ve_details"]["seniority_level"] == "senior"
        assert chain[2]["ve_details"]["seniority_level"] == "junior"
    
    def test_build_escalation_chain_excludes_failed_ve(self, mock_ves):
        """Test that failed VE is excluded from chain"""
        chain = build_escalation_chain(mock_ves, failed_ve_id="manager-1")
        
        assert len(chain) == 2
        assert all(ve["id"] != "manager-1" for ve in chain)
        assert chain[0]["ve_details"]["seniority_level"] == "senior"
    
    def test_build_escalation_chain_empty_list(self):
        """Test with empty VE list"""
        chain = build_escalation_chain([])
        assert len(chain) == 0

@pytest.mark.asyncio
class TestOrchestratorEscalation:
    """Test orchestrator escalation logic"""
    
    async def test_successful_first_attempt_no_escalation(self, mock_ves):
        """Test that successful first attempt doesn't trigger escalation"""
        with patch('app.services.orchestrator.get_supabase_admin') as mock_supabase, \
             patch('app.services.orchestrator.get_agent_gateway_service') as mock_gateway:
            
            # Mock database responses
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_ves
            mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = Mock()
            mock_supabase.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
            
            # Mock successful agent response
            mock_gateway.return_value.invoke_orchestrator = AsyncMock(return_value={
                "routed_to_ve": "manager-1"
            })
            mock_gateway.return_value.invoke_agent = AsyncMock(return_value={
                "message": "Task acknowledged and started"
            })
            
            result = await route_request_to_orchestrator(
                customer_id="test-customer",
                task_description="Test task",
                context={}
            )
            
            assert result["status"] == "routed"
            assert result["escalation_attempts"] == 0
            assert len(result["escalation_chain"]) == 1
            assert result["final_assigned_ve_id"] == "manager-1"
    
    async def test_escalation_after_first_failure(self, mock_ves):
        """Test that failure triggers escalation to next senior VE"""
        with patch('app.services.orchestrator.get_supabase_admin') as mock_supabase, \
             patch('app.services.orchestrator.get_agent_gateway_service') as mock_gateway:
            
            # Mock database responses
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_ves
            mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = Mock()
            mock_supabase.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
            
            # Mock orchestrator response
            mock_gateway.return_value.invoke_orchestrator = AsyncMock(return_value={
                "routed_to_ve": "manager-1"
            })
            
            # Mock agent failure on first attempt, success on second
            mock_gateway.return_value.invoke_agent = AsyncMock(
                side_effect=[
                    Exception("Agent timeout"),  # First attempt fails
                    {"message": "Task handled by escalated agent"}  # Second attempt succeeds
                ]
            )
            
            result = await route_request_to_orchestrator(
                customer_id="test-customer",
                task_description="Test task",
                context={}
            )
            
            assert result["escalation_attempts"] == 1
            assert len(result["escalation_chain"]) == 2
            assert result["escalation_log"][0]["status"] == "failed"
            assert result["escalation_log"][1]["status"] == "success"
    
    async def test_all_attempts_exhausted(self, mock_ves):
        """Test that all 3 attempts failing marks task as failed"""
        with patch('app.services.orchestrator.get_supabase_admin') as mock_supabase, \
             patch('app.services.orchestrator.get_agent_gateway_service') as mock_gateway:
            
            # Mock database responses
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_ves
            mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = Mock()
            mock_supabase.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
            
            # Mock orchestrator response
            mock_gateway.return_value.invoke_orchestrator = AsyncMock(return_value={
                "routed_to_ve": "manager-1"
            })
            
            # Mock all agent invocations to fail
            mock_gateway.return_value.invoke_agent = AsyncMock(
                side_effect=Exception("Agent unavailable")
            )
            
            result = await route_request_to_orchestrator(
                customer_id="test-customer",
                task_description="Test task",
                context={}
            )
            
            assert result["status"] == "failed_after_escalations"
            assert result["escalation_attempts"] == 3
            assert len(result["escalation_log"]) == 3
            assert all(log["status"] == "failed" for log in result["escalation_log"])
    
    async def test_escalation_log_contains_timestamps(self, mock_ves):
        """Test that escalation log includes timestamps"""
        with patch('app.services.orchestrator.get_supabase_admin') as mock_supabase, \
             patch('app.services.orchestrator.get_agent_gateway_service') as mock_gateway:
            
            # Mock database responses
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_ves
            mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = Mock()
            mock_supabase.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
            
            # Mock orchestrator and agent
            mock_gateway.return_value.invoke_orchestrator = AsyncMock(return_value={
                "routed_to_ve": "manager-1"
            })
            mock_gateway.return_value.invoke_agent = AsyncMock(return_value={
                "message": "Success"
            })
            
            result = await route_request_to_orchestrator(
                customer_id="test-customer",
                task_description="Test task",
                context={}
            )
            
            assert len(result["escalation_log"]) > 0
            for log_entry in result["escalation_log"]:
                assert "timestamp" in log_entry
                assert "attempt" in log_entry
                assert "ve_id" in log_entry
                assert "status" in log_entry

@pytest.mark.asyncio
class TestRouteTaskToVE:
    """Test route_task_to_ve function (manual routing)"""
    
    async def test_route_task_with_valid_ve_id(self, mock_ves):
        """Test routing task to valid VE updates status to in_progress"""
        from app.services.orchestrator import route_task_to_ve
        
        with patch('app.services.orchestrator.get_supabase_admin') as mock_supabase, \
             patch('app.services.orchestrator.get_agent_gateway_service') as mock_gateway:
            
            # Mock database responses
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [mock_ves[0]]
            mock_supabase.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
            mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = Mock()
            
            # Mock successful agent response
            mock_gateway.return_value.invoke_agent = AsyncMock(return_value={
                "message": "Task acknowledged"
            })
            
            result = await route_task_to_ve(
                customer_id="test-customer",
                task_id="test-task",
                ve_id="manager-1",
                task_description="Test task description"
            )
            
            # Verify success
            assert result is True
            
            # Verify task was updated to in_progress
            mock_supabase.return_value.table.return_value.update.assert_called()
            update_call_args = mock_supabase.return_value.table.return_value.update.call_args
            assert update_call_args[0][0]["status"] == "in_progress"
            assert update_call_args[0][0]["assigned_to_ve"] == "manager-1"
    
    async def test_route_task_with_invalid_ve_id(self):
        """Test routing task to invalid VE returns False with error log"""
        from app.services.orchestrator import route_task_to_ve
        
        with patch('app.services.orchestrator.get_supabase_admin') as mock_supabase, \
             patch('app.services.orchestrator.logger') as mock_logger:
            
            # Mock empty response (VE not found)
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
            
            result = await route_task_to_ve(
                customer_id="test-customer",
                task_id="test-task",
                ve_id="invalid-ve-id",
                task_description="Test task"
            )
            
            # Verify failure
            assert result is False
            
            # Verify error was logged
            mock_logger.error.assert_called()
            error_message = mock_logger.error.call_args[0][0]
            assert "not found" in error_message.lower()
            assert "invalid-ve-id" in error_message
    
    async def test_route_task_agent_invocation_failure(self, mock_ves):
        """Test that agent invocation failure marks task as failed"""
        from app.services.orchestrator import route_task_to_ve
        
        with patch('app.services.orchestrator.get_supabase_admin') as mock_supabase, \
             patch('app.services.orchestrator.get_agent_gateway_service') as mock_gateway:
            
            # Mock database responses
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [mock_ves[0]]
            mock_supabase.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
            
            # Mock agent invocation failure
            mock_gateway.return_value.invoke_agent = AsyncMock(
                side_effect=Exception("Agent timeout")
            )
            
            result = await route_task_to_ve(
                customer_id="test-customer",
                task_id="test-task",
                ve_id="manager-1",
                task_description="Test task"
            )
            
            # Verify failure
            assert result is False
            
            # Verify task was marked as failed
            update_calls = [call[0][0] for call in mock_supabase.return_value.table.return_value.update.call_args_list]
            failed_update = next((call for call in update_calls if call.get("status") == "failed"), None)
            assert failed_update is not None
            assert "metadata" in failed_update
            assert "failure_reason" in failed_update["metadata"]
    
    async def test_route_task_missing_agent_type(self, mock_ves):
        """Test that VE without agent_type returns False"""
        from app.services.orchestrator import route_task_to_ve
        
        with patch('app.services.orchestrator.get_supabase_admin') as mock_supabase:
            
            # Mock VE without agent_type
            ve_without_type = mock_ves[0].copy()
            ve_without_type["agent_type"] = None
            
            mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [ve_without_type]
            
            result = await route_task_to_ve(
                customer_id="test-customer",
                task_id="test-task",
                ve_id="manager-1",
                task_description="Test task"
            )
            
            # Verify failure
            assert result is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

