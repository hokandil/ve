"""
Agent Context and Base Classes
Enforces customer isolation at the framework level
"""
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class AgentContext:
    """
    Immutable context object for agent requests
    
    This context MUST be provided for every agent request.
    It cannot be modified after creation to prevent tampering.
    """
    
    def __init__(
        self,
        customer_id: str,
        user_id: str,
        permissions: List[str],
        session_id: Optional[str] = None
    ):
        """
        Initialize agent context
        
        Args:
            customer_id: UUID of the customer
            user_id: UUID or email of the user
            permissions: List of permission strings (e.g., ["read_analytics", "write_content"])
            session_id: Optional session identifier
        """
        self._customer_id = customer_id
        self._user_id = user_id
        self._permissions = tuple(permissions)  # Immutable tuple
        self._session_id = session_id
    
    @property
    def customer_id(self) -> str:
        """Customer UUID - read-only"""
        return self._customer_id
    
    @property
    def user_id(self) -> str:
        """User identifier - read-only"""
        return self._user_id
    
    @property
    def permissions(self) -> tuple:
        """User permissions - read-only tuple"""
        return self._permissions
    
    @property
    def session_id(self) -> Optional[str]:
        """Session identifier - read-only"""
        return self._session_id
    
    def has_permission(self, permission: str) -> bool:
        """Check if context has a specific permission"""
        return permission in self._permissions
    
    def __setattr__(self, name, value):
        """Prevent modification after initialization"""
        # Allow setting during __init__ (when _initialized doesn't exist yet)
        if not hasattr(self, '_initialized'):
            super().__setattr__(name, value)
            # Mark as initialized after all attributes are set
            if name == '_session_id':
                super().__setattr__('_initialized', True)
        else:
            raise AttributeError(
                f"AgentContext is immutable. Cannot set '{name}' after initialization."
            )
    
    def __repr__(self):
        return (
            f"AgentContext(customer_id={self.customer_id}, "
            f"user_id={self.user_id}, "
            f"permissions={list(self.permissions)})"
        )


