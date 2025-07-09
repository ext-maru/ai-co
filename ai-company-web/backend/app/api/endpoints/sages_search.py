"""
Search Sage API Endpoints
RAG-powered search across all knowledge sources
"""

import time
from typing import List, Optional
from uuid import uuid4

import structlog
from fastapi import APIRouter, HTTPException, Query

from app.schemas.sages import (
    SearchQuery,
    SearchResult,
    SearchResponse,
)
from app.websocket.manager import SageMessage, websocket_manager

# Import from other sage stores for cross-sage search
from app.api.endpoints.sages_knowledge import knowledge_store
from app.api.endpoints.sages_tasks import task_store
from app.api.endpoints.sages_incidents import incident_store

logger = structlog.get_logger()
router = APIRouter()


def calculate_relevance_score(query: str, content: str) -> float:
    """
    Calculate a simple relevance score based on keyword matching.
    In production, this would use semantic similarity models.
    """
    query_words = set(query.lower().split())
    content_words = set(content.lower().split())
    
    if not query_words:
        return 0.0
    
    # Simple Jaccard similarity
    intersection = len(query_words.intersection(content_words))
    union = len(query_words.union(content_words))
    
    if union == 0:
        return 0.0
    
    return intersection / union


def highlight_content(content: str, query: str, max_length: int = 200) -> str:
    """
    Create highlighted content snippet for search results.
    """
    query_words = query.lower().split()
    content_lower = content.lower()
    
    # Find the best snippet containing query words
    best_start = 0
    best_score = 0
    
    for i in range(0, len(content), 50):
        snippet = content[i:i+max_length]
        snippet_lower = snippet.lower()
        score = sum(1 for word in query_words if word in snippet_lower)
        
        if score > best_score:
            best_score = score
            best_start = i
    
    snippet = content[best_start:best_start+max_length]
    if best_start > 0:
        snippet = "..." + snippet
    if best_start + max_length < len(content):
        snippet = snippet + "..."
    
    # Simple highlighting (in production, use proper HTML highlighting)
    for word in query_words:
        snippet = snippet.replace(word, f"**{word}**")
        snippet = snippet.replace(word.capitalize(), f"**{word.capitalize()}**")
    
    return snippet


