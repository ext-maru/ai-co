#!/usr/bin/env python3
"""
🔨 タスク分解エンジン
Task Breakdown Engine

計画書やドキュメントからタスクを抽出・分解するエンジン
"""

import asyncio
import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class TaskBreakdown:
    """分解されたタスク"""

    task_id: str
    title: str
    description: str
    priority: str
    category: str
    estimated_hours: float
    dependencies: List[str]
    success_criteria: List[str]
    parent_plan: str
    created_at: str

    def __post_init__(self):
        """__post_init__特殊メソッド"""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.task_id:
            self.task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


class TaskBreakdownEngine:
    """タスク分解エンジン"""

    def __init__(self):
        """初期化メソッド"""
        self.base_path = Path("/home/aicompany/ai_co")
        self.plans_path = self.base_path / "docs" / "plans"

        # タスク抽出パターン
        self.task_patterns = [
            r"- \[ \] (.+?)(?:\n|$)",  # - [ ] タスク
            r"^\s*- \[ \] (.+?)(?:\n|$)",  # インデント付き - [ ] タスク
            r"(?:Week\s+\d+[^:]*?:\s*)\n((?:\s*- .+\n?)+)",  # Week sections
            r"^\s*\d+\.\s*(.+?)(?:\n|$)",  # 1.0 番号付きリスト
            r"^\s*\*\s*(.+?)(?:\n|$)",  # * リスト
            r"## (.+?)(?:\n|$)",  # ## 見出し
            r"### (.+?)(?:\n|$)",  # ### 見出し
        ]

        # 優先度キーワード
        self.priority_keywords = {
            "high": ["緊急", "重要", "急", "必須", "critical", "urgent", "high"],
            "medium": ["中", "普通", "標準", "medium", "normal"],
            "low": ["低", "後回し", "任意", "low", "optional"],
        }

        # カテゴリキーワード
        self.category_keywords = {
            "implementation": [
                "実装",
                "開発",
                "作成",
                "構築",
                "implementation",
                "develop",
                "create",
            ],
            "testing": ["テスト", "検証", "確認", "testing", "verify", "test"],
            "documentation": [
                "文書",
                "ドキュメント",
                "記録",
                "文書化",
                "documentation",
                "document",
            ],
            "architecture": [
                "設計",
                "アーキテクチャ",
                "構造",
                "architecture",
                "design",
            ],
            "security": [
                "セキュリティ",
                "認証",
                "権限",
                "security",
                "auth",
                "permission",
            ],
            "quality": [
                "品質",
                "改善",
                "最適化",
                "quality",
                "improvement",
                "optimization",
            ],
        }

        # 統計
        self.stats = {
            "total_extractions": 0,
            "total_tasks": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
        }

    async def extract_tasks_from_plan(self, plan_file_path: str) -> List[TaskBreakdown]:
        """計画書からタスクを抽出"""
        plan_path = Path(plan_file_path)

        if not plan_path.exists():
            logger.error(f"計画書が見つかりません: {plan_file_path}")
            return []

        try:
            # ファイルを読み込み
            with open(plan_path, "r", encoding="utf-8") as f:
                content = f.read()

            # タスクを抽出
            raw_tasks = self._extract_raw_tasks(content)

            # TaskBreakdownオブジェクトに変換
            tasks = []
            for i, raw_task in enumerate(raw_tasks):
                task = self._create_task_breakdown(raw_task, i + 1, plan_path.name)
                tasks.append(task)

            self.stats["total_extractions"] += 1
            self.stats["total_tasks"] += len(tasks)
            self.stats["successful_extractions"] += 1

            logger.info(f"タスク抽出完了: {len(tasks)}件 from {plan_file_path}")
            return tasks

        except Exception as e:
            logger.error(f"タスク抽出エラー: {e}")
            self.stats["failed_extractions"] += 1
            return []

    def _extract_raw_tasks(self, content: str) -> List[str]:
        """生のタスクテキストを抽出"""
        tasks = []

        for pattern in self.task_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
        # 繰り返し処理
                if isinstance(match, str):
                    task_text = match.strip()
                    if task_text and len(task_text) > 3:
                        tasks.append(task_text)

        # 重複を除去
        unique_tasks = list(set(tasks))

        # 短すぎるタスクを除外
        filtered_tasks = [task for task in unique_tasks if len(task) > 5]

        return filtered_tasks

    def _create_task_breakdown(
        self, raw_task: str, task_number: int, plan_name: str
    ) -> TaskBreakdown:
        """生のタスクからTaskBreakdownオブジェクトを作成"""
        # タスクIDを生成
        task_id = f"task_{plan_name}_{task_number:03d}"

        # タイトルと説明を分離
        title, description = self._split_title_description(raw_task)

        # 優先度を推定
        priority = self._estimate_priority(raw_task)

        # カテゴリを推定
        category = self._estimate_category(raw_task)

        # 工数を推定
        estimated_hours = self._estimate_hours(raw_task)

        # 依存関係を抽出
        dependencies = self._extract_dependencies(raw_task)

        # 成功基準を生成
        success_criteria = self._generate_success_criteria(raw_task, category)

        return TaskBreakdown(
            task_id=task_id,
            title=title,
            description=description,
            priority=priority,
            category=category,
            estimated_hours=estimated_hours,
            dependencies=dependencies,
            success_criteria=success_criteria,
            parent_plan=plan_name,
            created_at=datetime.now().isoformat(),
        )

    def _split_title_description(self, raw_task: str) -> Tuple[str, str]:
        """タイトルと説明を分離"""
        # コロンで分割
        if ":" in raw_task:
            parts = raw_task.split(":", 1)
            title = parts[0].strip()
            description = parts[1].strip()
        else:
            # 最初の文をタイトルとする
            sentences = raw_task.split(".")
            title = sentences[0].strip()
            description = (
                ".".join(sentences[1:]).strip() if len(sentences) > 1 else title
            )

        # タイトルが長すぎる場合は短縮
        if len(title) > 100:
            title = title[:97] + "..."

        return title, description

    def _estimate_priority(self, task_text: str) -> str:
        """優先度を推定"""
        task_lower = task_text.lower()

        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
        # 繰り返し処理
                if keyword in task_lower:
                    return priority

        # デフォルトは medium
        return "medium"

    def _estimate_category(self, task_text: str) -> str:
        """カテゴリを推定"""
        task_lower = task_text.lower()

        for category, keywords in self.category_keywords.items():
        # 繰り返し処理
            for keyword in keywords:
                if keyword in task_lower:
                    return category

        # デフォルトは implementation
        return "implementation"

    def _estimate_hours(self, task_text: str) -> float:
        """工数を推定"""
        # 簡易的な工数推定
        text_length = len(task_text)

        if text_length < 20:
            return 1.0
        elif text_length < 50:
            return 2.0
        elif text_length < 100:
            return 4.0
        else:
            return 8.0

    def _extract_dependencies(self, task_text: str) -> List[str]:
        """依存関係を抽出"""
        dependencies = []

        # 依存関係キーワード
        dependency_patterns = [
            r"(?:depends on|depends|requires|needs|after)\s+(.+?)(?:\n|$|[,.])",
            r"(?:依存|必要|前提|後)\s*[:：]\s*(.+?)(?:\n|$|[,.])",
        ]

        # 繰り返し処理
        for pattern in dependency_patterns:
            matches = re.findall(pattern, task_text, re.IGNORECASE)
            for match in matches:
                dep = match.strip()
                if dep and len(dep) > 3:
                    dependencies.append(dep)

        return dependencies

    def _generate_success_criteria(self, task_text: str, category: str) -> List[str]:
        """成功基準を生成"""
        criteria = []

        # カテゴリ別の基本成功基準
        category_criteria = {
            "implementation": [
                "コードが正常に動作する",
                "テストが通る",
                "コードレビューが完了する",
            ],
            "testing": [
                "テストケースが作成される",
                "テストが実行される",
                "カバレッジが基準を満たす",
            ],
            "documentation": [
                "ドキュメントが作成される",
                "内容が正確である",
                "レビューが完了する",
            ],
            "architecture": [
                "設計書が作成される",
                "アーキテクチャが承認される",
                "実装可能性が確認される",
            ],
            "security": [
                "セキュリティ要件が満たされる",
                "脆弱性検査が完了する",
                "認証・認可が正常に動作する",
            ],
            "quality": [
                "品質基準が満たされる",
                "改善効果が確認される",
                "パフォーマンスが向上する",
            ],
        }

        # カテゴリ別の基準を追加
        if category in category_criteria:
            criteria.extend(category_criteria[category])

        # タスクテキストから特定の基準を抽出
        if "テスト" in task_text:
            criteria.append("テストが実行される")
        if "文書" in task_text or "ドキュメント" in task_text:
            criteria.append("ドキュメントが作成される")
        if "実装" in task_text or "開発" in task_text:
            criteria.append("実装が完了する")

        # 重複を除去
        unique_criteria = list(set(criteria))

        return unique_criteria[:3]  # 最大3つまで

    def get_extraction_stats(self) -> Dict:
        """抽出統計を取得"""
        return {
            "stats": self.stats,
            "success_rate": (
                self.stats["successful_extractions"]
                / max(1, self.stats["total_extractions"])
            )
            * 100,
            "average_tasks_per_plan": self.stats["total_tasks"]
            / max(1, self.stats["successful_extractions"]),
            "supported_patterns": len(self.task_patterns),
            "supported_categories": list(self.category_keywords.keys()),
            "supported_priorities": list(self.priority_keywords.keys()),
        }

    async def validate_task_breakdown(self, task: TaskBreakdown) -> Dict:
        """タスク分解の妥当性を検証"""
        validation_result = {"valid": True, "issues": [], "score": 100.0}

        # タイトルの検証
        if not task.title or len(task.title) < 3:
            validation_result["issues"].append("タイトルが短すぎます")
            validation_result["score"] -= 20

        # 説明の検証
        if not task.description or len(task.description) < 10:
            validation_result["issues"].append("説明が不十分です")
            validation_result["score"] -= 15

        # 優先度の検証
        if task.priority not in ["high", "medium", "low"]:
            validation_result["issues"].append("無効な優先度です")
            validation_result["score"] -= 10

        # カテゴリの検証
        if task.category not in self.category_keywords:
            validation_result["issues"].append("無効なカテゴリです")
            validation_result["score"] -= 10

        # 工数の検証
        if task.estimated_hours <= 0 or task.estimated_hours > 40:
            validation_result["issues"].append("工数が不適切です")
            validation_result["score"] -= 15

        # 成功基準の検証
        if not task.success_criteria or len(task.success_criteria) == 0:
            validation_result["issues"].append("成功基準が設定されていません")
            validation_result["score"] -= 20

        # 検証結果を判定
        if validation_result["score"] < 70:
            validation_result["valid"] = False

        return validation_result

    async def optimize_task_breakdown(
        self, tasks: List[TaskBreakdown]
    ) -> List[TaskBreakdown]:
        """タスク分解を最適化"""
        optimized_tasks = []

        for task in tasks:
            # 妥当性検証
            validation = await self.validate_task_breakdown(task)

            if validation["valid"]:
                optimized_tasks.append(task)
            else:
                # 問題があるタスクを修正
                fixed_task = await self._fix_task_issues(task, validation["issues"])
                optimized_tasks.append(fixed_task)

        # 依存関係の最適化
        optimized_tasks = self._optimize_dependencies(optimized_tasks)

        return optimized_tasks

    async def _fix_task_issues(
        self, task: TaskBreakdown, issues: List[str]
    ) -> TaskBreakdown:
        """タスクの問題を修正"""
        fixed_task = TaskBreakdown(
            task_id=task.task_id,
            title=task.title,
            description=task.description,
            priority=task.priority,
            category=task.category,
            estimated_hours=task.estimated_hours,
            dependencies=task.dependencies,
            success_criteria=task.success_criteria,
            parent_plan=task.parent_plan,
            created_at=task.created_at,
        )

        for issue in issues:
            if "タイトルが短すぎます" in issue:
                if len(fixed_task.title) < 3:
                    fixed_task.title = f"タスク: {fixed_task.title}"

            if "説明が不十分です" in issue:
                if len(fixed_task.description) < 10:
                    fixed_task.description = f"{fixed_task.title}の実装を行う"

            if "無効な優先度です" in issue:
                fixed_task.priority = "medium"

            if "無効なカテゴリです" in issue:
                fixed_task.category = "implementation"

            if "工数が不適切です" in issue:
                fixed_task.estimated_hours = 4.0

            if "成功基準が設定されていません" in issue:
                fixed_task.success_criteria = ["タスクが完了する", "品質基準を満たす"]

        return fixed_task

    def _optimize_dependencies(self, tasks: List[TaskBreakdown]) -> List[TaskBreakdown]:
        """依存関係を最適化"""
        # 簡易的な依存関係最適化
        # 実際の実装では、より複雑な依存関係解析が必要

        for task in tasks:
            # 循環依存の検出・解決
            # 未定義の依存関係の削除
            valid_deps = []
            for dep in task.dependencies:
                if any(dep in other_task.title for other_task in tasks):
                    valid_deps.append(dep)

            task.dependencies = valid_deps

        return tasks


# 使用例
async def main():
    """メイン実行関数"""
    engine = TaskBreakdownEngine()

    # 統計情報を表示
    stats = engine.get_extraction_stats()
    print(f"🔨 タスク分解エンジン統計:")
    print(f"   📊 総抽出回数: {stats['stats']['total_extractions']}")
    print(f"   📋 総タスク数: {stats['stats']['total_tasks']}")
    print(f"   ✅ 成功率: {stats['success_rate']:0.1f}%")
    print(f"   🔄 サポートパターン数: {stats['supported_patterns']}")


if __name__ == "__main__":
    asyncio.run(main())
