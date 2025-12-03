import pytest
from unittest.mock import MagicMock

def test_list_marketplace_ves(client, mock_supabase):
    # Mock response
    mock_data = [
        {
            "id": "ve-1",
            "name": "Test Agent",
            "role": "Developer",
            "department": "Engineering",
            "seniority_level": "senior",
            "pricing_monthly": 1000.0,
            "status": "stable",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
    ]
    mock_supabase.table.return_value.select.return_value.range.return_value.execute.return_value.data = mock_data
    mock_supabase.table.return_value.select.return_value.range.return_value.execute.return_value.count = 1

    response = client.get("/api/marketplace/ves")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Test Agent"

def test_create_marketplace_ve(client, mock_supabase):
    # Mock response
    mock_ve = {
        "id": "new-ve-id",
        "name": "New Agent",
        "role": "Designer",
        "department": "Design",
        "seniority_level": "junior",
        "pricing_monthly": 500.0,
        "status": "beta",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [mock_ve]

    payload = {
        "name": "New Agent",
        "role": "Designer",
        "department": "Design",
        "seniority_level": "junior",
        "pricing_monthly": 500.0,
        "description": "A test agent"
    }
    
    response = client.post("/api/marketplace/ves", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "new-ve-id"
    assert data["name"] == "New Agent"

def test_update_marketplace_metadata(client, mock_supabase):
    # Mock check response (VE exists)
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"id": "ve-1"}]
    
    # Mock update response
    mock_updated_ve = {
        "id": "ve-1",
        "name": "Test Agent",
        "role": "Developer",
        "department": "Engineering",
        "seniority_level": "senior",
        "pricing_monthly": 1200.0, # Updated
        "status": "stable",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-02T00:00:00"
    }
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [mock_updated_ve]

    payload = {
        "pricing_monthly": 1200.0,
        "tags": ["python", "fastapi"]
    }
    
    response = client.put("/api/marketplace/admin/marketplace/agents/ve-1", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["pricing_monthly"] == 1200.0
