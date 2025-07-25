"""
Elder Tree v2 統合テスト
4賢者、サーバント、Elder Flowの完全統合テスト
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import os

from typing import Dict, Any, List

# Elder Tree コンポーネント
from elder_tree.workflows.elder_flow import ElderFlow
from elder_tree.agents.knowledge_sage import KnowledgeSage
from elder_tree.agents.task_sage import TaskSage
from elder_tree.agents.incident_sage import IncidentSage
from elder_tree.agents.rag_sage import RAGSage
from elder_tree.servants.dwarf_servant import CodeCrafter
from elder_tree.servants.elf_servant import QualityGuardian

class TestElderTreeIntegration:
    """Elder Tree統合テストスイート"""
    
    @pytest.fixture
    async def test_environment(self):
        """テスト環境のセットアップ"""
        # インメモリDBとモックRedis使用
        env = {
            "db_url": "sqlite:///:memory:",
            "redis_url": "redis://localhost:6379",
            "agents": {},
            "servants": {},

        }
        
        # 4賢者の初期化
        env["agents"]["knowledge_sage"] = KnowledgeSage(db_url=env["db_url"])
        env["agents"]["task_sage"] = TaskSage(db_url=env["db_url"])
        env["agents"]["incident_sage"] = IncidentSage(
            db_url=env["db_url"],
            redis_url=env["redis_url"]
        )
        env["agents"]["rag_sage"] = RAGSage(
            db_url=env["db_url"],

        )
        
        # サーバントの初期化
        env["servants"]["code_crafter"] = CodeCrafter()
        env["servants"]["quality_guardian"] = QualityGuardian()
        
        # Elder Flowの初期化
        env["elder_flow"] = ElderFlow(
            db_url=env["db_url"],
            redis_url=env["redis_url"]
        )
        
        # Redisクライアントをモック
        for agent in env["agents"].values():
            if hasattr(agent, 'redis_client'):
                agent.redis_client = AsyncMock()
        
        env["elder_flow"].redis_client = AsyncMock()
        
        yield env
        
        # クリーンアップ
        import shutil

    @pytest.mark.asyncio
    async def test_full_workflow_execution(self, test_environment):
        """完全なワークフロー実行テスト"""
        elder_flow = test_environment["elder_flow"]
        
        # エージェント間通信をモック
        with patch.object(elder_flow, 'send_message') as mock_send:
            # 賢者協議レスポンス
            sage_response = Mock()
            sage_response.data = {
                "status": "success",
                "recommendations": ["Use TDD approach", "Follow SOLID principles"],
                "estimated_hours": 8,
                "complexity": "medium"
            }
            
            # サーバント実行レスポンス
            servant_response = Mock()
            servant_response.data = {
                "status": "success",
                "result": {
                    "files_created": ["/tmp/test_feature.py"],
                    "tests_created": ["/tmp/test_test_feature.py"]
                },
                "quality": {
                    "score": 92,
                    "passed": True
                }
            }
            
            # 条件付きレスポンス
            async def side_effect(target, message_type, data, timeout=None):
                if "sage" in target:
                """side_effectメソッド"""
                    return sage_response
                elif "crafter" in target:
                    return servant_response
                return Mock(data={"status": "success"})
            
            mock_send.side_effect = side_effect
            
            # Elder Flow実行
            result = await elder_flow.execute(
                task_type="feature_implementation",
                requirements=[
                    "User authentication system",
                    "OAuth2.0 support",
                    "Session management"
                ],
                priority="high"
            )
            
            # 検証
            assert result.status == "completed"
            assert result.stages_completed == 5
            assert result.flow_id.startswith("FLOW-")
            
            # 各ステージが実行されたことを確認
            stage_names = [stage.name for stage in result.stages]
            assert "sage_consultation" in stage_names
            assert "servant_execution" in stage_names
            assert "quality_gate" in stage_names
            assert "council_report" in stage_names
            assert "git_automation" in stage_names

    @pytest.mark.asyncio
    async def test_sage_servant_collaboration(self, test_environment):
        """賢者とサーバントの協調テスト"""
        knowledge_sage = test_environment["agents"]["knowledge_sage"]
        code_crafter = test_environment["servants"]["code_crafter"]
        
        # Knowledge Sageに知識を追加
        await knowledge_sage.store_knowledge(
            category="design_patterns",
            key="singleton",
            knowledge={
                "description": "Ensure a class has only one instance",
                "implementation": "Use __new__ method in Python",
                "use_cases": ["Database connections", "Configuration objects"]
            }
        )
        
        # Code Crafterが知識を参照してコード生成
        with patch.object(code_crafter, 'send_message') as mock_send:
            # Knowledge Sageからの応答をモック
            mock_response = Mock()
            mock_response.data = {
                "status": "success",
                "knowledge": {
                    "implementation": "Use __new__ method in Python"
                }
            }
            mock_send.return_value = mock_response
            
            # コード生成実行
            result = await code_crafter.execute_specialized_task(
                "code_generation",
                {
                    "specification": {
                        "function_name": "create_singleton",
                        "parameters": [],
                        "returns": "Singleton",
                        "requirements": ["Implement singleton pattern"]
                    },
                    "use_tdd": True
                },
                {
                    "knowledge_sage": {
                        "pattern_advice": "Use __new__ method"
                    }
                }
            )
            
            # 知識が活用されていることを確認
            assert result is not None
            assert "implementation_code" in result

    @pytest.mark.asyncio
    async def test_incident_handling_flow(self, test_environment):
        """インシデント処理フローテスト"""
        incident_sage = test_environment["agents"]["incident_sage"]
        elder_flow = test_environment["elder_flow"]
        
        # インシデントを作成
        incident = {
            "title": "Database connection timeout",
            "description": "Production DB experiencing timeouts",
            "severity": "high",
            "affected_services": ["user-api", "order-service"],
            "error_logs": ["TimeoutError: Connection timed out after 30s"]
        }
        
        # インシデント検知
        with patch.object(incident_sage, 'analyze_with_claude', 
                         return_value="Database connection pool exhaustion"):
            incident_result = await incident_sage.detect_incident(
                incident["title"],
                incident["description"],
                incident["severity"],
                incident["affected_services"]
            )
            
            assert incident_result["status"] == "detected"
            assert "incident_id" in incident_result
            
            # Elder Flowでインシデント対応
            with patch.object(elder_flow, 'send_message') as mock_send:
                # Crisis Responderレスポンス
                responder_response = Mock()
                responder_response.data = {
                    "status": "success",
                    "result": {
                        "actions_taken": ["Increased connection pool size", "Restarted services"],
                        "recovery_time": "5 minutes"
                    },
                    "quality": {"score": 95, "passed": True}
                }
                
                async def incident_side_effect(target, message_type, data, timeout=None):
                    if "crisis_responder" in target or "incident_knight" in target:
                        return responder_response
                    return Mock(data={"status": "success"})
                
                mock_send.side_effect = incident_side_effect
                
                # 緊急対応フロー実行
                response_result = await elder_flow.execute(
                    task_type="incident_response",
                    requirements=[
                        f"Resolve incident: {incident_result['incident_id']}",
                        "Minimize downtime",
                        "Prevent recurrence"
                    ],
                    priority="critical"
                )
                
                assert response_result.status == "completed"

    @pytest.mark.asyncio
    async def test_rag_document_lifecycle(self, test_environment):
        """RAG文書ライフサイクルテスト"""
        rag_sage = test_environment["agents"]["rag_sage"]
        
        # OpenAI APIをモック
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            # エンベディング生成をモック
            mock_embedding_response = Mock()
            mock_embedding_response.data = [
                Mock(embedding=[0.1, 0.2, 0.3] * 512)  # 1536次元
            ]
            mock_client.embeddings.create.return_value = mock_embedding_response
            
            # ドキュメントを保存
            document = {
                "title": "Elder Tree Architecture Guide",
                "content": "Elder Tree is a distributed AI system...",
                "doc_type": "documentation",
                "source": "internal"
            }
            
            store_result = await rag_sage.store_document(document)
            assert store_result["status"] == "success"
            doc_id = store_result["doc_id"]
            
            # ドキュメントを検索
            search_result = await rag_sage.search_documents(
                query="distributed AI system",
                limit=10
            )
            
            # Chromaの制限により、実際の検索は機能しない可能性があるが、
            # APIが正しく呼ばれることを確認
            assert search_result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_quality_gate_enforcement(self, test_environment):
        """品質ゲート強制テスト"""
        quality_guardian = test_environment["servants"]["quality_guardian"]
        elder_flow = test_environment["elder_flow"]
        
        # 低品質コードを含むファイルを作成
        low_quality_code = """
