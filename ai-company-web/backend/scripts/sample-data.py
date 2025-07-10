#!/usr/bin/env python3
"""
Sample Data Generator for Elders Guild Web Four Sages System
Creates test data for development and demonstration
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from uuid import uuid4

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.schemas.sages import (
    KnowledgeArticleCreate,
    TaskCreate,
    IncidentCreate,
)

# Sample data for Knowledge Sage
SAMPLE_KNOWLEDGE_ARTICLES = [
    {
        "title": "FastAPI Best Practices",
        "content": """# FastAPI Best Practices

## Project Structure
- Use dependency injection for database connections
- Separate models, schemas, and services
- Implement proper error handling

## Security
- Use OAuth 2.0 with JWT tokens
- Validate all input data with Pydantic
- Implement rate limiting

## Performance
- Use async/await for I/O operations
- Implement caching with Redis
- Use connection pooling for databases
""",
        "category": "Development",
        "tags": ["fastapi", "python", "best-practices", "web-development"],
        "author": "Elders Guild Tech Team",
    },
    {
        "title": "WebSocket Real-time Communication",
        "content": """# WebSocket Implementation Guide

## Overview
WebSocket enables full-duplex communication between client and server.

## Four Sages Integration
- Knowledge Sage: Document updates
- Task Sage: Status changes
- Incident Sage: Alert notifications
- Search Sage: Real-time results

## Best Practices
- Implement heartbeat for connection monitoring
- Use message queues for reliability
- Handle reconnection gracefully
""",
        "category": "Architecture",
        "tags": ["websocket", "real-time", "communication", "four-sages"],
        "author": "System Architect",
    },
    {
        "title": "Four Sages System Architecture",
        "content": """# Four Sages System Design

## Knowledge Sage
Manages documentation, learning materials, and institutional knowledge.

## Task Sage  
Handles project management, workflows, and task automation.

## Incident Sage
Monitors system health, manages alerts, and automates responses.

## Search Sage
Provides intelligent search across all sage domains using RAG.

## Elder Council
Coordinates between sages for complex decision-making.
""",
        "category": "Architecture",
        "tags": ["four-sages", "system-design", "architecture"],
        "author": "Chief Architect",
    },
]

# Sample data for Task Sage
SAMPLE_TASKS = [
    {
        "title": "Implement WebSocket heartbeat mechanism",
        "description": "Add heartbeat functionality to maintain WebSocket connections and detect disconnections",
        "status": "in_progress",
        "priority": "high",
        "assignee": "Backend Developer",
        "project": "Four Sages System",
        "labels": ["websocket", "backend", "real-time"],
        "estimated_hours": 8.0,
        "actual_hours": 4.5,
    },
    {
        "title": "Create Elder Council UI components",
        "description": "Design and implement React components for Elder Council session management",
        "status": "todo",
        "priority": "medium", 
        "assignee": "Frontend Developer",
        "project": "Four Sages System",
        "labels": ["react", "ui", "elder-council"],
        "estimated_hours": 12.0,
    },
    {
        "title": "Set up PostgreSQL database schema",
        "description": "Design and implement database schema for all Four Sages data models",
        "status": "done",
        "priority": "high",
        "assignee": "Database Admin",
        "project": "Infrastructure",
        "labels": ["database", "postgresql", "schema"],
        "estimated_hours": 16.0,
        "actual_hours": 14.0,
    },
    {
        "title": "Implement search index optimization",
        "description": "Optimize search algorithms and implement semantic search capabilities",
        "status": "blocked",
        "priority": "medium",
        "assignee": "ML Engineer",
        "project": "Search Enhancement",
        "labels": ["search", "ml", "optimization"],
        "estimated_hours": 20.0,
    },
]

# Sample data for Incident Sage
SAMPLE_INCIDENTS = [
    {
        "title": "High CPU usage on production API server",
        "description": "API server showing 95% CPU utilization, causing slow response times and timeouts",
        "severity": "high",
        "status": "investigating",
        "assignee": "DevOps Engineer",
        "reporter": "Monitoring System",
        "affected_systems": ["api-server", "load-balancer", "database"],
    },
    {
        "title": "WebSocket connection drops during peak hours",
        "description": "Multiple WebSocket connections are dropping during high traffic periods",
        "severity": "medium",
        "status": "open",
        "assignee": "Backend Developer",
        "reporter": "Customer Support",
        "affected_systems": ["websocket-server", "redis"],
    },
    {
        "title": "Database connection pool exhaustion",
        "description": "PostgreSQL connection pool reaching maximum capacity, new connections failing",
        "severity": "critical",
        "status": "resolved",
        "assignee": "Database Admin",
        "reporter": "Application Monitoring",
        "affected_systems": ["postgresql", "api-server"],
        "resolution": "Increased connection pool size and implemented connection recycling",
    },
]

async def generate_sample_data():
    """
    Generate sample data by calling the API endpoints.
    This simulates real usage of the Four Sages system.
    """
    print("Generating sample data for Four Sages System...")
    
    # In a real implementation, you would use the actual API client
    # For now, we'll just print what would be created
    
    print("\n=== Knowledge Sage Sample Data ===")
    for i, article in enumerate(SAMPLE_KNOWLEDGE_ARTICLES, 1):
        print(f"{i}. {article['title']}")
        print(f"   Category: {article['category']}")
        print(f"   Tags: {', '.join(article['tags'])}")
        print(f"   Author: {article['author']}")
        print()
    
    print("=== Task Sage Sample Data ===")
    for i, task in enumerate(SAMPLE_TASKS, 1):
        print(f"{i}. {task['title']}")
        print(f"   Status: {task['status']} | Priority: {task['priority']}")
        print(f"   Assignee: {task['assignee']} | Project: {task['project']}")
        print(f"   Labels: {', '.join(task['labels'])}")
        print()
    
    print("=== Incident Sage Sample Data ===")
    for i, incident in enumerate(SAMPLE_INCIDENTS, 1):
        print(f"{i}. {incident['title']}")
        print(f"   Severity: {incident['severity']} | Status: {incident['status']}")
        print(f"   Assignee: {incident['assignee']} | Reporter: {incident['reporter']}")
        print(f"   Affected Systems: {', '.join(incident['affected_systems'])}")
        if incident.get('resolution'):
            print(f"   Resolution: {incident['resolution']}")
        print()
    
    print("Sample data generation completed!")
    print("\nTo populate the actual system:")
    print("1. Start the FastAPI backend: python start-dev.py")
    print("2. Open http://localhost:8000/api/docs")
    print("3. Use the API endpoints to create the sample data")
    print("4. Or integrate this script with the actual API client")

if __name__ == "__main__":
    asyncio.run(generate_sample_data())