#!/usr/bin/env python3
"""
Knowledge Grimoire アダプター
既存のKnowledgeBaseManagerを魔法書システムと連携させる
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from libs.knowledge_base_manager import KnowledgeBaseManager
from libs.rag_grimoire_integration import RagGrimoireConfig, RagGrimoireIntegration


class KnowledgeGrimoireAdapter:
    """Knowledge Grimoire アダプター - 既存の知識管理と魔法書システムの連携"""

    def __init__(self, grimoire_enabled: bool = True):
        """初期化メソッド"""
        self.logger = logging.getLogger(__name__)
        self.grimoire_enabled = grimoire_enabled
        self.use_mock_grimoire = False

        # 既存システム
        self.knowledge_manager = KnowledgeBaseManager()

        # 新しい魔法書システム
        self.grimoire_integration = None
        if grimoire_enabled:
            try:
                # PostgreSQL接続を試行
                config = RagGrimoireConfig(
                    database_url=os.getenv(
                        "GRIMOIRE_DATABASE_URL", "postgresql://localhost/grimoire"
                    ),
                    enable_spell_evolution=True,
                    enable_auto_indexing=True,
                    migration_mode=True,
                )
                self.grimoire_integration = RagGrimoireIntegration(config)
                self.logger.info("魔法書統合システムを初期化")
            except Exception as e:
                self.logger.warning(f"PostgreSQL魔法書システム初期化失敗: {e}")
                # フォールバック: モックGrimoireデータベースを使用
                try:
                    from libs.mock_grimoire_database import (
                        MockGrimoireDatabase,
                        MockGrimoireVectorSearch,
                    )

                    self.mock_database = MockGrimoireDatabase()
                    self.mock_search = MockGrimoireVectorSearch(self.mock_database)
                    self.logger.info(
                        "🎭 モックGrimoireデータベースを使用（PostgreSQL未接続）"
                    )
                    self.grimoire_enabled = True
                    self.use_mock_grimoire = True
                except Exception as mock_e:
                    self.logger.error(f"モックGrimoireも初期化失敗: {mock_e}")
                    self.grimoire_enabled = False
                    self.use_mock_grimoire = False

    async def initialize_async(self):
        """非同期初期化"""
        if self.grimoire_enabled and self.grimoire_integration:
            try:
                await self.grimoire_integration.initialize()
                self.logger.info("魔法書統合システムが初期化されました")
            except Exception as e:
                self.logger.error(f"魔法書システム初期化エラー: {e}")
                self.grimoire_enabled = False

    def get_knowledge(self, topic: str) -> Optional[str]:
        """トピックに関連するナレッジを取得（既存+魔法書の統合）"""
        # 既存システムからの取得
        legacy_knowledge = self.knowledge_manager.get_knowledge(topic)

        if not self.grimoire_enabled:
            return legacy_knowledge

        # 魔法書システムからの取得
        try:
            # モックGrimoireを使用している場合
            if self.use_mock_grimoire:
                grimoire_results = self.mock_database.search_spells(topic, limit=3)
            else:
                # PostgreSQL Grimoireを使用（直接検索で非同期問題を回避）
                grimoire_results = self._direct_postgresql_search(topic, limit=3)

            grimoire_knowledge = []
            for result in grimoire_results:
                grimoire_knowledge.append(
                    f"""
## 📜 {result.get('spell_name', result.get('id', 'unknown'))} (魔法書)
スコア: {result.get('similarity_score', 0.5):0.3f} | ソース: {result.get('source', 'mock_grimoire')}

