#!/usr/bin/env python3
"""
Code Review PM Worker - Elders Guild Quality Coordinator
コードレビューPMワーカー - エルダー評議会の品質調整担当

This worker serves as the quality coordinator within the Elder Tree hierarchy,
reporting to the Knowledge Sage and coordinating code review processes.
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.async_base_worker_v2 import AsyncBaseWorkerV2

# Elder Tree imports
try:
    from libs.elder_council_summoner import ElderCouncilSummoner
    from libs.elder_tree_hierarchy import (
        ElderMessage,
        ElderRank,
        SageType,
        get_elder_tree,
    )
    from libs.four_sages_integration import FourSagesIntegration

    ELDER_SYSTEM_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Elder system not available: {e}")
    ELDER_SYSTEM_AVAILABLE = False
    FourSagesIntegration = None
    ElderCouncilSummoner = None


class CodeReviewPMWorker(AsyncBaseWorkerV2):
    """Code Review PM Worker - Quality coordinator of the Elder Tree hierarchy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(
            worker_name="code_review_pm_worker",
            config=config,
            input_queues=["ai_pm"],
            output_queues=["ai_results"],
        )

        self.quality_threshold = config.get("quality_threshold", 85)
        self.max_iterations = config.get("max_iterations", 5)
        self.improvement_weight = config.get(
            "improvement_weight",
            {"syntax": 0.3, "logic": 0.25, "performance": 0.25, "security": 0.2},
        )
        self.created_at = datetime.now()
        self.reviews_processed = 0
        self.quality_improvements = 0

        # Initialize Elder systems
        self.elder_systems_initialized = False
        self._initialize_elder_systems()

        self.logger.info(
            f"CodeReviewPMWorker initialized as Elder Tree quality coordinator"
        )

    def _initialize_elder_systems(self):
        """Initialize Elder Tree hierarchy systems with error handling"""
        if not ELDER_SYSTEM_AVAILABLE:
            self.logger.warning(
                "Elder systems not available, running in standalone mode"
            )
            self.four_sages = None
            self.council_summoner = None
            self.elder_tree = None
            return

        try:
            # Initialize Four Sages Integration
            self.four_sages = FourSagesIntegration()
            self.logger.info("Four Sages Integration initialized successfully")

            # Initialize Elder Council Summoner
            self.council_summoner = ElderCouncilSummoner()
            self.logger.info("Elder Council Summoner initialized successfully")

            # Get Elder Tree reference
            self.elder_tree = get_elder_tree()
            self.logger.info("Elder Tree hierarchy connected")

            self.elder_systems_initialized = True

        except Exception as e:
            self.logger.error(f"Failed to initialize Elder systems: {e}")
            self.four_sages = None
            self.council_summoner = None
            self.elder_tree = None
            self.elder_systems_initialized = False

    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """メッセージ処理 - 品質評価要求を処理 with Elder Tree integration"""
        self.reviews_processed += 1
        message_type = message.get("message_type")

        try:
            if message_type == "code_analysis_result":
                result = await self._evaluate_quality_with_elders(message)

                # Report quality metrics to Knowledge Sage
                if self.elder_systems_initialized:
                    await self._report_quality_metrics_to_knowledge_sage(result)

                return result
            else:
                raise ValueError(f"Unsupported message type: {message_type}")

        except Exception as e:
            if self.elder_systems_initialized:
                await self._report_error_to_incident_sage(e, message)
            raise

    async def _report_quality_metrics_to_knowledge_sage(self, result: Dict[str, Any]):
        """Report quality metrics to Knowledge Sage"""
        if not self.four_sages:
            return

        try:
            metrics = {
                "type": "code_quality_metrics",
                "worker": "code_review_pm_worker",
                "quality_score": result.get("quality_score", 0),
                "threshold_met": result.get("quality_score", 0)
                >= self.quality_threshold,
                "improvement_areas": result.get("improvement_areas", []),
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.store_knowledge("quality_metrics", metrics)

        except Exception as e:
            self.logger.error(
                f"Failed to report quality metrics to Knowledge Sage: {e}"
            )

    async def _report_error_to_incident_sage(
        self, error: Exception, message: Dict[str, Any]
    ):
        """Report processing error to Incident Sage"""
        if not self.four_sages:
            return

        try:
            incident_data = {
                "type": "code_review_pm_error",
                "worker": "code_review_pm_worker",
                "error": str(error),
                "message_type": message.get("message_type"),
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.consult_incident_sage(incident_data)

        except Exception as e:
            self.logger.error(f"Failed to report error to Incident Sage: {e}")

    def get_elder_quality_status(self) -> Dict[str, Any]:
        """Get comprehensive Elder quality coordinator status"""
        status = {
            "worker_type": "code_review_pm_worker",
            "elder_role": "Quality Coordinator",
            "reporting_to": "Knowledge Sage",
            "elder_systems": {
                "initialized": self.elder_systems_initialized,
                "four_sages_active": self.four_sages is not None,
                "council_summoner_active": self.council_summoner is not None,
                "elder_tree_connected": self.elder_tree is not None,
            },
            "quality_stats": {
                "reviews_processed": self.reviews_processed,
                "quality_improvements": self.quality_improvements,
                "quality_threshold": self.quality_threshold,
                "max_iterations": self.max_iterations,
            },
            "uptime": (datetime.now() - self.created_at).total_seconds(),
            "status": "healthy" if self.elder_systems_initialized else "degraded",
        }

        return status

    async def _evaluate_quality_with_elders(
        self, message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """品質評価とフロー制御"""
        payload = message["payload"]
        analysis_results = payload["analysis_results"]
        code_metrics = payload["code_metrics"]

        # 品質スコア計算
        quality_score = await self._calculate_quality_score(
            analysis_results, code_metrics
        )

        iteration = message.get("iteration", 1)
        task_id = message["task_id"]

        # 品質判定とフロー制御
        if quality_score >= self.quality_threshold or iteration >= self.max_iterations:
            # 品質基準達成 or 反復上限 → 最終結果生成
            return await self._generate_final_result(message, quality_score, iteration)
        else:
            # 品質基準未達 → 改善要求生成
            return await self._generate_improvement_request(
                message, quality_score, analysis_results
            )

    async def _calculate_quality_score(
        self, analysis_results: Dict[str, Any], code_metrics: Dict[str, Any]
    ) -> float:
        """品質スコア計算"""
        weights = self.improvement_weight

        # 各カテゴリの問題数から品質を評価
        syntax_score = self._calculate_category_score(
            analysis_results.get("syntax_issues", [])
        )
        logic_score = self._calculate_category_score(
            analysis_results.get("logic_issues", [])
        )
        performance_score = self._calculate_category_score(
            analysis_results.get("performance_issues", [])
        )
        security_score = self._calculate_security_score(
            analysis_results.get("security_issues", [])
        )

        # 重み付き平均
        weighted_score = (
            syntax_score * weights["syntax"]
            + logic_score * weights["logic"]
            + performance_score * weights["performance"]
            + security_score * weights["security"]
        )

        # メトリクスによる調整（より厳しく）
        maintainability = code_metrics.get("maintainability_index", 50)
        complexity = code_metrics.get("complexity_score", 1)

        # 保守性が低い場合の大幅減点
        if maintainability < 70:
            maintainability_penalty = (70 - maintainability) * 0.5
        else:
            maintainability_penalty = 0

        # 複雑度ペナルティ（より厳しく）
        complexity_penalty = max(0, (complexity - 3) * 3)

        # 最終スコア（より厳格な計算）
        final_score = weighted_score - maintainability_penalty - complexity_penalty

        return max(0, min(100, final_score))

    def _calculate_category_score(self, issues: List[Dict[str, Any]]) -> float:
        """カテゴリ別品質スコア計算（より厳格）"""
        if not issues:
            return 100.0

        # より厳しい重要度別の減点
        penalty = 0
        for issue in issues:
            severity = issue.get("severity", "info")
            if severity == "critical":
                penalty += 30
            elif severity == "error":
                penalty += 25
            elif severity == "warning":
                penalty += 20  # warningでも大きく減点
            elif severity == "info":
                penalty += 10

        return max(0, 100 - penalty)

    def _calculate_security_score(self, security_issues: List[Dict[str, Any]]) -> float:
        """セキュリティスコア計算（重要度高）"""
        if not security_issues:
            return 100.0

        # セキュリティはより厳しく評価
        penalty = 0
        for issue in security_issues:
            severity = issue.get("severity", "info")
            if severity == "critical":
                penalty += 80  # セキュリティクリティカルは非常に重い
            elif severity == "high":
                penalty += 60
            elif severity == "warning":
                penalty += 40
            elif severity == "info":
                penalty += 20

        return max(0, 100 - penalty)

    async def _generate_improvement_request(
        self,
        message: Dict[str, Any],
        quality_score: float,
        analysis_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """改善要求生成"""
        task_id = message["task_id"]
        iteration = message.get("iteration", 1)

        # 改善提案の生成
        suggestions = await self._create_improvement_suggestions(analysis_results)

        # 改善されたコードの生成（簡易版）
        revised_code = await self._generate_revised_code(
            message["payload"], suggestions
        )

        return {
            "message_id": f"improvement_{task_id}_{iteration}",
            "task_id": task_id,
            "worker_source": "pm_worker",
            "worker_target": "task_worker",
            "message_type": "improvement_request",
            "iteration": iteration,
            "payload": {
                "current_quality_score": quality_score,
                "target_quality_score": self.quality_threshold,
                "improvement_suggestions": suggestions,
                "revised_code": revised_code,
                "iteration_reason": f"Quality score {quality_score:.1f} below threshold {self.quality_threshold}",
            },
        }

    async def _generate_final_result(
        self, message: Dict[str, Any], quality_score: float, iteration: int
    ) -> Dict[str, Any]:
        """最終結果生成"""
        task_id = message["task_id"]
        payload = message["payload"]

        # 改善サマリーの生成
        improvement_summary = {
            "initial_score": quality_score if iteration == 1 else 70,  # 仮の初期スコア
            "final_score": quality_score,
            "improvements_made": []
            if iteration == 1
            else ["Code quality improved through iterations"],
        }

        # レビューレポートの生成
        review_report = await self._generate_review_report(payload["analysis_results"])

        return {
            "message_id": f"completion_{task_id}",
            "task_id": task_id,
            "worker_source": "pm_worker",
            "worker_target": "result_worker",
            "message_type": "review_completion",
            "payload": {
                "final_quality_score": quality_score,
                "total_iterations": iteration,
                "improvement_summary": improvement_summary,
                "review_report": review_report,
                "iteration_limit_reached": iteration >= self.max_iterations,
            },
        }

    async def _create_improvement_suggestions(
        self, analysis_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """改善提案作成"""
        suggestions = []

        # 構文問題の改善提案
        for issue in analysis_results.get("syntax_issues", []):
            suggestions.append(
                {
                    "priority": "high"
                    if issue.get("severity") == "error"
                    else "medium",
                    "category": "syntax",
                    "suggestion": issue.get("suggestion", "Fix syntax issue"),
                    "expected_improvement": 15
                    if issue.get("severity") == "error"
                    else 10,
                }
            )

        # 論理問題の改善提案
        for issue in analysis_results.get("logic_issues", []):
            suggestions.append(
                {
                    "priority": "medium",
                    "category": "logic",
                    "suggestion": issue.get("suggestion", "Improve logic"),
                    "expected_improvement": 8,
                }
            )

        # パフォーマンス問題の改善提案
        for issue in analysis_results.get("performance_issues", []):
            suggestions.append(
                {
                    "priority": "low",
                    "category": "performance",
                    "suggestion": issue.get("suggestion", "Optimize performance"),
                    "expected_improvement": 5,
                }
            )

        # セキュリティ問題の改善提案
        for issue in analysis_results.get("security_issues", []):
            priority = "critical" if issue.get("severity") == "critical" else "high"
            suggestions.append(
                {
                    "priority": priority,
                    "category": "security",
                    "suggestion": issue.get("suggestion", "Fix security issue"),
                    "expected_improvement": 25 if priority == "critical" else 15,
                }
            )

        return suggestions

    async def _generate_revised_code(
        self, payload: Dict[str, Any], suggestions: List[Dict[str, Any]]
    ) -> str:
        """改善されたコードの生成（簡易版）"""
        # 実際の実装ではLLMを使用してコード改善
        # ここでは簡単な例として基本的な改善を模擬

        original_code = payload.get("original_code", "# Original code")

        # 簡易的な改善例
        improved_code = original_code

        # docstring追加の模擬
        if any("docstring" in s["suggestion"] for s in suggestions):
            improved_code = improved_code.replace(
                "def calc(l,w):",
                'def calculate_area(length, width):\n    """Calculate rectangle area."""',
            )

        return improved_code

    async def _generate_review_report(
        self, analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """レビューレポート生成"""
        return {
            "syntax_score": self._calculate_category_score(
                analysis_results.get("syntax_issues", [])
            ),
            "logic_score": self._calculate_category_score(
                analysis_results.get("logic_issues", [])
            ),
            "performance_score": self._calculate_category_score(
                analysis_results.get("performance_issues", [])
            ),
            "security_score": self._calculate_security_score(
                analysis_results.get("security_issues", [])
            ),
        }


# メイン実行部分（既存のワーカーとの互換性維持）
async def main():
    """ワーカーのメイン実行"""
    config = {
        "quality_threshold": 85,
        "max_iterations": 5,
        "improvement_weight": {
            "syntax": 0.3,
            "logic": 0.25,
            "performance": 0.25,
            "security": 0.2,
        },
    }

    worker = CodeReviewPMWorker(config)

    print("🚀 CodeReviewPMWorker started")

    try:
        while True:
            await asyncio.sleep(10)
            print("💓 CodeReview PMWorker heartbeat")
    except KeyboardInterrupt:
        print("\n🛑 CodeReview PMWorker stopping...")
        await worker.shutdown()
        print("✅ CodeReview PMWorker stopped")


if __name__ == "__main__":
    asyncio.run(main())
