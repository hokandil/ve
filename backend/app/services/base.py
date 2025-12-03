from typing import Optional
from supabase import Client

class BaseService:
    """Base service class with Supabase client injection"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Centralized error handling"""
        print(f"Error in {context}: {str(error)}")
        raise error
