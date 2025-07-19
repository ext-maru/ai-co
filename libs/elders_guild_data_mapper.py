"""
Elders Guild Data Mapper - データマッピング・変換システム
Created: 2025-07-11
Author: Claude Elder
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from abc import ABC, abstractmethod

import asyncpg
from pydantic import BaseModel, ValidationError

from .elders_guild_data_models import (
    BaseDataModel,
    KnowledgeEntity,
    TaskEntity,
    IncidentEntity,
    DocumentEntity,
    RAGContext,
    SageType,
    DataStatus,
)
from .elders_guild_db_manager import EldersGuildDatabaseManager

logger = logging.getLogger(__name__)

# ============================================================================
# Data Mapping Configuration
# ============================================================================


class MappingStrategy(Enum):
    """マッピング戦略"""

    DIRECT = "direct"  # 直接マッピング
    TRANSFORM = "transform"  # 変換マッピング
    AGGREGATE = "aggregate"  # 集約マッピング
    SPLIT = "split"  # 分割マッピング
    CUSTOM = "custom"  # カスタムマッピング


@dataclass
class FieldMapping:
    """フィールドマッピング定義"""

    source_field: str
    target_field: str
    strategy: MappingStrategy = MappingStrategy.DIRECT
    transform_func: Optional[Callable] = None
    default_value: Any = None
    required: bool = False

    def apply_mapping(self, source_data: Dict[str, Any]) -> Any:
        """マッピングの適用"""
        if self.source_field not in source_data:
            if self.required:
                raise ValueError(f"Required field '{self.source_field}' not found")
            return self.default_value

        value = source_data[self.source_field]

        if self.strategy == MappingStrategy.DIRECT:
            return value
        elif self.strategy == MappingStrategy.TRANSFORM and self.transform_func:
            return self.transform_func(value)
        elif self.strategy == MappingStrategy.CUSTOM and self.transform_func:
            return self.transform_func(source_data)
        else:
            return value


@dataclass
class DataMapping:
    """データマッピング定義"""

    name: str
    description: str
    source_type: str
    target_type: str
    field_mappings: List[FieldMapping]
    pre_processors: List[Callable] = field(default_factory=list)
    post_processors: List[Callable] = field(default_factory=list)
    validation_rules: List[Callable] = field(default_factory=list)

    def apply_mapping(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """データマッピングの適用"""
        # 前処理
        for processor in self.pre_processors:
            source_data = processor(source_data)

        # フィールドマッピング
        target_data = {}
        for field_mapping in self.field_mappings:
            try:
                value = field_mapping.apply_mapping(source_data)
                if value is not None:
                    target_data[field_mapping.target_field] = value
            except Exception as e:
                logger.error(
                    f"Field mapping error for {field_mapping.source_field}: {e}"
                )
                if field_mapping.required:
                    raise

        # 後処理
        for processor in self.post_processors:
            target_data = processor(target_data)

        # 検証
        for rule in self.validation_rules:
            if not rule(target_data):
                raise ValidationError(f"Validation failed for mapping {self.name}")

        return target_data


# ============================================================================
# Data Transformation Functions
# ============================================================================


class DataTransformers:
    """データ変換関数群"""

    @staticmethod
    def string_to_list(value: str, delimiter: str = ",") -> List[str]:
        """文字列をリストに変換"""
        if not value:
            return []
        return [item.strip() for item in value.split(delimiter)]

    @staticmethod
    def timestamp_to_datetime(value: Union[str, int, float]) -> datetime:
        """タイムスタンプを datetime に変換"""
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        elif isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)
        else:
            raise ValueError(f"Cannot convert {type(value)} to datetime")

    @staticmethod
    def normalize_text(value: str) -> str:
        """テキストの正規化"""
        if not value:
            return ""
        return value.strip().replace("\n", " ").replace("\r", "")

    @staticmethod
    def calculate_quality_score(data: Dict[str, Any]) -> float:
        """品質スコアの計算"""
        score = 0.0

        # 内容の充実度
        content_length = len(data.get("content", ""))
        if content_length > 1000:
            score += 0.3
        elif content_length > 500:
            score += 0.2
        elif content_length > 100:
            score += 0.1

        # メタデータの充実度
        metadata_count = len(data.get("metadata", {}))
        if metadata_count > 5:
            score += 0.2
        elif metadata_count > 2:
            score += 0.1

        # タグの存在
        tags_count = len(data.get("tags", []))
        if tags_count > 3:
            score += 0.2
        elif tags_count > 0:
            score += 0.1

        # カテゴリの存在
        if data.get("category_id"):
            score += 0.1

        # 参照の存在
        if data.get("source_references"):
            score += 0.1

        # 関連性の存在
        if data.get("related_knowledge_ids"):
            score += 0.1

        return min(score, 1.0)

    @staticmethod
    def extract_keywords(content: str) -> List[str]:
        """キーワードの抽出"""
        if not content:
            return []

        # 簡易的なキーワード抽出
        words = content.lower().split()

        # ストップワードの除外
        stop_words = {
            "の",
            "は",
            "が",
            "を",
            "に",
            "で",
            "と",
            "から",
            "まで",
            "より",
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }

        keywords = []
        for word in words:
            if len(word) > 2 and word not in stop_words:
                keywords.append(word)

        # 頻出順でソート（簡易実装）
        from collections import Counter

        word_count = Counter(keywords)

        return [word for word, count in word_count.most_common(10)]

    @staticmethod
    def generate_summary(content: str, max_length: int = 200) -> str:
        """要約の生成"""
        if not content:
            return ""

        # 簡易的な要約（最初の数文を使用）
        sentences = content.split("。")
        summary = ""

        for sentence in sentences:
            if len(summary + sentence) <= max_length:
                summary += sentence + "。"
            else:
                break

        return summary.strip()


# ============================================================================
# Data Mapper Registry
# ============================================================================


class DataMapperRegistry:
    """データマッパー登録システム"""

    def __init__(self):
        self.mappings: Dict[str, DataMapping] = {}
        self.transformers = DataTransformers()
        self._register_default_mappings()

    def register_mapping(self, mapping: DataMapping):
        """マッピングの登録"""
        self.mappings[mapping.name] = mapping
        logger.info(f"Registered data mapping: {mapping.name}")

    def get_mapping(self, name: str) -> Optional[DataMapping]:
        """マッピングの取得"""
        return self.mappings.get(name)

    def list_mappings(self) -> List[str]:
        """マッピング一覧の取得"""
        return list(self.mappings.keys())

    def _register_default_mappings(self):
        """デフォルトマッピングの登録"""
        # Legacy Knowledge -> KnowledgeEntity
        legacy_to_knowledge = DataMapping(
            name="legacy_knowledge_to_entity",
            description="Legacy knowledge format to KnowledgeEntity",
            source_type="legacy_knowledge",
            target_type="knowledge_entity",
            field_mappings=[
                FieldMapping("title", "title", required=True),
                FieldMapping("content", "content", required=True),
                FieldMapping("category", "category_id"),
                FieldMapping(
                    "tags",
                    "tags",
                    MappingStrategy.TRANSFORM,
                    self.transformers.string_to_list,
                ),
                FieldMapping(
                    "created_date",
                    "created_at",
                    MappingStrategy.TRANSFORM,
                    self.transformers.timestamp_to_datetime,
                ),
                FieldMapping(
                    "updated_date",
                    "updated_at",
                    MappingStrategy.TRANSFORM,
                    self.transformers.timestamp_to_datetime,
                ),
                FieldMapping("quality", "quality_score", default_value=0.0),
                FieldMapping(
                    "keywords",
                    "keywords",
                    MappingStrategy.TRANSFORM,
                    self.transformers.string_to_list,
                ),
                FieldMapping(
                    "summary",
                    "summary",
                    MappingStrategy.CUSTOM,
                    lambda data: self.transformers.generate_summary(
                        data.get("content", "")
                    ),
                ),
            ],
            post_processors=[
                lambda data: {
                    **data,
                    "quality_score": self.transformers.calculate_quality_score(data),
                }
            ],
        )
        self.register_mapping(legacy_to_knowledge)

        # External Task -> TaskEntity
        external_to_task = DataMapping(
            name="external_task_to_entity",
            description="External task format to TaskEntity",
            source_type="external_task",
            target_type="task_entity",
            field_mappings=[
                FieldMapping("name", "name", required=True),
                FieldMapping("description", "description"),
                FieldMapping(
                    "priority",
                    "priority",
                    MappingStrategy.TRANSFORM,
                    lambda x: getattr(DataPriority, x.upper(), DataPriority.NORMAL),
                ),
                FieldMapping("assignee", "assigned_to"),
                FieldMapping(
                    "due_date",
                    "deadline",
                    MappingStrategy.TRANSFORM,
                    self.transformers.timestamp_to_datetime,
                ),
                FieldMapping(
                    "depends_on",
                    "dependencies",
                    MappingStrategy.TRANSFORM,
                    self.transformers.string_to_list,
                ),
                FieldMapping(
                    "status",
                    "status",
                    MappingStrategy.TRANSFORM,
                    lambda x: getattr(DataStatus, x.upper(), DataStatus.ACTIVE),
                ),
            ],
        )
        self.register_mapping(external_to_task)

        # Raw Document -> DocumentEntity
        raw_to_document = DataMapping(
            name="raw_document_to_entity",
            description="Raw document format to DocumentEntity",
            source_type="raw_document",
            target_type="document_entity",
            field_mappings=[
                FieldMapping("title", "title"),
                FieldMapping("content", "content", required=True),
                FieldMapping("source", "source"),
                FieldMapping("url", "source_url"),
                FieldMapping("language", "language", default_value="ja"),
                FieldMapping("content_type", "content_type", default_value="text"),
                FieldMapping("hash", "content_hash", required=True),
            ],
            post_processors=[
                lambda data: {
                    **data,
                    "quality_score": self.transformers.calculate_quality_score(data),
                    "indexed_at": datetime.now(),
                }
            ],
        )
        self.register_mapping(raw_to_document)


# ============================================================================
# Data Conversion Engine
# ============================================================================


class DataConversionEngine:
    """データ変換エンジン"""

    def __init__(self, db_manager: EldersGuildDatabaseManager):
        self.db_manager = db_manager
        self.mapper_registry = DataMapperRegistry()
        self.conversion_stats = {
            "total_conversions": 0,
            "successful_conversions": 0,
            "failed_conversions": 0,
            "conversion_time_total": 0.0,
        }

    async def convert_data(
        self, mapping_name: str, source_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """データの変換"""
        start_time = asyncio.get_event_loop().time()

        try:
            mapping = self.mapper_registry.get_mapping(mapping_name)
            if not mapping:
                raise ValueError(f"Unknown mapping: {mapping_name}")

            # マッピングの適用
            target_data = mapping.apply_mapping(source_data)

            # 成功統計
            self.conversion_stats["successful_conversions"] += 1

            logger.info(f"Successfully converted data using mapping: {mapping_name}")
            return target_data

        except Exception as e:
            # 失敗統計
            self.conversion_stats["failed_conversions"] += 1
            logger.error(f"Data conversion failed for mapping {mapping_name}: {e}")
            raise

        finally:
            # 処理時間の記録
            conversion_time = asyncio.get_event_loop().time() - start_time
            self.conversion_stats["conversion_time_total"] += conversion_time
            self.conversion_stats["total_conversions"] += 1

    async def batch_convert_data(
        self, mapping_name: str, source_data_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """バッチデータ変換"""
        converted_data = []

        for source_data in source_data_list:
            try:
                target_data = await self.convert_data(mapping_name, source_data)
                converted_data.append(target_data)
            except Exception as e:
                logger.error(f"Failed to convert data item: {e}")
                # エラーアイテムをスキップして継続
                continue

        return converted_data

    async def convert_and_store(
        self,
        mapping_name: str,
        source_data: Dict[str, Any],
        target_model_class: Type[BaseDataModel],
    ) -> BaseDataModel:
        """データ変換と保存"""
        # データ変換
        converted_data = await self.convert_data(mapping_name, source_data)

        # モデルインスタンスの作成
        try:
            model_instance = target_model_class(**converted_data)
        except ValidationError as e:
            logger.error(f"Model validation failed: {e}")
            raise

        # データベースに保存
        await self._save_model_instance(model_instance)

        return model_instance

    async def _save_model_instance(self, model_instance: BaseDataModel):
        """モデルインスタンスの保存"""
        # 簡易実装 - 実際のデータベース保存は別途実装
        logger.info(f"Saving model instance: {model_instance.id}")

    def validate_mapping(self, mapping_name: str, sample_data: Dict[str, Any]) -> bool:
        """マッピングの検証"""
        try:
            mapping = self.mapper_registry.get_mapping(mapping_name)
            if not mapping:
                return False

            # サンプルデータで変換テスト
            target_data = mapping.apply_mapping(sample_data)
            return True

        except Exception as e:
            logger.error(f"Mapping validation failed: {e}")
            return False

    def get_conversion_statistics(self) -> Dict[str, Any]:
        """変換統計の取得"""
        stats = self.conversion_stats.copy()

        # 平均処理時間の計算
        if stats["total_conversions"] > 0:
            stats["avg_conversion_time"] = (
                stats["conversion_time_total"] / stats["total_conversions"]
            )
        else:
            stats["avg_conversion_time"] = 0.0

        # 成功率の計算
        if stats["total_conversions"] > 0:
            stats["success_rate"] = (
                stats["successful_conversions"] / stats["total_conversions"]
            )
        else:
            stats["success_rate"] = 0.0

        return stats

    def register_custom_mapping(self, mapping: DataMapping):
        """カスタムマッピングの登録"""
        self.mapper_registry.register_mapping(mapping)

    def list_available_mappings(self) -> List[str]:
        """利用可能なマッピング一覧"""
        return self.mapper_registry.list_mappings()


# ============================================================================
# Data Migration Tools
# ============================================================================


class DataMigrationTool:
    """データ移行ツール"""

    def __init__(self, conversion_engine: DataConversionEngine):
        self.conversion_engine = conversion_engine
        self.migration_history = []

    async def migrate_legacy_knowledge(
        self, legacy_data: List[Dict[str, Any]]
    ) -> List[KnowledgeEntity]:
        """レガシー知識データの移行"""
        logger.info(f"Starting migration of {len(legacy_data)} legacy knowledge items")

        migrated_entities = []

        for item in legacy_data:
            try:
                entity = await self.conversion_engine.convert_and_store(
                    "legacy_knowledge_to_entity", item, KnowledgeEntity
                )
                migrated_entities.append(entity)

            except Exception as e:
                logger.error(
                    f"Failed to migrate knowledge item {item.get('id', 'unknown')}: {e}"
                )
                continue

        # 移行履歴の記録
        self.migration_history.append(
            {
                "type": "legacy_knowledge",
                "timestamp": datetime.now(),
                "total_items": len(legacy_data),
                "migrated_items": len(migrated_entities),
                "success_rate": (
                    len(migrated_entities) / len(legacy_data) if legacy_data else 0.0
                ),
            }
        )

        logger.info(
            f"Completed migration: {len(migrated_entities)}/{len(legacy_data)} items migrated"
        )
        return migrated_entities

    async def migrate_external_tasks(
        self, external_data: List[Dict[str, Any]]
    ) -> List[TaskEntity]:
        """外部タスクデータの移行"""
        logger.info(f"Starting migration of {len(external_data)} external tasks")

        migrated_entities = []

        for item in external_data:
            try:
                entity = await self.conversion_engine.convert_and_store(
                    "external_task_to_entity", item, TaskEntity
                )
                migrated_entities.append(entity)

            except Exception as e:
                logger.error(
                    f"Failed to migrate task item {item.get('id', 'unknown')}: {e}"
                )
                continue

        # 移行履歴の記録
        self.migration_history.append(
            {
                "type": "external_tasks",
                "timestamp": datetime.now(),
                "total_items": len(external_data),
                "migrated_items": len(migrated_entities),
                "success_rate": (
                    len(migrated_entities) / len(external_data)
                    if external_data
                    else 0.0
                ),
            }
        )

        logger.info(
            f"Completed migration: {len(migrated_entities)}/{len(external_data)} tasks migrated"
        )
        return migrated_entities

    def get_migration_report(self) -> Dict[str, Any]:
        """移行レポートの取得"""
        total_items = sum(item["total_items"] for item in self.migration_history)
        migrated_items = sum(item["migrated_items"] for item in self.migration_history)

        return {
            "total_migrations": len(self.migration_history),
            "total_items_processed": total_items,
            "total_items_migrated": migrated_items,
            "overall_success_rate": (
                migrated_items / total_items if total_items > 0 else 0.0
            ),
            "migration_history": self.migration_history,
            "conversion_statistics": self.conversion_engine.get_conversion_statistics(),
        }


# ============================================================================
# Usage Example
# ============================================================================


async def main():
    """使用例"""
    from .elders_guild_db_manager import EldersGuildDatabaseManager, DatabaseConfig

    # データベース設定
    db_config = DatabaseConfig()
    db_manager = EldersGuildDatabaseManager(db_config)

    # データ変換エンジン
    conversion_engine = DataConversionEngine(db_manager)

    # レガシーデータの変換例
    legacy_knowledge_data = {
        "title": "PostgreSQL パフォーマンスチューニング",
        "content": "PostgreSQLのパフォーマンスを向上させるための手法について説明します。",
        "category": "database",
        "tags": "postgresql,performance,tuning,database",
        "created_date": "2025-01-01T00:00:00Z",
        "updated_date": "2025-01-15T12:00:00Z",
        "quality": 0.8,
        "keywords": "postgresql,performance,index,query",
    }

    try:
        # データ変換
        converted_data = await conversion_engine.convert_data(
            "legacy_knowledge_to_entity", legacy_knowledge_data
        )

        print(f"Converted data: {json.dumps(converted_data, indent=2, default=str)}")

        # データ移行ツールの使用
        migration_tool = DataMigrationTool(conversion_engine)

        # 複数のレガシーデータを移行
        legacy_data_list = [legacy_knowledge_data]
        migrated_entities = await migration_tool.migrate_legacy_knowledge(
            legacy_data_list
        )

        print(f"Migrated {len(migrated_entities)} knowledge entities")

        # 移行レポート
        report = migration_tool.get_migration_report()
        print(f"Migration report: {json.dumps(report, indent=2, default=str)}")

    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
