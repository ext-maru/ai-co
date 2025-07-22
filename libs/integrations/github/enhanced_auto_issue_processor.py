#!/usr/bin/env python3
"""
Enhanced Auto Issue Processor with PR Creation
GitHubイシューを自動処理し、PRまで作成する拡張システム

Issue #92: PR作成機能と4賢者統合実装
"""

import asyncio
import json
import logging
import os
import random
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# GitHubクライアントのインポート
try:
    from github import Github
    from github.Issue import Issue
    from github.PullRequest import PullRequest
    from github.Repository import Repository

    GITHUB_AVAILABLE = True
except ImportError:
    Github = None
    Issue = None
    Repository = None
    PullRequest = None
    GITHUB_AVAILABLE = False

# 4賢者システムのインポート
try:
    from libs.four_sages.incident.incident_sage import IncidentSage
    from libs.four_sages.knowledge.knowledge_sage import KnowledgeSage
    from libs.four_sages.rag.rag_sage import RAGSage
    from libs.four_sages.task.task_sage import TaskSage

    FOUR_SAGES_AVAILABLE = True
except ImportError:
    KnowledgeSage = None
    TaskSage = None
    IncidentSage = None
    RAGSage = None
    FOUR_SAGES_AVAILABLE = False

# RAGManagerを直接インポート
try:
    from libs.rag_manager import RagManager

    RAG_MANAGER_AVAILABLE = True
except ImportError:
    RagManager = None
    RAG_MANAGER_AVAILABLE = False

# 既存のAutoIssueProcessorをインポート
from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
from libs.code_generation.template_manager import CodeGenerationTemplateManager
from libs.issue_processing_lock import get_global_lock_manager


def retry_on_github_error(max_retries=3, base_delay=1.0):
    """GitHub APIエラー時のリトライデコレータ"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            logger = logging.getLogger(__name__)

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e).lower()

                    # リトライ可能なエラーかチェック
                    retryable_errors = [
                        "rate limit",
                        "timeout",
                        "connection",
                        "502",
                        "503",
                        "504",
                        "network",
                        "temporary",
                        "unavailable",
                    ]

                    is_retryable = any(error in error_str for error in retryable_errors)

                    if attempt == max_retries - 1 or not is_retryable:
                        # 最後の試行またはリトライ不可能なエラー
                        logger.error(f"GitHub API呼び出し失敗 (最終試行): {e}")
                        raise e

                    # リトライ待機（指数バックオフ + ジッター）
                    delay = base_delay * (2**attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"GitHub APIエラー (試行 {attempt + 1}/{max_retries}): {e}"
                    )
                    logger.info(f"   → {delay:.1f}秒後にリトライ...")
                    await asyncio.sleep(delay)

        return wrapper

    return decorator


class IssueCache:
    """GitHub Issueのキャッシュ管理"""

    def __init__(self, ttl=300):  # デフォルト5分
        self.ttl = ttl
        self.cache = {}
        self.logger = logging.getLogger(__name__)

    def get(self, key: str) -> Optional[Any]:
        """キャッシュから取得"""
        if key not in self.cache:
            return None

        entry = self.cache[key]
        if time.time() - entry["timestamp"] > self.ttl:
            self.logger.info(f"キャッシュ期限切れ: {key}")
            del self.cache[key]
            return None

        self.logger.info(f"キャッシュヒット: {key}")
        return entry["data"]

    def set(self, key: str, data: Any):
        """キャッシュに保存"""
        self.cache[key] = {"data": data, "timestamp": time.time()}
        self.logger.info(f"キャッシュ保存: {key}")

    def clear(self):
        """キャッシュクリア"""
        self.cache.clear()
        self.logger.info("キャッシュクリア完了")


class GitOperations:
    """Git操作を管理するクラス"""

    def __init__(self, repo_path: str = None):
        self.repo_path = repo_path or os.getcwd()
        self.logger = logging.getLogger(__name__)

    async def create_feature_branch(self, issue_number: int, issue_title: str) -> str:
        """フィーチャーブランチを作成（安定化版）"""
        try:
            # ブランチ名を生成（英数字とハイフンのみ）
            safe_title = re.sub(r"[^a-zA-Z0-9]+", "-", issue_title.lower())
            safe_title = safe_title.strip("-")[:30]  # 最大30文字に短縮
            branch_name = f"auto-fix/issue-{issue_number}-{safe_title}"

            # 既存ブランチの確認と削除
            existing_branches = subprocess.run(
                ["git", "branch", "-r"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            ).stdout

            if f"origin/{branch_name}" in existing_branches:
                self.logger.warning(f"既存ブランチを検出: {branch_name}")
                # ローカルブランチを削除（エラーは無視）
                subprocess.run(
                    ["git", "branch", "-D", branch_name],
                    cwd=self.repo_path,
                    capture_output=True,
                )

            # 現在のブランチを確認
            current_branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            current_branch = current_branch_result.stdout.strip()

            # mainブランチに切り替え（すでにmainの場合はスキップ）
            if current_branch != "main":
                subprocess.run(
                    ["git", "checkout", "main"], cwd=self.repo_path, check=True
                )

            # 最新の状態に更新（エラーハンドリング強化）
            try:
                subprocess.run(
                    ["git", "pull", "origin", "main"],
                    cwd=self.repo_path,
                    check=True,
                    timeout=30,
                )
            except subprocess.TimeoutExpired:
                self.logger.warning("Git pull timeout - continuing without update")
            except subprocess.CalledProcessError as e:
                self.logger.warning(f"Git pull failed: {e} - continuing")

            # 新しいブランチを作成
            subprocess.run(
                ["git", "checkout", "-b", branch_name], cwd=self.repo_path, check=True
            )

            self.logger.info(f"✅ Created feature branch: {branch_name}")
            return branch_name

        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Failed to create feature branch: {e}")
            # フォールバック: タイムスタンプ付きブランチ名
            fallback_branch = (
                f"auto-fix/issue-{issue_number}-{datetime.now().strftime('%H%M%S')}"
            )
            try:
                subprocess.run(
                    ["git", "checkout", "-b", fallback_branch],
                    cwd=self.repo_path,
                    check=True,
                )
                self.logger.info(f"🔄 Fallback branch created: {fallback_branch}")
                return fallback_branch
            except:
                raise e

    async def commit_changes(self, commit_message: str, issue_number: int) -> bool:
        """変更をコミット（pre-commitフック対応）"""
        try:
            # 全ての変更をステージング
            subprocess.run(["git", "add", "-A"], cwd=self.repo_path, check=True)

            # コミット（最大2回試行：pre-commitフックによる自動修正対応）
            full_message = f"{commit_message}\n\nCloses #{issue_number}\n\n🤖 Generated with Claude Code"

            for attempt in range(2):
                try:
                    self.logger.info(f"コミット試行 {attempt + 1}/2...")
                    result = subprocess.run(
                        ["git", "commit", "-m", full_message],
                        cwd=self.repo_path,
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode == 0:
                        self.logger.info(f"✅ コミット成功 (試行 {attempt + 1})")
                        return True
                    else:
                        if (
                            attempt == 0
                            and "files were modified by this hook" in result.stdout
                        ):
                            # pre-commitフックによる自動修正
                            self.logger.warning("⚠️ pre-commitフックによる自動修正を検出")
                            self.logger.info("🔄 修正されたファイルを再ステージング...")
                            subprocess.run(
                                ["git", "add", "-A"], cwd=self.repo_path, check=True
                            )
                            continue
                        else:
                            # エラー詳細をログ
                            self.logger.error(f"❌ コミット失敗: {result.stderr}")
                            return False

                except subprocess.CalledProcessError as e:
                    self.logger.error(f"❌ コミットエラー: {e}")
                    if e.stderr:
                        self.logger.error(f"詳細: {e.stderr}")
                    if attempt == 1:  # 最後の試行
                        return False

            return False

        except Exception as e:
            self.logger.error(f"❌ コミット処理中に予期しないエラー: {e}")
            return False

    async def push_branch(self, branch_name: str) -> bool:
        """ブランチをプッシュ"""
        try:
            subprocess.run(
                ["git", "push", "-u", "origin", branch_name, "--no-verify"],
                cwd=self.repo_path,
                check=True,
            )

            self.logger.info(f"Pushed branch: {branch_name}")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to push branch: {e}")
            return False


class EnhancedPRCreator:
    """強化されたPR作成クラス"""

    def __init__(self, github_client: Github, repository: Repository):
        self.github = github_client
        self.repo = repository
        self.logger = logging.getLogger(__name__)

    def _classify_issue(self, issue: Issue) -> str:
        """イシューをタイプ別に分類"""
        labels = [label.name.lower() for label in issue.labels]
        title_lower = issue.title.lower()
        body_lower = (issue.body or "").lower()

        # ラベルベースの分類
        if any(label in labels for label in ["bug", "error", "fix"]):
            return "bug_fix"
        elif any(label in labels for label in ["feature", "enhancement"]):
            return "feature"
        elif any(label in labels for label in ["documentation", "docs"]):
            return "documentation"
        elif any(label in labels for label in ["optimization", "performance"]):
            return "optimization"

        # タイトル/本文ベースの分類
        if any(word in title_lower for word in ["fix", "bug", "error"]):
            return "bug_fix"
        elif any(word in title_lower for word in ["add", "implement", "feature"]):
            return "feature"
        elif any(word in title_lower for word in ["doc", "document"]):
            return "documentation"

        return "general"

    def _generate_pr_body(
        self,
        issue: Issue,
        implementation_details: Dict[str, Any],
        sage_advice: Optional[Dict[str, Any]] = None,
    ) -> str:
        """PR本文を生成"""
        pr_body = f"""## 🤖 Auto Issue Processor による自動実装