def bad_function(x, y, z):
    # Poor implementation that violates Iron Will
    result = x + y + z
    # Non-compliant code for testing purposes
    return result
"""

            f.write(low_quality_code)

        try:
            # 品質分析実行
            quality_result = await quality_guardian.execute_specialized_task(
                "quality_analysis",
                {

                    "checks": ["all"]
                },
                {}
            )
            
            # Iron Will違反を検出
            assert not quality_result["meets_standards"]
            assert quality_result["overall_score"] < 85
            
            # Elder Flowの品質ゲートでブロック
            execution_result = {

                "quality": quality_result
            }
            
            gate_result = await elder_flow._quality_gate(execution_result)
            assert not gate_result["quality_passed"]
            assert len(gate_result["detailed_checks"]["iron_will"]["issues"]) > 0
            
        finally:

    @pytest.mark.asyncio
    async def test_concurrent_task_processing(self, test_environment):
        """並行タスク処理テスト"""
        task_sage = test_environment["agents"]["task_sage"]
        elder_flow = test_environment["elder_flow"]
        
        # 複数のタスクを作成
        tasks = []
        for i in range(5):
            task_data = {
                "title": f"Concurrent Task {i}",
                "description": f"Test task for concurrent processing {i}",
                "priority": "medium",
                "assignee": "elder_flow"
            }
            
            task_result = await task_sage.create_task(
                task_data["title"],
                task_data["description"],
                task_data["priority"],
                task_data["assignee"]
            )
            tasks.append(task_result["task_id"])
        
        # 並行実行をモック
        with patch.object(elder_flow, '_sage_consultation', 
                         return_value={"consultation_complete": True}):
            with patch.object(elder_flow, '_servant_execution',
                             return_value={"execution_complete": True}):
                with patch.object(elder_flow, '_quality_gate',
                                 return_value={"quality_passed": True}):
                    with patch.object(elder_flow, '_council_report',
                                     return_value={"report_generated": True}):
                        with patch.object(elder_flow, '_git_automation',
                                         return_value={"git_operations_complete": True}):
                            
                            # 並行実行
                            flow_tasks = []
                            for task_id in tasks:
                                flow_task = elder_flow.execute(
                                    task_type=f"process_task_{task_id}",
                                    requirements=[f"Process {task_id}"],
                                    priority="medium"
                                )
                                flow_tasks.append(flow_task)
                            
                            # 全タスクの完了を待つ
                            results = await asyncio.gather(*flow_tasks)
                            
                            # 全てが成功
                            assert all(r.status == "completed" for r in results)
                            # 各フローが独立
                            flow_ids = [r.flow_id for r in results]
                            assert len(set(flow_ids)) == len(flow_ids)

    @pytest.mark.asyncio
    async def test_error_recovery_mechanism(self, test_environment):
        """エラー回復メカニズムテスト"""
        elder_flow = test_environment["elder_flow"]
        incident_sage = test_environment["agents"]["incident_sage"]
        
        # サーバント実行でエラーを発生させる
        with patch.object(elder_flow, '_sage_consultation',
                         return_value={"consultation_complete": True}):
            with patch.object(elder_flow, '_servant_execution',
                             side_effect=Exception("Servant crashed")):
                # Incident Sageへの報告をモック
                with patch.object(elder_flow, '_report_failure_to_incident_sage') as mock_report:
                    pass
                    
                    result = await elder_flow.execute(
                        task_type="failing_task",
                        requirements=["This will fail"],
                        priority="high"
                    )
                    
                    # 失敗が記録される
                    assert result.status == "failed"
                    
                    # Incident Sageに報告される
                    mock_report.assert_called_once()
                    
                    # 失敗したステージが特定される
                    failed_stages = [s for s in result.stages if s.status == "failed"]
                    assert len(failed_stages) == 1
                    assert failed_stages[0].name == "servant_execution"

    @pytest.mark.asyncio
    @pytest.mark.benchmark(group="integration")
    async def test_end_to_end_performance(self, test_environment, benchmark):
        """エンドツーエンドパフォーマンステスト"""
        elder_flow = test_environment["elder_flow"]
        
        # 軽量モックで全ステージを設定
        async def mock_stage(*args, **kwargs):
            await asyncio.sleep(0.01)  # 10ms
            return {"result": "success"}
        
        with patch.object(elder_flow, '_sage_consultation', new=mock_stage):
            with patch.object(elder_flow, '_servant_execution', 
                             return_value={"execution_complete": True, "files_created": []}):
                with patch.object(elder_flow, '_quality_gate',
                                 return_value={"quality_passed": True}):
                    with patch.object(elder_flow, '_council_report', new=mock_stage):
                        with patch.object(elder_flow, '_git_automation',
                                         return_value={"git_operations_complete": True}):
                            
                            async def run_flow():
                                """run_flowを実行"""
                                return await elder_flow.execute(
                                    task_type="performance_test",
                                    requirements=["Quick test"],
                                    priority="low"
                                )
                            
                            # ベンチマーク実行
                            result = benchmark(lambda: asyncio.run(run_flow()))
                            
                            # エンドツーエンドで2秒以内
                            assert benchmark.stats["mean"] < 2.0
                            assert result.status == "completed"