#!/usr/bin/env python3
"""
Elders Guild 統合エンティティマネージャー v1.0
ナレッジ・インシデント・タスク統合管理システム
"""

import json
import logging
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# プロジェクトルートの設定
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "unified_entities.db"
SCHEMA_PATH = PROJECT_ROOT / "integration" / "unified_database_schema.sql"

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BaseEntity:
    """基底エンティティクラス"""

    id: str
    type: str  # 'knowledge', 'incident', 'task', 'worker', 'system'
    title: str
    content: str = ""
    metadata: Dict[str, Any] = None
    relationships: Dict[str, Any] = None
    search_metadata: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.relationships is None:
            self.relationships = {}
        if self.search_metadata is None:
            self.search_metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class KnowledgeEntity(BaseEntity):
    """知識エンティティ"""

    knowledge_data: Dict[str, Any] = None

    def __init__(self, id: str = "", title: str = "", content: str = "", **kwargs):
        super().__init__(
            id=id, type="knowledge", title=title, content=content, **kwargs
        )
        if self.knowledge_data is None:
            self.knowledge_data = {
                "source_type": "manual",
                "confidence_score": 0.8,
                "verification_status": "pending",
                "usage_count": 0,
                "effectiveness_rating": 0.0,
                "domain": "general",
            }


@dataclass
class IncidentEntity(BaseEntity):
    """インシデントエンティティ"""

    incident_data: Dict[str, Any] = None

    def __init__(self, id: str = "", title: str = "", content: str = "", **kwargs):
        super().__init__(id=id, type="incident", title=title, content=content, **kwargs)
        if self.incident_data is None:
            self.incident_data = {
                "severity": "medium",
                "status": "open",
                "affected_systems": [],
                "resolution_steps": [],
                "root_cause": "",
                "lessons_learned": [],
                "auto_generated_knowledge": None,
            }


@dataclass
class TaskEntity(BaseEntity):
    """タスクエンティティ"""

    task_data: Dict[str, Any] = None

    def __init__(self, id: str = "", title: str = "", content: str = "", **kwargs):
        super().__init__(id=id, type="task", title=title, content=content, **kwargs)
        if self.task_data is None:
            self.task_data = {
                "task_type": "general",
                "status": "pending",
                "assigned_worker": None,
                "completion_percentage": 0,
                "dependencies": [],
                "estimated_duration": None,
                "actual_duration": None,
            }


