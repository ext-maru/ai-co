#!/usr/bin/env python3
"""
知能的タスク分割システム - 大きなタスクを効率的に分割・並列化

PMが設計したタスクを複雑度に応じて自動分割し、
依存関係を解析して最適な実行順序を決定する
"""

import json
import logging
import re
import sqlite3

# プロジェクトルートをPythonパスに追加
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseManager

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """タスク複雑度レベル"""

    SIMPLE = "simple"  # 単純タスク（1-2時間）
    MODERATE = "moderate"  # 中程度（半日-1日）
    COMPLEX = "complex"  # 複雑（2-3日）
    VERY_COMPLEX = "very_complex"  # 非常に複雑（1週間以上）


class TaskType(Enum):
    """タスクタイプ"""

    RESEARCH = "research"  # 調査・分析
    DESIGN = "design"  # 設計
    IMPLEMENTATION = "implementation"  # 実装
    TESTING = "testing"  # テスト
    DOCUMENTATION = "documentation"  # ドキュメント作成
    INTEGRATION = "integration"  # 統合
    DEPLOYMENT = "deployment"  # デプロイ
    REVIEW = "review"  # レビュー


@dataclass
class TaskDependency:
    """タスク依存関係"""

    task_id: str
    depends_on: str
    dependency_type: str  # "blocks", "requires", "enhances"
    weight: float = 1.0  # 依存関係の重要度


@dataclass
class SubTask:
    """分割されたサブタスク"""

    id: str
    parent_task_id: str
    title: str
    description: str
    task_type: TaskType
    complexity: TaskComplexity
    estimated_hours: float
    dependencies: List[str]
    required_skills: List[str]
    priority: int
    can_parallel: bool
    order_index: int


