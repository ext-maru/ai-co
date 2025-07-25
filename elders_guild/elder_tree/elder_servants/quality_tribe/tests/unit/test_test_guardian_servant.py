"""
🛡️ TestGuardianServant テストスイート - TDD実装

テスト生成・実行専門のエルダーサーバントのテスト
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from elders_guild.elder_tree.elder_servants.base.unified_elder_servant import (
    TestGuardianServant, ServantTask, ServantStatus
)


class TestTestGuardianServant:
    """🛡️ TestGuardianServant テストクラス"""
    
    @pytest.fixture
    def test_guardian(self):
        """TestGuardianServantインスタンス"""
        return TestGuardianServant()
    
    @pytest.fixture
    def temp_dir(self):
        """テスト用一時ディレクトリ"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_test_guardian_initialization(self, test_guardian):
        """初期化テスト"""
        assert test_guardian.servant_id == "test_guardian_001"
        assert test_guardian.name == "TestGuardian"
        assert test_guardian.specialization == "test_creation"
        assert test_guardian.status == ServantStatus.IDLE
        assert len(test_guardian.capabilities) == 1
        assert test_guardian.capabilities[0].name == "test_creation"
    
    @pytest.mark.asyncio
    async def test_generate_unit_test(self, test_guardian):
        """ユニットテスト生成テスト"""
        task = ServantTask(
            id="task_001",
            name="generate_unit_test",
            description="add_numbers関数のユニットテストを生成",
            priority="high"
        )
        
        result = await test_guardian.execute_task(task)
        
        assert result["status"] == "completed"
        assert "test_code" in result
        assert "def test_" in result["test_code"]
        assert "assert" in result["test_code"]
        assert result["test_framework"] == "pytest"
        assert result["test_count"] > 0
    
    @pytest.mark.asyncio
    async def test_generate_integration_test(self, test_guardian):
        """統合テスト生成テスト"""
        task = ServantTask(
            id="task_002",
            name="generate_integration_test",
            description="API エンドポイントの統合テストを生成"
        )
        
        result = await test_guardian.execute_task(task)
        
        assert result["status"] == "completed"
        assert "test_code" in result
        assert "async def test_" in result["test_code"]
        assert "client" in result["test_code"]
        assert result["test_type"] == "integration"
    
    @pytest.mark.asyncio
    async def test_run_tests(self, test_guardian, temp_dir):
        """テスト実行テスト"""
        # テストファイル作成
        test_file = temp_dir / "test_sample.py"
        test_file.write_text("""
import pytest

def test_simple():
    assert 1 + 1 == 2

def test_failure():
    assert 1 + 1 == 3
""")
        
        task = ServantTask(
            id="task_003",
            name="run_tests",
            description=f"テストファイルを実行: {test_file}"
        )
        
        result = await test_guardian.execute_task(task)
        
        assert result["status"] == "completed"
        assert result["tests_run"] == 2
        assert result["tests_passed"] == 1
        assert result["tests_failed"] == 1
        assert len(result["failures"]) == 1
    
    @pytest.mark.asyncio
    async def test_calculate_coverage(self, test_guardian):
        """カバレッジ測定テスト"""
        task = ServantTask(
            id="task_004",
            name="calculate_coverage",
            description="コードカバレッジを測定"
        )
        
        result = await test_guardian.execute_task(task)
        
        assert result["status"] == "completed"
        assert "coverage_percentage" in result
        assert 0 <= result["coverage_percentage"] <= 100
        assert "coverage_report" in result
        assert "uncovered_lines" in result
    
    @pytest.mark.asyncio
    async def test_generate_mock_test(self, test_guardian):
        """モックテスト生成テスト"""
        task = ServantTask(
            id="task_005",
            name="generate_mock_test",
            description="外部API呼び出しのモックテストを生成"
        )
        
        result = await test_guardian.execute_task(task)
        
        assert result["status"] == "completed"
        assert "mock" in result["test_code"].lower()
        assert "@patch" in result["test_code"]
        assert result["mock_targets"] > 0
    
    @pytest.mark.asyncio
    async def test_generate_parametrized_test(self, test_guardian):
        """パラメータ化テスト生成テスト"""
        task = ServantTask(
            id="task_006",
            name="generate_parametrized_test",
            description="複数の入力値でのパラメータ化テスト生成"
        )
        
        result = await test_guardian.execute_task(task)
        
        assert result["status"] == "completed"
        assert "@pytest.mark.parametrize" in result["test_code"]
        assert result["parameter_sets"] > 1
    
    @pytest.mark.asyncio
    async def test_generate_property_based_test(self, test_guardian):
        """プロパティベーステスト生成テスト"""
        task = ServantTask(
            id="task_007",
            name="generate_property_test",
            description="hypothesis を使用したプロパティベーステスト生成"
        )
        
        result = await test_guardian.execute_task(task)
        
        assert result["status"] == "completed"
        assert "hypothesis" in result["test_code"]
        assert "@given" in result["test_code"]
        assert result["properties_tested"] > 0
    
    @pytest.mark.asyncio
    async def test_performance_test_generation(self, test_guardian):
        """パフォーマンステスト生成テスト"""
        task = ServantTask(
            id="task_008",
            name="generate_performance_test",
            description="パフォーマンステストを生成"
        )
        
        result = await test_guardian.execute_task(task)
        
        assert result["status"] == "completed"
        assert "time" in result["test_code"]
        assert "performance" in result["test_code"].lower()
        assert result["performance_metrics"] > 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, test_guardian):
        """エラーハンドリングテスト"""
        task = ServantTask(
            id="task_009",
            name="invalid_test_task",
            description="存在しないテストタスクタイプ"
        )
        
        result = await test_guardian.execute_task(task)
        
        assert result["status"] == "error"
        assert "error_message" in result
        assert "unknown task type" in result["error_message"].lower()
    
    @pytest.mark.asyncio
    async def test_test_report_generation(self, test_guardian):
        """テストレポート生成テスト"""
        task = ServantTask(
            id="task_010",
            name="generate_test_report",
            description="包括的なテストレポートを生成"
        )
        
        result = await test_guardian.execute_task(task)
        
        assert result["status"] == "completed"
        assert "report" in result
        assert "summary" in result["report"]
        assert "coverage" in result["report"]
        assert "recommendations" in result["report"]
    
    @pytest.mark.asyncio
    async def test_test_suite_validation(self, test_guardian):
        """テストスイート検証テスト"""
        task = ServantTask(
            id="task_011",
            name="validate_test_suite",
            description="テストスイートの品質を検証"
        )
        
        result = await test_guardian.execute_task(task)
        
        assert result["status"] == "completed"
        assert "validation_score" in result
        assert 0 <= result["validation_score"] <= 100
        assert "issues_found" in result
        assert "suggestions" in result


class TestTestGuardianIntegration:
    """🛡️ TestGuardian統合テスト"""
    
    @pytest.mark.asyncio
    async def test_full_testing_workflow(self):
        """完全テストワークフロー: 生成→実行→カバレッジ→レポート"""
        guardian = TestGuardianServant()
        
        # 1.0 テスト生成
        gen_task = ServantTask("gen", "generate_unit_test", "関数テスト生成")
        gen_result = await guardian.execute_task(gen_task)
        assert gen_result["status"] == "completed"
        
        # 2.0 テスト実行
        run_task = ServantTask("run", "run_tests", "テスト実行")
        run_result = await guardian.execute_task(run_task)
        assert run_result["status"] == "completed"
        
        # 3.0 カバレッジ測定
        cov_task = ServantTask("coverage", "calculate_coverage", "カバレッジ測定")
        cov_result = await guardian.execute_task(cov_task)
        assert cov_result["status"] == "completed"
        
        # 4.0 レポート生成
        report_task = ServantTask("report", "generate_test_report", "レポート生成")
        report_result = await guardian.execute_task(report_task)
        assert report_result["status"] == "completed"
        
        # 全体確認
        assert len(guardian.completed_tasks) == 4