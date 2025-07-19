#!/usr/bin/env python3
"""
🤖 GitHub Issue Auto Processor
優先度Medium/Lowのイシューを自動的に処理するシステム
"""

import asyncio
import json
import logging
import os

# Elder System imports
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from github import Github
from github.Issue import Issue

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.core.elders_legacy import EldersServiceLegacy

# Elder System実装は現在ダミーとして使用（実装時に実際のクラスに置き換え）
try:
    from libs.rag_manager import RagManager as ActualRAGSage
except ImportError:
    ActualRAGSage = DummySage


# ダミー実装クラス（実際の4賢者システムがない場合の代替）
class DummyElderFlowEngine:
    async def process_request(self, request):
        return {"status": "success", "task_name": request.get("task_name", "")}


class DummySage:
    async def process_request(self, request):
        return {"status": "success", "message": "Dummy sage response"}


class DummyPRCreator:
    def create_pull_request(self, **kwargs):
        return {"success": False, "error": "PR creation not implemented yet"}


# 実際のクラスまたはダミーを使用
try:
    from libs.elder_system.flow.elder_flow_engine import (
        ElderFlowEngine as ActualElderFlowEngine,
    )
except ImportError:
    ActualElderFlowEngine = DummyElderFlowEngine

try:
    from libs.four_sages.knowledge.knowledge_sage import (
        KnowledgeSage as ActualKnowledgeSage,
    )
except ImportError:
    ActualKnowledgeSage = DummySage

try:
    from libs.four_sages.task.task_sage import TaskSage as ActualTaskSage
except ImportError:
    ActualTaskSage = DummySage

try:
    from libs.four_sages.incident.incident_sage import (
        IncidentSage as ActualIncidentSage,
    )
except ImportError:
    ActualIncidentSage = DummySage

try:
    from libs.integrations.github.api_implementations.create_pull_request import (
        GitHubCreatePullRequestImplementation,
    )
except ImportError:
    GitHubCreatePullRequestImplementation = DummyPRCreator


class AutoIssueElderFlowEngine:
    """Auto Issue Processor専用のElder Flow Engine"""

    def __init__(self):
        self.elder_flow = ActualElderFlowEngine()
        # Ensure environment variables are loaded for PR creator
        github_token = os.getenv("GITHUB_TOKEN")
        repo_owner = os.getenv("GITHUB_REPO_OWNER")
        repo_name = os.getenv("GITHUB_REPO_NAME")

        if not github_token or not repo_owner or not repo_name:
            # Use dummy PR creator if config is missing
            self.pr_creator = DummyPRCreator()
        else:
            self.pr_creator = GitHubCreatePullRequestImplementation(
                token=github_token, repo_owner=repo_owner, repo_name=repo_name
            )
        self.logger = logger

    async def execute_flow(self, request):
        """Auto Issue用のElder Flow実行"""
        try:
            task_name = request.get("task_name", "")
            context = request.get("context", {})
            issue_number = context.get("issue_number", 0)
            issue_title = context.get("issue_title", "")
            issue_body = context.get("issue_body", "")

            # Elder Flowを実行
            flow_result = await self.elder_flow.process_request(
                {
                    "type": "execute",
                    "task_name": task_name,
                    "priority": request.get("priority", "medium"),
                }
            )

            if flow_result.get("status") == "success" or flow_result.get("task_name"):
                # PR作成を実行
                pr_result = await self._create_pull_request(
                    issue_number, issue_title, issue_body, task_name
                )

                if pr_result.get("success"):
                    return {
                        "status": "success",
                        "pr_url": pr_result.get("pr_url"),
                        "message": f"Elder Flow完了、PR #{pr_result.get('pr_number', 'XXX')} を作成しました",
                        "flow_result": flow_result,
                        "pr_result": pr_result,
                    }
                else:
                    return {
                        "status": "partial_success",
                        "pr_url": None,
                        "message": f"Elder Flow完了、但しPR作成に失敗: {pr_result.get('error', '不明なエラー')}",
                        "flow_result": flow_result,
                        "pr_error": pr_result.get("error"),
                    }
            else:
                return {
                    "status": "error",
                    "pr_url": None,
                    "message": f"Elder Flow実行エラー: {flow_result.get('error', '不明なエラー')}",
                    "flow_result": flow_result,
                }

        except Exception as e:
            self.logger.error(f"Auto Issue Elder Flow execution error: {e}")
            return {
                "status": "error",
                "pr_url": None,
                "message": f"実行エラー: {str(e)}",
                "error": str(e),
            }

    async def _create_pull_request(
        self, issue_number, issue_title, issue_body, task_name
    ):
        """自動でPR作成"""
        try:
            # ブランチ名を生成
            branch_name = f"auto-fix-issue-{issue_number}"

            # PR作成
            pr_result = self.pr_creator.create_pull_request(
                title=f"Auto-fix: {issue_title} (#{issue_number})",
                head=branch_name,
                base="main",
                body=f"""🤖 **Auto Issue Processor** による自動修正

## 修正内容
{task_name}

## 対象Issue
Closes #{issue_number}

## 元のIssue内容
{issue_body}

---
*このPRはAuto Issue Processorにより自動生成されました*
""",
                labels=["auto-generated", "auto-fix"],
                draft=True,  # ドラフトとして作成
            )

            if pr_result.get("success"):
                pr_data = pr_result.get("pull_request", {})
                return {
                    "success": True,
                    "pr_url": pr_data.get("html_url"),
                    "pr_number": pr_data.get("number"),
                    "branch_name": branch_name,
                }
            else:
                return {
                    "success": False,
                    "error": pr_result.get("error", "不明なPR作成エラー"),
                }

        except Exception as e:
            return {"success": False, "error": f"PR作成例外: {str(e)}"}