@router.post("/", response_model=SearchResponse)
async def search_all_content(query: SearchQuery):
    """
    Search across all Four Sages content using RAG techniques.
    """
    start_time = time.time()
    
    try:
        results = []
        
        # Search Knowledge Base
        for article_id, article in knowledge_store.items():
            content_text = f"{article.title} {article.content} {' '.join(article.tags)}"
            score = calculate_relevance_score(query.query, content_text)
            
            if score > 0:
                results.append(SearchResult(
                    id=article_id,
                    title=article.title,
                    content=article.content[:500] + "..." if len(article.content) > 500 else article.content,
                    source="knowledge",
                    score=score,
                    metadata={
                        "category": article.category,
                        "author": article.author,
                        "status": article.status,
                        "tags": article.tags,
                        "version": article.version,
                    },
                    highlighted_content=highlight_content(article.content, query.query),
                ))
        
        # Search Tasks
        for task_id, task in task_store.items():
            content_text = f"{task.title} {task.description or ''} {' '.join(task.labels)}"
            score = calculate_relevance_score(query.query, content_text)
            
            if score > 0:
                results.append(SearchResult(
                    id=task_id,
                    title=task.title,
                    content=task.description or task.title,
                    source="task",
                    score=score,
                    metadata={
                        "status": task.status,
                        "priority": task.priority,
                        "assignee": task.assignee,
                        "project": task.project,
                        "labels": task.labels,
                    },
                    highlighted_content=highlight_content(
                        task.description or task.title, query.query
                    ),
                ))
        
        # Search Incidents
        for incident_id, incident in incident_store.items():
            content_text = f"{incident.title} {incident.description} {' '.join(incident.affected_systems)}"
            score = calculate_relevance_score(query.query, content_text)
            
            if score > 0:
                results.append(SearchResult(
                    id=incident_id,
                    title=incident.title,
                    content=incident.description,
                    source="incident",
                    score=score,
                    metadata={
                        "severity": incident.severity,
                        "status": incident.status,
                        "assignee": incident.assignee,
                        "reporter": incident.reporter,
                        "affected_systems": incident.affected_systems,
                        "resolution": incident.resolution,
                    },
                    highlighted_content=highlight_content(incident.description, query.query),
                ))
        
        # Apply filters if provided
        if query.filters:
            if "source" in query.filters:
                allowed_sources = query.filters["source"]
                if isinstance(allowed_sources, str):
                    allowed_sources = [allowed_sources]
                results = [r for r in results if r.source in allowed_sources]
            
            if "min_score" in query.filters:
                min_score = query.filters["min_score"]
                results = [r for r in results if r.score >= min_score]
        
        # Sort by relevance score
        results.sort(key=lambda r: r.score, reverse=True)
        
        # Apply pagination
        total_count = len(results)
        results = results[query.offset:query.offset + query.limit]
        
        # Calculate query time
        query_time_ms = (time.time() - start_time) * 1000
        
        # Generate search suggestions (simple implementation)
        suggestions = []
        if not results and len(query.query.split()) > 1:
            # Suggest individual words from the query
            suggestions = query.query.split()[:3]
        
        # Broadcast search activity
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="search",
                message_type="status_update",
                content={
                    "action": "search_executed",
                    "query": query.query,
                    "search_type": query.search_type,
                    "results_count": len(results),
                    "total_count": total_count,
                    "query_time_ms": query_time_ms,
                },
                timestamp=0,
            )
        )
        
        logger.info(
            "Search executed",
            query=query.query,
            search_type=query.search_type,
            results_count=len(results),
            total_count=total_count,
            query_time_ms=query_time_ms,
        )
        
        return SearchResponse(
            results=results,
            total_count=total_count,
            query_time_ms=query_time_ms,
            suggestions=suggestions if suggestions else None,
            message=f"Found {total_count} results in {query_time_ms:.2f}ms",
        )
        
    except Exception as e:
        logger.error("Error executing search", error=str(e))
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/suggestions", response_model=SearchResponse)
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Partial query for suggestions"),
    limit: int = Query(5, ge=1, le=20, description="Number of suggestions"),
):
    """
    Get search suggestions based on partial query.
    """
    try:
        suggestions = set()
        
        # Extract suggestions from knowledge base
        for article in knowledge_store.values():
            words = article.title.lower().split()
            for word in words:
                if word.startswith(q.lower()) and len(word) > len(q):
                    suggestions.add(word)
            
            for tag in article.tags:
                if tag.lower().startswith(q.lower()) and len(tag) > len(q):
                    suggestions.add(tag)
        
        # Extract suggestions from tasks
        for task in task_store.items():
            words = task.title.lower().split()
            for word in words:
                if word.startswith(q.lower()) and len(word) > len(q):
                    suggestions.add(word)
        
        # Extract suggestions from incidents
        for incident in incident_store.values():
            words = incident.title.lower().split()
            for word in words:
                if word.startswith(q.lower()) and len(word) > len(q):
                    suggestions.add(word)
        
        # Sort and limit suggestions
        suggestion_list = sorted(list(suggestions))[:limit]
        
        return SearchResponse(
            results=[],
            total_count=0,
            query_time_ms=0,
            suggestions=suggestion_list,
            message=f"Generated {len(suggestion_list)} suggestions",
        )
        
    except Exception as e:
        logger.error("Error generating suggestions", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate suggestions")


@router.get("/similar/{content_type}/{content_id}", response_model=SearchResponse)
async def find_similar_content(
    content_type: str = Query(..., regex="^(knowledge|task|incident)$"),
    content_id: str = Query(..., description="ID of the content to find similar items for"),
    limit: int = Query(5, ge=1, le=20, description="Number of similar items"),
):
    """
    Find content similar to a specific item.
    """
    try:
        # Get the source content
        source_content = ""
        source_title = ""
        
        if content_type == "knowledge" and content_id in knowledge_store:
            article = knowledge_store[content_id]
            source_content = f"{article.title} {article.content}"
            source_title = article.title
        elif content_type == "task" and content_id in task_store:
            task = task_store[content_id]
            source_content = f"{task.title} {task.description or ''}"
            source_title = task.title
        elif content_type == "incident" and content_id in incident_store:
            incident = incident_store[content_id]
            source_content = f"{incident.title} {incident.description}"
            source_title = incident.title
        else:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Create a search query from the source content
        # Extract key terms (simple implementation)
        words = source_content.lower().split()
        # Remove common words and take the most meaningful ones
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        key_words = [w for w in words if len(w) > 3 and w not in common_words][:10]
        search_query = " ".join(key_words)
        
        # Perform search with the extracted query
        query = SearchQuery(
            query=search_query,
            search_type="semantic",
            limit=limit + 1,  # +1 to exclude the source item
        )
        
        search_response = await search_all_content(query)
        
        # Filter out the source item
        similar_results = [
            result for result in search_response.results
            if not (result.source == content_type and result.id == content_id)
        ][:limit]
        
        # Broadcast similarity search
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="search",
                message_type="status_update",
                content={
                    "action": "similarity_search",
                    "source_type": content_type,
                    "source_id": content_id,
                    "source_title": source_title,
                    "similar_count": len(similar_results),
                },
                timestamp=0,
            )
        )
        
        return SearchResponse(
            results=similar_results,
            total_count=len(similar_results),
            query_time_ms=search_response.query_time_ms,
            message=f"Found {len(similar_results)} similar items",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error finding similar content", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to find similar content")


