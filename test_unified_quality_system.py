#!/usr/bin/env python3
"""
統合品質パイプラインシステム 完全動作テスト
Issue #309: 自動化品質パイプライン実装

目的: Phase 1-4 の全実装を統合して実際に動作確認
"""

import asyncio
import tempfile
import shutil
from pathlib import Path
import time

# Import all implemented components
from libs.quality.static_analysis_engine import StaticAnalysisEngine
from libs.quality.test_automation_engine import TestAutomationEngine  
from libs.quality.comprehensive_quality_engine import ComprehensiveQualityEngine
from libs.quality.unified_quality_pipeline import UnifiedQualityPipeline
from libs.quality.pipeline_performance_optimizer import PipelinePerformanceOptimizer
from libs.quality.quality_metrics_monitor import QualityMetricsMonitor

# Import servants
from libs.elder_servants.quality_watcher_judgment import QualityWatcherJudgment
from libs.elder_servants.test_forge_judgment import TestForgeJudgment


async def create_test_project():
    """テスト用プロジェクト作成"""
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir)
    
    # メインモジュール
    main_file = project_path / "calculator.py"
    main_file.write_text('''"""
Calculator module for testing unified quality pipeline.
"""

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

def divide(a: int, b: int) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Division by zero!")
    return a / b

class Calculator:
    """Calculator class with memory."""
    
    def __init__(self):
        self.memory = 0
    
    def add_to_memory(self, value: float) -> None:
        """Add value to memory."""
        self.memory += value
    
    def clear_memory(self) -> None:
        """Clear memory."""
        self.memory = 0
    
    def get_memory(self) -> float:
        """Get memory value."""
        return self.memory
''')
    
    # テストファイル
    test_file = project_path / "test_calculator.py"
    test_file.write_text('''"""
Tests for calculator module.
"""

import pytest
from calculator import add, subtract, multiply, divide, Calculator


def test_add():
    """Test addition."""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0


def test_subtract():
    """Test subtraction."""
    assert subtract(5, 3) == 2
    assert subtract(0, 5) == -5
    assert subtract(-5, -3) == -2


def test_multiply():
    """Test multiplication."""
    assert multiply(3, 4) == 12
    assert multiply(-2, 3) == -6
    assert multiply(0, 100) == 0


def test_divide():
    """Test division."""
    assert divide(10, 2) == 5.0
    assert divide(7, 2) == 3.5
    
    with pytest.raises(ValueError):
        divide(5, 0)


class TestCalculator:
    """Test Calculator class."""
    
    def test_memory_operations(self):
        """Test memory operations."""
        calc = Calculator()
        assert calc.get_memory() == 0
        
        calc.add_to_memory(10)
        assert calc.get_memory() == 10
        
        calc.add_to_memory(-5)
        assert calc.get_memory() == 5
        
        calc.clear_memory()
        assert calc.get_memory() == 0
''')
    
    # 設定ファイル
    setup_cfg = project_path / "setup.cfg"
    setup_cfg.write_text('''[metadata]
name = test-project
version = 1.0.0

[mypy]
python_version = 3.12
warn_return_any = True
warn_unused_configs = True

[tool:pytest]
testpaths = .
python_files = test_*.py
''')
    
    # pyproject.toml
    pyproject = project_path / "pyproject.toml"
    pyproject.write_text('''[tool.black]
line-length = 88
target-version = ['py312']

[tool.isort]
profile = "black"
line_length = 88
''')
    
    return str(project_path)


