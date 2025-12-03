"""Knowledge Base API routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.schemas import KnowledgeBaseItemCreate, KnowledgeBaseItemResponse, KnowledgeSearchRequest, KnowledgeSearchResponse
from app.core.database import get_supabase_admin
from app.core.security import get_current_customer_id
from app.services.embeddings_service import get_embeddings_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("", response_model=KnowledgeBaseItemResponse, status_code=201)
async def add_knowledge_item(
    item: KnowledgeBaseItemCreate,
    customer_id: str = Depends(get_current_customer_id)
):
    """Add item to company knowledge base with automatic embedding generation"""
    try:
        embeddings_service = get_embeddings_service()
        
        # Add knowledge with embedding
        result = await embeddings_service.add_knowledge_with_embedding(
            customer_id=customer_id,
            content=item.content,
            content_type=item.content_type,
            metadata=item.metadata
        )
        
        return KnowledgeBaseItemResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to add knowledge item: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add knowledge item: {str(e)}")

@router.get("", response_model=List[KnowledgeBaseItemResponse])
async def list_knowledge_items(
    customer_id: str = Depends(get_current_customer_id)
):
    """List all knowledge base items"""
    supabase = get_supabase_admin()
    
    response = supabase.table("company_knowledge").select("*").eq("customer_id", customer_id).order("created_at", desc=True).execute()
    
    return [KnowledgeBaseItemResponse(**item) for item in response.data]

@router.post("/search", response_model=List[KnowledgeSearchResponse])
async def search_knowledge(
    request: KnowledgeSearchRequest,
    customer_id: str = Depends(get_current_customer_id)
):
    """
    Search knowledge base using vector similarity (RAG)
    Returns most relevant knowledge items for the query
    """
    try:
        embeddings_service = get_embeddings_service()
        
        results = await embeddings_service.search_similar_knowledge(
            customer_id=customer_id,
            query=request.query,
            limit=request.limit or 5,
            similarity_threshold=request.similarity_threshold or 0.7
        )
        
        return [KnowledgeSearchResponse(**item) for item in results]
        
    except Exception as e:
        logger.error(f"Failed to search knowledge: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.delete("/{item_id}")
async def delete_knowledge_item(
    item_id: str,
    customer_id: str = Depends(get_current_customer_id)
):
    """Delete a knowledge base item"""
    supabase = get_supabase_admin()
    
    response = supabase.table("company_knowledge").delete().eq("id", item_id).eq("customer_id", customer_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Item not found")
        
    return {"message": "Item deleted successfully"}
