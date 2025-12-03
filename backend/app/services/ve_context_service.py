"""
VE Context Service
Manages VE memory and context persistence
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.core.database import get_supabase_admin

logger = logging.getLogger(__name__)


class VEContextService:
    """Service for managing VE context and memory"""
    
    def __init__(self):
        self.supabase = get_supabase_admin()
    
    async def get_context(self, customer_ve_id: str) -> Optional[Dict[str, Any]]:
        """
        Get VE context data
        Returns the context_data JSON or None if not found
        """
        try:
            response = self.supabase.table("ve_contexts")\
                .select("*")\
                .eq("customer_ve_id", customer_ve_id)\
                .execute()
            
            if response.data:
                return response.data[0]["context_data"]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get VE context: {e}")
            return None
    
    async def update_context(
        self,
        customer_ve_id: str,
        context_data: Dict[str, Any],
        merge: bool = True
    ) -> bool:
        """
        Update VE context
        
        Args:
            customer_ve_id: VE identifier
            context_data: New context data
            merge: If True, merge with existing context. If False, replace entirely
        
        Returns:
            True if successful
        """
        try:
            if merge:
                # Get existing context
                existing = await self.get_context(customer_ve_id)
                if existing:
                    # Deep merge
                    merged_context = self._deep_merge(existing, context_data)
                    context_data = merged_context
            
            # Check if context exists
            existing_response = self.supabase.table("ve_contexts")\
                .select("id")\
                .eq("customer_ve_id", customer_ve_id)\
                .execute()
            
            data = {
                "context_data": context_data,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            if existing_response.data:
                # Update
                self.supabase.table("ve_contexts")\
                    .update(data)\
                    .eq("customer_ve_id", customer_ve_id)\
                    .execute()
            else:
                # Insert
                data["customer_ve_id"] = customer_ve_id
                self.supabase.table("ve_contexts").insert(data).execute()
            
            logger.info(f"Updated context for VE {customer_ve_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update VE context: {e}")
            return False
    
    async def add_conversation_memory(
        self,
        customer_ve_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a conversation turn to VE memory
        
        Args:
            customer_ve_id: VE identifier
            role: 'user' or 'assistant'
            content: Message content
            metadata: Additional metadata (task_id, etc.)
        """
        try:
            context = await self.get_context(customer_ve_id) or {}
            
            if "conversation_history" not in context:
                context["conversation_history"] = []
            
            # Add conversation turn
            context["conversation_history"].append({
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            })
            
            # Keep only last 50 turns to avoid bloat
            if len(context["conversation_history"]) > 50:
                context["conversation_history"] = context["conversation_history"][-50:]
            
            return await self.update_context(customer_ve_id, context, merge=False)
            
        except Exception as e:
            logger.error(f"Failed to add conversation memory: {e}")
            return False
    
    async def add_learning(
        self,
        customer_ve_id: str,
        lesson: str,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a learning/lesson to VE memory
        Used for error recovery and continuous improvement
        
        Args:
            customer_ve_id: VE identifier
            lesson: The lesson learned
            category: Category (e.g., 'error_recovery', 'best_practice')
            metadata: Additional context
        """
        try:
            context = await self.get_context(customer_ve_id) or {}
            
            if "learnings" not in context:
                context["learnings"] = []
            
            # Add learning
            context["learnings"].append({
                "lesson": lesson,
                "category": category,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            })
            
            # Keep only last 100 learnings
            if len(context["learnings"]) > 100:
                context["learnings"] = context["learnings"][-100:]
            
            logger.info(f"Added learning to VE {customer_ve_id}: {lesson}")
            return await self.update_context(customer_ve_id, context, merge=False)
            
        except Exception as e:
            logger.error(f"Failed to add learning: {e}")
            return False
    
    async def get_learnings(
        self,
        customer_ve_id: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get learnings for a VE, optionally filtered by category
        """
        try:
            context = await self.get_context(customer_ve_id)
            if not context or "learnings" not in context:
                return []
            
            learnings = context["learnings"]
            
            if category:
                learnings = [l for l in learnings if l.get("category") == category]
            
            return learnings
            
        except Exception as e:
            logger.error(f"Failed to get learnings: {e}")
            return []
    
    async def share_learning_across_ves(
        self,
        customer_id: str,
        lesson: str,
        category: str = "shared",
        exclude_ve_id: Optional[str] = None
    ) -> int:
        """
        Share a learning across all VEs for a customer
        Useful for system-wide improvements
        
        Returns:
            Number of VEs updated
        """
        try:
            # Get all VEs for customer
            ves_response = self.supabase.table("customer_ves")\
                .select("id")\
                .eq("customer_id", customer_id)\
                .execute()
            
            count = 0
            for ve in ves_response.data:
                if exclude_ve_id and ve["id"] == exclude_ve_id:
                    continue
                
                success = await self.add_learning(
                    customer_ve_id=ve["id"],
                    lesson=lesson,
                    category=category,
                    metadata={"shared": True}
                )
                
                if success:
                    count += 1
            
            logger.info(f"Shared learning across {count} VEs for customer {customer_id}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to share learning: {e}")
            return 0
    
    def _deep_merge(self, dict1: Dict, dict2: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result


# Singleton instance
_ve_context_service: Optional[VEContextService] = None


def get_ve_context_service() -> VEContextService:
    """Get singleton VE context service instance"""
    global _ve_context_service
    if _ve_context_service is None:
        _ve_context_service = VEContextService()
    return _ve_context_service
