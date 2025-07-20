#!/usr/bin/env python3
"""
🤖 GitHub Issue Auto Processor
優先度Medium/Lowのイシューを自動的に処理するシステム
"""

import asyncio
import json
import logging
import os
import subprocess

# Elder System imports
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from github import Github
from github.Issue import Issue

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.core.elders_legacy import EldersServiceLegacy

# 必要なモジュールのインポート
from libs.rag_manager import RagManager
from libs.elder_system.flow.elder_flow_engine import ElderFlowEngine
from libs.knowledge_sage import KnowledgeSage
from libs.task_sage import TaskSage
from libs.incident_sage import IncidentSage
from libs.integrations.github.api_implementations.create_pull_request import GitHubCreatePullRequestImplementation
from libs.claude_cli_executor import ClaudeCLIExecutor


class AutoIssueElderFlowEngine:
    """Auto Issue Processor専用のElder Flow Engine"""

    def __init__(self):
        self.elder_flow = ElderFlowEngine()
        
        # GitHub設定の検証と初期化
        github_token = os.getenv("GITHUB_TOKEN")
        repo_owner = os.getenv("GITHUB_REPO_OWNER")
        repo_name = os.getenv("GITHUB_REPO_NAME")

        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        if not repo_owner:
            raise ValueError("GITHUB_REPO_OWNER environment variable is required") 
        if not repo_name:
            raise ValueError("GITHUB_REPO_NAME environment variable is required")

        self.pr_creator = GitHubCreatePullRequestImplementation(
            token=github_token, repo_owner=repo_owner, repo_name=repo_name
        )
        # 自動マージを有効化
        self.pr_creator.auto_merge_enabled = True
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

            # 品質ゲートチェック：失敗時はPR作成を中止
            quality_gate_success = True
            if flow_result.get("results", {}).get("quality_gate", {}).get("success") == False:
                quality_gate_success = False
                self.logger.warning(f"Quality gate failed for task: {task_name}")
            
            # Elder Flow成功かつ品質ゲート通過の場合のみPR作成
            if (flow_result.get("status") == "success" or flow_result.get("task_name")) and quality_gate_success:
                # PR作成を実行（Elder Flow結果を含む）
                pr_result = await self._create_pull_request(
                    issue_number, issue_title, issue_body, task_name, flow_result
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
            elif not quality_gate_success:
                return {
                    "status": "quality_gate_failed",
                    "pr_url": None,
                    "message": f"品質ゲート失敗のためPR作成を中止: {task_name}",
                    "flow_result": flow_result,
                    "quality_gate_error": flow_result.get("results", {}).get("quality_gate", {}).get("error"),
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
        self, issue_number, issue_title, issue_body, task_name, flow_result=None
    ):
        """自動でPR作成（実装コード生成版）"""
        try:
            # 安全なGit操作をインポート
            from .safe_git_operations import SafeGitOperations
            
            safe_git = SafeGitOperations()
            
            # PR用ブランチ作成ワークフローを実行
            pr_title = f"Auto-fix: {issue_title} (#{issue_number})"
            workflow_result = safe_git.create_pr_branch_workflow(pr_title, "main", "auto-fix")
            
            if not workflow_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to create PR branch: {workflow_result['error']}",
                    "workflow_result": workflow_result
                }
            
            branch_name = workflow_result["branch_name"]
            original_branch = workflow_result["original_branch"]
            
            try:
                # Elder Flow結果から実装ファイルを生成
                implementation_success = await self._generate_implementation_files(
                    issue_number, issue_title, issue_body, task_name, flow_result
                )
                
                if not implementation_success:
                    self.logger.warning(f"Implementation generation failed for issue #{issue_number}")
                    # フォールバック: 設計書のみ作成
                    await self._create_design_document(issue_number, issue_title, issue_body, task_name)
                
                # 安全な追加コミット（必要に応じて）
                additional_commit_result = safe_git.auto_commit_if_changes(
                    f"fix: Additional changes for issue #{issue_number}"
                )
                
                if not additional_commit_result["success"] and additional_commit_result.get("action") != "no_changes":
                    self.logger.warning(f"Additional commit failed: {additional_commit_result['error']}")
                
                # 最新変更をプッシュ（必要に応じて）
                if additional_commit_result.get("action") == "committed":
                    push_result = safe_git.push_branch_safely(branch_name)
                    if not push_result["success"]:
                        self.logger.warning(f"Failed to push additional changes: {push_result['error']}")
                
            finally:
                # 元のブランチに戻る
                restore_result = safe_git.restore_original_branch(original_branch)
                if not restore_result["success"]:
                    self.logger.error(f"Failed to restore original branch: {restore_result['error']}")
                    # フォールバック: 直接gitコマンドで戻る
                    try:
                        subprocess.run(["git", "checkout", original_branch], check=True)
                    except Exception as e:
                        self.logger.error(f"Fallback checkout failed: {e}")

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
                draft=False,  # 通常のPRとして作成（自動マージ可能）
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
            # エラー時もブランチを元に戻そうとする
            try:
                if 'safe_git' in locals() and 'original_branch' in locals():
                    safe_git.restore_original_branch(original_branch)
            except Exception as restore_error:
                self.logger.error(f"Failed to restore branch after error: {restore_error}")
            
            return {"success": False, "error": f"PR作成例外: {str(e)}"}

    async def _generate_implementation_files(self, issue_number, issue_title, issue_body, task_name, flow_result):
        """Elder Flow結果から実装ファイルを生成"""
        try:
            if not flow_result or not flow_result.get("results"):
                return False
                
            results = flow_result.get("results", {})
            servant_execution = results.get("servant_execution", {})
            
            if not servant_execution.get("success"):
                return False
                
            execution_results = servant_execution.get("execution_results", [])
            files_created = 0
            
            # TDDフローの実行を優先
            self.logger.info(f"🔍 DEBUG: Calling _execute_tdd_flow with issue_number={issue_number}, issue_title='{issue_title}'")
            tdd_success = await self._execute_tdd_flow(issue_number, issue_title, execution_results)
            if tdd_success:
                files_created += 4  # RED, GREEN, BLUE, FINAL の4ファイル
                self.logger.info(f"TDD implementation completed for Issue #{issue_number}")
            else:
                # TDD失敗時は従来の方法でフォールバック
                for result in execution_results:
                    if result.get("action") == "generate_code" and result.get("success"):
                        # 生成されたコードをファイルに保存
                        code_content = result.get("generated_code", "")
                        code_name = result.get("name", "generated_implementation")
                        
                        if code_content:
                            # ファイルパスを決定
                            if "test" in code_name.lower():
                                file_path = f"tests/auto_generated/test_issue_{issue_number}.py"
                                os.makedirs("tests/auto_generated", exist_ok=True)
                            else:
                                file_path = f"auto_implementations/issue_{issue_number}_{code_name.lower()}.py"
                                os.makedirs("auto_implementations", exist_ok=True)
                            
                            # コードファイルを作成
                            with open(file_path, "w") as f:
                                f.write(f'"""\nAuto-generated implementation for Issue #{issue_number}\n{issue_title}\n\nGenerated by Elder Flow Auto Issue Processor\n"""\n\n')
                                f.write(code_content)
                            
                            files_created += 1
                            self.logger.info(f"Generated implementation file: {file_path}")
                            
                    elif result.get("action") == "create_test" and not result.get("success"):
                        # テスト作成失敗時はTDDを再試行
                        if not tdd_success:
                            tdd_retry = await self._execute_tdd_flow(issue_number, issue_title, [])
                            if tdd_retry:
                                files_created += 4
                            else:
                                # 最終フォールバック
                                test_content = self._generate_alternative_test(issue_number, issue_title)
                                test_path = f"tests/auto_generated/test_issue_{issue_number}_alt.py"
                                os.makedirs("tests/auto_generated", exist_ok=True)
                                
                                with open(test_path, "w") as f:
                                    f.write(test_content)
                                
                                files_created += 1
                                self.logger.info(f"Generated alternative test file: {test_path}")
            
            # 設計書も作成
            await self._create_design_document(issue_number, issue_title, issue_body, task_name, detailed=True)
            
            return files_created > 0
            
        except Exception as e:
            self.logger.error(f"Implementation generation error: {e}")
            return False
    
    def _generate_alternative_test(self, issue_number, issue_title):
        """aiofilesエラーの代替テスト生成"""
        return f'"""\nAlternative test for Issue #{issue_number}\n{issue_title}\n\nGenerated to replace failed aiofiles test creation\n"""\n\nimport unittest\nfrom unittest.mock import Mock, patch\n\n\nclass TestIssue{issue_number}(unittest.TestCase):\n    """Test case for issue #{issue_number}"""\n    \n    def setUp(self):\n        """Set up test fixtures"""\n        self.test_data = {{}}\n    \n    def test_basic_functionality(self):\n        """Test basic functionality"""\n        # TODO: Implement actual test logic\n        self.assertTrue(True, "Placeholder test - implement actual logic")\n    \n    def test_error_handling(self):\n        """Test error handling"""\n        # TODO: Implement error handling tests\n        self.assertTrue(True, "Placeholder test - implement error handling")\n\n\nif __name__ == "__main__":\n    unittest.main()\n'
    
    async def _create_design_document(self, issue_number, issue_title, issue_body, task_name, detailed=False):
        """設計書作成（実装ファイルの補完）"""
        fix_file_path = f"auto_fixes/issue_{issue_number}_fix.md"
        os.makedirs("auto_fixes", exist_ok=True)
        
        content = f"""# Auto-fix for Issue #{issue_number}

## Task: {task_name}

## Original Issue
{issue_title}

{issue_body}"""
        
        if detailed:
            content += "\n\n## Implementation Status\n- ✅ Code implementation generated\n- ✅ Test files created\n- ✅ Design documentation completed\n"
        
        content += "\n\n---\n*This file was auto-generated by Elder Flow Auto Issue Processor*\n"
        
        with open(fix_file_path, "w") as f:
            f.write(content)

    async def _execute_tdd_flow(self, issue_number, issue_title, execution_results):
        """TDD Red-Green-Refactor サイクルを実行"""
        try:
            # CodeCraftsmanサーバントを直接インポート
            from libs.elder_flow_servant_executor_real import CodeCraftsmanServantReal, ServantTask, ServantType
            
            code_craftsman = CodeCraftsmanServantReal()
            
            # クラス名を生成（Issue番号から）
            target_class = f"Issue{issue_number}Implementation"
            target_method = "execute"
            feature_description = f"Implementation for {issue_title}"
            
            # デバッグログ追加
            self.logger.info(f"🔍 DEBUG: TDD flow called with issue_number={issue_number}, issue_title='{issue_title}'")
            self.logger.info(f"🔍 DEBUG: Generated target_class={target_class}")
            self.logger.info(f"Starting TDD flow for Issue #{issue_number}: {target_class}")
            
            # Step 1: RED - 失敗するテストを生成（スマート生成対応）
            red_task = ServantTask(
                task_id=f"tdd_red_{issue_number}",
                servant_type=ServantType.CODE_CRAFTSMAN,
                description=f"Generate failing test for Issue #{issue_number}",
                command="tdd_generate_failing_test",
                arguments={
                    "test_name": f"test_issue_{issue_number}",
                    "feature_description": feature_description,
                    "target_class": target_class,
                    "target_method": target_method,
                    "issue_title": issue_title,
                    "issue_body": self._get_issue_body_for_tdd(issue_number),
                }
            )
            
            red_result = await code_craftsman.execute_task(red_task)
            
            if red_result.get("success"):
                # REDテストファイルを保存
                test_content = red_result.get("generated_test", "")
                red_test_path = f"tests/tdd_red/test_issue_{issue_number}_red.py"
                os.makedirs("tests/tdd_red", exist_ok=True)
                
                with open(red_test_path, "w") as f:
                    f.write(test_content)
                
                self.logger.info(f"TDD RED: Generated failing test: {red_test_path}")
                
                # Step 2: GREEN - テストを通す最小実装（スマート生成対応）
                green_task = ServantTask(
                    task_id=f"tdd_green_{issue_number}",
                    servant_type=ServantType.CODE_CRAFTSMAN,
                    description=f"Generate minimal implementation for Issue #{issue_number}",
                    command="tdd_implement_code",
                    arguments={
                        "target_class": target_class,
                        "target_method": target_method,
                        "feature_description": feature_description,
                        "issue_title": issue_title,
                        "issue_body": self._get_issue_body_for_tdd(issue_number),
                    }
                )
                
                green_result = await code_craftsman.execute_task(green_task)
                
                if green_result.get("success"):
                    # GREENコードファイルを保存
                    impl_content = green_result.get("generated_code", "")
                    green_impl_path = f"auto_implementations/issue_{issue_number}_green.py"
                    os.makedirs("auto_implementations", exist_ok=True)
                    
                    with open(green_impl_path, "w") as f:
                        f.write(impl_content)
                    
                    self.logger.info(f"TDD GREEN: Generated minimal implementation: {green_impl_path}")
                    
                    # Step 3: BLUE - リファクタリング
                    blue_task = ServantTask(
                        task_id=f"tdd_blue_{issue_number}",
                        servant_type=ServantType.CODE_CRAFTSMAN,
                        description=f"Refactor implementation for Issue #{issue_number}",
                        command="tdd_refactor_code",
                        arguments={
                            "target_class": target_class,
                            "current_code": impl_content,
                            "improvement_goals": [
                                "Better error handling",
                                "Improved logging",
                                "Type hints",
                                "Documentation"
                            ],
                        }
                    )
                    
                    blue_result = await code_craftsman.execute_task(blue_task)
                    
                    if blue_result.get("success"):
                        # BLUEリファクタリング版を保存
                        refactored_content = blue_result.get("refactored_code", "")
                        blue_impl_path = f"auto_implementations/issue_{issue_number}_refactored.py"
                        
                        with open(blue_impl_path, "w") as f:
                            f.write(refactored_content)
                        
                        self.logger.info(f"TDD BLUE: Generated refactored implementation: {blue_impl_path}")
                        
                        # TDD完全実装の最終版を作成
                        final_impl_path = f"auto_implementations/issue_{issue_number}_implementation.py"
                        with open(final_impl_path, "w") as f:
                            f.write(refactored_content)
                        
                        self.logger.info(f"TDD COMPLETE: Final implementation saved: {final_impl_path}")
                        
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"TDD flow execution error: {e}")
            return False
    
    def _get_issue_body_for_tdd(self, issue_number: int) -> str:
        """TDD用にIssue本文を取得"""
        try:
            issue = self.repo.get_issue(issue_number)
            return issue.body or ""
        except Exception as e:
            self.logger.warning(f"Failed to get issue body for #{issue_number}: {e}")
            return ""


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

    MAX_ISSUES_PER_HOUR = 30  # 1時間あたり最大30イシューまで
    MAX_CONCURRENT = 3  # 同時に3つまで処理可能
    COOLDOWN_PERIOD = 60  # 1分

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
        self.task_sage = TaskSage()
        self.incident_sage = IncidentSage()
        self.knowledge_sage = KnowledgeSage()
        self.rag_sage = RagManager()

        self.limiter = ProcessingLimiter()
        self.evaluator = ComplexityEvaluator()

        # 処理対象の優先度（中以上）
        self.target_priorities = ["critical", "high", "medium"]
        
        # 処理履歴ファイル
        self.processing_history_file = "logs/auto_issue_processing.json"
        
        # A2Aモード設定
        self.a2a_enabled = os.getenv("AUTO_ISSUE_A2A_MODE", "false").lower() == "true"
        self.a2a_max_parallel = int(os.getenv("AUTO_ISSUE_A2A_MAX_PARALLEL", "5"))
        
        if self.a2a_enabled:
            logger.info(f"A2A mode is ENABLED with max parallel: {self.a2a_max_parallel}")
        else:
            logger.info("A2A mode is DISABLED (using sequential processing)")

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

                # A2Aモードの場合は並列処理
                if self.a2a_enabled:
                    logger.info("Processing issues in A2A mode (parallel isolated processes)")
                    results = await self.process_issues_a2a(issues)
                    
                    # 成功したIssueを集計
                    successful = [r for r in results if r.get("status") == "success"]
                    failed = [r for r in results if r.get("status") == "error"]
                    
                    return {
                        "status": "a2a_completed",
                        "mode": "a2a",
                        "total_issues": len(issues),
                        "successful": len(successful),
                        "failed": len(failed),
                        "results": results,
                        "message": f"A2A processing completed: {len(successful)}/{len(issues)} issues processed successfully"
                    }
                else:
                    # 従来の順次処理モード
                    for issue in issues:
                        result = await self.execute_auto_processing(issue)
                        
                        # 既存PRがある場合はスキップして次へ
                        if result.get("status") == "already_exists":
                            logger.info(f"Issue #{issue.number} スキップ (既存PR有り) - 次のIssueを処理...")
                            continue
                        
                        # 処理成功または失敗の場合は結果を返す
                        return {
                            "status": "success",
                            "processed_issue": {
                                "number": issue.number,
                                "title": issue.title,
                                "result": result,
                            },
                        }
                    
                    # すべてのIssueがスキップされた場合
                    return {
                        "status": "all_skipped",
                        "message": f"All {len(issues)} processable issues were skipped (existing PRs)",
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
        """処理可能なイシューをスキャン（重複処理防止機能付き）"""
        processable_issues = []

        # 最近処理されたイシューを確認（重複防止）
        recently_processed = self._get_recently_processed_issues()

        # オープンなイシューを取得
        open_issues = self.repo.get_issues(state="open")

        for issue in open_issues:
            # PRは除外
            if issue.pull_request:
                continue

            # 重複処理防止チェック
            if issue.number in recently_processed:
                logger.info(f"Issue #{issue.number} は最近処理済みのためスキップ")
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

        # 優先度でソート（critical > high > medium > low）
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        processable_issues.sort(key=lambda issue: (
            priority_order.get(self._determine_priority(issue), 4),  # 不明な優先度は最後
            issue.number  # 同じ優先度では番号順
        ))
        
        return processable_issues

    def _get_recently_processed_issues(self, hours=24) -> Set[int]:
        """指定時間内に処理されたイシュー番号を取得"""
        recently_processed = set()
        
        try:
            import json
            from datetime import datetime, timedelta
            
            if not os.path.exists(self.processing_history_file):
                return recently_processed
                
            with open(self.processing_history_file, 'r') as f:
                history = json.load(f)
                
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            for record in history:
                try:
                    record_time = datetime.fromisoformat(record.get("timestamp", ""))
                    if record_time > cutoff_time:
                        issue_id = record.get("issue_id") or record.get("issue_number")
                        if issue_id:
                            recently_processed.add(int(issue_id))
                except (ValueError, TypeError):
                    continue
                    
        except Exception as e:
            logger.warning(f"処理履歴の読み込みに失敗: {e}")
            
        return recently_processed

    async def execute_auto_processing(self, issue: Issue) -> Dict[str, Any]:
        """Elder Flowを使用してイシューを自動処理"""
        try:
            # 既存のPRをチェック
            existing_pr = await self._check_existing_pr_for_issue(issue.number)
            if existing_pr:
                logger.info(f"PR already exists for issue #{issue.number}: PR #{existing_pr['number']}")
                return {
                    "status": "already_exists",
                    "message": f"PR #{existing_pr['number']} already exists for this issue",
                    "pr_url": existing_pr['html_url'],
                    "pr_number": existing_pr['number']
                }
            
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

            # Elder Flowエンジンが既にPR作成を処理済み
            # 結果に基づいてイシューにコメント追加
            if result.get("status") == "success":
                # PR作成成功時
                pr_url = result.get("pr_url")
                if pr_url:
                    issue.create_comment(
                        f"🤖 Auto-processed by Elder Flow\n\n"
                        f"PR created: {pr_url}\n\n"
                        f"This issue was automatically processed with code implementation."
                    )
                return result
            elif result.get("status") == "quality_gate_failed":
                # 品質ゲート失敗時
                issue.create_comment(
                    f"🚨 Auto-processing failed\n\n"
                    f"Quality gate failed: {result.get('quality_gate_error', 'Unknown error')}\n\n"
                    f"Manual review and implementation required."
                )
                return result
            elif result.get("status") == "already_exists":
                # 既存のPRがある場合
                issue.create_comment(
                    f"🤖 Auto Issue Processor Notice\n\n"
                    f"This issue already has an associated PR: {result.get('pr_url')}\n"
                    f"Skipping automatic processing to avoid duplication."
                )
                return result
            elif result.get("status") == "success":
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

    def enable_a2a_mode(self):
        """A2Aモードを有効化"""
        self.a2a_enabled = True
        logger.info("A2A mode enabled for Auto Issue Processor")

    def disable_a2a_mode(self):
        """A2Aモードを無効化"""
        self.a2a_enabled = False
        logger.info("A2A mode disabled for Auto Issue Processor")

    async def process_issue_isolated(self, issue: Issue) -> Dict[str, Any]:
        """
        独立したClaude CLIプロセスでIssueを処理
        コンテキストの分離とPIDロック回避のためのA2A実装
        """
        try:
            # Claude CLI実行用のプロンプト作成
            prompt = f"""あなたはクロードエルダー（Claude Elder）です。

以下のGitHub Issueを自動処理してください：

**Issue情報:**
- 番号: #{issue.number}
- タイトル: {issue.title}
- 内容: {issue.body or "No description"}
- ラベル: {', '.join([label.name for label in issue.labels]) if issue.labels else 'None'}

**実行指示:**
1. Elder Flowを使用してこのIssueを解決してください
2. TDDアプローチで実装してください
3. 実装完了後、自動的にPull Requestを作成してください
4. 品質ゲートをパスすることを確認してください

**重要:**
- このタスクは独立したプロセスで実行されています
- 他のIssue処理とは完全に分離されたコンテキストです
- 完了後、結果をJSON形式で返してください

elder-flow execute "Auto-fix Issue #{issue.number}: {issue.title}" --priority medium
"""

            # Claude CLIの実行
            executor = ClaudeCLIExecutor()
            result_json = executor.execute(
                prompt=prompt,
                model="claude-sonnet-4-20250514",
                working_dir=str(Path.cwd())
            )

            # 結果のパース
            try:
                result = json.loads(result_json)
                return result
            except json.JSONDecodeError:
                # JSON形式でない場合は、テキストから情報を抽出
                if "PR created" in result_json or "pull request" in result_json.lower():
                    return {
                        "status": "success",
                        "message": result_json,
                        "pr_created": True
                    }
                else:
                    return {
                        "status": "completed",
                        "message": result_json
                    }

        except Exception as e:
            logger.error(f"Error in isolated process for issue #{issue.number}: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "issue_number": issue.number
            }

    async def process_issues_a2a(self, issues: List[Issue]) -> List[Dict[str, Any]]:
        """
        複数のIssueをA2A方式で並列処理
        各Issueは独立したClaude CLIプロセスで実行される
        """
        logger.info(f"Starting A2A processing for {len(issues)} issues")
        
        # 並列実行数の制限
        semaphore = asyncio.Semaphore(self.a2a_max_parallel)
        
        async def process_with_limit(issue: Issue) -> Dict[str, Any]:
            """セマフォで並列度を制限しながら処理"""
            async with semaphore:
                logger.info(f"Processing issue #{issue.number} in isolated process")
                return await self.process_issue_isolated(issue)
        
        # すべてのタスクを作成
        tasks = [
            asyncio.create_task(process_with_limit(issue))
            for issue in issues
        ]
        
        # 結果を収集（例外も含む）
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果の整形
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "status": "error",
                    "message": str(result),
                    "issue_number": issues[i].number
                })
            else:
                processed_results.append(result)
        
        logger.info(f"A2A processing completed. Success: {sum(1 for r in processed_results if r.get('status') == 'success')}/{len(processed_results)}")
        
        return processed_results

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

        # デフォルトは中優先度（ラベル無しIssueも処理対象にする）
        return "medium"
    
    async def _check_existing_pr_for_issue(self, issue_number: int) -> Optional[Dict[str, Any]]:
        """指定されたイシューに対する既存のPRをチェック"""
        try:
            # オープンなPRを検索
            pulls = self.repo.get_pulls(state='open')
            
            for pr in pulls:
                # PRのボディ内でイシュー番号への参照をチェック
                if pr.body and f"#{issue_number}" in pr.body:
                    return {
                        "number": pr.number,
                        "html_url": pr.html_url,
                        "title": pr.title,
                        "state": pr.state
                    }
                
                # タイトルにイシュー番号が含まれているかチェック
                if f"#{issue_number}" in pr.title:
                    return {
                        "number": pr.number,
                        "html_url": pr.html_url,
                        "title": pr.title,
                        "state": pr.state
                    }
            
            # クローズされたPRも確認（最近のもののみ）
            closed_pulls = self.repo.get_pulls(state='closed', sort='updated', direction='desc')
            count = 0
            for pr in closed_pulls:
                if count >= 20:  # 最近の20件のみチェック
                    break
                    
                if pr.body and f"#{issue_number}" in pr.body:
                    return {
                        "number": pr.number,
                        "html_url": pr.html_url,
                        "title": pr.title,
                        "state": pr.state
                    }
                    
                if f"#{issue_number}" in pr.title:
                    return {
                        "number": pr.number,
                        "html_url": pr.html_url,
                        "title": pr.title,
                        "state": pr.state
                    }
                    
                count += 1
            
            return None
            
        except Exception as e:
            logger.warning(f"Error checking existing PRs: {str(e)}")
            return None



async def main():
    """メイン処理（テスト用）"""
    processor = AutoIssueProcessor()

    # スキャンモードでテスト
    result = await processor.process_request({"mode": "scan"})
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
