"""
Elder Flow Auto Integration - 自動Elder Flow適用システム
Created: 2025-07-12
Author: Claude Elder
Version: 1.0.0

このモジュールは、クロードエルダーが開発タスクを受け取った際に
自動的にElder Flowを適用するためのシステムです。
"""

import asyncio
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from libs.elder_flow_integration import execute_elder_flow, get_elder_flow_status


# Task Detection Patterns
class TaskType(Enum):
    """TaskTypeクラス"""
    FEATURE_IMPLEMENTATION = "feature_implementation"
    BUG_FIX = "bug_fix"
    REFACTORING = "refactoring"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    OPTIMIZATION = "optimization"
    SECURITY = "security"
    UNKNOWN = "unknown"


# Auto Integration Configuration
@dataclass
class AutoIntegrationConfig:
    """AutoIntegrationConfigクラス"""
    # Elder Flow適用の閾値
    auto_apply_threshold: float = 0.5

    # 自動適用するタスクタイプ
    auto_apply_task_types: List[TaskType] = None

    # 自動コミット設定
    auto_commit_enabled: bool = True

    # 品質スコア閾値
    quality_threshold: float = 70.0

    # 優先度マッピング
    priority_mapping: Dict[str, str] = None

    def __post_init__(self):
        """__post_init__特殊メソッド"""
        if self.auto_apply_task_types is None:
            self.auto_apply_task_types = [
                TaskType.FEATURE_IMPLEMENTATION,
                TaskType.BUG_FIX,
                TaskType.REFACTORING,
                TaskType.OPTIMIZATION,
                TaskType.SECURITY,
            ]

        if self.priority_mapping is None:
            self.priority_mapping = {
                "critical": "high",
                "high": "high",
                "urgent": "high",
                "important": "high",
                "medium": "medium",
                "normal": "medium",
                "low": "low",
                "minor": "low",
            }


# Task Analysis
class TaskAnalyzer:
    """タスク分析器"""

    def __init__(self)self.logger = logging.getLogger(__name__)
    """初期化メソッド"""

        # タスクタイプ検出パターン
        self.task_patterns = {
            TaskType.FEATURE_IMPLEMENTATION: [
                r"実装|implement|add|create|build|develop|新機能",
                r"機能|feature|functionality",
                r"システム|system|API|インターフェース",
            ],
            TaskType.BUG_FIX: [
                r"修正|fix|bug|エラー|error|問題|issue",
                r"直す|repair|resolve|solve",
                r"バグ|不具合|障害",
            ],
            TaskType.REFACTORING: [
                r"リファクタリング|refactor|refactoring",
                r"改善|improve|enhancement",
                r"最適化|optimize|optimization",
            ],
            TaskType.TESTING: [
                r"テスト|test|testing",
                r"検証|verify|validation",
                r"カバレッジ|coverage",
            ],
            TaskType.DOCUMENTATION: [
                r"ドキュメント|document|documentation",
                r"説明|readme|guide|manual",
            ],
            TaskType.OPTIMIZATION: [
                r"最適化|optimize|optimization",
                r"パフォーマンス|performance|速度|speed",
            ],
            TaskType.SECURITY: [
                r"セキュリティ|security|認証|authentication",
                r"権限|authorization|暗号化|encryption",
            ],
        }

    def analyze_task(self, description: str) -> Dict[str, Any]:
        """タスク分析"""
        analysis = {
            "task_type": TaskType.UNKNOWN,
            "confidence": 0.0,
            "priority": "medium",
            "estimated_complexity": "medium",
            "elder_flow_recommended": False,
            "keywords": [],
        }

        description_lower = description.lower()

        # タスクタイプ検出
        best_match_type = TaskType.UNKNOWN
        best_confidence = 0.0
        matched_keywords = []

        for task_type, patterns in self.task_patterns.items():
            confidence = 0.0
            type_keywords = []

            for pattern in patterns:
                matches = re.findall(pattern, description_lower)
                if matches:
                    confidence += len(matches) * 0.3
                    type_keywords.extend(matches)

            if confidence > best_confidence:
                best_confidence = confidence
                best_match_type = task_type
                matched_keywords = type_keywords

        analysis["task_type"] = best_match_type
        analysis["confidence"] = min(best_confidence, 1.0)
        analysis["keywords"] = matched_keywords

        # 優先度検出
        priority_keywords = {
            "high": ["緊急", "urgent", "critical", "重要", "important", "高", "high"],
            "medium": ["medium", "normal", "普通", "中"],
            "low": ["low", "minor", "軽微", "低"],
        }

        for priority, keywords in priority_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                analysis["priority"] = priority
                break

        # 複雑度推定
        complexity_indicators = {
            "high": [
                "system",
                "architecture",
                "database",
                "API",
                "複雑",
                "システム",
                "アーキテクチャ",
            ],
            "medium": ["feature", "function", "module", "機能", "モジュール"],
            "low": ["fix", "update", "modify", "修正", "更新", "変更"],
        }

        for complexity, indicators in complexity_indicators.items():
            if any(indicator in description_lower for indicator in indicators):
                analysis["estimated_complexity"] = complexity
                break

        # Elder Flow推奨判定
        analysis["elder_flow_recommended"] = analysis["confidence"] >= 0.5 and analysis[
            "task_type"
        ] in [
            TaskType.FEATURE_IMPLEMENTATION,
            TaskType.BUG_FIX,
            TaskType.REFACTORING,
            TaskType.OPTIMIZATION,
            TaskType.SECURITY,
        ]

        return analysis


