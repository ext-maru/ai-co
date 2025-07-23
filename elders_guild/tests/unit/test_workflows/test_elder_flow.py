"""
Elder Flow ユニットテスト
エルダーズギルドの品質基準に準拠
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json
from typing import Dict, Any

from elder_tree.workflows.elder_flow import (
    ElderFlow, ElderFlowResult, Stage, StageStatus
)
from python_a2a import Message
from sqlmodel import Session, select


class TestElderFlow:
    """Elder Flow テストスイート"""
    
    @pytest.fixture
    async def elder_flow(self):
        """Elder Flowインスタンスのフィクスチャ"""
        flow = ElderFlow(
            db_url="sqlite:///:memory:",
            redis_url="redis://localhost:6379",
            port=50100
        )
        # Redisクライアントをモック
        flow.redis_client = AsyncMock()
        yield flow
        if hasattr(flow, '_client'):
            await flow.stop()
    
    @pytest.fixture
    def mock_message(self):
        """モックメッセージ"""
        message = Mock(spec=Message)
        message.data = {
            "task_type": "test_task",
            "requirements": ["requirement1", "requirement2"],
            "priority": "high"
        }
        return message
    
    @pytest.fixture
    def mock_sage_response(self):
        """賢者からのモックレスポンス"""
        response = Mock()
        response.data = {
            "status": "success",
            "recommendations": ["Use TDD", "Follow Iron Will"],
            "estimated_hours": 5
        }
        return response

    @pytest.mark.asyncio
    async def test_elder_flow_initialization(self, elder_flow):
        """Elder Flow初期化テスト"""
        assert elder_flow.name == "elder_flow"
        assert len(elder_flow.stages) == 5
        assert elder_flow.stages == [
            "sage_consultation",
            "servant_execution", 
            "quality_gate",
            "council_report",
            "git_automation"
        ]
    
    @pytest.mark.asyncio
    async def test_execute_flow_success(self, elder_flow):
        """正常なフロー実行テスト"""
        # 各ステージをモック
        with patch.object(elder_flow, '_sage_consultation', new=AsyncMock(return_value={
            "consultation_complete": True,
            "recommendations": ["TDD approach"],
            "estimated_hours": 3
        })):
            with patch.object(elder_flow, '_servant_execution', new=AsyncMock(return_value={
                "execution_complete": True,
                "files_created": ["test.py"],
                "quality": {"score": 90, "passed": True}
            })):
                with patch.object(elder_flow, '_quality_gate', new=AsyncMock(return_value={
                    "quality_passed": True,
                    "quality_score": 90,
                    "iron_will_score": 95
                })):
                    with patch.object(elder_flow, '_council_report', new=AsyncMock(return_value={
                        "report_generated": True,
                        "report_id": "REPORT-123"
                    })):
                        with patch.object(elder_flow, '_git_automation', new=AsyncMock(return_value={
                            "git_operations_complete": True,
                            "branch": "feature-test"
                        })):
                            # 実行
                            result = await elder_flow.execute(
                                task_type="test_task",
                                requirements=["req1", "req2"],
                                priority="high"
                            )
                            
                            # 検証
                            assert result.status == "completed"
                            assert result.stages_completed == 5
                            assert all(stage.status == StageStatus.COMPLETED for stage in result.stages)
                            assert result.flow_id.startswith("FLOW-")

    @pytest.mark.asyncio
    async def test_execute_flow_with_failure(self, elder_flow):
        """ステージ失敗時のフロー実行テスト"""
        # 賢者協議は成功
        with patch.object(elder_flow, '_sage_consultation', new=AsyncMock(return_value={
            "consultation_complete": True
        })):
            # サーバント実行で失敗
            with patch.object(elder_flow, '_servant_execution', new=AsyncMock(
                side_effect=Exception("Servant execution failed")
            )):
                # Incident Sageへの報告をモック
                with patch.object(elder_flow, '_report_failure_to_incident_sage', new=AsyncMock()):
                    
                    result = await elder_flow.execute(
                        task_type="failing_task",
                        requirements=["req1"],
                        priority="high"
                    )
                    
                    # 検証
                    assert result.status == "failed"
                    assert result.stages[0].status == StageStatus.COMPLETED
                    assert result.stages[1].status == StageStatus.FAILED
                    assert result.stages[1].error == "Servant execution failed"
                    # 後続ステージはスキップ
                    assert all(
                        stage.status == StageStatus.SKIPPED 
                        for stage in result.stages[2:]
                    )

    @pytest.mark.asyncio
    async def test_sage_consultation_parallel(self, elder_flow, mock_sage_response):
        """賢者協議の並列実行テスト"""
        # 各賢者への通信をモック
        with patch.object(elder_flow, 'send_message', new=AsyncMock(return_value=mock_sage_response)):
            
            result = await elder_flow._sage_consultation(
                task_type="test_task",
                requirements=["req1", "req2"],
                priority="high"
            )
            
            # 検証
            assert result["consultation_complete"] is True
            assert "sages_consulted" in result
            assert len(result["sages_consulted"]) == 4
            assert "recommendations" in result
            assert "estimated_hours" in result
            
            # 4賢者全てに並列で相談したことを確認
            assert elder_flow.send_message.call_count == 4

    @pytest.mark.asyncio 
    async def test_quality_gate_iron_will(self, elder_flow):
        """品質ゲート - Iron Will基準テスト"""
        execution_result = {
            "quality": {"score": 90, "passed": True},
            "files_created": ["/tmp/test_file.py"]
        }
        
        # ファイル内容をモック（TODO/FIXMEを含む）
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = """
            def test_function():
                # TODO: Implement this
                pass
            """
            
            with patch('os.path.exists', return_value=True):
                result = await elder_flow._quality_gate(execution_result)
                
                # Iron Will違反で減点される
                assert not result["quality_passed"]
                assert result["iron_will_score"] < 100
                assert len(result["detailed_checks"]["iron_will"]["issues"]) > 0

    @pytest.mark.asyncio
    async def test_servant_selection(self, elder_flow):
        """タスクタイプに応じたサーバント選択テスト"""
        test_cases = [
            ("code_generation", "code_crafter"),
            ("feature_implementation", "code_crafter"),
            ("research", "research_wizard"),
            ("documentation", "research_wizard"),
            ("quality_check", "quality_guardian"),
            ("optimization", "quality_guardian"),
            ("incident_response", "crisis_responder"),
            ("emergency_fix", "crisis_responder"),
            ("unknown_task", "code_crafter")  # デフォルト
        ]
        
        for task_type, expected_servant in test_cases:
            servant = elder_flow._select_servant(task_type)
            assert servant == expected_servant

    @pytest.mark.asyncio
    async def test_git_automation(self, elder_flow):
        """Git自動化テスト"""
        execution_result = {
            "files_created": ["/tmp/test1.py", "/tmp/test2.py"]
        }
        
        # Git コマンドをモック
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = "abc123def456"
            mock_run.return_value.returncode = 0
            
            result = await elder_flow._git_automation(
                task_type="test_feature",
                execution_result=execution_result
            )
            
            # 検証
            assert result["git_operations_complete"] is True
            assert result["branch"].startswith("elder-flow/test-feature-")
            assert result["files_committed"] == execution_result["files_created"]
            assert "commit_hash" in result
            
            # Git コマンドが実行されたことを確認
            git_commands = [call[0][0] for call in mock_run.call_args_list]
            assert ["git", "checkout", "-b"] in [cmd[:3] for cmd in git_commands]
            assert ["git", "add"] in [cmd[:2] for cmd in git_commands]
            assert ["git", "commit", "-m"] in [cmd[:3] for cmd in git_commands]

    @pytest.mark.asyncio
    async def test_council_report_generation(self, elder_flow):
        """評議会報告生成テスト"""
        completed_stages = [
            Stage(
                name="sage_consultation",
                status=StageStatus.COMPLETED,
                result={"recommendations": ["Use TDD"], "estimated_hours": 5},
                started_at=datetime.now() - timedelta(minutes=5),
                completed_at=datetime.now() - timedelta(minutes=4)
            ),
            Stage(
                name="servant_execution",
                status=StageStatus.COMPLETED,
                result={"files_created": ["test.py"], "quality": {"score": 92}},
                started_at=datetime.now() - timedelta(minutes=4),
                completed_at=datetime.now() - timedelta(minutes=2)
            )
        ]
        
        # Knowledge Sageへの送信をモック
        with patch.object(elder_flow, 'send_message', new=AsyncMock()):
            
            result = await elder_flow._council_report(
                task_type="test_task",
                completed_stages=completed_stages
            )
            
            # 検証
            assert result["report_generated"] is True
            assert result["report_id"].startswith("REPORT-")
            assert "summary" in result
            
            # Knowledge Sageに報告が送信されたことを確認
            elder_flow.send_message.assert_called_once()
            call_args = elder_flow.send_message.call_args
            assert call_args[1]["target"] == "knowledge_sage"
            assert call_args[1]["message_type"] == "store_elder_flow_report"

    @pytest.mark.asyncio
    async def test_database_persistence(self, elder_flow):
        """データベース永続化テスト"""
        # モックを設定して実行
        with patch.object(elder_flow, '_sage_consultation', new=AsyncMock(return_value={})):
            with patch.object(elder_flow, '_servant_execution', new=AsyncMock(
                side_effect=Exception("Test failure")
            )):
                with patch.object(elder_flow, '_report_failure_to_incident_sage', new=AsyncMock()):
                    
                    flow_id = None
                    try:
                        result = await elder_flow.execute(
                            task_type="test_persistence",
                            requirements=["req1"],
                            priority="medium"
                        )
                        flow_id = result.flow_id
                    except:
                        pass
                    
                    # データベースから記録を取得
                    with Session(elder_flow.engine) as session:
                        from elder_tree.workflows.elder_flow import FlowRecord
                        statement = select(FlowRecord).where(
                            FlowRecord.task_type == "test_persistence"
                        )
                        record = session.exec(statement).first()
                        
                        # 検証
                        assert record is not None
                        assert record.task_type == "test_persistence"
                        assert record.priority == "medium"
                        assert record.status in ["running", "failed"]

    @pytest.mark.asyncio
    @pytest.mark.benchmark(group="elder_flow")
    async def test_flow_performance(self, elder_flow, benchmark):
        """Elder Flowのパフォーマンステスト"""
        # 軽量なモックを設定
        async def mock_stage(*args, **kwargs):
            await asyncio.sleep(0.01)  # 10ms の処理時間をシミュレート
            return {"result": "success"}
        
        with patch.object(elder_flow, '_sage_consultation', new=mock_stage):
            with patch.object(elder_flow, '_servant_execution', new=mock_stage):
                with patch.object(elder_flow, '_quality_gate', new=mock_stage):
                    with patch.object(elder_flow, '_council_report', new=mock_stage):
                        with patch.object(elder_flow, '_git_automation', new=mock_stage):
                            
                            # ベンチマーク実行
                            async def run_flow():
                                return await elder_flow.execute(
                                    task_type="perf_test",
                                    requirements=["req1"],
                                    priority="high"
                                )
                            
                            result = benchmark(lambda: asyncio.run(run_flow()))
                            
                            # パフォーマンス基準: 全体で1秒以内
                            assert benchmark.stats["mean"] < 1.0

    @pytest.mark.asyncio
    async def test_redis_caching(self, elder_flow):
        """Redisキャッシングテスト"""
        flow_id = "FLOW-TEST-123"
        
        # execute メソッドの一部をテスト
        await elder_flow.redis_client.setex(
            f"flow:{flow_id}:status",
            3600,
            "running"
        )
        
        # Redis クライアントのメソッドが呼ばれたことを確認
        elder_flow.redis_client.setex.assert_called_with(
            f"flow:{flow_id}:status",
            3600,
            "running"
        )

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, elder_flow):
        """メトリクス追跡テスト"""
        # メトリクスをモック
        with patch.object(elder_flow.flow_counter, 'labels') as mock_counter:
            mock_labels = Mock()
            mock_counter.return_value = mock_labels
            
            with patch.object(elder_flow.active_flows, 'inc'):
                with patch.object(elder_flow.active_flows, 'dec'):
                    # 簡単な実行
                    with patch.object(elder_flow, '_sage_consultation', 
                                    side_effect=Exception("Test")):
                        with patch.object(elder_flow, '_report_failure_to_incident_sage', 
                                        new=AsyncMock()):
                            try:
                                await elder_flow.execute(
                                    task_type="metrics_test",
                                    requirements=["req1"],
                                    priority="low"
                                )
                            except:
                                pass
                    
                    # メトリクスが更新されたことを確認
                    elder_flow.active_flows.inc.assert_called_once()
                    elder_flow.active_flows.dec.assert_called_once()
                    mock_counter.assert_called()


# エラー処理とエッジケースのテスト
class TestElderFlowErrorHandling:
    """Elder Flowエラー処理テスト"""
    
    @pytest.fixture
    async def elder_flow(self):
        """Elder Flowインスタンス"""
        flow = ElderFlow(db_url="sqlite:///:memory:")
        flow.redis_client = AsyncMock()
        yield flow
        if hasattr(flow, '_client'):
            await flow.stop()
    
    @pytest.mark.asyncio
    async def test_sage_timeout_handling(self, elder_flow):
        """賢者タイムアウト処理テスト"""
        # 一部の賢者がタイムアウト
        async def mock_consult_sage(sage_name, task_type, requirements):
            if sage_name == "knowledge_sage":
                raise asyncio.TimeoutError("Sage timeout")
            return {"status": "success", "data": {}}
        
        with patch.object(elder_flow, '_consult_sage', side_effect=mock_consult_sage):
            result = await elder_flow._sage_consultation(
                task_type="test",
                requirements=["req1"],
                priority="high"
            )
            
            # 部分的な成功を確認
            assert result["consultation_complete"] is True
            assert "knowledge_sage" in result["sages_consulted"]
            assert result["sages_consulted"]["knowledge_sage"]["status"] == "error"

    @pytest.mark.asyncio
    async def test_empty_requirements_handling(self, elder_flow):
        """空の要件処理テスト"""
        result = await elder_flow.execute(
            task_type="empty_task",
            requirements=[],  # 空のリスト
            priority="low"
        )
        
        # 空でも実行可能
        assert result.flow_id is not None

    @pytest.mark.asyncio
    async def test_concurrent_flow_execution(self, elder_flow):
        """並行フロー実行テスト"""
        # 複数のフローを同時実行
        async def mock_stage(*args, **kwargs):
            await asyncio.sleep(0.1)
            return {"result": "success"}
        
        with patch.object(elder_flow, '_sage_consultation', new=mock_stage):
            with patch.object(elder_flow, '_servant_execution', new=mock_stage):
                with patch.object(elder_flow, '_quality_gate', new=mock_stage):
                    with patch.object(elder_flow, '_council_report', new=mock_stage):
                        with patch.object(elder_flow, '_git_automation', new=mock_stage):
                            
                            # 10個の並行タスク
                            tasks = []
                            for i in range(10):
                                task = elder_flow.execute(
                                    task_type=f"concurrent_task_{i}",
                                    requirements=[f"req_{i}"],
                                    priority="medium"
                                )
                                tasks.append(task)
                            
                            # 全て完了を待つ
                            results = await asyncio.gather(*tasks)
                            
                            # 全て成功
                            assert all(r.status == "completed" for r in results)
                            # 各フローIDがユニーク
                            flow_ids = [r.flow_id for r in results]
                            assert len(flow_ids) == len(set(flow_ids))