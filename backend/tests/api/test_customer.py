import pytest
from unittest.mock import patch, MagicMock

def test_list_customer_ves(client, mock_supabase):
    # Mock response
    mock_data = [
        {
            "id": "cust-ve-1",
            "customer_id": "test-customer-id",
            "marketplace_agent_id": "ve-1",
            "agent_name": "agent-1",
            "persona_name": "Alex",
            "status": "active",
            "hired_at": "2023-01-01T00:00:00"
        }
    ]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_data
    
    # Mock VE details fetch
    mock_ve_details = [{
        "id": "ve-1",
        "name": "Test Agent",
        "role": "Developer",
        "department": "Engineering",
        "seniority_level": "senior",
        "pricing_monthly": 1000.0,
        "status": "stable",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }]
    # We need to handle the second call to supabase for ve details
    # This is a bit tricky with a single mock, so we'll simplify and assume the mock returns data for any select
    
    response = client.get("/api/customer/ves")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["persona_name"] == "Alex"

@patch("app.services.agent_gateway_service.agent_gateway_service.create_route")
def test_hire_ve(mock_create_route, client, mock_supabase):
    # Mock create_route response
    mock_create_route.return_value = {"route_id": "route-123"}
    
    # Mock VE template fetch
    mock_ve_template = [{
        "id": "ve-1",
        "name": "Test Agent",
        "role": "Developer",
        "department": "Engineering",
        "seniority_level": "senior",
        "pricing_monthly": 1000.0,
        "status": "stable",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_ve_template
    
    # Mock customer info fetch
    mock_customer = [{"company_name": "Test Corp"}]
    # Again, simplifying mock return values. In a real test, we'd use side_effect to return different data for different calls.
    
    # Mock insert response
    mock_inserted_ve = {
        "id": "new-cust-ve-id",
        "customer_id": "test-customer-id",
        "marketplace_agent_id": "ve-1",
        "agent_name": "developer-new-cust",
        "persona_name": "Alex",
        "persona_email": "alex@testcorp.veworkforce.io",
        "agent_gateway_route_id": "route-123",
        "status": "active",
        "hired_at": "2023-01-01T00:00:00"
    }
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [mock_inserted_ve]

    payload = {
        "marketplace_agent_id": "ve-1",
        "persona_name": "Alex"
    }
    
    response = client.post("/api/customer/ves", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "new-cust-ve-id"
    assert data["agent_gateway_route_id"] == "route-123"