{result.get('content', '')}
"""
                )

            # 結果の統合
            combined_knowledge = []
            if legacy_knowledge:
                combined_knowledge.append("# 📚 従来の知識ベース")
                combined_knowledge.append(legacy_knowledge)

            if grimoire_knowledge:
                combined_knowledge.append("\n# 🔮 魔法書システム")
                combined_knowledge.extend(grimoire_knowledge)

            return (
                "\n\n---\n\n".join(combined_knowledge) if combined_knowledge else None
            )

        except Exception as e:
            self.logger.error(f"魔法書検索エラー: {e}")
            return legacy_knowledge

    def _direct_postgresql_search(
        self, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """PostgreSQLから直接検索（非同期ループ問題回避）"""
        try:
            import json
            import subprocess

            # psqlコマンドで直接検索
            db_url = os.getenv(
                "GRIMOIRE_DATABASE_URL",
                "postgresql://aicompany@localhost:5432/ai_company_grimoire",
            )

            sql_query = f"""
            SELECT spell_name, content, created_at
            FROM knowledge_grimoire
            WHERE content ILIKE '%{query}%'
            ORDER BY created_at SHA256C
            LIMIT {limit};
            """

            result = subprocess.run(
                ["psql", db_url, "-t", "-A", "-F", "|||", "-c", sql_query],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0 and result.stdout.strip():
                rows = []
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        parts = line.split("|||")
                        if len(parts) >= 2:
                            rows.append(
                                {
                                    "spell_name": parts[0],
                                    "content": parts[1][:1000]
                                    + ("..." if len(parts[1]) > 1000 else ""),
                                    "similarity_score": 0.8,
                                    "source": "postgresql_grimoire",
                                }
                            )
                return rows
            else:
                self.logger.warning(f"PostgreSQL search failed: {result.stderr}")
                return []

        except Exception as e:
            self.logger.error(f"Direct PostgreSQL search error: {e}")
            return []

    def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """ナレッジベース内を検索（統合検索）"""
        # 既存システムでの検索
        legacy_results = self.knowledge_manager.search_knowledge(query)

        if not self.grimoire_enabled:
            return legacy_results

        # 魔法書システムでの検索
        try:
            # モックGrimoireを使用している場合
            if self.use_mock_grimoire:
                grimoire_results = self.mock_database.search_spells(query, limit=10)
            else:
                # PostgreSQL Grimoireを使用
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    grimoire_results = loop.run_until_complete(
                        self.grimoire_integration.search_unified(query, limit=10)
                    )
                finally:
                    loop.close()

            # 結果の統合とフォーマット
            combined_results = []

            # 既存システムの結果を追加
            for result in legacy_results:
                result["source_system"] = "legacy"
                combined_results.append(result)

            # 魔法書システムの結果を追加
            for result in grimoire_results:
                combined_results.append(
                    {
                        "file": result.get("spell_name", result.get("id", "unknown")),
                        "line": 1,
                        "context": result.get("content", "")[:200] + "...",
                        "match": (
                            result.get("content", "").split("\n")[0]
                            if result.get("content")
                            else ""
                        ),
                        "similarity_score": result.get("similarity_score", 0.5),
                        "source_system": "grimoire",
                        "spell_id": result.get("id", "unknown"),
                    }
                )

            # スコアでソート（魔法書の結果を優先）
            combined_results.sort(
                key=lambda x: (
                    x.get("similarity_score", 0.0)
                    if x.get("source_system") == "grimoire"
                    else 0.0
                ),
                reverse=True,
            )

            return combined_results

        except Exception as e:
            self.logger.error(f"統合検索エラー: {e}")
            return legacy_results

    def add_knowledge(
        self,
        spell_name: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        save_to_legacy: bool = True,
    ) -> Dict[str, Any]:
        """新しい知識を追加（魔法書システム優先）"""
        result = {
            "spell_name": spell_name,
            "legacy_saved": False,
            "grimoire_saved": False,
            "spell_id": None,
            "error": None,
        }

        # 魔法書システムに追加
        if self.grimoire_enabled:
            try:
                # モックGrimoireを使用している場合
                if self.use_mock_grimoire:
                    spell_id = self.mock_database.add_spell(
                        spell_name=spell_name, content=content, metadata=metadata or {}
                    )
                else:
                    # PostgreSQL Grimoireを使用
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    try:
                        spell_id = loop.run_until_complete(
                            self.grimoire_integration.add_knowledge_unified(
                                spell_name=spell_name,
                                content=content,
                                metadata=metadata or {},
                                category="user_added",
                            )
                        )
                    finally:
                        loop.close()

                result["grimoire_saved"] = True
                result["spell_id"] = spell_id
                self.logger.info(f"魔法書システムに知識を追加: {spell_name}")

            except Exception as e:
                result["error"] = str(e)
                self.logger.error(f"魔法書システムへの追加エラー: {e}")

        # 既存システムにも保存（バックアップとして）
        if save_to_legacy:
            try:
                # 既存システム用のファイル保存
                knowledge_file = (
                    Path("/home/aicompany/ai_co/knowledge_base") / f"{spell_name}.md"
                )

                content_with_metadata = f"""# {spell_name}

