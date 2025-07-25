#!/usr/bin/env python3
"""
📝 Logging Crafter Servant テストスイート
========================================

Logging Crafter（D14）の包括的なテストスイート。
ログ設定、フォーマット、ローテーション、分析をテスト。

Author: Claude Elder
Created: 2025-07-23
"""

import pytest
import asyncio
from typing import Dict, Any, List
import json

from pathlib import Path
import logging
from datetime import datetime, timedelta
import os

# テスト対象をインポート
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.elder_tree.servants.dwarf_workshop.logging_crafter import LoggingCrafterServant

class TestLoggingCrafterServant:
    """Logging Crafter Servantのテストクラス"""
    
    @pytest.fixture
    def logging_crafter(self):
        """Logging Crafterインスタンスを作成"""
        return LoggingCrafterServant()
        
    @pytest.fixture

        """一時ログディレクトリを作成"""

            yield Path(tmpdir)
            
    @pytest.fixture
    def sample_log_configs(self):
        """テスト用ログ設定サンプル"""
        return {
            "basic": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "handlers": ["console"]
            },
            "advanced": {

                "format": "%(asctime)s [%(levelname)s] %(name)s - %(funcName)s:%(lineno)d - %(message)s",
                "handlers": ["console", "file", "rotating"],
                "file_path": "app.log",
                "max_bytes": 10485760,  # 10MB
                "backup_count": 5
            },
            "json": {
                "level": "INFO",
                "format": "json",
                "handlers": ["console", "file"],
                "fields": ["timestamp", "level", "logger", "message", "extra"]
            }
        }
        
    # Phase 1: ログ設定生成（Log Configuration）
    async def test_generate_basic_config(self, logging_crafter):
        """基本的なログ設定生成テスト"""
        requirements = {
            "environment": "development",
            "output": "console",

        }
        
        result = await logging_crafter.generate_config(requirements)
        
        assert result["success"] is True
        config = result["config"]

        assert "console" in config["handlers"]
        assert "formatters" in config
        
    async def test_generate_production_config(self, logging_crafter):
        """本番環境向けログ設定生成テスト"""
        requirements = {
            "environment": "production",
            "output": ["file", "syslog"],
            "level": "warning",
            "rotation": "daily",
            "retention": "30 days"
        }
        
        result = await logging_crafter.generate_config(requirements)
        
        assert result["success"] is True
        config = result["config"]
        assert config["level"] == "WARNING"
        assert "file" in config["handlers"]
        assert "rotation" in config
        assert config["rotation"]["when"] == "midnight"
        assert config["rotation"]["backup_count"] == 30
        
    async def test_generate_structured_logging_config(self, logging_crafter):
        """構造化ログ設定生成テスト"""
        requirements = {
            "format": "json",
            "fields": ["timestamp", "level", "service", "trace_id", "message"],
            "enrichment": True
        }
        
        result = await logging_crafter.generate_config(requirements)
        
        assert result["success"] is True
        config = result["config"]
        assert config["format_type"] == "json"
        assert all(field in config["fields"] for field in requirements["fields"])
        assert config["enrichment"]["enabled"] is True
        
    # Phase 2: ログハンドラー実装（Log Handler Implementation）

        """ファイルハンドラー実装テスト"""
        handler_config = {
            "type": "file",

            "mode": "a",
            "encoding": "utf-8"
        }
        
        result = await logging_crafter.implement_handler(handler_config)
        
        assert result["success"] is True
        code = result["implementation"]
        assert "FileHandler" in code
        assert handler_config["filename"] in code
        assert "encoding='utf-8'" in code
        
    async def test_implement_rotating_handler(self, logging_crafter):
        """ローテーティングハンドラー実装テスト"""
        handler_config = {
            "type": "rotating",
            "filename": "app.log",
            "max_bytes": 10485760,  # 10MB
            "backup_count": 5
        }
        
        result = await logging_crafter.implement_handler(handler_config)
        
        assert result["success"] is True
        code = result["implementation"]
        assert "RotatingFileHandler" in code
        assert "maxBytes=10485760" in code
        assert "backupCount=5" in code
        
    async def test_implement_custom_handler(self, logging_crafter):
        """カスタムハンドラー実装テスト"""
        handler_config = {
            "type": "custom",
            "class": "ElasticSearchHandler",
            "params": {
                "hosts": ["localhost:9200"],
                "index": "application-logs"
            }
        }
        
        result = await logging_crafter.implement_handler(handler_config)
        
        assert result["success"] is True
        code = result["implementation"]
        assert "class ElasticSearchHandler" in code
        assert "emit(self, record)" in code
        assert "elasticsearch" in code.lower()
        
    # Phase 3: ログフォーマッター（Log Formatter）
    async def test_create_basic_formatter(self, logging_crafter):
        """基本フォーマッター作成テスト"""
        format_config = {
            "type": "basic",
            "pattern": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
        
        result = await logging_crafter.create_formatter(format_config)
        
        assert result["success"] is True
        formatter = result["formatter"]
        assert isinstance(formatter, dict)
        assert formatter["type"] == "basic"
        assert "implementation" in formatter
        
    async def test_create_json_formatter(self, logging_crafter):
        """JSONフォーマッター作成テスト"""
        format_config = {
            "type": "json",
            "fields": {
                "timestamp": "%(asctime)s",
                "level": "%(levelname)s",
                "logger": "%(name)s",
                "message": "%(message)s"
            }
        }
        
        result = await logging_crafter.create_formatter(format_config)
        
        assert result["success"] is True
        formatter = result["formatter"]
        assert formatter["type"] == "json"
        code = formatter["implementation"]
        assert "json.dumps" in code
        assert "timestamp" in code
        
    # Phase 4: ログ分析ツール（Log Analysis）
    async def test_analyze_log_patterns(self, logging_crafter):
        """ログパターン分析テスト"""
        log_samples = [
            "2025-01-01 10:00:00 ERROR Database connection failed",
            "2025-01-01 10:00:05 ERROR Database connection failed",
            "2025-01-01 10:00:10 ERROR Database connection failed",
            "2025-01-01 10:05:00 WARNING High memory usage: 85%",
            "2025-01-01 10:10:00 INFO Application started"
        ]
        
        result = await logging_crafter.analyze_patterns(log_samples)
        
        assert result["success"] is True
        patterns = result["patterns"]
        assert len(patterns) > 0
        
        # 繰り返しパターンを検出
        db_pattern = next(p for p in patterns if "Database" in p["pattern"])
        assert db_pattern["count"] == 3
        assert db_pattern["severity"] == "ERROR"
        
    async def test_suggest_log_improvements(self, logging_crafter):
        """ログ改善提案テスト"""
        current_config = {

            "handlers": ["console"],
            "format": "%(message)s"
        }
        
        issues = [

            "No timestamp in logs",
            "No structured logging"
        ]
        
        result = await logging_crafter.suggest_improvements(current_config, issues)
        
        assert result["success"] is True
        suggestions = result["suggestions"]
        assert len(suggestions) >= 3
        
        # 具体的な改善提案を確認
        assert any("level" in s["improvement"] for s in suggestions)
        assert any("timestamp" in s["improvement"] for s in suggestions)
        assert any("json" in s["improvement"].lower() for s in suggestions)
        
    # Phase 5: ログ統合（Log Integration）
    async def test_integrate_with_framework(self, logging_crafter):
        """フレームワーク統合テスト"""
        framework_config = {
            "framework": "fastapi",
            "middleware": True,
            "request_logging": True,
            "response_logging": True
        }
        
        result = await logging_crafter.integrate_framework(framework_config)
        
        assert result["success"] is True
        integration = result["integration"]
        assert "middleware" in integration
        assert "request_id" in integration["middleware"]
        assert "setup_code" in integration
        
    async def test_integrate_with_monitoring(self, logging_crafter):
        """監視システム統合テスト"""
        monitoring_config = {
            "system": "prometheus",
            "metrics": ["error_count", "warning_count", "log_volume"],
            "export_interval": 60
        }
        
        result = await logging_crafter.integrate_monitoring(monitoring_config)
        
        assert result["success"] is True
        integration = result["integration"]
        assert "exporter" in integration
        assert "metrics" in integration
        assert all(m in integration["metrics"] for m in monitoring_config["metrics"])
        
    # Phase 6: 高度なログ機能（Advanced Logging）
    async def test_implement_correlation_id(self, logging_crafter):
        """相関ID実装テスト"""
        correlation_config = {
            "header_name": "X-Correlation-ID",
            "generate_if_missing": True,
            "propagate": True
        }
        
        result = await logging_crafter.implement_correlation(correlation_config)
        
        assert result["success"] is True
        implementation = result["implementation"]
        assert "correlation_id" in implementation["filter"]
        assert "ContextVar" in implementation["context_manager"]
        assert correlation_config["header_name"] in implementation["middleware"]
        
    async def test_implement_log_sampling(self, logging_crafter):
        """ログサンプリング実装テスト"""
        sampling_config = {
            "strategy": "probabilistic",
            "rate": 0.1,  # 10%
            "always_sample": ["ERROR", "CRITICAL"]
        }
        
        result = await logging_crafter.implement_sampling(sampling_config)
        
        assert result["success"] is True
        implementation = result["implementation"]
        assert "random" in implementation
        assert "0.1" in implementation
        assert "ERROR" in implementation
        
    # Phase 7: ログセキュリティ（Log Security）
    async def test_implement_log_sanitization(self, logging_crafter):
        """ログサニタイゼーション実装テスト"""
        sanitization_config = {
            "patterns": [
                {"name": "credit_card", "regex": r"\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}"},
                {"name": "email", "regex": r"[\w\.-]+@[\w\.-]+\.\w+"},
                {"name": "api_key", "regex": r"api[_-]?key[\"']?\s*[:=]\s*[\"']?[\w-]+"}
            ],
            "replacement": "[REDACTED]"
        }
        
        result = await logging_crafter.implement_sanitization(sanitization_config)
        
        assert result["success"] is True
        implementation = result["implementation"]
        assert "filter" in implementation
        assert "re.sub" in implementation["filter"]
        assert "[REDACTED]" in implementation["filter"]
        
    # Phase 8: パフォーマンステスト
    async def test_high_performance_logging(self, logging_crafter):
        """高性能ログ設定テスト"""
        performance_requirements = {
            "throughput": "10000 logs/second",
            "latency": "< 1ms",
            "async": True,
            "buffering": True
        }
        
        result = await logging_crafter.optimize_for_performance(performance_requirements)
        
        assert result["success"] is True
        optimization = result["optimization"]
        assert optimization["async_handler"] is True
        assert optimization["buffer_size"] >= 1000
        assert "QueueHandler" in optimization["implementation"]
        assert optimization["estimated_throughput"] >= 10000
        
    # Phase 9: 完全なログシステム実装

        """完全なログシステム実装テスト"""
        system_requirements = {
            "application": "microservice",
            "environment": "production",
            "features": [
                "structured_logging",
                "correlation_id",
                "error_tracking",
                "performance_monitoring"
            ],
            "outputs": ["file", "elasticsearch"],

        }
        
        result = await logging_crafter.implement_complete_system(system_requirements)
        
        assert result["success"] is True
        system = result["system"]
        
        # 全コンポーネントが含まれているか確認
        assert "configuration" in system
        assert "handlers" in system
        assert "formatters" in system
        assert "filters" in system
        assert "integration_code" in system
        
        # 機能が実装されているか確認
        assert "correlation_id" in system["filters"]
        assert "json" in system["formatters"]
        assert len(system["handlers"]) >= 2

@pytest.mark.asyncio
class TestLoggingCrafterIntegration:
    """Logging Crafter統合テスト"""
    
    async def test_elder_tree_integration(self):
        """Elder Treeシステムとの統合テスト"""
        crafter = LoggingCrafterServant()
        
        # Elder Treeメッセージ形式
        message = {
            "action": "setup_logging",
            "data": {
                "project": {
                    "name": "elder-tree-service",
                    "type": "fastapi",
                    "environment": "production"
                },
                "requirements": {
                    "structured_logging": True,
                    "distributed_tracing": True,
                    "log_level": "INFO"
                }
            }
        }
        
        result = await crafter.process_elder_message(message)
        
        assert result["success"] is True
        assert "logging_config" in result["data"]
        assert "implementation_files" in result["data"]
        assert result["data"]["sage_notified"] is True  # Task Sageに通知

if __name__ == "__main__":
    pytest.main(["-v", __file__])