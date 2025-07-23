"""
Enhanced Knowledge Sage Implementation
Extends the base Knowledge Sage with vector search, auto-tagging, and quality assurance
"""

import asyncio
import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

# Import base implementation
from libs.four_sages.knowledge.knowledge_sage import KnowledgeSage


class EnhancedKnowledgeSage(KnowledgeSage):
    """Enhanced Knowledge Sage with advanced features"""

    def __init__(self):
        """Initialize Enhanced Knowledge Sage"""
        super().__init__()

        # Vector search components
        self.embeddings_cache = {}
        self.vector_index = {}

        # Auto-tagging components
        self.tag_patterns = self._initialize_tag_patterns()
        self.category_keywords = self._initialize_category_keywords()

        # Quality assurance
        self.quality_weights = {
            "content_length": 0.2,
            "has_structure": 0.2,
            "tag_count": 0.15,
            "title_quality": 0.15,
            "uniqueness": 0.15,
            "completeness": 0.15,
        }

        # Knowledge relationships
        self.knowledge_graph = defaultdict(list)

        # Versioning
        self.version_history = defaultdict(list)

        # Caching
        self.cache_enabled = False
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes default

        # Collaboration references
        self.task_sage = None
        self.incident_sage = None
        self.rag_sage = None

    def _initialize_tag_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for auto-tagging"""
        return {
            "python": ["python", "py", "pip", "django", "flask", "asyncio"],
            "javascript": ["javascript", "js", "node", "react", "vue", "angular"],
            "docker": ["docker", "container", "dockerfile", "compose"],
            "kubernetes": ["kubernetes", "k8s", "kubectl", "pod", "deployment"],
            "testing": ["test", "tdd", "unit test", "integration", "pytest"],
            "security": [
                "security",
                "authentication",
                "authorization",
                "vulnerability",
            ],
            "api": ["api", "rest", "graphql", "endpoint", "http"],
            "database": ["database", "sql", "nosql", "postgresql", "mongodb"],
            "devops": ["devops", "ci/cd", "pipeline", "deployment", "automation"],
            "architecture": [
                "architecture",
                "microservices",
                "design pattern",
                "scalability",
            ],
        }

    def _initialize_category_keywords(self) -> Dict[str, List[str]]:
        """Initialize keywords for category classification"""
        return {
            "development": [
                "code",
                "implement",
                "function",
                "class",
                "method",
                "programming",
            ],
            "architecture": [
                "design",
                "pattern",
                "architecture",
                "structure",
                "system",
            ],
            "best_practices": [
                "best practice",
                "should",
                "recommendation",
                "guideline",
            ],
            "troubleshooting": ["fix", "error", "bug", "issue", "problem", "debug"],
            "documentation": ["document", "guide", "tutorial", "reference", "manual"],
            "tools": ["tool", "utility", "software", "application", "framework"],
            "processes": [
                "process",
                "workflow",
                "methodology",
                "procedure",
                "practice",
            ],
        }

    async def generate_embedding(self, text: str) -> np.ndarray:
        """Generate vector embedding for text"""
        # Simple implementation using hash-based pseudo-embeddings
        # In production, use sentence-transformers or OpenAI embeddings

        # Create deterministic embedding from text
        text_hash = hashlib.sha256(text.encode()).hexdigest()

        # Generate 384-dimensional embedding (sentence-transformers dimension)
        np.random.seed(int(text_hash[:8], 16))
        embedding = np.random.randn(384)

        # Normalize to unit vector
        embedding = embedding / np.linalg.norm(embedding)

        return embedding

    async def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic/vector search"""
        # Generate query embedding
        query_embedding = await self.generate_embedding(query)

        # Calculate similarities with all knowledge entries
        similarities = []

        # Use synchronous sqlite3 connection from parent class
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, title, content, category, tags FROM knowledge_entries"
            )
            entries = cursor.fetchall()

        for entry in entries:
            entry_id, title, content, category, tags = entry

            # Get or generate embedding
            if entry_id not in self.embeddings_cache:
                text = f"{title} {content}"
                self.embeddings_cache[entry_id] = await self.generate_embedding(text)

            # Calculate cosine similarity
            similarity = np.dot(query_embedding, self.embeddings_cache[entry_id])
            similarities.append(
                {
                    "id": entry_id,
                    "title": title,
                    "content": content,
                    "category": category,
                    "tags": json.loads(tags) if tags else [],
                    "similarity_score": float(similarity),
                }
            )

        # Sort by similarity and return top-k
        similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similarities[:top_k]

    async def auto_generate_tags(self, content: str) -> List[str]:
        """Automatically generate tags from content"""
        content_lower = content.lower()
        tags = set()

        # Check for pattern matches
        for tag, patterns in self.tag_patterns.items():
            if any(pattern in content_lower for pattern in patterns):
                tags.add(tag)

        # Extract technical terms
        # Simple implementation - in production use NLP
        technical_terms = re.findall(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b", content)
        for term in technical_terms[:3]:  # Limit to top 3
            if len(term) > 3:  # Skip short terms
                tags.add(term.lower().replace(" ", "-"))

        # Limit total tags
        return list(tags)[:10]

    async def auto_categorize(self, content: str) -> str:
        """Automatically categorize content"""
        content_lower = content.lower()
        category_scores = defaultdict(int)

        # Score each category based on keyword matches
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    category_scores[category] += 1

        # Return category with highest score, default to "documentation"
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        return "documentation"

    async def assess_knowledge_quality(self, knowledge: Dict[str, Any]) -> float:
        """Assess quality of knowledge entry (0-1 score)"""
        scores = {}

        # Content length score
        content_length = len(knowledge.get("content", ""))
        scores["content_length"] = min(content_length / 500, 1.0)  # 500 chars = perfect

        # Structure score (has sections, lists, etc.)
        content = knowledge.get("content", "")
        has_sections = bool(
            re.findall(r"\n\s*[-\d]\.\s", content) or re.findall(r"\n#+\s", content)
        )
        scores["has_structure"] = 1.0 if has_sections else 0.3

        # Tag count score
        tag_count = len(knowledge.get("tags", []))
        scores["tag_count"] = min(tag_count / 5, 1.0)  # 5 tags = perfect

        # Title quality score
        title = knowledge.get("title", "")
        title_words = len(title.split())
        scores["title_quality"] = min(title_words / 5, 1.0) if title_words > 1 else 0.2

        # Uniqueness score (simplified - check if not too generic)
        generic_terms = ["bug", "fix", "update", "change"]
        is_generic = any(term == title.lower() for term in generic_terms)
        scores["uniqueness"] = 0.3 if is_generic else 1.0

        # Completeness score
        has_all_fields = all(
            knowledge.get(field) for field in ["title", "content", "category", "tags"]
        )
        scores["completeness"] = 1.0 if has_all_fields else 0.5

        # Calculate weighted average
        total_score = sum(scores[key] * self.quality_weights[key] for key in scores)
        return round(total_score, 2)

    async def check_duplicate(self, knowledge: Dict[str, Any]) -> Tuple[bool, float]:
        """Check if knowledge is duplicate"""
        # Generate embedding for new knowledge
        new_text = f"{knowledge.get('title', '')} {knowledge.get('content', '')}"
        new_embedding = await self.generate_embedding(new_text)

        # Check against existing entries
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id, title, content FROM knowledge_entries")
            entries = cursor.fetchall()

        max_similarity = 0.0
        for entry_id, title, content in entries:
            # Get or generate embedding
            if entry_id not in self.embeddings_cache:
                text = f"{title} {content}"
                self.embeddings_cache[entry_id] = await self.generate_embedding(text)

            # Calculate similarity
            similarity = np.dot(new_embedding, self.embeddings_cache[entry_id])
            max_similarity = max(max_similarity, similarity)

        # Consider duplicate if similarity > 0.8
        is_duplicate = max_similarity > 0.8
        return is_duplicate, float(max_similarity)

    async def store_knowledge(
        self,
        title: str,
        content: str,
        category: str = None,
        tags: List[str] = None,
        source: str = None,
        expires_in_days: Optional[int] = None,
    ) -> str:
        """Store knowledge with enhanced features"""
        # Auto-generate tags if not provided
        if not tags:
            tags = await self.auto_generate_tags(content)

        # Auto-categorize if not provided
        if not category:
            category = await self.auto_categorize(content)

        # Check for duplicates
        is_duplicate, similarity = await self.check_duplicate(
            {"title": title, "content": content, "category": category, "tags": tags}
        )

        if is_duplicate:
            self.logger.warning(
                f"Potential duplicate detected (similarity: {similarity:.2f})"
            )

        # Store using parent's process_request method
        result = await self.process_request(
            {
                "type": "store_knowledge",
                "title": title,
                "content": content,
                "category": category,
                "tags": tags,
                "source": source or "unknown",
            }
        )

        if not result.get("success"):
            raise Exception(f"Failed to store knowledge: {result.get('error')}")

        knowledge_id = str(result.get("knowledge_id"))

        # Generate and cache embedding
        text = f"{title} {content}"
        self.embeddings_cache[knowledge_id] = await self.generate_embedding(text)

        # Store initial version
        self.version_history[knowledge_id].append(
            {
                "version": 1,
                "timestamp": datetime.now().isoformat(),
                "title": title,
                "content": content,
                "category": category,
                "tags": tags,
            }
        )

        # Set expiration if specified
        if expires_in_days:
            expiration_date = datetime.now() + timedelta(days=expires_in_days)
            await self._set_knowledge_expiration(knowledge_id, expiration_date)

        return knowledge_id

    async def update_knowledge(self, knowledge_id: str, **updates) -> bool:
        """Update knowledge with versioning"""
        # Get current version
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT title, content, category, tags FROM knowledge_entries WHERE id = ?",
                (knowledge_id,),
            )
            current = cursor.fetchone()

        if not current:
            return False

        # Create new version
        title, content, category, tags = current
        new_version = {
            "version": len(self.version_history[knowledge_id]) + 1,
            "timestamp": datetime.now().isoformat(),
            "title": updates.get("title", title),
            "content": updates.get("content", content),
            "category": updates.get("category", category),
            "tags": updates.get("tags", json.loads(tags) if tags else []),
        }

        # Store version
        self.version_history[knowledge_id].append(new_version)

        # Update using parent's process_request
        result = await self.process_request(
            {"type": "update_knowledge", "id": int(knowledge_id), "updates": updates}
        )

        return result.get("success", False)

    async def get_knowledge(self, knowledge_id: str) -> Optional[Dict[str, Any]]:
        """Get knowledge entry by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, title, content, category, tags, created_at, access_count FROM " \
                    "knowledge_entries WHERE id = ?",
                (int(knowledge_id),),
            )
            row = cursor.fetchone()

            if row:
                # Increment access count
                conn.execute(
                    "UPDATE knowledge_entries SET access_count = access_count + 1 WHERE id = ?",
                    (int(knowledge_id),),
                )

                return {
                    "id": str(row[0]),
                    "title": row[1],
                    "content": row[2],
                    "category": row[3],
                    "tags": json.loads(row[4]) if row[4] else [],
                    "created_at": row[5],
                    "access_count": row[6] + 1,
                }
        return None

    async def get_knowledge_history(self, knowledge_id: str) -> List[Dict[str, Any]]:
        """Get version history of knowledge"""
        return self.version_history.get(knowledge_id, [])

    async def create_relationship(
        self, source_id: str, target_id: str, relationship_type: str
    ) -> None:
        """Create relationship between knowledge entries"""
        self.knowledge_graph[source_id].append(
            {
                "target": target_id,
                "type": relationship_type,
                "created": datetime.now().isoformat(),
            }
        )

        # Create reverse relationship for bidirectional navigation
        reverse_type = f"reverse_{relationship_type}"
        self.knowledge_graph[target_id].append(
            {
                "target": source_id,
                "type": reverse_type,
                "created": datetime.now().isoformat(),
            }
        )

    async def get_related_knowledge(self, knowledge_id: str) -> List[Dict[str, Any]]:
        """Get related knowledge entries"""
        relationships = self.knowledge_graph.get(knowledge_id, [])
        related = []

        for rel in relationships:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT id, title, category FROM knowledge_entries WHERE id = ?",
                    (rel["target"],),
                )
                entry = cursor.fetchone()

            if entry:
                related.append(
                    {
                        "id": entry[0],
                        "title": entry[1],
                        "category": entry[2],
                        "relationship_type": rel["type"],
                    }
                )

        return related

    async def batch_import_knowledge(
        self,
        knowledge_batch: List[Dict[str, Any]],
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Import knowledge in batch with progress tracking"""
        results = {
            "total": len(knowledge_batch),
            "successful": 0,
            "failed": 0,
            "errors": [],
        }

        for i, knowledge in enumerate(knowledge_batch):
            try:
                await self.store_knowledge(**knowledge)
                results["successful"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(
                    {"index": i, "error": str(e), "knowledge": knowledge}
                )

            # Report progress
            if progress_callback:
                await progress_callback(i + 1, results["total"])

        return results

    async def is_knowledge_expired(self, knowledge_id: str) -> bool:
        """Check if knowledge has expired"""
        expiration = await self._get_knowledge_expiration(knowledge_id)
        if expiration:
            return datetime.now() > expiration
        return False

    async def _set_knowledge_expiration(
        self, knowledge_id: str, expiration_date: datetime
    ) -> None:
        """Set expiration date for knowledge"""
        # In production, store in database
        # For now, store in memory
        if not hasattr(self, "_expirations"):
            self._expirations = {}
        self._expirations[knowledge_id] = expiration_date

    async def _get_knowledge_expiration(self, knowledge_id: str) -> Optional[datetime]:
        """Get expiration date for knowledge"""
        if hasattr(self, "_expirations"):
            return self._expirations.get(knowledge_id)
        return None

    def set_collaborators(self, task_sage=None, incident_sage=None, rag_sage=None):
        """Set references to other sages for collaboration"""
        self.task_sage = task_sage
        self.incident_sage = incident_sage
        self.rag_sage = rag_sage

    async def get_knowledge_for_task(
        self, task_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get relevant knowledge for a task"""
        # Extract task description
        task_desc = task_context.get("current_task", "")

        # Search for relevant knowledge
        if task_desc:
            return await self.semantic_search(task_desc, top_k=5)
        return []

    async def get_incident_solutions(
        self, incident_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get knowledge about similar incidents and solutions"""
        # Extract error type
        error_type = incident_context.get("error_type", "")

        # Search for troubleshooting knowledge
        query = f"troubleshooting {error_type} solution fix"
        results = await self.semantic_search(query, top_k=10)

        # Filter for troubleshooting category
        return [r for r in results if r.get("category") == "troubleshooting"]

    async def get_knowledge_analytics(self) -> Dict[str, Any]:
        """Get analytics about knowledge base"""
        with sqlite3.connect(self.db_path) as conn:
            # Total entries
            cursor = conn.execute("SELECT COUNT(*) FROM knowledge_entries")
            total = cursor.fetchone()[0]

            # Category distribution
            cursor = conn.execute(
                "SELECT category, COUNT(*) FROM knowledge_entries GROUP BY category"
            )
            categories = cursor.fetchall()
            category_dist = {cat: count for cat, count in categories}

            # Popular tags
            cursor = conn.execute(
                "SELECT tags FROM knowledge_entries WHERE tags IS NOT NULL"
            )
            all_tags = []
            for (tags_json,) in cursor.fetchall():
                if tags_json:
                    all_tags.extend(json.loads(tags_json))

            tag_counts = Counter(all_tags)
            popular_tags = tag_counts.most_common(10)

            # Access patterns (simplified)
            cursor = conn.execute(
                "SELECT title, access_count FROM knowledge_entries ORDER BY access_count " \
                    "DESC LIMIT 10"
            )
            top_accessed = cursor.fetchall()

        return {
            "total_entries": total,
            "categories_distribution": category_dist,
            "popular_tags": popular_tags,
            "access_patterns": [
                {"title": title, "count": count} for title, count in top_accessed
            ],
        }

    async def export_knowledge(self, format: str = "json") -> str:
        """Export knowledge base in different formats"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, title, content, category, tags FROM knowledge_entries"
            )
            entries = cursor.fetchall()

        knowledge_list = []
        for entry_id, title, content, category, tags in entries:
            knowledge_list.append(
                {
                    "id": entry_id,
                    "title": title,
                    "content": content,
                    "category": category,
                    "tags": json.loads(tags) if tags else [],
                }
            )

        if format == "json":
            return json.dumps(knowledge_list, indent=2)
        elif format == "markdown":
            md_content = "# Knowledge Base Export\n\n"
            for k in knowledge_list:
                md_content += f"## {k['title']}\n\n"
                md_content += f"**Category:** {k['category']}\n"
                md_content += f"**Tags:** {', '.join(k['tags'])}\n\n"
                md_content += f"{k['content']}\n\n---\n\n"
            return md_content
        else:
            raise ValueError(f"Unsupported format: {format}")

    def enable_caching(self, ttl_seconds: int = 300):
        """Enable caching with TTL"""
        self.cache_enabled = True
        self.cache_ttl = ttl_seconds
        self.cache = {}
        self.cache_timestamps = {}

    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if not self.cache_enabled:
            return None

        if key in self.cache:
            timestamp = self.cache_timestamps.get(key, 0)
            if datetime.now().timestamp() - timestamp < self.cache_ttl:
                return self.cache[key]
            else:
                # Expired, remove from cache
                del self.cache[key]
                del self.cache_timestamps[key]

        return None

    async def _set_cache(self, key: str, value: Any):
        """Set value in cache"""
        if self.cache_enabled:
            self.cache[key] = value
            self.cache_timestamps[key] = datetime.now().timestamp()
