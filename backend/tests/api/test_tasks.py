import pytest
from unittest.mock import patch, MagicMock, AsyncMock

@patch("app.api.tasks.get_supabase_admin")
def test_create_task_simple(mock_get_supabase, client, mock_supabase):
    mock_get_supabase.return_value = mock_supabase
    
    # Mock insert response
    mock_task = {
        "id": "task-1",
        "customer_id": "test-customer-id",
        "title": "Test Task",
        "description": "Do something",
        "status": "pending",
        "priority": "medium",
        "created_at": "2023-01-01T00:00:00"
    }
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [mock_task]
    
    payload = {
        "title": "Test Task",
        "description": "Do something",
        "priority": "medium"
    }
    
    response = client.post("/api/tasks", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "task-1"
    assert data["title"] == "Test Task"

@patch("app.api.tasks.get_supabase_admin")
@patch("app.services.agent_gateway_service.agent_gateway_service.invoke_agent")
def test_create_task_assigned_to_ve(mock_invoke_agent, mock_get_supabase, client, mock_supabase):
    mock_get_supabase.return_value = mock_supabase
    
    # Mock insert response for task
    mock_task = {
        "id": "task-1",
        "customer_id": "test-customer-id",
        "title": "VE Task",
        "description": "Do something for me",
        "assigned_to_ve": "ve-123",
        "status": "pending",
        "priority": "high",
        "created_at": "2023-01-01T00:00:00"
    }
    
    # Mock VE details fetch
    mock_ve = {
        "id": "ve-123",
        "agent_type": "marketing-manager",
        "persona_name": "Alex"
    }
    
    # Configure mocks for sequential calls
    def table_side_effect(table_name):
        mock_table = MagicMock()
        if table_name == "tasks":
            mock_table.insert.return_value.execute.return_value.data = [mock_task]
        elif table_name == "customer_ves":
            mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value.data = mock_ve
        elif table_name == "task_comments":
            mock_table.insert.return_value.execute.return_value.data = [{"id": "comment-1"}]
        return mock_table
        
    mock_supabase.table.side_effect = table_side_effect
    
    # Mock agent invocation response
    mock_invoke_agent.return_value = {
        "message": "I'll get right on that!",
        "agent_type": "marketing-manager"
    }
    
    payload = {
        "title": "VE Task",
        "description": "Do something for me",
        "priority": "high",
        "assigned_to_ve": "ve-123"
    }
    
    response = client.post("/api/tasks", json=payload)
    
    assert response.status_code == 200
    
    # Verify agent was invoked
    mock_invoke_agent.assert_called_once()
    call_args = mock_invoke_agent.call_args
    assert call_args.kwargs["agent_type"] == "marketing-manager"
    assert "New Task Assigned" in call_args.kwargs["message"]
