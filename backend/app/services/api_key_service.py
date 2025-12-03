"""
API Key Service
Manages API keys for agent authentication
"""
import logging
import secrets
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime
from app.core.database import get_supabase_admin

logger = logging.getLogger(__name__)


class APIKeyService:
    """Service for managing API keys for agent authentication"""
    
    def __init__(self):
        self.supabase = get_supabase_admin()
    
    def _hash_key(self, api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    async def create_api_key(
        self,
        customer_id: str,
        name: str,
        key_type: str = "agent",  # "agent" or "service"
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new API key
        Returns the plain key (only shown once) and key info
        """
        try:
            # Generate secure random key
            plain_key = f"vek_{secrets.token_urlsafe(32)}"
            key_hash = self._hash_key(plain_key)
            
            # Store in database
            data = {
                "customer_id": customer_id,
                "name": name,
                "key_hash": key_hash,
                "key_type": key_type,
                "metadata": metadata or {},
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "last_used_at": None
            }
            
            response = self.supabase.table("api_keys").insert(data).execute()
            
            if not response.data:
                raise Exception("Failed to create API key")
            
            result = response.data[0]
            result["plain_key"] = plain_key  # Only returned once
            
            logger.info(f"Created API key '{name}' for customer {customer_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
            raise
    
    async def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Verify API key and return associated customer info
        Returns None if invalid
        """
        try:
            key_hash = self._hash_key(api_key)
            
            # Look up key
            response = self.supabase.table("api_keys")\
                .select("*")\
                .eq("key_hash", key_hash)\
                .eq("is_active", True)\
                .execute()
            
            if not response.data:
                return None
            
            key_info = response.data[0]
            
            # Update last used timestamp
            self.supabase.table("api_keys")\
                .update({"last_used_at": datetime.utcnow().isoformat()})\
                .eq("id", key_info["id"])\
                .execute()
            
            return key_info
            
        except Exception as e:
            logger.error(f"Failed to verify API key: {e}")
            return None
    
    async def revoke_api_key(self, key_id: str, customer_id: str) -> bool:
        """Revoke an API key"""
        try:
            response = self.supabase.table("api_keys")\
                .update({"is_active": False})\
                .eq("id", key_id)\
                .eq("customer_id", customer_id)\
                .execute()
            
            if response.data:
                logger.info(f"Revoked API key {key_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to revoke API key: {e}")
            return False
    
    async def list_api_keys(self, customer_id: str) -> list:
        """List all API keys for a customer (without plain keys)"""
        try:
            response = self.supabase.table("api_keys")\
                .select("id, name, key_type, is_active, created_at, last_used_at, metadata")\
                .eq("customer_id", customer_id)\
                .order("created_at", desc=True)\
                .execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Failed to list API keys: {e}")
            return []


# Singleton instance
_api_key_service: Optional[APIKeyService] = None


def get_api_key_service() -> APIKeyService:
    """Get singleton API key service instance"""
    global _api_key_service
    if _api_key_service is None:
        _api_key_service = APIKeyService()
    return _api_key_service