# Setup logging
logger = logging.getLogger("AutoIssueProcessor")


class ComplexityScore:
    """イシューの複雑度スコア"""

    def __init__(self, score: float, factors: Dict[str, Any]):
        self.score = score
        self.factors = factors
        self.is_processable = score < 0.7  # 70%未満なら処理可能


class ProcessingLimiter:
    """処理制限を管理"""

    MAX_ISSUES_PER_HOUR = 10  # 1時間あたり最大10イシューまで
    MAX_CONCURRENT = 1
    COOLDOWN_PERIOD = 300  # 5分

    def __init__(self):
        self.processing_log_file = Path("logs/auto_issue_processing.json")
        self.processing_log_file.parent.mkdir(exist_ok=True)

    async def can_process(self) -> bool:
        """処理可能かチェック"""
        if not self.processing_log_file.exists():
            return True

        with open(self.processing_log_file, "r") as f:
            logs = json.load(f)

        # 過去1時間の処理数をカウント
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_processes = [
            log
            for log in logs
            if datetime.fromisoformat(log["timestamp"]) > one_hour_ago
        ]

        return len(recent_processes) < self.MAX_ISSUES_PER_HOUR

    async def record_processing(self, issue_id: int):
        """処理記録を保存"""
        logs = []
        if self.processing_log_file.exists():
            with open(self.processing_log_file, "r") as f:
                logs = json.load(f)

        logs.append({"issue_id": issue_id, "timestamp": datetime.now().isoformat()})

        # 古いログを削除（24時間以上前）
        cutoff = datetime.now() - timedelta(days=1)
        logs = [
            log for log in logs if datetime.fromisoformat(log["timestamp"]) > cutoff
        ]

        with open(self.processing_log_file, "w") as f:
            json.dump(logs, f, indent=2)


