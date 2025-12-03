"""
Middleware package initialization
"""
from app.middleware.context_enforcement import ContextEnforcementMiddleware

__all__ = ["ContextEnforcementMiddleware"]