@router.get("/analytics", response_model=SearchResponse)
async def get_search_analytics():
    """
    Get search analytics and content statistics.
    """
    try:
        analytics = {
            "content_counts": {
                "knowledge_articles": len(knowledge_store),
                "tasks": len(task_store),
                "incidents": len(incident_store),
                "total_searchable_items": len(knowledge_store) + len(task_store) + len(incident_store),
            },
            "knowledge_categories": list(set(
                article.category for article in knowledge_store.values()
            )),
            "task_projects": list(set(
                task.project for task in task_store.values() if task.project
            )),
            "incident_systems": list(set(
                system for incident in incident_store.values()
                for system in incident.affected_systems
            )),
            "most_common_tags": [],  # Could implement tag frequency analysis
        }
        
        return SearchResponse(
            results=[],
            total_count=0,
            query_time_ms=0,
            message="Search analytics retrieved",
            success=True,
            data=analytics,
        )
        
    except Exception as e:
        logger.error("Error retrieving search analytics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")


@router.post("/index/rebuild")
async def rebuild_search_index():
    """
    Rebuild the search index (placeholder for future implementation).
    """
    try:
        # In a real implementation, this would rebuild search indexes,
        # update embeddings, etc.
        
        total_items = len(knowledge_store) + len(task_store) + len(incident_store)
        
        # Broadcast index rebuild
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="search",
                message_type="broadcast",
                content={
                    "action": "search_index_rebuilt",
                    "total_items": total_items,
                    "knowledge_items": len(knowledge_store),
                    "task_items": len(task_store),
                    "incident_items": len(incident_store),
                },
                timestamp=0,
            )
        )
        
        logger.info("Search index rebuilt", total_items=total_items)
        
        return SearchResponse(
            results=[],
            total_count=total_items,
            query_time_ms=0,
            message=f"Search index rebuilt with {total_items} items",
        )
        
    except Exception as e:
        logger.error("Error rebuilding search index", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to rebuild search index")