#!/usr/bin/env python3
"""
Enhanced Auto Issue Processor のテスト
Issue #191対応: 包括的なエラーハンドリングと回復機能の実装
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import os

# テスト対象モジュールをインポート
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from libs.integrations.github.auto_issue_processor_enhanced import EnhancedAutoIssueProcessor
from libs.auto_issue_processor_error_handling import (
    RecoveryAction, CircuitBreakerOpenError, ErrorType
)


class TestEnhancedAutoIssueProcessor:
    """Enhanced Auto Issue Processorのテスト"""
    
    @pytest.fixture
    def mock_github(self):
        """GitHub モックの設定"""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_token',
            'GITHUB_REPO_OWNER': 'test_owner',
            'GITHUB_REPO_NAME': 'test_repo'
        }):
            with patch('libs.integrations.github.auto_issue_processor_enhanced.Github') as mock_github:
                mock_repo = Mock()
                mock_github.return_value.get_repo.return_value = mock_repo
                yield mock_github, mock_repo
    
    @pytest.fixture
    async def processor(self, mock_github):
        """テスト用プロセッサーインスタンス"""
        _, mock_repo = mock_github
        with patch('libs.integrations.github.auto_issue_processor_enhanced.AutoIssueElderFlowEngine'):
            with patch('libs.integrations.github.auto_issue_processor_enhanced.TaskSage'):
                with patch('libs.integrations.github.auto_issue_processor_enhanced.IncidentSage'):
                    with patch('libs.integrations.github.auto_issue_processor_enhanced.KnowledgeSage'):
                        # Deep nesting detected (depth: 5) - consider refactoring
                        with patch('libs.integrations.github.auto_issue_processor_enhanced.RagManager'):
                            # Deep nesting detected (depth: 6) - consider refactoring
                            with patch('libs.integrations.github.auto_issue_processor_enhanced.ReopenedIssueTracker'):
                                processor = EnhancedAutoIssueProcessor()
                                return processor
    
    @pytest.mark.asyncio
    async def test_get_capabilities(self, processor):
        """機能取得のテスト"""
        capabilities = processor.get_capabilities()
        
        assert capabilities["service"] == "EnhancedAutoIssueProcessor"
        assert capabilities["version"] == "2.0.0"
        assert "Comprehensive error handling" in capabilities["capabilities"]
        assert "Circuit breaker protection" in capabilities["capabilities"]
        assert capabilities["error_handling"]["circuit_breaker"] is True
        assert "retry" in capabilities["error_handling"]["recovery_actions"]
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_activation(self, processor):
        """サーキットブレーカー動作のテスト"""
        # サーキットブレーカーを開く
        cb = processor.error_handler.get_circuit_breaker("process_request")
        for _ in range(5):
            cb.record_failure()
        
        # リクエスト処理
        result = await processor.process_request({"mode": "scan"})
        
        assert result["status"] == "circuit_breaker_open"
        assert "temporarily unavailable" in result["message"]
        assert processor.metrics["circuit_breaker_activations"] == 1
    
    @pytest.mark.asyncio
    async def test_scan_with_recovery(self, processor):
        """スキャン処理のエラーリカバリーテスト"""
        # モックのセットアップ
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.labels = []
        
        with patch.object(processor, 'scan_processable_issues') as mock_scan:
            # 最初は失敗、次に成功
            mock_scan.side_effect = [
                Exception("Network error"),
                [mock_issue]
            ]
            
            with patch.object(processor.evaluator, 'evaluate', new_callable=AsyncMock) as mock_eval:
                mock_complexity = Mock()
                mock_complexity.score = 0.5
                mock_eval.return_value = mock_complexity
                
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    result = await processor._scan_issues_with_recovery()
                    
                    assert result["status"] == "success"
                    assert result["processable_issues"] == 1
                    assert processor.metrics["retry_count"] == 1
    
    @pytest.mark.asyncio
    async def test_process_with_rate_limit(self, processor):
        """レート制限のテスト"""
        with patch.object(processor.limiter, 'can_process', new_callable=AsyncMock) as mock_can_process:
            mock_can_process.return_value = False
            
            result = await processor._process_issues_with_recovery()
            
            assert result["status"] == "rate_limited"
            assert "Processing limit reached" in result["message"]
    
    @pytest.mark.asyncio
    async def test_process_with_no_issues(self, processor):
        """処理可能なイシューがない場合のテスト"""
        with patch.object(processor.limiter, 'can_process', new_callable=AsyncMock) as mock_can_process:
            mock_can_process.return_value = True
            
            with patch.object(processor, 'scan_processable_issues', new_callable=AsyncMock) as mock_scan:
                mock_scan.return_value = []
                
                result = await processor._process_issues_with_recovery()
                
                assert result["status"] == "no_issues"
                assert "No processable issues found" in result["message"]
    
    @pytest.mark.asyncio
    async def test_execute_auto_processing_with_recovery(self, processor):
        """自動処理実行のリカバリーテスト"""
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test body"
        mock_issue.labels = []
        
        # モックのセットアップ
        with patch.object(processor, '_check_existing_pr_for_issue', new_callable=AsyncMock) as mock_check_pr:
            mock_check_pr.return_value = None
            
            with patch.object(processor.limiter, 'record_processing', new_callable=AsyncMock):
                with patch.object(processor.evaluator, 'evaluate', new_callable=AsyncMock) as mock_eval:
                    mock_complexity = Mock()
                    mock_complexity.score = 0.5
                    mock_eval.return_value = mock_complexity
                    
                    with patch.object(processor, 'consult_four_sages', new_callable=AsyncMock) as mock_sages:
                        mock_sages.return_value = {"advice": "test"}
                        
                        # Deep nesting detected (depth: 5) - consider refactoring
                        with patch.object(processor.elder_flow, 'execute_flow', new_callable=AsyncMock) as mock_flow:
                            # 最初は失敗、次に成功
                            mock_flow.side_effect = [
                                Exception("GitHub API error"),
                                {
                                    "status": "success",
                                    "pr_url": "https://github.com/test/pr/1",
                                    "pr_number": 1
                                }
                            ]
                            
                            # Deep nesting detected (depth: 6) - consider refactoring
                            with patch.object(
                                processor,
                                '_handle_processing_result',
                                new_callable=AsyncMock
                            ) as mock_handle:
                                mock_handle.return_value = {"status": "success"}
                                
                                # TODO: Extract this complex nested logic into a separate method
                                with patch('asyncio.sleep', new_callable=AsyncMock):
                                    result = await processor._execute_auto_processing_with_recovery(mock_issue)
                                    
                                    assert result["status"] == "success"
                                    assert processor.metrics["retry_count"] >= 1
    
    @pytest.mark.asyncio
    async def test_handle_existing_pr(self, processor):
        """既存PRの処理テスト"""
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.create_comment = Mock()
        
        existing_pr = {
            "number": 456,
            "html_url": "https://github.com/test/pr/456",
            "state": "open",
            "merged": False
        }
        
        with patch.object(processor.reopened_tracker, 'check_if_reopened', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = {"is_reopened": False}
            
            result = await processor._handle_existing_pr(mock_issue, existing_pr)
            
            assert result["status"] == "already_exists"
            assert result["pr_number"] == 456
    
    @pytest.mark.asyncio
    async def test_handle_reopened_issue_with_pr(self, processor):
        """再オープンされたIssueの処理テスト"""
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.create_comment = Mock()
        
        existing_pr = {
            "number": 456,
            "html_url": "https://github.com/test/pr/456",
            "state": "closed",
            "merged": False
        }
        
        reopened_info = {
            "is_reopened": True,
            "reopen_count": 2,
            "reopened_at": "2025-07-21T10:00:00",
            "reopened_by": "test_user"
        }
        
        with patch.object(processor.reopened_tracker, 'record_reprocessing', new_callable=AsyncMock):
            await processor._handle_reopened_issue_with_pr(mock_issue, existing_pr, reopened_info)
            
            # コメントが作成されたことを確認
            mock_issue.create_comment.assert_called_once()
            comment_text = mock_issue.create_comment.call_args[0][0]
            assert "再オープン検知" in comment_text
            assert "PR #456" in comment_text
    
    @pytest.mark.asyncio
    async def test_dry_run_mode(self, processor):
        """ドライランモードのテスト"""
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.labels = []
        
        with patch.object(processor.repo, 'get_issue') as mock_get_issue:
            mock_get_issue.return_value = mock_issue
            
            with patch.object(processor.evaluator, 'evaluate', new_callable=AsyncMock) as mock_eval:
                mock_complexity = Mock()
                mock_complexity.score = 0.5
                mock_complexity.is_processable = True
                mock_complexity.factors = {"test": "factor"}
                mock_eval.return_value = mock_complexity
                
                result = await processor._dry_run_with_recovery({"issue_number": 123})
                
                assert result["status"] == "dry_run"
                assert result["issue"]["number"] == 123
                assert result["issue"]["complexity"] == 0.5
                assert result["issue"]["processable"] is True
    
    @pytest.mark.asyncio
    async def test_get_metrics(self, processor):
        """メトリクス取得のテスト"""
        # いくつかのメトリクスを更新
        processor.metrics["total_processed"] = 10
        processor.metrics["successful"] = 8
        processor.metrics["failed"] = 2
        
        metrics = processor.get_metrics()
        
        assert metrics["processing_metrics"]["total_processed"] == 10
        assert metrics["processing_metrics"]["successful"] == 8
        assert metrics["processing_metrics"]["failed"] == 2
        assert "circuit_breakers" in metrics
    
    @pytest.mark.asyncio
    async def test_error_handling_with_rollback(self, processor):
        """ロールバックを伴うエラーハンドリングのテスト"""
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test body"
        mock_issue.labels = []
        
        with patch.object(processor, '_check_existing_pr_for_issue', new_callable=AsyncMock) as mock_check_pr:
            mock_check_pr.return_value = None
            
            with patch.object(processor.elder_flow, 'execute_flow', new_callable=AsyncMock) as mock_flow:
                # 常に失敗する
                mock_flow.side_effect = Exception("Permanent failure")
                
                with patch.object(processor.error_handler, 'handle_error', new_callable=AsyncMock) as mock_handler:
                    mock_handler.return_value = Mock(
                        success=False,
                        action_taken=RecoveryAction.ROLLBACK,
                        message="Rolled back",
                        cleaned_resources=["file1", "file2"]
                    )
                    
                    with pytest.raises(Exception) as exc_info:
                        await processor._execute_auto_processing_with_recovery(mock_issue)
                    
                    assert "rolled back" in str(exc_info.value)
                    assert processor.metrics["rollback_count"] == 1