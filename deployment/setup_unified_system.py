#!/usr/bin/env python3
"""
Elders Guild 統合システムセットアップスクリプト v1.0
統一アーキテクチャの初期化とデータマイグレーション
"""

import json
import logging
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from integration.unified_entity_manager import (
        BaseEntity,
        IncidentEntity,
        KnowledgeEntity,
        TaskEntity,
        UnifiedEntityManager,
        create_incident_entity,
        create_knowledge_entity,
        create_task_entity,
    )
    from integration.unified_rag_manager import UnifiedRAGManager
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you are running from the correct directory.")
    sys.exit(1)

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UnifiedSystemSetup:
    """統合システムセットアップマネージャー"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.data_dir = self.project_root / "data"
        self.knowledge_base_dir = self.project_root / "knowledge_base"
        self.integration_dir = self.project_root / "integration"

        # マネージャーインスタンス
        self.entity_manager = None
        self.rag_manager = None

        # 統計情報
        self.migration_stats = {
            "knowledge_files_processed": 0,
            "incidents_migrated": 0,
            "tasks_migrated": 0,
            "relationships_created": 0,
            "errors": [],
        }

    def setup_complete_system(self):
        """完全なシステムセットアップ実行"""
        logger.info("=== Elders Guild 統合システムセットアップ開始 ===")

        try:
            # 1.0 ディレクトリ作成
            self._create_directories()

            # 2.0 データベース初期化
            self._initialize_database()

            # 3.0 マネージャー初期化
            self._initialize_managers()

            # 4.0 既存データのマイグレーション
            self._migrate_existing_data()

            # 5.0 サンプルデータ作成
            self._create_sample_data()

            # 6.0 初期関係性構築
            self._build_initial_relationships()

            # 7.0 検証とテスト
            self._verify_system()

            # 8.0 レポート生成
            self._generate_setup_report()

            logger.info("=== 統合システムセットアップ完了 ===")
            return True

        except Exception as e:
            logger.error(f"セットアップ失敗: {e}")
            self.migration_stats["errors"].append(str(e))
            return False

    def _create_directories(self):
        """必要なディレクトリ作成"""
        logger.info("ディレクトリ構造作成中...")

        directories = [
            self.data_dir,
            self.integration_dir,
            self.integration_dir / "backups",
            self.integration_dir / "logs",
            self.integration_dir / "temp",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"ディレクトリ作成: {directory}")

    def _initialize_database(self):
        """データベース初期化"""
        logger.info("統合データベース初期化中...")

        # 既存データベースのバックアップ
        db_path = self.data_dir / "unified_entities.db"
        if db_path.exists():
            backup_path = (
                self.integration_dir
                / "backups"
                / f"unified_entities_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            shutil.copy2(db_path, backup_path)
            logger.info(f"既存DBをバックアップ: {backup_path}")

        # エンティティマネージャーによる初期化
        try:
            self.entity_manager = UnifiedEntityManager()
            logger.info("統合データベース初期化完了")
        except Exception as e:
            logger.error(f"データベース初期化エラー: {e}")
            raise

    def _initialize_managers(self):
        """マネージャー初期化"""
        logger.info("統合マネージャー初期化中...")

        try:
            if not self.entity_manager:
                self.entity_manager = UnifiedEntityManager()

            self.rag_manager = UnifiedRAGManager(self.entity_manager)
            logger.info("統合マネージャー初期化完了")
        except Exception as e:
            logger.error(f"マネージャー初期化エラー: {e}")
            raise

    def _migrate_existing_data(self):
        """既存データのマイグレーション"""
        logger.info("既存データマイグレーション開始...")

        # 1.0 ナレッジベースファイルのマイグレーション
        self._migrate_knowledge_base_files()

        # 2.0 既存SQLiteデータベースのマイグレーション
        self._migrate_existing_databases()

        # 3.0 設定ファイルの統合
        self._migrate_configuration_files()

        logger.info("データマイグレーション完了")

    def _migrate_knowledge_base_files(self):
        """ナレッジベースファイルのマイグレーション"""
        logger.info("ナレッジベースファイル処理中...")

        if not self.knowledge_base_dir.exists():
            logger.warning(f"ナレッジベースディレクトリが見つかりません: {self.knowledge_base_dir}")
            return

        # Markdownファイルの処理
        md_files = list(self.knowledge_base_dir.glob("**/*.md"))

        for md_file in md_files:
            try:
                self._process_knowledge_file(md_file)
                self.migration_stats["knowledge_files_processed"] += 1
            except Exception as e:
                error_msg = f"ナレッジファイル処理エラー {md_file}: {e}"
                logger.error(error_msg)
                self.migration_stats["errors"].append(error_msg)

        logger.info(
            f"ナレッジファイル処理完了: {self.migration_stats['knowledge_files_processed']}件"
        )

    def _process_knowledge_file(self, file_path: Path):
        """個別ナレッジファイルの処理"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # ファイル名から情報抽出
            title = file_path.stem.replace("_", " ").title()

            # カテゴリ推定
            category = self._determine_category_from_path(file_path)

            # ドメイン推定
            domain = self._determine_domain_from_content(content)

            # 知識エンティティ作成
            knowledge_entity = create_knowledge_entity(
                title=title, content=content, confidence_score=0.8, domain=domain
            )

            # メタデータ設定
            knowledge_entity.metadata.update(
                {
                    "source_file": str(file_path.relative_to(self.project_root)),
                    "category": category,
                    "tags": self._extract_tags_from_content(content),
                    "file_size": file_path.stat().st_size,
                    "last_modified": datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    ).isoformat(),
                }
            )

            # エンティティ保存
            entity_id = self.entity_manager.create_entity(knowledge_entity)
            logger.debug(f"ナレッジエンティティ作成: {entity_id} - {title}")

        except Exception as e:
            logger.error(f"ナレッジファイル処理エラー {file_path}: {e}")
            raise

    def _migrate_existing_databases(self):
        """既存SQLiteデータベースのマイグレーション"""
        logger.info("既存データベースマイグレーション中...")

        # 既存のデータベースファイルを探索
        db_files = [
            self.project_root / "task_history.db",
            self.project_root / "incident_management.db",
            self.project_root / "worker_status.db",
            self.project_root / "data" / "task_history.db",
        ]

        for db_file in db_files:
            if db_file.exists():
                try:
                    self._migrate_database_file(db_file)
                except Exception as e:
                    error_msg = f"データベースマイグレーションエラー {db_file}: {e}"
                    logger.error(error_msg)
                    self.migration_stats["errors"].append(error_msg)

    def _migrate_database_file(self, db_path: Path):
        """個別データベースファイルのマイグレーション"""
        logger.info(f"データベースマイグレーション: {db_path}")

        try:
            with sqlite3connect(db_path) as conn:
                conn.row_factory = sqlite3Row
                cursor = conn.cursor()

                # テーブル一覧取得
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]

                for table in tables:
                    self._migrate_table_data(cursor, table, db_path.stem)

        except Exception as e:
            logger.error(f"データベースファイル処理エラー {db_path}: {e}")
            raise

    def _migrate_table_data(
        self, cursor: sqlite3Cursor, table_name: str, db_source: str
    ):
        """テーブルデータのマイグレーション"""
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            if not rows:
                return

            logger.debug(f"テーブルマイグレーション: {table_name} ({len(rows)}行)")

            for row in rows:
                row_dict = dict(row)

                # テーブル名に基づいてエンティティタイプを決定
                entity_type = self._determine_entity_type_from_table(table_name)

                if entity_type == "incident":
                    self._create_incident_from_row(row_dict, db_source)
                    self.migration_stats["incidents_migrated"] += 1
                elif entity_type == "task":
                    self._create_task_from_row(row_dict, db_source)
                    self.migration_stats["tasks_migrated"] += 1
                else:
                    # 汎用エンティティとして処理
                    self._create_generic_entity_from_row(
                        row_dict, table_name, db_source
                    )

        except Exception as e:
            logger.error(f"テーブルデータマイグレーションエラー {table_name}: {e}")
            raise

    def _create_incident_from_row(self, row_data: Dict, source: str):
        """行データからインシデントエンティティ作成"""
        try:
            title = (
                row_data.get("title")
                or row_data.get("description", "Unknown Incident")[:50]
            )
            content = row_data.get("description") or row_data.get("details", "")

            incident_entity = create_incident_entity(
                title=title,
                content=content,
                severity=row_data.get("severity", "medium"),
                affected_systems=[],
            )

            # メタデータ設定
            incident_entity.metadata.update(
                {
                    "source_db": source,
                    "migrated_from": "legacy_database",
                    "original_id": str(row_data.get("id", "")),
                }
            )

            # インシデント固有データ設定
            incident_entity.incident_data.update(
                {
                    "status": row_data.get("status", "open"),
                    "root_cause": row_data.get("root_cause", ""),
                    "resolution_steps": [],
                }
            )

            entity_id = self.entity_manager.create_entity(incident_entity)
            logger.debug(f"インシデントエンティティ作成: {entity_id}")

        except Exception as e:
            logger.error(f"インシデント作成エラー: {e}")
            raise

    def _create_task_from_row(self, row_data: Dict, source: str):
        """行データからタスクエンティティ作成"""
        try:
            title = row_data.get("title") or row_data.get("task_name", "Unknown Task")
            content = row_data.get("description") or row_data.get("details", "")

            task_entity = create_task_entity(
                title=title,
                content=content,
                task_type=row_data.get("task_type", "general"),
                assigned_worker=row_data.get("assigned_worker"),
            )

            # メタデータ設定
            task_entity.metadata.update(
                {
                    "source_db": source,
                    "migrated_from": "legacy_database",
                    "original_id": str(row_data.get("id", "")),
                }
            )

            # タスク固有データ設定
            task_entity.task_data.update(
                {
                    "status": row_data.get("status", "pending"),
                    "completion_percentage": row_data.get("completion_percentage", 0),
                }
            )

            entity_id = self.entity_manager.create_entity(task_entity)
            logger.debug(f"タスクエンティティ作成: {entity_id}")

        except Exception as e:
            logger.error(f"タスク作成エラー: {e}")
            raise

    def _create_generic_entity_from_row(
        self, row_data: Dict, table_name: str, source: str
    ):
        """行データから汎用エンティティ作成"""
        try:
            title = (
                row_data.get("title")
                or row_data.get("name")
                or f"{table_name}_{row_data.get('id', 'unknown')}"
            )

            content = (
                row_data.get("description")
                or row_data.get("content")
                or json.dumps(row_data, indent=2)
            )

            entity = BaseEntity(id="", type="system", title=title, content=content)

            entity.metadata.update(
                {
                    "source_db": source,
                    "source_table": table_name,
                    "migrated_from": "legacy_database",
                    "original_data": row_data,
                }
            )

            entity_id = self.entity_manager.create_entity(entity)
            logger.debug(f"汎用エンティティ作成: {entity_id}")

        except Exception as e:
            logger.error(f"汎用エンティティ作成エラー: {e}")
            raise

    def _migrate_configuration_files(self):
        """設定ファイルの統合"""
        logger.info("設定ファイル統合中...")

        config_files = [
            self.project_root / "config" / "config.json",
            self.project_root / "config" / "slack_config.json",
            self.project_root / "config" / "error_intelligence.json",
        ]

        for config_file in config_files:
            if config_file.exists():
                try:
                    self._process_config_file(config_file)
                except Exception as e:
                    error_msg = f"設定ファイル処理エラー {config_file}: {e}"
                    logger.error(error_msg)
                    self.migration_stats["errors"].append(error_msg)

    def _process_config_file(self, config_path: Path):
        """設定ファイルの処理"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # 設定を知識エンティティとして保存
            knowledge_entity = create_knowledge_entity(
                title=f"システム設定: {config_path.stem}",
                content=json.dumps(config_data, indent=2, ensure_ascii=False),
                confidence_score=1.0,
                domain="system",
            )

            knowledge_entity.metadata.update(
                {
                    "source_file": str(config_path.relative_to(self.project_root)),
                    "category": "configuration",
                    "tags": ["configuration", "system", config_path.stem],
                }
            )

            entity_id = self.entity_manager.create_entity(knowledge_entity)
            logger.debug(f"設定エンティティ作成: {entity_id} - {config_path.stem}")

        except Exception as e:
            logger.error(f"設定ファイル処理エラー {config_path}: {e}")
            raise

    def _create_sample_data(self):
        """サンプルデータ作成"""
        logger.info("サンプルデータ作成中...")

        # サンプル知識
        sample_knowledge = [
            {
                "title": "Python例外処理ベストプラクティス",
                "content": "try-except文を使用する際は、具体的な例外クラスをキャッチし、適切なログ出力を行うこと。",
                "domain": "development",
                "tags": ["python", "exception", "best-practice"],
            },
            {
                "title": "APIタイムアウト対処法",
                "content": "API呼び出し時のタイムアウトは、リトライ機構と指数バックオフを実装して対処する。",
                "domain": "operations",
                "tags": ["api", "timeout", "retry"],
            },
        ]

        # サンプルインシデント
        sample_incidents = [
            {
                "title": "データベース接続エラー",
                "content": "PostgreSQLへの接続が断続的に失敗する問題が発生。",
                "severity": "high",
                "affected_systems": ["database", "api_server"],
            },
            {
                "title": "メモリリークによるパフォーマンス低下",
                "content": "長時間稼働後にメモリ使用量が増加し続ける問題。",
                "severity": "medium",
                "affected_systems": ["worker_processes"],
            },
        ]

        # サンプルデータ作成
        try:
            for knowledge_data in sample_knowledge:
                entity = create_knowledge_entity(
                    title=knowledge_data["title"],
                    content=knowledge_data["content"],
                    domain=knowledge_data["domain"],
                )
                entity.metadata["tags"] = knowledge_data["tags"]
                self.entity_manager.create_entity(entity)

            for incident_data in sample_incidents:
                entity = create_incident_entity(
                    title=incident_data["title"],
                    content=incident_data["content"],
                    severity=incident_data["severity"],
                    affected_systems=incident_data["affected_systems"],
                )
                self.entity_manager.create_entity(entity)

            logger.info("サンプルデータ作成完了")

        except Exception as e:
            logger.error(f"サンプルデータ作成エラー: {e}")
            raise

    def _build_initial_relationships(self):
        """初期関係性構築"""
        logger.info("初期関係性構築中...")

        try:
            # エンティティ一覧取得
            all_entities = self.entity_manager.list_entities(limit=1000)

            # 関連性の自動検出と作成
            for i, entity1 in enumerate(all_entities):
                for entity2 in all_entities[i + 1 :]:
                    relationship_type = self._detect_relationship(entity1, entity2)
                    if relationship_type:
                        from integration.unified_entity_manager import (
                            EntityRelationship,
                        )

                        rel = EntityRelationship(
                            source_id=entity1.id,
                            target_id=entity2.id,
                            relationship_type=relationship_type,
                            weight=0.5,
                            created_by="system_setup",
                        )

                        self.entity_manager.create_relationship(rel)
                        self.migration_stats["relationships_created"] += 1

            logger.info(f"関係性構築完了: {self.migration_stats['relationships_created']}件")

        except Exception as e:
            logger.error(f"関係性構築エラー: {e}")
            raise

    def _verify_system(self):
        """システム検証"""
        logger.info("システム検証中...")

        try:
            # 基本統計取得
            stats = self.entity_manager.get_statistics()
            logger.info(f"エンティティ統計: {stats}")

            # 検索テスト
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                search_result = loop.run_until_complete(
                    self.rag_manager.search("API エラー")
                )
                logger.info(f"検索テスト成功: {search_result.total_found}件の結果")
            finally:
                loop.close()

            logger.info("システム検証完了")

        except Exception as e:
            logger.error(f"システム検証エラー: {e}")
            raise

    def _generate_setup_report(self):
        """セットアップレポート生成"""
        logger.info("セットアップレポート生成中...")

        report = {
            "setup_timestamp": datetime.now().isoformat(),
            "migration_statistics": self.migration_stats,
            "system_statistics": self.entity_manager.get_statistics(),
            "setup_status": "success"
            if not self.migration_stats["errors"]
            else "partial_success",
        }

        # レポートファイル出力
        report_path = (
            self.integration_dir
            / f"setup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"セットアップレポート生成完了: {report_path}")

        # コンソール出力
        print("\n" + "=" * 60)
        print("Elders Guild 統合システムセットアップ完了")
        print("=" * 60)
        print(f"ナレッジファイル処理: {self.migration_stats['knowledge_files_processed']}件")
        print(f"インシデントマイグレーション: {self.migration_stats['incidents_migrated']}件")
        print(f"タスクマイグレーション: {self.migration_stats['tasks_migrated']}件")
        print(f"関係性作成: {self.migration_stats['relationships_created']}件")

        if self.migration_stats["errors"]:
            print(f"エラー: {len(self.migration_stats['errors'])}件")
            print("詳細はログファイルを確認してください。")

        print(f"\nレポートファイル: {report_path}")
        print("=" * 60)

    # ============================================
    # ユーティリティメソッド
    # ============================================

    def _determine_category_from_path(self, file_path: Path) -> str:
        """ファイルパスからカテゴリを推定"""
        path_parts = file_path.parts

        if "incident" in str(file_path).lower():
            return "incident"
        elif "task" in str(file_path).lower():
            return "task"
        elif "guide" in str(file_path).lower() or "doc" in str(file_path).lower():
            return "documentation"
        elif "config" in str(file_path).lower():
            return "configuration"
        else:
            return "knowledge"

    def _determine_domain_from_content(self, content: str) -> str:
        """コンテンツからドメインを推定"""
        content_lower = content.lower()

        if any(
            word in content_lower
            for word in ["python", "javascript", "code", "function"]
        ):
            return "development"
        elif any(
            word in content_lower for word in ["server", "database", "api", "deploy"]
        ):
            return "operations"
        elif any(
            word in content_lower for word in ["error", "incident", "problem", "issue"]
        ):
            return "incident"
        elif any(word in content_lower for word in ["test", "testing", "quality"]):
            return "testing"
        else:
            return "general"

    def _extract_tags_from_content(self, content: str) -> List[str]:
        """コンテンツからタグを抽出"""
        content_lower = content.lower()

        potential_tags = [
            "python",
            "javascript",
            "api",
            "database",
            "error",
            "fix",
            "guide",
            "documentation",
            "best-practice",
            "troubleshooting",
            "configuration",
            "system",
            "worker",
            "task",
            "incident",
        ]

        found_tags = [tag for tag in potential_tags if tag in content_lower]
        return found_tags[:5]  # 最大5個

    def _determine_entity_type_from_table(self, table_name: str) -> str:
        """テーブル名からエンティティタイプを推定"""
        table_lower = table_name.lower()

        if "incident" in table_lower or "error" in table_lower:
            return "incident"
        elif "task" in table_lower or "job" in table_lower:
            return "task"
        elif "knowledge" in table_lower or "kb" in table_lower:
            return "knowledge"
        else:
            return "system"

    def _detect_relationship(
        self, entity1: BaseEntity, entity2: BaseEntity
    ) -> Optional[str]:
        """エンティティ間の関係性を検出"""
        # 簡易的な関係性検出

        # インシデントと知識の関係
        if isinstance(entity1, IncidentEntity) and isinstance(entity2, KnowledgeEntity):
            if any(
                tag in entity2.metadata.get("tags", [])
                for tag in ["fix", "solution", "resolve"]
            ):
                return "resolved_by"

        # 同じタグを持つエンティティ
        tags1 = set(entity1.metadata.get("tags", []))
        tags2 = set(entity2.metadata.get("tags", []))
        if tags1 & tags2:  # 共通タグがある
            return "related_to"

        # 同じドメインの知識エンティティ
        if isinstance(entity1, KnowledgeEntity) and isinstance(
            entity2, KnowledgeEntity
        ):
            domain1 = entity1.knowledge_data.get("domain")
            domain2 = entity2.knowledge_data.get("domain")
            if domain1 == domain2 and domain1 != "general":
                return "related_to"

        return None


def main():
    """メイン実行関数"""
    print("Elders Guild 統合システムセットアップを開始します...")

    setup = UnifiedSystemSetup()
    success = setup.setup_complete_system()

    if success:
        print("セットアップが正常に完了しました。")
        sys.exit(0)
    else:
        print("セットアップ中にエラーが発生しました。ログを確認してください。")
        sys.exit(1)


if __name__ == "__main__":
    main()
