#!/usr/bin/env python3
"""
Magic Grimoire Database System
魔法書データベースシステム - PostgreSQL + pgvector実装
"""

import os
import sys
import json
import uuid
import logging
import asyncio
import asyncpg
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
from enum import Enum

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

class SpellType(Enum):
    """呪文種別"""
    KNOWLEDGE = "knowledge"          # 知識系
    PROCEDURE = "procedure"          # 手順系
    CONFIGURATION = "configuration" # 設定系
    TEMPLATE = "template"           # テンプレート系
    REFERENCE = "reference"         # 参照系

class MagicSchool(Enum):
    """魔法学派（4賢者対応）"""
    KNOWLEDGE_SAGE = "knowledge_sage"     # ナレッジ賢者
    TASK_ORACLE = "task_oracle"           # タスク賢者
    CRISIS_SAGE = "crisis_sage"           # インシデント賢者
    SEARCH_MYSTIC = "search_mystic"       # RAG賢者

class EvolutionType(Enum):
    """昇華種別"""
    ENHANCE = "enhance"        # 強化
    MERGE = "merge"           # 統合
    SPLIT = "split"           # 分割
    REFACTOR = "refactor"     # リファクタリング
    DEPRECATE = "deprecate"   # 非推奨化

@dataclass
class SpellMetadata:
    """呪文メタデータ"""
    id: str
    spell_name: str
    content: str
    spell_type: SpellType
    magic_school: MagicSchool
    tags: List[str]
    power_level: int
    casting_frequency: int
    last_cast_at: Optional[datetime]
    is_eternal: bool
    evolution_history: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    version: int

