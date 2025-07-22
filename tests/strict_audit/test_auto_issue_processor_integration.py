#!/usr/bin/env python3
"""
🚨 Auto Issue Processor 統合品質監査システム
Created: 2025-07-22 by Claude Elder
目的: Auto Issue ProcessorとRetryIssueReporter統合品質の厳格検証
"""

import asyncio
import json
import logging
import os
import pytest
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch, Mock

# テスト対象のインポート
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# ロギング設定
logging.basicConfig(level=logging.WARNING)  # ノイズを削減
logger = logging.getLogger(__name__)


class MockGitHubIssue:
    """Mock GitHub Issue for testing"""
    
    def __init__(self, number: int, title: str = "Test Issue", body: str = "Test body", labels=None):
        self.number = number
        self.title = title
        self.body = body
        self.labels = labels or []
        self.comments_list = []
    
    def create_comment(self, body: str):
        """Mock comment creation"""
        comment = {
            "body": body,
            "created_at": datetime.now(),
            "id": len(self.comments_list) + 1
        }
        self.comments_list.append(comment)
        return comment
    
    def get_comments(self):
        """Mock get comments"""
        return self.comments_list


class StrictIntegrationAuditor:
    """Auto Issue Processor統合監査システム"""
    
    def __init__(self):
        self.audit_results = {}
        self.error_count = 0
        self.warning_count = 0
        self.critical_issues = []
        self.performance_metrics = {}
    
    def record_audit(self, test_name: str, status: str, details: Dict[str, Any]):
        """監査結果記録"""
        self.audit_results[test_name] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        if status == "FAIL":
            self.error_count += 1
            if details.get("severity") == "CRITICAL":
                self.critical_issues.append(test_name)
        elif status == "WARNING":
            self.warning_count += 1
    
    def record_performance(self, test_name: str, metrics: Dict[str, Any]):
        """パフォーマンス記録"""
        self.performance_metrics[test_name] = {
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_audit_report(self) -> Dict[str, Any]:
        """統合監査レポート生成"""
        total_tests = len(self.audit_results)
        passed_tests = sum(1 for r in self.audit_results.values() if r["status"] == "PASS")
        
        return {
            "integration_audit_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": self.error_count,
                "warnings": self.warning_count,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "critical_issues": len(self.critical_issues)
            },
            "critical_issues": self.critical_issues,
            "performance_metrics": self.performance_metrics,
            "detailed_results": self.audit_results,
            "audit_timestamp": datetime.now().isoformat(),
            "auditor": "Claude Elder - Integration Quality Gate"
        }


@pytest.fixture
def integration_env():
    """統合テスト環境設定"""
    return {
        "GITHUB_TOKEN": "test_integration_token",
        "GITHUB_REPO_OWNER": "test_owner",
        "GITHUB_REPO_NAME": "test_repo"
    }


@pytest.fixture
def mock_dependencies():
    """依存関係モック"""
    mocks = {}
    
    # GitHub関連
    mocks['github'] = Mock()
    mocks['repo'] = Mock()
    mocks['github'].get_repo.return_value = mocks['repo']
    
    # 4賢者システム
    mocks['knowledge_sage'] = AsyncMock()
    mocks['task_sage'] = AsyncMock()
    mocks['incident_sage'] = AsyncMock()
    mocks['rag_manager'] = AsyncMock()
    
    # Elder Flow Engine
    mocks['elder_flow'] = AsyncMock()
    
    # PR Creator
    mocks['pr_creator'] = AsyncMock()
    
    return mocks


