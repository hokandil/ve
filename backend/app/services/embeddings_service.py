"""
Embeddings Service
Handles generation and management of vector embeddings for RAG
Supports multiple LLM providers (Gemini, OpenAI, etc.)
"""
import logging
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings
from app.core.database import get_supabase_admin

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for generating and managing embeddings (LLM-agnostic)"""
    
    def __init__(self):
        self.dimensions = 768  # Default for most models
        self.provider = self._detect_provider()
        
    def _detect_provider(self) -> str:
        """Auto-detect which LLM provider to use based on available API keys"""
        if hasattr(settings, 'GOOGLE_API_KEY') and settings.GOOGLE_API_KEY:
            return "gemini"
        elif hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            return "openai"
        else:
            logger.warning("No LLM API key configured, using mock embeddings")
            return "mock"
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text using configured LLM provider
        Supports: Gemini, OpenAI, and mock (fallback)
        """
        try:
            if self.provider == "gemini":
                return await self._generate_gemini_embedding(text)
            elif self.provider == "openai":
                return await self._generate_openai_embedding(text)
            else:
                return self._generate_mock_embedding(text)
                
        except Exception as e:
            logger.error(f"Failed to generate embedding with {self.provider}: {e}")
            # Fallback to mock
            return self._generate_mock_embedding(text)
    
    async def _generate_gemini_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using Google Gemini API"""
        try:
            async with httpx.AsyncClient() as client:
                # Gemini embedding model
                model = "models/text-embedding-004"
                
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/{model}:embedContent",
                    headers={
                        "Content-Type": "application/json",
                    },
                    params={
                        "key": settings.GOOGLE_API_KEY
                    },
                    json={
                        "model": model,
                        "content": {
                            "parts": [{
                                "text": text
                            }]
                        }
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                embedding = result.get("embedding", {}).get("values", [])
                
                if embedding:
                    self.dimensions = len(embedding)  # Update dimensions
                    logger.info(f"Generated Gemini embedding with {self.dimensions} dimensions")
                    return embedding
                
                return None
                
        except Exception as e:
            logger.error(f"Gemini embedding generation failed: {e}")
            raise
    
    async def _generate_openai_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using OpenAI API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "input": text,
                        "model": "text-embedding-3-small"
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                embedding = result["data"][0]["embedding"]
                self.dimensions = len(embedding)
                logger.info(f"Generated OpenAI embedding with {self.dimensions} dimensions")
                return embedding
                
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            raise
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """Generate mock embedding for development/testing"""
        # Simple hash-based mock embedding
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to list of floats normalized to [-1, 1]
        embedding = []
        for i in range(self.dimensions):
            byte_val = hash_bytes[i % len(hash_bytes)]
            normalized = (byte_val / 255.0) * 2 - 1
            embedding.append(normalized)
        
        return embedding
    
    async def add_knowledge_with_embedding(
        self,
        customer_id: str,
        content: str,
        content_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add knowledge item and generate embedding
        """
        try:
            # Generate embedding
            embedding = await self.generate_embedding(content)
            
            if not embedding:
                raise Exception("Failed to generate embedding")
            
            # Store in database
            supabase = get_supabase_admin()
            
            data = {
                "customer_id": customer_id,
                "content": content,
                "content_type": content_type,
                "metadata": metadata or {},
                "embeddings": embedding  # pgvector column
            }
            
            response = supabase.table("company_knowledge").insert(data).execute()
            
            if not response.data:
                raise Exception("Failed to insert knowledge item")
            
            logger.info(f"Added knowledge item with embedding for customer {customer_id}")
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Failed to add knowledge with embedding: {e}")
            raise
    
    async def search_similar_knowledge(
        self,
        customer_id: str,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar knowledge items using vector similarity
        """
        try:
            # Generate embedding for query
            query_embedding = await self.generate_embedding(query)
            
            if not query_embedding:
                raise Exception("Failed to generate query embedding")
            
            supabase = get_supabase_admin()
            
            # Use pgvector similarity search
            # Note: This requires pgvector extension and proper indexing
            # For now, we'll use a simple RPC call
            
            # Fallback: If pgvector RPC not available, fetch all and compute similarity in Python
            response = supabase.table("company_knowledge")\
                .select("*")\
                .eq("customer_id", customer_id)\
                .execute()
            
            if not response.data:
                return []
            
            # Compute cosine similarity
            results = []
            for item in response.data:
                if item.get("embeddings"):
                    similarity = self._cosine_similarity(query_embedding, item["embeddings"])
                    if similarity >= similarity_threshold:
                        results.append({
                            **item,
                            "similarity": similarity
                        })
            
            # Sort by similarity and limit
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to search similar knowledge: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)


# Singleton instance
_embeddings_service: Optional[EmbeddingsService] = None


def get_embeddings_service() -> EmbeddingsService:
    """Get singleton embeddings service instance"""
    global _embeddings_service
    if _embeddings_service is None:
        _embeddings_service = EmbeddingsService()
    return _embeddings_service
