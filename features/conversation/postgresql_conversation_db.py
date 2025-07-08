#!/usr/bin/env python3
"""
PostgreSQL統合会話管理データベース - AI Company Unified System
"""

import asyncio
import asyncpg
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import os

logger = logging.getLogger(__name__)

class PostgreSQLConversationDB:
    """PostgreSQL統合会話管理"""
    
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
    
    async def create_conversation(self, task_id: str, initial_context: Dict = None) -> str:
        """新規会話作成"""
        conversation_id = f"conv_{task_id}"
        context = initial_context or {}
        
        try:
            await self.init_pool()
            
            # コンテキストメタデータ構築
            context_metadata = {
                'task_id': task_id,
                'state': 'active',
                'initial_context': context,
                'created_by': 'conversation_system',
                'conversation_type': 'task_based'
            }
            
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO unified_conversations (
                        conversation_id, session_id, user_message, ai_response,
                        timestamp, context, sage_consulted
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (conversation_id) DO UPDATE SET
                        context = EXCLUDED.context,
                        timestamp = EXCLUDED.timestamp
                """, 
                conversation_id,
                task_id,  # session_id
                f"Conversation started for task: {task_id}",  # user_message
                "Conversation initialized",  # ai_response
                datetime.now(),  # timestamp
                json.dumps(context_metadata),  # context
                'conversation_sage'  # sage_consulted
                )
            
            logger.info(f"PostgreSQL 会話作成: {conversation_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"PostgreSQL 会話作成失敗: {e}")
            return conversation_id  # 既存の場合は返す
    
    async def add_message(self, conversation_id: str, sender: str, content: str, 
                         message_type: str = 'text', metadata: Dict = None) -> int:
        """メッセージ追加"""
        try:
            await self.init_pool()
            
            # メッセージメタデータ構築
            msg_metadata = {
                'sender': sender,
                'message_type': message_type,
                'metadata': metadata or {},
                'timestamp': datetime.now().isoformat()
            }
            
            async with self.pool.acquire() as conn:
                # 新しいメッセージとして追加
                result = await conn.fetchrow("""
                    INSERT INTO unified_conversations (
                        conversation_id, session_id, user_message, ai_response,
                        timestamp, context, sage_consulted
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """, 
                conversation_id,
                conversation_id,  # session_id
                content if sender == 'user' else '',  # user_message
                content if sender != 'user' else '',  # ai_response
                datetime.now(),  # timestamp
                json.dumps(msg_metadata),  # context
                sender  # sage_consulted
                )
            
            message_id = result['id'] if result else 0
            logger.info(f"PostgreSQL メッセージ追加: {conversation_id} - {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"PostgreSQL メッセージ追加失敗: {e}")
            return 0
    
    async def update_state(self, conversation_id: str, new_state: str) -> bool:
        """会話状態更新"""
        try:
            await self.init_pool()
            
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE unified_conversations 
                    SET context = jsonb_set(context, '{state}', $1, true),
                        timestamp = $2
                    WHERE conversation_id = $3
                """, json.dumps(new_state), datetime.now(), conversation_id)
            
            affected = int(result.split()[-1]) if result else 0
            success = affected > 0
            
            if success:
                logger.info(f"PostgreSQL 会話状態更新: {conversation_id} -> {new_state}")
            
            return success
            
        except Exception as e:
            logger.error(f"PostgreSQL 会話状態更新失敗: {e}")
            return False
    
    async def get_messages(self, conversation_id: str, limit: int = 100) -> List[Dict]:
        """メッセージ履歴取得"""
        try:
            await self.init_pool()
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        id, conversation_id, session_id, user_message, ai_response,
                        timestamp, context, sage_consulted
                    FROM unified_conversations
                    WHERE conversation_id = $1
                    ORDER BY timestamp ASC
                    LIMIT $2
                """, conversation_id, limit)
            
            messages = []
            for row in rows:
                msg = dict(row)
                if msg['context']:
                    msg['context'] = json.loads(msg['context'])
                
                # SQLite互換形式に変換
                messages.append({
                    'message_id': msg['id'],
                    'conversation_id': msg['conversation_id'],
                    'sender': msg['context'].get('sender', 'system'),
                    'content': msg['user_message'] or msg['ai_response'],
                    'message_type': msg['context'].get('message_type', 'text'),
                    'metadata': msg['context'].get('metadata', {}),
                    'timestamp': msg['timestamp']
                })
            
            return messages
            
        except Exception as e:
            logger.error(f"PostgreSQL メッセージ履歴取得失敗: {e}")
            return []
    
    async def get_active_conversations(self) -> List[Dict]:
        """アクティブな会話一覧"""
        try:
            await self.init_pool()
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        conversation_id, session_id as task_id,
                        context, timestamp as updated_at,
                        COUNT(*) as message_count
                    FROM unified_conversations
                    WHERE context->>'state' IN ('active', 'waiting_user')
                       OR context->>'state' IS NULL
                    GROUP BY conversation_id, session_id, context, timestamp
                    ORDER BY timestamp DESC
                """)
            
            conversations = []
            for row in rows:
                conv = dict(row)
                if conv['context']:
                    context = json.loads(conv['context'])
                    conv['context'] = context.get('initial_context', {})
                    conv['state'] = context.get('state', 'active')
                else:
                    conv['context'] = {}
                    conv['state'] = 'active'
                
                conv['created_at'] = conv['updated_at']
                conversations.append(conv)
            
            return conversations
            
        except Exception as e:
            logger.error(f"PostgreSQL アクティブ会話取得失敗: {e}")
            return []

# 互換性のためのラッパー関数
class ConversationDBCompat:
    """SQLite互換性ラッパー"""
    
    def __init__(self, db_path=None):
        self.pg_db = PostgreSQLConversationDB()
        logger.info("PostgreSQL統合会話管理システムに移行済み")
    
    def init_db(self):
        """データベース初期化（互換性のため）"""
        pass  # PostgreSQLは既に初期化済み
    
    def create_conversation(self, task_id: str, initial_context: Dict = None) -> str:
        """非同期メソッドの同期ラッパー"""
        return asyncio.run(self.pg_db.create_conversation(task_id, initial_context))
    
    def add_message(self, conversation_id: str, sender: str, content: str, 
                   message_type: str = 'text', metadata: Dict = None) -> int:
        """非同期メソッドの同期ラッパー"""
        return asyncio.run(self.pg_db.add_message(
            conversation_id, sender, content, message_type, metadata
        ))
    
    def update_state(self, conversation_id: str, new_state: str) -> bool:
        """非同期メソッドの同期ラッパー"""
        return asyncio.run(self.pg_db.update_state(conversation_id, new_state))
    
    def get_messages(self, conversation_id: str, limit: int = 100) -> List[Dict]:
        """非同期メソッドの同期ラッパー"""
        return asyncio.run(self.pg_db.get_messages(conversation_id, limit))
    
    def get_active_conversations(self) -> List[Dict]:
        """非同期メソッドの同期ラッパー"""
        return asyncio.run(self.pg_db.get_active_conversations())

# 後方互換性のためのエイリアス
ConversationDB = ConversationDBCompat