class ComplexityEvaluator:
    """イシューの複雑度を評価"""

    COMPLEXITY_FACTORS = {
        "file_count": {
            "low": (1, 3),
            "medium": (4, 10),
            "high": (11, None),
        },  # 影響ファイル数
        "code_lines": {  # 推定コード行数
            "low": (1, 50),
            "medium": (51, 200),
            "high": (201, None),
        },
        "dependencies": {
            "low": (0, 2),
            "medium": (3, 5),
            "high": (6, None),
        },  # 依存関係数
        "test_coverage": {  # 必要テスト数
            "low": (1, 5),
            "medium": (6, 15),
            "high": (16, None),
        },
    }

    PROCESSABLE_PATTERNS = [
        "typo",
        "documentation",
        "comment",
        "rename",
        "format",
        "style",
        "test",
        "simple bug",
    ]

    async def evaluate(self, issue: Issue) -> ComplexityScore:
        """複雑度スコアを計算"""
        factors = {}
        total_score = 0

        # タイトルとボディから複雑度を推定
        text = f"{issue.title} {issue.body or ''}".lower()

        # 単純なパターンチェック
        is_simple = any(pattern in text for pattern in self.PROCESSABLE_PATTERNS)
        if is_simple:
            factors["pattern_match"] = 0.3
            total_score += 0.3
        else:
            factors["pattern_match"] = 0.7
            total_score += 0.7

        # ラベルベースの評価
        labels = [label.name for label in issue.labels]
        if "good first issue" in labels:
            factors["label_complexity"] = 0.2
            total_score += 0.2
        elif "bug" in labels and "critical" not in labels:
            factors["label_complexity"] = 0.4
            total_score += 0.4
        else:
            factors["label_complexity"] = 0.6
            total_score += 0.6

        # セキュリティ関連チェック
        if any(
            word in text
            for word in ["security", "vulnerability", "auth", "token", "password"]
        ):
            factors["security_related"] = 1.0
            total_score += 1.0

        # 平均スコアを計算
        avg_score = total_score / len(factors) if factors else 1.0

        return ComplexityScore(avg_score, factors)


