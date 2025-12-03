"""
Security Tests for Context Isolation
These tests MUST pass before any deployment
"""
import pytest
from app.agents.base_agent import AgentContext, ScopedMemory, BaseAgent
from typing import Dict, Any


class MockVectorDB:
    """Mock vector database for testing"""
    
    def __init__(self):
        self.data = []
        self.search_calls = []
    
    def search(self, query: str, filter: Dict[str, Any], top_k: int = 5):
        """Mock search - records calls for verification"""
        self.search_calls.append({
            "query": query,
            "filter": filter,
            "top_k": top_k
        })
        
        # Return filtered data
        return [
            item for item in self.data
            if all(item.get(k) == v for k, v in filter.items())
        ][:top_k]
    
    def add(self, data: Dict[str, Any]):
        """Mock add"""
        self.data.append(data)
        return f"id-{len(self.data)}"
    
    def query(self, filter: Dict[str, Any], order_by: str, limit: int):
        """Mock query"""
        results = [
            item for item in self.data
            if all(item.get(k) == v for k, v in filter.items())
        ]
        return results[:limit]


class TestAgentContext:
    """Test AgentContext immutability"""
    
    def test_context_creation(self):
        """Test that context can be created with valid data"""
        context = AgentContext(
            customer_id="customer-123",
            user_id="user-456",
            permissions=["read", "write"]
        )
        
        assert context.customer_id == "customer-123"
        assert context.user_id == "user-456"
        assert context.permissions == ("read", "write")
    
    def test_context_immutability(self):
        """CRITICAL: Test that context cannot be modified"""
        context = AgentContext(
            customer_id="customer-123",
            user_id="user-456",
            permissions=["read"]
        )
        
        # Attempt to modify should raise AttributeError
        with pytest.raises(AttributeError):
            context.customer_id = "customer-999"
        
        with pytest.raises(AttributeError):
            context._customer_id = "customer-999"
    
    def test_has_permission(self):
        """Test permission checking"""
        context = AgentContext(
            customer_id="customer-123",
            user_id="user-456",
            permissions=["read", "write"]
        )
        
        assert context.has_permission("read") == True
        assert context.has_permission("write") == True
        assert context.has_permission("delete") == False


class TestScopedMemory:
    """Test ScopedMemory enforcement"""
    
    def test_memory_scoping(self):
        """CRITICAL: Test that memory is scoped to customer"""
        mock_db = MockVectorDB()
        
        # Add data for different customers
        mock_db.add({"customer_id": "customer-a", "content": "Secret A"})
        mock_db.add({"customer_id": "customer-b", "content": "Secret B"})
        
        # Create scoped memory for customer-a
        memory_a = ScopedMemory(mock_db, "customer-a")
        
        # Search should only return customer-a's data
        results = memory_a.search("secret")
        
        assert len(results) == 1
        assert results[0]["customer_id"] == "customer-a"
        assert results[0]["content"] == "Secret A"
    
    def test_memory_filter_enforcement(self):
        """CRITICAL: Test that customer filter is always applied"""
        mock_db = MockVectorDB()
        memory = ScopedMemory(mock_db, "customer-123")
        
        # Perform search
        memory.search("test query")
        
        # Verify filter was applied
        assert len(mock_db.search_calls) == 1
        call = mock_db.search_calls[0]
        assert call["filter"]["customer_id"] == "customer-123"
    
    def test_memory_add_auto_scoping(self):
        """Test that added memories are automatically scoped"""
        mock_db = MockVectorDB()
        memory = ScopedMemory(mock_db, "customer-123")
        
        # Add memory
        memory.add("Test content", {"key": "value"})
        
        # Verify customer_id was injected
        assert len(mock_db.data) == 1
        assert mock_db.data[0]["customer_id"] == "customer-123"
        assert mock_db.data[0]["content"] == "Test content"


class TestBaseAgent:
    """Test BaseAgent context enforcement"""
    
    def test_agent_requires_context(self):
        """CRITICAL: Test that agents reject requests without context"""
        
        class TestAgent(BaseAgent):
            def _execute(self, task, context, memory, tools):
                return {"result": "success"}
        
        agent = TestAgent("test-agent", "Test Agent")
        
        # Should raise TypeError if context is not AgentContext
        with pytest.raises(TypeError):
            agent.process_task(
                {"message": "test"},
                {"customer_id": "customer-123"}  # Dict, not AgentContext
            )
    
    def test_agent_context_validation(self):
        """Test that agents validate context type"""
        
        class TestAgent(BaseAgent):
            def _execute(self, task, context, memory, tools):
                return {"result": "success"}
        
        agent = TestAgent("test-agent", "Test Agent")
        
        # Valid context should work
        context = AgentContext(
            customer_id="customer-123",
            user_id="user-456",
            permissions=["read"]
        )
        
        # This should not raise (but will fail on missing dependencies)
        # We're just testing the context validation part
        try:
            agent.process_task({"message": "test"}, context)
        except Exception as e:
            # Expected to fail on missing vector_db, but NOT on context validation
            assert "context must be AgentContext" not in str(e)


@pytest.mark.security
class TestCrossCustomerIsolation:
    """
    CRITICAL SECURITY TESTS
    These tests verify that Customer B cannot access Customer A's data
    """
    
    def test_cross_customer_memory_access(self):
        """
        CRITICAL: Ensure Customer B cannot access Customer A's memories
        
        This is the most important security test.
        """
        mock_db = MockVectorDB()
        
        # Customer A stores sensitive data
        memory_a = ScopedMemory(mock_db, "customer-a")
        memory_a.add("Our revenue is $5,000,000 ARR")
        memory_a.add("Our secret project: Project Phoenix")
        
        # Customer B tries to access memories
        memory_b = ScopedMemory(mock_db, "customer-b")
        results = memory_b.search("revenue")
        
        # MUST NOT return Customer A's data
        assert len(results) == 0
        
        # Customer B adds their own data
        memory_b.add("Our revenue is $100,000 ARR")
        
        # Customer B should only see their own data
        results_b = memory_b.search("revenue")
        assert len(results_b) == 1
        assert results_b[0]["customer_id"] == "customer-b"
        assert "$100,000" in results_b[0]["content"]
        assert "$5,000,000" not in results_b[0]["content"]
    
    def test_context_cannot_be_tampered(self):
        """
        CRITICAL: Test that context cannot be modified to access other customers
        """
        context = AgentContext(
            customer_id="customer-b",
            user_id="user-b",
            permissions=["read"]
        )
        
        # Attacker tries to change customer_id
        with pytest.raises(AttributeError):
            context._customer_id = "customer-a"
        
        # Context should still be customer-b
        assert context.customer_id == "customer-b"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "security"])
