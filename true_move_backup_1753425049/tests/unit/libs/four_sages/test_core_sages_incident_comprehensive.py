#!/usr/bin/env python3
"""
🚨 core/sages/incident.py 包括的テストスイート
Comprehensive Test Suite for Incident Sage
Created: 2025-07-17
Author: Claude Elder
Version: 1.0.0 - 95%カバレッジ目標
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# テスト対象のインポート
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.sages.incident import IncidentSage


class TestIncidentSageInitialization:
    """IncidentSage初期化テスト"""
    
    def test_init_without_config(self):
        """設定なしでの初期化テスト"""
        sage = IncidentSage()
        
        assert sage.config == {}
        assert sage.logger is not None
        assert sage.logger.name == "IncidentSage"
    
    def test_init_with_config(self):
        """設定ありでの初期化テスト"""
        config = {
            "max_incidents": 100,
            "alert_threshold": 5,
            "auto_resolve": True
        }
        sage = IncidentSage(config)
        
        assert sage.config == config
        assert sage.config["max_incidents"] == 100
        assert sage.config["alert_threshold"] == 5
        assert sage.config["auto_resolve"] is True
    
    def test_init_with_empty_config(self):
        """空設定での初期化テスト"""
        sage = IncidentSage({})
        
        assert sage.config == {}
        assert sage.logger is not None
    
    def test_init_with_none_config(self):
        """None設定での初期化テスト"""
        sage = IncidentSage(None)
        
        assert sage.config == {}
        assert sage.logger is not None
    
    def test_logger_configuration(self):
        """ロガー設定テスト"""
        sage = IncidentSage()
        
        assert isinstance(sage.logger, logging.Logger)
        assert sage.logger.name == "IncidentSage"


class TestIncidentSageProcessIncident:
    """IncidentSage.process_incident テスト"""
    
    @pytest.mark.asyncio
    async def test_process_incident_with_id(self):
        """IDありインシデント処理テスト"""
        sage = IncidentSage()
        incident_data = {
            "id": "INC-001",
            "title": "System Error",
            "description": "Database connection failed",
            "severity": "high"
        }
        
        result = await sage.process_incident(incident_data)
        
        assert result["status"] == "processed"
        assert result["incident_id"] == "INC-001"
        assert result["action"] == "resolved"
    
    @pytest.mark.asyncio
    async def test_process_incident_without_id(self):
        """IDなしインシデント処理テスト"""
        sage = IncidentSage()
        incident_data = {
            "title": "Network Error",
            "description": "Connection timeout",
            "severity": "medium"
        }
        
        result = await sage.process_incident(incident_data)
        
        assert result["status"] == "processed"
        assert result["incident_id"] == "unknown"
        assert result["action"] == "resolved"
    
    @pytest.mark.asyncio
    async def test_process_incident_empty_data(self):
        """空データでのインシデント処理テスト"""
        sage = IncidentSage()
        incident_data = {}
        
        result = await sage.process_incident(incident_data)
        
        assert result["status"] == "processed"
        assert result["incident_id"] == "unknown"
        assert result["action"] == "resolved"
    
    @pytest.mark.asyncio
    async def test_process_incident_with_complex_data(self):
        """複雑なデータでのインシデント処理テスト"""
        sage = IncidentSage()
        incident_data = {
            "id": "INC-002",
            "title": "Performance Degradation",
            "description": "Response time increased by 200%",
            "severity": "critical",
            "timestamp": "2025-07-17T12:00:00Z",
            "affected_services": ["api", "database", "cache"],
            "reporter": "monitoring_system",
            "metadata": {
                "cpu_usage": 85,
                "memory_usage": 92,
                "error_rate": 0.15
            }
        }
        
        result = await sage.process_incident(incident_data)
        
        assert result["status"] == "processed"
        assert result["incident_id"] == "INC-002"
        assert result["action"] == "resolved"
    
    @pytest.mark.asyncio
    async def test_process_incident_with_special_characters(self):
        """特殊文字を含むインシデント処理テスト"""
        sage = IncidentSage()
        incident_data = {
            "id": "INC-特殊-001",
            "title": "システムエラー 🚨",
            "description": "データベース接続エラー: Connection failed with error #500",
            "severity": "high"
        }
        
        result = await sage.process_incident(incident_data)
        
        assert result["status"] == "processed"
        assert result["incident_id"] == "INC-特殊-001"
        assert result["action"] == "resolved"
    
    @pytest.mark.asyncio
    async def test_process_incident_return_type(self):
        """戻り値の型テスト"""
        sage = IncidentSage()
        incident_data = {"id": "test"}
        
        result = await sage.process_incident(incident_data)
        
        assert isinstance(result, dict)
        assert "status" in result
        assert "incident_id" in result
        assert "action" in result
        assert len(result) == 3
    
    @pytest.mark.asyncio
    async def test_process_incident_async_behavior(self):
        """非同期動作テスト"""
        sage = IncidentSage()
        incident_data = {"id": "async-test"}
        
        # 複数の並行実行
        tasks = [
            sage.process_incident({"id": f"incident-{i}"})
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result["incident_id"] == f"incident-{i}"
            assert result["status"] == "processed"


class TestIncidentSageAnalyzeIncident:
    """IncidentSage.analyze_incident テスト"""
    
    @pytest.mark.asyncio
    async def test_analyze_incident_basic(self):
        """基本的なインシデント分析テスト"""
        sage = IncidentSage()
        incident_data = {
            "id": "INC-001",
            "title": "System Error"
        }
        
        result = await sage.analyze_incident(incident_data)
        
        assert result["severity"] == "medium"
        assert result["impact"] == "low"
        assert result["recommendation"] == "monitor"
    
    @pytest.mark.asyncio
    async def test_analyze_incident_empty_data(self):
        """空データでのインシデント分析テスト"""
        sage = IncidentSage()
        incident_data = {}
        
        result = await sage.analyze_incident(incident_data)
        
        assert result["severity"] == "medium"
        assert result["impact"] == "low"
        assert result["recommendation"] == "monitor"
    
    @pytest.mark.asyncio
    async def test_analyze_incident_complex_data(self):
        """複雑なデータでのインシデント分析テスト"""
        sage = IncidentSage()
        incident_data = {
            "id": "INC-002",
            "title": "Critical System Failure",
            "severity": "critical",
            "affected_users": 10000,
            "downtime": 30,
            "error_messages": [
                "Database connection lost",
                "Service unavailable",
                "Internal server error"
            ]
        }
        
        result = await sage.analyze_incident(incident_data)
        
        assert result["severity"] == "medium"
        assert result["impact"] == "low"
        assert result["recommendation"] == "monitor"
    
    @pytest.mark.asyncio
    async def test_analyze_incident_return_type(self):
        """戻り値の型テスト"""
        sage = IncidentSage()
        incident_data = {"id": "test"}
        
        result = await sage.analyze_incident(incident_data)
        
        assert isinstance(result, dict)
        assert "severity" in result
        assert "impact" in result
        assert "recommendation" in result
        assert len(result) == 3
    
    @pytest.mark.asyncio
    async def test_analyze_incident_consistent_results(self):
        """一貫した結果のテスト"""
        sage = IncidentSage()
        incident_data = {"id": "consistency-test"}
        
        # 複数回実行して同じ結果を得ることを確認
        results = []
        for _ in range(3):
            result = await sage.analyze_incident(incident_data)
            results.append(result)
        
        # すべての結果が同じであることを確認
        for result in results:
            assert result == results[0]
    
    @pytest.mark.asyncio
    async def test_analyze_incident_async_behavior(self):
        """非同期動作テスト"""
        sage = IncidentSage()
        
        # 複数の並行実行
        tasks = [
            sage.analyze_incident({"id": f"analyze-{i}"})
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        for result in results:
            assert result["severity"] == "medium"
            assert result["impact"] == "low"
            assert result["recommendation"] == "monitor"


class TestIncidentSageIntegration:
    """IncidentSage統合テスト"""
    
    @pytest.mark.asyncio
    async def test_full_incident_workflow(self):
        """完全なインシデントワークフローテスト"""
        sage = IncidentSage({
            "auto_resolve": True,
            "notification_enabled": True
        })
        
        # インシデントデータ
        incident_data = {
            "id": "INC-WORKFLOW-001",
            "title": "API Performance Issue",
            "description": "Response time exceeded threshold",
            "severity": "high",
            "timestamp": "2025-07-17T12:00:00Z"
        }
        
        # 処理と分析を並行実行
        process_task = sage.process_incident(incident_data)
        analyze_task = sage.analyze_incident(incident_data)
        
        process_result, analyze_result = await asyncio.gather(
            process_task, analyze_task
        )
        
        # 処理結果検証
        assert process_result["status"] == "processed"
        assert process_result["incident_id"] == "INC-WORKFLOW-001"
        assert process_result["action"] == "resolved"
        
        # 分析結果検証
        assert analyze_result["severity"] == "medium"
        assert analyze_result["impact"] == "low"
        assert analyze_result["recommendation"] == "monitor"
    
    @pytest.mark.asyncio
    async def test_multiple_incidents_handling(self):
        """複数インシデント同時処理テスト"""
        sage = IncidentSage()
        
        # 複数のインシデント
        incidents = [
            {"id": f"INC-{i:03d}", "title": f"Incident {i}", "severity": "low"}
            for i in range(10)
        ]
        
        # 全インシデントを並行処理
        process_tasks = [sage.process_incident(inc) for inc in incidents]
        analyze_tasks = [sage.analyze_incident(inc) for inc in incidents]
        
        process_results = await asyncio.gather(*process_tasks)
        analyze_results = await asyncio.gather(*analyze_tasks)
        
        # 結果検証
        assert len(process_results) == 10
        assert len(analyze_results) == 10
        
        for i, (p_result, a_result) in enumerate(zip(process_results, analyze_results)):
            assert p_result["incident_id"] == f"INC-{i:03d}"
            assert p_result["status"] == "processed"
            assert a_result["severity"] == "medium"


class TestIncidentSageErrorHandling:
    """IncidentSageエラーハンドリングテスト"""
    
    @pytest.mark.asyncio
    async def test_process_incident_with_invalid_data_types(self):
        """無効なデータ型でのインシデント処理テスト"""
        sage = IncidentSage()
        
        # None データはAttributeErrorを発生させる
        with pytest.raises(AttributeError):
            await sage.process_incident(None)
        
        # 空の辞書は正常に処理される
        result = await sage.process_incident({})
        assert result["incident_id"] == "unknown"
        
    @pytest.mark.asyncio
    async def test_analyze_incident_with_none_data(self):
        """Noneデータでのインシデント分析テスト"""
        sage = IncidentSage()
        
        # analyze_incidentは引数を使用していないため、
        # Noneを渡しても問題なく動作するはず
        result = await sage.analyze_incident(None)
        
        assert result["severity"] == "medium"
        assert result["impact"] == "low"
        assert result["recommendation"] == "monitor"


class TestIncidentSageConfiguration:
    """IncidentSage設定テスト"""
    
    def test_config_access(self):
        """設定アクセステスト"""
        config = {
            "max_incidents": 50,
            "timeout": 30,
            "retry_count": 3,
            "enable_logging": True
        }
        sage = IncidentSage(config)
        
        assert sage.config["max_incidents"] == 50
        assert sage.config["timeout"] == 30
        assert sage.config["retry_count"] == 3
        assert sage.config["enable_logging"] is True
    
    def test_config_modification(self):
        """設定変更テスト"""
        sage = IncidentSage({"initial": "value"})
        
        # 設定を変更
        sage.config["new_setting"] = "new_value"
        sage.config["initial"] = "modified"
        
        assert sage.config["new_setting"] == "new_value"
        assert sage.config["initial"] == "modified"
    
    def test_config_with_nested_dict(self):
        """ネストした辞書設定テスト"""
        config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "credentials": {
                    "username": "admin",
                    "password": "secret"
                }
            },
            "notifications": {
                "email": True,
                "slack": False
            }
        }
        sage = IncidentSage(config)
        
        assert sage.config["database"]["host"] == "localhost"
        assert sage.config["database"]["credentials"]["username"] == "admin"
        assert sage.config["notifications"]["email"] is True


class TestIncidentSageLogging:
    """IncidentSageロギングテスト"""
    
    def test_logger_existence(self):
        """ロガー存在テスト"""
        sage = IncidentSage()
        
        assert hasattr(sage, "logger")
        assert sage.logger is not None
        assert isinstance(sage.logger, logging.Logger)
    
    def test_logger_name(self):
        """ロガー名テスト"""
        sage = IncidentSage()
        
        assert sage.logger.name == "IncidentSage"
    
    @patch('logging.getLogger')
    def test_logger_initialization(self, mock_get_logger):
        """ロガー初期化テスト"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        sage = IncidentSage()
        
        mock_get_logger.assert_called_once_with("IncidentSage")
        assert sage.logger == mock_logger


