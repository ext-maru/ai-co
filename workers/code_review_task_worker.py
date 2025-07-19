#!/usr/bin/env python3
"""
Code Review Task Worker - Elders Guild Code Analysis Specialist
コードレビュータスクワーカー - エルダー評議会のコード分析専門家

This worker serves as the code analysis specialist within the Elder Tree hierarchy,
reporting to the Knowledge Sage and performing detailed code reviews.
"""

import ast
import asyncio
import logging
import re
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


class CodeReviewTaskWorker(AsyncBaseWorkerV2):
    """Code Review Task Worker - Code analysis specialist of the Elder Tree hierarchy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(
            worker_name="code_review_task_worker",
            config=config,
            input_queues=["ai_tasks"],
            output_queues=["ai_pm"],
        )
        self.analysis_timeout = config.get("analysis_timeout", 30)
        self.created_at = datetime.now()
        self.analyses_performed = 0
        self.issues_found = 0

        # Initialize Elder systems
        self.elder_systems_initialized = False
        self._initialize_elder_systems()

        self.logger.info(
            f"CodeReviewTaskWorker initialized as Elder Tree code analysis specialist"
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
        """メッセージ処理 - コードレビュー要求を処理 with Elder Tree integration"""
        self.analyses_performed += 1
        message_type = message.get("message_type")

        try:
            if message_type == "code_review_request":
                result = await self._analyze_code_with_elders(message)

                # Report analysis patterns to Knowledge Sage
                if self.elder_systems_initialized:
                    await self._report_analysis_patterns_to_knowledge_sage(result)

                return result
            elif message_type == "improvement_request":
                return await self._re_analyze_improved_code_with_elders(message)
            else:
                raise ValueError(f"Unsupported message type: {message_type}")

        except Exception as e:
            if self.elder_systems_initialized:
                await self._report_error_to_incident_sage(e, message)
            raise

    async def _analyze_code_with_elders(
        self, message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """コード解析実行"""
        payload = message["payload"]
        code_content = payload["code_content"]
        language = payload.get("language", "python")
        review_options = payload.get("review_options", {})

        # 基本的な解析実行
        analysis_results = {
            "syntax_issues": [],
            "logic_issues": [],
            "performance_issues": [],
            "security_issues": [],
        }

        if language == "python":
            # Python固有の解析
            if review_options.get("check_syntax", True):
                analysis_results["syntax_issues"] = await self._check_python_syntax(
                    code_content
                )

            if review_options.get("check_logic", True):
                analysis_results["logic_issues"] = await self._check_python_logic(
                    code_content
                )

            if review_options.get("check_performance", True):
                analysis_results[
                    "performance_issues"
                ] = await self._check_python_performance(code_content)

            if review_options.get("check_security", True):
                analysis_results["security_issues"] = await self._check_python_security(
                    code_content
                )

        # コードメトリクス計算
        code_metrics = await self._calculate_code_metrics(code_content)

        return {
            "message_id": f"analysis_{message['task_id']}",
            "task_id": message["task_id"],
            "worker_source": "task_worker",
            "worker_target": "pm_worker",
            "message_type": "code_analysis_result",
            "iteration": message.get("iteration", 1),
            "payload": {
                "analysis_results": analysis_results,
                "code_metrics": code_metrics,
            },
        }

    async def _re_analyze_improved_code_with_elders(
        self, message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """改善されたコードの再解析"""
        payload = message["payload"]
        revised_code = payload["revised_code"]

        # 改善されたコードで新しい解析実行
        code_message = {
            "task_id": message["task_id"],
            "iteration": message.get("iteration", 1) + 1,
            "payload": {
                "code_content": revised_code,
                "language": "python",
                "review_options": {
                    "check_syntax": True,
                    "check_logic": True,
                    "check_performance": True,
                    "check_security": True,
                },
            },
        }

        return await self._analyze_code(code_message)

    async def _check_python_syntax(self, code: str) -> List[Dict[str, Any]]:
        """Python構文チェック"""
        issues = []

        try:
            # AST解析で構文チェック
            ast.parse(code)
        except SyntaxError as e:
            issues.append(
                {
                    "line": e.lineno or 0,
                    "type": "syntax_error",
                    "severity": "error",
                    "message": f"Syntax error: {e.msg}",
                    "suggestion": "Fix syntax error",
                }
            )

        # 基本的なスタイルチェック
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            # docstringチェック
            if line.strip().startswith("def ") and "def __" not in line:
                # 次の行がdocstringでない場合
                if (
                    i < len(lines)
                    and not lines[i].strip().startswith('"""')
                    and not lines[i].strip().startswith("'''")
                ):
                    issues.append(
                        {
                            "line": i,
                            "type": "style",
                            "severity": "warning",
                            "message": "Missing function docstring",
                            "suggestion": "Add docstring explaining function purpose",
                        }
                    )

        return issues

    async def _check_python_logic(self, code: str) -> List[Dict[str, Any]]:
        """Python論理チェック"""
        issues = []

        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            # 短い変数名チェック
            if "def " in line and "(" in line:
                # 関数定義から引数を抽出
                func_match = re.search(r"def\s+\w+\s*\(([^)]*)\)", line)
                if func_match:
                    params = func_match.group(1)
                    # 1文字の引数名をチェック
                    param_names = [
                        p.strip().split(":")[0].strip()
                        for p in params.split(",")
                        if p.strip()
                    ]
                    for param in param_names:
                        if len(param) == 1 and param.isalpha():
                            issues.append(
                                {
                                    "line": i,
                                    "type": "naming",
                                    "severity": "warning",
                                    "message": f"Variable names '{param}' are not descriptive",
                                    "suggestion": "Use descriptive names like 'length', 'width'",
                                }
                            )

            # 未使用変数チェック（簡易版）
            if " = " in line and "=" not in line.replace(" = ", ""):
                var_match = re.search(r"(\w+)\s*=", line)
                if var_match:
                    var_name = var_match.group(1)
                    if var_name not in code.replace(line, ""):  # 他の場所で使われていない
                        issues.append(
                            {
                                "line": i,
                                "type": "unused_variable",
                                "severity": "warning",
                                "message": f"Variable '{var_name}' is defined but never used",
                                "suggestion": "Remove unused variable or use it",
                            }
                        )

        return issues

    async def _check_python_performance(self, code: str) -> List[Dict[str, Any]]:
        """Pythonパフォーマンスチェック"""
        issues = []

        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            # 非効率的な文字列結合チェック
            if '" + ' in line or "' + " in line:
                issues.append(
                    {
                        "line": i,
                        "type": "string_concatenation",
                        "severity": "info",
                        "message": "Inefficient string concatenation",
                        "suggestion": "Use f-string for better performance",
                    }
                )

        return issues

    async def _check_python_security(self, code: str) -> List[Dict[str, Any]]:
        """Pythonセキュリティチェック"""
        issues = []

        # 危険なパターンをチェック
        security_patterns = [
            (r"eval\s*\(", "eval_usage", "critical", "Use of eval() is dangerous"),
            (r"exec\s*\(", "exec_usage", "critical", "Use of exec() is dangerous"),
            (
                r"os\.system\s*\(",
                "command_injection",
                "critical",
                "os.system() is vulnerable to command injection",
            ),
            (
                r"subprocess\.call\([^)]*shell=True",
                "command_injection",
                "critical",
                "subprocess with shell=True is dangerous",
            ),
            # SQL injection用の改善されたパターン（f-stringとSQLを区別）
            (
                r'f["\'].*SELECT.*\{.*\}.*["\']',
                "sql_injection",
                "high",
                "Potential SQL injection vulnerability",
            ),
            (
                r'f["\'].*INSERT.*\{.*\}.*["\']',
                "sql_injection",
                "high",
                "Potential SQL injection vulnerability",
            ),
            (
                r'f["\'].*UPDATE.*\{.*\}.*["\']',
                "sql_injection",
                "high",
                "Potential SQL injection vulnerability",
            ),
        ]

        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern, issue_type, severity, message in security_patterns:
                if re.search(pattern, line):
                    issues.append(
                        {
                            "line": i,
                            "type": issue_type,
                            "severity": severity,
                            "message": message,
                            "suggestion": "Use safer alternatives",
                        }
                    )

        return issues

    async def _calculate_code_metrics(self, code: str) -> Dict[str, Any]:
        """コードメトリクス計算"""
        lines = code.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]

        # 基本メトリクス
        lines_of_code = len(non_empty_lines)

        # シンプルな複雑度計算（制御構造の数）
        complexity_keywords = ["if", "elif", "for", "while", "try", "except"]
        complexity_score = 1  # 基本複雑度
        for line in lines:
            for keyword in complexity_keywords:
                if f" {keyword} " in line or line.strip().startswith(keyword + " "):
                    complexity_score += 1

        # 保守性指数（簡易計算）
        # 短いコード、低複雑度、コメント有りで高スコア
        comment_lines = len(
            [line for line in lines if line.strip().startswith("#") or '"""' in line]
        )
        maintainability_index = max(
            0,
            100 - complexity_score * 5 - max(0, lines_of_code - 50) + comment_lines * 2,
        )

        return {
            "lines_of_code": lines_of_code,
            "complexity_score": complexity_score,
            "maintainability_index": min(100, maintainability_index),
        }

    async def _report_analysis_patterns_to_knowledge_sage(self, result: Dict[str, Any]):
        """Report code analysis patterns to Knowledge Sage"""
        if not self.four_sages:
            return

        try:
            # Count total issues
            total_issues = 0
            issue_types = {}

            for category in [
                "syntax_issues",
                "logic_issues",
                "performance_issues",
                "security_issues",
            ]:
                issues = result.get("analysis_results", {}).get(category, [])
                total_issues += len(issues)

                for issue in issues:
                    issue_type = issue.get("type", "unknown")
                    issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

            self.issues_found += total_issues

            pattern_data = {
                "type": "code_analysis_pattern",
                "worker": "code_review_task_worker",
                "total_issues": total_issues,
                "issue_breakdown": issue_types,
                "code_metrics": result.get("code_metrics", {}),
                "language": result.get("language", "unknown"),
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.store_knowledge("analysis_patterns", pattern_data)

        except Exception as e:
            self.logger.error(
                f"Failed to report analysis patterns to Knowledge Sage: {e}"
            )

    async def _report_error_to_incident_sage(
        self, error: Exception, message: Dict[str, Any]
    ):
        """Report processing error to Incident Sage"""
        if not self.four_sages:
            return

        try:
            incident_data = {
                "type": "code_review_task_error",
                "worker": "code_review_task_worker",
                "error": str(error),
                "message_type": message.get("message_type"),
                "task_id": message.get("task_id"),
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.consult_incident_sage(incident_data)

        except Exception as e:
            self.logger.error(f"Failed to report error to Incident Sage: {e}")

    def get_elder_analysis_status(self) -> Dict[str, Any]:
        """Get comprehensive Elder code analysis specialist status"""
        status = {
            "worker_type": "code_review_task_worker",
            "elder_role": "Code Analysis Specialist",
            "reporting_to": "Knowledge Sage",
            "elder_systems": {
                "initialized": self.elder_systems_initialized,
                "four_sages_active": self.four_sages is not None,
                "council_summoner_active": self.council_summoner is not None,
                "elder_tree_connected": self.elder_tree is not None,
            },
            "analysis_stats": {
                "analyses_performed": self.analyses_performed,
                "issues_found": self.issues_found,
                "analysis_timeout": self.analysis_timeout,
                "average_issues_per_analysis": self.issues_found
                / max(1, self.analyses_performed),
            },
            "uptime": (datetime.now() - self.created_at).total_seconds(),
            "status": "healthy" if self.elder_systems_initialized else "degraded",
        }

        return status


# メイン実行部分（既存のワーカーとの互換性維持）
async def main():
    """ワーカーのメイン実行"""
    config = {
        "circuit_breaker_threshold": 5,
        "circuit_breaker_timeout": 60,
        "analysis_timeout": 30,
    }

    worker = CodeReviewTaskWorker(config)

    print("🚀 CodeReviewTaskWorker started")

    try:
        while True:
            await asyncio.sleep(10)
            print("💓 CodeReview TaskWorker heartbeat")
    except KeyboardInterrupt:
        print("\n🛑 CodeReview TaskWorker stopping...")
        await worker.shutdown()
        print("✅ CodeReview TaskWorker stopped")


if __name__ == "__main__":
    asyncio.run(main())