# Auto Integration System
class ElderFlowAutoIntegration:
    """Elder Flow自動統合システム"""

    def __init__(self, config: AutoIntegrationConfig = None)self.config = config or AutoIntegrationConfig()
    """初期化メソッド"""
        self.analyzer = TaskAnalyzer()
        self.logger = logging.getLogger(__name__)

        # 実行履歴
        self.execution_history: List[Dict] = []

        self.logger.info("Elder Flow Auto Integration System initialized")

    async def should_apply_elder_flow(self, description: str) -> Tuple[bool, Dict]analysis = self.analyzer.analyze_task(description):
    """lder Flow適用判定"""

        # 自動適用条件チェック
        should_apply = (
            analysis["confidence"] >= self.config.auto_apply_threshold
            and analysis["task_type"] in self.config.auto_apply_task_types
            and analysis["elder_flow_recommended"]
        )

        decision = {:
            "should_apply": should_apply,
            "analysis": analysis,
            "reason": self._get_decision_reason(should_apply, analysis),
        }

        return should_apply, decision

    def _get_decision_reason(self, should_apply: bool, analysis: Dict) -> str:
        """判定理由取得"""
        if should_apply:
            return f"Elder Flow適用: {analysis['task_type'].value} (信頼度: {analysis['confidence']:0.2f})"
        else:
            reasons = []
            if analysis["confidence"] < self.config.auto_apply_threshold:
                reasons.append(
                    f"信頼度不足 ({analysis['confidence']:0.2f} < {self.config.auto_apply_threshold})"
                )
            if analysis["task_type"] not in self.config.auto_apply_task_types:
                reasons.append(f"対象外タスクタイプ ({analysis['task_type'].value})")
            if not analysis["elder_flow_recommended"]:
                reasons.append("Elder Flow推奨されない")

            return "Elder Flow非適用: " + ", ".join(reasons)

    async def auto_execute_if_applicable(
        self, description: str, force_apply: bool = False
    ) -> Optional[Dict]:
        """適用可能な場合のElder Flow自動実行"""

        # 適用判定
        should_apply, decision = await self.should_apply_elder_flow(description)

        if not should_apply and not force_apply:
            self.logger.info(f"Elder Flow auto-execution skipped: {decision['reason']}")
            return {
                "applied": False,
                "decision": decision,
                "reason": decision["reason"],
            }

        # Elder Flow実行
        try:
            self.logger.info(f"Auto-executing Elder Flow: {description}")

            analysis = decision["analysis"]
            priority = self.config.priority_mapping.get(analysis["priority"], "medium")

            task_id = await execute_elder_flow(
                description, priority, auto_commit=self.config.auto_commit_enabled
            )

            # 実行結果取得
            result = get_elder_flow_status(task_id)

            # 履歴記録
            execution_record = {
                "task_id": task_id,
                "description": description,
                "decision": decision,
                "result": result,
                "success": result and result.get("status") == "completed",
            }

            self.execution_history.append(execution_record)

            self.logger.info(f"Elder Flow auto-execution completed: {task_id}")

            return {
                "applied": True,
                "task_id": task_id,
                "result": result,
                "decision": decision,
                "execution_record": execution_record,
            }

        except Exception as e:
            self.logger.error(f"Elder Flow auto-execution failed: {str(e)}")
            return {"applied": False, "error": str(e), "decision": decision}

    def get_execution_statistics(self) -> Dicttotal_executions = len(self.execution_history):
    """行統計取得"""
        successful_executions = sum(
            1 for record in self.execution_history if record["success"]
        )

        task_types = {}:
        for record in self.execution_history:
            task_type = record["decision"]["analysis"]["task_type"].value
            task_types[task_type] = task_types.get(task_type, 0) + 1

        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": (
                (successful_executions / total_executions * 100)
                if total_executions > 0
                else 0
            ),
            "task_type_distribution": task_types,
            "recent_executions": (
                self.execution_history[-5:] if self.execution_history else []
            ),
        }


