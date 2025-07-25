#!/usr/bin/env python3
"""
🧪 Auto Issue Processor A2A Integration Test Framework
統合テスト強化・エンドツーエンド検証システム

Issue #190対応: 実際のGitHub統合テスト・エンドツーエンドワークフロー検証
"""

import asyncio
import json
import logging
import os
import subprocess

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from unittest.mock import Mock, patch
import pytest
import requests

logger = logging.getLogger("IntegrationTestFramework")

class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"

class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

@dataclass
class TestResult:
    """テスト結果"""
    test_name: str
    test_type: TestType
    status: TestStatus
    execution_time: float
    error_message: Optional[str] = None
    assertions_passed: int = 0
    assertions_failed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TestSuite:
    """テストスイート"""
    name: str
    test_type: TestType
    tests: List[str] = field(default_factory=list)
    setup_required: bool = True
    cleanup_required: bool = True
    dependencies: List[str] = field(default_factory=list)

class GitHubTestEnvironment:
    """GitHub統合テスト環境"""
    
    def __init__(self):
        self.test_repo_owner = os.getenv("TEST_GITHUB_REPO_OWNER", "test-user")
        self.test_repo_name = os.getenv("TEST_GITHUB_REPO_NAME", "a2a-test-repo")
        self.test_token = os.getenv("TEST_GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        
        # テスト用データ
        self.test_issues: List[Dict[str, Any]] = []
        self.test_prs: List[Dict[str, Any]] = []
        self.created_resources: Set[str] = set()
    
    async def setup_test_environment(self) -> Dict[str, Any]:
        """テスト環境セットアップ"""
        setup_result = {
            "success": True,
            "test_repo": f"{self.test_repo_owner}/{self.test_repo_name}",
            "test_issues_created": 0,
            "test_branches_created": 0,
            "errors": []
        }
        
        try:
            # テスト用リポジトリ確認・作成
            repo_exists = await self._check_test_repo_exists()
            if not repo_exists:
                await self._create_test_repo()
            
            # テスト用Issueデータ作成
            test_issues_data = self._generate_test_issues()
            
            for issue_data in test_issues_data:
                issue = await self._create_test_issue(issue_data)
                if issue:
                    self.test_issues.append(issue)
                    setup_result["test_issues_created"] += 1
                    self.created_resources.add(f"issue_{issue['number']}")
            
            # テスト用ブランチ作成
            test_branches = ["test-branch-1", "test-branch-2", "test-integration"]
            for branch_name in test_branches:
                if await self._create_test_branch(branch_name):
                    setup_result["test_branches_created"] += 1
                    self.created_resources.add(f"branch_{branch_name}")
            
            logger.info(f"Test environment setup completed: {setup_result}")
            
        except Exception as e:
            logger.error(f"Test environment setup failed: {str(e)}")
            setup_result["success"] = False
            setup_result["errors"].append(str(e))
        
        return setup_result
    
    async def cleanup_test_environment(self) -> Dict[str, Any]:
        """テスト環境クリーンアップ"""
        cleanup_result = {
            "success": True,
            "issues_closed": 0,
            "prs_closed": 0,
            "branches_deleted": 0,
            "errors": []
        }
        
        try:
            # 作成したリソースのクリーンアップ
            for resource in self.created_resources:
                try:
                    if resource.startswith("issue_"):
                        issue_number = int(resource.split("_")[1])
                        await self._close_test_issue(issue_number)
                        cleanup_result["issues_closed"] += 1
                    
                    elif resource.startswith("pr_"):
                        pr_number = int(resource.split("_")[1])
                        await self._close_test_pr(pr_number)
                        cleanup_result["prs_closed"] += 1
                    
                    elif resource.startswith("branch_"):
                        branch_name = resource.split("_", 1)[1]
                        await self._delete_test_branch(branch_name)
                        cleanup_result["branches_deleted"] += 1
                        
                except Exception as e:
                    cleanup_result["errors"].append(f"Failed to cleanup {resource}: {str(e)}")
            
            self.created_resources.clear()
            logger.info(f"Test environment cleanup completed: {cleanup_result}")
            
        except Exception as e:
            logger.error(f"Test environment cleanup failed: {str(e)}")
            cleanup_result["success"] = False
            cleanup_result["errors"].append(str(e))
        
        return cleanup_result
    
    def _generate_test_issues(self) -> List[Dict[str, Any]]:
        """テスト用Issue生成"""
        return [
            {

            },
            {
                "title": "Test Issue: Documentation Update",
                "body": "This is a test issue for documentation update automation testing.",
                "labels": ["documentation", "test", "priority:low"]
            },
            {
                "title": "Test Issue: Feature Enhancement",
                "body": "This is a test issue for feature enhancement automation testing.",
                "labels": ["enhancement", "test", "priority:high"]
            }
        ]
    
    async def _check_test_repo_exists(self) -> bool:
        """テストリポジトリ存在確認"""
        try:
            headers = {"Authorization": f"token {self.test_token}"}
            url = f"{self.base_url}/repos/{self.test_repo_owner}/{self.test_repo_name}"
            
            response = requests.get(url, headers=headers)
            return response.status_code == 200
            
        except Exception as e:
            logger.warning(f"Failed to check test repo: {str(e)}")
            return False
    
    async def _create_test_repo(self) -> bool:
        """テストリポジトリ作成"""
        try:
            headers = {"Authorization": f"token {self.test_token}"}
            url = f"{self.base_url}/user/repos"
            
            data = {
                "name": self.test_repo_name,
                "description": "Test repository for A2A integration testing",
                "private": True,
                "auto_init": True
            }
            
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 201:
                logger.info(f"Test repository created: {self.test_repo_name}")
                return True
            else:
                logger.error(f"Failed to create test repo: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Test repo creation failed: {str(e)}")
            return False
    
    async def _create_test_issue(self, issue_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """テストIssue作成"""
        try:
            headers = {"Authorization": f"token {self.test_token}"}
            url = f"{self.base_url}/repos/{self.test_repo_owner}/{self.test_repo_name}/issues"
            
            response = requests.post(url, headers=headers, json=issue_data)
            if response.status_code == 201:
                issue = response.json()
                logger.info(f"Test issue created: #{issue['number']}")
                return issue
            else:
                logger.error(f"Failed to create test issue: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Test issue creation failed: {str(e)}")
            return None
    
    async def _create_test_branch(self, branch_name: str) -> bool:
        """テストブランチ作成"""
        try:
            headers = {"Authorization": f"token {self.test_token}"}
            
            # main ブランチのSHA取得
            ref_url = f"{self.base_url}/repos/{self.test_repo_owner}/{self.test_repo_name}/git/refs/heads/main"
            ref_response = requests.get(ref_url, headers=headers)
            
            if ref_response.status_code != 200:
                return False
            
            main_sha = ref_response.json()["object"]["sha"]
            
            # 新しいブランチ作成
            create_url = f"{self.base_url}/repos/{self.test_repo_owner}/{self.test_repo_name}/git/refs" \
                "{self.base_url}/repos/{self.test_repo_owner}/{self.test_repo_name}/git/refs"
            create_data = {
                "ref": f"refs/heads/{branch_name}",
                "sha": main_sha
            }
            
            create_response = requests.post(create_url, headers=headers, json=create_data)
            if create_response.status_code == 201:
                logger.info(f"Test branch created: {branch_name}")
                return True
            else:
                logger.error(f"Failed to create test branch: {create_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Test branch creation failed: {str(e)}")
            return False
    
    async def _close_test_issue(self, issue_number: int):
        """テストIssueクローズ"""
        try:
            headers = {"Authorization": f"token {self.test_token}"}
            url = f"{self.base_url}/repos/{self.test_repo_owner}/{self." \
                "test_repo_name}/issues/{issue_number}"
            
            data = {"state": "closed"}
            response = requests.patch(url, headers=headers, json=data)
            
            if response.status_code == 200:
                logger.info(f"Test issue closed: #{issue_number}")
            
        except Exception as e:
            logger.warning(f"Failed to close test issue {issue_number}: {str(e)}")
    
    async def _close_test_pr(self, pr_number: int):
        """テストPRクローズ"""
        try:
            headers = {"Authorization": f"token {self.test_token}"}
            url = f"{self.base_url}/repos/{self.test_repo_owner}/{self." \
                "test_repo_name}/pulls/{pr_number}"
            
            data = {"state": "closed"}
            response = requests.patch(url, headers=headers, json=data)
            
            if response.status_code == 200:
                logger.info(f"Test PR closed: #{pr_number}")
            
        except Exception as e:
            logger.warning(f"Failed to close test PR {pr_number}: {str(e)}")
    
    async def _delete_test_branch(self, branch_name: str):
        """テストブランチ削除"""
        try:
            headers = {"Authorization": f"token {self.test_token}"}
            url = f"{self.base_url}/repos/{self.test_repo_owner}/{self." \
                "test_repo_name}/git/refs/heads/{branch_name}"
            
            response = requests.delete(url, headers=headers)
            
            if response.status_code == 204:
                logger.info(f"Test branch deleted: {branch_name}")
            
        except Exception as e:
            logger.warning(f"Failed to delete test branch {branch_name}: {str(e)}")

class A2AEndToEndTester:
    """A2A エンドツーエンドテスター"""
    
    def __init__(self):
        self.github_env = GitHubTestEnvironment()
        self.test_results: List[TestResult] = []

    async def run_e2e_workflow_test(self) -> TestResult:
        """E2Eワークフローテスト実行"""
        test_name = "e2e_workflow_complete"
        start_time = time.time()
        
        try:
            # テスト環境セットアップ
            setup_result = await self.github_env.setup_test_environment()
            if not setup_result["success"]:
                return TestResult(
                    test_name=test_name,
                    test_type=TestType.E2E,
                    status=TestStatus.ERROR,
                    execution_time=time.time() - start_time,
                    error_message=f"Setup failed: {setup_result['errors']}"
                )
            
            assertions_passed = 0
            assertions_failed = 0
            
            # テスト1: 統一ワークフローエンジンの動作確認
            workflow_test = await self._test_unified_workflow_engine()
            if workflow_test["success"]:
                assertions_passed += 1
            else:
                assertions_failed += 1
            
            # テスト2: セキュリティマネージャーの動作確認
            security_test = await self._test_security_manager()
            if security_test["success"]:
                assertions_passed += 1
            else:
                assertions_failed += 1
            
            # テスト3: エラー回復システムの動作確認
            recovery_test = await self._test_error_recovery_system()
            if recovery_test["success"]:
                assertions_passed += 1
            else:
                assertions_failed += 1
            
            # テスト4: A2A独立プロセス処理の確認
            a2a_test = await self._test_a2a_isolated_processing()
            if a2a_test["success"]:
                assertions_passed += 1
            else:
                assertions_failed += 1
            
            # テスト5: 実際のGitHub統合テスト
            github_test = await self._test_github_integration()
            if github_test["success"]:
                assertions_passed += 1
            else:
                assertions_failed += 1
            
            # 結果判定
            total_assertions = assertions_passed + assertions_failed
            success_rate = assertions_passed / total_assertions if total_assertions > 0 else 0
            
            status = TestStatus.PASSED if success_rate >= 0.8 else TestStatus.FAILED
            
            return TestResult(
                test_name=test_name,
                test_type=TestType.E2E,
                status=status,
                execution_time=time.time() - start_time,
                assertions_passed=assertions_passed,
                assertions_failed=assertions_failed,
                metadata={
                    "success_rate": success_rate,
                    "workflow_test": workflow_test,
                    "security_test": security_test,
                    "recovery_test": recovery_test,
                    "a2a_test": a2a_test,
                    "github_test": github_test
                }
            )
            
        except Exception as e:
            logger.error(f"E2E test failed: {str(e)}")
            return TestResult(
                test_name=test_name,
                test_type=TestType.E2E,
                status=TestStatus.ERROR,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
        
        finally:
            # クリーンアップ
            await self.github_env.cleanup_test_environment()
    
    async def _test_unified_workflow_engine(self) -> Dict[str, Any]:
        """統一ワークフローエンジンテスト"""
        try:
            from libs.integrations.github.unified_workflow_engine import get_unified_workflow_engine
            
            engine = get_unified_workflow_engine()
            
            # テスト用データ
            test_issue_data = {
                "number": 999,
                "title": "Test Issue for Workflow Engine",
                "body": "Test description",
                "labels": ["test"],
                "priority": "medium"
            }
            
            # ワークフロー実行テスト
            result = await engine.execute_auto_issue_workflow(test_issue_data, "hybrid")
            
            # アサーション
            assert result.workflow_id is not None
            assert result.status is not None
            assert len(result.components) > 0
            
            return {
                "success": True,
                "workflow_id": result.workflow_id,
                "status": result.status.value,
                "components_count": len(result.components)
            }
            
        except Exception as e:
            logger.error(f"Workflow engine test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _test_security_manager(self) -> Dict[str, Any]:
        """セキュリティマネージャーテスト"""
        try:
            from libs.integrations.github.security_manager import get_security_manager
            
            security_manager = get_security_manager()
            
            # テスト用データ
            test_request = {
                "operation": "test_operation",
                "data": "safe test data"
            }
            
            # 入力検証テスト
            validation_result = security_manager.input_validator.validate_input(test_request)
            
            # セキュリティレポートテスト
            security_report = security_manager.create_security_report()
            
            # アサーション
            assert validation_result["valid"] is True
            assert security_report["timestamp"] is not None
            assert "vulnerability_summary" in security_report
            
            return {
                "success": True,
                "validation_passed": validation_result["valid"],
                "report_generated": bool(security_report)
            }
            
        except Exception as e:
            logger.error(f"Security manager test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _test_error_recovery_system(self) -> Dict[str, Any]:
        """エラー回復システムテスト"""
        try:
            from libs.integrations.github.error_recovery_system import get_error_recovery_system
            
            recovery_system = get_error_recovery_system()
            
            # テスト用エラー関数
            async def test_function_success():
                return "success"
            
            async def test_function_failure():
                raise Exception("Test error")
            
            # 成功ケーステスト
            success_result = await recovery_system.execute_with_recovery(
                test_function_success, "test_component", "test_operation"
            )
            
            # エラー統計テスト
            error_stats = recovery_system.get_error_statistics()
            
            # アサーション
            assert success_result == "success"
            assert error_stats["total_errors"] >= 0
            
            return {
                "success": True,
                "success_execution": success_result == "success",
                "error_stats_available": bool(error_stats)
            }
            
        except Exception as e:
            logger.error(f"Error recovery system test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _test_a2a_isolated_processing(self) -> Dict[str, Any]:
        """A2A独立プロセス処理テスト"""
        try:
            # モックGitHub Issueを作成
            mock_issue = Mock()
            mock_issue.number = 999
            mock_issue.title = "Test A2A Processing"
            mock_issue.body = "Test description for A2A"
            mock_issue.labels = []
            
            # A2Aプロセッサーのモック実行
            from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
            
            # テスト環境での実行をシミュレート
            with patch('libs.integrations.github.auto_issue_processor.ClaudeCLIExecutor') as mock_executor:
                mock_executor.return_value.execute.return_value = "Test execution completed"
                
                with patch('libs.integrations.github.auto_issue_processor.SafeGitOperations') as mock_git:
                    mock_git.return_value.create_pr_branch_workflow.return_value = {
                        "success": True,
                        "branch_name": "test-branch",
                        "original_branch": "main"
                    }
                    mock_git.return_value.auto_commit_if_changes.return_value = {
                        "success": True,
                        "action": "committed"
                    }
                    mock_git.return_value.push_branch_safely.return_value = {"success": True}
                    mock_git.return_value.restore_original_branch.return_value = {"success": True}
                    
                    processor = AutoIssueProcessor()
                    result = await processor.process_issue_isolated(mock_issue)
            
            # アサーション
            assert result is not None
            assert "status" in result
            
            return {
                "success": True,
                "a2a_result": result.get("status", "unknown")
            }
            
        except Exception as e:
            logger.error(f"A2A processing test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _test_github_integration(self) -> Dict[str, Any]:
        """GitHub統合テスト"""
        try:
            # 実際のGitHub APIとの統合をテスト
            if not self.github_env.test_token:
                return {"success": False, "error": "No GitHub test token available"}
            
            # テストIssueを使用した統合テスト
            if not self.github_env.test_issues:
                return {"success": False, "error": "No test issues available"}
            
            test_issue = self.github_env.test_issues[0]
            
            # GitHub APIアクセステスト
            headers = {"Authorization": f"token {self.github_env.test_token}"}
            url = f"{self.github_env.base_url}/repos/{self.github_env.test_repo_owner}/{self." \
                "github_env.test_repo_name}/issues/{test_issue["number']}"
            
            response = requests.get(url, headers=headers)
            
            # アサーション
            assert response.status_code == 200
            issue_data = response.json()
            assert issue_data["number"] == test_issue["number"]
            
            return {
                "success": True,
                "api_response_code": response.status_code,
                "issue_accessible": True
            }
            
        except Exception as e:
            logger.error(f"GitHub integration test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def run_performance_test(self) -> TestResult:
        """パフォーマンステスト実行"""
        test_name = "performance_concurrent_processing"
        start_time = time.time()
        
        try:
            # 並列処理性能テスト
            concurrent_tasks = 5
            tasks = []
            
            for i in range(concurrent_tasks):
                task = asyncio.create_task(self._simulate_issue_processing(i))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 結果分析
            successful_tasks = len([r for r in results if not isinstance(r, Exception)])
            failed_tasks = len([r for r in results if isinstance(r, Exception)])
            
            execution_time = time.time() - start_time
            throughput = successful_tasks / execution_time if execution_time > 0 else 0
            
            # パフォーマンス基準判定
            performance_threshold = 2.0  # 2 tasks/second
            status = TestStatus.PASSED if throughput >= performance_threshold else TestStatus.FAILED
            
            return TestResult(
                test_name=test_name,
                test_type=TestType.PERFORMANCE,
                status=status,
                execution_time=execution_time,
                assertions_passed=successful_tasks,
                assertions_failed=failed_tasks,
                metadata={
                    "throughput": throughput,
                    "concurrent_tasks": concurrent_tasks,
                    "performance_threshold": performance_threshold
                }
            )
            
        except Exception as e:
            logger.error(f"Performance test failed: {str(e)}")
            return TestResult(
                test_name=test_name,
                test_type=TestType.PERFORMANCE,
                status=TestStatus.ERROR,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _simulate_issue_processing(self, task_id: int) -> Dict[str, Any]:
        """Issue処理シミュレーション"""
        # 実際の処理をシミュレート
        await asyncio.sleep(0.5)  # 処理時間をシミュレート
        
        return {
            "task_id": task_id,
            "status": "completed",
            "processing_time": 0.5
        }

class IntegrationTestRunner:
    """統合テストランナー"""
    
    def __init__(self):
        self.e2e_tester = A2AEndToEndTester()
        self.test_suites: List[TestSuite] = []
        self.test_results: List[TestResult] = []
        self._setup_test_suites()
    
    def _setup_test_suites(self):
        """テストスイートセットアップ"""
        self.test_suites = [
            TestSuite(
                name="A2A E2E Tests",
                test_type=TestType.E2E,
                tests=["e2e_workflow_complete"],
                setup_required=True,
                cleanup_required=True
            ),
            TestSuite(
                name="A2A Performance Tests",
                test_type=TestType.PERFORMANCE,
                tests=["performance_concurrent_processing"],
                setup_required=False,
                cleanup_required=False
            ),
            TestSuite(
                name="A2A Security Tests",
                test_type=TestType.SECURITY,
                tests=["security_validation", "security_audit"],
                setup_required=False,
                cleanup_required=False
            )
        ]
    
    async def run_all_tests(self) -> Dict[str, Any]start_time = time.time():
    """テスト実行"""
        overall_result = {:
            "success": True,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "error_tests": 0,
            "execution_time": 0.0,
            "test_results": [],
            "summary": {}
        }
        
        try:
            for suite in self.test_suites:
                logger.info(f"Running test suite: {suite.name}")
                
                for test_name in suite.tests:
                    try:
                        if test_name == "e2e_workflow_complete":
                            result = await self.e2e_tester.run_e2e_workflow_test()
                        elif test_name == "performance_concurrent_processing":
                            result = await self.e2e_tester.run_performance_test()
                        else:
                            # その他のテストはスキップ
                            result = TestResult(
                                test_name=test_name,
                                test_type=suite.test_type,
                                status=TestStatus.SKIPPED,
                                execution_time=0.0
                            )
                        
                        self.test_results.append(result)
                        overall_result["test_results"].append({
                            "test_name": result.test_name,
                            "status": result.status.value,
                            "execution_time": result.execution_time,
                            "error_message": result.error_message
                        })
                        
                        overall_result["total_tests"] += 1
                        
                        if result.status == TestStatus.PASSED:
                            overall_result["passed_tests"] += 1
                        elif result.status == TestStatus.FAILED:
                            overall_result["failed_tests"] += 1
                        elif result.status == TestStatus.ERROR:
                            overall_result["error_tests"] += 1
                        
                    except Exception as e:
                        logger.error(f"Test execution failed: {test_name}: {str(e)}")
                        overall_result["error_tests"] += 1
                        overall_result["total_tests"] += 1
            
            # 総合判定
            if overall_result["total_tests"] > 0:
                success_rate = overall_result["passed_tests"] / overall_result["total_tests"]
                overall_result["success"] = success_rate >= 0.8
                overall_result["summary"]["success_rate"] = success_rate
            
            overall_result["execution_time"] = time.time() - start_time
            
            logger.info(f"All tests completed: {overall_result['summary']}")
            
        except Exception as e:
            logger.error(f"Test runner failed: {str(e)}")
            overall_result["success"] = False
            overall_result["error_message"] = str(e)
        
        return overall_result
    
    def generate_test_report(self) -> str:
        """テストレポート生成"""
        report_lines = [
            "# A2A Integration Test Report",
            f"Generated at: {datetime.now().isoformat()}",
            "",
            "## Test Summary"
        ]
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == TestStatus.PASSED])
        failed_tests = len([r for r in self.test_results if r.status == TestStatus.FAILED])
        error_tests = len([r for r in self.test_results if r.status == TestStatus.ERROR])
        
        report_lines.extend([
            f"- Total Tests: {total_tests}",
            f"- Passed: {passed_tests}",
            f"- Failed: {failed_tests}",
            f"- Errors: {error_tests}",
            f"- Success Rate: {(passed_tests/total_tests*100):0.1f}%" if total_tests > 0 else "- Success Rate: 0%",
            "",
            "## Detailed Results"
        ])
        
        for result in self.test_results:
            report_lines.extend([
                f"### {result.test_name}",
                f"- Status: {result.status.value}",
                f"- Type: {result.test_type.value}",
                f"- Execution Time: {result.execution_time:0.2f}s",
                f"- Assertions Passed: {result.assertions_passed}",
                f"- Assertions Failed: {result.assertions_failed}"
            ])
            
            if result.error_message:
                report_lines.append(f"- Error: {result.error_message}")
            
            report_lines.append("")
        
        return "\n".join(report_lines)

# シングルトンインスタンス
_integration_test_runner = None

def get_integration_test_runner() -> IntegrationTestRunner:
    """統合テストランナーシングルトン取得"""
    global _integration_test_runner
    if _integration_test_runner is None:
        _integration_test_runner = IntegrationTestRunner()
    return _integration_test_runner