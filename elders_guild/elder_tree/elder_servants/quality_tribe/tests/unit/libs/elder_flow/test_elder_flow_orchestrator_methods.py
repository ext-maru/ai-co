"""
Elder Flow Orchestrator新メソッドのテスト
Created: 2025-01-20
Author: Claude Elder
"""

import asyncio
import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from elders_guild.elder_tree.elder_flow_orchestrator import ElderFlowOrchestrator, FlowStatus


class TestElderFlowOrchestratorMethods:
    """ElderFlowOrchestratorの新しいメソッドのテスト"""

    @pytest.fixture
    def orchestrator(self):
        """テスト用のオーケストレーターインスタンス"""
        return ElderFlowOrchestrator()

    @pytest.mark.asyncio
    async def test_execute_sage_council_success(self, orchestrator):
        """execute_sage_council メソッドの正常系テスト"""
        request = {
            "task_name": "テストタスク",
            "priority": "high",
            "flow_id": str(uuid.uuid4())
        }

        # モックを使って4賢者システムの応答をシミュレート
        with patch.object(orchestrator.sage_council, 'hold_council_meeting') as mock_council:
            mock_council.return_value = {
                "individual_advice": {
                    "knowledge": {"advice": "知識の助言"},
                    "task": {"advice": "タスクの助言"},
                    "incident": {"advice": "インシデントの助言"},
                    "rag": {"advice": "RAGの助言"}
                },
                "integrated_advice": {
                    "recommended_approach": ["TDD実装", "セキュリティ重視"]
                },
                "consensus_reached": True
            }

            result = await orchestrator.execute_sage_council(request)

            assert result["status"] == "success"
            assert result["flow_id"] == request["flow_id"]
            assert "sage_advice" in result
            assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_execute_elder_servants_success(self, orchestrator):
        """execute_elder_servants メソッドの正常系テスト"""
        # まず賢者会議を実行してタスクを作成
        flow_id = str(uuid.uuid4())
        council_request = {
            "task_name": "テストタスク",
            "priority": "high",
            "flow_id": flow_id
        }

        with patch.object(orchestrator.sage_council, 'hold_council_meeting') as mock_council:
            mock_council.return_value = {
                "individual_advice": {},
                "integrated_advice": {},
                "consensus_reached": True
            }
            await orchestrator.execute_sage_council(council_request)

        # サーバント実行
        servant_request = {
            "task_name": "テストタスク",
            "flow_id": flow_id,
            "sage_recommendations": []
        }

        # サーバントファクトリとサーバントのモック
        with patch('libs.elder_flow_orchestrator.ServantFactory') as mock_factory:
            mock_servant = MagicMock()
            mock_servant.execute_task = asyncio.coroutine(lambda x: {"success": True, "results": {}})
            mock_factory.create_servant.return_value = mock_servant

            result = await orchestrator.execute_elder_servants(servant_request)

            assert result["status"] == "success"
            assert result["flow_id"] == flow_id
            assert "execution_plan" in result
            assert "execution_results" in result

    @pytest.mark.asyncio
    async def test_execute_quality_gate_success(self, orchestrator):
        """execute_quality_gate メソッドの正常系テスト"""
        # タスクを準備
        flow_id = str(uuid.uuid4())
        task = orchestrator.active_tasks[flow_id] = Mock()
        task.quality_results = {}
        task.execution_results = []

        quality_request = {
            "flow_id": flow_id,
            "implementation_results": {}
        }

        # 品質チェックのモック
        with patch('libs.elder_flow_orchestrator.ServantFactory') as mock_factory:
            mock_servant = MagicMock()
            mock_servant.execute_task = asyncio.coroutine(
                lambda x: {"success": True, "results": {"coverage": 85}}
            )
            mock_factory.create_servant.return_value = mock_servant

            result = await orchestrator.execute_quality_gate(quality_request)

            assert result["status"] == "success"
            assert result["flow_id"] == flow_id
            assert "quality_results" in result
            assert "overall_score" in result

    @pytest.mark.asyncio
    async def test_execute_council_report_success(self, orchestrator):
        """execute_council_report メソッドの正常系テスト"""
        # タスクを準備
        flow_id = str(uuid.uuid4())
        task = Mock()
        task.description = "テストタスク"
        task.task_id = flow_id
        task.status = FlowStatus.QUALITY_CHECK
        task.created_at = asyncio.get_event_loop().time()
        task.sage_advice = {"consensus_reached": True}
        task.quality_results = {"overall_score": 85}
        task.execution_results = [{"success": True}]
        task.add_log = Mock()

        orchestrator.active_tasks[flow_id] = task

        report_request = {
            "flow_id": flow_id,
            "all_results": {}
        }

        result = await orchestrator.execute_council_report(report_request)

        assert result["status"] == "success"
        assert result["flow_id"] == flow_id
        assert "council_report" in result
        assert task.add_log.called

    @pytest.mark.asyncio
    async def test_execute_git_automation_success(self, orchestrator):
        """execute_git_automation メソッドの正常系テスト"""
        # タスクを準備
        flow_id = str(uuid.uuid4())
        task = Mock()
        task.description = "テストタスク"
        task.git_commit_id = None
        task.add_log = Mock()

        orchestrator.active_tasks[flow_id] = task

        git_request = {
            "flow_id": flow_id,
            "implementation_results": {}
        }

        # Git操作のモック
        with patch('libs.elder_flow_orchestrator.ServantFactory') as mock_factory:
            mock_servant = MagicMock()
            mock_servant.execute_task = asyncio.coroutine(
                lambda x: {"success": True, "commit_id": "abc123"}
            )
            mock_factory.create_servant.return_value = mock_servant

            result = await orchestrator.execute_git_automation(git_request)

            assert result["status"] == "success"
            assert result["flow_id"] == flow_id
            assert "git_commit_id" in result
            assert "git_status" in result

    @pytest.mark.asyncio
    async def test_execute_sage_council_error(self, orchestrator):
        """execute_sage_council メソッドのエラー系テスト"""
        request = {
            "task_name": "エラーテストタスク",
            "priority": "high",
            "flow_id": str(uuid.uuid4())
        }

        # エラーを発生させる
        with patch.object(orchestrator.sage_council, 'hold_council_meeting') as mock_council:
            mock_council.side_effect = Exception("賢者会議エラー")

            result = await orchestrator.execute_sage_council(request)

            assert result["status"] == "error"
            assert result["flow_id"] == request["flow_id"]
            assert "error" in result
            assert "賢者会議エラー" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_elder_servants_no_task(self, orchestrator):
        """execute_elder_servants メソッドのタスク未存在テスト"""
        servant_request = {
            "task_name": "存在しないタスク",
            "flow_id": str(uuid.uuid4()),
            "sage_recommendations": []
        }

        result = await orchestrator.execute_elder_servants(servant_request)

        assert result["status"] == "error"
        assert "Task not found" in result["error"]

    @pytest.mark.asyncio
    async def test_full_flow_integration(self, orchestrator):
        """5つのメソッドを順次実行する統合テスト"""
        flow_id = str(uuid.uuid4())
        task_name = "統合テストタスク"

        # Phase 1: Sage Council
        with patch.object(orchestrator.sage_council, 'hold_council_meeting') as mock_council:
            mock_council.return_value = {
                "individual_advice": {},
                "integrated_advice": {"recommended_approach": ["TDD"]},
                "consensus_reached": True
            }
            
            council_result = await orchestrator.execute_sage_council({
                "task_name": task_name,
                "flow_id": flow_id
            })
            assert council_result["status"] == "success"

        # Phase 2: Elder Servants
        with patch('libs.elder_flow_orchestrator.ServantFactory') as mock_factory:
            mock_servant = MagicMock()
            mock_servant.execute_task = asyncio.coroutine(
                lambda x: {"success": True, "results": {}}
            )
            mock_factory.create_servant.return_value = mock_servant

            servant_result = await orchestrator.execute_elder_servants({
                "task_name": task_name,
                "flow_id": flow_id
            })
            assert servant_result["status"] == "success"

            # Phase 3: Quality Gate
            quality_result = await orchestrator.execute_quality_gate({
                "flow_id": flow_id
            })
            assert quality_result["status"] == "success"

            # Phase 4: Council Report
            report_result = await orchestrator.execute_council_report({
                "flow_id": flow_id
            })
            assert report_result["status"] == "success"

            # Phase 5: Git Automation
            git_result = await orchestrator.execute_git_automation({
                "flow_id": flow_id
            })
            assert git_result["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])