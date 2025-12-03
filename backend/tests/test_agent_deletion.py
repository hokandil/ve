import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_supabase_admin

# Mock data
MOCK_VE_ID = "ve-123"
MOCK_AGENT_TYPE = "wellness"

@pytest.fixture
def mock_supabase_admin():
    mock = MagicMock()
    return mock

@pytest.fixture
def mock_gateway_service():
    # Patch where it is defined, not where it is imported (since it is imported inside function)
    with patch("app.services.gateway_config_service.get_gateway_config_service") as mock:
        service = MagicMock()
        mock.return_value = service
        yield service

@pytest.fixture
def client(mock_supabase_admin):
    # Patch get_supabase_admin in the discovery module because it's called directly, not via Depends
    with patch("app.api.discovery.get_supabase_admin", return_value=mock_supabase_admin):
        with TestClient(app) as c:
            yield c

def test_delete_agent_with_active_customers_fails(client, mock_supabase_admin):
    """Test that deleting an agent with active customers returns 400"""
    
    def table_side_effect(table_name):
        mock_table = MagicMock()
        mock_response = MagicMock()
        
        if table_name == "virtual_employees":
            mock_response.data = [{"id": MOCK_VE_ID, "name": MOCK_AGENT_TYPE}]
            mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
        elif table_name == "customer_ves":
            # Simulate 2 active customers
            mock_response.data = [{"id": "c1"}, {"id": "c2"}]
            mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
            
        return mock_table
        
    mock_supabase_admin.table.side_effect = table_side_effect
    
    response = client.delete(f"/api/discovery/agents/{MOCK_VE_ID}")
    
    # Debug output if it fails
    if response.status_code != 400:
        print(f"Response: {response.json()}")
        
    assert response.status_code == 400
    assert "2 customer(s) are currently using it" in response.json()["detail"]

def test_delete_agent_success(client, mock_supabase_admin, mock_gateway_service):
    """Test that deleting an agent with no customers succeeds and cleans up resources"""
    
    def table_side_effect(table_name):
        mock_table = MagicMock()
        mock_response = MagicMock()
        
        if table_name == "virtual_employees":
            mock_response.data = [{"id": MOCK_VE_ID, "name": MOCK_AGENT_TYPE, "source_id": MOCK_AGENT_TYPE}]
            mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
            
            # For the delete call
            mock_table.delete.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": MOCK_VE_ID}])
            
        elif table_name == "customer_ves":
            # Simulate NO active customers
            mock_response.data = []
            mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
            
        return mock_table
        
    mock_supabase_admin.table.side_effect = table_side_effect
    mock_gateway_service.delete_agent_route.return_value = True
    
    response = client.delete(f"/api/discovery/agents/{MOCK_VE_ID}")
    
    if response.status_code != 200:
        print(f"Response: {response.json()}")
        
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify Gateway cleanup called
    mock_gateway_service.delete_agent_route.assert_called_once_with(MOCK_AGENT_TYPE)
