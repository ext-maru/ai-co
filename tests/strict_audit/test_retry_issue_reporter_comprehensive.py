#!/usr/bin/env python3
"""
🚨 RetryIssueReporter 厳格テスト・監査システム
Created: 2025-07-22 by Claude Elder
目的: リトライシステムの包括的品質検証
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
from unittest.mock import AsyncMock, MagicMock, patch

# テスト対象のインポート
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from libs.retry_issue_reporter import RetryIssueReporter, with_retry_reporting

# ロギング設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class StrictRetryReporterAuditor:
    """厳格なRetryIssueReporter監査システム"""
    
    def __init__(self):
        self.audit_results = {}
        self.error_count = 0
        self.warning_count = 0
        self.critical_issues = []
    
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
    
    def generate_audit_report(self) -> Dict[str, Any]:
        """監査レポート生成"""
        total_tests = len(self.audit_results)
        passed_tests = sum(1 for r in self.audit_results.values() if r["status"] == "PASS")
        
        return {
            "audit_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": self.error_count,
                "warnings": self.warning_count,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "critical_issues": len(self.critical_issues)
            },
            "critical_issues": self.critical_issues,
            "detailed_results": self.audit_results,
            "audit_timestamp": datetime.now().isoformat(),
            "auditor": "Claude Elder - Strict Quality Gate"
        }


class MockGitHubRepo:
    """MockGitHubリポジトリ（テスト用）"""
    
    def __init__(self):
        self.issues = {}
        self.comments = {}
    
    def get_issue(self, issue_number: int):
        """Issue取得"""
        if issue_number not in self.issues:
            self.issues[issue_number] = MockGitHubIssue(issue_number)
        return self.issues[issue_number]


class MockGitHubIssue:
    """MockGitHub Issue"""
    
    def __init__(self, number: int):
        self.number = number
        self.comments_list = []
    
    def create_comment(self, body: str):
        """コメント作成"""
        comment = {
            "body": body,
            "created_at": datetime.now(),
            "id": len(self.comments_list) + 1
        }
        self.comments_list.append(comment)
        return comment
    
    def get_comments(self):
        """コメント一覧取得"""
        return self.comments_list


@pytest.fixture
def mock_github():
    """GitHub Mock Fixture"""
    with patch('libs.retry_issue_reporter.Github') as mock_gh:
        mock_repo = MockGitHubRepo()
        mock_gh.return_value.get_repo.return_value = mock_repo
        yield mock_repo


@pytest.fixture
def audit_env():
    """監査環境設定"""
    return {
        "GITHUB_TOKEN": "test_token_strict_audit",
        "GITHUB_REPO_OWNER": "test_owner",
        "GITHUB_REPO_NAME": "test_repo"
    }


class TestRetryIssueReporterStrictAudit:
    """RetryIssueReporter 厳格監査テストクラス"""
    
    auditor = StrictRetryReporterAuditor()  # クラス変数として共有
    
    def setup_method(self):
        """テストセットアップ"""
        pass
    
    @pytest.mark.asyncio
    async def test_001_initialization_robustness(self, mock_github, audit_env):
        """🔍 Test 001: 初期化堅牢性検証"""
        test_name = "initialization_robustness"
        
        try:
            # 正常初期化
            with patch.dict(os.environ, audit_env):
                reporter = RetryIssueReporter()
                assert reporter.github_token == "test_token_strict_audit"
                assert reporter.repo_owner == "test_owner"
                assert reporter.repo_name == "test_repo"
            
            # 環境変数なしでエラー処理確認
            with patch.dict(os.environ, {}, clear=True):
                try:
                    RetryIssueReporter()
                    assert False, "Should raise ValueError for missing token"
                except ValueError as e:
                    assert "GitHub token is required" in str(e)
            
            # カスタムパラメータ初期化
            reporter_custom = RetryIssueReporter(
                github_token="custom_token",
                repo_owner="custom_owner", 
                repo_name="custom_repo"
            )
            assert reporter_custom.github_token == "custom_token"
            
            TestRetryIssueReporterStrictAudit.auditor.record_audit(test_name, "PASS", {
                "initialization_modes": ["env_vars", "custom_params", "error_handling"],
                "robustness_score": 95
            })
            
        except Exception as e:
            TestRetryIssueReporterStrictAudit.auditor.record_audit(test_name, "FAIL", {
                "error": str(e),
                "severity": "CRITICAL"
            })
            raise
    
    @pytest.mark.asyncio
    async def test_002_session_management_integrity(self, mock_github, audit_env):
        """🔍 Test 002: セッション管理整合性検証"""
        test_name = "session_management_integrity"
        
        try:
            with patch.dict(os.environ, audit_env):
                reporter = RetryIssueReporter()
                
                # 複数セッション同時管理
                sessions = []
                for i in range(10):
                    session_id = reporter.start_retry_session(100 + i, f"operation_{i}")
                    sessions.append(session_id)
                
                # セッションID一意性確認
                assert len(set(sessions)) == 10, "Session IDs must be unique"
                
                # セッション情報整合性確認
                for session_id in sessions:
                    summary = reporter.get_session_summary(session_id)
                    assert summary.get("session_id") == session_id
                    assert "issue_number" in summary
                    assert "operation" in summary
                    assert summary.get("attempt_count") == 0  # 初期状態
                
                # 無効セッションハンドリング
                invalid_summary = reporter.get_session_summary("invalid_session_id")
                assert "error" in invalid_summary
                
                TestRetryIssueReporterStrictAudit.auditor.record_audit(test_name, "PASS", {
                    "concurrent_sessions": 10,
                    "uniqueness_verified": True,
                    "integrity_checks": ["session_id", "issue_number", "operation", "attempt_count"]
                })
                
        except Exception as e:
            TestRetryIssueReporterStrictAudit.auditor.record_audit(test_name, "FAIL", {
                "error": str(e),
                "severity": "HIGH"
            })
            raise
    
    @pytest.mark.asyncio 
    async def test_003_retry_recording_accuracy(self, mock_github, audit_env):
        """🔍 Test 003: リトライ記録精度検証"""
        test_name = "retry_recording_accuracy"
        
        try:
            with patch.dict(os.environ, audit_env):
                reporter = RetryIssueReporter()
                session_id = reporter.start_retry_session(200, "accuracy_test")
                
                # 複数リトライ記録
                test_errors = [
                    ConnectionError("Network timeout"),
                    ValueError("Invalid parameter"),
                    RuntimeError("System error")
                ]
                
                for i, error in enumerate(test_errors, 1):
                    await reporter.record_retry_attempt(
                        session_id=session_id,
                        attempt_number=i,
                        error=error,
                        recovery_action="RETRY",
                        recovery_message=f"Retry attempt {i}",
                        retry_delay=2.0 ** i,
                        context={"test_data": f"value_{i}"}
                    )
                
                # セッション状態検証
                session = reporter.retry_sessions[session_id]
                assert len(session["attempts"]) == 3
                
                # 各試行データ検証
                for i, attempt in enumerate(session["attempts"]):
                    assert attempt["attempt"] == i + 1
                    assert attempt["error_type"] == type(test_errors[i]).__name__
                    assert attempt["error_message"] == str(test_errors[i])
                    assert attempt["recovery_action"] == "RETRY"
                    assert attempt["retry_delay"] == 2.0 ** (i + 1)
                    assert attempt["context"]["test_data"] == f"value_{i + 1}"
                
                # 成功記録
                result = {"status": "success", "data": "test_result"}
                await reporter.record_retry_success(session_id, result)
                
                assert session["final_status"] == "success"
                assert session["result"] == result
                
                TestRetryIssueReporterStrictAudit.auditor.record_audit(test_name, "PASS", {
                    "retry_attempts_recorded": 3,
                    "data_accuracy": 100,
                    "context_preservation": True,
                    "final_status_recorded": True
                })
                
        except Exception as e:
            TestRetryIssueReporterStrictAudit.auditor.record_audit(test_name, "FAIL", {
                "error": str(e),
                "severity": "HIGH"
            })
            raise
    
    @pytest.mark.asyncio
    async def test_004_github_comment_generation_quality(self, mock_github, audit_env):
        """🔍 Test 004: GitHubコメント生成品質検証"""
        test_name = "github_comment_generation_quality"
        
        try:
            with patch.dict(os.environ, audit_env):
                reporter = RetryIssueReporter()
                session_id = reporter.start_retry_session(300, "GitHub comment quality test")
                
                # リトライコメント生成テスト
                error = ConnectionError("Detailed connection error message")
                await reporter.record_retry_attempt(
                    session_id=session_id,
                    attempt_number=1,
                    error=error,
                    recovery_action="RETRY",
                    recovery_message="Network connection failed, retrying with backoff",
                    retry_delay=4.0,
                    context={
                        "branch_name": "test-branch",
                        "pr_number": 123,
                        "additional_info": "test context"
                    }
                )
                
                # コメント品質検証
                issue = mock_github.get_issue(300)
                comments = issue.get_comments()
                
                assert len(comments) == 1, "One comment should be created"
                
                comment_body = comments[0]["body"]
                
                # 必須要素の存在確認
                required_elements = [
                    "Auto Issue Processor リトライ #1",
                    "🕐 時刻",
                    "🔧 操作", 
                    "❌ エラー",
                    "🛠️ 回復アクション",
                    "💬 詳細",
                    "⏰ 次回試行まで",
                    "🌿 ブランチ",
                    "📋 関連PR",
                    "🤖 自動生成"
                ]
                
                missing_elements = []
                for element in required_elements:
                    if element not in comment_body:
                        missing_elements.append(element)
                
                assert len(missing_elements) == 0, f"Missing required elements: {missing_elements}"
                
                # コメント長さ制限確認
                assert len(comment_body) < 2000, "Comment should be under GitHub's practical limit"
                
                # マークダウン形式確認
                assert comment_body.startswith("##"), "Should start with markdown header"
                assert "**" in comment_body, "Should contain bold formatting"
                
                TestRetryIssueReporterStrictAudit.auditor.record_audit(test_name, "PASS", {
                    "required_elements_present": len(required_elements),
                    "comment_length": len(comment_body),
                    "markdown_formatted": True,
                    "context_integration": True
                })
                
        except Exception as e:
            TestRetryIssueReporterStrictAudit.auditor.record_audit(test_name, "FAIL", {
                "error": str(e),
                "severity": "HIGH"
            })
            raise
    
    @pytest.mark.asyncio
    async def test_005_error_handling_resilience(self, mock_github, audit_env):
        """🔍 Test 005: エラーハンドリング回復力検証"""
        test_name = "error_handling_resilience"
        
        try:
            with patch.dict(os.environ, audit_env):
                reporter = RetryIssueReporter()
                
                # GitHub API失敗シミュレーション
                with patch.object(reporter.repo, 'get_issue', side_effect=Exception("GitHub API Error")):
                    session_id = reporter.start_retry_session(400, "error_handling_test")
                    
                    # エラー時でもクラッシュしないことを確認
                    await reporter.record_retry_attempt(
                        session_id=session_id,
                        attempt_number=1,
                        error=ValueError("Test error"),
                        recovery_action="RETRY",
                        recovery_message="Testing error resilience"
                    )
                    
                    # セッションデータは保持されている
                    session = reporter.retry_sessions[session_id]
                    assert len(session["attempts"]) == 1
                
                # 無効セッションID処理
                await reporter.record_retry_attempt(
                    session_id="invalid_session_id",
                    attempt_number=1,
                    error=RuntimeError("Test"),
                    recovery_action="RETRY",
                    recovery_message="Should not crash"
                )
                
                # メモリ不足シミュレーション（大量データ）
                large_context = {"large_data": "x" * 10000}
                session_id_large = reporter.start_retry_session(401, "large_data_test")
                
                await reporter.record_retry_attempt(
                    session_id=session_id_large,
                    attempt_number=1,
                    error=MemoryError("Out of memory"),
                    recovery_action="ABORT",
                    recovery_message="Memory limit exceeded",
                    context=large_context
                )
                
                TestRetryIssueReporterStrictAudit.auditor.record_audit(test_name, "PASS", {
                    "github_api_error_handled": True,
                    "invalid_session_handled": True,
                    "large_data_handled": True,
                    "no_crashes": True
                })
                
        except Exception as e:
            TestRetryIssueReporterStrictAudit.auditor.record_audit(test_name, "FAIL", {
                "error": str(e),
                "severity": "CRITICAL"
            })
            raise
    
    @pytest.mark.asyncio
    async def test_006_performance_scalability(self, mock_github, audit_env):
        """🔍 Test 006: パフォーマンス・スケーラビリティ検証"""
        test_name = "performance_scalability"
        
        try:
            with patch.dict(os.environ, audit_env):
                reporter = RetryIssueReporter()
                
                # 大量セッション作成パフォーマンス
                start_time = time.time()
                session_ids = []
                
                for i in range(100):
                    session_id = reporter.start_retry_session(500 + i, f"perf_test_{i}")
                    session_ids.append(session_id)
                
                creation_time = time.time() - start_time
                
                # 大量リトライ記録パフォーマンス
                start_time = time.time()
                
                for session_id in session_ids[:10]:  # 10セッションでテスト
                    for attempt in range(1, 4):  # 各セッション3回リトライ
                        await reporter.record_retry_attempt(
                            session_id=session_id,
                            attempt_number=attempt,
                            error=RuntimeError(f"Test error {attempt}"),
                            recovery_action="RETRY",
                            recovery_message=f"Performance test attempt {attempt}"
                        )
                
                recording_time = time.time() - start_time
                
                # メモリ使用量確認
                import psutil
                process = psutil.Process()
                memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                
                # パフォーマンス基準
                assert creation_time < 5.0, f"Session creation too slow: {creation_time}s"
                assert recording_time < 10.0, f"Recording too slow: {recording_time}s"
                assert memory_usage < 100, f"Memory usage too high: {memory_usage}MB"
                
                TestRetryIssueReporterStrictAudit.auditor.record_audit(test_name, "PASS", {
                    "session_creation_time": f"{creation_time:.2f}s",
                    "recording_time": f"{recording_time:.2f}s", 
                    "memory_usage": f"{memory_usage:.1f}MB",
                    "sessions_created": 100,
                    "retry_records": 30,
                    "performance_acceptable": True
                })
                
        except Exception as e:
            TestRetryIssueReporterStrictAudit.auditor.record_audit(test_name, "FAIL", {
                "error": str(e),
                "severity": "MEDIUM"
            })
            raise
    
    @pytest.mark.asyncio
    async def test_007_helper_function_integration(self, mock_github, audit_env):
        """🔍 Test 007: ヘルパー関数統合検証"""
        test_name = "helper_function_integration"
        
        try:
            with patch.dict(os.environ, audit_env):
                
                # 成功するテスト関数
                async def successful_function(value):
                    return {"result": value, "status": "success"}
                
                result = await with_retry_reporting(
                    successful_function,
                    issue_number=600,
                    operation="helper_success_test",
                    max_retries=3,
                    value="test_value"
                )
                
                assert result["result"] == "test_value"
                assert result["status"] == "success"
                
                # 失敗してリトライするテスト関数
                call_count = 0
                async def failing_then_success_function():
                    nonlocal call_count
                    call_count += 1
                    if call_count <= 2:
                        raise ConnectionError(f"Simulated failure #{call_count}")
                    return {"result": "success_after_retries", "call_count": call_count}
                
                call_count = 0  # リセット
                result = await with_retry_reporting(
                    failing_then_success_function,
                    issue_number=601,
                    operation="helper_retry_test", 
                    max_retries=4
                )
                
                assert result["result"] == "success_after_retries"
                assert result["call_count"] == 3
                
                # 最終的に失敗するテスト
                async def always_failing_function():
                    raise RuntimeError("Always fails")
                
                try:
                    await with_retry_reporting(
                        always_failing_function,
                        issue_number=602,
                        operation="helper_failure_test",
                        max_retries=2
                    )
                    assert False, "Should raise exception"
                except RuntimeError as e:
                    assert "Always fails" in str(e)
                
                TestRetryIssueReporterStrictAudit.auditor.record_audit(test_name, "PASS", {
                    "success_case": True,
                    "retry_success_case": True,
                    "final_failure_case": True,
                    "helper_function_working": True
                })
                
        except Exception as e:
            TestRetryIssueReporterStrictAudit.auditor.record_audit(test_name, "FAIL", {
                "error": str(e),
                "severity": "HIGH"
            })
            raise
    
    def test_zzz_generate_comprehensive_audit_report(self):
        """🔍 Test ZZZ: 包括的監査レポート生成"""
        audit_report = TestRetryIssueReporterStrictAudit.auditor.generate_audit_report()
        
        # レポートをファイルに保存
        report_file = Path(__file__).parent / "retry_issue_reporter_strict_audit_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(audit_report, f, indent=2, ensure_ascii=False)
        
        # コンソール出力
        print("\n" + "="*80)
        print("🚨 RETRY ISSUE REPORTER - 厳格監査結果")
        print("="*80)
        print(f"📊 総テスト数: {audit_report['audit_summary']['total_tests']}")
        print(f"✅ 成功: {audit_report['audit_summary']['passed']}")
        print(f"❌ 失敗: {audit_report['audit_summary']['failed']}")
        print(f"⚠️ 警告: {audit_report['audit_summary']['warnings']}")
        print(f"📈 成功率: {audit_report['audit_summary']['success_rate']:.1f}%")
        print(f"🚨 重大問題: {audit_report['audit_summary']['critical_issues']}")
        
        if audit_report['critical_issues']:
            print(f"\n🚨 重大問題詳細:")
            for issue in audit_report['critical_issues']:
                print(f"  - {issue}")
        
        print(f"\n📄 詳細レポート: {report_file}")
        print("="*80)
        
        # 品質ゲート判定
        success_rate = audit_report['audit_summary']['success_rate']
        critical_issues = audit_report['audit_summary']['critical_issues']
        
        if success_rate >= 95 and critical_issues == 0:
            print("🎉 品質ゲート: 合格 (EXCELLENT)")
        elif success_rate >= 85 and critical_issues <= 1:
            print("✅ 品質ゲート: 合格 (GOOD)")
        elif success_rate >= 70:
            print("⚠️ 品質ゲート: 条件付き合格 (ACCEPTABLE)")
        else:
            print("❌ 品質ゲート: 不合格 (REQUIRES_IMPROVEMENT)")
            raise AssertionError("Quality gate failed - requires improvement")


if __name__ == "__main__":
    # pytest実行
    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
        "-x",  # 最初のエラーで停止
        "--asyncio-mode=auto"
    ]
    
    exit_code = pytest.main(pytest_args)
    sys.exit(exit_code)