# Global auto integration instance
auto_integration = ElderFlowAutoIntegration()


# Helper functions
async def auto_elder_flow(
    description: str, force_apply: bool = False
) -> Optional[Dict]:
    """Elder Flow自動適用"""
    return await auto_integration.auto_execute_if_applicable(description, force_apply)


async def should_use_elder_flow(description: str) -> Tuple[bool, Dict]return await auto_integration.should_apply_elder_flow(description)
Elder Flow使用判定


def get_auto_integration_stats() -> Dictreturn auto_integration.get_execution_statistics():
    """動統合統計取得"""


# Claude Integration Function:
async def claude_auto_elder_flow(user_request: str) -> Optional[Dict]:
    """
    クロードエルダー用自動Elder Flow判定・実行

    ユーザーのリクエストを分析し、Elder Flowが適用可能な場合は自動実行
    """

    # 特定のキーワードでElder Flow強制適用
    force_keywords = ["elder flow", "elder-flow", "エルダーフロー", "エルダー・フロー"]
    force_apply = any(keyword in user_request.lower() for keyword in force_keywords)

    if force_apply:
        # キーワードを除いたタスク記述を抽出
        cleaned_request = user_request
        for keyword in force_keywords:
            cleaned_request = re.sub(
                rf"\b{keyword}\b", "", cleaned_request, flags=re.IGNORECASE
            )
        cleaned_request = re.sub(r"\s+", " ", cleaned_request).strip()

        return await auto_elder_flow(cleaned_request or user_request, force_apply=True)

    # 通常の自動判定
    return await auto_elder_flow(user_request)


# Example usage
if __name__ == "__main__":
    pass

    async def main()print("🔮 Elder Flow Auto Integration Test")
    """mainメソッド"""

        # テストケース
        test_cases = [
            "OAuth2.0認証システムを実装してください",
            "バグを修正してください",
            "ドキュメントを更新してください",
            "緊急でAPIの最適化が必要です",
            "エルダーフローでユーザー管理機能を作成",
        ]

        for test_case in test_cases:
            print(f"\n📋 Test: {test_case}")

            # 判定テスト
            should_apply, decision = await should_use_elder_flow(test_case)
            print(f"🤖 Should apply: {should_apply}")
            print(
                (
                    f"f"📊 Analysis: {decision['analysis']['task_type'].value} (confidence: "
                    f"{decision['analysis']['confidence']:0.2f})""
                )
            )

            # 自動実行テスト（実際には実行しない）
            # result = await auto_elder_flow(test_case)
            # print(f"🌊 Auto result: {result}")

        # 統計表示
        stats = get_auto_integration_stats()
        print(f"\n📈 Statistics: {stats}")

    asyncio.run(main())
