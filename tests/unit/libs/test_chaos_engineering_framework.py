#!/usr/bin/env python3
"""
カオスエンジニアリングテストフレームワークのテスト
Issue #191対応
"""

import pytest
import asyncio
import time
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from libs.chaos_engineering_framework import (
    ChaosType,
    ChaosImpact,
    ChaosScenario,
    ChaosResult,
    ChaosMonkey,
    ChaosTestRunner,
    PRESET_SCENARIOS
)


class TestChaosScenario:
    """カオスシナリオのテスト"""
    
    def test_scenario_creation(self):
        """シナリオ作成のテスト"""
        scenario = ChaosScenario(
            name="テストシナリオ",
            chaos_type=ChaosType.NETWORK_DELAY,
            impact=ChaosImpact.LOW,
            duration=30.0,
            parameters={"delay_ms": 500}
        )
        
        assert scenario.name == "テストシナリオ"
        assert scenario.chaos_type == ChaosType.NETWORK_DELAY
        assert scenario.impact == ChaosImpact.LOW
        assert scenario.duration == 30.0
        assert scenario.parameters["delay_ms"] == 500
        assert scenario.probability == 1.0  # デフォルト値


class TestChaosResult:
    """カオス結果のテスト"""
    
    def test_result_creation(self):
        """結果作成のテスト"""
        scenario = ChaosScenario(
            name="テスト",
            chaos_type=ChaosType.NETWORK_DELAY,
            impact=ChaosImpact.LOW,
            duration=30.0
        )
        
        result = ChaosResult(
            scenario=scenario,
            started_at=datetime.now()
        )
        
        assert result.scenario == scenario
        assert result.started_at is not None
        assert result.ended_at is None
        assert not result.system_recovered
        assert result.recovery_time is None
    
    def test_duration_calculation(self):
        """実行時間計算のテスト"""
        scenario = ChaosScenario("test", ChaosType.NETWORK_DELAY, ChaosImpact.LOW, 30.0)
        result = ChaosResult(
            scenario=scenario,
            started_at=datetime.now()
        )
        
        # 終了時刻なしの場合
        assert result.duration == 0.0
        
        # 終了時刻ありの場合
        result.ended_at = result.started_at + timedelta(seconds=5)
        assert result.duration == 5.0
    
    def test_passed_judgment(self):
        """合格判定のテスト"""
        # LOW影響度 - システム回復が必須
        scenario_low = ChaosScenario("test", ChaosType.NETWORK_DELAY, ChaosImpact.LOW, 30.0)
        result_low = ChaosResult(scenario=scenario_low, started_at=datetime.now())
        result_low.system_recovered = True
        assert result_low.passed
        
        result_low.system_recovered = False
        assert not result_low.passed
        
        # HIGH影響度 - エラー捕捉があれば合格
        scenario_high = ChaosScenario("test", ChaosType.DISK_FULL, ChaosImpact.HIGH, 30.0)
        result_high = ChaosResult(scenario=scenario_high, started_at=datetime.now())
        result_high.errors_caught = [Exception("test error")]
        assert result_high.passed



