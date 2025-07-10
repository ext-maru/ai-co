"""
Knowledge Sage API Endpoints
Manages knowledge base, documentation, and learning resources
"""

from typing import List, Optional
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.schemas.sages import (
    KnowledgeArticle,
    KnowledgeArticleCreate,
    KnowledgeArticleUpdate,
    KnowledgeResponse,
)
from app.websocket.manager import SageMessage, websocket_manager

logger = structlog.get_logger()
router = APIRouter()

# In-memory storage for demonstration (replace with database in production)
knowledge_store: dict[str, KnowledgeArticle] = {}


@router.get("/", response_model=KnowledgeResponse)
async def get_knowledge_articles(
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    limit: int = Query(10, ge=1, le=100, description="Number of articles to return"),
    offset: int = Query(0, ge=0, description="Number of articles to skip"),
):
    """
    Get all knowledge articles with optional filtering.
    """
    try:
        articles = list(knowledge_store.values())
        
        # Apply filters
        if category:
            articles = [a for a in articles if a.category == category]
        
        if status:
            articles = [a for a in articles if a.status == status]
        
        if tags:
            articles = [a for a in articles if any(tag in a.tags for tag in tags)]
        
        # Pagination
        total_count = len(articles)
        articles = articles[offset:offset + limit]
        
        # Broadcast status update
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="knowledge",
                message_type="status_update",
                content={
                    "action": "articles_retrieved",
                    "count": len(articles),
                    "total": total_count,
                },
                timestamp=0,  # Will be set by manager
            )
        )
        
        return KnowledgeResponse(
            data=articles,
            total_count=total_count,
            message=f"Retrieved {len(articles)} knowledge articles",
        )
        
    except Exception as e:
        logger.error("Error retrieving knowledge articles", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve articles")


@router.post("/", response_model=KnowledgeResponse)
async def create_knowledge_article(article: KnowledgeArticleCreate):
    """
    Create a new knowledge article.
    """
    try:
        # Generate ID
        article_id = str(uuid4())
        
        # Create article
        new_article = KnowledgeArticle(
            id=UUID(article_id),
            **article.dict(),
        )
        
        # Store article
        knowledge_store[article_id] = new_article
        
        # Broadcast creation to other sages
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="knowledge",
                message_type="broadcast",
                content={
                    "action": "article_created",
                    "article_id": article_id,
                    "title": new_article.title,
                    "category": new_article.category,
                    "author": new_article.author,
                },
                timestamp=0,
            )
        )
        
        logger.info(
            "Knowledge article created",
            article_id=article_id,
            title=new_article.title,
            category=new_article.category,
        )
        
        return KnowledgeResponse(
            data=new_article,
            message="Knowledge article created successfully",
        )
        
    except Exception as e:
        logger.error("Error creating knowledge article", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create article")


@router.get("/{article_id}", response_model=KnowledgeResponse)
async def get_knowledge_article(article_id: str):
    """
    Get a specific knowledge article by ID.
    """
    try:
        if article_id not in knowledge_store:
            raise HTTPException(status_code=404, detail="Article not found")
        
        article = knowledge_store[article_id]
        
        # Broadcast view event
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="knowledge",
                message_type="status_update",
                content={
                    "action": "article_viewed",
                    "article_id": article_id,
                    "title": article.title,
                },
                timestamp=0,
            )
        )
        
        return KnowledgeResponse(
            data=article,
            message="Article retrieved successfully",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving knowledge article", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve article")


@router.put("/{article_id}", response_model=KnowledgeResponse)
async def update_knowledge_article(article_id: str, update: KnowledgeArticleUpdate):
    """
    Update a knowledge article.
    """
    try:
        if article_id not in knowledge_store:
            raise HTTPException(status_code=404, detail="Article not found")
        
        article = knowledge_store[article_id]
        
        # Update fields
        update_data = update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(article, field, value)
        
        # Increment version
        article.version += 1
        
        # Update timestamp
        from datetime import datetime
        article.updated_at = datetime.utcnow()
        
        # Broadcast update
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="knowledge",
                message_type="broadcast",
                content={
                    "action": "article_updated",
                    "article_id": article_id,
                    "title": article.title,
                    "version": article.version,
                    "updated_fields": list(update_data.keys()),
                },
                timestamp=0,
            )
        )
        
        logger.info(
            "Knowledge article updated",
            article_id=article_id,
            version=article.version,
            updated_fields=list(update_data.keys()),
        )
        
        return KnowledgeResponse(
            data=article,
            message="Article updated successfully",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating knowledge article", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update article")


@router.delete("/{article_id}", response_model=KnowledgeResponse)
async def delete_knowledge_article(article_id: str):
    """
    Delete a knowledge article.
    """
    try:
        if article_id not in knowledge_store:
            raise HTTPException(status_code=404, detail="Article not found")
        
        article = knowledge_store[article_id]
        del knowledge_store[article_id]
        
        # Broadcast deletion
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="knowledge",
                message_type="broadcast",
                content={
                    "action": "article_deleted",
                    "article_id": article_id,
                    "title": article.title,
                },
                timestamp=0,
            )
        )
        
        logger.info("Knowledge article deleted", article_id=article_id)
        
        return KnowledgeResponse(
            message="Article deleted successfully",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting knowledge article", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete article")


@router.get("/categories/", response_model=KnowledgeResponse)
async def get_knowledge_categories():
    """
    Get all available knowledge categories.
    """
    try:
        categories = list(set(article.category for article in knowledge_store.values()))
        categories.sort()
        
        return KnowledgeResponse(
            data=categories,
            message=f"Retrieved {len(categories)} categories",
        )
        
    except Exception as e:
        logger.error("Error retrieving categories", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve categories")


@router.get("/tags/", response_model=KnowledgeResponse)
async def get_knowledge_tags():
    """
    Get all available knowledge tags.
    """
    try:
        all_tags = set()
        for article in knowledge_store.values():
            all_tags.update(article.tags)
        
        tags = sorted(list(all_tags))
        
        return KnowledgeResponse(
            data=tags,
            message=f"Retrieved {len(tags)} tags",
        )
        
    except Exception as e:
        logger.error("Error retrieving tags", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve tags")


@router.get("/stats/", response_model=KnowledgeResponse)
async def get_knowledge_stats():
    """
    Get knowledge base statistics.
    """
    try:
        total_articles = len(knowledge_store)
        
        stats = {
            "total_articles": total_articles,
            "published_articles": len([a for a in knowledge_store.values() if a.status == "published"]),
            "draft_articles": len([a for a in knowledge_store.values() if a.status == "draft"]),
            "archived_articles": len([a for a in knowledge_store.values() if a.status == "archived"]),
            "total_categories": len(set(a.category for a in knowledge_store.values())),
            "total_authors": len(set(a.author for a in knowledge_store.values())),
        }
        
        return KnowledgeResponse(
            data=stats,
            message="Knowledge base statistics retrieved",
        )
        
    except Exception as e:
        logger.error("Error retrieving knowledge stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")