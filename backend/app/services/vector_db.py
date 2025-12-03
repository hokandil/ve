"""
Vector Database Service with Customer Scoping
Provides vector database operations with automatic customer isolation
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class VectorDB:
    """
    Mock Vector Database for development
    
    In production, replace with actual vector DB (Pinecone, Weaviate, etc.)
    """
    
    def __init__(self):
        self.data: List[Dict[str, Any]] = []
    
    def search(
        self,
        query: str,
        filter: Dict[str, Any],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search vector database with filters
        
        Args:
            query: Search query
            filter: Filter dict (MUST include customer_id)
            top_k: Number of results
        
        Returns:
            List of matching documents
        """
        # Validate customer_id in filter
        if "customer_id" not in filter:
            raise ValueError("SECURITY: customer_id required in filter")
        
        # Filter data
        results = [
            item for item in self.data
            if all(item.get(k) == v for k, v in filter.items())
        ]
        
        # Simple relevance scoring (in production, use actual vector similarity)
        scored_results = [
            {**item, "score": self._calculate_score(query, item["content"])}
            for item in results
        ]
        
        # Sort by score and return top_k
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]
    
    def add(self, data: Dict[str, Any]) -> str:
        """
        Add document to vector database
        
        Args:
            data: Document data (MUST include customer_id)
        
        Returns:
            Document ID
        """
        # Validate customer_id
        if "customer_id" not in data:
            raise ValueError("SECURITY: customer_id required in data")
        
        # Generate ID
        doc_id = f"doc-{len(self.data) + 1}"
        
        # Add document
        doc = {
            "id": doc_id,
            "timestamp": datetime.utcnow().isoformat(),
            **data
        }
        self.data.append(doc)
        
        logger.info(f"Added document {doc_id} for customer {data['customer_id']}")
        return doc_id
    
    def query(
        self,
        filter: Dict[str, Any],
        order_by: str = "timestamp",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query documents with filters
        
        Args:
            filter: Filter dict (MUST include customer_id)
            order_by: Field to sort by
            limit: Max results
        
        Returns:
            List of documents
        """
        # Validate customer_id in filter
        if "customer_id" not in filter:
            raise ValueError("SECURITY: customer_id required in filter")
        
        # Filter data
        results = [
            item for item in self.data
            if all(item.get(k) == v for k, v in filter.items())
        ]
        
        # Sort
        results.sort(key=lambda x: x.get(order_by, ""), reverse=True)
        
        return results[:limit]
    
    def delete(self, filter: Dict[str, Any]):
        """
        Delete documents matching filter
        
        Args:
            filter: Filter dict (MUST include customer_id)
        """
        # Validate customer_id in filter
        if "customer_id" not in filter:
            raise ValueError("SECURITY: customer_id required in filter")
        
        # Remove matching documents
        self.data = [
            item for item in self.data
            if not all(item.get(k) == v for k, v in filter.items())
        ]
    
    def _calculate_score(self, query: str, content: str) -> float:
        """Simple scoring - replace with actual vector similarity in production"""
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Simple keyword matching
        query_words = set(query_lower.split())
        content_words = set(content_lower.split())
        
        if not query_words:
            return 0.0
        
        # Jaccard similarity
        intersection = query_words & content_words
        union = query_words | content_words
        
        return len(intersection) / len(union) if union else 0.0


# Singleton instance
_vector_db = None


def get_vector_db() -> VectorDB:
    """Get or create vector database singleton"""
    global _vector_db
    if _vector_db is None:
        _vector_db = VectorDB()
    return _vector_db