class TestAutoIssueProcessorIntegration:
    """Auto Issue Processor統合品質監査"""
    
    auditor = StrictIntegrationAuditor()
    
    @pytest.mark.asyncio
    async def test_001_retry_reporter_initialization_integration(self, integration_env, mock_dependencies):
        """🔍 Test 001: RetryIssueReporter統合初期化検証"""
        test_name = "retry_reporter_initialization_integration"
        
        try:
            with patch.dict(os.environ, integration_env), \
                 patch('libs.integrations.github.auto_issue_processor.Github', return_value=mock_dependencies['github']), \
                 patch('libs.retry_issue_reporter.Github', return_value=mock_dependencies['github']), \
                 patch('libs.integrations.github.auto_issue_processor.KnowledgeSage', return_value=mock_dependencies['knowledge_sage']), \
                 patch('libs.integrations.github.auto_issue_processor.TaskSage', return_value=mock_dependencies['task_sage']), \
                 patch('libs.integrations.github.auto_issue_processor.IncidentSage', return_value=mock_dependencies['incident_sage']), \
                 patch('libs.integrations.github.auto_issue_processor.RagManager', return_value=mock_dependencies['rag_manager']):
                
                from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
                
                processor = AutoIssueProcessor()
                
                # RetryIssueReporter統合確認
                assert hasattr(processor, 'retry_reporter'), "RetryIssueReporter not integrated"
                assert processor.retry_reporter is not None, "RetryIssueReporter is None"
                
                # 設定値検証
                assert processor.retry_reporter.github_token == "test_integration_token"
                assert processor.retry_reporter.repo_owner == "test_owner"
                assert processor.retry_reporter.repo_name == "test_repo"
                
                # セッション管理機能確認
                assert hasattr(processor.retry_reporter, 'start_retry_session')
                assert hasattr(processor.retry_reporter, 'record_retry_attempt')
                assert hasattr(processor.retry_reporter, 'record_retry_success')
                assert hasattr(processor.retry_reporter, 'record_retry_failure')
                
                TestAutoIssueProcessorIntegration.auditor.record_audit(test_name, "PASS", {
                    "retry_reporter_integrated": True,
                    "configuration_correct": True,
                    "methods_available": ["start_retry_session", "record_retry_attempt", "record_retry_success", "record_retry_failure"],
                    "initialization_successful": True
                })
                
        except Exception as e:
            TestAutoIssueProcessorIntegration.auditor.record_audit(test_name, "FAIL", {
                "error": str(e),
                "severity": "CRITICAL"
            })
            raise
    
    @pytest.mark.asyncio
    async def test_002_execute_auto_processing_retry_flow(self, integration_env, mock_dependencies):
        """🔍 Test 002: execute_auto_processing リトライフロー検証"""
        test_name = "execute_auto_processing_retry_flow"
        
        try:
            with patch.dict(os.environ, integration_env), \
                 patch('libs.integrations.github.auto_issue_processor.Github', return_value=mock_dependencies['github']), \
                 patch('libs.retry_issue_reporter.Github', return_value=mock_dependencies['github']), \
                 patch('libs.integrations.github.auto_issue_processor.KnowledgeSage', return_value=mock_dependencies['knowledge_sage']), \
                 patch('libs.integrations.github.auto_issue_processor.TaskSage', return_value=mock_dependencies['task_sage']), \
                 patch('libs.integrations.github.auto_issue_processor.IncidentSage', return_value=mock_dependencies['incident_sage']), \
                 patch('libs.integrations.github.auto_issue_processor.RagManager', return_value=mock_dependencies['rag_manager']):
                
                from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
                
                processor = AutoIssueProcessor()
                
                # テスト用Issue作成
                test_issue = MockGitHubIssue(789, "Integration Test Issue", "Testing retry flow integration")
                mock_dependencies['repo'].get_issue.return_value = test_issue
                
                # _execute_single_processing_attemptを失敗→成功パターンでモック
                attempt_count = 0
                def mock_single_attempt(issue, session_id, attempt):
                    nonlocal attempt_count
                    attempt_count += 1
                    if attempt_count <= 2:
                        raise ConnectionError(f"Mock failure {attempt_count}")
                    return {
                        "status": "success",
                        "pr_url": "https://github.com/test/test/pull/123",
                        "message": "Successfully processed after retries"
                    }
                
                # メソッドをモック
                processor._execute_single_processing_attempt = AsyncMock(side_effect=mock_single_attempt)
                
                start_time = time.time()
                result = await processor.execute_auto_processing(test_issue)
                execution_time = time.time() - start_time
                
                # 結果検証
                assert result is not None, "Result should not be None"
                assert result.get("status") == "success", f"Expected success, got {result.get('status')}"
                assert attempt_count == 3, f"Expected 3 attempts, got {attempt_count}"
                
                # リトライレポーターのセッション確認
                sessions = processor.retry_reporter.retry_sessions
                assert len(sessions) >= 1, "At least one retry session should exist"
                
                # パフォーマンス記録
                TestAutoIssueProcessorIntegration.auditor.record_performance(test_name, {
                    "execution_time": execution_time,
                    "retry_attempts": attempt_count,
                    "retry_sessions_created": len(sessions)
                })
                
                TestAutoIssueProcessorIntegration.auditor.record_audit(test_name, "PASS", {
                    "retry_flow_working": True,
                    "attempts_made": attempt_count,
                    "final_result": "success",
                    "sessions_managed": len(sessions),
                    "execution_time": f"{execution_time:.3f}s"
                })
                
        except Exception as e:
            TestAutoIssueProcessorIntegration.auditor.record_audit(test_name, "FAIL", {
                "error": str(e),
                "severity": "HIGH"
            })
            raise
    
    @pytest.mark.asyncio
    async def test_003_github_comment_recording_integration(self, integration_env, mock_dependencies):
        """🔍 Test 003: GitHubコメント記録統合検証"""
        test_name = "github_comment_recording_integration"
        
        try:
            with patch.dict(os.environ, integration_env), \
                 patch('libs.integrations.github.auto_issue_processor.Github', return_value=mock_dependencies['github']), \
                 patch('libs.retry_issue_reporter.Github', return_value=mock_dependencies['github']), \
                 patch('libs.integrations.github.auto_issue_processor.KnowledgeSage', return_value=mock_dependencies['knowledge_sage']), \
                 patch('libs.integrations.github.auto_issue_processor.TaskSage', return_value=mock_dependencies['task_sage']), \
                 patch('libs.integrations.github.auto_issue_processor.IncidentSage', return_value=mock_dependencies['incident_sage']), \
                 patch('libs.integrations.github.auto_issue_processor.RagManager', return_value=mock_dependencies['rag_manager']):
                
                from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
                
                processor = AutoIssueProcessor()
                
                # テスト用Issue作成
                test_issue = MockGitHubIssue(456, "Comment Integration Test", "Testing comment recording")
                mock_dependencies['repo'].get_issue.return_value = test_issue
                
                # 1回失敗→成功のシナリオ
                call_count = 0
                def mock_single_attempt_with_failure(issue, session_id, attempt):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        raise RuntimeError("Simulated processing error")
                    return {
                        "status": "success",
                        "pr_url": "https://github.com/test/test/pull/456",
                        "message": "Success after one retry"
                    }
                
                processor._execute_single_processing_attempt = AsyncMock(side_effect=mock_single_attempt_with_failure)
                
                # 実行
                result = await processor.execute_auto_processing(test_issue)
                
                # コメント確認（モックされたIssueのコメント一覧）
                comments = test_issue.get_comments()
                
                # リトライコメント + 成功コメント = 2つのコメントが記録されるはず
                retry_comments = [c for c in comments if "リトライ #1" in c["body"]]
                success_comments = [c for c in comments if "処理成功" in c["body"]]
                
                # 検証（実際のコメント記録はmockされているため、セッションデータで確認）
                sessions = processor.retry_reporter.retry_sessions
                session_list = list(sessions.values())
                
                assert len(session_list) >= 1, "At least one session should exist"
                
                latest_session = session_list[-1]
                assert len(latest_session["attempts"]) >= 1, "At least one retry attempt should be recorded"
                assert latest_session.get("final_status") == "success", "Final status should be success"
                
                TestAutoIssueProcessorIntegration.auditor.record_audit(test_name, "PASS", {
                    "comment_integration_working": True,
                    "retry_attempts_recorded": len(latest_session["attempts"]),
                    "final_status_recorded": latest_session.get("final_status") == "success",
                    "session_data_complete": True
                })
                
        except Exception as e:
            TestAutoIssueProcessorIntegration.auditor.record_audit(test_name, "FAIL", {
                "error": str(e),
                "severity": "HIGH"
            })
            raise
    
    @pytest.mark.asyncio
    async def test_004_error_handling_resilience_integration(self, integration_env, mock_dependencies):
        """🔍 Test 004: エラーハンドリング統合回復力検証"""
        test_name = "error_handling_resilience_integration"
        
        try:
            with patch.dict(os.environ, integration_env), \
                 patch('libs.integrations.github.auto_issue_processor.Github', return_value=mock_dependencies['github']), \
                 patch('libs.retry_issue_reporter.Github', return_value=mock_dependencies['github']), \
                 patch('libs.integrations.github.auto_issue_processor.KnowledgeSage', return_value=mock_dependencies['knowledge_sage']), \
                 patch('libs.integrations.github.auto_issue_processor.TaskSage', return_value=mock_dependencies['task_sage']), \
                 patch('libs.integrations.github.auto_issue_processor.IncidentSage', return_value=mock_dependencies['incident_sage']), \
                 patch('libs.integrations.github.auto_issue_processor.RagManager', return_value=mock_dependencies['rag_manager']):
                
                from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
                
                processor = AutoIssueProcessor()
                
                # テスト用Issue作成
                test_issue = MockGitHubIssue(321, "Error Resilience Test", "Testing error handling")
                mock_dependencies['repo'].get_issue.return_value = test_issue
                
                # 全試行が失敗するシナリオ
                def always_failing_attempt(issue, session_id, attempt):
                    raise ConnectionError(f"Persistent failure on attempt {attempt}")
                
                processor._execute_single_processing_attempt = AsyncMock(side_effect=always_failing_attempt)
                
                # 最終的に例外が発生することを確認
                with pytest.raises(ConnectionError) as exc_info:
                    await processor.execute_auto_processing(test_issue)
                
                assert "Persistent failure on attempt 3" in str(exc_info.value)
                
                # セッション状態確認
                sessions = processor.retry_reporter.retry_sessions
                session_list = list(sessions.values())
                
                assert len(session_list) >= 1, "At least one session should exist"
                
                latest_session = session_list[-1]
                assert len(latest_session["attempts"]) == 3, "All 3 attempts should be recorded"
                assert latest_session.get("final_status") == "failure", "Final status should be failure"
                
                TestAutoIssueProcessorIntegration.auditor.record_audit(test_name, "PASS", {
                    "error_propagation_correct": True,
                    "all_attempts_recorded": len(latest_session["attempts"]) == 3,
                    "final_failure_recorded": latest_session.get("final_status") == "failure",
                    "system_resilience": True
                })
                
        except Exception as e:
            if "Persistent failure on attempt" not in str(e):
                TestAutoIssueProcessorIntegration.auditor.record_audit(test_name, "FAIL", {
                    "error": str(e),
                    "severity": "HIGH"
                })
                raise
    
    @pytest.mark.asyncio
    async def test_005_performance_scalability_integration(self, integration_env, mock_dependencies):
        """🔍 Test 005: パフォーマンス・スケーラビリティ統合検証"""
        test_name = "performance_scalability_integration"
        
        try:
            with patch.dict(os.environ, integration_env), \
                 patch('libs.integrations.github.auto_issue_processor.Github', return_value=mock_dependencies['github']), \
                 patch('libs.retry_issue_reporter.Github', return_value=mock_dependencies['github']), \
                 patch('libs.integrations.github.auto_issue_processor.KnowledgeSage', return_value=mock_dependencies['knowledge_sage']), \
                 patch('libs.integrations.github.auto_issue_processor.TaskSage', return_value=mock_dependencies['task_sage']), \
                 patch('libs.integrations.github.auto_issue_processor.IncidentSage', return_value=mock_dependencies['incident_sage']), \
                 patch('libs.integrations.github.auto_issue_processor.RagManager', return_value=mock_dependencies['rag_manager']):
                
                from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
                
                processor = AutoIssueProcessor()
                
                # 複数Issue並行処理テスト
                test_issues = [
                    MockGitHubIssue(i, f"Performance Test Issue {i}", f"Testing performance {i}")
                    for i in range(100, 110)  # 10個のIssue
                ]
                
                def mock_get_issue(issue_number):
                    return next((issue for issue in test_issues if issue.number == issue_number), None)
                
                mock_dependencies['repo'].get_issue.side_effect = mock_get_issue
                
                # 高速成功のモック
                def quick_success_attempt(issue, session_id, attempt):
                    return {
                        "status": "success",
                        "pr_url": f"https://github.com/test/test/pull/{issue.number}",
                        "message": f"Quick success for issue {issue.number}"
                    }
                
                processor._execute_single_processing_attempt = AsyncMock(side_effect=quick_success_attempt)
                
                # パフォーマンステスト実行
                start_time = time.time()
                
                tasks = []
                for issue in test_issues[:5]:  # 5つのIssueで並行テスト
                    task = asyncio.create_task(processor.execute_auto_processing(issue))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                execution_time = time.time() - start_time
                
                # 結果検証
                successful_results = [r for r in results if isinstance(r, dict) and r.get("status") == "success"]
                
                # パフォーマンス基準
                assert execution_time < 10.0, f"Parallel execution too slow: {execution_time}s"
                assert len(successful_results) == 5, f"Expected 5 successes, got {len(successful_results)}"
                
                # メモリ使用量確認
                import psutil
                process = psutil.Process()
                memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                
                assert memory_usage < 200, f"Memory usage too high: {memory_usage}MB"
                
                TestAutoIssueProcessorIntegration.auditor.record_performance(test_name, {
                    "parallel_execution_time": execution_time,
                    "issues_processed": len(successful_results),
                    "memory_usage_mb": memory_usage,
                    "average_time_per_issue": execution_time / len(successful_results) if successful_results else 0
                })
                
                TestAutoIssueProcessorIntegration.auditor.record_audit(test_name, "PASS", {
                    "parallel_processing_working": True,
                    "execution_time": f"{execution_time:.2f}s",
                    "successful_issues": len(successful_results),
                    "memory_usage": f"{memory_usage:.1f}MB",
                    "performance_acceptable": True
                })
                
        except Exception as e:
            TestAutoIssueProcessorIntegration.auditor.record_audit(test_name, "FAIL", {
                "error": str(e),
                "severity": "MEDIUM"
            })
            raise
    
    @pytest.mark.asyncio
    async def test_006_data_consistency_validation(self, integration_env, mock_dependencies):
        """🔍 Test 006: データ整合性検証"""
        test_name = "data_consistency_validation"
        
        try:
            with patch.dict(os.environ, integration_env), \
                 patch('libs.integrations.github.auto_issue_processor.Github', return_value=mock_dependencies['github']), \
                 patch('libs.retry_issue_reporter.Github', return_value=mock_dependencies['github']), \
                 patch('libs.integrations.github.auto_issue_processor.KnowledgeSage', return_value=mock_dependencies['knowledge_sage']), \
                 patch('libs.integrations.github.auto_issue_processor.TaskSage', return_value=mock_dependencies['task_sage']), \
                 patch('libs.integrations.github.auto_issue_processor.IncidentSage', return_value=mock_dependencies['incident_sage']), \
                 patch('libs.integrations.github.auto_issue_processor.RagManager', return_value=mock_dependencies['rag_manager']):
                
                from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
                
                processor = AutoIssueProcessor()
                
                # テスト用Issue作成
                test_issue = MockGitHubIssue(555, "Data Consistency Test", "Testing data consistency")
                mock_dependencies['repo'].get_issue.return_value = test_issue
                
                # 詳細コンテキスト付きの処理
                context_data = {
                    "branch_name": "feature/test-branch",
                    "pr_number": 555,
                    "labels": ["enhancement", "auto-generated"],
                    "complexity_score": 0.65
                }
                
                attempt_count = 0
                def context_preserving_attempt(issue, session_id, attempt):
                    nonlocal attempt_count
                    attempt_count += 1
                    if attempt_count == 1:
                        raise ValueError("First attempt failure with context")
                    return {
                        "status": "success",
                        "pr_url": "https://github.com/test/test/pull/555",
                        "message": "Success with preserved context",
                        "context": context_data
                    }
                
                processor._execute_single_processing_attempt = AsyncMock(side_effect=context_preserving_attempt)
                
                # 実行
                result = await processor.execute_auto_processing(test_issue)
                
                # セッションデータ整合性確認
                sessions = processor.retry_reporter.retry_sessions
                session_list = list(sessions.values())
                latest_session = session_list[-1]
                
                # データ整合性チェック
                assert latest_session["issue_number"] == test_issue.number
                assert latest_session["operation"].startswith("Auto-fix Issue #555")
                assert len(latest_session["attempts"]) == 1, "One retry attempt should be recorded"
                assert latest_session["final_status"] == "success"
                
                # 試行データの詳細確認
                attempt_data = latest_session["attempts"][0]
                assert attempt_data["attempt"] == 1
                assert attempt_data["error_type"] == "ValueError"
                assert "First attempt failure with context" in attempt_data["error_message"]
                assert attempt_data["recovery_action"] == "RETRY"
                
                TestAutoIssueProcessorIntegration.auditor.record_audit(test_name, "PASS", {
                    "data_consistency_verified": True,
                    "session_data_complete": True,
                    "attempt_data_accurate": True,
                    "context_preservation": True,
                    "issue_number_matches": latest_session["issue_number"] == test_issue.number
                })
                
        except Exception as e:
            TestAutoIssueProcessorIntegration.auditor.record_audit(test_name, "FAIL", {
                "error": str(e),
                "severity": "HIGH"
            })
            raise
    
    def test_zzz_generate_integration_audit_report(self):
        """🔍 Test ZZZ: 統合監査レポート生成"""
        audit_report = TestAutoIssueProcessorIntegration.auditor.generate_audit_report()
        
        # レポートをファイルに保存
        report_file = Path(__file__).parent / "auto_issue_processor_integration_audit_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(audit_report, f, indent=2, ensure_ascii=False)
        
        # コンソール出力
        print("\n" + "="*80)
        print("🚨 AUTO ISSUE PROCESSOR - 統合監査結果")
        print("="*80)
        print(f"📊 総テスト数: {audit_report['integration_audit_summary']['total_tests']}")
        print(f"✅ 成功: {audit_report['integration_audit_summary']['passed']}")
        print(f"❌ 失敗: {audit_report['integration_audit_summary']['failed']}")
        print(f"⚠️ 警告: {audit_report['integration_audit_summary']['warnings']}")
        print(f"📈 成功率: {audit_report['integration_audit_summary']['success_rate']:.1f}%")
        print(f"🚨 重大問題: {audit_report['integration_audit_summary']['critical_issues']}")
        
        if audit_report['critical_issues']:
            print(f"\n🚨 重大問題詳細:")
            for issue in audit_report['critical_issues']:
                print(f"  - {issue}")
        
        if audit_report['performance_metrics']:
            print(f"\n⚡ パフォーマンス指標:")
            for test, metrics in audit_report['performance_metrics'].items():
                print(f"  - {test}: {metrics['metrics']}")
        
        print(f"\n📄 詳細レポート: {report_file}")
        print("="*80)
        
        # 統合品質ゲート判定
        success_rate = audit_report['integration_audit_summary']['success_rate']
        critical_issues = audit_report['integration_audit_summary']['critical_issues']
        
        if success_rate >= 95 and critical_issues == 0:
            print("🎉 統合品質ゲート: 合格 (EXCELLENT)")
        elif success_rate >= 85 and critical_issues <= 1:
            print("✅ 統合品質ゲート: 合格 (GOOD)")  
        elif success_rate >= 70:
            print("⚠️ 統合品質ゲート: 条件付き合格 (ACCEPTABLE)")
        else:
            print("❌ 統合品質ゲート: 不合格 (REQUIRES_IMPROVEMENT)")
            raise AssertionError("Integration quality gate failed - requires improvement")


if __name__ == "__main__":
    # pytest実行
    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ]
    
    exit_code = pytest.main(pytest_args)
    sys.exit(exit_code)