import pytest
from unittest.mock import patch

def test_send_message(client, mock_supabase):
    # Mock insert response
    mock_msg = {
        "id": "msg-1",
        "customer_id": "test-customer-id",
        "to_ve_id": "ve-1",
        "subject": "Hello",
        "content": "Hi there",
        "message_type": "email",
        "read": False,
        "created_at": "2023-01-01T00:00:00",
        "from_type": "customer",
        "to_type": "ve"
    }
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [mock_msg]

    payload = {
        "to_ve_id": "ve-1",
        "subject": "Hello",
        "content": "Hi there",
        "message_type": "email"
    }
    
    response = client.post("/api/messages/send", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "msg-1"
    assert data["content"] == "Hi there"

@patch("asyncio.sleep") # Mock sleep to speed up test
def test_chat_with_ve(mock_sleep, client, mock_supabase):
    # Mock VE details
    mock_ve = [{
        "id": "ve-1",
        "agent_name": "agent-1",
        "persona_name": "Alex",
        "status": "active"
    }]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_ve
    
    # Mock message inserts (user msg and agent response)
    mock_user_msg = {
        "id": "msg-1",
        "customer_id": "test-customer-id",
        "to_ve_id": "ve-1",
        "subject": "Chat",
        "content": "Hello",
        "message_type": "chat",
        "from_type": "customer",
        "created_at": "2023-01-01T00:00:00"
    }
    mock_agent_msg = {
        "id": "msg-2",
        "customer_id": "test-customer-id",
        "from_ve_id": "ve-1",
        "subject": "Re: Chat",
        "content": "I received your message...",
        "message_type": "chat",
        "from_type": "ve",
        "created_at": "2023-01-01T00:00:01"
    }
    
    # We need to return different values for sequential calls to insert
    # This is complex with a single mock object chain, but for this test we can just ensure it returns *something* compatible
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [mock_user_msg] 
    
    payload = {
        "content": "Hello",
        "subject": "Chat"
    }
    
    response = client.post("/api/messages/ves/ve-1/chat", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "user_message" in data
    assert "agent_response" in data
