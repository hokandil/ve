import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_supabase_admin
from app.core.security import get_current_user, get_current_customer_id

# Mock User Data
MOCK_USER_ID = "test-user-id"
MOCK_CUSTOMER_ID = "test-customer-id"

class MockUser:
    def __init__(self):
        self.id = MOCK_USER_ID
        self.email = "test@example.com"
        self.role = "customer"

@pytest.fixture
def mock_supabase():
    mock = MagicMock()
    # Mock table().select().eq().execute() chain
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    mock.table.return_value.insert.return_value.execute.return_value.data = [{"id": "new-id"}]
    mock.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{"id": "updated-id"}]
    mock.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = [{"id": "deleted-id"}]
    return mock

@pytest.fixture
def client(mock_supabase):
    # Override dependencies
    app.dependency_overrides[get_supabase_admin] = lambda: mock_supabase
    app.dependency_overrides[get_current_user] = lambda: {"id": MOCK_USER_ID, "email": "test@example.com", "role": "customer"}
    app.dependency_overrides[get_current_customer_id] = lambda: MOCK_CUSTOMER_ID
    
    with TestClient(app) as c:
        yield c
    
    # Clean up
    app.dependency_overrides.clear()
