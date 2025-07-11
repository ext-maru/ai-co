#!/usr/bin/env python3
"""
RAG Grimoire統合システム
既存のRAGシステムと新しいPostgreSQL + pgvectorの魔法書システムを統合
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import hashlib
from dataclasses import dataclass, field

from libs.grimoire_database import GrimoireDatabase, SpellMetadata
from libs.grimoire_vector_search import GrimoireVectorSearch, SearchQuery, SearchResult
from libs.grimoire_spell_evolution import EvolutionEngine, EvolutionType
from libs.enhanced_rag_manager import EnhancedRagManager as EnhancedRAGManager, VectorEmbedding
from libs.rag_manager import RagManager as RAGManager
from libs.knowledge_base_manager import KnowledgeBaseManager


@dataclass
class RagGrimoireConfig:
    """RAG Grimoire統合設定"""
    database_url: str = "postgresql://aicompany@localhost:5432/ai_company_grimoire"
    vector_dimensions: int = 1536
    search_threshold: float = 0.7
    max_search_results: int = 10
    enable_spell_evolution: bool = True
    enable_auto_indexing: bool = True
    batch_size: int = 100
    migration_mode: bool = False


class RagGrimoireIntegration:
    """RAG Grimoire統合クラス - 既存RAGシステムと魔法書システムの橋渡し"""

    def __init__(self, config: Optional[RagGrimoireConfig] = None):
        self.config = config or RagGrimoireConfig()
        self.logger = logging.getLogger(__name__)

        # 既存RAGシステム
        self.rag_manager = None
        self.enhanced_rag = None
        self.knowledge_manager = None

        # 新しい魔法書システム
        self.grimoire_db = None
        self.grimoire_search = None
        self.evolution_engine = None

        # 統合状態
        self.integration_active = False
        self.migration_stats = {
            "total_entries": 0,
            "migrated_entries": 0,
            "failed_entries": 0,
            "evolution_applied": 0
        }

    async def initialize(self):
        """統合システムを初期化"""
        try:
            # 既存RAGシステムの初期化
            await self._initialize_legacy_rag()

            # 新しい魔法書システムの初期化
            await self._initialize_grimoire_system()

            # 統合設定の適用
            await self._apply_integration_settings()

            self.integration_active = True
            self.logger.info("RAG Grimoire統合システムが正常に初期化されました")

        except Exception as e:
            self.logger.error(f"統合システム初期化エラー: {e}")
            raise

    async def _initialize_legacy_rag(self):
        """既存RAGシステムの初期化"""
        try:
            self.rag_manager = RAGManager()
            self.enhanced_rag = EnhancedRAGManager()
            self.knowledge_manager = KnowledgeBaseManager()

            self.logger.info("既存RAGシステムが初期化されました")

        except Exception as e:
            self.logger.warning(f"既存RAGシステム初期化に一部失敗: {e}")

    async def _initialize_grimoire_system(self):
        """新しい魔法書システムの初期化"""
        try:
            # 魔法書データベース
            self.grimoire_db = GrimoireDatabase(self.config.database_url)
            await self.grimoire_db.initialize()

            # ベクトル検索エンジン
            self.grimoire_search = GrimoireVectorSearch(
                database=self.grimoire_db
            )
            await self.grimoire_search.initialize()

            # 進化エンジン
            if self.config.enable_spell_evolution:
                self.evolution_engine = EvolutionEngine(
                    database=self.grimoire_db
                )
                await self.evolution_engine.initialize()

            self.logger.info("魔法書システムが初期化されました")

        except Exception as e:
            self.logger.error(f"魔法書システム初期化エラー: {e}")
            raise

    async def _apply_integration_settings(self):
        """統合設定の適用"""
        if self.config.enable_auto_indexing:
            # 自動インデックス化のセットアップ
            await self._setup_auto_indexing()

        if self.config.migration_mode:
            # 移行モードの設定
            await self._setup_migration_mode()

    async def search_unified(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """統合検索 - 既存RAGと魔法書システムを統合した検索"""
        if not self.integration_active:
            raise RuntimeError("統合システムが初期化されていません")

        limit = kwargs.get('limit', self.config.max_search_results)
        threshold = kwargs.get('threshold', self.config.search_threshold)

        # 結果を統合
        unified_results = []

        # 魔法書システムでの検索
        if self.grimoire_search:
            grimoire_query = SearchQuery(
                query_text=query,
                limit=limit,
                similarity_threshold=threshold,
                filters=kwargs.get('filters', {})
            )

            grimoire_results = await self.grimoire_search.search(grimoire_query)

            for result in grimoire_results:
                unified_results.append({
                    "id": result.spell_id,
                    "content": result.content,
                    "similarity_score": result.similarity_score,
                    "metadata": result.metadata,
                    "source": "grimoire_system",
                    "spell_name": result.spell_name,
                    "evolution_level": result.metadata.get('evolution_level', 0)
                })

        # 既存RAGシステムでの検索（フォールバック）
        if self.enhanced_rag and len(unified_results) < limit:
            try:
                legacy_results = self.enhanced_rag.search_similar_contexts(
                    query,
                    limit=limit - len(unified_results),
                    threshold=threshold
                )

                for result in legacy_results:
                    unified_results.append({
                        "id": result.get('id', 'legacy_' + str(hash(result.get('content', '')))),
                        "content": result.get('content', ''),
                        "similarity_score": result.get('score', 0.0),
                        "metadata": result.get('metadata', {}),
                        "source": "legacy_rag",
                        "category": result.get('category', 'unknown')
                    })
            except Exception as e:
                self.logger.warning(f"既存RAG検索エラー: {e}")

        # 結果の統合とソート
        unified_results.sort(key=lambda x: x['similarity_score'], reverse=True)

        return unified_results[:limit]

    async def add_knowledge_unified(self,
                                  spell_name: str,
                                  content: str,
                                  metadata: Optional[Dict[str, Any]] = None,
                                  **kwargs) -> str:
        """統合知識追加 - 魔法書システムと既存RAGに同期追加"""
        if not self.integration_active:
            raise RuntimeError("統合システムが初期化されていません")

        # SpellMetadataを適切なパラメータで作成
        from libs.grimoire_database import SpellType, MagicSchool

        spell_metadata = SpellMetadata(
            id=str(uuid.uuid4()),
            spell_name=spell_name,
            content=content,
            spell_type=SpellType.KNOWLEDGE,
            magic_school=MagicSchool.KNOWLEDGE_SAGE,
            tags=kwargs.get('tags', []),
            power_level=1,
            casting_frequency=0,
            last_cast_at=None,
            is_eternal=kwargs.get('is_eternal', False),
            evolution_history=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=1
        )

        # 魔法書システムに追加（辞書形式に変換）
        spell_data = {
            'spell_name': spell_name,
            'content': content,
            'spell_type': SpellType.KNOWLEDGE.value,
            'magic_school': MagicSchool.KNOWLEDGE_SAGE.value,
            'tags': kwargs.get('tags', []),
            'power_level': 1,
            'is_eternal': kwargs.get('is_eternal', False)
        }
        spell_id = await self.grimoire_db.create_spell(spell_data)

        # ベクトル化してインデックス追加
        if self.grimoire_search:
            await self.grimoire_search.index_spell(spell_id, spell_data)

        # 既存RAGシステムにも追加（互換性維持）
        if self.enhanced_rag:
            try:
                embedding = VectorEmbedding(
                    id=spell_id,
                    content=content,
                    embedding=await self._generate_embedding(content),
                    metadata=metadata or {}
                )
                self.enhanced_rag.add_embedding(embedding)
            except Exception as e:
                self.logger.warning(f"既存RAGへの追加エラー: {e}")

        self.logger.info(f"統合知識追加完了: {spell_name} (ID: {spell_id})")
        return spell_id

    async def migrate_legacy_knowledge(self,
                                     force: bool = False,
                                     dry_run: bool = False) -> Dict[str, Any]:
        """既存RAGシステムから魔法書システムへの移行"""
        if not self.integration_active:
            raise RuntimeError("統合システムが初期化されていません")

        migration_report = {
            "started_at": datetime.now().isoformat(),
            "total_processed": 0,
            "successfully_migrated": 0,
            "failed_migrations": 0,
            "duplicates_found": 0,
            "evolution_applied": 0,
            "errors": []
        }

        try:
            # 既存の知識ベースファイルを収集
            knowledge_files = []
            if self.knowledge_manager:
                knowledge_files = self.knowledge_manager.get_all_knowledge_files()

            migration_report["total_processed"] = len(knowledge_files)

            # バッチ処理で移行
            for i in range(0, len(knowledge_files), self.config.batch_size):
                batch = knowledge_files[i:i + self.config.batch_size]
                batch_result = await self._migrate_knowledge_batch(batch, dry_run)

                migration_report["successfully_migrated"] += batch_result["success_count"]
                migration_report["failed_migrations"] += batch_result["error_count"]
                migration_report["duplicates_found"] += batch_result["duplicate_count"]
                migration_report["evolution_applied"] += batch_result["evolution_count"]
                migration_report["errors"].extend(batch_result["errors"])

                # 進捗ログ
                progress = (i + len(batch)) / len(knowledge_files) * 100
                self.logger.info(f"移行進捗: {progress:.1f}% ({i + len(batch)}/{len(knowledge_files)})")

        except Exception as e:
            migration_report["errors"].append(str(e))
            self.logger.error(f"移行処理エラー: {e}")

        migration_report["completed_at"] = datetime.now().isoformat()

        # 移行レポートの保存
        await self._save_migration_report(migration_report)

        return migration_report

    async def _migrate_knowledge_batch(self,
                                     batch: List[Dict[str, Any]],
                                     dry_run: bool = False) -> Dict[str, int]:
        """知識ベースバッチ移行"""
        result = {
            "success_count": 0,
            "error_count": 0,
            "duplicate_count": 0,
            "evolution_count": 0,
            "errors": []
        }

        for file_info in batch:
            try:
                # ファイル内容の読み込み
                file_path = Path(file_info["path"])
                if not file_path.exists():
                    continue

                content = file_path.read_text(encoding='utf-8')
                spell_name = file_path.stem

                # 重複チェック
                if await self._check_spell_exists(spell_name):
                    result["duplicate_count"] += 1
                    continue

                if not dry_run:
                    # 魔法書システムに追加
                    metadata = {
                        "original_file": str(file_path),
                        "file_size": file_info["size"],
                        "modified_date": file_info["modified"],
                        "migration_date": datetime.now().isoformat(),
                        "source": "legacy_migration"
                    }

                    spell_id = await self.add_knowledge_unified(
                        spell_name=spell_name,
                        content=content,
                        metadata=metadata,
                        category="migrated_knowledge"
                    )

                    # 進化の適用（類似スペルとのマージ可能性チェック）
                    if self.evolution_engine:
                        evolution_applied = await self._check_and_apply_evolution(
                            spell_id, spell_name, content
                        )
                        if evolution_applied:
                            result["evolution_count"] += 1

                result["success_count"] += 1

            except Exception as e:
                result["error_count"] += 1
                result["errors"].append(f"ファイル {file_info.get('filename', 'unknown')}: {str(e)}")
                self.logger.error(f"バッチ移行エラー: {e}")

        return result

    async def _check_spell_exists(self, spell_name: str) -> bool:
        """スペルの存在チェック"""
        try:
            existing_spells = await self.grimoire_db.search_spells(
                query=spell_name,
                limit=1,
                exact_match=True
            )
            return len(existing_spells) > 0
        except Exception:
            return False

    async def _check_and_apply_evolution(self,
                                       spell_id: str,
                                       spell_name: str,
                                       content: str) -> bool:
        """進化の適用可能性チェックと実行"""
        try:
            if not self.evolution_engine:
                return False

            # 類似スペルの検索
            similar_spells = await self.grimoire_search.search(
                SearchQuery(
                    query_text=content[:500],  # 最初の500文字で類似検索
                    limit=5,
                    threshold=0.85  # 高い類似度
                )
            )

            # 進化の候補があるかチェック
            for similar in similar_spells:
                if similar.spell_id != spell_id:
                    # マージ可能性の判定
                    if await self._should_merge_spells(spell_id, similar.spell_id):
                        await self.evolution_engine.evolve_spell(
                            original_id=similar.spell_id,
                            evolved_data={"content": content, "spell_name": spell_name},
                            evolution_type=EvolutionType.MERGE,
                            reason="Legacy migration: similar content detected"
                        )
                        return True

            return False

        except Exception as e:
            self.logger.error(f"進化適用エラー: {e}")
            return False

    async def _should_merge_spells(self, spell_id1: str, spell_id2: str) -> bool:
        """スペルマージの判定"""
        try:
            # 簡単なマージ判定ロジック
            # 実際の実装では、より複雑な判定が必要
            spell1 = await self.grimoire_db.get_spell(spell_id1)
            spell2 = await self.grimoire_db.get_spell(spell_id2)

            if not spell1 or not spell2:
                return False

            # 内容の重複度チェック
            overlap = self._calculate_content_overlap(spell1.content, spell2.content)
            return overlap > 0.7  # 70%以上の重複でマージ候補

        except Exception:
            return False

    def _calculate_content_overlap(self, content1: str, content2: str) -> float:
        """コンテンツの重複度計算"""
        # 簡単な重複度計算（実際にはより高度なアルゴリズムを使用）
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    async def _generate_embedding(self, content: str) -> List[float]:
        """コンテンツの埋め込みベクトル生成"""
        # 実際の実装では、OpenAI APIやその他の埋め込みサービスを使用
        # ここではプレースホルダー
        import numpy as np
        return np.random.random(self.config.vector_dimensions).tolist()

    async def _save_migration_report(self, report: Dict[str, Any]):
        """移行レポートの保存"""
        reports_dir = Path("/home/aicompany/ai_co/migration_reports")
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = reports_dir / f"rag_migration_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.logger.info(f"移行レポートを保存: {report_file}")

    async def _setup_auto_indexing(self):
        """自動インデックス化のセットアップ"""
        # 実装: 新しいスペルの自動インデックス化
        pass

    async def _setup_migration_mode(self):
        """移行モードのセットアップ"""
        # 実装: 移行中の特別な処理
        pass

    async def get_integration_status(self) -> Dict[str, Any]:
        """統合システムの状態取得"""
        status = {
            "integration_active": self.integration_active,
            "grimoire_system_ready": self.grimoire_db is not None,
            "legacy_rag_available": self.enhanced_rag is not None,
            "knowledge_manager_available": self.knowledge_manager is not None,
            "migration_stats": self.migration_stats,
            "config": {
                "database_url": self.config.database_url,
                "vector_dimensions": self.config.vector_dimensions,
                "search_threshold": self.config.search_threshold,
                "max_search_results": self.config.max_search_results
            }
        }

        if self.grimoire_db:
            # 魔法書システムの統計情報
            try:
                stats = await self.grimoire_db.get_statistics()
                status["grimoire_stats"] = stats
            except Exception as e:
                status["grimoire_stats"] = {"error": str(e)}

        return status

    async def cleanup(self):
        """リソースのクリーンアップ"""
        try:
            if self.grimoire_db:
                await self.grimoire_db.close()

            if self.grimoire_search:
                await self.grimoire_search.cleanup()

            if self.evolution_engine:
                await self.evolution_engine.cleanup()

            self.integration_active = False
            self.logger.info("RAG Grimoire統合システムのクリーンアップ完了")

        except Exception as e:
            self.logger.error(f"クリーンアップエラー: {e}")


# 使用例とテスト用のヘルパー関数
async def test_integration():
    """統合システムのテスト"""
    integration = RagGrimoireIntegration()

    try:
        await integration.initialize()

        # 統合検索のテスト
        results = await integration.search_unified("テスト", limit=5)
        print(f"検索結果: {len(results)}件")

        # 知識追加のテスト
        spell_id = await integration.add_knowledge_unified(
            spell_name="test_spell",
            content="これはテスト用のスペルです",
            metadata={"test": True}
        )
        print(f"スペル追加: {spell_id}")

        # 状態確認
        status = await integration.get_integration_status()
        print(f"統合システム状態: {status}")

    finally:
        await integration.cleanup()


if __name__ == "__main__":
    asyncio.run(test_integration())