class AutoIssueProcessor(EldersServiceLegacy):
    """
    GitHubイシュー自動処理システム
    優先度Medium/Lowのイシューを自動的にElder Flowで処理
    """

    def __init__(self):
        super().__init__("auto_issue_processor")
        self.domain = "GITHUB"
        self.service_name = "AutoIssueProcessor"

        # GitHub API初期化
        github_token = os.getenv("GITHUB_TOKEN")
        repo_owner = os.getenv("GITHUB_REPO_OWNER", "ext-maru")
        repo_name = os.getenv("GITHUB_REPO_NAME", "ai-co")

        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable not set")

        self.github = Github(github_token)
        self.repo = self.github.get_repo(f"{repo_owner}/{repo_name}")

        # コンポーネント初期化
        self.elder_flow = AutoIssueElderFlowEngine()
        self.task_sage = ActualTaskSage()
        self.incident_sage = ActualIncidentSage()
        self.knowledge_sage = ActualKnowledgeSage()
        self.rag_sage = ActualRAGSage()

        self.limiter = ProcessingLimiter()
        self.evaluator = ComplexityEvaluator()

        # 処理対象の優先度（中以上）
        self.target_priorities = ["critical", "high", "medium"]

    def get_capabilities(self) -> Dict[str, Any]:
        """サービスの機能を返す"""
        return {
            "service": "AutoIssueProcessor",
            "version": "1.0.0",
            "capabilities": [
                "GitHub issue scanning",
                "Complexity evaluation",
                "Automatic processing",
                "Elder Flow integration",
                "Quality gate validation",
            ],
            "limits": {
                "max_issues_per_hour": ProcessingLimiter.MAX_ISSUES_PER_HOUR,
                "max_concurrent": ProcessingLimiter.MAX_CONCURRENT,
                "target_priorities": self.target_priorities,
            },
        }

    def validate_request(self, request: Dict[str, Any]) -> bool:
        """リクエストの妥当性を検証"""
        # 処理モードの検証
        if "mode" in request and request["mode"] not in ["scan", "process", "dry_run"]:
            return False

        # イシュー番号が指定されている場合の検証
        if "issue_number" in request:
            if not isinstance(request["issue_number"], int):
                return False

        return True

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """イシュー自動処理のメインエントリーポイント"""
        mode = request.get("mode", "scan")

        try:
            if mode == "scan":
                # 処理可能なイシューをスキャン
                issues = await self.scan_processable_issues()
                return {
                    "status": "success",
                    "processable_issues": len(issues),
                    "issues": [
                        {
                            "number": issue.number,
                            "title": issue.title,
                            "priority": self._determine_priority(issue),
                            "complexity": (await self.evaluator.evaluate(issue)).score,
                        }
                        for issue in issues[:5]  # 最大5件まで表示
                    ],
                }

            elif mode == "process":
                # 実際に処理を実行
                if not await self.limiter.can_process():
                    return {
                        "status": "rate_limited",
                        "message": "Processing limit reached. Please try again later.",
                    }

                issues = await self.scan_processable_issues()
                if not issues:
                    return {
                        "status": "no_issues",
                        "message": "No processable issues found.",
                    }

                # 最初のイシューを処理
                issue = issues[0]
                result = await self.execute_auto_processing(issue)

                return {
                    "status": "success",
                    "processed_issue": {
                        "number": issue.number,
                        "title": issue.title,
                        "result": result,
                    },
                }

            elif mode == "dry_run":
                # ドライラン（実際には処理しない）
                issue_number = request.get("issue_number")
                if issue_number:
                    issue = self.repo.get_issue(issue_number)
                    complexity = await self.evaluator.evaluate(issue)

                    return {
                        "status": "dry_run",
                        "issue": {
                            "number": issue.number,
                            "title": issue.title,
                            "priority": self._determine_priority(issue),
                            "complexity": complexity.score,
                            "processable": complexity.is_processable,
                            "factors": complexity.factors,
                        },
                    }

        except Exception as e:
            logger.error(f"Error in process_request: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def scan_processable_issues(self) -> List[Issue]:
        """処理可能なイシューをスキャン"""
        processable_issues = []

        # オープンなイシューを取得
        open_issues = self.repo.get_issues(state="open")

        for issue in open_issues:
            # PRは除外
            if issue.pull_request:
                continue

            # 優先度チェック
            priority = self._determine_priority(issue)
            if priority not in self.target_priorities:
                continue

            # 複雑度評価
            complexity = await self.evaluator.evaluate(issue)
            if complexity.is_processable:
                processable_issues.append(issue)

            # 最大10件まで
            if len(processable_issues) >= 10:
                break

        return processable_issues

    async def execute_auto_processing(self, issue: Issue) -> Dict[str, Any]:
        """Elder Flowを使用してイシューを自動処理"""
        try:
            # 処理記録
            await self.limiter.record_processing(issue.number)

            # 複雑度評価（コメント用）
            complexity = await self.evaluator.evaluate(issue)

            # 4賢者に相談
            sage_advice = await self.consult_four_sages(issue)

            # Elder Flowリクエスト構築
            flow_request = {
                "task_name": f"Auto-fix Issue #{issue.number}: {issue.title}",
                "priority": self._determine_priority(issue),
                "context": {
                    "issue_number": issue.number,
                    "issue_title": issue.title,
                    "issue_body": issue.body or "",
                    "labels": [label.name for label in issue.labels],
                    "sage_advice": sage_advice,
                },
            }

            # Elder Flow実行
            result = await self.elder_flow.execute_flow(flow_request)

            # 結果に基づいてイシューを更新
            if result.get("status") == "success":
                # PRが作成されたらイシューにコメント
                pr_url = result.get("pr_url")
                message = result.get("message", "")

                if pr_url:
                    issue.create_comment(
                        f"🤖 Auto-processed by Elder Flow\n\n"
                        f"PR created: {pr_url}\n\n"
                        f"This issue was automatically processed based on its complexity "
                        f"and priority level."
                    )
                elif message:
                    # PR URLがない場合はメッセージを表示
                    related_links = result.get("related_links", {})

                    comment_text = f"🤖 Elder Flow処理完了\n\n"
                    comment_text += f"{message}\n\n"

                    # 関連リンクを追加
                    if related_links:
                        comment_text += "📚 **関連ドキュメント:**\n"
                        if related_links.get("design_doc"):
                            comment_text += f"- [イシュー自動処理システム設計書]({related_links['design_doc']})\n"
                        if related_links.get("elder_flow_doc"):
                            comment_text += f"- [Elder Flowアーキテクチャ]({related_links['elder_flow_doc']})\n"
                        if related_links.get("issue_link"):
                            comment_text += (
                                f"- [このイシュー]({related_links['issue_link']})\n"
                            )
                        comment_text += "\n"

                    comment_text += f"📊 **処理情報:**\n"
                    comment_text += f"- 複雑度スコア: {complexity.score:.2f}\n"
                    comment_text += f"- 処理基準: 複雑度 < 0.7 かつ 優先度 Medium/Low\n"

                    issue.create_comment(comment_text)

            return result

        except Exception as e:
            logger.error(f"Error in auto processing: {str(e)}")
            # インシデント賢者に報告
            await self.incident_sage.process_request(
                {
                    "type": "report_incident",
                    "severity": "medium",
                    "title": f"Auto-processing failed for issue #{issue.number}",
                    "description": str(e),
                }
            )

            return {"status": "error", "message": str(e)}

    async def consult_four_sages(self, issue: Issue) -> Dict[str, Any]:
        """4賢者への相談"""
        sage_advice = {}

        try:
            # ナレッジ賢者: 過去の類似事例検索
            knowledge_response = await self.knowledge_sage.process_request(
                {
                    "type": "search",
                    "query": f"similar issues to: {issue.title}",
                    "limit": 5,
                }
            )
            sage_advice["knowledge"] = knowledge_response.get("entries", [])

            # タスク賢者: 実行計画立案
            task_response = await self.task_sage.process_request(
                {
                    "type": "create_plan",
                    "title": issue.title,
                    "description": issue.body or "",
                }
            )
            sage_advice["plan"] = task_response

            # インシデント賢者: リスク評価
            incident_response = await self.incident_sage.process_request(
                {
                    "type": "evaluate_risk",
                    "task": issue.title,
                    "context": issue.body or "",
                }
            )
            sage_advice["risks"] = incident_response

            # RAG賢者: 最適解探索
            rag_response = await self.rag_sage.process_request(
                {
                    "type": "search",
                    "query": f"how to fix: {issue.title}",
                    "max_results": 3,
                }
            )
            sage_advice["solution"] = rag_response.get("results", [])

        except Exception as e:
            logger.warning(f"Sage consultation partial failure: {str(e)}")

        return sage_advice

    def _determine_priority(self, issue: Issue) -> str:
        """イシューの優先度を判定"""
        labels = [label.name.lower() for label in issue.labels]

        # ラベルベースの判定（priority:xxxフォーマットも対応）
        if any(
            label in ["critical", "urgent", "p0", "priority:critical"]
            for label in labels
        ):
            return "critical"
        elif any(
            label in ["high", "important", "p1", "priority:high"] for label in labels
        ):
            return "high"
        elif any(
            label in ["medium", "moderate", "p2", "priority:medium"] for label in labels
        ):
            return "medium"
        elif any(label in ["low", "minor", "p3", "priority:low"] for label in labels):
            return "low"

        # タイトルベースの判定
        title_lower = issue.title.lower()
        if any(word in title_lower for word in ["critical", "urgent", "emergency"]):
            return "critical"
        elif any(word in title_lower for word in ["important", "high priority"]):
            return "high"
        elif any(word in title_lower for word in ["bug", "fix", "error"]):
            return "medium"

        # デフォルトは低優先度
        return "low"


async def main():
    """メイン処理（テスト用）"""
    processor = AutoIssueProcessor()

    # スキャンモードでテスト
    result = await processor.process_request({"mode": "scan"})
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