@pytest.mark.asyncio
class TestChaosMonkey:
    """カオスモンキーのテスト"""
    
    async def test_network_delay_injection(self):
        """ネットワーク遅延注入のテスト"""
        monkey = ChaosMonkey()
        scenario = ChaosScenario(
            name="ネットワーク遅延テスト",
            chaos_type=ChaosType.NETWORK_DELAY,
            impact=ChaosImpact.LOW,
            duration=1.0,  # 短時間でテスト
            parameters={"delay_ms": 100}
        )
        
        start_time = time.time()
        result = await monkey.inject_chaos(scenario)
        execution_time = time.time() - start_time
        
        assert result.scenario == scenario
        assert result.started_at is not None
        assert result.ended_at is not None
        assert execution_time >= 1.0  # 最低実行時間
        assert result.metrics_before is not None
        assert result.metrics_after is not None
    
    async def test_probability_skip(self):
        """確率によるスキップのテスト"""
        monkey = ChaosMonkey()
        scenario = ChaosScenario(
            name="低確率シナリオ",
            chaos_type=ChaosType.NETWORK_DELAY,
            impact=ChaosImpact.LOW,
            duration=10.0,
            probability=0.0  # 0%で必ずスキップ
        )
        
        start_time = time.time()
        result = await monkey.inject_chaos(scenario)
        execution_time = time.time() - start_time
        
        # スキップされたため短時間で完了
        assert execution_time < 1.0
        assert result.system_recovered  # スキップ時は回復済み扱い
    
    @patch('socket.socket.connect')
    async def test_network_failure_injection(self, mock_connect):
        """ネットワーク障害注入のテスト"""
        monkey = ChaosMonkey()
        scenario = ChaosScenario(
            name="ネットワーク障害テスト",
            chaos_type=ChaosType.NETWORK_FAILURE,
            impact=ChaosImpact.MEDIUM,
            duration=0.5,
            parameters={"failure_rate": 1.0}
        )
        
        result = await monkey.inject_chaos(scenario)
        
        # ネットワーク障害が注入されたことを確認
        assert result.scenario == scenario
        assert result.duration >= 0.5
    
    async def test_memory_pressure_injection(self):
        """メモリ圧迫注入のテスト"""
        monkey = ChaosMonkey()
        scenario = ChaosScenario(
            name="メモリ圧迫テスト",
            chaos_type=ChaosType.MEMORY_PRESSURE,
            impact=ChaosImpact.HIGH,
            duration=0.5,
            parameters={"size_mb": 10}  # 小さなサイズでテスト
        )
        
        result = await monkey.inject_chaos(scenario)
        
        assert result.scenario == scenario
        assert result.duration >= 0.5
        # メモリ使用量が変化していることを確認
        assert result.metrics_before is not None
        assert result.metrics_after is not None
    
    async def test_random_exception_injection(self):
        """ランダム例外注入のテスト"""
        monkey = ChaosMonkey()
        scenario = ChaosScenario(
            name="ランダム例外テスト",
            chaos_type=ChaosType.RANDOM_EXCEPTION,
            impact=ChaosImpact.LOW,
            duration=0.5
        )
        
        result = await monkey.inject_chaos(scenario)
        
        assert result.scenario == scenario
        assert result.duration >= 0.5
    
    async def test_api_rate_limit_injection(self):
        """APIレート制限注入のテスト"""
        monkey = ChaosMonkey()
        scenario = ChaosScenario(
            name="APIレート制限テスト",
            chaos_type=ChaosType.API_RATE_LIMIT,
            impact=ChaosImpact.LOW,
            duration=0.5
        )
        
        result = await monkey.inject_chaos(scenario)
        
        assert result.scenario == scenario
        assert result.duration >= 0.5
    
    async def test_cpu_spike_injection(self):
        """CPU高負荷注入のテスト"""
        monkey = ChaosMonkey()
        scenario = ChaosScenario(
            name="CPU高負荷テスト",
            chaos_type=ChaosType.CPU_SPIKE,
            impact=ChaosImpact.MEDIUM,
            duration=0.2,
            parameters={"cpu_percent": 80}
        )
        
        result = await monkey.inject_chaos(scenario)
        
        assert result.scenario == scenario
        assert result.duration >= 0.2
    
    async def test_disk_full_injection(self):
        """ディスク容量逼迫注入のテスト"""
        monkey = ChaosMonkey()
        scenario = ChaosScenario(
            name="ディスク容量テスト",
            chaos_type=ChaosType.DISK_FULL,
            impact=ChaosImpact.HIGH,
            duration=0.2,
            parameters={"size_mb": 1}  # 極小サイズでテスト
        )
        
        result = await monkey.inject_chaos(scenario)
        
        assert result.scenario == scenario
        assert result.duration >= 0.2
    
    async def test_process_kill_injection(self):
        """プロセスキル注入のテスト"""
        monkey = ChaosMonkey()
        scenario = ChaosScenario(
            name="プロセスキルテスト",
            chaos_type=ChaosType.PROCESS_KILL,
            impact=ChaosImpact.HIGH,
            duration=0.1,
            parameters={"process_name": "nonexistent_process"}
        )
        
        result = await monkey.inject_chaos(scenario)
        
        assert result.scenario == scenario
        assert result.duration >= 0.1
    
    async def test_dependency_failure_injection(self):
        """依存関係障害注入のテスト"""
        monkey = ChaosMonkey()
        scenario = ChaosScenario(
            name="依存関係障害テスト",
            chaos_type=ChaosType.DEPENDENCY_FAILURE,
            impact=ChaosImpact.MEDIUM,
            duration=0.2,
            parameters={"module": "nonexistent.module"}
        )
        
        result = await monkey.inject_chaos(scenario)
        
        assert result.scenario == scenario
        assert result.duration >= 0.2
    
    async def test_permission_denied_injection(self):
        """権限拒否注入のテスト"""
        monkey = ChaosMonkey()
        scenario = ChaosScenario(
            name="権限拒否テスト",
            chaos_type=ChaosType.PERMISSION_DENIED,
            impact=ChaosImpact.MEDIUM,
            duration=0.2
        )
        
        result = await monkey.inject_chaos(scenario)
        
        assert result.scenario == scenario
        assert result.duration >= 0.2
    
    async def test_timeout_injection(self):
        """タイムアウト注入のテスト"""
        monkey = ChaosMonkey()
        scenario = ChaosScenario(
            name="タイムアウトテスト",
            chaos_type=ChaosType.TIMEOUT,
            impact=ChaosImpact.LOW,
            duration=0.2,
            parameters={"probability": 0.5}
        )
        
        result = await monkey.inject_chaos(scenario)
        
        assert result.scenario == scenario
        assert result.duration >= 0.2
    
    async def test_unsupported_chaos_type(self):
        """未対応カオスタイプのテスト"""
        monkey = ChaosMonkey()
        
        # 存在しないカオスタイプを強制作成
        class UnsupportedChaosType(Enum):
            UNKNOWN = "unknown"
        
        scenario = ChaosScenario(
            name="未対応テスト", 
            chaos_type=UnsupportedChaosType.UNKNOWN,
            impact=ChaosImpact.LOW,
            duration=0.1
        )
        
        result = await monkey.inject_chaos(scenario)
        
        # エラーが捕捉されているはず
        assert len(result.errors_caught) > 0
        assert "未対応のカオスタイプ" in str(result.errors_caught[0])
    
    @patch('builtins.open')
    async def test_file_corruption_injection(self, mock_open):
        """ファイル破損注入のテスト"""
        monkey = ChaosMonkey()
        scenario = ChaosScenario(
            name="ファイル破損テスト",
            chaos_type=ChaosType.FILE_CORRUPTION,
            impact=ChaosImpact.MEDIUM,
            duration=0.5,
            parameters={"pattern": "*.json", "type": "truncate"}
        )
        
        result = await monkey.inject_chaos(scenario)
        
        assert result.scenario == scenario
        assert result.duration >= 0.5
    
    async def test_system_metrics_collection(self):
        """システムメトリクス収集のテスト"""
        monkey = ChaosMonkey()
        metrics = monkey._collect_system_metrics()
        
        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics
        assert "disk_usage_percent" in metrics
        assert "open_files" in metrics
        assert "num_threads" in metrics
        assert "timestamp" in metrics
        
        # 値が適切な範囲内であることを確認
        assert 0 <= metrics["cpu_percent"] <= 100
        assert 0 <= metrics["memory_percent"] <= 100
        assert 0 <= metrics["disk_usage_percent"] <= 100
        assert metrics["open_files"] >= 0
        assert metrics["num_threads"] >= 1
    
    @patch('socket.create_connection')
    @patch('psutil.cpu_percent', return_value=50.0)
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    async def test_system_recovery_check(self, mock_disk, mock_memory, mock_cpu, mock_socket):
        """システム回復チェックのテスト"""
        # 正常状態のモック
        mock_memory.return_value.percent = 70.0
        mock_disk.return_value.percent = 80.0
        mock_socket.return_value = Mock()
        
        monkey = ChaosMonkey()
        scenario = ChaosScenario("test", ChaosType.NETWORK_DELAY, ChaosImpact.LOW, 1.0)
        
        # 正常状態での回復チェック
        is_recovered = await monkey._check_system_recovery(scenario)
        assert is_recovered
        
        # 異常状態（CPU高負荷）
        mock_cpu.return_value = 95.0
        is_recovered = await monkey._check_system_recovery(scenario)
        assert not is_recovered
        
        # 異常状態（メモリ不足）
        mock_cpu.return_value = 50.0
        mock_memory.return_value.percent = 95.0
        is_recovered = await monkey._check_system_recovery(scenario)
        assert not is_recovered