class IntelligentTaskSplitter(BaseManager):
    """知能的タスク分割システム"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__("IntelligentTaskSplitter")
        self.db_path = PROJECT_ROOT / "db" / "task_splitting.db"

        # 分割パターンの定義
        self.complexity_patterns = {
            # 非常に複雑なパターン
            TaskComplexity.VERY_COMPLEX: [
                r"complete\s+system|entire\s+application|full\s+platform",
                r"end\s*to\s*end|e2e|全体的|システム全体",
                r"multiple\s+components|複数のコンポーネント|複数の機能",
                r"architecture|アーキテクチャ|基盤設計",
            ],
            # 複雑なパターン
            TaskComplexity.COMPLEX: [
                r"implement\s+\w+\s+system|作成.*システム",
                r"create\s+\w+\s+framework|フレームワーク.*作成",
                r"design\s+and\s+implement|設計.*実装",
                r"integrate\s+with|統合.*機能",
            ],
            # 中程度のパターン
            TaskComplexity.MODERATE: [
                r"create\s+\w+\s+class|クラス.*作成",
                r"implement\s+\w+\s+function|関数.*実装",
                r"add\s+\w+\s+feature|機能.*追加",
                r"modify\s+\w+|変更.*機能",
            ],
            # 単純なパターン
            TaskComplexity.SIMPLE: [
                r"fix\s+bug|バグ.*修正",
                r"update\s+\w+|更新",
                r"add\s+comment|コメント.*追加",
                r"simple\s+change|簡単.*変更",
            ],
        }

        # タスクタイプパターン
        self.type_patterns = {
            TaskType.RESEARCH: [
                r"research|調査|analyze|分析|investigate|検討",
                r"study|学習|explore|探索|survey|サーベイ",
            ],
            TaskType.DESIGN: [
                r"design|設計|architecture|アーキテクチャ|plan|計画",
                r"spec|仕様|requirement|要件|wireframe|ワイヤーフレーム",
            ],
            TaskType.IMPLEMENTATION: [
                r"implement|実装|create|作成|develop|開発|code|コード",
                r"build|構築|construct|構成|program|プログラム",
            ],
            TaskType.TESTING: [
                r"test|テスト|verify|検証|validate|バリデーション",
                r"check|チェック|quality|品質|qa|QA",
            ],
            TaskType.DOCUMENTATION: [
                r"document|ドキュメント|doc|docs|manual|マニュアル",
                r"readme|README|guide|ガイド|instruction|説明",
            ],
            TaskType.INTEGRATION: [
                r"integrate|統合|merge|マージ|connect|接続",
                r"combine|結合|link|リンク|join|結合",
            ],
            TaskType.DEPLOYMENT: [
                r"deploy|デプロイ|release|リリース|publish|公開",
                r"install|インストール|setup|セットアップ",
            ],
            TaskType.REVIEW: [
                r"review|レビュー|inspect|検査|audit|監査",
                r"evaluate|評価|assess|査定|examine|調査",
            ],
        }

        # スキル要件マッピング
        self.skill_requirements = {
            TaskType.IMPLEMENTATION: ["python", "coding", "programming"],
            TaskType.TESTING: ["testing", "qa", "debugging"],
            TaskType.DESIGN: ["architecture", "design", "planning"],
            TaskType.RESEARCH: ["analysis", "research", "documentation"],
            TaskType.DOCUMENTATION: ["writing", "documentation", "communication"],
            TaskType.INTEGRATION: ["integration", "system_design", "troubleshooting"],
            TaskType.DEPLOYMENT: ["devops", "deployment", "system_admin"],
            TaskType.REVIEW: ["review", "analysis", "quality_assurance"],
        }

        self.initialize()

    def initialize(self) -> bool:
        """初期化処理"""
        try:
            self._init_database()
            return True
        except Exception as e:
            self.handle_error(e, "初期化")
            return False

    def _init_database(self):
        """データベース初期化"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3connect(self.db_path) as conn:
            # 分割されたタスクテーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS split_tasks (
                    id TEXT PRIMARY KEY,
                    parent_task_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    task_type TEXT,
                    complexity TEXT,
                    estimated_hours REAL,
                    required_skills TEXT,
                    priority INTEGER DEFAULT 0,
                    can_parallel BOOLEAN DEFAULT 1,
                    order_index INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    assigned_worker TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # タスク依存関係テーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    depends_on TEXT NOT NULL,
                    dependency_type TEXT DEFAULT 'blocks',
                    weight REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES split_tasks (id),
                    FOREIGN KEY (depends_on) REFERENCES split_tasks (id)
                )
            """
            )

            # 分割履歴テーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS splitting_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_task_id TEXT NOT NULL,
                    split_reason TEXT,
                    subtask_count INTEGER,
                    estimated_time_savings REAL,
                    actual_time_savings REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # インデックス作成
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_parent_task ON split_tasks(parent_task_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_status ON split_tasks(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_deps ON task_dependencies(task_id)"
            )

    def analyze_task_complexity(
        self, task_description: str
    ) -> Tuple[TaskComplexity, float]:
        """タスク複雑度分析"""
        try:
            description_lower = task_description.lower()

            # 各複雑度レベルでパターンマッチング
            complexity_scores = {}

            for complexity, patterns in self.complexity_patterns.items():
                score = 0
                for pattern in patterns:
            # 繰り返し処理
                    matches = len(re.findall(pattern, description_lower))
                    score += matches
                complexity_scores[complexity] = score

            # 追加要因の分析
            additional_factors = self._analyze_additional_complexity_factors(
                description_lower
            )

            # 基本複雑度を決定
            if not any(complexity_scores.values()):
                base_complexity = TaskComplexity.MODERATE
                base_score = 2.0
            else:
                base_complexity = max(
                    complexity_scores.keys(), key=lambda k: complexity_scores[k]
                )
                base_score = complexity_scores[base_complexity]

            # 追加要因で調整
            final_score = base_score + additional_factors

            # スコアに基づく最終複雑度決定
            if final_score >= 5:
                final_complexity = TaskComplexity.VERY_COMPLEX
            elif final_score >= 3:
                final_complexity = TaskComplexity.COMPLEX
            elif final_score >= 1:
                final_complexity = TaskComplexity.MODERATE
            else:
                final_complexity = TaskComplexity.SIMPLE

            return final_complexity, final_score

        except Exception as e:
            logger.error(f"複雑度分析エラー: {e}")
            return TaskComplexity.MODERATE, 2.0

    def _analyze_additional_complexity_factors(self, description: str) -> float:
        """追加の複雑度要因分析"""
        additional_score = 0.0

        # 長い説明文は複雑
        if len(description) > 500:
            additional_score += 1.0
        elif len(description) > 200:
            additional_score += 0.5

        # 複数の技術要素
        tech_keywords = [
            "database",
            "api",
            "frontend",
            "backend",
            "ui",
            "ux",
            "security",
            "performance",
            "scale",
            "optimization",
        ]
        tech_count = sum(1 for keyword in tech_keywords if keyword in description)
        additional_score += tech_count * 0.3

        # 複数のファイル/コンポーネント
        file_indicators = ["file", "component", "module", "class", "function"]
        file_count = sum(1 for indicator in file_indicators if indicator in description)
        if file_count > 3:
            additional_score += 1.0
        elif file_count > 1:
            additional_score += 0.5

        # 外部依存関係
        external_deps = ["integrate", "api", "third-party", "external", "service"]
        dep_count = sum(1 for dep in external_deps if dep in description)
        additional_score += dep_count * 0.4

        return additional_score

    def determine_task_type(self, task_description: str) -> TaskType:
        """タスクタイプ決定"""
        try:
            description_lower = task_description.lower()
            type_scores = {}

            for task_type, patterns in self.type_patterns.items():
                score = 0
            # 繰り返し処理
                for pattern in patterns:
                    matches = len(re.findall(pattern, description_lower))
                    score += matches
                type_scores[task_type] = score

            # 最高スコアのタイプを選択
            if not any(type_scores.values()):
                return TaskType.IMPLEMENTATION  # デフォルト

            return max(type_scores.keys(), key=lambda k: type_scores[k])

        except Exception as e:
            logger.error(f"タスクタイプ決定エラー: {e}")
            return TaskType.IMPLEMENTATION

    def split_into_subtasks(
        self, task_id: str, task_description: str, task_prompt: str = ""
    ) -> List[SubTask]:
        """タスクをサブタスクに分割"""
        try:
            logger.info(f"🔄 タスク分割開始: {task_id}")

            # 複雑度とタイプを分析
            complexity, complexity_score = self.analyze_task_complexity(
                task_description
            )
            task_type = self.determine_task_type(task_description)

            logger.info(
                f"📊 分析結果 - 複雑度: {complexity.value}, タイプ: {task_type.value}"
            )

            # 複雑度に応じて分割戦略を決定
            if complexity in [TaskComplexity.SIMPLE, TaskComplexity.MODERATE]:
                # 単純・中程度は分割しない
                subtasks = [
                    self._create_single_subtask(
                        task_id, task_description, task_type, complexity
                    )
                ]
            else:
                # 複雑なタスクは分割
                subtasks = self._split_complex_task(
                    task_id, task_description, task_prompt, task_type, complexity
                )

            # データベースに保存
            self._save_subtasks_to_db(subtasks)

            # 分割履歴を記録
            self._record_splitting_history(task_id, len(subtasks), complexity_score)

            logger.info(f"✅ タスク分割完了: {len(subtasks)}個のサブタスクを作成")

            return subtasks

        except Exception as e:
            logger.error(f"タスク分割エラー: {e}")
            return []

    def _create_single_subtask(
        self,
        task_id: str,
        description: str,
        task_type: TaskType,
        complexity: TaskComplexity,
    ) -> SubTask:
        """単一サブタスク作成"""
        estimated_hours = self._estimate_hours_by_complexity(complexity)
        required_skills = self.skill_requirements.get(task_type, [])

        return SubTask(
            id=f"{task_id}_main",
            parent_task_id=task_id,
            title=description[:100] + "..." if len(description) > 100 else description,
            description=description,
            task_type=task_type,
            complexity=complexity,
            estimated_hours=estimated_hours,
            dependencies=[],
            required_skills=required_skills,
            priority=1,
            can_parallel=True,
            order_index=1,
        )

    def _split_complex_task(
        self,
        task_id: str,
        description: str,
        prompt: str,
        task_type: TaskType,
        complexity: TaskComplexity,
    ) -> List[SubTask]:
        """複雑なタスクの分割"""
        subtasks = []

        # タスクタイプに応じた分割戦略
        if task_type == TaskType.IMPLEMENTATION:
            subtasks = self._split_implementation_task(
                task_id, description, prompt, complexity
            )
        elif task_type == TaskType.DESIGN:
            subtasks = self._split_design_task(task_id, description, prompt, complexity)
        elif task_type == TaskType.RESEARCH:
            subtasks = self._split_research_task(
                task_id, description, prompt, complexity
            )
        elif task_type == TaskType.TESTING:
            subtasks = self._split_testing_task(
                task_id, description, prompt, complexity
            )
        elif task_type == TaskType.INTEGRATION:
            subtasks = self._split_integration_task(
                task_id, description, prompt, complexity
            )
        else:
            # 汎用的な分割
            subtasks = self._split_generic_task(
                task_id, description, prompt, task_type, complexity
            )

        return subtasks

    def _split_implementation_task(
        self, task_id: str, description: str, prompt: str, complexity: TaskComplexity
    ) -> List[SubTask]:
        """実装タスクの分割"""
        subtasks = []
        base_hours = self._estimate_hours_by_complexity(complexity)

        # 1.0 設計・計画フェーズ
        subtasks.append(
            SubTask(
                id=f"{task_id}_design",
                parent_task_id=task_id,
                title=f"設計: {description[:50]}...",
                description=f"実装前の詳細設計とアーキテクチャ検討\n{description}",
                task_type=TaskType.DESIGN,
                complexity=TaskComplexity.MODERATE,
                estimated_hours=base_hours * 0.2,
                dependencies=[],
                required_skills=["architecture", "design", "planning"],
                priority=1,
                can_parallel=False,
                order_index=1,
            )
        )

        # 2.0 主要実装
        subtasks.append(
            SubTask(
                id=f"{task_id}_implementation",
                parent_task_id=task_id,
                title=f"実装: {description[:50]}...",
                description=f"メイン機能の実装\n{description}",
                task_type=TaskType.IMPLEMENTATION,
                complexity=complexity,
                estimated_hours=base_hours * 0.6,
                dependencies=[f"{task_id}_design"],
                required_skills=["python", "coding", "programming"],
                priority=2,
                can_parallel=False,
                order_index=2,
            )
        )

        # 3.0 テスト
        subtasks.append(
            SubTask(
                id=f"{task_id}_testing",
                parent_task_id=task_id,
                title=f"テスト: {description[:50]}...",
                description=f"実装機能のテスト作成と実行\n{description}",
                task_type=TaskType.TESTING,
                complexity=TaskComplexity.MODERATE,
                estimated_hours=base_hours * 0.15,
                dependencies=[f"{task_id}_implementation"],
                required_skills=["testing", "qa", "debugging"],
                priority=3,
                can_parallel=True,
                order_index=3,
            )
        )

        # 4.0 ドキュメント作成
        subtasks.append(
            SubTask(
                id=f"{task_id}_documentation",
                parent_task_id=task_id,
                title=f"ドキュメント: {description[:50]}...",
                description=f"実装内容のドキュメント作成\n{description}",
                task_type=TaskType.DOCUMENTATION,
                complexity=TaskComplexity.SIMPLE,
                estimated_hours=base_hours * 0.05,
                dependencies=[f"{task_id}_implementation"],
                required_skills=["writing", "documentation"],
                priority=4,
                can_parallel=True,
                order_index=4,
            )
        )

        return subtasks

    def _split_design_task(
        self, task_id: str, description: str, prompt: str, complexity: TaskComplexity
    ) -> List[SubTask]:
        """設計タスクの分割"""
        subtasks = []
        base_hours = self._estimate_hours_by_complexity(complexity)

        # 1.0 要件分析
        subtasks.append(
            SubTask(
                id=f"{task_id}_requirements",
                parent_task_id=task_id,
                title=f"要件分析: {description[:50]}...",
                description=f"設計対象の要件詳細分析\n{description}",
                task_type=TaskType.RESEARCH,
                complexity=TaskComplexity.MODERATE,
                estimated_hours=base_hours * 0.3,
                dependencies=[],
                required_skills=["analysis", "research"],
                priority=1,
                can_parallel=False,
                order_index=1,
            )
        )

        # 2.0 アーキテクチャ設計
        subtasks.append(
            SubTask(
                id=f"{task_id}_architecture",
                parent_task_id=task_id,
                title=f"アーキテクチャ設計: {description[:50]}...",
                description=f"システム全体のアーキテクチャ設計\n{description}",
                task_type=TaskType.DESIGN,
                complexity=complexity,
                estimated_hours=base_hours * 0.5,
                dependencies=[f"{task_id}_requirements"],
                required_skills=["architecture", "system_design"],
                priority=2,
                can_parallel=False,
                order_index=2,
            )
        )

        # 3.0 詳細設計
        subtasks.append(
            SubTask(
                id=f"{task_id}_detailed_design",
                parent_task_id=task_id,
                title=f"詳細設計: {description[:50]}...",
                description=f"個別コンポーネントの詳細設計\n{description}",
                task_type=TaskType.DESIGN,
                complexity=TaskComplexity.MODERATE,
                estimated_hours=base_hours * 0.2,
                dependencies=[f"{task_id}_architecture"],
                required_skills=["design", "planning"],
                priority=3,
                can_parallel=True,
                order_index=3,
            )
        )

        return subtasks

    def _split_research_task(
        self, task_id: str, description: str, prompt: str, complexity: TaskComplexity
    ) -> List[SubTask]:
        """調査タスクの分割"""
        subtasks = []
        base_hours = self._estimate_hours_by_complexity(complexity)

        # 1.0 情報収集
        subtasks.append(
            SubTask(
                id=f"{task_id}_information_gathering",
                parent_task_id=task_id,
                title=f"情報収集: {description[:50]}...",
                description=f"関連情報の収集と整理\n{description}",
                task_type=TaskType.RESEARCH,
                complexity=TaskComplexity.MODERATE,
                estimated_hours=base_hours * 0.4,
                dependencies=[],
                required_skills=["research", "analysis"],
                priority=1,
                can_parallel=True,
                order_index=1,
            )
        )

        # 2.0 分析・評価
        subtasks.append(
            SubTask(
                id=f"{task_id}_analysis",
                parent_task_id=task_id,
                title=f"分析・評価: {description[:50]}...",
                description=f"収集した情報の分析と評価\n{description}",
                task_type=TaskType.RESEARCH,
                complexity=complexity,
                estimated_hours=base_hours * 0.4,
                dependencies=[f"{task_id}_information_gathering"],
                required_skills=["analysis", "evaluation"],
                priority=2,
                can_parallel=False,
                order_index=2,
            )
        )

        # 3.0 レポート作成
        subtasks.append(
            SubTask(
                id=f"{task_id}_report",
                parent_task_id=task_id,
                title=f"レポート作成: {description[:50]}...",
                description=f"調査結果のレポート作成\n{description}",
                task_type=TaskType.DOCUMENTATION,
                complexity=TaskComplexity.MODERATE,
                estimated_hours=base_hours * 0.2,
                dependencies=[f"{task_id}_analysis"],
                required_skills=["writing", "documentation"],
                priority=3,
                can_parallel=False,
                order_index=3,
            )
        )

        return subtasks

    def _split_testing_task(
        self, task_id: str, description: str, prompt: str, complexity: TaskComplexity
    ) -> List[SubTask]:
        """テストタスクの分割"""
        subtasks = []
        base_hours = self._estimate_hours_by_complexity(complexity)

        # 1.0 テスト計画
        subtasks.append(
            SubTask(
                id=f"{task_id}_test_planning",
                parent_task_id=task_id,
                title=f"テスト計画: {description[:50]}...",
                description=f"テスト戦略と計画の策定\n{description}",
                task_type=TaskType.DESIGN,
                complexity=TaskComplexity.MODERATE,
                estimated_hours=base_hours * 0.2,
                dependencies=[],
                required_skills=["testing", "planning"],
                priority=1,
                can_parallel=False,
                order_index=1,
            )
        )

        # 2.0 テスト実装
        subtasks.append(
            SubTask(
                id=f"{task_id}_test_implementation",
                parent_task_id=task_id,
                title=f"テスト実装: {description[:50]}...",
                description=f"テストケースの実装\n{description}",
                task_type=TaskType.TESTING,
                complexity=complexity,
                estimated_hours=base_hours * 0.6,
                dependencies=[f"{task_id}_test_planning"],
                required_skills=["testing", "coding"],
                priority=2,
                can_parallel=True,
                order_index=2,
            )
        )

        # 3.0 テスト実行
        subtasks.append(
            SubTask(
                id=f"{task_id}_test_execution",
                parent_task_id=task_id,
                title=f"テスト実行: {description[:50]}...",
                description=f"テストの実行と結果分析\n{description}",
                task_type=TaskType.TESTING,
                complexity=TaskComplexity.MODERATE,
                estimated_hours=base_hours * 0.2,
                dependencies=[f"{task_id}_test_implementation"],
                required_skills=["testing", "analysis"],
                priority=3,
                can_parallel=False,
                order_index=3,
            )
        )

        return subtasks

    def _split_integration_task(
        self, task_id: str, description: str, prompt: str, complexity: TaskComplexity
    ) -> List[SubTask]:
        """統合タスクの分割"""
        subtasks = []
        base_hours = self._estimate_hours_by_complexity(complexity)

        # 1.0 統合計画
        subtasks.append(
            SubTask(
                id=f"{task_id}_integration_planning",
                parent_task_id=task_id,
                title=f"統合計画: {description[:50]}...",
                description=f"統合戦略と手順の計画\n{description}",
                task_type=TaskType.DESIGN,
                complexity=TaskComplexity.MODERATE,
                estimated_hours=base_hours * 0.25,
                dependencies=[],
                required_skills=["integration", "planning"],
                priority=1,
                can_parallel=False,
                order_index=1,
            )
        )

        # 2.0 統合実装
        subtasks.append(
            SubTask(
                id=f"{task_id}_integration_implementation",
                parent_task_id=task_id,
                title=f"統合実装: {description[:50]}...",
                description=f"統合処理の実装\n{description}",
                task_type=TaskType.INTEGRATION,
                complexity=complexity,
                estimated_hours=base_hours * 0.5,
                dependencies=[f"{task_id}_integration_planning"],
                required_skills=["integration", "coding"],
                priority=2,
                can_parallel=False,
                order_index=2,
            )
        )

        # 3.0 統合テスト
        subtasks.append(
            SubTask(
                id=f"{task_id}_integration_testing",
                parent_task_id=task_id,
                title=f"統合テスト: {description[:50]}...",
                description=f"統合動作のテスト\n{description}",
                task_type=TaskType.TESTING,
                complexity=TaskComplexity.MODERATE,
                estimated_hours=base_hours * 0.25,
                dependencies=[f"{task_id}_integration_implementation"],
                required_skills=["testing", "integration"],
                priority=3,
                can_parallel=False,
                order_index=3,
            )
        )

        return subtasks

    def _split_generic_task(
        self,
        task_id: str,
        description: str,
        prompt: str,
        task_type: TaskType,
        complexity: TaskComplexity,
    ) -> List[SubTask]:
        """汎用的なタスク分割"""
        subtasks = []
        base_hours = self._estimate_hours_by_complexity(complexity)

        # 複雑なタスクを3段階に分割
        subtasks.append(
            SubTask(
                id=f"{task_id}_phase1",
                parent_task_id=task_id,
                title=f"Phase 1: {description[:50]}...",
                description=f"第1段階: 準備・計画\n{description}",
                task_type=task_type,
                complexity=TaskComplexity.MODERATE,
                estimated_hours=base_hours * 0.3,
                dependencies=[],
                required_skills=self.skill_requirements.get(task_type, []),
                priority=1,
                can_parallel=False,
                order_index=1,
            )
        )

        subtasks.append(
            SubTask(
                id=f"{task_id}_phase2",
                parent_task_id=task_id,
                title=f"Phase 2: {description[:50]}...",
                description=f"第2段階: メイン作業\n{description}",
                task_type=task_type,
                complexity=complexity,
                estimated_hours=base_hours * 0.5,
                dependencies=[f"{task_id}_phase1"],
                required_skills=self.skill_requirements.get(task_type, []),
                priority=2,
                can_parallel=False,
                order_index=2,
            )
        )

        subtasks.append(
            SubTask(
                id=f"{task_id}_phase3",
                parent_task_id=task_id,
                title=f"Phase 3: {description[:50]}...",
                description=f"第3段階: 完成・検証\n{description}",
                task_type=task_type,
                complexity=TaskComplexity.MODERATE,
                estimated_hours=base_hours * 0.2,
                dependencies=[f"{task_id}_phase2"],
                required_skills=self.skill_requirements.get(task_type, []),
                priority=3,
                can_parallel=False,
                order_index=3,
            )
        )

        return subtasks

    def _estimate_hours_by_complexity(self, complexity: TaskComplexity) -> float:
        """複雑度による時間見積もり"""
        hour_mapping = {
            TaskComplexity.SIMPLE: 2.0,  # 2時間
            TaskComplexity.MODERATE: 8.0,  # 1日
            TaskComplexity.COMPLEX: 24.0,  # 3日
            TaskComplexity.VERY_COMPLEX: 80.0,  # 2週間
        }
        return hour_mapping.get(complexity, 8.0)

    def _save_subtasks_to_db(self, subtasks: List[SubTask]):
        """サブタスクをデータベースに保存"""
        with sqlite3connect(self.db_path) as conn:
            for subtask in subtasks:
            # 繰り返し処理
                conn.execute(
                    """
                    INSERT OR REPLACE INTO split_tasks
                    (id, parent_task_id, title, description, task_type, complexity,
                     estimated_hours, required_skills, priority, can_parallel, order_index)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        subtask.id,
                        subtask.parent_task_id,
                        subtask.title,
                        subtask.description,
                        subtask.task_type.value,
                        subtask.complexity.value,
                        subtask.estimated_hours,
                        json.dumps(subtask.required_skills),
                        subtask.priority,
                        subtask.can_parallel,
                        subtask.order_index,
                    ),
                )

                # 依存関係を保存
                for dependency in subtask.dependencies:
                    conn.execute(
                        """
                        INSERT INTO task_dependencies (task_id, depends_on)
                        VALUES (?, ?)
                    """,
                        (subtask.id, dependency),
                    )

    def _record_splitting_history(
        self, task_id: str, subtask_count: int, complexity_score: float
    ):
        """分割履歴を記録"""
        with sqlite3connect(self.db_path) as conn:
            # 時間削減見積もり
            estimated_savings = subtask_count * 0.1 * complexity_score  # 簡易計算

            conn.execute(
                """
                INSERT INTO splitting_history
                (original_task_id, split_reason, subtask_count, estimated_time_savings)
                VALUES (?, ?, ?, ?)
            """,
                (
                    task_id,
                    f"Complexity score: {complexity_score}",
                    subtask_count,
                    estimated_savings,
                ),
            )

    def determine_dependencies(self, subtasks: List[SubTask]) -> List[TaskDependency]:
        """依存関係の自動決定"""
        dependencies = []

        # 既に設定された依存関係を TaskDependency に変換
        for subtask in subtasks:
            for dep_id in subtask.dependencies:
                dependencies.append(
                    TaskDependency(
                        task_id=subtask.id,
                        depends_on=dep_id,
                        dependency_type="blocks",
                        weight=1.0,
                    )
                )

        return dependencies

    def get_parallel_execution_groups(
        self, subtasks: List[SubTask]
    ) -> List[List[SubTask]]:
        """並列実行可能なグループを特定"""
        try:
            # 依存関係に基づくトポロジカルソート
            groups = []
            remaining_tasks = subtasks.copy()
            completed_tasks = set()

            while remaining_tasks:
                # 現在実行可能なタスクを特定
                executable_tasks = []
                for task in remaining_tasks:
                    if all(dep in completed_tasks for dep in task.dependencies):
                        executable_tasks.append(task)

                if not executable_tasks:
                    # デッドロック状態 - 依存関係エラー
                    logger.warning("依存関係にサイクルが検出されました")
                    groups.append(remaining_tasks)
                    break

                # 並列実行可能なタスクをグループ化
                parallel_group = [
                    task for task in executable_tasks if task.can_parallel
                ]
                sequential_tasks = [
                    task for task in executable_tasks if not task.can_parallel
                ]

                # 順次実行タスクを個別グループに
                for task in sequential_tasks:
                    groups.append([task])
                    remaining_tasks.remove(task)
                    completed_tasks.add(task.id)

                # 並列実行タスクを1つのグループに
                if parallel_group:
                    groups.append(parallel_group)
                    for task in parallel_group:
                        remaining_tasks.remove(task)
                        completed_tasks.add(task.id)

            return groups

        except Exception as e:
            logger.error(f"並列実行グループ特定エラー: {e}")
            # エラー時は全タスクを順次実行
            return [[task] for task in subtasks]

    def get_subtasks_by_parent(self, parent_task_id: str) -> List[SubTask]:
        """親タスクIDからサブタスクを取得"""
        try:
            with sqlite3connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT id, parent_task_id, title, description, task_type, complexity,
                           estimated_hours, required_skills, priority, can_parallel, order_index
                    FROM split_tasks
                    WHERE parent_task_id = ?
                    ORDER BY order_index
                """,
                    (parent_task_id,),
                )

                subtasks = []
                for row in cursor:
                    # 依存関係を取得
                    dep_cursor = conn.execute(
                        "SELECT depends_on FROM task_dependencies WHERE task_id = ?",
                        (row[0],),
                    )
                    dependencies = [dep_row[0] for dep_row in dep_cursor]

                    subtask = SubTask(
                        id=row[0],
                        parent_task_id=row[1],
                        title=row[2],
                        description=row[3],
                        task_type=TaskType(row[4]),
                        complexity=TaskComplexity(row[5]),
                        estimated_hours=row[6],
                        dependencies=dependencies,
                        required_skills=json.loads(row[7]) if row[7] else [],
                        priority=row[8],
                        can_parallel=bool(row[9]),
                        order_index=row[10],
                    )
                    subtasks.append(subtask)

                return subtasks

        except Exception as e:
            logger.error(f"サブタスク取得エラー: {e}")
            return []

    def get_splitting_statistics(self) -> Dict[str, Any]:
        """分割統計情報取得"""
        try:
            with sqlite3connect(self.db_path) as conn:
                stats = {}

                # 全体統計
                cursor = conn.execute(
                    """
                    SELECT
                        COUNT(DISTINCT parent_task_id) as total_split_tasks,
                        COUNT(*) as total_subtasks,
                        AVG(estimated_hours) as avg_estimated_hours,
                        SUM(estimated_hours) as total_estimated_hours
                    FROM split_tasks
                """
                )
                row = cursor.fetchone()
                stats["total_split_tasks"] = row[0]
                stats["total_subtasks"] = row[1]
                stats["avg_estimated_hours"] = row[2] or 0.0
                stats["total_estimated_hours"] = row[3] or 0.0

                # 複雑度別統計
                cursor = conn.execute(
                    """
                    SELECT complexity, COUNT(*) as count, AVG(estimated_hours) as avg_hours
                    FROM split_tasks
                    GROUP BY complexity
                """
                )
                stats["by_complexity"] = {}
                for row in cursor:
                    stats["by_complexity"][row[0]] = {
                        "count": row[1],
                        "avg_hours": row[2],
                    }

                # タイプ別統計
                cursor = conn.execute(
                    """
                    SELECT task_type, COUNT(*) as count, AVG(estimated_hours) as avg_hours
                    FROM split_tasks
                    GROUP BY task_type
                """
                )
                stats["by_type"] = {}
                for row in cursor:
                    stats["by_type"][row[0]] = {"count": row[1], "avg_hours": row[2]}

                # 時間削減効果
                cursor = conn.execute(
                    """
                    SELECT
                        AVG(estimated_time_savings) as avg_time_savings,
                        SUM(estimated_time_savings) as total_time_savings
                    FROM splitting_history
                """
                )
                row = cursor.fetchone()
                stats["time_savings"] = {
                    "avg_savings": row[0] or 0.0,
                    "total_savings": row[1] or 0.0,
                }

                return stats

        except Exception as e:
            logger.error(f"統計取得エラー: {e}")
            return {}


if __name__ == "__main__":
    # テスト実行
    splitter = IntelligentTaskSplitter()

    # テストケース
    test_cases = [
        {
            "task_id": "test_001",
            "description": "Create a complete user authentication system with login, registration, password reset, and \
                session management",
            "prompt": "Implement a comprehensive authentication system",
        },
        {
            "task_id": "test_002",
            "description": "Fix a simple bug in the login function",
            "prompt": "Quick bug fix needed",
        },
        {
            "task_id": "test_003",
            "description": "Research and analyze the best practices for microservices architecture in Python",
            "prompt": "Research task for architecture decision",
        },
    ]

    print("=" * 80)
    print("🔄 Intelligent Task Splitter Test")
    print("=" * 80)

    # 繰り返し処理
    for test_case in test_cases:
        print(f"\n📋 Processing: {test_case['task_id']}")
        print(f"Description: {test_case['description']}")

        # 複雑度分析
        complexity, score = splitter.analyze_task_complexity(test_case["description"])
        task_type = splitter.determine_task_type(test_case["description"])

        print(f"🎯 Analysis: {complexity.value} ({score:0.1f}), Type: {task_type.value}")

        # タスク分割
        subtasks = splitter.split_into_subtasks(
            test_case["task_id"], test_case["description"], test_case["prompt"]
        )

        print(f"📊 Split into {len(subtasks)} subtasks:")
        for i, subtask in enumerate(subtasks, 1):
            print(f"  {i}. {subtask.title}")
            print(
                f"     Type: {subtask.task_type.value}, Hours: {subtask.estimated_hours}"
            )
            print(f"     Dependencies: {subtask.dependencies}")
            print(f"     Parallel: {subtask.can_parallel}")

        # 並列実行グループ
        groups = splitter.get_parallel_execution_groups(subtasks)
        print(f"🔄 Parallel execution groups: {len(groups)}")
        for i, group in enumerate(groups, 1):
            task_titles = [task.title[:30] + "..." for task in group]
            print(f"  Group {i}: {task_titles}")

    # 統計情報
    print(f"\n📈 Splitting Statistics:")
    stats = splitter.get_splitting_statistics()
    print(f"Total split tasks: {stats.get('total_split_tasks', 0)}")
    print(f"Total subtasks: {stats.get('total_subtasks', 0)}")
    print(f"Average estimated hours: {stats.get('avg_estimated_hours', 0.0):0.1f}")
