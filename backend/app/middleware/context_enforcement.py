"""
Context Enforcement Middleware
Ensures ALL requests to agents include valid customer context
"""
import re
import logging
from fastapi import Request, HTTPException
from datetime import datetime
import hashlib
from typing import Callable

logger = logging.getLogger(__name__)


class ContextEnforcementMiddleware:
    """
    Enforces customer context on all agent requests
    
    This middleware is the FIRST line of defense against data leakage.
    It ensures that no request reaches an agent without a valid customer_id.
    """
    
    # UUID v4 pattern
    CUSTOMER_ID_PATTERN = re.compile(
        r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
    )
    
    async def __call__(
        self,
        request: Request,
        call_next: Callable
    ):
        """
        Process request and enforce context
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
        
        Returns:
            Response
        
        Raises:
            HTTPException: If customer_id missing or invalid
        """
        # Only enforce on agent routes
        if not request.url.path.startswith("/agents/"):
            return await call_next(request)
        
        # Extract customer_id from path or JWT
        customer_id = self.extract_customer_id(request)
        
        # CRITICAL: Reject if missing
        if not customer_id:
            logger.error(
                f"SECURITY VIOLATION: Request to {request.url.path} missing customer_id"
            )
            raise HTTPException(
                status_code=403,
                detail="Forbidden: customer_id required for agent access"
            )
        
        # CRITICAL: Validate format (prevent injection attacks)
        if not self.CUSTOMER_ID_PATTERN.match(customer_id):
            logger.error(
                f"SECURITY VIOLATION: Invalid customer_id format: {customer_id}"
            )
            raise HTTPException(
                status_code=403,
                detail="Forbidden: invalid customer_id format"
            )
        
        # Inject into request state (immutable)
        request.state.customer_id = customer_id
        request.state.context_hash = self.generate_context_hash(customer_id, request)
        
        # Audit log EVERY request
        await self.audit_log(request, customer_id)
        
        # Process request
        response = await call_next(request)
        
        return response
    
    def extract_customer_id(self, request: Request) -> str:
        """
        Extract customer_id from request
        
        Priority:
        1. Path parameter: /agents/{customer_id}/{agent_name}
        2. JWT token (if authenticated)
        
        Args:
            request: FastAPI request
        
        Returns:
            Customer ID or None
        """
        # From path: /agents/{customer_id}/{agent_name}
        path_parts = request.url.path.split('/')
        if len(path_parts) >= 3 and path_parts[1] == "agents":
            return path_parts[2]
        
        # From JWT (fallback)
        # TODO: Extract from validated JWT token in Authorization header
        # auth_header = request.headers.get("Authorization")
        # if auth_header:
        #     token = auth_header.replace("Bearer ", "")
        #     payload = decode_jwt(token)
        #     return payload.get("customer_id")
        
        return None
    
    def generate_context_hash(self, customer_id: str, request: Request) -> str:
        """
        Generate unique hash for this request context
        
        Used for audit trail and correlation
        
        Args:
            customer_id: Customer UUID
            request: FastAPI request
        
        Returns:
            SHA256 hash
        """
        content = f"{customer_id}:{request.url.path}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def audit_log(self, request: Request, customer_id: str):
        """
        Log every agent request for security audit
        
        Args:
            request: FastAPI request
            customer_id: Customer UUID
        """
        from app.core.database import get_supabase_admin
        
        supabase = get_supabase_admin()
        
        try:
            supabase.table("security_audit_log").insert({
                "timestamp": datetime.utcnow().isoformat(),
                "customer_id": customer_id,
                "path": request.url.path,
                "method": request.method,
                "context_hash": request.state.context_hash,
                "ip_address": request.client.host if request.client else None
            }).execute()
        except Exception as e:
            # Don't fail request if audit logging fails
            logger.error(f"Failed to write audit log: {e}")
