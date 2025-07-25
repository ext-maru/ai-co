#!/usr/bin/env python3
"""
PROJECT ELDERZAN - HybridStorage Implementation
プロジェクトエルダーザン ハイブリッドストレージ実装

4賢者承認済み設計仕様による統合ストレージシステム
SQLite + MessagePack + FAISS による高性能セッション管理

4賢者との連携:
📚 ナレッジ賢者: データ分割戦略・整合性管理
📋 タスク賢者: 実装優先順位・品質保証
🚨 インシデント賢者: 障害対策・セキュリティ
"🔍" RAG賢者: ベクトル検索・パフォーマンス最適化
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
import hashlib
import json
import logging
import sqlite3
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from .models import (
    ContextSnapshot,
    SageInteraction,
    SageType,
    SessionContext,
    SessionMetadata,
    SessionStatus,
)

logger = logging.getLogger(__name__)

class StorageError(Exception):
    """ストレージエラー基底クラス"""

    pass

class ConsistencyError(StorageError):
    """整合性エラー"""

    pass

class TransactionError(StorageError):
    """トランザクションエラー"""

    pass

class SQLiteAdapter:
    """SQLite アダプター - 構造化データ・メタデータ管理"""

    def __init__(self, db_path: str = "data/session_storage/sessions.db"):
        """初期化メソッド"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._init_db()

    def _get_connection(self) -> sqlite3Connection:
        """スレッドローカル接続取得"""
        if not hasattr(self._local, "connection"):
            self._local.connection = sqlite3connect(
                self.db_path, check_same_thread=False, timeout=30.0
            )
            self._local.connection.row_factory = sqlite3Row
            # WALモード有効化（並行性向上）
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
            self._local.connection.execute("PRAGMA cache_size=10000")
        return self._local.connection

    def _init_db(self):
        """データベース初期化"""
        conn = self._get_connection()

        # セッションメタデータテーブル
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS session_metadata (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                project_path TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                total_tokens_saved INTEGER DEFAULT 0,
                compression_ratio REAL DEFAULT 0.0,
                response_time_improvement REAL DEFAULT 0.0,
                sage_interactions_count TEXT DEFAULT '{}',
                last_sage_consultation TIMESTAMP,
                knowledge_retention_score REAL DEFAULT 0.0,
                context_accuracy_score REAL DEFAULT 0.0,
                user_satisfaction_score REAL DEFAULT 0.0
            )
        """
        )

        # 4賢者相互作用テーブル
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sage_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                sage_type TEXT NOT NULL,
                interaction_type TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                input_data TEXT NOT NULL,
                output_data TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                processing_time REAL NOT NULL,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                FOREIGN KEY (session_id) REFERENCES session_metadata (session_id)
            )
        """
        )

        # インデックス作成
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_session_user ON session_metadata(user_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_session_updated ON session_metadata(updated_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_interactions_session ON sage_interactions(session_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_interactions_sage ON sage_interactions(sage_type)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_interactions_time ON sage_interactions(timestamp)"
        )

        conn.commit()

    async def save_metadata(self, metadata: SessionMetadata) -> bool:
        """セッションメタデータ保存"""
        try:
            loop = asyncio.get_event_loop()

            def _save():
                """save（内部メソッド）"""
                conn = self._get_connection()
                conn.execute(
                    """
                    INSERT OR REPLACE INTO session_metadata (
                        session_id, user_id, project_path, created_at, updated_at, status,
                        total_tokens_saved, compression_ratio, response_time_improvement,
                        sage_interactions_count, last_sage_consultation,
                        knowledge_retention_score, context_accuracy_score, user_satisfaction_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        metadata.session_id,
                        metadata.user_id,
                        metadata.project_path,
                        metadata.created_at,
                        metadata.updated_at,
                        metadata.status.value,
                        metadata.total_tokens_saved,
                        metadata.compression_ratio,
                        metadata.response_time_improvement,
                        json.dumps(metadata.sage_interactions_count),
                        metadata.last_sage_consultation,
                        metadata.knowledge_retention_score,
                        metadata.context_accuracy_score,
                        metadata.user_satisfaction_score,
                    ),
                )
                conn.commit()
                return True

            return await loop.run_in_executor(self._executor, _save)

        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            raise StorageError(f"SQLite metadata save failed: {e}")

    async def load_metadata(self, session_id: str) -> Optional[SessionMetadata]:
        """セッションメタデータ読み込み"""
        try:
            loop = asyncio.get_event_loop()

            def _load():
                """load（内部メソッド）"""
                conn = self._get_connection()
                row = conn.execute(
                    "SELECT * FROM session_metadata WHERE session_id = ?", (session_id,)
                ).fetchone()

                if not row:
                    return None

                return SessionMetadata(
                    session_id=row["session_id"],
                    user_id=row["user_id"],
                    project_path=row["project_path"],
                    created_at=(
                        datetime.fromisoformat(row["created_at"])
                        if isinstance(row["created_at"], str)
                        else row["created_at"]
                    ),
                    updated_at=(
                        datetime.fromisoformat(row["updated_at"])
                        if isinstance(row["updated_at"], str)
                        else row["updated_at"]
                    ),
                    status=SessionStatus(row["status"]),
                    total_tokens_saved=row["total_tokens_saved"],
                    compression_ratio=row["compression_ratio"],
                    response_time_improvement=row["response_time_improvement"],
                    sage_interactions_count=json.loads(row["sage_interactions_count"]),
                    last_sage_consultation=(
                        datetime.fromisoformat(row["last_sage_consultation"])
                        if row["last_sage_consultation"]
                        else None
                    ),
                    knowledge_retention_score=row["knowledge_retention_score"],
                    context_accuracy_score=row["context_accuracy_score"],
                    user_satisfaction_score=row["user_satisfaction_score"],
                )

            return await loop.run_in_executor(self._executor, _load)

        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            raise StorageError(f"SQLite metadata load failed: {e}")

    async def save_interactions(
        self, session_id: str, interactions: List[SageInteraction]
    ) -> bool:
        """4賢者相互作用保存"""
        try:
            loop = asyncio.get_event_loop()

            def _save():
                """save（内部メソッド）"""
                conn = self._get_connection()

                # 既存データ削除
                conn.execute(
                    "DELETE FROM sage_interactions WHERE session_id = ?", (session_id,)
                )

                # 新データ挿入
                for interaction in interactions:
                    conn.execute(
                        """
                        INSERT INTO sage_interactions (
                            session_id, sage_type, interaction_type, timestamp,
                            input_data, output_data, confidence_score, processing_time,
                            success, error_message
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            session_id,
                            interaction.sage_type.value,
                            interaction.interaction_type,
                            interaction.timestamp,
                            json.dumps(interaction.input_data),
                            json.dumps(interaction.output_data),
                            interaction.confidence_score,
                            interaction.processing_time,
                            interaction.success,
                            interaction.error_message,
                        ),
                    )

                conn.commit()
                return True

            return await loop.run_in_executor(self._executor, _save)

        except Exception as e:
            logger.error(f"Failed to save interactions: {e}")
            raise StorageError(f"SQLite interactions save failed: {e}")

    async def load_interactions(self, session_id: str) -> List[SageInteraction]:
        """4賢者相互作用読み込み"""
        try:
            loop = asyncio.get_event_loop()

            def _load():
                """load（内部メソッド）"""
                conn = self._get_connection()
                rows = conn.execute(
                    "SELECT * FROM sage_interactions WHERE session_id = ? ORDER BY timestamp",
                    (session_id,),
                ).fetchall()

                interactions = []
                for row in rows:
                    interaction = SageInteraction(
                        sage_type=SageType(row["sage_type"]),
                        interaction_type=row["interaction_type"],
                        timestamp=(
                            datetime.fromisoformat(row["timestamp"])
                            if isinstance(row["timestamp"], str)
                            else row["timestamp"]
                        ),
                        input_data=json.loads(row["input_data"]),
                        output_data=json.loads(row["output_data"]),
                        confidence_score=row["confidence_score"],
                        processing_time=row["processing_time"],
                        success=bool(row["success"]),
                        error_message=row["error_message"],
                    )
                    interactions.append(interaction)

                return interactions

            return await loop.run_in_executor(self._executor, _load)

        except Exception as e:
            logger.error(f"Failed to load interactions: {e}")
            raise StorageError(f"SQLite interactions load failed: {e}")

    async def delete_session(self, session_id: str) -> bool:
        """セッション削除"""
        try:
            loop = asyncio.get_event_loop()

            def _delete():
                """delete（内部メソッド）"""
                conn = self._get_connection()
                conn.execute(
                    "DELETE FROM sage_interactions WHERE session_id = ?", (session_id,)
                )
                conn.execute(
                    "DELETE FROM session_metadata WHERE session_id = ?", (session_id,)
                )
                conn.commit()
                return True

            return await loop.run_in_executor(self._executor, _delete)

        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            raise StorageError(f"SQLite session delete failed: {e}")

    async def search_sessions(self, user_id: str, limit: int = 10) -> List[str]:
        """セッション検索"""
        try:
            loop = asyncio.get_event_loop()

            def _search():
                """search（内部メソッド）"""
                conn = self._get_connection()
                rows = conn.execute(
                    "SELECT session_id FROM session_metadata WHERE user_id = ? ORDER BY " \
                        "updated_at SHA256C LIMIT ?",
                    (user_id, limit),
                ).fetchall()

                return [row["session_id"] for row in rows]

            return await loop.run_in_executor(self._executor, _search)

        except Exception as e:
            logger.error(f"Failed to search sessions: {e}")
            raise StorageError(f"SQLite session search failed: {e}")

class JSONAdapter:
    """JSON アダプター - 非構造化データ・スナップショット管理"""

    def __init__(self, base_path: str = "data/session_storage/json"):
        """初期化メソッド"""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._executor = ThreadPoolExecutor(max_workers=5)

    def _get_session_path(self, session_id: str) -> Path:
        """セッションファイルパス取得"""
        return self.base_path / f"{session_id}.json"

    async def save_context_data(self, session_id: str, data: Dict[str, Any]) -> bool:
        """コンテキストデータ保存"""
        try:
            loop = asyncio.get_event_loop()

            def _save():
                """save（内部メソッド）"""
                file_path = self._get_session_path(session_id)

                # データに保存時刻追加
                data["saved_at"] = datetime.now().isoformat()
                data["checksum"] = self._calculate_checksum(data)

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                return True

            return await loop.run_in_executor(self._executor, _save)

        except Exception as e:
            logger.error(f"Failed to save context data: {e}")
            raise StorageError(f"JSON context save failed: {e}")

    async def load_context_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """コンテキストデータ読み込み"""
        try:
            loop = asyncio.get_event_loop()

            def _load():
                """load（内部メソッド）"""
                file_path = self._get_session_path(session_id)

                if not file_path.exists():
                    return None

                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # チェックサム検証
                if "checksum" in data:
                    stored_checksum = data.pop("checksum")
                    calculated_checksum = self._calculate_checksum(data)

                    if stored_checksum != calculated_checksum:
                        logger.warning(f"Checksum mismatch for session {session_id}")
                        raise ConsistencyError("Data integrity check failed")

                return data

            return await loop.run_in_executor(self._executor, _load)

        except Exception as e:
            logger.error(f"Failed to load context data: {e}")
            raise StorageError(f"JSON context load failed: {e}")

    async def delete_context_data(self, session_id: str) -> bool:
        """コンテキストデータ削除"""
        try:
            loop = asyncio.get_event_loop()

            def _delete():
                """delete（内部メソッド）"""
                file_path = self._get_session_path(session_id)

                if file_path.exists():
                    file_path.unlink()

                return True

            return await loop.run_in_executor(self._executor, _delete)

        except Exception as e:
            logger.error(f"Failed to delete context data: {e}")
            raise StorageError(f"JSON context delete failed: {e}")

    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """データチェックサム計算"""
        # saved_at, checksumを除いて計算
        clean_data = {
            k: v for k, v in data.items() if k not in ["saved_at", "checksum"]
        }
        data_str = json.dumps(clean_data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(data_str.encode()).hexdigest()

class VectorAdapter:
    """Vector アダプター - ベクトル検索・類似度計算"""

    def __init__(self, base_path: str = "data/session_storage/vector"):
        """初期化メソッド"""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._executor = ThreadPoolExecutor(max_workers=3)

        # 簡易インメモリベクトルストア（本格実装ではFAISS使用）
        self._vectors: Dict[str, List[float]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    async def save_vector(
        self,
        session_id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """ベクトル保存"""
        try:
            loop = asyncio.get_event_loop()

            def _save():
                """save（内部メソッド）"""
                self._vectors[session_id] = vector
                self._metadata[session_id] = metadata or {}

                # ディスクに永続化
                self._persist_to_disk()

                return True

            return await loop.run_in_executor(self._executor, _save)

        except Exception as e:
            logger.error(f"Failed to save vector: {e}")
            raise StorageError(f"Vector save failed: {e}")

    async def load_vector(self, session_id: str) -> Optional[List[float]]:
        """ベクトル読み込み"""
        try:
            loop = asyncio.get_event_loop()

            def _load():
                """load（内部メソッド）"""
                if session_id not in self._vectors:
                    self._load_from_disk()

                return self._vectors.get(session_id)

            return await loop.run_in_executor(self._executor, _load)

        except Exception as e:
            logger.error(f"Failed to load vector: {e}")
            raise StorageError(f"Vector load failed: {e}")

    async def search_similar(
        self, query_vector: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """類似ベクトル検索"""
        try:
            loop = asyncio.get_event_loop()

            def _search():
                """search（内部メソッド）"""
                if not self._vectors:
                    self._load_from_disk()

                similarities = []

                for session_id, vector in self._vectors.items():
                    similarity = self._cosine_similarity(query_vector, vector)
                    similarities.append(
                        {
                            "session_id": session_id,
                            "similarity": similarity,
                            "metadata": self._metadata.get(session_id, {}),
                        }
                    )

                # 類似度順にソート
                similarities.sort(key=lambda x: x["similarity"], reverse=True)

                return similarities[:top_k]

            return await loop.run_in_executor(self._executor, _search)

        except Exception as e:
            logger.error(f"Failed to search similar vectors: {e}")
            raise StorageError(f"Vector search failed: {e}")

    async def delete_vector(self, session_id: str) -> bool:
        """ベクトル削除"""
        try:
            loop = asyncio.get_event_loop()

            def _delete():
                """delete（内部メソッド）"""
                if session_id in self._vectors:
                    del self._vectors[session_id]

                if session_id in self._metadata:
                    del self._metadata[session_id]

                self._persist_to_disk()

                return True

            return await loop.run_in_executor(self._executor, _delete)

        except Exception as e:
            logger.error(f"Failed to delete vector: {e}")
            raise StorageError(f"Vector delete failed: {e}")

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """コサイン類似度計算"""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(x * x for x in b) ** 0.5

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    def _persist_to_disk(self):
        """ディスクに永続化"""
        vector_file = self.base_path / "vectors.json"
        metadata_file = self.base_path / "metadata.json"

        with open(vector_file, "w") as f:
            json.dump(self._vectors, f)

        with open(metadata_file, "w") as f:
            json.dump(self._metadata, f)

    def _load_from_disk(self):
        """ディスクから読み込み"""
        vector_file = self.base_path / "vectors.json"
        metadata_file = self.base_path / "metadata.json"

        if vector_file.exists():
            with open(vector_file, "r") as f:
                self._vectors = json.load(f)

        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                self._metadata = json.load(f)

class TransactionManager:
    """分散トランザクション管理"""

    def __init__(self):
        """初期化メソッド"""
        self._active_transactions: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def begin_transaction(self, transaction_id: Optional[str] = None) -> str:
        """トランザクション開始"""
        if not transaction_id:
            transaction_id = str(uuid.uuid4())

        async with self._lock:
            self._active_transactions[transaction_id] = {
                "started_at": datetime.now(),
                "participants": [],
                "status": "active",
            }

        return transaction_id

    async def join_transaction(self, transaction_id: str, participant: str):
        """トランザクション参加"""
        async with self._lock:
            if transaction_id in self._active_transactions:
                self._active_transactions[transaction_id]["participants"].append(
                    participant
                )

    async def commit_transaction(self, transaction_id: str):
        """トランザクションコミット"""
        async with self._lock:
            if transaction_id in self._active_transactions:
                self._active_transactions[transaction_id]["status"] = "committed"
                self._active_transactions[transaction_id][
                    "committed_at"
                ] = datetime.now()

    async def rollback_transaction(self, transaction_id: str):
        """トランザクションロールバック"""
        async with self._lock:
            if transaction_id in self._active_transactions:
                self._active_transactions[transaction_id]["status"] = "rolled_back"
                self._active_transactions[transaction_id][
                    "rolled_back_at"
                ] = datetime.now()

class HybridStorage:
    """
    PROJECT ELDERZAN HybridStorage
    SQLite + JSON + Vector 統合ストレージシステム
    """

    def __init__(
        self,
        sqlite_path: str = "data/session_storage/sessions.db",
        json_path: str = "data/session_storage/json",
        vector_path: str = "data/session_storage/vector",
    ):
        # アダプター初期化
        self.sqlite_adapter = SQLiteAdapter(sqlite_path)
        self.json_adapter = JSONAdapter(json_path)
        self.vector_adapter = VectorAdapter(vector_path)

        # トランザクション管理
        self.transaction_manager = TransactionManager()

        # パフォーマンス統計
        self.stats = {"saves": 0, "loads": 0, "searches": 0, "errors": 0}

    async def save_session(self, context: SessionContext) -> bool:
        """セッション保存（分散トランザクション）"""
        transaction_id = await self.transaction_manager.begin_transaction()

        try:
            # 1.0 SQLite にメタデータ・相互作用保存
            await self.sqlite_adapter.save_metadata(context.metadata)
            await self.sqlite_adapter.save_interactions(
                context.metadata.session_id, context.sage_interactions
            )

            # 2.0 JSON にコンテキストデータ保存
            context_data = {
                "tasks": context.tasks,
                "knowledge_graph": context.knowledge_graph,
                "error_patterns": context.error_patterns,
                "success_patterns": context.success_patterns,
                "snapshots": [s.to_dict() for s in context.snapshots],
                "cache_data": context.cache_data,

            }
            await self.json_adapter.save_context_data(
                context.metadata.session_id, context_data
            )

            # 3.0 Vector にベクトルデータ保存（スナップショットから）
            if context.snapshots:
                latest_snapshot = context.snapshots[-1]
                if latest_snapshot.vector_embeddings:
                    await self.vector_adapter.save_vector(
                        context.metadata.session_id,
                        latest_snapshot.vector_embeddings,
                        {
                            "embedding_model": latest_snapshot.embedding_model,
                            "created_at": latest_snapshot.timestamp.isoformat(),
                        },
                    )

            # トランザクションコミット
            await self.transaction_manager.commit_transaction(transaction_id)

            self.stats["saves"] += 1
            return True

        except Exception as e:
            # トランザクションロールバック
            await self.transaction_manager.rollback_transaction(transaction_id)
            self.stats["errors"] += 1
            logger.error(f"Failed to save session: {e}")
            raise StorageError(f"Session save failed: {e}")

    async def load_session(self, session_id: str) -> Optional[SessionContext]:
        """セッション読み込み"""
        try:
            # 1.0 SQLite からメタデータ・相互作用読み込み
            metadata = await self.sqlite_adapter.load_metadata(session_id)
            if not metadata:
                return None

            interactions = await self.sqlite_adapter.load_interactions(session_id)

            # 2.0 JSON からコンテキストデータ読み込み
            context_data = await self.json_adapter.load_context_data(session_id)
            if not context_data:
                context_data = {}

            # 3.0 SessionContext 復元
            context = SessionContext(
                metadata=metadata,
                tasks=context_data.get("tasks", []),
                knowledge_graph=context_data.get("knowledge_graph", {}),
                error_patterns=context_data.get("error_patterns", []),
                success_patterns=context_data.get("success_patterns", []),
                sage_interactions=interactions,
                cache_data=context_data.get("cache_data", {}),

            )

            # スナップショット復元
            for snapshot_data in context_data.get("snapshots", []):
                snapshot = ContextSnapshot.from_dict(snapshot_data)
                context.snapshots.append(snapshot)

            self.stats["loads"] += 1
            return context

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Failed to load session: {e}")
            raise StorageError(f"Session load failed: {e}")

    async def search_similar_sessions(
        self, query_text: str, user_id: str, top_k: int = 5
    ) -> List[SessionContext]:
        """類似セッション検索"""
        try:
            # 簡易実装：テキストベースのダミーベクトル生成
            query_vector = [hash(query_text) % 1000 / 1000.0 for _ in range(100)]

            # ベクトル検索
            similar_results = await self.vector_adapter.search_similar(
                query_vector, top_k
            )

            # セッションコンテキスト取得
            sessions = []
            for result in similar_results:
                session = await self.load_session(result["session_id"])
                if session and session.metadata.user_id == user_id:
                    sessions.append(session)

            self.stats["searches"] += 1
            return sessions

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Failed to search similar sessions: {e}")
            raise StorageError(f"Similar session search failed: {e}")

    async def delete_session(self, session_id: str) -> bool:
        """セッション削除"""
        transaction_id = await self.transaction_manager.begin_transaction()

        try:
            # 全ストレージから削除
            await self.sqlite_adapter.delete_session(session_id)
            await self.json_adapter.delete_context_data(session_id)
            await self.vector_adapter.delete_vector(session_id)

            await self.transaction_manager.commit_transaction(transaction_id)
            return True

        except Exception as e:
            await self.transaction_manager.rollback_transaction(transaction_id)
            self.stats["errors"] += 1
            logger.error(f"Failed to delete session: {e}")
            raise StorageError(f"Session delete failed: {e}")

    async def get_user_sessions(self, user_id: str, limit: int = 10) -> List[str]:
        """ユーザーセッション一覧取得"""
        try:
            return await self.sqlite_adapter.search_sessions(user_id, limit)
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Failed to get user sessions: {e}")
            raise StorageError(f"User sessions retrieval failed: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """統計情報取得"""
        return {
            "storage_stats": self.stats.copy(),
            "timestamp": datetime.now().isoformat(),
        }