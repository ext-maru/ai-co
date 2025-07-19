#!/usr/bin/env python3
"""
PM品質評価システム - PMが納得するまで繰り返すフィードバック機能
"""

import json
import logging
import re
import sqlite3
import subprocess

# プロジェクトルートをPythonパスに追加
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseManager
from libs.error_intelligence_manager import ErrorIntelligenceManager
from libs.test_manager import TestManager

logger = logging.getLogger(__name__)


class PMQualityEvaluator(BaseManager):
    """PM品質評価とフィードバック機能を提供するクラス"""

    def __init__(self):
        super().__init__("PMQualityEvaluator")
        self.db_path = PROJECT_ROOT / "db" / "pm_quality_records.db"
        self.test_manager = TestManager(str(PROJECT_ROOT))
        self.error_manager = ErrorIntelligenceManager()

        # 品質評価基準
        self.quality_criteria = {
            "test_success_rate": 95.0,  # テスト成功率（%）
            "code_quality_score": 80.0,  # コード品質スコア
            "requirement_compliance": 90.0,  # 要件適合度（%）
            "error_rate": 5.0,  # エラー率（%）以下
            "performance_score": 75.0,  # パフォーマンススコア
            "security_score": 85.0,  # セキュリティスコア
        }

        # 重要度重み付け
        self.criterion_weights = {
            "test_success_rate": 0.25,
            "code_quality_score": 0.20,
            "requirement_compliance": 0.25,
            "error_rate": 0.15,
            "performance_score": 0.10,
            "security_score": 0.05,
        }

        # 合格基準
        self.pass_threshold = 80.0  # 総合スコア80%以上で合格
        self.max_retry_attempts = 3  # 最大再試行回数

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
        """品質評価データベースの初期化"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # 品質評価記録テーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS quality_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    attempt_number INTEGER DEFAULT 1,
                    evaluation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    test_success_rate REAL,
                    code_quality_score REAL,
                    requirement_compliance REAL,
                    error_rate REAL,
                    performance_score REAL,
                    security_score REAL,
                    overall_score REAL,
                    pm_approved BOOLEAN DEFAULT 0,
                    feedback_message TEXT,
                    retry_required BOOLEAN DEFAULT 0,
                    files_evaluated TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # フィードバック履歴テーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    attempt_number INTEGER,
                    feedback_type TEXT,
                    feedback_content TEXT,
                    improvement_suggestions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 学習パターンテーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_description TEXT,
                    success_rate REAL,
                    usage_count INTEGER DEFAULT 1,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # インデックス作成
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_id ON quality_evaluations(task_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_pm_approved ON quality_evaluations(pm_approved)"
            )

    def evaluate_task_quality(
        self, task_id: str, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """タスクの品質を総合評価"""
        try:
            logger.info(f"🎯 品質評価開始: {task_id}")

            # 各基準で評価
            evaluation_results = {}

            # 1. テスト成功率評価
            evaluation_results["test_success_rate"] = self._evaluate_test_success(
                task_data
            )

            # 2. コード品質評価
            evaluation_results["code_quality_score"] = self._evaluate_code_quality(
                task_data
            )

            # 3. 要件適合度評価
            evaluation_results[
                "requirement_compliance"
            ] = self._evaluate_requirement_compliance(task_data)

            # 4. エラー率評価
            evaluation_results["error_rate"] = self._evaluate_error_rate(task_data)

            # 5. パフォーマンス評価
            evaluation_results["performance_score"] = self._evaluate_performance(
                task_data
            )

            # 6. セキュリティ評価
            evaluation_results["security_score"] = self._evaluate_security(task_data)

            # 総合スコア計算
            overall_score = self._calculate_overall_score(evaluation_results)
            evaluation_results["overall_score"] = overall_score

            # PM承認判定
            pm_approved = overall_score >= self.pass_threshold
            evaluation_results["pm_approved"] = pm_approved

            # フィードバックメッセージ生成
            feedback_message = self._generate_feedback_message(evaluation_results)
            evaluation_results["feedback_message"] = feedback_message

            # 再試行要否判定
            retry_required = not pm_approved and self._should_retry(task_id)
            evaluation_results["retry_required"] = retry_required

            # データベースに記録
            self._record_evaluation(task_id, evaluation_results, task_data)

            logger.info(
                f"✅ 品質評価完了: {task_id} - スコア: {overall_score:.1f}% - {'承認' if pm_approved else '要改善'}"
            )

            return evaluation_results

        except Exception as e:
            logger.error(f"品質評価エラー: {e}")
            return {
                "overall_score": 0.0,
                "pm_approved": False,
                "feedback_message": f"評価エラー: {str(e)}",
                "retry_required": False,
            }

    def _evaluate_test_success(self, task_data: Dict[str, Any]) -> float:
        """テスト成功率評価"""
        try:
            files_created = task_data.get("files_created", [])
            python_files = [f for f in files_created if f.endswith(".py")]

            if not python_files:
                return 100.0  # Pythonファイルがない場合は満点

            # テスト実行
            test_results = []
            for py_file in python_files:
                file_path = Path(py_file)

                # 対応するテストファイルを探す
                if file_path.parts[0] in ["workers", "libs"]:
                    test_file = (
                        PROJECT_ROOT / "tests" / "unit" / f"test_{file_path.name}"
                    )

                    if test_file.exists():
                        result = self.test_manager.run_specific_test(str(test_file))
                        test_results.append(result.get("success", False))
                    else:
                        # 基本的な構文チェック
                        result = self._run_syntax_check(str(PROJECT_ROOT / py_file))
                        test_results.append(result.get("success", False))

            if not test_results:
                return 100.0

            success_rate = (sum(test_results) / len(test_results)) * 100
            return success_rate

        except Exception as e:
            logger.error(f"テスト評価エラー: {e}")
            return 0.0

    def _evaluate_code_quality(self, task_data: Dict[str, Any]) -> float:
        """コード品質評価"""
        try:
            files_created = task_data.get("files_created", [])
            python_files = [f for f in files_created if f.endswith(".py")]

            if not python_files:
                return 100.0

            quality_scores = []

            for py_file in python_files:
                file_path = PROJECT_ROOT / py_file
                if file_path.exists():
                    score = self._analyze_code_quality(file_path)
                    quality_scores.append(score)

            if not quality_scores:
                return 100.0

            return sum(quality_scores) / len(quality_scores)

        except Exception as e:
            logger.error(f"コード品質評価エラー: {e}")
            return 0.0

    def _evaluate_requirement_compliance(self, task_data: Dict[str, Any]) -> float:
        """要件適合度評価"""
        try:
            # 基本的な要件チェック
            prompt = task_data.get("prompt", "")
            response = task_data.get("response", "")
            files_created = task_data.get("files_created", [])

            compliance_score = 0.0

            # ファイル生成要件
            if "ファイル" in prompt or "file" in prompt.lower():
                if files_created:
                    compliance_score += 30.0

            # 実装要件
            if "class" in prompt.lower() or "クラス" in prompt:
                if self._check_class_implementation(files_created):
                    compliance_score += 25.0

            # 機能要件
            if "function" in prompt.lower() or "関数" in prompt:
                if self._check_function_implementation(files_created):
                    compliance_score += 25.0

            # レスポンス品質
            if response and len(response) > 100:
                compliance_score += 20.0

            return min(compliance_score, 100.0)

        except Exception as e:
            logger.error(f"要件適合度評価エラー: {e}")
            return 0.0

    def _evaluate_error_rate(self, task_data: Dict[str, Any]) -> float:
        """エラー率評価（低いほど良い）"""
        try:
            error_trace = task_data.get("error_trace", "")
            status = task_data.get("status", "completed")

            if status == "completed" and not error_trace:
                return 100.0  # エラーなし

            if status == "failed":
                return 0.0  # 完全失敗

            # エラーの重要度分析
            if error_trace:
                analysis = self.error_manager.analyze_error(error_trace)
                severity = analysis.get("severity", "low")

                if severity == "high":
                    return 20.0
                elif severity == "medium":
                    return 60.0
                else:
                    return 80.0

            return 100.0

        except Exception as e:
            logger.error(f"エラー率評価エラー: {e}")
            return 0.0

    def _evaluate_performance(self, task_data: Dict[str, Any]) -> float:
        """パフォーマンス評価"""
        try:
            duration = task_data.get("duration", 0.0)

            # 実行時間に基づく評価
            if duration <= 10.0:
                return 100.0
            elif duration <= 30.0:
                return 80.0
            elif duration <= 60.0:
                return 60.0
            elif duration <= 120.0:
                return 40.0
            else:
                return 20.0

        except Exception as e:
            logger.error(f"パフォーマンス評価エラー: {e}")
            return 75.0

    def _evaluate_security(self, task_data: Dict[str, Any]) -> float:
        """セキュリティ評価"""
        try:
            files_created = task_data.get("files_created", [])

            security_score = 100.0

            for file_path in files_created:
                if file_path.endswith(".py"):
                    full_path = PROJECT_ROOT / file_path
                    if full_path.exists():
                        issues = self._check_security_issues(full_path)
                        security_score -= len(issues) * 10

            return max(security_score, 0.0)

        except Exception as e:
            logger.error(f"セキュリティ評価エラー: {e}")
            return 85.0

    def _calculate_overall_score(self, evaluation_results: Dict[str, float]) -> float:
        """総合スコア計算"""
        weighted_score = 0.0

        for criterion, weight in self.criterion_weights.items():
            score = evaluation_results.get(criterion, 0.0)
            weighted_score += score * weight

        return weighted_score

    def _generate_feedback_message(self, evaluation_results: Dict[str, Any]) -> str:
        """フィードバックメッセージ生成"""
        overall_score = evaluation_results.get("overall_score", 0.0)
        pm_approved = evaluation_results.get("pm_approved", False)

        if pm_approved:
            return f"✅ PM承認: 総合スコア {overall_score:.1f}% - 品質基準を満たしています"

        # 改善点を特定
        improvements = []

        for criterion, threshold in self.quality_criteria.items():
            current_score = evaluation_results.get(criterion, 0.0)

            if criterion == "error_rate":
                if current_score < 100 - threshold:  # エラー率は逆転
                    improvements.append(f"エラー率改善 (現在: {100-current_score:.1f}%)")
            else:
                if current_score < threshold:
                    improvements.append(f"{criterion}改善 (現在: {current_score:.1f}%)")

        message = f"❌ PM再評価要: 総合スコア {overall_score:.1f}%\n"
        message += "改善点:\n"
        for improvement in improvements[:3]:  # 最大3つの改善点
            message += f"  - {improvement}\n"

        return message

    def _should_retry(self, task_id: str) -> bool:
        """再試行すべきかの判定"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM quality_evaluations WHERE task_id = ?", (task_id,)
            )
            attempt_count = cursor.fetchone()[0]

            return attempt_count < self.max_retry_attempts

    def _record_evaluation(
        self,
        task_id: str,
        evaluation_results: Dict[str, Any],
        task_data: Dict[str, Any],
    ):
        """評価結果をデータベースに記録"""
        with sqlite3.connect(self.db_path) as conn:
            # 試行回数取得
            cursor = conn.execute(
                "SELECT COUNT(*) FROM quality_evaluations WHERE task_id = ?", (task_id,)
            )
            attempt_number = cursor.fetchone()[0] + 1

            conn.execute(
                """
                INSERT INTO quality_evaluations
                (task_id, attempt_number, test_success_rate, code_quality_score,
                 requirement_compliance, error_rate, performance_score, security_score,
                 overall_score, pm_approved, feedback_message, retry_required, files_evaluated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    task_id,
                    attempt_number,
                    evaluation_results.get("test_success_rate", 0.0),
                    evaluation_results.get("code_quality_score", 0.0),
                    evaluation_results.get("requirement_compliance", 0.0),
                    evaluation_results.get("error_rate", 0.0),
                    evaluation_results.get("performance_score", 0.0),
                    evaluation_results.get("security_score", 0.0),
                    evaluation_results.get("overall_score", 0.0),
                    evaluation_results.get("pm_approved", False),
                    evaluation_results.get("feedback_message", ""),
                    evaluation_results.get("retry_required", False),
                    json.dumps(task_data.get("files_created", [])),
                ),
            )

    def _run_syntax_check(self, file_path: str) -> Dict[str, Any]:
        """構文チェック"""
        try:
            cmd = ["python3", "-m", "py_compile", file_path]
            result = subprocess.run(cmd, capture_output=True, text=True)

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
            }
        except Exception as e:
            return {"success": False, "output": "", "errors": str(e)}

    def _analyze_code_quality(self, file_path: Path) -> float:
        """コード品質分析"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            quality_score = 100.0

            # 基本的な品質チェック
            lines = content.split("\n")

            # 1. 行の長さチェック
            long_lines = [line for line in lines if len(line) > 120]
            quality_score -= len(long_lines) * 2

            # 2. コメント率チェック
            comment_lines = [line for line in lines if line.strip().startswith("#")]
            if len(lines) > 0:
                comment_ratio = len(comment_lines) / len(lines)
                if comment_ratio < 0.1:  # 10%未満
                    quality_score -= 10

            # 3. 関数の複雑さチェック（簡易版）
            function_lines = [line for line in lines if "def " in line]
            if len(function_lines) > 10:  # 関数が多すぎる
                quality_score -= 5

            return max(quality_score, 0.0)

        except Exception as e:
            logger.error(f"コード品質分析エラー: {e}")
            return 75.0

    def _check_class_implementation(self, files_created: List[str]) -> bool:
        """クラス実装チェック"""
        for file_path in files_created:
            if file_path.endswith(".py"):
                full_path = PROJECT_ROOT / file_path
                if full_path.exists():
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            if "class " in content:
                                return True
                    except:
                        pass
        return False

    def _check_function_implementation(self, files_created: List[str]) -> bool:
        """関数実装チェック"""
        for file_path in files_created:
            if file_path.endswith(".py"):
                full_path = PROJECT_ROOT / file_path
                if full_path.exists():
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            if "def " in content:
                                return True
                    except:
                        pass
        return False

    def _check_security_issues(self, file_path: Path) -> List[str]:
        """セキュリティ問題チェック"""
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 危険なパターンチェック
            dangerous_patterns = [
                r"eval\s*\(",
                r"exec\s*\(",
                r"subprocess\.call\s*\(",
                r"os\.system\s*\(",
                r"input\s*\(",
                r"raw_input\s*\(",
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, content):
                    issues.append(f"Potentially dangerous pattern: {pattern}")

        except Exception as e:
            logger.error(f"セキュリティチェックエラー: {e}")

        return issues

    def get_evaluation_history(self, task_id: str) -> List[Dict[str, Any]]:
        """評価履歴取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM quality_evaluations
                WHERE task_id = ?
                ORDER BY attempt_number
            """,
                (task_id,),
            )

            columns = [desc[0] for desc in cursor.description]
            history = []

            for row in cursor:
                record = dict(zip(columns, row))
                history.append(record)

            return history

    def get_quality_statistics(self) -> Dict[str, Any]:
        """品質統計情報取得"""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}

            # 全体統計
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_evaluations,
                    AVG(overall_score) as avg_score,
                    COUNT(CASE WHEN pm_approved = 1 THEN 1 END) as approved_count,
                    COUNT(CASE WHEN retry_required = 1 THEN 1 END) as retry_count
                FROM quality_evaluations
            """
            )

            row = cursor.fetchone()
            stats["total_evaluations"] = row[0]
            stats["average_score"] = row[1] or 0.0
            stats["approval_rate"] = (row[2] / row[0] * 100) if row[0] > 0 else 0.0
            stats["retry_rate"] = (row[3] / row[0] * 100) if row[0] > 0 else 0.0

            # 基準別統計
            cursor = conn.execute(
                """
                SELECT
                    AVG(test_success_rate) as avg_test_success,
                    AVG(code_quality_score) as avg_code_quality,
                    AVG(requirement_compliance) as avg_requirement,
                    AVG(error_rate) as avg_error_rate,
                    AVG(performance_score) as avg_performance,
                    AVG(security_score) as avg_security
                FROM quality_evaluations
            """
            )

            row = cursor.fetchone()
            stats["criteria_averages"] = {
                "test_success_rate": row[0] or 0.0,
                "code_quality_score": row[1] or 0.0,
                "requirement_compliance": row[2] or 0.0,
                "error_rate": row[3] or 0.0,
                "performance_score": row[4] or 0.0,
                "security_score": row[5] or 0.0,
            }

            return stats


if __name__ == "__main__":
    # テスト実行
    evaluator = PMQualityEvaluator()

    # テストデータ
    test_task_data = {
        "task_id": "test_task_001",
        "status": "completed",
        "files_created": ["workers/test_worker.py"],
        "duration": 25.0,
        "prompt": "Create a test worker class",
        "response": "Created TestWorker class with proper initialization and methods",
        "error_trace": "",
    }

    print("=== PM Quality Evaluator Test ===")
    result = evaluator.evaluate_task_quality("test_task_001", test_task_data)

    print(f"Overall Score: {result['overall_score']:.1f}%")
    print(f"PM Approved: {result['pm_approved']}")
    print(f"Feedback: {result['feedback_message']}")
    print(f"Retry Required: {result['retry_required']}")

    print("\n=== Quality Statistics ===")
    stats = evaluator.get_quality_statistics()
    print(f"Total Evaluations: {stats['total_evaluations']}")
    print(f"Average Score: {stats['average_score']:.1f}%")
    print(f"Approval Rate: {stats['approval_rate']:.1f}%")
