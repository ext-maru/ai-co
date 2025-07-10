#!/usr/bin/env python3
"""
PostgreSQL統合タスク履歴管理 - Elders Guild Unified System
"""

import asyncio
import asyncpg
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import os

logger = logging.getLogger(__name__)

class PostgreSQLTaskHistory:
    """PostgreSQL統合タスク履歴管理"""
    
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv('GRIMOIRE_DATABASE_URL', 
                                         'postgresql://aicompany@localhost:5432/ai_company_grimoire')
        self.pool = None
    
    async def init_pool(self):
        """コネクションプール初期化"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(self.db_url)
    
    async def close_pool(self):
        """コネクションプール終了"""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    async def save_task(self, task_id: str, worker: str, model: str, prompt: str, 
                       response: str, summary: str = None, status: str = "completed", 
                       task_type: str = "general") -> bool:
        """タスク履歴を保存"""
        try:
            await self.init_pool()
            
            # メタデータ構築
            metadata = {
                'worker': worker,
                'model': model,
                'task_type': task_type,
                'original_prompt': prompt,
                'response_length': len(response),
                'has_summary': summary is not None
            }
            
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO unified_tasks (
                        task_id, title, description, status, priority, 
                        created_at, updated_at, metadata, assigned_sage
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (task_id) DO UPDATE SET
                        description = EXCLUDED.description,
                        status = EXCLUDED.status,
                        updated_at = EXCLUDED.updated_at,
                        metadata = EXCLUDED.metadata
                """, 
                task_id, 
                summary or f"Task {task_id}",  # title
                response,  # description
                status,
                'medium',  # priority
                datetime.now(),  # created_at
                datetime.now(),  # updated_at
                json.dumps(metadata),  # metadata
                worker  # assigned_sage
                )
            
            logger.info(f"PostgreSQL タスク履歴保存成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL タスク履歴保存失敗: {e}")
            return False
    
    async def update_summary(self, task_id: str, summary: str) -> bool:
        """要約を更新"""
        try:
            await self.init_pool()
            
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE unified_tasks 
                    SET title = $1, updated_at = $2
                    WHERE task_id = $3
                """, summary, datetime.now(), task_id)
            
            if result == 'UPDATE 1':
                logger.info(f"PostgreSQL 要約更新成功: {task_id}")
                return True
            else:
                logger.warning(f"PostgreSQL 要約更新対象なし: {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"PostgreSQL 要約更新失敗: {e}")
            return False
    
    async def search_tasks(self, keyword: str = None, worker: str = None, limit: int = 10) -> List[Dict]:
        """タスク検索"""
        try:
            await self.init_pool()
            
            query = """
                SELECT 
                    task_id, title, description, status, priority,
                    assigned_sage, created_at, updated_at, metadata
                FROM unified_tasks 
                WHERE 1=1
            """
            params = []
            
            if keyword:
                query += " AND (title ILIKE $" + str(len(params) + 1) + " OR description ILIKE $" + str(len(params) + 2) + ")"
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            
            if worker:
                query += " AND assigned_sage = $" + str(len(params) + 1)
                params.append(worker)
            
            query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
            params.append(limit)
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
            
            tasks = []
            for row in rows:
                task = dict(row)
                if task['metadata']:
                    task['metadata'] = json.loads(task['metadata'])
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"PostgreSQL タスク検索失敗: {e}")
            return []
    
    async def get_recent_tasks(self, limit: int = 10) -> List[Dict]:
        """最新タスク取得"""
        try:
            await self.init_pool()
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        task_id, title, description, status, priority,
                        assigned_sage, created_at, updated_at, metadata
                    FROM unified_tasks 
                    ORDER BY created_at DESC 
                    LIMIT $1
                """, limit)
            
            tasks = []
            for row in rows:
                task = dict(row)
                if task['metadata']:
                    task['metadata'] = json.loads(task['metadata'])
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"PostgreSQL 最新タスク取得失敗: {e}")
            return []
    
    async def get_stats(self) -> Dict:
        """統計情報取得"""
        try:
            await self.init_pool()
            
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_tasks,
                        COUNT(DISTINCT assigned_sage) as unique_workers,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks,
                        COUNT(CASE WHEN title != 'Untitled Task' THEN 1 END) as summarized_tasks
                    FROM unified_tasks
                """)
            
            return dict(row) if row else {}
            
        except Exception as e:
            logger.error(f"PostgreSQL 統計情報取得失敗: {e}")
            return {}
    
    async def get_task_by_id(self, task_id: str) -> Optional[Dict]:
        """タスクIDで検索"""
        try:
            await self.init_pool()
            
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT 
                        task_id, title, description, status, priority,
                        assigned_sage, created_at, updated_at, metadata
                    FROM unified_tasks 
                    WHERE task_id = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                """, task_id)
            
            if row:
                task = dict(row)
                if task['metadata']:
                    task['metadata'] = json.loads(task['metadata'])
                return task
            
            return None
            
        except Exception as e:
            logger.error(f"PostgreSQL タスクID検索失敗: {e}")
            return None

# 互換性のためのラッパー関数
class TaskHistoryDBCompat:
    """SQLite互換性ラッパー"""
    
    def __init__(self, db_path=None):
        self.pg_db = PostgreSQLTaskHistory()
        logger.info("PostgreSQL統合タスク履歴システムに移行済み")
    
    def save_task(self, task_id, worker, model, prompt, response, 
                  summary=None, status="completed", task_type="general"):
        """非同期メソッドの同期ラッパー"""
        return asyncio.run(self.pg_db.save_task(
            task_id, worker, model, prompt, response, summary, status, task_type
        ))
    
    def update_summary(self, task_id, summary):
        """非同期メソッドの同期ラッパー"""
        return asyncio.run(self.pg_db.update_summary(task_id, summary))
    
    def search_tasks(self, keyword=None, worker=None, limit=10):
        """非同期メソッドの同期ラッパー"""
        return asyncio.run(self.pg_db.search_tasks(keyword, worker, limit))
    
    def get_recent_tasks(self, limit=10):
        """非同期メソッドの同期ラッパー"""
        return asyncio.run(self.pg_db.get_recent_tasks(limit))
    
    def get_stats(self):
        """非同期メソッドの同期ラッパー"""
        return asyncio.run(self.pg_db.get_stats())
    
    def get_task_by_id(self, task_id):
        """非同期メソッドの同期ラッパー"""
        return asyncio.run(self.pg_db.get_task_by_id(task_id))

# 後方互換性のためのエイリアス
TaskHistoryDB = TaskHistoryDBCompat