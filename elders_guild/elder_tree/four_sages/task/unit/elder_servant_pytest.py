#!/usr/bin/env python3
"""
Elder Servant基盤クラス用ユニットテスト (pytest版)
Issue #93: OSS移行プロジェクト - unittest → pytest

EldersLegacy統合とIron Will品質基準の完全テスト実装
Issue #69対応: EldersServiceLegacy継承とTDD品質保証
"""

import pytest
from datetime import datetime

from libs.core.elders_legacy import (
    EldersLegacyDomain,
    EldersServiceLegacy,
)
from libs.elder_servants.base.elder_servant import (
    ElderServant,
    ServantCapability,
    ServantCategory,
    ServantRegistry,
    ServantRequest,
    ServantResponse,
    TaskPriority,
    TaskResult,
    TaskStatus,
)


class TestElderServant(ElderServant):
    """テスト用ElderServant実装"""

    def __init__(self):
        capabilities = [
            ServantCapability(
                "test_capability", "テスト用機能", ["test_input"], ["test_output"], 1
            )
        ]
        super().__init__(
            servant_id="test_servant_001",
            servant_name="TestServant",
            category=ServantCategory.DWARF,
            specialization="test_specialization",
            capabilities=capabilities,
        )

    def get_specialized_capabilities(self) -> List[ServantCapability]:
        """専門特化能力の取得"""
        return [
            ServantCapability(
                "test_specialized", "テスト専門能力", ["test_data"], ["test_result"], 2
            )
        ]

    async def execute_task(self, task: dict) -> TaskResult:
        """テスト用タスク実行"""
        task_id = task.get("task_id", "test_task")

        # 成功パターンのモック実装
        if task.get("task_type") == "success_test":
            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.COMPLETED,
                result_data={"message": "success", "processed": True},
                quality_score=98.5,
                execution_time_ms=100.0,
            )

        # 失敗パターンのモック実装
        if task.get("task_type") == "failure_test":
            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.FAILED,
                result_data={},
                error_message="テスト用エラー",
                quality_score=0.0,
                execution_time_ms=50.0,
            )

        # 警告パターンのモック実装
        if task.get("task_type") == "warning_test":
            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.COMPLETED,
                result_data={"message": "success with warning"},
                quality_score=92.0,  # Iron Will閾値未満
                execution_time_ms=200.0,
            )

        # デフォルト成功パターン
        return TaskResult(
            task_id=task_id,
            servant_id=self.servant_id,
            status=TaskStatus.COMPLETED,
            result_data={"message": "default success"},
            quality_score=96.0,
            execution_time_ms=100.0,
        )


@pytest.fixture
def test_servant():
    """テスト用ElderServantインスタンス"""
    return TestElderServant()


@pytest.fixture 
def sample_task():
    """サンプルタスクデータ"""
    return {
        "task_id": "test_task_001",
        "task_type": "success_test",
        "description": "テスト用タスク",
        "priority": TaskPriority.MEDIUM,
        "metadata": {"test": True}
    }


class TestElderServantInitialization:
    """ElderServant初期化テスト"""

    def test_elder_servant_initialization(self, test_servant):
        """ElderServant初期化テスト"""
        # 基本プロパティ確認
        assert test_servant.servant_id == "test_servant_001"
        assert test_servant.servant_name == "TestServant"
        assert test_servant.category == ServantCategory.DWARF
        assert test_servant.specialization == "test_specialization"

        # EldersServiceLegacy継承確認
        assert isinstance(test_servant, EldersServiceLegacy)
        assert test_servant.domain == EldersLegacyDomain.EXECUTION

        # 統計初期化確認
        assert test_servant.stats["tasks_executed"] == 0
        assert test_servant.stats["tasks_succeeded"] == 0
        assert test_servant.stats["tasks_failed"] == 0

        # Iron Will品質閾値確認
        assert test_servant.quality_threshold == 95.0

    def test_servant_capabilities(self, test_servant):
        """サーバント能力テスト"""
        # EldersLegacy能力取得メソッド確認  
        legacy_capabilities = test_servant.get_capabilities()
        assert isinstance(legacy_capabilities, list)
        assert len(legacy_capabilities) > 0
        
        # 基本プロパティ確認
        assert hasattr(test_servant, 'capabilities')
        assert isinstance(test_servant.capabilities, list)


class TestElderServantAsync:
    """ElderServant非同期機能テスト"""

    @pytest.mark.asyncio
    async def test_execute_task_direct(self, test_servant, sample_task):
        """タスク直接実行テスト"""
        result = await test_servant.execute_task(sample_task)

        assert isinstance(result, TaskResult)
        assert result.task_id == sample_task["task_id"]
        assert result.status == TaskStatus.COMPLETED
        assert result.quality_score > 0


class TestElderServantBasic:
    """ElderServant基本機能テスト"""

    @pytest.mark.asyncio
    async def test_multiple_task_execution(self, test_servant):
        """複数タスク実行テスト"""
        tasks = [
            {"task_id": "multi_1", "task_type": "success_test"},
            {"task_id": "multi_2", "task_type": "failure_test"}, 
            {"task_id": "multi_3", "task_type": "warning_test"}
        ]
        
        results = []
        for task in tasks:
            result = await test_servant.execute_task(task)
            results.append(result)
            
        assert len(results) == 3
        assert results[0].status == TaskStatus.COMPLETED
        assert results[1].status == TaskStatus.FAILED
        assert results[2].status == TaskStatus.COMPLETED


@pytest.mark.parametrize("task_type,expected_status", [
    ("success_test", TaskStatus.COMPLETED),
    ("failure_test", TaskStatus.FAILED),
    ("warning_test", TaskStatus.COMPLETED),
])
@pytest.mark.asyncio
async def test_task_execution_patterns(test_servant, task_type, expected_status):
    """タスク実行パターンテスト"""
    task = {
        "task_id": f"pattern_test_{task_type}",
        "task_type": task_type,
        "description": f"パターンテスト: {task_type}"
    }

    result = await test_servant.execute_task(task)
    assert result.status == expected_status


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])