"""
Security utilities for authentication and authorization
Supports both User JWT tokens and API Key authentication
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.database import get_supabase
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)  # Make optional for API key auth

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify JWT token"""
    try:
        # Try with the secret as provided (string)
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        # If that fails, try decoding the secret from Base64 (common for Supabase)
        try:
            import base64
            decoded_secret = base64.b64decode(settings.JWT_SECRET)
            payload = jwt.decode(token, decoded_secret, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except Exception as e:
            logger.error(f"Token verification failed (Base64 attempt): {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not validate credentials: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception as e:
        logger.error(f"Token verification failed (Initial attempt): {e}")
        # Continue to Base64 attempt

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None)
) -> dict:
    """
    Get current authenticated user from token OR API key
    Supports both user authentication and agent/service authentication
    """
    # Try API Key authentication first (for agents)
    if x_api_key:
        from app.services.api_key_service import get_api_key_service
        
        api_key_service = get_api_key_service()
        key_info = await api_key_service.verify_api_key(x_api_key)
        
        if key_info:
            # Return a user-like object for API key auth
            return {
                "id": key_info["customer_id"],
                "auth_type": "api_key",
                "key_type": key_info["key_type"],
                "key_name": key_info["name"],
                "metadata": key_info.get("metadata", {})
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
    
    # Fall back to JWT authentication (for users)
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication credentials provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    local_e = None
    
    # Try local verification first (faster, avoids API rate limits)
    try:
        payload = verify_token(token)
        # Construct user data from JWT payload
        user_data = {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "app_metadata": payload.get("app_metadata", {}),
            "user_metadata": payload.get("user_metadata", {}),
            "aud": payload.get("aud"),
            "role": payload.get("role"),
            "auth_type": "jwt"
        }
        return user_data
    except Exception as e:
        local_e = e
        logger.warning(f"Local token verification failed: {local_e}. Falling back to Supabase API.")
    
    # Verify with Supabase (Fallback)
    supabase = get_supabase()
    try:
        logger.info(f"Verifying token with Supabase API: {token[:10]}...")
        user = supabase.auth.get_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # user.user is a User object, we need to convert it to a dict or handle it
        # Depending on the library version, it might be a Pydantic model or simple object
        # Let's try to convert to dict safely
        if hasattr(user.user, "model_dump"):
            user_data = user.user.model_dump()
        elif hasattr(user.user, "dict"):
            user_data = user.user.dict()
        else:
            # Fallback for older versions or plain objects
            user_data = user.user.__dict__
            
        user_data["auth_type"] = "jwt"
        return user_data
        
    except Exception as e:
        logger.error(f"User authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials. Local error: {local_e}. Supabase error: {e}"
        )

async def get_current_customer_id(current_user: dict = Depends(get_current_user)) -> str:
    """Get current customer ID from authenticated user or API key"""
    return current_user["id"]

async def require_agent_auth(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Require agent/service authentication (API key only)
    Use this for endpoints that should only be called by agents
    """
    if current_user.get("auth_type") != "api_key":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires agent authentication (API key)"
        )
    return current_user

async def verify_service_token(
    authorization: Optional[str] = Header(None)
) -> bool:
    """
    Verify internal service token (for Agent Gateway / MCP Servers)
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    token = parts[1]
    
    if token != settings.AGENT_GATEWAY_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service token"
        )
        
    return True