{content}

---
_追加日時: {datetime.now().isoformat()}_
_メタデータ: {metadata or {}}_
"""

                knowledge_file.write_text(content_with_metadata, encoding="utf-8")
                result["legacy_saved"] = True
                self.logger.info(f"既存システムに知識を保存: {spell_name}")

            except Exception as e:
                if not result["error"]:
                    result["error"] = str(e)
                self.logger.error(f"既存システムへの保存エラー: {e}")

        return result

    def get_system_status(self) -> Dict[str, Any]:
        """システム状態の取得"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "legacy_system": {
                "available": True,
                "knowledge_files": len(
                    self.knowledge_manager.get_all_knowledge_files()
                ),
            },
            "grimoire_system": {
                "enabled": self.grimoire_enabled,
                "available": False,
                "using_mock": self.use_mock_grimoire,
                "stats": {},
            },
        }

        # 魔法書システムの状態
        if self.grimoire_enabled:
            if self.use_mock_grimoire:
                # モックGrimoireの状態
                try:
                    mock_stats = self.mock_database.get_stats()
                    status["grimoire_system"]["available"] = True
                    status["grimoire_system"]["stats"] = mock_stats
                    status["grimoire_system"]["type"] = "mock_file_based"
                except Exception as e:
                    status["grimoire_system"]["error"] = str(e)
            elif self.grimoire_integration:
                # PostgreSQL Grimoireの状態
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    try:
                        grimoire_status = loop.run_until_complete(
                            self.grimoire_integration.get_integration_status()
                        )

                        status["grimoire_system"]["available"] = grimoire_status[
                            "integration_active"
                        ]
                        status["grimoire_system"]["stats"] = grimoire_status.get(
                            "grimoire_stats", {}
                        )
                        status["grimoire_system"]["type"] = "postgresql_pgvector"
                    finally:
                        loop.close()

                except Exception as e:
                    status["grimoire_system"]["error"] = str(e)

        return status

    def migrate_all_knowledge(self, dry_run: bool = True) -> Dict[str, Any]:
        """全ての既存知識を魔法書システムに移行"""
        if not self.grimoire_enabled:
            return {"error": "魔法書システムが無効です"}

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 統合システムの初期化
            loop.run_until_complete(self.grimoire_integration.initialize())

            # 移行の実行
            migration_report = loop.run_until_complete(
                self.grimoire_integration.migrate_legacy_knowledge(
                    dry_run=dry_run, force=False
                )
            )

            return migration_report

        except Exception as e:
            return {"error": str(e)}
        finally:
            try:
                loop.close()
            except:
                pass

    async def cleanup_async(self):
        """非同期クリーンアップ"""
        if self.grimoire_integration:
            try:
                await self.grimoire_integration.cleanup()
            except Exception as e:
                self.logger.error(f"クリーンアップエラー: {e}")


