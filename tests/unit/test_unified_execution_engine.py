#!/usr/bin/env python3
"""
⚡ 統合実行エンジン テスト

TDDアプローチによる包括的テストスイート
エルダー評議会令第400号 Phase 2 テスト実装
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

# 統合実行エンジンのインポート
sys_path_backup = None
try:
    import sys
    sys_path_backup = sys.path.copy()
    sys.path.insert(0, '/home/aicompany/ai_co/libs')
    
    from unified_execution_engine import (
        UnifiedExecutionEngine,
        TaskType,
        ExecutionStrategy,
        ExecutionStatus,
        UnifiedTask,
        get_unified_engine
    )
except ImportError as e:
    if sys_path_backup:
        sys.path = sys_path_backup
    
    # フォールバックテスト実装
    print(f"テストインポートエラー: {e}")
    
    class MockTaskType:
        DEVELOPMENT = "development"
        RESEARCH = "research"
        QUALITY_CHECK = "quality_check"
        INCIDENT_RESPONSE = "incident"
    
    class MockExecutionStrategy:
        ELDER_FLOW = "elder_flow"
        ELDER_TREE = "elder_tree"
        UNIFIED = "unified"
        PARALLEL = "parallel"
        ADAPTIVE = "adaptive"
    
    class MockExecutionStatus:
        QUEUED = "queued"
        EXECUTING = "executing"
        COMPLETED = "completed"
        FAILED = "failed"
        """MockTaskTypeクラス"""
    
    TaskType = MockTaskType()
    ExecutionStrategy = MockExecutionStrategy()
    ExecutionStatus = MockExecutionStatus()
    
        """MockExecutionStrategyクラス"""
    class MockUnifiedExecutionEngine:
        def __init__(self):
            self.engine_id = "test_engine"
            self.active_tasks = {}
            self.performance_metrics = {
                "total_tasks_executed": 0,
        """MockExecutionStatusクラス"""
                "average_execution_time": 0,
                "average_quality_score": 85.0
            }
        
        async def execute_unified_task(
            self,
            title,
            description,
            task_type=None,
        """MockUnifiedExecutionEngineクラス"""
            priority="medium",
            execution_strategy=None,
            context=None
        ):
            return "mock_task_001"
        
        def get_active_tasks(self):
            return []
        
            """execute_unified_taskを実行"""
        def get_performance_statistics(self):
            return {
                "engine_id": self.engine_id,
                "performance_metrics": self.performance_metrics,
                "total_active_tasks": 0
            }
    
    UnifiedExecutionEngine = MockUnifiedExecutionEngine
    
    def get_unified_engine():
        return MockUnifiedExecutionEngine()

class TestUnifiedExecutionEngine:
            """get_performance_statisticsの値を取得"""
    """
    統合実行エンジン ユニットテスト
    
    TDDアプローチで全機能を網羅した包括的テスト
    """
    
    @pytest.fixture
    def engine(self)return UnifiedExecutionEngine()
    """テスト用統合実行エンジンインスタンス"""
    
    @pytest.fixture
    def mock_unified_council(self)mock_council = Mock()
    """モック統合評議会"""
        mock_council.submit_matter = AsyncMock(return_value="matter_001")
        return mock_council
    
    def test_engine_initialization(self, engine):
        """
        テスト: エンジンの初期化が正しく行われること
        """
        # Act & Assert
        assert engine.engine_id.startswith("unified_execution_engine")
        assert hasattr(engine, 'active_tasks')
        assert hasattr(engine, 'performance_metrics')
        assert hasattr(engine, 'config')
        assert hasattr(engine, 'sages')
        assert hasattr(engine, 'servants')
        
        # 4賢者が正しく初期化されていること
        assert 'knowledge' in engine.sages
        assert 'task' in engine.sages
        assert 'incident' in engine.sages
        assert 'rag' in engine.sages
        
        # 4サーバントが正しく初期化されていること
        assert 'code_crafter' in engine.servants
        assert 'research_wizard' in engine.servants
        assert 'quality_guardian' in engine.servants
        assert 'crisis_responder' in engine.servants
    
    def test_config_default_values(self, engine):
        """
        テスト: デフォルト設定値が正しいこと
        """
        # Assert
        assert engine.config["enable_parallel_execution"] is True
        assert engine.config["auto_quality_optimization"] is True
        assert engine.config["adaptive_strategy_selection"] is True
        assert engine.config["max_concurrent_tasks"] == 5
        assert engine.config["quality_threshold"] == 85.0
        assert engine.config["optimization_interval"] == 3600
    
    def test_determine_execution_strategy_development(self, engine):
        """
        テスト: 開発タスクの戦略判定が正しいこと
        """
        # Arrange
        task_type = TaskType.DEVELOPMENT
        description = "new feature development"
        context = {}
        
        # Act
        strategy = engine._determine_execution_strategy(task_type, description, context)
        
        # Assert
        assert strategy == ExecutionStrategy.UNIFIED
    
    def test_determine_execution_strategy_incident(self, engine):
        """
        テスト: インシデントタスクの戦略判定が正しいこと
        """
        # Arrange
        task_type = TaskType.INCIDENT_RESPONSE
        description = "emergency bug fix"
        context = {}
        
        # Act
        strategy = engine._determine_execution_strategy(task_type, description, context)
        
        # Assert
        assert strategy == ExecutionStrategy.ELDER_TREE
    
    def test_determine_execution_strategy_quality(self, engine):
        """
        テスト: 品質チェックタスクの戦略判定が正しいこと
        """
        # Arrange
        task_type = TaskType.QUALITY_CHECK
        description = "code quality analysis"
        context = {}
        
        # Act
        strategy = engine._determine_execution_strategy(task_type, description, context)
        
        # Assert
        assert strategy == ExecutionStrategy.ELDER_FLOW
    
    def test_determine_execution_strategy_research(self, engine):
        """
        テスト: 研究タスクの戦略判定が正しいこと
        """
        # Arrange
        task_type = TaskType.RESEARCH
        description = "technical research"
        context = {}
        
        # Act
        strategy = engine._determine_execution_strategy(task_type, description, context)
        
        # Assert
        assert strategy == ExecutionStrategy.ELDER_TREE
    
    def test_determine_execution_strategy_complex(self, engine):
        """
        テスト: 複雑タスクの戦略判定が正しいこと
        """
        # Arrange
        task_type = TaskType.DEVELOPMENT
        # 50単語以上の複雑な説明
        description = " ".join(["complex"] + ["word"] * 60)
        context = {}
        
        # Act
        strategy = engine._determine_execution_strategy(task_type, description, context)
        
        # Assert
        assert strategy == ExecutionStrategy.PARALLEL
    
    def test_select_optimal_servant(self, engine):
        """
        テスト: タスクタイプに応じた最適サーバント選択が正しいこと
        """
        # Test cases
        test_cases = [
            (TaskType.DEVELOPMENT, "code_crafter"),
            (TaskType.RESEARCH, "research_wizard"),
            (TaskType.QUALITY_CHECK, "quality_guardian"),
            (TaskType.INCIDENT_RESPONSE, "crisis_responder"),
            (TaskType.OPTIMIZATION, "quality_guardian"),
            (TaskType.INTEGRATION, "code_crafter")
        ]
        
        for task_type, expected_servant in test_cases:
            # Act
            servant = engine._select_optimal_servant(task_type)
            
            # Assert
            assert servant == expected_servant, f"Task type {task_type} should select {expected_servant}, got {servant}"
    
    def test_analyze_task_complexity_simple(self, engine):
        """
        テスト: シンプルタスクの複雑度解析が正しいこと
        """
        # Arrange
        from dataclasses import dataclass
        
        @dataclass
        class MockTask:
            description: str
            priority: str
        
        task = MockTask(description="simple task", priority="low")
        
        # Act
        complexity = engine._analyze_task_complexity(task)
        
        # Assert
        assert 0.0 <= complexity <= 1.0
        assert complexity < 0.5  # シンプルなタスクは低複雑度
            """MockTaskクラス"""
    
    def test_analyze_task_complexity_complex(self, engine):
        """
        テスト: 複雑タスクの複雑度解析が正しいこと
        """
        # Arrange
        from dataclasses import dataclass
        
        @dataclass
        class MockTask:
            description: str
            priority: str
        
        # 長い説明と高優先度の複雑タスク
        long_description = "complex " + " ".join(["detailed"] * 100) + " task description"
        task = MockTask(description=long_description, priority="high")
        
        # Act
        complexity = engine._analyze_task_complexity(task)
        
            """MockTaskクラス"""
        # Assert
        assert 0.0 <= complexity <= 1.0
        assert complexity > 0.7  # 複雑なタスクは高複雑度
    
    @pytest.mark.asyncio
    async def test_execute_unified_task_basic(self, engine, mock_unified_council):
        """
        テスト: 基本的な統合タスク実行が正しく動作すること
        """
        # Arrange
        engine.unified_council = mock_unified_council
        title = "Test Task"
        description = "Test description"
        
        # モック設定
        with patch.object(engine, '_execute_task_with_strategy', new=AsyncMock()) as mock_execute:
            with patch.object(engine, '_perform_quality_check', new=AsyncMock()) as mock_quality:
                with patch.object(engine, '_update_performance_metrics', new=AsyncMock()) as mock_metrics:
                    # Act
                    task_id = await engine.execute_unified_task(title, description)
                    
                    # Assert
                    assert task_id.startswith("unified_task_")
                    assert task_id in engine.active_tasks
                    
                    task = engine.active_tasks[task_id]
                    assert task.title == title
                    assert task.description == description
                    assert task.task_type == TaskType.DEVELOPMENT  # デフォルト
                    assert task.priority == "medium"  # デフォルト
                    assert task.status == ExecutionStatus.COMPLETED
                    
                    # モックの呼び出し確認
                    mock_execute.assert_called_once()
                    mock_quality.assert_called_once()
                    mock_metrics.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_unified_task_with_parameters(self, engine, mock_unified_council):
        """
        テスト: パラメータ付き統合タスク実行が正しく動作すること
        """
        # Arrange
        engine.unified_council = mock_unified_council
        title = "Research Task"
        description = "Research technical solution"
        task_type = TaskType.RESEARCH
        priority = "high"
        execution_strategy = ExecutionStrategy.ELDER_TREE
        context = {"project": "test_project"}
        
        # モック設定
        with patch.object(engine, '_execute_task_with_strategy', new=AsyncMock()) as mock_execute:
            with patch.object(engine, '_perform_quality_check', new=AsyncMock()) as mock_quality:
                with patch.object(engine, '_update_performance_metrics', new=AsyncMock()) as mock_metrics:
                    # Act
                    task_id = await engine.execute_unified_task(
                        title, description, task_type, priority, execution_strategy, context
                    )
                    
                    # Assert
                    task = engine.active_tasks[task_id]
                    assert task.title == title
                    assert task.description == description
                    assert task.task_type == task_type
                    assert task.priority == priority
                    assert task.execution_strategy == execution_strategy
                    assert task.context == context
    
    @pytest.mark.asyncio
    async def test_execute_unified_task_error_handling(self, engine, mock_unified_council):
        """
        テスト: タスク実行エラー時の適切なハンドリング
        """
        # Arrange
        engine.unified_council = mock_unified_council
        title = "Error Task"
        description = "Task that will fail"
        
        # エラーを発生させるモック
        with patch.object(engine, '_execute_task_with_strategy', new=AsyncMock(side_effect=Exception("Test error"))):
            # Act
            task_id = await engine.execute_unified_task(title, description)
            
            # Assert
            task = engine.active_tasks[task_id]
            assert task.status == ExecutionStatus.FAILED
            assert task.execution_time is not None
            
            # エスカレーション確認
            mock_unified_council.submit_matter.assert_called_once()
            call_args = mock_unified_council.submit_matter.call_args
            assert "統合タスク実行失敗" in call_args[0][0]
            assert call_args[1]["priority"] == "high"
    
    @pytest.mark.asyncio
    async def test_execute_with_elder_flow(self, engine):
        """
        テスト: Elder Flow主導実行が正しく動作すること
        """
        # Arrange
        from dataclasses import dataclass
        from datetime import datetime
        
        @dataclass
        class MockTask:
            id: str
            title: str
            description: str
            execution_strategy: any
            status: any
            assigned_components: list
            context: dict
            results: list
            updated_at: datetime = None
            """MockTaskクラス"""
        
        task = MockTask(
            id="test_task",
            title="Test Elder Flow Task",
            description="Test description",
            execution_strategy=ExecutionStrategy.ELDER_FLOW,
            status=ExecutionStatus.PLANNING,
            assigned_components=[],
            context={},
            results=[]
        )
        
        # Elder Flowのモック設定
        mock_result = {"status": "success", "result": "Elder Flow completed"}
        engine.elder_flow.execute_task = AsyncMock(return_value=mock_result)
        
        # Act
        await engine._execute_with_elder_flow(task)
        
        # Assert
        assert task.status == ExecutionStatus.EXECUTING
        assert "ElderFlow" in task.assigned_components
        assert "QualityGate" in task.assigned_components
        assert len(task.results) == 1
        assert task.results[0]["component"] == "ElderFlow"
        assert task.results[0]["result"] == mock_result
        
        # Elder Flowの呼び出し確認
        engine.elder_flow.execute_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_with_elder_tree(self, engine):
        """
        テスト: Elder Tree v2主導実行が正しく動作すること
        """
        # Arrange
        from dataclasses import dataclass
        from datetime import datetime
        
        @dataclass
        class MockTask:
            id: str
            title: str
            description: str
            task_type: any
            execution_strategy: any
            status: any
            assigned_components: list
            context: dict
            """MockTaskクラス"""
            results: list
            updated_at: datetime = None
        
        task = MockTask(
            id="test_task",
            title="Test Elder Tree Task",
            description="Test description",
            task_type=TaskType.RESEARCH,
            execution_strategy=ExecutionStrategy.ELDER_TREE,
            status=ExecutionStatus.PLANNING,
            assigned_components=[],
            context={},
            results=[]
        )
        
        # 4賤者のモック設定
        for sage in engine.sages.values():
            sage.process = AsyncMock(return_value="Sage consultation completed")
        
        # サーバントのモック設定
        mock_servant_result = "Servant execution completed"
        engine.servants["research_wizard"].execute = AsyncMock(return_value=mock_servant_result)
        
        # Act
        await engine._execute_with_elder_tree(task)
        
        # Assert
        assert task.status == ExecutionStatus.EXECUTING
        assert "ElderTree" in task.assigned_components
        assert "FourSages" in task.assigned_components
        assert "FourServants" in task.assigned_components
        assert len(task.results) == 1
        assert task.results[0]["component"] == "ElderTree"
        
        # 4賤者の相談確認
        sage_consultations = task.results[0]["sage_consultations"]
        assert len(sage_consultations) == 4
        
        # サーバント実行確認
        servant_execution = task.results[0]["servant_execution"]
        assert servant_execution["servant"] == "research_wizard"
        assert servant_execution["result"] == mock_servant_result
    
    @pytest.mark.asyncio
    async def test_execute_with_unified_approach(self, engine):
        """
        テスト: 統合アプローチ実行が正しく動作すること
        """
        # Arrange
        from dataclasses import dataclass
        from datetime import datetime
        
        @dataclass
        class MockTask:
            id: str
            title: str
            description: str
            execution_strategy: any
            status: any
            assigned_components: list
            context: dict
            """MockTaskクラス"""
            results: list
            updated_at: datetime = None
        
        task = MockTask(
            id="test_task",
            title="Test Unified Task",
            description="Test description",
            execution_strategy=ExecutionStrategy.UNIFIED,
            status=ExecutionStatus.PLANNING,
            assigned_components=[],
            context={},
            results=[]
        )
        
        # Elder FlowとElder Treeのモック設定
        elder_flow_result = {"status": "success", "result": "Elder Flow part"}
        elder_tree_result = {"status": "completed", "result": "Elder Tree part"}
        
        engine.elder_flow.execute_task = AsyncMock(return_value=elder_flow_result)
        engine.elder_tree_flow.run_workflow = AsyncMock(return_value=elder_tree_result)
        
        # Act
        await engine._execute_with_unified_approach(task)
        
        # Assert
        assert task.status == ExecutionStatus.EXECUTING
        assert "ElderFlow" in task.assigned_components
        assert "ElderTree" in task.assigned_components
        assert "UnifiedOrchestration" in task.assigned_components
        assert len(task.results) == 1
        
        result = task.results[0]
        assert result["component"] == "UnifiedApproach"
        assert result["elder_flow_result"] == elder_flow_result
        assert result["elder_tree_result"] == elder_tree_result
        assert "unified_effectiveness" in result
    
    @pytest.mark.asyncio
    async def test_execute_with_parallel_approach(self, engine):
        """
        テスト: 並列アプローチ実行が正しく動作すること
        """
        # Arrange
        from dataclasses import dataclass
        from datetime import datetime
        
        @dataclass
        class MockTask:
            id: str
            title: str
            description: str
            execution_strategy: any
            status: any
            assigned_components: list
            """MockTaskクラス"""
            context: dict
            results: list
            updated_at: datetime = None
        
        task = MockTask(
            id="test_task",
            title="Test Parallel Task",
            description="Test description",
            execution_strategy=ExecutionStrategy.PARALLEL,
            status=ExecutionStatus.PLANNING,
            assigned_components=[],
            context={},
            results=[]
        )
        
        # 並列実行のモック設定
        elder_flow_result = {"status": "success", "source": "elder_flow"}
        elder_tree_result = {"status": "completed", "source": "elder_tree"}
        
        engine.elder_flow.execute_task = AsyncMock(return_value=elder_flow_result)
        engine.elder_tree_flow.run_workflow = AsyncMock(return_value=elder_tree_result)
        
        # Act
        await engine._execute_with_parallel_approach(task)
        
        # Assert
        assert task.status == ExecutionStatus.EXECUTING
        assert "ParallelExecution" in task.assigned_components
        assert "ElderFlow" in task.assigned_components
        assert "ElderTree" in task.assigned_components
        assert len(task.results) == 1
        
        result = task.results[0]
        assert result["component"] == "ParallelExecution"
        assert result["elder_flow_result"] == elder_flow_result
        assert result["elder_tree_result"] == elder_tree_result
        assert "optimal_result" in result
    
    @pytest.mark.asyncio
    async def test_execute_with_adaptive_approach(self, engine):
        """
        テスト: 適応的アプローチ実行が正しく動作すること
        """
        # Arrange
        from dataclasses import dataclass
        from datetime import datetime
        
        @dataclass
        class MockTask:
            id: str
            title: str
            description: str
            execution_strategy: any
            status: any
            """MockTaskクラス"""
            assigned_components: list
            context: dict
            results: list
            updated_at: datetime = None
        
        task = MockTask(
            id="test_task",
            title="Test Adaptive Task",
            description="simple task",  # シンプルなタスク
            execution_strategy=ExecutionStrategy.ADAPTIVE,
            status=ExecutionStatus.PLANNING,
            assigned_components=[],
            context={},
            results=[]
        )
        
        # 適応的実行のモック
        with patch.object(engine, '_execute_task_with_strategy', new=AsyncMock()) as mock_execute:
            # Act
            await engine._execute_with_adaptive_approach(task)
            
            # Assert
            assert task.status == ExecutionStatus.EXECUTING
            assert "AdaptiveExecution" in task.assigned_components
            assert len(task.results) == 1
            
            result = task.results[0]
            assert result["component"] == "AdaptiveExecution"
            assert "original_strategy" in result
            assert "adaptive_strategy" in result
            assert "adaptation_reason" in result
            
            # 適応的戦略での再実行確認
            mock_execute.assert_called_once_with(task)
    
    @pytest.mark.asyncio
    async def test_perform_quality_check_pass(self, engine):
        """
        テスト: 品質チェックが成功すること
        """
        # Arrange
        from dataclasses import dataclass
        from datetime import datetime
        
        @dataclass
        class MockTask:
            id: str
            title: str
            status: any
            quality_score: float = None
            """MockTaskクラス"""
            results: list = None
            context: dict = None
        
        task = MockTask(
            id="test_task",
            title="Test Task",
            status=ExecutionStatus.EXECUTING,
            results=[],
            context={}
        )
        
        # 品質チェック成功のモック
        quality_result = {"score": 90, "passed": True}
        engine.quality_gate.check_quality = AsyncMock(return_value=quality_result)
        
        # Act
        await engine._perform_quality_check(task)
        
        # Assert
        assert task.quality_score == 90
        assert task.status == ExecutionStatus.QUALITY_CHECK  # 最終ステータス
    
    @pytest.mark.asyncio
    async def test_perform_quality_check_fail_and_optimize(self, engine):
        """
        テスト: 品質チェック失敗時の最適化処理
        """
        # Arrange
        from dataclasses import dataclass
        from datetime import datetime
        
        @dataclass
        class MockTask:
            id: str
            title: str
            status: any
            """MockTaskクラス"""
            quality_score: float = None
            results: list = None
            context: dict = None
        
        task = MockTask(
            id="test_task",
            title="Test Task",
            status=ExecutionStatus.EXECUTING,
            results=[],
            context={}
        )
        
        # 品質チェック失敗のモック (闾値未満)
        quality_result = {"score": 70, "passed": False}  # 85未満
        engine.quality_gate.check_quality = AsyncMock(return_value=quality_result)
        
        # 最適化処理のモック
        with patch.object(engine, '_optimize_task_quality', new=AsyncMock()) as mock_optimize:
            # Act
            await engine._perform_quality_check(task)
            
            # Assert
            assert task.quality_score == 70
            mock_optimize.assert_called_once_with(task)
    
    @pytest.mark.asyncio
    async def test_optimize_task_quality(self, engine):
        """
        テスト: タスク品質最適化が正しく動作すること
        """
        # Arrange
        from dataclasses import dataclass
        from datetime import datetime
        
        @dataclass
        class MockTask:
            id: str
            title: str
            """MockTaskクラス"""
            quality_score: float
            results: list
        
        task = MockTask(
            id="test_task",
            title="Test Task",
            quality_score=70,
            results=[]
        )
        
        # Quality Guardianサーバントのモック
        optimization_result = "Quality optimization completed"
        engine.servants["quality_guardian"].execute = AsyncMock(return_value=optimization_result)
        
        # Act
        await engine._optimize_task_quality(task)
        
        # Assert
        assert task.quality_score == 80  # 70 + 10 (最大改善幅)
        assert len(task.results) == 1
        assert task.results[0]["component"] == "QualityOptimization"
        assert task.results[0]["optimization_result"] == optimization_result
        assert task.results[0]["improved_score"] == 80
    
    @pytest.mark.asyncio
    async def test_update_performance_metrics(self, engine):
        """
        テスト: パフォーマンスメトリクス更新が正しく動作すること
        """
        # Arrange
        from dataclasses import dataclass
        
        @dataclass
        class MockTask:
            execution_time: float
            """MockTaskクラス"""
            quality_score: float
        
        # 初期状態
        initial_metrics = engine.performance_metrics.copy()
        
        task = MockTask(execution_time=60.0, quality_score=85.0)
        
        # Act
        await engine._update_performance_metrics(task)
        
        # Assert
        assert engine.performance_metrics["total_tasks_executed"] == initial_metrics["total_tasks_executed"] + 1
        assert engine.performance_metrics["average_execution_time"] > 0
        assert engine.performance_metrics["average_quality_score"] > 0
        assert 0 <= engine.performance_metrics["efficiency_improvement"] <= 100
    
    def test_get_active_tasks(self, engine):
        """
        テスト: アクティブタスク一覧取得が正しく動作すること
        """
        # Arrange - テスト用タスクを直接追加
        from dataclasses import dataclass
        from datetime import datetime
        
        @dataclass
        class MockUnifiedTask:
            """MockUnifiedTaskクラス"""
            id: str
            title: str
            task_type: any
            execution_strategy: any
            status: any
            priority: str
            quality_score: float
            execution_time: float
            assigned_components: list
            created_at: datetime
            updated_at: datetime
        
        test_task = MockUnifiedTask(
            id="test_task_001",
            title="Test Task",
            task_type=TaskType.DEVELOPMENT,
            execution_strategy=ExecutionStrategy.UNIFIED,
            status=ExecutionStatus.EXECUTING,
            priority="high",
            quality_score=85.0,
            execution_time=120.0,
            assigned_components=["ElderFlow", "ElderTree"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        engine.active_tasks["test_task_001"] = test_task
        
        # Act
        active_tasks = engine.get_active_tasks()
        
        # Assert
        assert len(active_tasks) == 1
        task_info = active_tasks[0]
        assert task_info["id"] == "test_task_001"
        assert task_info["title"] == "Test Task"
        assert task_info["task_type"] == TaskType.DEVELOPMENT
        assert task_info["execution_strategy"] == ExecutionStrategy.UNIFIED
        assert task_info["status"] == ExecutionStatus.EXECUTING
        assert task_info["priority"] == "high"
        assert task_info["quality_score"] == 85.0
        assert task_info["execution_time"] == 120.0
        assert task_info["assigned_components"] == ["ElderFlow", "ElderTree"]
        assert "created_at" in task_info
        assert "updated_at" in task_info
    
    def test_get_performance_statistics(self, engine):
        """
        テスト: パフォーマンス統計情報取得が正しく動作すること
        """
        # Act
        stats = engine.get_performance_statistics()
        
        # Assert
        assert "engine_id" in stats
        assert stats["engine_id"] == engine.engine_id
        assert "uptime" in stats
        assert stats["uptime"] >= 0
        assert "total_active_tasks" in stats
        assert stats["total_active_tasks"] == len(engine.active_tasks)
        assert "performance_metrics" in stats
        assert "system_status" in stats
        assert "last_updated" in stats
        
        # システムステータス確認
        system_status = stats["system_status"]
        assert system_status["elder_flow_integrated"] is True
        assert system_status["elder_tree_integrated"] is True
        assert system_status["quality_gates_active"] == engine.config["auto_quality_optimization"]
        assert system_status["parallel_execution_enabled"] == engine.config["enable_parallel_execution"]
    
    def test_singleton_get_unified_engine(self):
        """
        テスト: シングルトンインスタンスの取得が正しく動作すること
        """
        # Act
        engine1 = get_unified_engine()
        engine2 = get_unified_engine()
        
        # Assert
        assert engine1 is engine2  # 同一インスタンス
        assert isinstance(engine1, UnifiedExecutionEngine)
    
    def test_calculate_unified_effectiveness(self, engine):
        """
        テスト: 統合効果性算出が正しく動作すること
        """
        # Arrange
        elder_flow_result = {"status": "success"}
        elder_tree_result = {"status": "completed"}
        
        # Act
        effectiveness = engine._calculate_unified_effectiveness(elder_flow_result, elder_tree_result)
        
        # Assert
        assert 0.0 <= effectiveness <= 1.0
        assert effectiveness == 0.85  # 現在の実装では固定値
    
    def test_select_optimal_result(self, engine):
        """
        テスト: 最適結果選択が正しく動作すること
        """
        # Arrange
        elder_flow_result = {"source": "elder_flow", "quality": 80}
        elder_tree_result = {"source": "elder_tree", "quality": 90}
        
        # Act
        optimal_result = engine._select_optimal_result(elder_flow_result, elder_tree_result)
        
        # Assert
        # 現在の実装ではElder Tree結果を優先
        assert optimal_result == elder_tree_result


class TestUnifiedExecutionEngineIntegration:
    """
    統合実行エンジン 統合テスト
    
    統合評議会システムとの連携や終端間ワークフローをテスト
    """
    
    @pytest.mark.asyncio
    async def test_full_task_execution_workflow(self):
        """
        テスト: 全タスク実行ワークフローの統合テスト
        """
        # Arrange
        engine = UnifiedExecutionEngine()
        
        # モックの設定
        with patch.object(engine, 'unified_council') as mock_council:
            with patch.object(engine.elder_flow, 'execute_task', new=AsyncMock(return_value={"status": "success"})):
                with patch.object(engine.quality_gate, 'check_quality', new=AsyncMock(return_value={"score": 90})):
                    # Act
                    task_id = await engine.execute_unified_task(
                        "Integration Test Task",
                        "Full workflow integration test",
                        TaskType.DEVELOPMENT,
                        "high"
                    )
                    
                    # Assert
                    assert task_id in engine.active_tasks
                    task = engine.active_tasks[task_id]
                    assert task.status == ExecutionStatus.COMPLETED
                    assert task.quality_score == 90
                    assert task.execution_time is not None
                    assert len(task.results) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_task_execution(self):
        """
        テスト: 並行タスク実行の統合テスト
        """
        # Arrange
        engine = UnifiedExecutionEngine()
        
        with patch.object(engine, 'unified_council'):
            with patch.object(engine.elder_flow, 'execute_task', new=AsyncMock(return_value={"status": "success"})):
                with patch.object(engine.quality_gate, 'check_quality', new=AsyncMock(return_value={"score": 85})):
                    # Act - 複数タスクを並行実行
                    tasks = await asyncio.gather(
                        engine.execute_unified_task("Task 1", "First concurrent task"),
                        engine.execute_unified_task("Task 2", "Second concurrent task"),
                        engine.execute_unified_task("Task 3", "Third concurrent task")
                    )
                    
                    # Assert
                    assert len(tasks) == 3
                    assert len(engine.active_tasks) == 3
                    
                    for task_id in tasks:
                        task = engine.active_tasks[task_id]
                        assert task.status == ExecutionStatus.COMPLETED
    
    def test_performance_metrics_accuracy(self):
        """
        テスト: パフォーマンスメトリクスの精度確認
        """
        # Arrange
        engine = UnifiedExecutionEngine()
        initial_stats = engine.get_performance_statistics()
        
        # Act & Assert - 初期状態
        assert initial_stats["total_active_tasks"] == 0
        assert initial_stats["performance_metrics"]["total_tasks_executed"] == 0
        assert initial_stats["performance_metrics"]["average_execution_time"] == 0
        assert initial_stats["performance_metrics"]["average_quality_score"] == 0
        
        # システムステータス確認
        system_status = initial_stats["system_status"]
        assert all(system_status.values())  # すべてTrueであること

# テスト実行関数
def test_unified_execution_engine_module_load():
    """
    テスト: 統合実行エンジンモジュールの読み込み確認
    """
    # モジュールが正常に読み込まれることを確認
    assert UnifiedExecutionEngine is not None
    assert TaskType is not None
    assert ExecutionStrategy is not None
    assert ExecutionStatus is not None
    assert get_unified_engine is not None

if __name__ == "__main__":
    # テスト実行
    pytest.main(["-v", __file__])