async def run_unified_quality_pipeline_test():
    """統合品質パイプライン完全テスト実行"""
    print("🚀 統合品質パイプラインシステム 動作テスト開始")
    print("=" * 80)
    
    # テストプロジェクト作成
    test_project_path = await create_test_project()
    print(f"📁 テストプロジェクト作成: {test_project_path}")
    
    try:
        # Phase 1: 品質メトリクス監視システム初期化
        print("\n📊 Phase 1: 品質メトリクス監視システム初期化")
        monitor = QualityMetricsMonitor(monitoring_interval=5.0)
        monitor.start_monitoring()
        print("✅ 監視システム起動完了")
        
        # Phase 2: 統合品質パイプライン初期化
        print("\n🏗️ Phase 2: 統合品質パイプライン初期化")
        pipeline = UnifiedQualityPipeline()
        print("✅ パイプライン初期化完了")
        
        # Phase 3: パイプライン実行（監視付き）
        print("\n⚡ Phase 3: 品質パイプライン実行")
        start_time = time.time()
        
        result = await pipeline.execute_complete_quality_pipeline(test_project_path)
        
        execution_time = time.time() - start_time
        print(f"✅ パイプライン実行完了: {execution_time:.2f}秒")
        
        # 実行結果をモニターに記録
        monitor.record_pipeline_execution(result, execution_time, "TEST-001")
        
        # Phase 4: 結果分析
        print("\n📈 Phase 4: 実行結果分析")
        print(f"- 統合品質スコア: {result.unified_quality_score:.1f}/100")
        print(f"- Elder承認状態: {result.overall_status}")
        print(f"- パイプライン効率: {result.pipeline_efficiency:.1f}%")
        
        if result.graduation_certificate:
            print(f"🎓 品質卒業証明書発行: {result.graduation_certificate}")
        
        # Phase 5: パフォーマンス最適化
        print("\n⚡ Phase 5: パフォーマンス最適化実行")
        optimizer = PipelinePerformanceOptimizer()
        
        optimization_result = await optimizer.optimize_unified_pipeline_performance(
            pipeline, test_project_path, "comprehensive"
        )
        
        print(f"✅ 最適化完了: {optimization_result.improvement_percentage:.1f}%改善")
        
        # 最適化結果をモニターに記録
        if optimization_result.success:
            monitor.record_pipeline_execution(
                result, 
                optimization_result.optimized_metrics.execution_time,
                "TEST-002-OPTIMIZED"
            )
        
        # Phase 6: 監視レポート生成
        print("\n📋 Phase 6: 監視レポート生成")
        monitoring_report = monitor.generate_monitoring_report(period_hours=1)
        
        print(f"- 総実行回数: {monitoring_report.total_executions}")
        print(f"- 成功実行数: {monitoring_report.successful_executions}")
        print(f"- 平均品質スコア: {monitoring_report.average_quality_score:.1f}")
        print(f"- Elder承認率: {monitoring_report.elder_approval_rate:.1f}%")
        print(f"- 効率トレンド: {monitoring_report.pipeline_efficiency_trend}")
        
        # アクティブアラート確認
        if monitoring_report.active_alerts:
            print(f"⚠️ アクティブアラート: {len(monitoring_report.active_alerts)}件")
            for alert in monitoring_report.active_alerts:
                print(f"  - {alert.alert_level.value}: {alert.message}")
        
        # 監視統計
        stats = monitor.get_monitoring_statistics()
        print(f"\n📊 監視統計:")
        print(f"- 記録メトリクス数: {stats['total_metrics_recorded']}")
        print(f"- アクティブアラート: {stats['active_alerts_count']}")
        print(f"- 解決済みアラート: {stats['resolved_alerts_count']}")
        
        # 最終結果
        print("\n" + "=" * 80)
        print("🏆 統合品質パイプラインシステム テスト完了")
        print(f"最終品質スコア: {result.unified_quality_score:.1f}/100")
        print(f"Elder承認状態: {result.overall_status}")
        print(f"実行時間: {execution_time:.2f}秒 → {optimization_result.optimized_metrics.execution_time:.2f}秒")
        print(f"性能改善: {optimization_result.improvement_percentage:.1f}%")
        
        # 監視停止
        monitor.stop_monitoring()
        
        return True
        
    except Exception as e:
        print(f"\n❌ エラー発生: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # クリーンアップ
        shutil.rmtree(test_project_path, ignore_errors=True)
        print("\n🧹 テストプロジェクトクリーンアップ完了")


if __name__ == "__main__":
    # 統合テスト実行
    success = asyncio.run(run_unified_quality_pipeline_test())
    
    if success:
        print("\n✅ すべてのテストが成功しました！")
        print("自動化品質パイプラインは正常に動作しています。")
    else:
        print("\n❌ テストに失敗しました。")
        print("エラーログを確認してください。")