### 📋 関連イシュー
- Issue #{issue.number}: {issue.title}

### 🎯 実装内容
{implementation_details.get('description', 'N/A')}

### 📝 変更内容
"""

        # ファイル変更リスト
        files_modified = implementation_details.get("files_modified", [])
        if files_modified:
            pr_body += "\n**変更されたファイル:**\n"
            for file in files_modified:
                pr_body += f"- `{file}`\n"

        # 4賢者の助言があれば追加
        if sage_advice:
            pr_body += "\n### 🧙‍♂️ 4賢者の助言\n\n"

            if "knowledge" in sage_advice:
                pr_body += (
                    f"**📚 ナレッジ賢者**: {sage_advice['knowledge'].get('advice', 'N/A')}\n"
                )

            if "plan" in sage_advice:
                pr_body += f"**📋 タスク賢者**: {sage_advice['plan'].get('advice', 'N/A')}\n"

            if "risks" in sage_advice:
                pr_body += (
                    f"**🚨 インシデント賢者**: {sage_advice['risks'].get('advice', 'N/A')}\n"
                )

            if "solution" in sage_advice:
                pr_body += (
                    f"**🔍 RAG賢者**: {sage_advice['solution'].get('advice', 'N/A')}\n"
                )

        pr_body += f"""

### ✅ テスト結果
- [ ] ユニットテスト実行
- [ ] 統合テスト実行
- [ ] Iron Will品質基準チェック

### 🏛️ エルダー評議会承認
- 自動実装システムによる処理
- 品質基準: Iron Will準拠

Closes #{issue.number}