class TestIncidentSageEdgeCases:
    """IncidentSageエッジケーステスト"""
    
    @pytest.mark.asyncio
    async def test_large_incident_data(self):
        """大きなインシデントデータテスト"""
        sage = IncidentSage()
        
        # 大量のデータを含むインシデント
        large_data = {
            "id": "INC-LARGE-001",
            "title": "Large Data Incident",
            "description": "A" * 10000,  # 10KB の文字列
            "logs": ["log entry " + str(i) for i in range(1000)],  # 1000個のログエントリ
            "metadata": {
                f"key_{i}": f"value_{i}" for i in range(100)  # 100個のメタデータエントリ
            }
        }
        
        # 処理と分析を実行
        process_result = await sage.process_incident(large_data)
        analyze_result = await sage.analyze_incident(large_data)
        
        assert process_result["incident_id"] == "INC-LARGE-001"
        assert process_result["status"] == "processed"
        assert analyze_result["severity"] == "medium"
    
    @pytest.mark.asyncio
    async def test_unicode_incident_data(self):
        """Unicode文字を含むインシデントデータテスト"""
        sage = IncidentSage()
        
        unicode_data = {
            "id": "INC-多言語-001",
            "title": "システムエラー 🚨 System Error",
            "description": "データベースエラー: 데이터베이스 오류 - Database Error - エラー発生",
            "emoji_status": "🔥💥⚠️",
            "multilingual_notes": {
                "japanese": "システムが停止しました",
                "korean": "시스템이 중단되었습니다",
                "chinese": "系统已停止",
                "arabic": "تم إيقاف النظام",
                "russian": "Система остановлена"
            }
        }
        
        process_result = await sage.process_incident(unicode_data)
        analyze_result = await sage.analyze_incident(unicode_data)
        
        assert process_result["incident_id"] == "INC-多言語-001"
        assert process_result["status"] == "processed"
        assert analyze_result["severity"] == "medium"


class TestIncidentSagePerformance:
    """IncidentSageパフォーマンステスト"""
    
    @pytest.mark.asyncio
    async def test_high_concurrency(self):
        """高並行性テスト"""
        sage = IncidentSage()
        
        # 100個の並行タスク
        tasks = []
        for i in range(100):
            incident_data = {"id": f"concurrent-{i}"}
            tasks.append(sage.process_incident(incident_data))
            tasks.append(sage.analyze_incident(incident_data))
        
        # 全タスクを並行実行
        results = await asyncio.gather(*tasks)
        
        # 結果検証
        assert len(results) == 200  # 100 process + 100 analyze
        
        # process_incident の結果（偶数インデックス）
        for i in range(0, 200, 2):
            assert results[i]["status"] == "processed"
            assert results[i]["incident_id"] == f"concurrent-{i//2}"
        
        # analyze_incident の結果（奇数インデックス）
        for i in range(1, 200, 2):
            assert results[i]["severity"] == "medium"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])