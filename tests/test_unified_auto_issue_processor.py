#!/usr/bin/env python3
"""
統一Auto Issue Processorのテスト
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from libs.auto_issue_processor import AutoIssueProcessor, ProcessorConfig
from libs.auto_issue_processor.utils import ProcessLock


@pytest.fixture
def test_config():
    """テスト用設定"""
    config = ProcessorConfig()
    config.github.token = "test_token"
    config.github.repo = "test_repo"
    config.github.owner = "test_owner"
    config.processing.max_issues_per_run = 2
    config.dry_run = True
    return config


@pytest.fixture
def mock_issue():
    """モックIssue"""
    issue = Mock()
    issue.number = 123
    issue.title = "Test Issue"
    issue.body = "Test issue body"
    issue.created_at = datetime.now()
    issue.labels = []
    issue.comments = 0
    issue.pull_request = None
    return issue


class TestUnifiedAutoIssueProcessor:
    """統一Auto Issue Processorのテスト"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, test_config):
        """初期化テスト"""
        processor = AutoIssueProcessor(test_config)
        
        assert processor.config == test_config
        assert processor.lock_manager is not None
        assert processor.stats["processed"] == 0
    
    @pytest.mark.asyncio
    async def test_process_issues_dry_run(self, test_config, mock_issue):
        """ドライランでのIssue処理テスト"""
        processor = AutoIssueProcessor(test_config)
        
        # GitHubをモック
        with patch.object(processor, 'repo') as mock_repo:
            mock_repo.get_issue.return_value = mock_issue
            
            result = await processor.process_issues([123])
            
            assert result["success"] is True
            assert result["stats"]["processed"] == 1
            assert result["stats"]["success"] == 1
    
    @pytest.mark.asyncio
    async def test_lock_mechanism(self, test_config, mock_issue):
        """ロック機構のテスト"""
        processor = AutoIssueProcessor(test_config)
        
        # ロックを取得
        lock_key = f"issue_{mock_issue.number}"
        acquired = await processor.lock_manager.acquire(lock_key, ttl=10)
        assert acquired is True
        
        # 同じキーで再度ロック取得を試みる（失敗するはず）
        acquired2 = await processor.lock_manager.acquire(lock_key, ttl=10)
        assert acquired2 is False
        
        # ロックを解放
        released = await processor.lock_manager.release(lock_key)
        assert released is True
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, test_config):
        """エラーリカバリーのテスト"""
        test_config.features.error_recovery = True
        processor = AutoIssueProcessor(test_config)
        
        # エラーリカバリーが初期化されていることを確認
        assert processor.error_recovery is not None
    
    @pytest.mark.asyncio
    async def test_four_sages_integration(self, test_config, mock_issue):
        """4賢者統合のテスト"""
        test_config.features.four_sages_integration = True
        processor = AutoIssueProcessor(test_config)
        
        # 4賢者が初期化されていることを確認
        assert processor.four_sages is not None
        
        # 分析をモック
        with patch.object(processor.four_sages, 'analyze_issue') as mock_analyze:
            mock_analyze.return_value = {
                "skip": False,
                "reason": None,
                "summary": "Test analysis"
            }
            
            with patch.object(processor, 'repo') as mock_repo:
                mock_repo.get_issue.return_value = mock_issue
                
                result = await processor.process_issues([123])
                
                # 4賢者の分析が呼ばれたことを確認
                mock_analyze.assert_called_once()


class TestProcessLock:
    """プロセスロックのテスト"""
    
    @pytest.mark.asyncio
    async def test_file_lock_backend(self):
        """ファイルロックバックエンドのテスト"""
        lock = ProcessLock("file", lock_dir="./test_locks")
        
        # ロック取得
        acquired = await lock.acquire("test_key", ttl=5)
        assert acquired is True
        
        # ロック情報確認
        info = await lock.get_lock_info("test_key")
        assert info is not None
        assert info.key == "test_key"
        
        # ロック解放
        released = await lock.release("test_key")
        assert released is True
    
    @pytest.mark.asyncio
    async def test_memory_lock_backend(self):
        """メモリロックバックエンドのテスト"""
        lock = ProcessLock("memory")
        
        # ロック取得
        acquired = await lock.acquire("test_key", ttl=5)
        assert acquired is True
        
        # 重複ロック防止
        acquired2 = await lock.acquire("test_key", ttl=5)
        assert acquired2 is False
        
        # ロック解放
        released = await lock.release("test_key")
        assert released is True
    
    @pytest.mark.asyncio
    async def test_lock_context_manager(self):
        """ロックコンテキストマネージャーのテスト"""
        lock = ProcessLock("memory")
        
        async with lock.lock_context("test_key", ttl=5):
            # ロック内での処理
            is_locked = await lock.is_locked("test_key")
            assert is_locked is True
        
        # コンテキスト外ではロックが解放されている
        is_locked = await lock.is_locked("test_key")
        assert is_locked is False


class TestConfiguration:
    """設定管理のテスト"""
    
    def test_default_config(self):
        """デフォルト設定のテスト"""
        config = ProcessorConfig()
        
        assert config.enabled is True
        assert config.dry_run is False
        assert config.features.pr_creation is True
        assert config.processing.use_enhanced_templates is False
    
    def test_config_validation(self):
        """設定検証のテスト"""
        config = ProcessorConfig()
        
        # 有効な設定
        assert config.validate() is True
        
        # 無効な設定
        config.processing.max_issues_per_run = 0
        assert config.validate() is False
    
    def test_config_to_dict(self):
        """設定の辞書変換テスト"""
        config = ProcessorConfig()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "features" in config_dict
        assert "github" in config_dict
        assert "processing" in config_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])