class GrimoireDatabase:
    """魔法書データベース管理システム"""
    
    def __init__(self, database_url: Optional[str] = None):
        """初期化"""
        self.database_url = database_url or os.getenv(
            'GRIMOIRE_DATABASE_URL', 
            'postgresql://postgres:password@localhost:5432/ai_company_grimoire'
        )
        self.connection_pool = None
        logger.info("🔮 Grimoire Database System initialized")
    
    async def initialize(self) -> bool:
        """データベース初期化"""
        try:
            # 接続プール作成
            self.connection_pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            
            # 必要な拡張とスキーマを作成
            await self._setup_database()
            
            logger.info("✅ Grimoire Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False
    
    async def _setup_database(self):
        """データベースセットアップ"""
        async with self.connection_pool.acquire() as conn:
            # pgvector拡張の有効化
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
            
            # メイン魔法書テーブル
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_grimoire (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                spell_name VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                content_vector vector(1536),
                spell_type VARCHAR(50) NOT NULL,
                magic_school VARCHAR(50) NOT NULL,
                tags TEXT[] DEFAULT '{}',
                power_level INTEGER DEFAULT 1 CHECK (power_level >= 1 AND power_level <= 10),
                casting_frequency INTEGER DEFAULT 0,
                last_cast_at TIMESTAMP WITH TIME ZONE,
                is_eternal BOOLEAN DEFAULT FALSE,
                evolution_history JSONB DEFAULT '[]',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                version INTEGER DEFAULT 1,
                file_path VARCHAR(500),
                checksum VARCHAR(64)
            )
            """)
            
            # 呪文昇華履歴テーブル
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS spell_evolution (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                original_spell_id UUID REFERENCES knowledge_grimoire(id),
                evolved_spell_id UUID REFERENCES knowledge_grimoire(id),
                evolution_type VARCHAR(50) NOT NULL,
                evolution_reason TEXT,
                confidence_score FLOAT DEFAULT 0.0,
                evolved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                evolved_by VARCHAR(100),
                metadata JSONB DEFAULT '{}'
            )
            """)
            
            # グランドエルダー解呪許可テーブル
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS grand_elder_permissions (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                spell_id UUID REFERENCES knowledge_grimoire(id),
                permission_type VARCHAR(50) NOT NULL,
                request_reason TEXT NOT NULL,
                impact_analysis JSONB,
                requested_by VARCHAR(100) NOT NULL,
                requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                approved_by VARCHAR(100),
                approved_at TIMESTAMP WITH TIME ZONE,
                rejected_at TIMESTAMP WITH TIME ZONE,
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'executed')),
                grand_elder_note TEXT,
                sage_reviews JSONB DEFAULT '[]'
            )
            """)
            
            # インデックス作成
            await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_grimoire_vector 
            ON knowledge_grimoire USING hnsw (content_vector vector_cosine_ops)
            """)
            
            await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_grimoire_tags 
            ON knowledge_grimoire USING gin(tags)
            """)
            
            await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_grimoire_school_type 
            ON knowledge_grimoire (magic_school, spell_type)
            """)
            
            await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_grimoire_eternal 
            ON knowledge_grimoire (is_eternal, power_level DESC)
            """)
            
            # トリガー関数: updated_at自動更新
            await conn.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql'
            """)
            
            await conn.execute("""
            DROP TRIGGER IF EXISTS update_grimoire_updated_at ON knowledge_grimoire;
            CREATE TRIGGER update_grimoire_updated_at
                BEFORE UPDATE ON knowledge_grimoire
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
            """)
    
    async def create_spell(self, spell_data: Dict[str, Any], content_vector: Optional[List[float]] = None) -> str:
        """新しい呪文を作成"""
        async with self.connection_pool.acquire() as conn:
            spell_id = str(uuid.uuid4())
            
            # ベクトルデータの準備（PostgreSQL vector型用）
            if content_vector:
                vector_data = f"[{','.join(map(str, content_vector))}]"
            else:
                vector_data = f"[{','.join(['0.0'] * 1536)}]"
            
            await conn.execute("""
            INSERT INTO knowledge_grimoire (
                id, spell_name, content, content_vector, spell_type, magic_school,
                tags, power_level, is_eternal, file_path
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, 
            spell_id,
            spell_data['spell_name'],
            spell_data['content'],
            vector_data,
            spell_data.get('spell_type', SpellType.KNOWLEDGE.value),
            spell_data.get('magic_school', MagicSchool.KNOWLEDGE_SAGE.value),
            spell_data.get('tags', []),
            spell_data.get('power_level', 1),
            spell_data.get('is_eternal', False),
            spell_data.get('file_path')
            )
            
            logger.info(f"🔮 New spell created: {spell_id} - {spell_data['spell_name']}")
            return spell_id
    
    async def search_spells_by_vector(self, query_vector: List[float], limit: int = 10, 
                                    filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """ベクトル類似度による呪文検索"""
        async with self.connection_pool.acquire() as conn:
            base_query = """
            SELECT id, spell_name, content, spell_type, magic_school, tags,
                   power_level, casting_frequency, is_eternal, created_at,
                   (content_vector <=> $1) as similarity_distance
            FROM knowledge_grimoire
            """
            
            params = [query_vector]
            where_conditions = []
            param_count = 1
            
            # フィルター条件の追加
            if filters:
                if 'magic_school' in filters:
                    param_count += 1
                    where_conditions.append(f"magic_school = ${param_count}")
                    params.append(filters['magic_school'])
                
                if 'spell_type' in filters:
                    param_count += 1
                    where_conditions.append(f"spell_type = ${param_count}")
                    params.append(filters['spell_type'])
                
                if 'min_power_level' in filters:
                    param_count += 1
                    where_conditions.append(f"power_level >= ${param_count}")
                    params.append(filters['min_power_level'])
                
                if 'is_eternal' in filters:
                    param_count += 1
                    where_conditions.append(f"is_eternal = ${param_count}")
                    params.append(filters['is_eternal'])
                
                if 'tags' in filters:
                    param_count += 1
                    where_conditions.append(f"tags && ${param_count}")
                    params.append(filters['tags'])
            
            if where_conditions:
                base_query += " WHERE " + " AND ".join(where_conditions)
            
            base_query += f" ORDER BY similarity_distance ASC LIMIT ${param_count + 1}"
            params.append(limit)
            
            rows = await conn.fetch(base_query, *params)
            
            return [dict(row) for row in rows]
    
    async def evolve_spell(self, original_id: str, evolved_data: Dict[str, Any], 
                         evolution_type: EvolutionType, reason: str) -> str:
        """呪文昇華"""
        async with self.connection_pool.acquire() as conn:
            async with conn.transaction():
                # 元呪文を永続化
                await conn.execute("""
                UPDATE knowledge_grimoire 
                SET is_eternal = TRUE, updated_at = NOW()
                WHERE id = $1
                """, original_id)
                
                # 新しい進化呪文を作成
                evolved_id = await self.create_spell(evolved_data)
                
                # 昇華履歴を記録
                await conn.execute("""
                INSERT INTO spell_evolution (
                    original_spell_id, evolved_spell_id, evolution_type, 
                    evolution_reason, evolved_by
                ) VALUES ($1, $2, $3, $4, $5)
                """, original_id, evolved_id, evolution_type.value, reason, "system")
                
                # 元呪文の昇華履歴を更新
                evolution_entry = {
                    'evolved_to': evolved_id,
                    'evolution_type': evolution_type.value,
                    'reason': reason,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
                await conn.execute("""
                UPDATE knowledge_grimoire 
                SET evolution_history = evolution_history || $1::jsonb
                WHERE id = $2
                """, json.dumps([evolution_entry]), original_id)
                
                logger.info(f"🔄 Spell evolved: {original_id} -> {evolved_id} ({evolution_type.value})")
                return evolved_id
    
    async def request_spell_dispel(self, spell_id: str, reason: str, requester: str) -> str:
        """解呪許可申請"""
        async with self.connection_pool.acquire() as conn:
            permission_id = str(uuid.uuid4())
            
            # 影響分析を実行
            impact_analysis = await self._analyze_spell_impact(spell_id)
            
            await conn.execute("""
            INSERT INTO grand_elder_permissions (
                id, spell_id, permission_type, request_reason, 
                impact_analysis, requested_by
            ) VALUES ($1, $2, $3, $4, $5, $6)
            """, permission_id, spell_id, "dispel", reason, 
            json.dumps(impact_analysis), requester)
            
            logger.info(f"🏛️ Dispel permission requested: {permission_id} for spell {spell_id}")
            return permission_id
    
    async def _analyze_spell_impact(self, spell_id: str) -> Dict[str, Any]:
        """呪文影響分析"""
        async with self.connection_pool.acquire() as conn:
            # 基本情報取得
            spell_info = await conn.fetchrow("""
            SELECT spell_name, power_level, casting_frequency, is_eternal,
                   array_length(tags, 1) as tag_count
            FROM knowledge_grimoire WHERE id = $1
            """, spell_id)
            
            # 昇華関係の確認
            evolution_count = await conn.fetchval("""
            SELECT COUNT(*) FROM spell_evolution 
            WHERE original_spell_id = $1 OR evolved_spell_id = $1
            """, spell_id)
            
            # 関連呪文の確認（類似度ベース）
            related_spells = await conn.fetchval("""
            SELECT COUNT(*) FROM knowledge_grimoire k1, knowledge_grimoire k2
            WHERE k1.id = $1 AND k2.id != $1 
            AND (k1.content_vector <=> k2.content_vector) < 0.3
            """, spell_id)
            
            risk_level = "low"
            if spell_info['is_eternal'] or spell_info['power_level'] >= 8:
                risk_level = "critical"
            elif spell_info['casting_frequency'] > 50 or evolution_count > 0:
                risk_level = "high"
            elif related_spells > 5:
                risk_level = "medium"
            
            return {
                'risk_level': risk_level,
                'casting_frequency': spell_info['casting_frequency'],
                'power_level': spell_info['power_level'],
                'is_eternal': spell_info['is_eternal'],
                'evolution_count': evolution_count,
                'related_spells_count': related_spells,
                'analysis_timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def update_casting_frequency(self, spell_id: str):
        """詠唱回数更新"""
        async with self.connection_pool.acquire() as conn:
            await conn.execute("""
            UPDATE knowledge_grimoire 
            SET casting_frequency = casting_frequency + 1,
                last_cast_at = NOW()
            WHERE id = $1
            """, spell_id)
    
    async def get_spell_by_id(self, spell_id: str) -> Optional[Dict[str, Any]]:
        """ID による呪文取得"""
        async with self.connection_pool.acquire() as conn:
            row = await conn.fetchrow("""
            SELECT * FROM knowledge_grimoire WHERE id = $1
            """, spell_id)
            
            return dict(row) if row else None
    
    async def get_evolution_history(self, spell_id: str) -> List[Dict[str, Any]]:
        """昇華履歴取得"""
        async with self.connection_pool.acquire() as conn:
            rows = await conn.fetch("""
            SELECT se.*, 
                   orig.spell_name as original_name,
                   evol.spell_name as evolved_name
            FROM spell_evolution se
            LEFT JOIN knowledge_grimoire orig ON se.original_spell_id = orig.id
            LEFT JOIN knowledge_grimoire evol ON se.evolved_spell_id = evol.id
            WHERE se.original_spell_id = $1 OR se.evolved_spell_id = $1
            ORDER BY se.evolved_at DESC
            """, spell_id)
            
            return [dict(row) for row in rows]
    
    async def close(self):
        """接続クローズ"""
        if self.connection_pool:
            await self.connection_pool.close()
            logger.info("🔮 Grimoire Database connection closed")

# 使用例とテスト用関数
async def test_grimoire_database():
    """テスト実行"""
    db = GrimoireDatabase()
    
    try:
        # 初期化
        await db.initialize()
        
        # サンプル呪文作成
        sample_spell = {
            'spell_name': 'Claude CLI TDD Guide',
            'content': 'ClaudeでTDD開発を行うための完全ガイド...',
            'spell_type': SpellType.KNOWLEDGE.value,
            'magic_school': MagicSchool.KNOWLEDGE_SAGE.value,
            'tags': ['tdd', 'claude', 'development'],
            'power_level': 8,
            'is_eternal': True
        }
        
        spell_id = await db.create_spell(sample_spell)
        print(f"✅ Test spell created: {spell_id}")
        
        # 呪文取得テスト
        retrieved_spell = await db.get_spell_by_id(spell_id)
        print(f"✅ Spell retrieved: {retrieved_spell['spell_name']}")
        
        # 解呪申請テスト
        permission_id = await db.request_spell_dispel(
            spell_id, 
            "Testing dispel request", 
            "test_user"
        )
        print(f"✅ Dispel permission requested: {permission_id}")
        
    finally:
        await db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_grimoire_database())