# 4賢者システム統合用のラッパー
class KnowledgeSageGrimoireIntegration(KnowledgeGrimoireAdapter):
    """ナレッジ賢者 + 魔法書システム統合"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(grimoire_enabled=True)
        self.sage_type = "Knowledge Sage + Grimoire"
        self.wisdom_level = "unified_knowledge_system"
        self.collaboration_mode = True
        self.knowledge_evolution_active = True

        self.logger.info(
            f"📚🔮 {self.sage_type} 初期化完了 - 統合知識システムアクティブ"
        )

    def consult_unified_wisdom(self, topic: str) -> Optional[str]:
        """統合知恵の相談 - 魔法書と従来システムの統合検索"""
        return self.get_knowledge(topic)

    def evolve_knowledge(
        self,
        spell_name: str,
        new_content: str,
        evolution_reason: str = "Knowledge evolution",
    ) -> Dict[str, Any]:
        """知識の進化 - 魔法書システムの進化機能を使用"""
        if not self.grimoire_enabled:
            return {"error": "魔法書システムが無効です"}

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # まず類似の呪文を検索
            similar_spells = loop.run_until_complete(
                self.grimoire_integration.search_unified(
                    spell_name, limit=1, threshold=0.8
                )
            )

            if similar_spells:
                # 既存の呪文を進化
                original_spell = similar_spells[0]

                # 進化エンジンがあれば使用
                if (
                    hasattr(self.grimoire_integration, "evolution_engine")
                    and self.grimoire_integration.evolution_engine
                ):
                    evolved_spell_id = loop.run_until_complete(
                        self.grimoire_integration.evolution_engine.evolve_spell(
                            original_id=original_spell["id"],
                            evolved_data={
                                "content": new_content,
                                "spell_name": spell_name,
                            },
                            evolution_type="enhance",  # EvolutionType.ENHANCE
                            reason=evolution_reason,
                        )
                    )

                    return {
                        "evolved": True,
                        "original_spell_id": original_spell["id"],
                        "evolved_spell_id": evolved_spell_id,
                        "evolution_type": "enhance",
                    }

            # 新しい呪文として追加
            spell_id = loop.run_until_complete(
                self.grimoire_integration.add_knowledge_unified(
                    spell_name=spell_name,
                    content=new_content,
                    metadata={"evolution_reason": evolution_reason},
                    category="evolved_knowledge",
                )
            )

            return {
                "evolved": True,
                "spell_id": spell_id,
                "evolution_type": "new_spell",
            }

        except Exception as e:
            return {"error": str(e)}
        finally:
            try:
                loop.close()
            except:
                pass


if __name__ == "__main__":
    # テスト実行
    async def test_adapter():
        """test_adapterテストメソッド"""
        adapter = KnowledgeGrimoireAdapter()
        await adapter.initialize_async()

        # 検索テスト
        knowledge = adapter.get_knowledge("test")
        print(f"取得した知識: {len(knowledge) if knowledge else 0}文字")

        # 追加テスト
        result = adapter.add_knowledge(
            "test_spell", "これはテスト用の魔法です", {"test": True}
        )
        print(f"追加結果: {result}")

        # 状態確認
        status = adapter.get_system_status()
        print(f"システム状態: {status}")

        await adapter.cleanup_async()

    # 統合テスト
    async def test_sage_integration():
        """test_sage_integrationテストメソッド"""
        sage = KnowledgeSageGrimoireIntegration()
        await sage.initialize_async()

        # 統合知恵の相談
        wisdom = sage.consult_unified_wisdom("テスト")
        print(f"統合知恵: {len(wisdom) if wisdom else 0}文字")

        # 知識の進化
        evolution_result = sage.evolve_knowledge(
            "advanced_test_spell",
            "これは進化したテスト魔法です",
            "Testing knowledge evolution",
        )
        print(f"進化結果: {evolution_result}")

        await sage.cleanup_async()

    # テスト実行
    print("🔍 Knowledge Grimoire Adapter テスト")
    asyncio.run(test_adapter())

    print("\n📚 Knowledge Sage Integration テスト")
    asyncio.run(test_sage_integration())
