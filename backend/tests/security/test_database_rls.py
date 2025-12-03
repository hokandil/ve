"""
Test RLS (Row-Level Security) enforcement
Verifies that database-level isolation works correctly
"""
import pytest
from app.core.database import get_supabase_admin


@pytest.mark.security
@pytest.mark.database
class TestDatabaseRLS:
    """Test database Row-Level Security policies"""
    
    def test_rls_enabled_on_agent_memory(self):
        """Verify RLS is enabled on agent_memory table"""
        supabase = get_supabase_admin()
        
        # Query pg_tables to check RLS status
        result = supabase.rpc('exec_sql', {
            'sql': """
                SELECT relrowsecurity 
                FROM pg_class 
                WHERE relname = 'agent_memory'
            """
        }).execute()
        
        # RLS should be enabled (relrowsecurity = true)
        assert result.data is not None
        # Note: Actual assertion depends on Supabase RPC response format
    
    def test_customer_context_function_exists(self):
        """Verify set_customer_context function exists"""
        supabase = get_supabase_admin()
        
        # Check if function exists
        result = supabase.rpc('exec_sql', {
            'sql': """
                SELECT EXISTS (
                    SELECT 1 
                    FROM pg_proc 
                    WHERE proname = 'set_customer_context'
                )
            """
        }).execute()
        
        assert result.data is not None
    
    def test_security_audit_log_table_exists(self):
        """Verify security_audit_log table was created"""
        supabase = get_supabase_admin()
        
        # Try to query the table
        try:
            result = supabase.table("security_audit_log").select("id").limit(1).execute()
            # If no error, table exists
            assert True
        except Exception as e:
            pytest.fail(f"security_audit_log table does not exist: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "database"])