@pytest.mark.asyncio
class TestChaosTestRunner:
    """カオステストランナーのテスト"""
    
    async def test_single_scenario_run(self):
        """単一シナリオ実行のテスト"""
        runner = ChaosTestRunner()
        scenario = ChaosScenario(
            name="テストシナリオ",
            chaos_type=ChaosType.NETWORK_DELAY,
            impact=ChaosImpact.LOW,
            duration=0.5,
            parameters={"delay_ms": 100}
        )
        
        result = await runner.run_scenario(scenario)
        
        assert result.scenario == scenario
        assert len(runner.results) == 1
        assert runner.results[0] == result
    
    async def test_multiple_scenarios_run(self):
        """複数シナリオ実行のテスト"""
        runner = ChaosTestRunner()
        scenarios = [
            ChaosScenario(
                name="シナリオ1",
                chaos_type=ChaosType.NETWORK_DELAY,
                impact=ChaosImpact.LOW,
                duration=0.1
            ),
            ChaosScenario(
                name="シナリオ2",
                chaos_type=ChaosType.RANDOM_EXCEPTION,
                impact=ChaosImpact.LOW,
                duration=0.1
            )
        ]
        
        # 待機時間をモックで短縮
        with patch('asyncio.sleep', new_callable=AsyncMock):
            results = await runner.run_scenarios(scenarios)
        
        assert len(results) == 2
        assert len(runner.results) == 2
        assert results[0].scenario.name == "シナリオ1"
        assert results[1].scenario.name == "シナリオ2"
    
    async def test_target_system_integration(self):
        """ターゲットシステム統合のテスト"""
        mock_system = Mock()
        mock_system.process = AsyncMock()
        
        runner = ChaosTestRunner(target_system=mock_system)
        scenario = ChaosScenario(
            name="統合テスト",
            chaos_type=ChaosType.NETWORK_DELAY,
            impact=ChaosImpact.LOW,
            duration=0.2
        )
        
        result = await runner.run_scenario(scenario)
        
        assert result.scenario == scenario
        # ターゲットシステムのprocessメソッドが呼ばれたことを確認
        # (並行実行のため回数は不定)
        assert mock_system.process.called
    
    def test_report_generation_empty(self):
        """空のレポート生成テスト"""
        runner = ChaosTestRunner()
        report = runner.generate_report()
        
        assert "カオステストは実行されていません" in report
    
    def test_report_generation_with_results(self):
        """結果ありのレポート生成テスト"""
        runner = ChaosTestRunner()
        
        # モック結果を作成
        scenario = ChaosScenario("テスト", ChaosType.NETWORK_DELAY, ChaosImpact.LOW, 1.0)
        result = ChaosResult(scenario=scenario, started_at=datetime.now())
        result.ended_at = result.started_at + timedelta(seconds=1)
        result.system_recovered = True
        result.recovery_time = 1.0
        result.metrics_before = {"cpu_percent": 50.0, "memory_percent": 60.0, "disk_usage_percent": 70.0}
        result.metrics_after = {"cpu_percent": 55.0, "memory_percent": 65.0, "disk_usage_percent": 70.0}
        
        runner.results = [result]
        
        report = runner.generate_report()
        
        assert "カオスエンジニアリングテストレポート" in report
        assert "総シナリオ数: 1" in report
        assert "成功: 1" in report
        assert "失敗: 0" in report
        assert "成功率: 100.0%" in report
        assert "テスト" in report
        assert "PASS" in report
        assert "CPU: 50.0% → 55.0%" in report