@dataclass
class EntityRelationship:
    """エンティティ関係性"""

    source_id: str
    target_id: str
    relationship_type: str
    weight: float = 1.0
    metadata: Dict[str, Any] = None
    created_by: str = "system"

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class UnifiedEntityManager:
    """統合エンティティマネージャー"""

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    def _initialize_database(self):
        """データベース初期化"""
        try:
            # スキーマファイルが存在する場合は実行
            if SCHEMA_PATH.exists():
                with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                    schema_sql = f.read()

                with self._get_connection() as conn:
                    # 複数のSQL文を実行
                    conn.executescript(schema_sql)
                    conn.commit()

                logger.info(f"Database initialized with schema from {SCHEMA_PATH}")
            else:
                logger.warning(f"Schema file not found: {SCHEMA_PATH}")
                self._create_basic_schema()

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    def _create_basic_schema(self):
        """基本スキーマ作成（スキーマファイルが無い場合）"""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS unified_entities (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    metadata JSON DEFAULT '{}',
                    relationships JSON DEFAULT '{}',
                    search_metadata JSON DEFAULT '{}',
                    knowledge_data JSON DEFAULT NULL,
                    incident_data JSON DEFAULT NULL,
                    task_data JSON DEFAULT NULL,
                    worker_data JSON DEFAULT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.commit()

    @contextmanager
    def _get_connection(self):
        """データベース接続コンテキストマネージャー"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            conn.close()

    # ============================================
    # エンティティCRUD操作
    # ============================================

    def create_entity(self, entity: BaseEntity) -> str:
        """エンティティ作成"""
        try:
            if not entity.id:
                entity.id = str(uuid.uuid4())

            with self._get_connection() as conn:
                # エンティティタイプに応じた専用データを設定
                type_data = None
                if isinstance(entity, KnowledgeEntity):
                    type_data = ("knowledge_data", entity.knowledge_data)
                elif isinstance(entity, IncidentEntity):
                    type_data = ("incident_data", entity.incident_data)
                elif isinstance(entity, TaskEntity):
                    type_data = ("task_data", entity.task_data)

                # SQLクエリ構築
                if type_data:
                    sql = f"""
                        INSERT INTO unified_entities
                        (id, type, title, content, metadata, relationships, search_metadata, {type_data[0]})
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    params = (
                        entity.id,
                        entity.type,
                        entity.title,
                        entity.content,
                        json.dumps(entity.metadata),
                        json.dumps(entity.relationships),
                        json.dumps(entity.search_metadata),
                        json.dumps(type_data[1]),
                    )
                else:
                    sql = """
                        INSERT INTO unified_entities
                        (id, type, title, content, metadata, relationships, search_metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """
                    params = (
                        entity.id,
                        entity.type,
                        entity.title,
                        entity.content,
                        json.dumps(entity.metadata),
                        json.dumps(entity.relationships),
                        json.dumps(entity.search_metadata),
                    )

                conn.execute(sql, params)
                conn.commit()

                logger.info(f"Entity created: {entity.id} ({entity.type})")
                return entity.id

        except Exception as e:
            logger.error(f"Failed to create entity: {e}")
            raise

    def get_entity(self, entity_id: str) -> Optional[BaseEntity]:
        """エンティティ取得"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM unified_entities WHERE id = ?", (entity_id,)
                )
                row = cursor.fetchone()

                if not row:
                    return None

                return self._row_to_entity(row)

        except Exception as e:
            logger.error(f"Failed to get entity {entity_id}: {e}")
            return None

    def update_entity(self, entity: BaseEntity) -> bool:
        """エンティティ更新"""
        try:
            entity.updated_at = datetime.now()

            with self._get_connection() as conn:
                # エンティティタイプに応じた専用データを設定
                type_data = None
                if isinstance(entity, KnowledgeEntity):
                    type_data = ("knowledge_data", entity.knowledge_data)
                elif isinstance(entity, IncidentEntity):
                    type_data = ("incident_data", entity.incident_data)
                elif isinstance(entity, TaskEntity):
                    type_data = ("task_data", entity.task_data)

                if type_data:
                    sql = f"""
                        UPDATE unified_entities SET
                        title = ?, content = ?, metadata = ?, relationships = ?,
                        search_metadata = ?, {type_data[0]} = ?, updated_at = ?
                        WHERE id = ?
                    """
                    params = (
                        entity.title,
                        entity.content,
                        json.dumps(entity.metadata),
                        json.dumps(entity.relationships),
                        json.dumps(entity.search_metadata),
                        json.dumps(type_data[1]),
                        entity.updated_at.isoformat(),
                        entity.id,
                    )
                else:
                    sql = """
                        UPDATE unified_entities SET
                        title = ?, content = ?, metadata = ?, relationships = ?,
                        search_metadata = ?, updated_at = ?
                        WHERE id = ?
                    """
                    params = (
                        entity.title,
                        entity.content,
                        json.dumps(entity.metadata),
                        json.dumps(entity.relationships),
                        json.dumps(entity.search_metadata),
                        entity.updated_at.isoformat(),
                        entity.id,
                    )

                cursor = conn.execute(sql, params)
                conn.commit()

                updated = cursor.rowcount > 0
                if updated:
                    logger.info(f"Entity updated: {entity.id}")
                return updated

        except Exception as e:
            logger.error(f"Failed to update entity {entity.id}: {e}")
            return False

    def delete_entity(self, entity_id: str) -> bool:
        """エンティティ削除"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM unified_entities WHERE id = ?", (entity_id,)
                )
                conn.commit()

                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Entity deleted: {entity_id}")
                return deleted

        except Exception as e:
            logger.error(f"Failed to delete entity {entity_id}: {e}")
            return False

    def list_entities(
        self,
        entity_type: str = None,
        limit: int = 100,
        offset: int = 0,
        filters: Dict[str, Any] = None,
    ) -> List[BaseEntity]:
        """エンティティ一覧取得"""
        try:
            with self._get_connection() as conn:
                sql = "SELECT * FROM unified_entities"
                params = []
                conditions = []

                if entity_type:
                    conditions.append("type = ?")
                    params.append(entity_type)

                if filters:
                    for key, value in filters.items():
                        if not (key == "status"):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if key == "status":
                            conditions.append("json_extract(metadata, '$.status') = ?")
                            params.append(value)
                        elif key == "priority":
                            conditions.append(
                                "json_extract(metadata, '$.priority') = ?"
                            )
                            params.append(value)
                        elif key == "category":
                            conditions.append(
                                "json_extract(metadata, '$.category') = ?"
                            )
                            params.append(value)

                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)

                sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                cursor = conn.execute(sql, params)
                rows = cursor.fetchall()

                return [self._row_to_entity(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to list entities: {e}")
            return []

    # ============================================
    # 関係性管理
    # ============================================

    def create_relationship(self, relationship: EntityRelationship) -> bool:
        """関係性作成"""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO entity_relationships
                    (source_id, target_id, relationship_type, weight, metadata, created_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        relationship.source_id,
                        relationship.target_id,
                        relationship.relationship_type,
                        relationship.weight,
                        json.dumps(relationship.metadata),
                        relationship.created_by,
                    ),
                )
                conn.commit()

                logger.info(
                    f"Relationship created: {relationship.source_id} -> {relationship.target_id}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to create relationship: {e}")
            return False

    def get_relationships(
        self, entity_id: str, direction: str = "both"
    ) -> List[EntityRelationship]:
        """エンティティの関係性取得"""
        try:
            with self._get_connection() as conn:
                if direction == "outgoing":
                    sql = "SELECT * FROM entity_relationships WHERE source_id = ?"
                elif direction == "incoming":
                    sql = "SELECT * FROM entity_relationships WHERE target_id = ?"
                else:  # both
                    sql = "SELECT * FROM entity_relationships WHERE source_id = ? OR target_id = ?"

                if direction == "both":
                    cursor = conn.execute(sql, (entity_id, entity_id))
                else:
                    cursor = conn.execute(sql, (entity_id,))

                rows = cursor.fetchall()
                relationships = []

                for row in rows:
                    rel = EntityRelationship(
                        source_id=row["source_id"],
                        target_id=row["target_id"],
                        relationship_type=row["relationship_type"],
                        weight=row["weight"],
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                        created_by=row["created_by"],
                    )
                    relationships.append(rel)

                return relationships

        except Exception as e:
            logger.error(f"Failed to get relationships for {entity_id}: {e}")
            return []

    def find_related_entities(
        self, entity_id: str, relationship_types: List[str] = None, max_depth: int = 2
    ) -> List[BaseEntity]:
        """関連エンティティ検索"""
        try:
            related_ids = set()
            to_process = [(entity_id, 0)]
            processed = set()

            with self._get_connection() as conn:
                # ループ処理
                while to_process:
                    current_id, depth = to_process.pop(0)

                    if current_id in processed or depth >= max_depth:
                        continue

                    processed.add(current_id)

                    # 関係性クエリ
                    if relationship_types:
                        placeholders = ",".join(["?" for _ in relationship_types])
                        sql = f"""
                            SELECT target_id FROM entity_relationships
                            WHERE source_id = ? AND relationship_type IN ({placeholders})
                            UNION
                            SELECT source_id FROM entity_relationships
                            WHERE target_id = ? AND relationship_type IN ({placeholders})
                        """
                        params = (
                            [current_id]
                            + relationship_types
                            + [current_id]
                            + relationship_types
                        )
                    else:
                        sql = """
                            SELECT target_id FROM entity_relationships WHERE source_id = ?
                            UNION
                            SELECT source_id FROM entity_relationships WHERE target_id = ?
                        """
                        params = [current_id, current_id]

                    cursor = conn.execute(sql, params)
                    related_rows = cursor.fetchall()

                    for row in related_rows:
                        related_id = row[0]
                        if not (related_id != entity_id:  # 自分自身は除外):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if related_id != entity_id:  # 自分自身は除外
                            related_ids.add(related_id)
                            if not (depth + 1 < max_depth):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if depth + 1 < max_depth:
                                to_process.append((related_id, depth + 1))

                # 関連エンティティを取得
                if related_ids:
                    placeholders = ",".join(["?" for _ in related_ids])
                    sql = f"SELECT * FROM unified_entities WHERE id IN ({placeholders})"
                    cursor = conn.execute(sql, list(related_ids))
                    rows = cursor.fetchall()

                    return [self._row_to_entity(row) for row in rows]

                return []

        except Exception as e:
            logger.error(f"Failed to find related entities for {entity_id}: {e}")
            return []

    # ============================================
    # 検索機能
    # ============================================

    def search_entities(
        self, query: str, entity_types: List[str] = None, limit: int = 50
    ) -> List[BaseEntity]:
        """エンティティ検索"""
        try:
            with self._get_connection() as conn:
                # キーワード検索（簡易版）
                search_terms = query.lower().split()

                sql_parts = []
                params = []

                # タイトル・コンテンツでの検索
                for term in search_terms:
                    sql_parts.append("(LOWER(title) LIKE ? OR LOWER(content) LIKE ?)")
                    params.extend([f"%{term}%", f"%{term}%"])

                sql = (
                    f"SELECT * FROM unified_entities WHERE ({' AND '.join(sql_parts)})"
                )

                # エンティティタイプフィルタ
                if entity_types:
                    type_placeholders = ",".join(["?" for _ in entity_types])
                    sql += f" AND type IN ({type_placeholders})"
                    params.extend(entity_types)

                sql += " ORDER BY updated_at DESC LIMIT ?"
                params.append(limit)

                cursor = conn.execute(sql, params)
                rows = cursor.fetchall()

                return [self._row_to_entity(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to search entities: {e}")
            return []

    # ============================================
    # ユーティリティメソッド
    # ============================================

    def _row_to_entity(self, row: sqlite3.Row) -> BaseEntity:
        """データベース行をエンティティオブジェクトに変換"""
        # 基本データの解析
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        relationships = json.loads(row["relationships"]) if row["relationships"] else {}
        search_metadata = (
            json.loads(row["search_metadata"]) if row["search_metadata"] else {}
        )

        # 作成・更新日時の変換
        created_at = (
            datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
        )
        updated_at = (
            datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
        )

        # エンティティタイプに応じたオブジェクト作成
        if row["type"] == "knowledge":
            knowledge_data = (
                json.loads(row["knowledge_data"]) if row["knowledge_data"] else {}
            )
            return KnowledgeEntity(
                id=row["id"],
                title=row["title"],
                content=row["content"] or "",
                metadata=metadata,
                relationships=relationships,
                search_metadata=search_metadata,
                knowledge_data=knowledge_data,
                created_at=created_at,
                updated_at=updated_at,
            )

        elif row["type"] == "incident":
            incident_data = (
                json.loads(row["incident_data"]) if row["incident_data"] else {}
            )
            return IncidentEntity(
                id=row["id"],
                title=row["title"],
                content=row["content"] or "",
                metadata=metadata,
                relationships=relationships,
                search_metadata=search_metadata,
                incident_data=incident_data,
                created_at=created_at,
                updated_at=updated_at,
            )

        elif row["type"] == "task":
            task_data = json.loads(row["task_data"]) if row["task_data"] else {}
            return TaskEntity(
                id=row["id"],
                title=row["title"],
                content=row["content"] or "",
                metadata=metadata,
                relationships=relationships,
                search_metadata=search_metadata,
                task_data=task_data,
                created_at=created_at,
                updated_at=updated_at,
            )

        else:
            # 基本エンティティ
            return BaseEntity(
                id=row["id"],
                type=row["type"],
                title=row["title"],
                content=row["content"] or "",
                metadata=metadata,
                relationships=relationships,
                search_metadata=search_metadata,
                created_at=created_at,
                updated_at=updated_at,
            )

    def get_statistics(self) -> Dict[str, Any]:
        """システム統計取得"""
        try:
            with self._get_connection() as conn:
                stats = {}

                # エンティティ数
                cursor = conn.execute(
                    "SELECT type, COUNT(*) FROM unified_entities GROUP BY type"
                )
                entity_counts = {row[0]: row[1] for row in cursor.fetchall()}
                stats["entity_counts"] = entity_counts

                # 関係性数
                cursor = conn.execute("SELECT COUNT(*) FROM entity_relationships")
                stats["relationship_count"] = cursor.fetchone()[0]

                # 最近の活動
                cursor = conn.execute(
                    """
                    SELECT COUNT(*) FROM unified_entities
                    WHERE created_at > datetime('now', '-7 days')
                """
                )
                stats["recent_entities"] = cursor.fetchone()[0]

                return stats

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}


# ============================================
# ファクトリー関数
# ============================================


def create_knowledge_entity(
    title: str, content: str, confidence_score: float = 0.8, domain: str = "general"
) -> KnowledgeEntity:
    """知識エンティティ作成ヘルパー"""
    entity = KnowledgeEntity(id=str(uuid.uuid4()), title=title, content=content)
    entity.knowledge_data.update(
        {"confidence_score": confidence_score, "domain": domain}
    )
    return entity


def create_incident_entity(
    title: str,
    content: str,
    severity: str = "medium",
    affected_systems: List[str] = None,
) -> IncidentEntity:
    """インシデントエンティティ作成ヘルパー"""
    entity = IncidentEntity(id=str(uuid.uuid4()), title=title, content=content)
    entity.incident_data.update(
        {"severity": severity, "affected_systems": affected_systems or []}
    )
    return entity


def create_task_entity(
    title: str, content: str, task_type: str = "general", assigned_worker: str = None
) -> TaskEntity:
    """タスクエンティティ作成ヘルパー"""
    entity = TaskEntity(id=str(uuid.uuid4()), title=title, content=content)
    entity.task_data.update(
        {"task_type": task_type, "assigned_worker": assigned_worker}
    )
    return entity


# ============================================
# テスト用サンプル実行
# ============================================

if __name__ == "__main__":
    # サンプル使用例
    manager = UnifiedEntityManager()

    # サンプル知識エンティティ作成
    knowledge = create_knowledge_entity(
        "Python例外処理ベストプラクティス",
        "try-except文使用時は具体的な例外クラスをキャッチし、ログ出力を忘れずに。",
        confidence_score=0.9,
        domain="development",
    )

    knowledge_id = manager.create_entity(knowledge)
    print(f"Knowledge entity created: {knowledge_id}")

    # サンプルインシデント作成
    incident = create_incident_entity(
        "API応答タイムアウトエラー",
        "外部API呼び出し時に5秒以上の遅延が発生し、タイムアウトエラーが多発。",
        severity="high",
        affected_systems=["api_gateway", "user_service"],
    )

    incident_id = manager.create_entity(incident)
    print(f"Incident entity created: {incident_id}")

    # 関係性作成
    relationship = EntityRelationship(
        source_id=incident_id,
        target_id=knowledge_id,
        relationship_type="resolved_by",
        weight=0.8,
    )

    manager.create_relationship(relationship)
    print("Relationship created")

    # 統計表示
    stats = manager.get_statistics()
    print(f"System statistics: {stats}")
