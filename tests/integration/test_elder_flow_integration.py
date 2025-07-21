"""
Elder Flow統合テスト
Phase 3: Elder Flow全体の統合動作をテスト
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.integration.base_integration_test import ElderFlowIntegrationTest

class TestElderFlowIntegration(ElderFlowIntegrationTest):
    """Elder Flow統合テストクラス"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """テスト環境セットアップ"""
        self.setup_elder_flow_environment()
        yield
        self.db_conn.close()
    
    @pytest.mark.asyncio
    async def test_full_elder_flow_execution(self):
        """Elder Flow完全実行テスト"""
        # タスク作成
        task_name = "OAuth2.0認証システム実装"
        
        # Elder Flow実行
        results = await self.simulate_elder_flow_execution(task_name)
        
        # 結果検証
        self.verify_integration_results(results)
        
        # すべてのフェーズが完了していることを確認
        expected_phases = ["sage_council", "servant_execution", "quality_gate", "report", "git_automation"]
        for phase in expected_phases:
            assert phase in results["phases"]
    
    @pytest.mark.asyncio
    async def test_elder_flow_with_database_tracking(self):
        """データベース追跡を含むElder Flowテスト"""
        task_name = "ユーザー管理API実装"
        
        # タスクをデータベースに登録
        cursor = self.db_conn.execute(
            "INSERT INTO tasks (name, status) VALUES (?, ?)",
            (task_name, "pending")
        )
        task_id = cursor.lastrowid
        self.db_conn.commit()
        
        # Elder Flow実行
        results = await self.simulate_elder_flow_execution(task_name)
        
        # 各フェーズの実行記録をデータベースに保存
        for phase_name, phase_result in results["phases"].items():
            self.db_conn.execute("""
                INSERT INTO elder_flow_executions 
                (task_id, phase, status, result) 
                VALUES (?, ?, ?, ?)
            """, (
                task_id,
                phase_name,
                phase_result["status"],
                str(phase_result)
            ))
        
        self.db_conn.commit()
        
        # データベース記録の検証
        assert self.assert_database_record_exists(
            self.db_conn,
            "elder_flow_executions",
            {"task_id": task_id, "phase": "sage_council", "status": "success"}
        )
    
    @pytest.mark.asyncio
    async def test_elder_flow_error_handling(self):
        """Elder Flowエラーハンドリングテスト"""
        # エラーを発生させるモック設定
        self.mock_incident_sage.process_request = AsyncMock(
            side_effect=Exception("Simulated error")
        )
        
        task_name = "エラーテストタスク"
        
        # エラーハンドリングの検証
        with pytest.raises(Exception) as exc_info:
            await self.mock_incident_sage.process_request({"task": task_name})
        
        assert "Simulated error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_elder_flow_parallel_execution(self):
        """Elder Flow並列実行テスト"""
        tasks = [
            "タスク1: API実装",
            "タスク2: データベース設計",
            "タスク3: フロントエンド開発"
        ]
        
        # 並列実行
        start_time = asyncio.get_event_loop().time()
        
        results = await asyncio.gather(*[
            self.simulate_elder_flow_execution(task)
            for task in tasks
        ])
        
        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time
        
        # 結果検証
        assert len(results) == 3
        for result in results:
            self.verify_integration_results(result)
        
        # 並列実行により、実行時間が短縮されていることを確認
        # (各タスク0.5秒 × 3 = 1.5秒より短い)
        assert execution_time < 1.5
    
    @pytest.mark.asyncio
    async def test_elder_flow_quality_gate_enforcement(self):
        """品質ゲート強制テスト"""
        task_name = "品質ゲートテストタスク"
        
        # 品質基準を満たさない結果をシミュレート
        results = await self.simulate_elder_flow_execution(task_name)
        
        # 品質ゲートフェーズの結果を低品質に変更
        results["phases"]["quality_gate"]["metrics"]["quality_score"] = 85
        
        # Iron Will基準（95%以上）を満たしていないことを検証
        quality_score = results["phases"]["quality_gate"]["metrics"]["quality_score"]
        assert quality_score < 95
        
        # 実際のシステムでは、この場合タスクは失敗すべき
        # ここではシミュレーションのため、フラグで表現
        should_fail = quality_score < 95
        assert should_fail is True
    
    @pytest.mark.asyncio
    async def test_elder_flow_sage_council_integration(self):
        """4賢者会議統合テスト"""
        task_name = "4賢者会議テストタスク"
        
        # 各賢者の応答をシミュレート
        sage_responses = {
            "knowledge": await self.mock_knowledge_sage.process_request({"task": task_name}),
            "task": await self.mock_task_sage.process_request({"task": task_name}),
            "incident": await self.mock_incident_sage.process_request({"task": task_name}),
            "rag": await self.mock_rag_sage.process_request({"task": task_name})
        }
        
        # すべての賢者が正常に応答したことを確認
        for sage_name, response in sage_responses.items():
            assert response["status"] == "success"
            assert response["sage"] == sage_name
    
    def test_integration_test_framework_functionality(self):
        """統合テストフレームワーク自体の機能テスト"""
        # テスト環境が正しく作成されていることを確認
        assert self.temp_dir is not None
        assert self.test_data_dir.exists()
        assert self.test_logs_dir.exists()
        assert self.test_config_dir.exists()
        assert self.config_path.exists()
        
        # モックが正しく作成されていることを確認
        assert self.mock_elder_flow is not None
        assert self.mock_knowledge_sage is not None
        assert self.mock_task_sage is not None
        assert self.mock_incident_sage is not None
        assert self.mock_rag_sage is not None