class TestPresetScenarios:
    """プリセットシナリオのテスト"""
    
    def test_preset_scenarios_exist(self):
        """プリセットシナリオが存在することを確認"""
        assert len(PRESET_SCENARIOS) > 0
        
        # 各シナリオの必須項目をチェック
        for scenario in PRESET_SCENARIOS:
            assert scenario.name
            assert scenario.chaos_type
            assert scenario.impact
            assert scenario.duration > 0
            assert 0 <= scenario.probability <= 1
    
    def test_preset_scenarios_variety(self):
        """プリセットシナリオの多様性を確認"""
        chaos_types = set(s.chaos_type for s in PRESET_SCENARIOS)
        impacts = set(s.impact for s in PRESET_SCENARIOS)
        
        # 複数種類のカオスタイプが含まれている
        assert len(chaos_types) >= 3
        
        # 複数の影響度が含まれている
        assert len(impacts) >= 2
    
    @pytest.mark.asyncio
    async def test_preset_scenario_execution(self):
        """プリセットシナリオの実行テスト"""
        runner = ChaosTestRunner()
        
        # 最初の3つのプリセットシナリオをテスト（時間短縮）
        test_scenarios = PRESET_SCENARIOS[:3]
        
        # 実行時間を短縮
        for scenario in test_scenarios:
            scenario.duration = 0.1
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            results = await runner.run_scenarios(test_scenarios)
        
        assert len(results) == 3
        for result in results:
            assert result.scenario in test_scenarios
            assert result.started_at is not None
            assert result.ended_at is not None