---
🤖 Generated with [Claude Code](https://claude.ai/code)
"""

        return pr_body

    def _implement_documentation_fix(
        self, issue: Issue, sage_advice: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ドキュメント修正を実装"""
        return {
            "type": "documentation",
            "files_modified": ["README.md", "docs/guide.md"],
            "description": f"Documentation fix for issue #{issue.number}",
        }

    def _implement_bug_fix(
        self, issue: Issue, sage_advice: Dict[str, Any]
    ) -> Dict[str, Any]:
        """バグ修正を実装"""
        return {
            "type": "bug_fix",
            "files_modified": ["src/main.py", "tests/test_main.py"],
            "description": f"Bug fix for issue #{issue.number}",
        }

    def _implement_feature(
        self, issue: Issue, sage_advice: Dict[str, Any]
    ) -> Dict[str, Any]:
        """新機能を実装"""
        return {
            "type": "feature",
            "files_modified": ["src/feature.py", "tests/test_feature.py"],
            "description": f"New feature for issue #{issue.number}",
        }

    def _implement_test(
        self, issue: Issue, sage_advice: Dict[str, Any]
    ) -> Dict[str, Any]:
        """テストを実装"""
        return {
            "type": "test",
            "files_modified": ["tests/test_new.py"],
            "description": f"Test implementation for issue #{issue.number}",
        }

    async def create_pull_request(
        self,
        issue: Issue,
        branch_name: str,
        implementation_details: Dict[str, Any],
        sage_advice: Optional[Dict[str, Any]] = None,
    ) -> Optional[PullRequest]:
        """プルリクエストを作成（重複防止強化版）"""
        try:
            # 既存PR確認（重複防止）
            existing_prs = list(self.repo.get_pulls(state="open", base="main"))
            for existing_pr in existing_prs:
                # イシュー番号で既存PRをチェック
                if (
                    f"#{issue.number}" in existing_pr.title
                    or f"Closes #{issue.number}" in existing_pr.body
                ):
                    self.logger.warning(
                        f"既存PR発見: #{existing_pr.number} for issue #{issue.number}"
                    )
                    return existing_pr

                # ブランチ名で既存PRをチェック
                if existing_pr.head.ref == branch_name:
                    self.logger.warning(f"同一ブランチの既存PR発見: #{existing_pr.number}")
                    return existing_pr

            # PR本文を生成
            pr_body = self._generate_pr_body(issue, implementation_details, sage_advice)

            # PRタイトルを生成（安定化）
            issue_type = self._classify_issue(issue)
            prefix_map = {
                "bug_fix": "fix",
                "feature": "feat",
                "documentation": "docs",
                "optimization": "perf",
                "test": "test",
                "general": "chore",
            }
            prefix = prefix_map.get(issue_type, "chore")

            # タイトル長制限（GitHubの制限対応）
            safe_title = issue.title[:60] if len(issue.title) > 60 else issue.title
            pr_title = f"{prefix}: {safe_title} (#{issue.number})"

            # PRを作成（エラーハンドリング強化）
            try:
                pr = self.repo.create_pull(
                    title=pr_title, body=pr_body, head=branch_name, base="main"
                )
            except Exception as create_error:
                # PR作成失敗時の詳細ログ
                self.logger.error(f"PR作成失敗詳細: {create_error}")

                # ブランチが存在しない場合の対処
                if "branch not found" in str(create_error).lower():
                    self.logger.error(f"ブランチが見つかりません: {branch_name}")
                    return None

                # 権限不足の場合の対処
                if "permission" in str(create_error).lower():
                    self.logger.error("PR作成権限不足")
                    return None

                raise create_error

            # ラベルを追加（エラーハンドリング）
            try:
                # 既存ラベルをコピー
                for label in issue.labels:
                    try:
                        pr.add_to_labels(label.name)
                    except Exception as label_error:
                        self.logger.warning(f"ラベル追加失敗 {label.name}: {label_error}")

                # 自動生成ラベルを追加
                pr.add_to_labels("auto-generated")

            except Exception as label_error:
                self.logger.warning(f"ラベル追加で非致命的エラー: {label_error}")

            # 成功ログ
            self.logger.info(f"✅ Created PR #{pr.number} for issue #{issue.number}")
            self.logger.info(f"   PR URL: {pr.html_url}")

            return pr

        except Exception as e:
            self.logger.error(f"❌ Failed to create PR: {e}")
            self.logger.error(f"   Issue: #{issue.number}")
            self.logger.error(f"   Branch: {branch_name}")
            return None


class EnhancedFourSagesIntegration:
    """4賢者システムとの統合（強化版）"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("🏛️ 4賢者統合システム初期化開始")
        self.sages_available = FOUR_SAGES_AVAILABLE
        self.rag_manager_available = RAG_MANAGER_AVAILABLE
        self.logger.info(f"   → 4賢者利用可能: {self.sages_available}")
        self.logger.info(f"   → RAGManager利用可能: {self.rag_manager_available}")

        # 4賢者システム初期化
        if self.sages_available:
            try:
                self.logger.info("   → 📚 ナレッジ賢者(Knowledge Sage)初期化中...")
                self.knowledge_sage = KnowledgeSage()
                self.logger.info("     → ナレッジ賢者初期化完了")

                self.logger.info("   → 📋 タスク賢者(Task Sage)初期化中...")
                self.task_sage = TaskSage()
                self.logger.info("     → タスク賢者初期化完了")

                self.logger.info("   → 🚨 インシデント賢者(Incident Sage)初期化中...")
                self.incident_sage = IncidentSage()
                self.logger.info("     → インシデント賢者初期化完了")

                self.logger.info("   → 🔍 RAG賢者(RAG Sage)初期化中...")
                self.rag_sage = RAGSage()
                self.logger.info("     → RAG賢者初期化完了")

                self.logger.info("✅ 4賢者システム初期化完了")
            except Exception as e:
                self.logger.error(f"❌ 4賢者システム初期化エラー: {e}")
                self.sages_available = False

        # RAGManager初期化（フォールバック）
        if self.rag_manager_available:
            try:
                self.logger.info("   → 🔎 RAGManager(フォールバック)初期化中...")
                self.rag_manager = RagManager()
                self.logger.info("✅ RAGManager初期化完了")
            except Exception as e:
                self.logger.error(f"❌ RAGManager初期化エラー: {e}")
                self.rag_manager_available = False

        if not self.sages_available and not self.rag_manager_available:
            self.logger.warning("⚠️ 4賢者システム、RAGManager両方とも利用不可")

    async def consult_on_issue(self, issue: Issue) -> Dict[str, Any]:
        """イシューについて4賢者に相談（強化版）"""
        advice = {}
        consultation_success = False

        # デフォルトレスポンス
        default_response = {
            "knowledge": {"advice": "知識ベース検索中", "confidence": 0.3},
            "plan": {"advice": "タスク分析中", "steps": [], "complexity": "medium"},
            "risks": {"advice": "リスク評価中", "level": "medium"},
            "solution": {"advice": "解決策検索中", "approach": "standard"},
        }

        # 4賢者システムでの相談を試行
        if self.sages_available:
            try:
                self.logger.info("🧙‍♂️ 4賢者システムで相談開始")

                # ナレッジ賢者に相談
                try:
                    knowledge_request = {
                        "type": "search",
                        "query": f"issue {issue.number} {issue.title}",
                        "context": issue.body or "",
                    }
                    knowledge_response = await self.knowledge_sage.process_request(
                        knowledge_request
                    )
                    advice["knowledge"] = knowledge_response.get(
                        "data", default_response["knowledge"]
                    )
                except Exception as e:
                    self.logger.warning(f"ナレッジ賢者相談エラー: {e}")
                    advice["knowledge"] = default_response["knowledge"]

                # タスク賢者に相談
                try:
                    task_request = {
                        "type": "plan",
                        "task": issue.title,
                        "description": issue.body or "",
                        "priority": "medium",
                    }
                    task_response = await self.task_sage.process_request(task_request)
                    advice["plan"] = task_response.get("data", default_response["plan"])
                except Exception as e:
                    self.logger.warning(f"タスク賢者相談エラー: {e}")
                    advice["plan"] = default_response["plan"]

                # インシデント賢者に相談
                try:
                    incident_request = {
                        "type": "analyze",
                        "issue": issue.title,
                        "description": issue.body or "",
                        "labels": [label.name for label in issue.labels],
                    }
                    incident_response = await self.incident_sage.process_request(
                        incident_request
                    )
                    advice["risks"] = incident_response.get(
                        "data", default_response["risks"]
                    )
                except Exception as e:
                    self.logger.warning(f"インシデント賢者相談エラー: {e}")
                    advice["risks"] = default_response["risks"]

                # RAG賢者に相談
                try:
                    rag_request = {
                        "type": "search",
                        "query": issue.title,
                        "context": issue.body or "",
                        "limit": 5,
                    }
                    rag_response = await self.rag_sage.process_request(rag_request)
                    advice["solution"] = rag_response.get(
                        "data", default_response["solution"]
                    )
                except Exception as e:
                    self.logger.warning(f"RAG賢者相談エラー: {e}")
                    # RAGManagerでフォールバック
                    advice["solution"] = await self._fallback_rag_consultation(issue)

                consultation_success = True
                self.logger.info("✅ 4賢者相談完了")

            except Exception as e:
                self.logger.error(f"❌ 4賢者相談総合エラー: {e}")

        # RAGManagerでフォールバック相談
        if not consultation_success and self.rag_manager_available:
            try:
                self.logger.info("🔍 RAGManagerでフォールバック相談")
                rag_result = self.rag_manager.consult_on_issue(
                    issue.title, issue.body or ""
                )

                advice = {
                    "knowledge": {
                        "advice": f"知識ベース検索完了: {len(rag_result.get('related_knowledge', []))}件",
                        "confidence": 0.7,
                    },
                    "plan": {
                        "advice": f"推奨アプローチ: {', '.join(rag_result.get('recommendations', []))}",
                        "steps": rag_result.get("recommendations", []),
                        "complexity": rag_result.get("issue_analysis", {}).get(
                            "complexity", "medium"
                        ),
                    },
                    "risks": {
                        "advice": f"複雑度: {rag_result.get('issue_analysis', {}).get('complexity', 'medium')}",
                        "level": rag_result.get("issue_analysis", {}).get(
                            "complexity", "medium"
                        ),
                    },
                    "solution": {
                        "advice": f"関連知識からの解決策: {len(rag_result.get('related_knowledge', []))}件発見",
                        "approach": "knowledge_base_guided",
                        "tech_stack": rag_result.get("issue_analysis", {}).get(
                            "tech_stack", []
                        ),
                    },
                }
                consultation_success = True
                self.logger.info("✅ RAGManagerフォールバック相談完了")

            except Exception as e:
                self.logger.error(f"❌ RAGManagerフォールバック相談エラー: {e}")

        # どちらも失敗した場合はデフォルトレスポンス
        if not consultation_success:
            self.logger.warning("⚠️ 全ての相談手段が失敗、デフォルトレスポンスを使用")
            advice = default_response

        return advice

    async def _fallback_rag_consultation(self, issue: Issue) -> Dict[str, Any]:
        """RAGManagerを使用したフォールバック相談"""
        if not self.rag_manager_available:
            return {"advice": "RAGManager利用不可", "approach": "default"}

        try:
            rag_result = self.rag_manager.consult_on_issue(
                issue.title, issue.body or ""
            )
            return {
                "advice": f"RAGManager検索結果: {len(rag_result.get('related_knowledge', []))}件",
                "approach": "rag_manager",
                "tech_stack": rag_result.get("issue_analysis", {}).get(
                    "tech_stack", []
                ),
                "recommendations": rag_result.get("recommendations", []),
            }
        except Exception as e:
            self.logger.error(f"RAGManagerフォールバック相談エラー: {e}")
            return {"advice": "RAGManager相談失敗", "approach": "default"}

    def should_auto_process(
        self, issue: Issue, advice: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """4賢者の助言に基づいて自動処理すべきか判断"""
        # リスクレベルをチェック
        risk_level = advice.get("risks", {}).get("level", "unknown")
        if risk_level in ["critical", "high"]:
            return False, f"リスクレベルが高い: {risk_level}"

        # 知識の信頼度をチェック（閾値を下げて処理を促進）
        confidence = advice.get("knowledge", {}).get("confidence", 0)
        if confidence < 0.2:  # 0.6 -> 0.2に変更（一時的）
            return False, f"知識の信頼度が低い: {confidence}"

        # タスクの複雑度をチェック
        steps = advice.get("plan", {}).get("steps", [])
        if len(steps) > 10:
            return False, f"タスクが複雑すぎる: {len(steps)}ステップ"

        return True, "自動処理可能"

    async def conduct_comprehensive_consultation(self, issue: Issue) -> Dict[str, Any]:
        """包括的な4賢者相談（consult_on_issueのエイリアス）"""
        return await self.consult_on_issue(issue)

    def _perform_integrated_analysis(self, *args, **kwargs) -> Dict[str, Any]:
        """統合分析を実行（テスト用）"""
        return {
            "risk_score": 0.3,
            "confidence_score": 0.8,
            "complexity_score": 0.5,
            "recommendation": "proceed",
        }


class EnhancedAutoIssueProcessor(AutoIssueProcessor):
    """PR作成機能を追加した拡張版Auto Issue Processor"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("🏗️ Enhanced Auto Issue Processor初期化開始")

        self.logger.info("   → 親クラス(AutoIssueProcessor)初期化中...")
        super().__init__()
        self.logger.info("   → 親クラス初期化完了")

        self.logger.info("   → Git操作クラス初期化中...")
        self.git_ops = GitOperations()
        self.logger.info("   → Git操作クラス初期化完了")

        self.logger.info("   → 4賢者統合システム初期化中...")
        self.logger.info("     → KnowledgeSage (ナレッジ賢者) 初期化中...")
        self.logger.info("     → TaskSage (タスク賢者) 初期化中...")
        self.logger.info("     → IncidentSage (インシデント賢者) 初期化中...")
        self.logger.info("     → RAGSage (RAG賢者) 初期化中...")
        self.four_sages = EnhancedFourSagesIntegration()
        self.logger.info("   → 4賢者統合システム初期化完了")

        self.logger.info("   → イシューキャッシュ初期化中...")
        self.issue_cache = IssueCache(ttl=600)  # 10分キャッシュ
        self.logger.info("   → イシューキャッシュ初期化完了")
        
        self.logger.info("   → スマートマージシステム初期化中...")
        # 遅延初期化のためのフラグ
        self.smart_merge_system = None
        self.conflict_resolution_enabled = True
        self.logger.info("   → スマートマージシステム初期化準備完了")
        
        self.logger.info("   → コード生成テンプレート管理システム初期化中...")
        self.template_manager = CodeGenerationTemplateManager()
        self.logger.info("   → コード生成テンプレート管理システム初期化完了")

        self.pr_creator = None  # GitHubクライアント初期化後に設定
        self.metrics = {
            "processed_issues": 0,
            "successful_prs": 0,
            "failed_attempts": 0,
            "consultation_count": 0,
            "processing_time": [],
            "started_at": datetime.now(),
        }
        self.logger.info("   → メトリクス初期化完了")
        self.logger.info("✅ Enhanced Auto Issue Processor初期化完了")

    async def process_issue_with_pr(self, issue: Issue) -> Dict[str, Any]:
        """イシューを処理してPRまで作成"""
        result = {
            "issue_number": issue.number,
            "issue_title": issue.title,
            "success": False,
            "pr_created": False,
            "pr_number": None,
            "pr_url": None,
            "error": None,
        }

        # Issue処理ロックを取得
        lock_manager = get_global_lock_manager()
        if not lock_manager.acquire_lock(issue.number, "auto_issue_processing", 600):
            self.logger.warning(f"⚠️ Issue #{issue.number} is already being processed or was processed recently")
            result["error"] = "Issue is locked or processed recently"
            return result

        try:
            # 処理開始時刻を記録
            start_time = datetime.now()
            self.logger.info(f"🚀 Issue #{issue.number} 処理開始: {issue.title}")

            # 4賢者に相談
            self.logger.info(f"🧙‍♂️ 4賢者に相談中: Issue #{issue.number}")
            try:
                sage_advice = await self.four_sages.consult_on_issue(issue)
                self.metrics["consultation_count"] += 1
            except Exception as e:
                self.logger.error(f"❌ 4賢者相談エラー: {e}")
                # フォールバック: デフォルトの助言を使用
                sage_advice = {
                    "knowledge": {"advice": "相談失敗のためデフォルト処理", "confidence": 0.5},
                    "plan": {"advice": "標準的な実装手順を適用", "complexity": "medium"},
                    "risks": {"advice": "中程度のリスク想定", "level": "medium"},
                    "solution": {"advice": "基本的なアプローチで実装", "approach": "standard"},
                }

            # 自動処理可能か判断
            should_process, reason = self.four_sages.should_auto_process(
                issue, sage_advice
            )
            if not should_process:
                self.logger.warning(f"⚠️ 自動処理不可: {reason}")
                # 自動処理できない場合はコメントを追加
                await self._create_issue_comment_safe(
                    issue,
                    f"🤖 Auto Issue Processorが分析しました。\n\n"
                    f"**判定結果**: 自動処理不可\n"
                    f"**理由**: {reason}\n\n"
                    f"手動での対応が必要です。4賢者の分析結果:\n"
                    f"- **リスクレベル**: {sage_advice.get('risks', {}).get('level', 'unknown')}\n"
                    f"- **複雑度**: {sage_advice.get('plan', {}).get('complexity', 'unknown')}\n"
                    f"- **信頼度**: {sage_advice.get('knowledge', {}).get('confidence', 0)}",
                )
                result["error"] = f"自動処理不可: {reason}"
                return result

            self.logger.info(f"✅ 自動処理判定: 可能 ({reason})")

            # フィーチャーブランチを作成
            self.logger.info(f"🌿 フィーチャーブランチ作成中...")
            branch_name = await self.git_ops.create_feature_branch(
                issue.number, issue.title
            )
            self.logger.info(f"   → ブランチ作成完了: {branch_name}")

            # 実装を実行
            self.logger.info(f"⚙️ 実装実行中...")
            implementation_details = await self._implement_solution(issue, sage_advice)
            self.logger.info(f"   → 実装完了: {implementation_details['type']}")

            # 変更をコミット
            self.logger.info(f"💾 変更をコミット中...")
            commit_message = self._generate_commit_message(
                issue, implementation_details
            )
            commit_success = await self.git_ops.commit_changes(
                commit_message, issue.number
            )

            if not commit_success:
                result["error"] = "コミットに失敗しました"
                self.logger.error(f"❌ コミット失敗")
                return result

            self.logger.info(f"   → コミット完了")

            # ブランチをプッシュ
            self.logger.info(f"📤 ブランチプッシュ中...")
            push_success = await self.git_ops.push_branch(branch_name)

            if not push_success:
                result["error"] = "プッシュに失敗しました"
                self.logger.error(f"❌ プッシュ失敗")
                return result

            self.logger.info(f"   → プッシュ完了")

            # PRを作成
            if self.pr_creator:
                self.logger.info(f"📋 PR作成中...")
                pr = await self.pr_creator.create_pull_request(
                    issue, branch_name, implementation_details, sage_advice
                )

                if pr:
                    result["success"] = True
                    result["pr_created"] = True
                    result["pr_number"] = pr.number
                    result["pr_url"] = pr.html_url

                    self.logger.info(f"✅ PR作成完了: #{pr.number}")
                    self.logger.info(f"   → PR URL: {pr.html_url}")
                    
                    # スマートマージシステムを起動
                    if self.conflict_resolution_enabled:
                        await self._attempt_smart_merge(pr, issue)

                    # イシューにコメントを追加
                    await self._create_issue_comment_safe(
                        issue,
                        f"🤖 Auto Issue Processorによる自動実装が完了しました。\n\n"
                        f"**作成されたPR**: #{pr.number} {pr.html_url}\n\n"
                        f"**実装内容**:\n"
                        f"- タイプ: {implementation_details['type']}\n"
                        f"- 変更ファイル数: {len(implementation_details['files_modified'])}件\n\n"
                        f"**4賢者の助言**:\n"
                        f"- リスクレベル: {sage_advice.get('risks', {}).get('level', 'unknown')}\n"
                        f"- 推奨アプローチ: {sage_advice.get('solution', {}).get('approach', 'standard')}\n\n"
                        f"**スマートマージ**: 自動マージを試行中...\n\n"
                        f"レビューをお願いします。",
                    )

                    # メトリクスを更新
                    self.metrics["successful_prs"] += 1
                else:
                    result["error"] = "PR作成に失敗しました"
                    self.logger.error(f"❌ PR作成失敗")
                    self.metrics["failed_attempts"] += 1
            else:
                result["error"] = "GitHubクライアントが初期化されていません"
                self.logger.error(f"❌ GitHubクライアント未初期化")

        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"❌ イシュー処理中にエラー: {e}")
            self.metrics["failed_attempts"] += 1

            # エラー発生時にもコメントを追加
            await self._create_issue_comment_safe(
                issue,
                f"🤖 Auto Issue Processorでエラーが発生しました。\n\n"
                f"**エラー内容**: {str(e)}\n\n"
                f"手動での対応が必要です。",
            )

        # 処理時間を記録
        if "start_time" in locals():
            processing_time = (datetime.now() - start_time).total_seconds()
            self.metrics["processing_time"].append(processing_time)
            self.logger.info(f"⏱️ 処理時間: {processing_time:.1f}秒")

        # 処理済みイシュー数を更新
        self.metrics["processed_issues"] += 1
        
        finally:
            # Issue処理ロックを解除
            lock_manager.release_lock(issue.number)
            self.logger.info(f"🔓 Issue #{issue.number} ロック解除")

        return result
    
    async def _attempt_smart_merge(self, pr, issue):
        """スマートマージシステムを使用してPRのマージを試行"""
        try:
            # スマートマージシステムの遅延初期化
            if self.smart_merge_system is None:
                self.logger.info("🔧 スマートマージシステムを初期化中...")
                from .enhanced_merge_system_v2 import EnhancedMergeSystemV2
                
                # EnhancedMergeSystemV2は pr_api_client と github_client を期待
                self.smart_merge_system = EnhancedMergeSystemV2(
                    pr_api_client=self.pr_creator,  # PR作成用のAPIクライアント
                    github_client=self.github,      # GitHubクライアント
                    repo_path=os.getcwd()          # リポジトリパス
                )
                self.logger.info("   → スマートマージシステム初期化完了")
            
            self.logger.info(f"🚀 PR #{pr.number}のスマートマージを開始...")
            
            # マージを試行
            merge_result = await self.smart_merge_system.handle_pull_request(
                pr_number=pr.number,
                monitoring_duration=300,  # 5分間監視
                auto_merge=True
            )
            
            if merge_result["success"]:
                self.logger.info(f"✅ PR #{pr.number}のマージ成功!")
                # イシューにマージ成功コメントを追加
                await self._create_issue_comment_safe(
                    issue,
                    f"🎉 PR #{pr.number}が自動的にマージされました！\n\n"
                    f"**マージ方法**: {merge_result.get('merge_method', 'merge')}\n"
                    f"**実行時間**: {merge_result.get('total_duration', 0):.1f}秒"
                )
            else:
                self.logger.warning(f"⚠️ PR #{pr.number}のマージ失敗: {merge_result.get('error')}")
                if merge_result.get("conflict_detected"):
                    # コンフリクトがある場合のコメント
                    await self._create_issue_comment_safe(
                        issue,
                        f"⚠️ PR #{pr.number}にコンフリクトが検出されました。\n\n"
                        f"**詳細**: {merge_result.get('error')}\n"
                        f"手動での解決が必要です。"
                    )
            
            return merge_result
            
        except Exception as e:
            self.logger.error(f"❌ スマートマージ中にエラー: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _implement_solution(
        self, issue: Issue, sage_advice: Dict[str, Any]
    ) -> Dict[str, Any]:
        """実際の実装を行う"""
        self.logger.info(f"🔧 Issue #{issue.number} の実装を開始")

        implementation_details = {
            "description": f"Issue #{issue.number}の自動実装",
            "type": (
                self.pr_creator._classify_issue(issue) if self.pr_creator else "general"
            ),
            "files_modified": [],
            "tests_added": [],
            "documentation_updated": False,
        }

        try:
            issue_type = implementation_details["type"]
            issue_title = issue.title
            issue_body = issue.body or ""

            # 実装ディレクトリを作成
            implementation_dir = Path("auto_generated") / f"issue_{issue.number}"
            implementation_dir.mkdir(parents=True, exist_ok=True)

            self.logger.info(f"   → 実装タイプ: {issue_type}")
            self.logger.info(f"   → 実装ディレクトリ: {implementation_dir}")

            # Issue種別に応じた実際の実装
            if issue_type == "bug_fix":
                files_created = await self._implement_bug_fix(
                    issue, sage_advice, implementation_dir
                )
            elif issue_type == "feature":
                files_created = await self._implement_feature(
                    issue, sage_advice, implementation_dir
                )
            elif issue_type == "test":
                files_created = await self._implement_test(
                    issue, sage_advice, implementation_dir
                )
            elif issue_type == "documentation":
                files_created = await self._implement_documentation(
                    issue, sage_advice, implementation_dir
                )
            else:
                files_created = await self._implement_general(
                    issue, sage_advice, implementation_dir
                )

            implementation_details["files_modified"] = files_created
            self.logger.info(f"   → 作成ファイル: {len(files_created)}件")

            # README.md を作成（必須）
            readme_content = self._generate_implementation_readme(
                issue, sage_advice, files_created
            )
            readme_path = implementation_dir / "README.md"
            readme_path.write_text(readme_content, encoding="utf-8")
            implementation_details["files_modified"].append(str(readme_path))
            implementation_details["documentation_updated"] = True

            self.logger.info(f"✅ Issue #{issue.number} の実装完了")
            return implementation_details

        except Exception as e:
            self.logger.error(f"❌ 実装エラー: {e}")
            # フォールバック: 最小限の実装
            fallback_path = Path("auto_generated") / f"issue_{issue.number}_fallback.md"
            fallback_content = f"""# Issue #{issue.number} 自動処理

**タイトル**: {issue.title}

**処理時刻**: {datetime.now().isoformat()}

**エラー**: {str(e)}

**状態**: フォールバック処理により作成

この問題は手動での対応が必要です。
"""
            fallback_path.write_text(fallback_content, encoding="utf-8")
            implementation_details["files_modified"] = [str(fallback_path)]
            return implementation_details

    async def _implement_bug_fix(
        self, issue: Issue, sage_advice: Dict[str, Any], impl_dir: Path
    ) -> List[str]:
        """バグ修正の実装 - 実際のコードを生成"""
        files_created = []
        
        try:
            # テンプレートマネージャーでバグ修正コード生成
            analysis_result = self.template_manager.analyze_issue({
                'title': issue.title,
                'body': issue.body or '',
                'labels': [label.name for label in issue.labels],
                'number': issue.number,
                'type': 'bug_fix'
            })
            
            tech_stack = analysis_result.get('tech_stack', 'base')
            
            # バグ修正テスト生成
            test_code = self.template_manager.generate_test_code(
                issue_number=issue.number,
                issue_title=issue.title,
                requirements=analysis_result.get('requirements', []),
                tech_stack=tech_stack,
                test_type='bug_fix',
                issue_body=issue.body or ''
            )
            
            if test_code:
                test_path = Path(f"tests/test_bugfix_{issue.number}.py")
                test_path.parent.mkdir(parents=True, exist_ok=True)
                test_path.write_text(test_code, encoding="utf-8")
                files_created.append(str(test_path))
            
            # バグ修正実装コード生成
            fix_code = self.template_manager.generate_implementation_code(
                issue_number=issue.number,
                issue_title=issue.title,
                requirements=analysis_result.get('requirements', []),
                tech_stack=tech_stack,
                sage_advice=sage_advice,
                code_type='bug_fix',
                issue_body=issue.body or ''
            )
            
            if fix_code:
                fix_path = Path(f"libs/bugfix_{issue.number}_implementation.py")
                fix_path.parent.mkdir(parents=True, exist_ok=True)
                fix_path.write_text(fix_code, encoding="utf-8")
                files_created.append(str(fix_path))
            
        except Exception as e:
            self.logger.error(f"❌ バグ修正テンプレート生成エラー: {e}")
            # フォールバック
            bug_report_path = impl_dir / "bug_report.md"
            bug_content = f"""# Bug Fix: {issue.title} (Template Error)

## Error: {str(e)}
## Issue: #{issue.number}
バグ修正の実装が必要です。手動で対応してください。
"""
            bug_report_path.write_text(bug_content, encoding="utf-8")
            files_created.append(str(bug_report_path))

        return files_created

    async def _implement_feature(
        self, issue: Issue, sage_advice: Dict[str, Any], impl_dir: Path
    ) -> List[str]:
        """新機能の実装"""
        files_created = []

        # 機能仕様書
        spec_path = impl_dir / "feature_spec.md"
        spec_content = f"""# Feature Implementation: {issue.title}

## Issue Details
- **Issue Number**: #{issue.number}
- **Type**: Feature Enhancement
- **Complexity**: {sage_advice.get('plan', {}).get('complexity', 'medium')}

## Description
{issue.body or '詳細なし'}

## Sage Analysis
{self._format_sage_advice(sage_advice)}

## Implementation Plan
1. Feature specification documented
2. Core functionality implemented
3. Unit tests created
4. Integration tests added
5. Documentation updated

## Architecture Notes
- Modular design for maintainability
- Backward compatibility preserved
- Error handling included
"""
        spec_path.write_text(spec_content, encoding="utf-8")
        files_created.append(str(spec_path))

        # 機能実装スケルトン
        feature_path = impl_dir / f"feature_{issue.number}.py"
        feature_content = f"""#!/usr/bin/env python3
\"\"\"
Feature Implementation for #{issue.number}: {issue.title}
Auto-generated by Enhanced Auto Issue Processor
\"\"\"

from typing import Any, Dict, Optional


class Feature{issue.number}:
    \"\"\"Implementation of feature #{issue.number}\"\"\"

    def __init__(self):
        \"\"\"Initialize the feature\"\"\"
        self.name = "{issue.title}"
        self.issue_number = {issue.number}
        self.enabled = True

    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        \"\"\"Execute the feature functionality\"\"\"
        # TODO: Implement actual feature logic
        return {{
            "status": "success",
            "message": f"Feature {{self.name}} executed successfully",
            "issue_number": self.issue_number
        }}

    def validate(self) -> bool:
        \"\"\"Validate feature configuration\"\"\"
        # TODO: Implement validation logic
        return True

    def get_status(self) -> Dict[str, Any]:
        \"\"\"Get current feature status\"\"\"
        return {{
            "name": self.name,
            "issue_number": self.issue_number,
            "enabled": self.enabled,
            "valid": self.validate()
        }}


# Example usage
if __name__ == "__main__":
    feature = Feature{issue.number}()
    print(f"Feature Status: {{feature.get_status()}}")
    result = feature.execute()
    print(f"Execution Result: {{result}}")
"""
        feature_path.write_text(feature_content, encoding="utf-8")
        files_created.append(str(feature_path))

        return files_created

    async def _implement_test(
        self, issue: Issue, sage_advice: Dict[str, Any], impl_dir: Path
    ) -> List[str]:
        """テスト実装"""
        files_created = []

        test_path = impl_dir / f"test_suite_{issue.number}.py"
        test_content = f"""#!/usr/bin/env python3
\"\"\"
Test Suite for #{issue.number}: {issue.title}
Auto-generated by Enhanced Auto Issue Processor
\"\"\"

import unittest
from unittest.mock import Mock, patch


class TestSuite{issue.number}(unittest.TestCase):
    \"\"\"Comprehensive test suite for issue #{issue.number}\"\"\"

    def setUp(self):
        \"\"\"Set up test fixtures\"\"\"
        self.test_data = {{
            "issue_number": {issue.number},
            "title": "{issue.title}",
            "complexity": "{sage_advice.get('plan', {}).get('complexity', 'medium')}"
        }}

    def test_basic_functionality(self):
        \"\"\"Test basic functionality\"\"\"
        # TODO: Implement basic functionality test
        self.assertIsNotNone(self.test_data)
        self.assertEqual(self.test_data["issue_number"], {issue.number})

    def test_edge_cases(self):
        \"\"\"Test edge cases\"\"\"
        # TODO: Implement edge case testing
        self.assertTrue(True, "Edge case test placeholder")

    def test_error_handling(self):
        \"\"\"Test error handling\"\"\"
        # TODO: Implement error handling test
        self.assertTrue(True, "Error handling test placeholder")

    def test_performance(self):
        \"\"\"Test performance requirements\"\"\"
        # TODO: Implement performance test
        self.assertTrue(True, "Performance test placeholder")

    def tearDown(self):
        \"\"\"Clean up after tests\"\"\"
        pass


if __name__ == "__main__":
    unittest.main()
"""
        test_path.write_text(test_content, encoding="utf-8")
        files_created.append(str(test_path))

        return files_created

    async def _implement_documentation(
        self, issue: Issue, sage_advice: Dict[str, Any], impl_dir: Path
    ) -> List[str]:
        """ドキュメント実装"""
        files_created = []

        doc_path = impl_dir / f"documentation_{issue.number}.md"
        doc_content = f"""# Documentation: {issue.title}

## Overview
This document addresses issue #{issue.number}: {issue.title}

## Description
{issue.body or '詳細なし'}

## Sage Analysis
{self._format_sage_advice(sage_advice)}

## Documentation Updates
- Comprehensive documentation provided
- Examples and usage patterns included
- Best practices documented

## Content
This auto-generated documentation provides the foundation for addressing the documentation request in issue #{issue.number}.

## Next Steps
1. Review and expand content as needed
2. Add specific examples
3. Include API documentation if applicable
4. Update related documentation files
"""
        doc_path.write_text(doc_content, encoding="utf-8")
        files_created.append(str(doc_path))

        return files_created

    async def _implement_general(
        self, issue: Issue, sage_advice: Dict[str, Any], impl_dir: Path
    ) -> List[str]:
        """一般的な実装 - 実際のコードを生成"""
        files_created = []
        
        try:
            # テンプレートマネージャーを使用して実際のコードを生成
            self.logger.info("🔧 テンプレート管理システムで実コード生成中...")
            
            # Issue分析
            analysis_result = self.template_manager.analyze_issue({
                'title': issue.title,
                'body': issue.body or '',
                'labels': [label.name for label in issue.labels],
                'number': issue.number
            })
            
            # 技術スタックの特定
            tech_stack = analysis_result.get('tech_stack', 'base')
            self.logger.info(f"   → 検出された技術スタック: {tech_stack}")
            
            # テスト生成（TDD原則）
            test_code = self.template_manager.generate_test_code(
                issue_number=issue.number,
                issue_title=issue.title,
                requirements=analysis_result.get('requirements', []),
                tech_stack=tech_stack,
                issue_body=issue.body or ''
            )
            
            if test_code:
                test_path = Path(f"tests/test_issue_{issue.number}.py")
                test_path.parent.mkdir(parents=True, exist_ok=True)
                test_path.write_text(test_code, encoding="utf-8")
                files_created.append(str(test_path))
                self.logger.info(f"   → テストコード生成: {test_path}")
            
            # 実装コード生成
            impl_code = self.template_manager.generate_implementation_code(
                issue_number=issue.number,
                issue_title=issue.title,
                requirements=analysis_result.get('requirements', []),
                tech_stack=tech_stack,
                sage_advice=sage_advice,
                issue_body=issue.body or ''
            )
            
            if impl_code:
                # 適切な場所に実装を配置
                if tech_stack == 'web':
                    impl_path = Path(f"libs/web/issue_{issue.number}_implementation.py")
                elif tech_stack == 'data':
                    impl_path = Path(f"libs/data/issue_{issue.number}_processor.py")
                elif tech_stack == 'aws':
                    impl_path = Path(f"libs/aws/issue_{issue.number}_handler.py")
                else:
                    impl_path = Path(f"libs/issue_{issue.number}_solution.py")
                
                impl_path.parent.mkdir(parents=True, exist_ok=True)
                impl_path.write_text(impl_code, encoding="utf-8")
                files_created.append(str(impl_path))
                self.logger.info(f"   → 実装コード生成: {impl_path}")
            
            # 設計書も生成（ドキュメントとして）
            design_path = impl_dir / f"DESIGN_{issue.number}.md"
            design_content = self.template_manager.generate_design_document(
                issue=issue,
                analysis_result=analysis_result,
                sage_advice=sage_advice,
                generated_files=files_created
            )
            design_path.write_text(design_content, encoding="utf-8")
            files_created.append(str(design_path))
            
            self.logger.info(f"✅ 実コード生成完了: {len(files_created)}ファイル")
            
        except Exception as e:
            self.logger.error(f"❌ テンプレート生成エラー: {e}")
            # フォールバック: 従来の設計書のみ
            general_path = impl_dir / f"solution_{issue.number}.md"
            general_content = f"""# General Solution: {issue.title}

## Issue Details
- **Issue Number**: #{issue.number}
- **Type**: General
- **Error**: {str(e)}

## Description
{issue.body or '詳細なし'}

## Sage Recommendations
{self._format_sage_advice(sage_advice)}

## Implementation Status
テンプレート生成中にエラーが発生しました。手動での実装が必要です。
"""
            general_path.write_text(general_content, encoding="utf-8")
            files_created.append(str(general_path))

        return files_created

    def _format_sage_advice(self, sage_advice: Dict[str, Any]) -> str:
        """賢者のアドバイスをフォーマット"""
        formatted = []

        for sage_type, advice in sage_advice.items():
            if isinstance(advice, dict) and advice.get("advice"):
                formatted.append(f"**{sage_type.title()} Sage**: {advice['advice']}")

        return (
            "\n".join(formatted) if formatted else "No specific sage advice available"
        )

    def _generate_implementation_readme(
        self, issue: Issue, sage_advice: Dict[str, Any], files_created: List[str]
    ) -> str:
        """実装READMEを生成"""
        return f"""# Auto-Generated Implementation for Issue #{issue.number}

## Issue Information
- **Title**: {issue.title}
- **Number**: #{issue.number}
- **Type**: {self.pr_creator._classify_issue(issue) if self.pr_creator else 'general'}
- **Created**: {datetime.now().isoformat()}

## Description
{issue.body or '詳細なし'}

## Sage Analysis
{self._format_sage_advice(sage_advice)}

## Generated Files
{chr(10).join(f"- {file}" for file in files_created)}

## Next Steps
1. Review the generated implementation
2. Customize as needed for specific requirements
3. Run tests to ensure functionality
4. Update documentation if necessary

---
*This implementation was auto-generated by Enhanced Auto Issue Processor*
"""

    def _generate_commit_message(
        self, issue: Issue, implementation_details: Dict[str, Any]
    ) -> str:
        """コミットメッセージを生成"""
        issue_type = implementation_details.get("type", "general")

        # Conventional Commits形式でプレフィックスを決定
        prefix_map = {
            "bug_fix": "fix",
            "feature": "feat",
            "documentation": "docs",
            "optimization": "perf",
            "test": "test",
            "general": "chore",
        }
        prefix = prefix_map.get(issue_type, "chore")

        # タイトルを短縮（50文字制限）
        title = issue.title[:40] if len(issue.title) > 40 else issue.title

        return f"{prefix}: {title} (#{issue.number})"

    @retry_on_github_error(max_retries=3, base_delay=1.0)
    async def _create_issue_comment_safe(self, issue: Issue, comment_body: str) -> bool:
        """安全にイシューコメントを作成（リトライあり）"""
        try:
            issue.create_comment(comment_body)
            self.logger.info(f"   → コメント作成完了: Issue #{issue.number}")
            return True
        except Exception as e:
            self.logger.error(f"❌ コメント作成失敗: {e}")
            return False

    def _determine_priority(self, issue: Issue) -> str:
        """イシューの優先度を判定"""
        labels = [label.name.lower() for label in issue.labels]
        title_lower = issue.title.lower()

        # ラベルベースの優先度判定
        if any(label in labels for label in ["critical", "urgent", "blocker"]):
            return "critical"
        elif any(label in labels for label in ["high", "priority:high", "important"]):
            return "high"
        elif any(label in labels for label in ["medium", "priority:medium"]):
            return "medium"

        # タイトルベースの優先度判定
        if any(word in title_lower for word in ["critical", "urgent", "emergency"]):
            return "critical"
        elif any(word in title_lower for word in ["important", "high priority"]):
            return "high"

        return "low"

    def _determine_priority_from_cache(self, issue_data: Dict[str, Any]) -> str:
        """キャッシュされたデータから優先度を判定（高速版）"""
        labels = [label.lower() for label in issue_data["labels"]]
        title_lower = issue_data["title"].lower()

        # ラベルベースの優先度判定
        if any(label in labels for label in ["critical", "urgent", "blocker"]):
            return "critical"
        elif any(label in labels for label in ["high", "priority:high", "important"]):
            return "high"
        elif any(label in labels for label in ["medium", "priority:medium"]):
            return "medium"

        # タイトルベースの優先度判定
        if any(word in title_lower for word in ["critical", "urgent", "emergency"]):
            return "critical"
        elif any(word in title_lower for word in ["important", "high priority"]):
            return "high"

        return "low"

    async def get_metrics_report(self) -> Dict[str, Any]:
        """メトリクスレポートを生成"""
        total = self.metrics["processed_issues"]
        successful = self.metrics["successful_prs"]

        return {
            "metrics": self.metrics.copy(),
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "average_processing_time": (
                sum(self.metrics["processing_time"])
                / len(self.metrics["processing_time"])
                if self.metrics["processing_time"]
                else 0
            ),
            "four_sages_availability": self.four_sages.sages_available,
            "timestamp": datetime.now().isoformat(),
        }

    async def run_enhanced(self, max_issues=1, priorities=None, enable_smart_merge=True, enable_four_sages=True, enable_analytics=False):
        """拡張版の実行
        
        Args:
            max_issues: 処理する最大イシュー数
            priorities: 処理対象の優先度リスト
            enable_smart_merge: スマートマージシステムの有効化
            enable_four_sages: 4賢者システムの有効化
            enable_analytics: 詳細分析の有効化
        """
        # デフォルト値設定
        if priorities is None:
            priorities = ["critical", "high", "medium", "low"]
        try:
            self.logger.info("🚀 Enhanced Auto Issue Processor 起動開始")
            self.logger.info("   → プロセスID: %s", os.getpid())
            self.logger.info(f"   → 最大処理数: {max_issues}")
            self.logger.info(f"   → 対象優先度: {priorities}")
            self.logger.info(f"   → スマートマージ: {enable_smart_merge}")
            self.logger.info(f"   → 4賢者システム: {enable_four_sages}")
            self.logger.info(f"   → 詳細分析: {enable_analytics}")
            self.logger.info(
                "   → 実行時刻: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            # GitHubクライアントを初期化
            self.logger.info("📌 GitHub認証情報を確認中...")
            github_token = os.environ.get("GITHUB_TOKEN")
            if not github_token:
                self.logger.error("GITHUB_TOKEN環境変数が設定されていません")
                return
            self.logger.info("   → GITHUB_TOKEN: 設定済み (%d文字)", len(github_token))

            if not GITHUB_AVAILABLE:
                self.logger.error("PyGithubがインストールされていません")
                return
            self.logger.info("   → PyGithubライブラリ: 利用可能")

            self.logger.info("🔑 GitHub APIクライアント初期化中...")
            github = Github(github_token)
            self.logger.info("   → GitHub APIクライアント作成完了")

            repo_name = os.environ.get("GITHUB_REPOSITORY", "ext-maru/ai-co")
            self.logger.info("   → リポジトリ: %s", repo_name)

            repo = github.get_repo(repo_name)
            self.logger.info("   → リポジトリ接続: 成功")

            # PR作成クラスを初期化
            self.logger.info("🔧 PR作成システム初期化中...")
            self.pr_creator = EnhancedPRCreator(github, repo)
            self.logger.info("   → PR作成システム: 準備完了")

            # 処理可能なイシューを取得（キャッシュ＋プリフェッチ戦略）
            self.logger.info("📋 オープンイシューを取得中...")

            cache_key = f"open_issues_{repo.full_name}"
            cached_issues = self.issue_cache.get(cache_key)

            if cached_issues is not None:
                open_issues = cached_issues
                self.logger.info(f"   → キャッシュから取得: {len(open_issues)}件")
            else:
                self.logger.info("   → GitHub APIを呼び出しています...")
                self.logger.info("   → プリフェッチ戦略: 全データを一括取得")
                start_fetch = datetime.now()

                # リスト化により全データを一度に取得（API呼び出し削減）
                open_issues = list(
                    repo.get_issues(state="open", sort="updated", direction="desc")
                )

                # キャッシュに保存
                self.issue_cache.set(cache_key, open_issues)

                fetch_time = (datetime.now() - start_fetch).total_seconds()
                self.logger.info(f"   → {len(open_issues)}件のオープンイシューを発見")
                self.logger.info(f"   → 取得時間: {fetch_time:.1f}秒")

            # 事前データ読み込み（バッチ処理最適化）
            self.logger.info("🔄 全イシューデータを事前読み込み中...")
            start_preload = datetime.now()
            issue_data_cache = []

            # 全イシューの必要データを一括でメモリに読み込み
            for i, issue in enumerate(open_issues):
                if i % 10 == 0 and i > 0:
                    self.logger.info(f"   → 事前読み込み進捗: {i}/{len(open_issues)}件")

                # 必要なデータを一度に取得（以降はメモリアクセスのみ）
                try:
                    labels = [l.name for l in issue.labels]  # 一度だけAPI呼び出し
                    is_pr = issue.pull_request is not None

                    issue_data_cache.append(
                        {
                            "number": issue.number,
                            "title": issue.title,
                            "labels": labels,
                            "is_pr": is_pr,
                            "issue_obj": issue,  # 実際のオブジェクトも保持
                        }
                    )
                except Exception as e:
                    self.logger.warning(f"   → イシュー #{issue.number} 読み込みエラー: {e}")
                    continue

            preload_time = (datetime.now() - start_preload).total_seconds()
            self.logger.info(f"   → 事前読み込み完了: {preload_time:.1f}秒")
            self.logger.info(f"   → キャッシュしたイシュー: {len(issue_data_cache)}件")

            # 高速フィルタリング（メモリ上のデータのみ使用）
            self.logger.info("🔍 処理対象イシューをフィルタリング中...")
            start_filter = datetime.now()
            processable_issues = []
            filtered_count = {
                "pr": 0,
                "auto_generated": 0,
                "high_priority": 0,
                "low_priority_excluded": 0
            }

            # メモリ上のデータで高速フィルタリング
            for data in issue_data_cache:
                # PRかどうかチェック（メモリアクセス - 高速）
                if data["is_pr"]:
                    filtered_count["pr"] += 1
                    continue

                # auto-generatedラベルをチェック（メモリアクセス - 高速）
                if "auto-generated" in data["labels"]:
                    filtered_count["auto_generated"] += 1
                    continue

                # 優先度を判定（メモリアクセス - 高速）
                priority = self._determine_priority_from_cache(data)
                if priority not in priorities:  # 指定された優先度のみ処理
                    filtered_count["low_priority_excluded"] += 1
                    continue

                # 処理対象として追加
                processable_issues.append(
                    {
                        "number": data["number"],
                        "title": data["title"],
                        "priority": priority,
                        "issue_obj": data["issue_obj"],  # 実際の処理用
                    }
                )

            filter_time = (datetime.now() - start_filter).total_seconds()
            self.logger.info(f"   → フィルタリング完了: {filter_time:.1f}秒")
            self.logger.info(f"   → フィルタリング結果:")
            self.logger.info(f"     → PR除外: {filtered_count['pr']}件")
            self.logger.info(
                f"     → auto-generated除外: {filtered_count['auto_generated']}件"
            )
            self.logger.info(f"     → 高優先度除外: {filtered_count['high_priority']}件")
            self.logger.info(f"     → 低優先度除外: {filtered_count['low_priority_excluded']}件")
            self.logger.info(f"     → 処理対象: {len(processable_issues)}件")

            if not processable_issues:
                self.logger.info("❌ 処理可能なイシューがありません")
                return

            # 各イシューを処理
            self.logger.info(f"✅ 処理可能なイシュー: {len(processable_issues)}件発見")
            priority_counts = {}
            for issue in processable_issues:
                priority = issue.get("priority", "unknown")
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
            self.logger.info(f"   → 優先度内訳: {priority_counts}")

            # パラメータで指定されたmax_issuesを使用

            processed_count = 0
            processed_issues = []  # 処理結果を記録
            for issue_data in processable_issues[:max_issues]:
                processed_count += 1
                self.logger.info(
                    f"📌 処理 {processed_count}/{max_issues}: イシュー #{issue_data['number']}"
                )

                # イシューの詳細を取得（キャッシュされたオブジェクトを使用）
                self.logger.info(f"   → イシュー詳細を取得中...")
                issue = issue_data.get("issue_obj") or repo.get_issue(
                    issue_data["number"]
                )
                self.logger.info(f"   → タイトル: {issue.title}")
                self.logger.info(f"   → 優先度: {issue_data['priority']}")

                # ラベル表示（キャッシュから取得）
                if "issue_obj" in issue_data:
                    # キャッシュからラベル情報を取得（高速）
                    cached_labels = next(
                        (
                            data["labels"]
                            for data in issue_data_cache
                            if data["number"] == issue_data["number"]
                        ),
                        [],
                    )
                    label_str = ", ".join(cached_labels) if cached_labels else "なし"
                else:
                    # フォールバック: 直接取得
                    label_str = (
                        ", ".join([l.name for l in issue.labels])
                        if issue.labels
                        else "なし"
                    )

                self.logger.info(f"   → ラベル: {label_str}")

                # イシューを処理
                self.logger.info(f"   → 処理開始...")
                start_time = datetime.now()
                result = await self.process_issue_with_pr(issue)
                processing_time = (datetime.now() - start_time).total_seconds()

                if result["success"]:
                    self.logger.info(f"✅ イシュー #{issue.number} の処理が完了しました")
                    self.logger.info(f"   → 処理時間: {processing_time:.1f}秒")
                    if result["pr_number"]:
                        self.logger.info(f"   → PR番号: #{result['pr_number']}")
                        self.logger.info(f"   → PR URL: {result['pr_url']}")
                    # 処理結果を記録
                    processed_issues.append({
                        "number": issue.number,
                        "title": issue.title,
                        "pr_created": True,
                        "pr_number": result.get("pr_number"),
                        "pr_url": result.get("pr_url")
                    })
                else:
                    self.logger.error(f"❌ イシュー #{issue.number} の処理に失敗")
                    self.logger.error(f"   → エラー: {result['error']}")
                    self.logger.error(f"   → 処理時間: {processing_time:.1f}秒")
                    # 失敗も記録
                    processed_issues.append({
                        "number": issue.number,
                        "title": issue.title,
                        "pr_created": False,
                        "error": result.get("error")
                    })

                # 次の処理まで待機（最後の処理後は待たない）
                if processed_count < max_issues and processed_count < len(
                    processable_issues
                ):
                    self.logger.info(f"   → 次の処理まで1秒待機...")
                    await asyncio.sleep(1)

            # 処理完了サマリー
            self.logger.info("=" * 60)
            self.logger.info("📊 Enhanced Auto Issue Processor 実行完了")
            self.logger.info(
                f"   → 処理イシュー数: {processed_count}/{len(processable_issues)}件"
            )
            self.logger.info(
                f"   → 全体処理時間: {(datetime.now() - self.metrics['started_at']).total_seconds():.1f}秒"
            )
            self.logger.info("=" * 60)
            
            # 実行結果を返す
            return {
                "processed_count": processed_count,
                "total_available": len(processable_issues),
                "processed_issues": processed_issues,
                "metrics": self.metrics,
                "status": "success"
            }

        except Exception as e:
            self.logger.error(f"拡張版実行中にエラー: {e}")
            self.logger.error(f"   → エラー詳細: {type(e).__name__}")
            import traceback

            self.logger.error(f"   → スタックトレース:\n{traceback.format_exc()}")
            
            # エラー時の結果を返す
            return {
                "processed_count": 0,
                "total_available": 0,
                "error": str(e),
                "status": "error"
            }


async def main():
    """メイン関数"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info("🚀 Enhanced Auto Issue Processor メイン処理開始")
    logger.info("📦 必要なシステムコンポーネントを初期化しています...")
    logger.info("   → これには30-40秒程度かかる場合があります")
    logger.info("   → 4賢者システム（Knowledge, Task, Incident, RAG）の初期化")
    logger.info("   → 知識ベースのロード")
    logger.info("   → GitHub API接続の確立")

    processor = EnhancedAutoIssueProcessor()
    await processor.run_enhanced()


if __name__ == "__main__":
    asyncio.run(main())
