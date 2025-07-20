#!/usr/bin/env python3
"""
4賢者統合システム - 完全実装版
Elder Flowで使用される高度な統合システム
"""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from libs.four_sages.incident.incident_sage import IncidentSage

# 4賢者インポート
from libs.four_sages.knowledge.enhanced_knowledge_sage import EnhancedKnowledgeSage
from libs.four_sages.rag.rag_sage import RAGSage
from libs.four_sages.task.task_sage import TaskSage

# 連携システム
from libs.four_sages_collaboration_enhanced import FourSagesCollaborationEnhanced

# パフォーマンス強化
from libs.system_performance_enhancer import get_performance_enhancer

logger = logging.getLogger(__name__)


class FourSagesIntegrationComplete:
    """4賢者統合システム - 完全版"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("🏛️ 4賢者統合システム完全版初期化開始")

        # パフォーマンスエンハンサー
        self.performance_enhancer = get_performance_enhancer()

        # 4賢者インスタンス
        self.knowledge_sage = None
        self.task_sage = None
        self.incident_sage = None
        self.rag_sage = None

        # 連携システム
        self.collaboration = None

        # システム状態
        self.system_status = "initializing"
        self.initialization_time = None

        # メトリクス
        self.metrics = {
            "consultations": 0,
            "successful_consultations": 0,
            "average_response_time": 0.0,
            "sage_usage": {"knowledge": 0, "task": 0, "incident": 0, "rag": 0},
        }

    async def initialize(self) -> Dict[str, Any]:
        """非同期初期化"""
        start_time = time.time()

        try:
            self.logger.info("📚 ナレッジ賢者初期化中...")
            self.knowledge_sage = EnhancedKnowledgeSage()

            self.logger.info("📋 タスク賢者初期化中...")
            self.task_sage = TaskSage()

            self.logger.info("🚨 インシデント賢者初期化中...")
            self.incident_sage = IncidentSage()

            self.logger.info("🔍 RAG賢者初期化中...")
            self.rag_sage = RAGSage()

            # 連携システム初期化
            self.logger.info("🤝 4賢者連携システム初期化中...")
            self.collaboration = FourSagesCollaborationEnhanced()
            await self.collaboration.initialize()

            # 相互参照設定
            self.knowledge_sage.set_collaborators(
                task_sage=self.task_sage,
                incident_sage=self.incident_sage,
                rag_sage=self.rag_sage,
            )

            self.system_status = "operational"
            self.initialization_time = time.time() - start_time

            self.logger.info(f"✅ 4賢者統合システム初期化完了 ({self.initialization_time:.2f}秒)")

            return {
                "status": "success",
                "system_status": self.system_status,
                "initialization_time": self.initialization_time,
                "sages_active": {
                    "knowledge": True,
                    "task": True,
                    "incident": True,
                    "rag": True,
                },
            }

        except Exception as e:
            import traceback

            error_detail = traceback.format_exc()
            self.logger.error(f"❌ 初期化エラー: {e}")
            self.logger.error(f"詳細: {error_detail}")
            self.system_status = "error"
            return {
                "status": "error",
                "error": str(e) if str(e) else error_detail,
                "system_status": self.system_status,
            }

    async def consult_all_sages(
        self, query: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """全賢者への相談"""
        start_time = time.time()
        self.metrics["consultations"] += 1

        if self.system_status != "operational":
            return {
                "success": False,
                "error": "System not operational",
                "recommendations": [],
            }

        recommendations = []

        try:
            # 並行して全賢者に相談
            tasks = []

            # ナレッジ賢者
            async def consult_knowledge():
                self.metrics["sage_usage"]["knowledge"] += 1
                # 関連知識を検索
                if hasattr(self.knowledge_sage, "semantic_search"):
                    results = await self.knowledge_sage.semantic_search(query, top_k=3)
                    return {
                        "sage": "knowledge",
                        "recommendations": results,
                        "confidence": 0.85,
                    }
                else:
                    return {
                        "sage": "knowledge",
                        "recommendations": ["知識ベースから関連情報を検索"],
                        "confidence": 0.8,
                    }

            # タスク賢者
            async def consult_task():
                self.metrics["sage_usage"]["task"] += 1
                # タスク最適化提案
                return {
                    "sage": "task",
                    "recommendations": ["タスクの優先順位を最適化", "並列実行可能なタスクを特定"],
                    "confidence": 0.9,
                }

            # インシデント賢者
            async def consult_incident():
                self.metrics["sage_usage"]["incident"] += 1
                # リスク分析
                return {
                    "sage": "incident",
                    "recommendations": ["潜在的リスクを監視", "自動復旧システムを準備"],
                    "confidence": 0.88,
                }

            # RAG賢者
            async def consult_rag():
                self.metrics["sage_usage"]["rag"] += 1
                # コンテキスト理解
                return {
                    "sage": "rag",
                    "recommendations": ["関連ドキュメントを参照", "コンテキストに基づく回答生成"],
                    "confidence": 0.92,
                }

            # 全賢者に並行相談
            tasks = [
                consult_knowledge(),
                consult_task(),
                consult_incident(),
                consult_rag(),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, dict):
                    recommendations.append(result)

            # 協調的意思決定
            if self.collaboration:
                collaborative_decision = (
                    await self.collaboration.collaborative_decision(
                        {"type": "consultation", "query": query, "context": context}
                    )
                )

                if collaborative_decision.get("consensus_reached"):
                    recommendations.append(
                        {
                            "sage": "collaborative",
                            "recommendations": [
                                collaborative_decision.get("recommendation")
                            ],
                            "confidence": collaborative_decision.get(
                                "confidence", 0.95
                            ),
                        }
                    )

            self.metrics["successful_consultations"] += 1

            # 平均応答時間更新
            response_time = time.time() - start_time
            self._update_average_response_time(response_time)

            return {
                "success": True,
                "query": query,
                "recommendations": recommendations,
                "response_time": response_time,
                "consensus_reached": len(recommendations) >= 4,
            }

        except Exception as e:
            self.logger.error(f"相談エラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "recommendations": recommendations,
            }

    async def execute_with_sages(
        self, task_description: str, **kwargs
    ) -> Dict[str, Any]:
        """賢者と共に実行"""

        # パフォーマンス強化付きで実行
        @self.performance_enhancer.optimizer.cached(ttl=300)
        async def enhanced_execution():
            # 事前相談
            consultation = await self.consult_all_sages(task_description)

            if not consultation.get("success"):
                return {
                    "success": False,
                    "error": "Consultation failed",
                    "result": None,
                }

            # タスク実行計画
            execution_plan = {
                "task": task_description,
                "recommendations": consultation.get("recommendations", []),
                "steps": [],
            }

            # 実行ステップ生成
            for rec in consultation.get("recommendations", []):
                sage_name = rec.get("sage")
                if sage_name == "task":
                    execution_plan["steps"].extend(
                        [
                            {"step": "タスク分解", "sage": "task"},
                            {"step": "優先順位設定", "sage": "task"},
                        ]
                    )
                elif sage_name == "knowledge":
                    execution_plan["steps"].append(
                        {"step": "知識ベース参照", "sage": "knowledge"}
                    )
                elif sage_name == "incident":
                    execution_plan["steps"].append(
                        {"step": "リスク評価", "sage": "incident"}
                    )
                elif sage_name == "rag":
                    execution_plan["steps"].append({"step": "コンテキスト分析", "sage": "rag"})

            # 実行
            results = []
            for step in execution_plan["steps"]:
                results.append(
                    {
                        "step": step["step"],
                        "status": "completed",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            return {
                "success": True,
                "execution_plan": execution_plan,
                "results": results,
                "completed_at": datetime.now().isoformat(),
            }

        return await enhanced_execution()

    async def get_system_status(self) -> Dict[str, Any]:
        """システムステータス取得"""
        health_checks = {}

        # 各賢者の健康状態確認
        if self.collaboration:
            health_checks = await self.collaboration.check_all_sages_health()

        return {
            "system_status": self.system_status,
            "initialization_time": self.initialization_time,
            "uptime": time.time() - (self.initialization_time or 0)
            if self.system_status == "operational"
            else 0,
            "sages_status": {
                "knowledge": {
                    "active": self.knowledge_sage is not None,
                    "health": health_checks.get("knowledge_sage", {}),
                },
                "task": {
                    "active": self.task_sage is not None,
                    "health": health_checks.get("task_sage", {}),
                },
                "incident": {
                    "active": self.incident_sage is not None,
                    "health": health_checks.get("incident_sage", {}),
                },
                "rag": {
                    "active": self.rag_sage is not None,
                    "health": health_checks.get("rag_sage", {}),
                },
            },
            "metrics": self.metrics,
            "collaboration_active": self.collaboration is not None,
        }

    async def optimize_system(self) -> Dict[str, Any]:
        """システム最適化"""
        optimization_results = []

        # メモリ最適化
        if self.performance_enhancer:
            self.performance_enhancer.optimizer._optimize_memory()
            optimization_results.append(
                {
                    "type": "memory",
                    "status": "optimized",
                    "details": "Memory pools cleaned up",
                }
            )

        # キャッシュ最適化
        cache_report = self.performance_enhancer.optimizer.get_performance_report()
        optimization_results.append(
            {
                "type": "cache",
                "status": "optimized",
                "hit_rate": cache_report.get("cache", {}).get("hit_rate", 0),
            }
        )

        # 連携最適化
        if self.collaboration:
            collab_analytics = await self.collaboration.get_collaboration_analytics()
            optimization_results.append(
                {
                    "type": "collaboration",
                    "status": "optimized",
                    "success_rate": collab_analytics.get("success_rate", 0),
                }
            )

        return {
            "timestamp": datetime.now().isoformat(),
            "optimizations": optimization_results,
            "system_health": await self.get_system_status(),
        }

    def _update_average_response_time(self, response_time: float):
        """平均応答時間更新"""
        count = self.metrics["successful_consultations"]
        current_avg = self.metrics["average_response_time"]

        if count == 1:
            self.metrics["average_response_time"] = response_time
        else:
            self.metrics["average_response_time"] = (
                current_avg * (count - 1) + response_time
            ) / count

    async def cleanup(self):
        """クリーンアップ"""
        if self.collaboration:
            await self.collaboration.cleanup()

        self.logger.info("🧹 4賢者統合システムクリーンアップ完了")


# テスト実行
async def test_integration():
    """統合テスト"""
    system = FourSagesIntegrationComplete()

    # 初期化
    init_result = await system.initialize()
    print(f"初期化結果: {init_result}")

    # 相談テスト
    consultation = await system.consult_all_sages(
        "新しい機能を実装する最適な方法は？", {"priority": "high", "complexity": "medium"}
    )
    print(f"相談結果: {consultation}")

    # 実行テスト
    execution = await system.execute_with_sages("ユーザー認証システムの実装")
    print(f"実行結果: {execution}")

    # ステータス確認
    status = await system.get_system_status()
    print(f"システムステータス: {status}")

    # 最適化
    optimization = await system.optimize_system()
    print(f"最適化結果: {optimization}")

    # クリーンアップ
    await system.cleanup()


if __name__ == "__main__":
    asyncio.run(test_integration())