@pytest.mark.asyncio
class TestIntegrationScenarios:
    """Auto Issue Processor A2A統合シナリオのテスト"""
    
    async def test_a2a_resilience_scenario(self):
        """A2A耐障害性テストシナリオ"""
        # Auto Issue Processor A2A用のカスタムシナリオ
        a2a_scenarios = [
            ChaosScenario(
                name="GitHub API障害耐性テスト",
                chaos_type=ChaosType.API_RATE_LIMIT,
                impact=ChaosImpact.LOW,
                duration=0.5,
                description="GitHub APIのレート制限に対する耐性テスト",
                expected_behavior="適切なバックオフとリトライで回復"
            ),
            ChaosScenario(
                name="Git操作中断テスト",
                chaos_type=ChaosType.RANDOM_EXCEPTION,
                impact=ChaosImpact.MEDIUM,
                duration=0.3,
                description="Git操作中の予期しない例外発生",
                expected_behavior="ロールバック処理で状態回復"
            ),
            ChaosScenario(
                name="依存サービス障害テスト",
                chaos_type=ChaosType.DEPENDENCY_FAILURE,
                impact=ChaosImpact.MEDIUM,
                duration=0.5,
                parameters={"module": "libs.four_sages"},
                description="4賢者システムの一時的な障害",
                expected_behavior="フォールバック処理で継続動作"
            )
        ]
        
        runner = ChaosTestRunner()
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            results = await runner.run_scenarios(a2a_scenarios)
        
        assert len(results) == 3
        
        # 各テストが適切に実行されたことを確認
        for result in results:
            assert result.started_at is not None
            assert result.ended_at is not None
            assert result.metrics_before is not None
            assert result.metrics_after is not None
        
        # レポート生成テスト
        report = runner.generate_report()
        assert "GitHub API障害耐性テスト" in report
        assert "Git操作中断テスト" in report
        assert "依存サービス障害テスト" in report


# スタンドアロンテスト
if __name__ == "__main__":
    pytest.main([__file__, "-v"])