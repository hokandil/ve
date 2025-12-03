"""
Database connection and session management
"""
from supabase import create_client, Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Supabase client (for auth and real-time)
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_ANON_KEY
)

# Supabase admin client (for service operations)
supabase_admin: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY
)

def get_supabase() -> Client:
    """Get Supabase client"""
    return supabase

def get_supabase_admin() -> Client:
    """Get Supabase admin client"""
    return supabase_admin
