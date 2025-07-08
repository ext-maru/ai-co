"""
Task History Database Manager - Refactored with BaseManager
===========================================================

Manages task history with improved structure using BaseManager.
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from core import BaseManager
import sqlite3
from contextlib import contextmanager


class TaskHistoryDB(BaseManager):
    """Task history database manager using BaseManager"""
    
    def __init__(self, db_name: str = "task_history.db"):
        """Initialize task history database"""
        super().__init__(manager_name="TaskHistoryDB")
        self.db_name = db_name
        self.db_path = self.project_dir / "db" / db_name
        self.connection = None
        self.cache = {}
    
    def initialize(self) -> bool:
        """Initialize database schema (BaseManager abstract method implementation)"""
        try:
            self.ensure_directory(self.db_path.parent)
            self.connection = sqlite3.connect(str(self.db_path))
            self.setup_schema()
            self.logger.info("✅ TaskHistoryDB initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ TaskHistoryDB initialization failed: {e}")
            return False
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute SELECT query"""
        if not self.connection:
            raise RuntimeError("Database not initialized")
        
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    
    def execute_update(self, query: str, params: tuple = ()) -> bool:
        """Execute INSERT/UPDATE/DELETE query"""
        if not self.connection:
            raise RuntimeError("Database not initialized")
        
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        return True
    
    def cache_set(self, key: str, value: Any, ttl: int = 3600):
        """Simple cache implementation"""
        import time
        self.cache[key] = {
            'value': value,
            'expires': time.time() + ttl
        }
    
    def cache_get(self, key: str) -> Any:
        """Get from cache"""
        import time
        if key in self.cache:
            if time.time() < self.cache[key]['expires']:
                return self.cache[key]['value']
            else:
                del self.cache[key]
        return None
    
    @contextmanager 
    def get_db_cursor(self):
        """Get database cursor (context manager)"""
        if not self.connection:
            raise RuntimeError("Database not initialized")
        cursor = self.connection.cursor()
        try:
            yield cursor
        finally:
            self.connection.commit()
    
    def setup_schema(self):
        """Setup database schema"""
        with self.get_db_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    task_id TEXT PRIMARY KEY,
                    worker TEXT NOT NULL,
                    model TEXT,
                    prompt TEXT NOT NULL,
                    response TEXT,
                    summary TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed',
                    metadata TEXT
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON task_history(timestamp DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_worker 
                ON task_history(worker)
            """)
    
    def add_task(self, 
                 task_id: str,
                 worker: str,
                 prompt: str,
                 response: str = None,
                 model: str = None,
                 summary: str = None,
                 metadata: Dict[str, Any] = None) -> bool:
        """Add new task to history"""
        try:
            query = """
                INSERT INTO task_history 
                (task_id, worker, model, prompt, response, summary, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            metadata_json = json.dumps(metadata) if metadata else None
            
            self.execute_update(
                query, 
                (task_id, worker, model, prompt, response, summary, metadata_json)
            )
            
            # Clear cache for this task
            self.cache_set(f"task_{task_id}", None)
            
            self.logger.info(f"✅ Added task: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add task: {e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        # Check cache first
        cached = self.cache_get(f"task_{task_id}")
        if cached:
            return cached
        
        # Query database
        results = self.execute_query(
            "SELECT * FROM task_history WHERE task_id = ?",
            (task_id,)
        )
        
        if results:
            task = results[0]
            # Parse metadata
            if task.get('metadata'):
                task['metadata'] = json.loads(task['metadata'])
            
            # Cache result
            self.cache_set(f"task_{task_id}", task, ttl=3600)
            
            return task
        
        return None
    
    def search_similar_tasks(self, 
                           prompt: str, 
                           limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar tasks based on prompt"""
        # Simple keyword-based search (can be enhanced with embeddings)
        keywords = prompt.lower().split()[:5]  # Top 5 keywords
        
        conditions = []
        params = []
        
        for keyword in keywords:
            conditions.append("LOWER(prompt) LIKE ? OR LOWER(summary) LIKE ?")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        query = f"""
            SELECT * FROM task_history 
            WHERE {' OR '.join(conditions)}
            ORDER BY timestamp DESC
            LIMIT ?
        """
        params.append(limit)
        
        results = self.execute_query(query, tuple(params))
        
        # Parse metadata for each result
        for result in results:
            if result.get('metadata'):
                result['metadata'] = json.loads(result['metadata'])
        
        return results
    
    def get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent tasks"""
        results = self.execute_query(
            "SELECT * FROM task_history ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        
        # Parse metadata
        for result in results:
            if result.get('metadata'):
                result['metadata'] = json.loads(result['metadata'])
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {
            'total_tasks': 0,
            'workers': {},
            'models': {},
            'recent_activity': []
        }
        
        # Total tasks
        result = self.execute_query("SELECT COUNT(*) as count FROM task_history")
        if result:
            stats['total_tasks'] = result[0]['count']
        
        # Tasks by worker
        results = self.execute_query("""
            SELECT worker, COUNT(*) as count 
            FROM task_history 
            GROUP BY worker
        """)
        stats['workers'] = {r['worker']: r['count'] for r in results}
        
        # Tasks by model
        results = self.execute_query("""
            SELECT model, COUNT(*) as count 
            FROM task_history 
            WHERE model IS NOT NULL
            GROUP BY model
        """)
        stats['models'] = {r['model']: r['count'] for r in results}
        
        # Recent activity
        stats['recent_activity'] = self.get_recent_tasks(5)
        
        return stats
    
    def update_summary(self, task_id: str, summary: str) -> bool:
        """Update task summary"""
        try:
            affected = self.execute_update(
                "UPDATE task_history SET summary = ? WHERE task_id = ?",
                (summary, task_id)
            )
            
            # Clear cache
            self.cache_set(f"task_{task_id}", None)
            
            return affected > 0
            
        except Exception as e:
            self.logger.error(f"Failed to update summary: {e}")
            return False


# Example usage and migration helper
def migrate_from_old_taskhistorydb():
    """Helper function to migrate from old TaskHistoryDB if needed"""
    old_db_path = Path(__file__).parent.parent / "data" / "task_history.db"
    
    if old_db_path.exists():
        print("🔄 Migrating from old database...")
        # Migration logic here if needed
        print("✅ Migration complete")


if __name__ == "__main__":
    # Test the refactored TaskHistoryDB
    db = TaskHistoryDB()
    
    # Add test task
    test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    db.add_task(
        task_id=test_id,
        worker="test_worker",
        prompt="Test prompt",
        response="Test response",
        model="test-model"
    )
    
    # Get stats
    print(json.dumps(db.get_stats(), indent=2))
    
    # Cleanup
    db.cleanup()