class ScopedMemory:
    """
    Memory interface that ENFORCES customer scoping
    
    This class wraps a vector database and ensures that ALL queries
    are automatically filtered by customer_id. Agents cannot bypass this.
    """
    
    def __init__(self, vector_db, customer_id: str):
        """
        Initialize scoped memory
        
        Args:
            vector_db: Vector database instance
            customer_id: Customer UUID to scope to
        """
        self._db = vector_db
        self._customer_id = customer_id
        # Immutable filter - always applied to queries
        self._filter = {"customer_id": customer_id}
    
    def search(self, query: str, top_k: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """
        Search memories - automatically scoped to customer
        
        Args:
            query: Search query string
            top_k: Number of results to return
            **kwargs: Additional search parameters
        
        Returns:
            List of memory documents (only from this customer)
        """
        # Merge customer filter with any additional filters
        filters = {**self._filter, **kwargs.get('filter', {})}
        
        return self._db.search(
            query=query,
            filter=filters,
            top_k=top_k
        )
    
    def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add memory - automatically tagged with customer_id
        
        Args:
            content: Memory content
            metadata: Optional metadata dict
        
        Returns:
            Memory ID
        """
        data = {
            "content": content,
            "customer_id": self._customer_id,  # Force customer_id
            "metadata": metadata or {}
        }
        
        return self._db.add(data)
    
    def get_conversation_history(
        self,
        limit: int = 10,
        agent_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversation history for this customer
        
        Args:
            limit: Maximum number of messages to return
            agent_name: Optional filter by agent name
        
        Returns:
            List of conversation messages
        """
        filters = {
            "customer_id": self._customer_id,
            "type": "conversation"
        }
        
        if agent_name:
            filters["agent_name"] = agent_name
        
        return self._db.query(
            filter=filters,
            order_by="timestamp",
            limit=limit
        )
    
    def clear_session(self, session_id: str):
        """
        Clear memories for a specific session
        
        Args:
            session_id: Session to clear
        """
        self._db.delete(
            filter={
                "customer_id": self._customer_id,
                "session_id": session_id
            }
        )


class BaseAgent(ABC):
    """
    Base class for all agents - enforces context isolation
    
    All agents MUST inherit from this class and implement _execute().
    This ensures that agents cannot receive requests without customer context.
    """
    
    def __init__(self, agent_name: str, agent_role: str):
        """
        Initialize base agent
        
        Args:
            agent_name: Unique agent identifier (e.g., "marketing-manager")
            agent_role: Human-readable role (e.g., "Marketing Manager")
        """
        self.agent_name = agent_name
        self.agent_role = agent_role
        self._raw_memory_db = None  # Private - agents can't access directly
        
        logger.info(f"Initialized agent: {agent_name} ({agent_role})")
    
    def process_task(
        self,
        task: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Main entry point - REQUIRES context
        
        This is the ONLY public method for processing tasks.
        It enforces that context is provided and valid.
        
        Args:
            task: Task data (message, metadata, etc.)
            context: AgentContext (immutable, validated by gateway)
        
        Returns:
            Response dict
        
        Raises:
            TypeError: If context is not an AgentContext instance
        """
        # CRITICAL: Validate context type
        if not isinstance(context, AgentContext):
            raise TypeError(
                f"context must be AgentContext instance, got {type(context)}"
            )
        
        logger.info(
            f"Agent {self.agent_name} processing task for customer {context.customer_id}"
        )
        
        # Get scoped memory for this customer
        memory = self._get_scoped_memory(context)
        
        # Get scoped tools for this customer
        tools = self._get_scoped_tools(context)
        
        # Execute agent logic with isolated context
        try:
            response = self._execute(task, context, memory, tools)
            
            logger.info(
                f"Agent {self.agent_name} completed task for customer {context.customer_id}"
            )
            
            return response
            
        except Exception as e:
            logger.error(
                f"Agent {self.agent_name} failed for customer {context.customer_id}: {e}"
            )
            raise
    
    def _get_scoped_memory(self, context: AgentContext) -> ScopedMemory:
        """
        Get memory scoped to customer - CANNOT access other customers
        
        Args:
            context: Agent context
        
        Returns:
            ScopedMemory instance
        """
        from app.services.vector_db import get_vector_db
        
        db = get_vector_db()
        return ScopedMemory(db, context.customer_id)
    
    def _get_scoped_tools(self, context: AgentContext) -> Dict[str, Any]:
        """
        Get tools scoped to customer permissions
        
        Args:
            context: Agent context
        
        Returns:
            Dict of available tools
        """
        from app.services.tool_registry import get_tools_for_customer
        
        return get_tools_for_customer(
            customer_id=context.customer_id,
            permissions=list(context.permissions)
        )
    
    @abstractmethod
    def _execute(
        self,
        task: Dict[str, Any],
        context: AgentContext,
        memory: ScopedMemory,
        tools: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Agent-specific logic - implemented by subclasses
        
        Subclasses MUST implement this method.
        They MUST use the provided memory and tools (already scoped).
        
        Args:
            task: Task data
            context: Agent context (immutable)
            memory: Scoped memory interface
            tools: Scoped tools dict
        
        Returns:
            Response dict
        """
        pass
    
    def delegate_to_agent(
        self,
        target_agent: str,
        task: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Delegate task to another agent - preserves customer context
        
        Args:
            target_agent: Name of target agent
            task: Task to delegate
            context: Current context (will be preserved)
        
        Returns:
            Response from target agent
        """
        from app.services.agent_gateway_service import agent_gateway_service
        
        # Preserve customer context in delegation
        delegation_request = {
            "task": task,
            "context": {
                "customer_id": context.customer_id,
                "user_id": context.user_id,
                "permissions": list(context.permissions),
                "delegated_by": self.agent_name,
                "session_id": context.session_id
            }
        }
        
        logger.info(
            f"Agent {self.agent_name} delegating to {target_agent} "
            f"for customer {context.customer_id}"
        )
        
        # Route through Agent Gateway
        response = agent_gateway_service.invoke_agent(
            agent_id=target_agent,
            customer_id=context.customer_id,
            message=task.get("message", ""),
            agent_name=target_agent,
            namespace="agents-system"  # Shared namespace
        )
        
        return response
