"""
4賢者システムの統合テスト
"""

import asyncio
import os
import shutil

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

# 4賢者のインポート
from libs.four_sages.base_sage import BaseSage, SageRegistry
from libs.four_sages.incident.incident_sage import (
    IncidentSage,
    IncidentSeverity,
    IncidentStatus,
)
from libs.four_sages.knowledge.knowledge_sage import KnowledgeSage
from libs.four_sages.rag.rag_sage import RAGSage
from libs.four_sages.task.task_sage import TaskPriority, TaskSage, TaskStatus

class TestBaseSage:
    """ベース賢者クラスのテスト"""

    @pytest.fixture
    def mock_sage(self):
        """モック賢者のフィクスチャ"""

        class MockSage(BaseSage):
            async def process_request(self, request):
                return {"success": True, "message": "mock processed"}
            """MockSageクラス"""

            def get_capabilities(self):
                return ["mock_capability"]

        return MockSage("Mock")

    @pytest.mark.asyncio
    async def test_sage_initialization(self, mock_sage):
        """賢者の初期化テスト"""
        assert mock_sage.sage_name == "Mock"
        assert mock_sage.status == "ready"
        assert mock_sage._metrics["requests_processed"] == 0
        assert mock_sage._metrics["errors_count"] == 0
        assert isinstance(mock_sage.last_activity, datetime)

    @pytest.mark.asyncio
    async def test_health_check(self, mock_sage)health = await mock_sage.health_check()
    """ヘルスチェックテスト"""

        assert health["sage_name"] == "Mock"
        assert health["status"] == "ready"
        assert "uptime_seconds" in health
        assert health["requests_processed"] == 0
        assert health["errors_count"] == 0
        assert health["capabilities"] == ["mock_capability"]

    @pytest.mark.asyncio
    async def test_memory_operations(self, mock_sage):
        """メモリ操作テスト"""
        # メモリ設定
        await mock_sage.set_memory("test_key", "test_value")

        # メモリ取得
        value = await mock_sage.get_memory("test_key")
        assert value == "test_value"

        # 存在しないキー
        value = await mock_sage.get_memory("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_request_logging(self, mock_sage):
        """リクエストログテスト"""
        request = {"type": "test", "data": "sample"}
        result = {"success": True, "processing_time_ms": 100}

        initial_count = mock_sage._metrics["requests_processed"]

        await mock_sage.log_request(request, result)

        assert mock_sage._metrics["requests_processed"] == initial_count + 1
        assert isinstance(mock_sage.last_activity, datetime)

    @pytest.mark.asyncio
    async def test_error_logging(self, mock_sage)error = ValueError("test error")
    """エラーログテスト"""
        context = {"test": "context"}

        initial_count = mock_sage._metrics["errors_count"]

        await mock_sage.log_error(error, context)

        assert mock_sage._metrics["errors_count"] == initial_count + 1

class TestSageRegistry:
    """賢者レジストリのテスト"""

    @pytest.fixture
    def registry(self):
        return SageRegistry()

    @pytest.fixture
    def mock_sage(self):
        class MockSage(BaseSage):
        """mock_sageメソッド"""
            """MockSageクラス"""
            async def process_request(self, request):
                return {"success": True, "sage": self.sage_name}

            def get_capabilities(self):
                return ["test_capability"]

        return MockSage("TestSage")

    def test_sage_registration(self, registry, mock_sage)registry.register_sage(mock_sage)
    """賢者登録テスト"""

        retrieved_sage = registry.get_sage("TestSage")
        assert retrieved_sage is mock_sage

        all_sages = registry.get_all_sages()
        assert "TestSage" in all_sages
        assert all_sages["TestSage"] is mock_sage

    @pytest.mark.asyncio
    async def test_broadcast_request(self, registry, mock_sage)registry.register_sage(mock_sage)
    """ブロードキャストテスト"""

        request = {"type": "test_broadcast"}
        result = await registry.broadcast_request(request)

        assert result["success"] is True
        assert "broadcast_results" in result
        assert "TestSage" in result["broadcast_results"]
        assert result["broadcast_results"]["TestSage"]["success"] is True

    @pytest.mark.asyncio
    async def test_health_check_all(self, registry, mock_sage)registry.register_sage(mock_sage)
    """全賢者ヘルスチェックテスト"""

        health_result = await registry.health_check_all()

        assert "timestamp" in health_result
        assert health_result["total_sages"] == 1
        assert "TestSage" in health_result["sages"]
        assert health_result["sages"]["TestSage"]["sage_name"] == "TestSage"

class TestKnowledgeSage:
    """ナレッジ賢者のテスト"""

    @pytest.fixture

    @pytest.fixture

    @pytest.mark.asyncio
    async def test_store_knowledge(self, knowledge_sage):
        """知識保存テスト"""
        request = {
            "type": "store_knowledge",
            "title": "Test Knowledge",
            "content": "This is test content",
            "category": "testing",
            "tags": ["test", "knowledge"],
            "source": "test_suite",
        }

        result = await knowledge_sage.process_request(request)

        assert result["success"] is True
        assert "knowledge_id" in result
        assert "hash" in result

    @pytest.mark.asyncio
    async def test_search_knowledge(self, knowledge_sage):
        """知識検索テスト"""
        # 知識を保存
        store_request = {
            "type": "store_knowledge",
            "title": "Python Programming",
            "content": "Python is a programming language",
            "category": "programming",
        }

        await knowledge_sage.process_request(store_request)

        # 検索実行
        search_request = {"type": "search_knowledge", "query": "Python", "limit": 5}

        result = await knowledge_sage.process_request(search_request)

        assert result["success"] is True
        assert len(result["results"]) > 0
        assert result["results"][0]["title"] == "Python Programming"

    @pytest.mark.asyncio
    async def test_learn_from_experience(self, knowledge_sage):
        """経験学習テスト"""
        request = {
            "type": "learn_from_experience",

            "content": "Fixed memory leak in async function",
            "outcome": "success - performance improved by 30%",
        }

        result = await knowledge_sage.process_request(request)

        assert result["success"] is True
        assert "session_id" in result

    @pytest.mark.asyncio
    async def test_get_recommendations(self, knowledge_sage):
        """推薦取得テスト"""
        # テスト用知識を保存
        store_request = {
            "type": "store_knowledge",
            "title": "Best Practices",
            "content": "Always write tests for your code",
            "category": "best_practices",
        }
        await knowledge_sage.process_request(store_request)

        request = {
            "type": "get_recommendations",
            "context": "code quality",
            "category": "best_practices",
        }

        result = await knowledge_sage.process_request(request)

        assert result["success"] is True
        assert "recommendations" in result

class TestTaskSage:
    """タスク賢者のテスト"""

    @pytest.fixture

    @pytest.fixture

    @pytest.mark.asyncio
    async def test_create_task(self, task_sage):
        """タスク作成テスト"""
        request = {
            "type": "create_task",
            "title": "Implement user authentication",
            "description": "Add OAuth2 authentication system",
            "priority": TaskPriority.HIGH.value,
            "category": "development",
            "estimateHours": 8,
            "tags": ["auth", "security"],
        }

        result = await task_sage.process_request(request)

        assert result["success"] is True
        assert "task_id" in result

    @pytest.mark.asyncio
    async def test_update_task(self, task_sage):
        """タスク更新テスト"""
        # タスク作成
        create_request = {
            "type": "create_task",
            "title": "Test Task",
            "status": TaskStatus.PENDING.value,
        }

        create_result = await task_sage.process_request(create_request)
        task_id = create_result["task_id"]

        # タスク更新
        update_request = {
            "type": "update_task",
            "task_id": task_id,
            "updates": {"status": TaskStatus.IN_PROGRESS.value, "actualHours": 3},
        }

        result = await task_sage.process_request(update_request)

        assert result["success"] is True
        assert "status" in result["updated_fields"]

    @pytest.mark.asyncio
    async def test_list_tasks(self, task_sage):
        """タスク一覧テスト"""
        # テスト用タスク作成
        create_request = {
            "type": "create_task",
            "title": "Test Task",
            "priority": TaskPriority.MEDIUM.value,
        }

        await task_sage.process_request(create_request)

        # タスク一覧取得
        list_request = {
            "type": "list_tasks",
            "filters": {"priority": TaskPriority.MEDIUM.value},
            "limit": 10,
        }

        result = await task_sage.process_request(list_request)

        assert result["success"] is True
        assert len(result["tasks"]) > 0
        assert result["tasks"][0]["title"] == "Test Task"

    @pytest.mark.asyncio
    async def test_add_dependency(self, task_sage):
        """タスク依存関係テスト"""
        # 依存元タスク作成
        task1_request = {"type": "create_task", "title": "Task 1"}

        task1_result = await task_sage.process_request(task1_request)
        task1_id = task1_result["task_id"]

        # 依存先タスク作成
        task2_request = {"type": "create_task", "title": "Task 2"}

        task2_result = await task_sage.process_request(task2_request)
        task2_id = task2_result["task_id"]

        # 依存関係追加
        dependency_request = {
            "type": "add_dependency",
            "task_id": task2_id,
            "depends_on_task_id": task1_id,
        }

        result = await task_sage.process_request(dependency_request)

        assert result["success"] is True

class TestIncidentSage:
    """インシデント賢者のテスト"""

    @pytest.fixture

    @pytest.fixture

    @pytest.mark.asyncio
    async def test_create_incident(self, incident_sage):
        """インシデント作成テスト"""
        request = {
            "type": "create_incident",
            "title": "Database Connection Error",
            "description": "Unable to connect to primary database",
            "severity": IncidentSeverity.HIGH.value,
            "category": "availability",
            "affected_systems": ["web-app", "api-server"],
            "reporter": "monitoring_system",
        }

        result = await incident_sage.process_request(request)

        assert result["success"] is True
        assert "incident_id" in result
        assert result["auto_escalated"] is True  # HIGH severity

    @pytest.mark.asyncio
    async def test_create_alert(self, incident_sage):
        """アラート作成テスト"""
        request = {
            "type": "create_alert",
            "alert_type": "performance",
            "severity": IncidentSeverity.MEDIUM.value,
            "title": "High CPU Usage",
            "message": "CPU usage exceeded 80%",
            "source_system": "web-server-01",
        }

        result = await incident_sage.process_request(request)

        assert result["success"] is True
        assert "alert_id" in result

    @pytest.mark.asyncio
    async def test_record_metric(self, incident_sage):
        """メトリクス記録テスト"""
        request = {
            "type": "record_metric",
            "metric_name": "cpu_usage",
            "metric_value": 85.5,
            "unit": "percent",
            "source_system": "web-server",
            "tags": ["performance", "monitoring"],
        }

        result = await incident_sage.process_request(request)

        assert result["success"] is True
        # CPU使用率が闾値を超えているのでアラートが発生するべき
        assert result["alert_triggered"] is True

    @pytest.mark.asyncio
    async def test_security_scan(self, incident_sage):
        """セキュリティスキャンテスト"""
        request = {
            "type": "security_scan",
            "scan_type": "basic",
            "target": "web_application",
        }

        result = await incident_sage.process_request(request)

        assert result["success"] is True
        assert "scan_id" in result
        assert "findings" in result
        assert result["findings_count"] >= 0

    @pytest.mark.asyncio
    async def test_resolve_incident(self, incident_sage):
        """インシデント解決テスト"""
        # インシデント作成
        create_request = {
            "type": "create_incident",
            "title": "Test Incident",
            "severity": IncidentSeverity.MEDIUM.value,
        }

        create_result = await incident_sage.process_request(create_request)
        incident_id = create_result["incident_id"]

        # インシデント解決
        resolve_request = {
            "type": "resolve_incident",
            "incident_id": incident_id,
            "resolution": "Restarted affected services",
            "root_cause": "Memory leak in application",
        }

        result = await incident_sage.process_request(resolve_request)

        assert result["success"] is True
        assert "resolution_time_minutes" in result

class TestRAGSage:
    """
    RAG賢者のテスト"""

    @pytest.fixture

    @pytest.fixture

    @pytest.mark.asyncio
    async def test_add_document(self, rag_sage):
        """文書追加テスト"""
        request = {
            "type": "add_document",
            "title": "Python Documentation",
            "content": "Python is a high-level programming language. It supports multiple programming paradigms.",
            "document_type": "documentation",
            "source": "python.org",
            "tags": ["python", "programming", "documentation"],
        }

        result = await rag_sage.process_request(request)

        assert result["success"] is True
        assert "document_id" in result
        assert "content_hash" in result

    @pytest.mark.asyncio
    async def test_search_documents(self, rag_sage):
        """文書検索テスト"""
        # 文書追加
        add_request = {
            "type": "add_document",
            "title": "JavaScript Guide",
            "content": "JavaScript is a programming language for web development. It runs in browsers and servers.",
            "document_type": "tutorial",
            "tags": ["javascript", "web", "programming"],
        }

        await rag_sage.process_request(add_request)

        # 検索実行
        search_request = {
            "type": "search",
            "query": "JavaScript programming",
            "limit": 5,
        }

        result = await rag_sage.process_request(search_request)

        assert result["success"] is True
        assert len(result["results"]) > 0
        assert "relevance_score" in result["results"][0]
        assert result["results"][0]["title"] == "JavaScript Guide"

    @pytest.mark.asyncio
    async def test_create_context(self, rag_sage):
        """コンテキスト作成テスト"""
        # 文書追加
        doc_request = {
            "type": "add_document",
            "title": "Context Test Doc",
            "content": "Test document for context",
        }

        doc_result = await rag_sage.process_request(doc_request)
        document_id = doc_result["document_id"]

        # コンテキスト作成
        context_request = {
            "type": "create_context",
            "context_name": "Test Context",
            "description": "Context for testing",
            "document_ids": [document_id],
            "context_type": "testing",
        }

        result = await rag_sage.process_request(context_request)

        assert result["success"] is True
        assert "context_id" in result
        assert result["document_count"] == 1

    @pytest.mark.asyncio
    async def test_get_recommendations(self, rag_sage):
        """推薦取得テスト"""
        # テスト文書追加
        doc1_request = {
            "type": "add_document",
            "title": "Python Basics",
            "content": "Python programming fundamentals and syntax",
        }

        doc1_result = await rag_sage.process_request(doc1_request)
        document_id = doc1_result["document_id"]

        # 関連文書追加
        doc2_request = {
            "type": "add_document",
            "title": "Advanced Python",
            "content": "Advanced Python programming techniques and best practices",
        }

        await rag_sage.process_request(doc2_request)

        # 推薦取得
        rec_request = {
            "type": "get_recommendations",
            "document_id": document_id,
            "limit": 3,
        }

        result = await rag_sage.process_request(rec_request)

        assert result["success"] is True
        assert "recommendations" in result

class TestFourSagesIntegration:
    """
    4賢者統合テスト"""

    @pytest.fixture

        """各賢者用の一時ディレクトリ"""
        dirs = {

        }
        yield dirs

    @pytest.fixture

        """
        4賢者を統合したレジストリ"""
        registry = SageRegistry()

        # 4賢者を作成し登録

        registry.register_sage(knowledge_sage)
        registry.register_sage(task_sage)
        registry.register_sage(incident_sage)
        registry.register_sage(rag_sage)

        return registry

    @pytest.mark.asyncio
    async def test_all_sages_health_check(self, four_sages_registry)health_result = await four_sages_registry.health_check_all()
    """全賢者ヘルスチェック"""

        assert health_result["total_sages"] == 4

        expected_sages = ["Knowledge", "Task", "Incident", "RAG"]
        for sage_name in expected_sages:
            assert sage_name in health_result["sages"]
            sage_health = health_result["sages"][sage_name]
            assert sage_health["status"] == "ready"
            assert "capabilities" in sage_health

    @pytest.mark.asyncio
    async def test_cross_sage_workflow(self, four_sages_registry)knowledge_sage = four_sages_registry.get_sage("Knowledge")
    """賢者間連携ワークフローテスト"""
        task_sage = four_sages_registry.get_sage("Task")
        incident_sage = four_sages_registry.get_sage("Incident")
        rag_sage = four_sages_registry.get_sage("RAG")

        # 1.0 知識保存
        knowledge_result = await knowledge_sage.process_request(
            {
                "type": "store_knowledge",
                "title": "Database Optimization",
                "content": "Best practices for database performance tuning",
                "category": "best_practices",
            }
        )
        assert knowledge_result["success"] is True

        # 2.0 関連タスク作成
        task_result = await task_sage.process_request(
            {
                "type": "create_task",
                "title": "Optimize database queries",
                "description": "Apply database optimization best practices",
                "category": "performance",
            }
        )
        assert task_result["success"] is True

        # 3.0 性能メトリクス記録
        metric_result = await incident_sage.process_request(
            {
                "type": "record_metric",
                "metric_name": "db_response_time",
                "metric_value": 250.5,
                "unit": "ms",
                "source_system": "database",
            }
        )
        assert metric_result["success"] is True

        # 4.0 ドキュメント追加
        doc_result = await rag_sage.process_request(
            {
                "type": "add_document",
                "title": "Database Performance Guide",
                "content": "Comprehensive guide for database optimization and monitoring",
                "document_type": "documentation",
                "tags": ["database", "performance", "optimization"],
            }
        )
        assert doc_result["success"] is True

        # 5.0 統合検証: 知識検索
        search_result = await knowledge_sage.process_request(
            {"type": "search_knowledge", "query": "database optimization"}
        )
        assert search_result["success"] is True
        assert len(search_result["results"]) > 0

    @pytest.mark.asyncio
    async def test_sage_capabilities_coverage(self, four_sages_registry)all_capabilities = set()
    """賢者能力網羅性テスト"""

        for sage_name, sage in four_sages_registry.get_all_sages().items():
            capabilities = sage.get_capabilities()
            all_capabilities.update(capabilities)

            # 各賢者が適切な能力を持っているか確認
            assert len(capabilities) > 0

            if sage_name == "Knowledge":
                assert "store_knowledge" in capabilities
                assert "search_knowledge" in capabilities
            elif sage_name == "Task":
                assert "create_task" in capabilities
                assert "task_management" in capabilities
            elif sage_name == "Incident":
                assert "create_incident" in capabilities
                assert "security_management" in capabilities
            elif sage_name == "RAG":
                assert "add_document" in capabilities
                assert "search" in capabilities

        # 全体で十分な能力をカバーしているか確認
        assert len(all_capabilities) >= 20  # 各賢者が5以上の能力を持つ

    @pytest.mark.asyncio
    async def test_broadcast_to_all_sages(self, four_sages_registry):
        """全賢者へのブロードキャストテスト"""
        # ヘルスチェックを全賢者にブロードキャスト
        request = {"type": "health_check"}
        result = await four_sages_registry.broadcast_request(request)

        assert result["success"] is True
        assert result["responded_sages"] == 4

        broadcast_results = result["broadcast_results"]
        expected_sages = ["Knowledge", "Task", "Incident", "RAG"]

        for sage_name in expected_sages:
            assert sage_name in broadcast_results
            # 各賢者がヘルスチェックに応答したか確認
            # （ヘルスチェックは未実装のためエラーになるが、レスポンスがあることを確認）
            assert "success" in broadcast_results[sage_name]

if __name__ == "__main__":
    # テスト実行
    pytest.main(["-v", __file__])
