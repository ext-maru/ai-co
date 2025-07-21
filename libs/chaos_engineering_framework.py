#!/usr/bin/env python3
"""
カオスエンジニアリングテストフレームワーク
Issue #191対応: Auto Issue Processor A2Aのレジリエンステスト
"""

import asyncio
import logging
import random
import time
import psutil
import threading
import os
import signal
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import tempfile
import shutil

logger = logging.getLogger(__name__)


class ChaosType(Enum):
    """カオスの種類"""
    NETWORK_DELAY = "network_delay"
    NETWORK_FAILURE = "network_failure"
    DISK_FULL = "disk_full"
    MEMORY_PRESSURE = "memory_pressure"
    CPU_SPIKE = "cpu_spike"
    PROCESS_KILL = "process_kill"
    RANDOM_EXCEPTION = "random_exception"
    API_RATE_LIMIT = "api_rate_limit"
    DEPENDENCY_FAILURE = "dependency_failure"
    FILE_CORRUPTION = "file_corruption"
    PERMISSION_DENIED = "permission_denied"
    TIMEOUT = "timeout"


class ChaosImpact(Enum):
    """カオスの影響度"""
    LOW = "low"       # システムは正常に回復すべき
    MEDIUM = "medium" # 一部機能低下は許容
    HIGH = "high"     # 大幅な機能低下、手動介入必要
    CRITICAL = "critical"  # システム停止レベル


@dataclass
class ChaosScenario:
    """カオスシナリオ定義"""
    name: str
    chaos_type: ChaosType
    impact: ChaosImpact
    duration: float  # 秒
    probability: float = 1.0  # 発生確率
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    expected_behavior: str = ""
    recovery_time_limit: float = 60.0  # 回復制限時間（秒）


@dataclass
class ChaosResult:
    """カオス実行結果"""
    scenario: ChaosScenario
    started_at: datetime
    ended_at: Optional[datetime] = None
    system_recovered: bool = False
    recovery_time: Optional[float] = None
    errors_caught: List[Exception] = field(default_factory=list)
    metrics_before: Dict[str, Any] = field(default_factory=dict)
    metrics_after: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        """実行時間を取得"""
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return 0.0
    
    @property
    def passed(self) -> bool:
        """テスト合格判定"""
        # 回復時間制限内に回復したか
        if self.recovery_time and self.recovery_time > self.scenario.recovery_time_limit:
            return False
        
        # 影響度に応じた判定
        if self.scenario.impact == ChaosImpact.LOW:
            return self.system_recovered
        elif self.scenario.impact == ChaosImpact.MEDIUM:
            return self.system_recovered or self.recovery_time < 300
        else:
            # HIGH/CRITICALは手動介入を想定
            return len(self.errors_caught) > 0  # エラーが適切に捕捉されたか


class ChaosMonkey:
    """カオスを注入するメインクラス"""
    
    def __init__(self):
        self.active_chaos: List[threading.Thread] = []
        self.logger = logging.getLogger(__name__)
        self._original_functions: Dict[str, Any] = {}
        self._chaos_active = False
        
    async def inject_chaos(self, scenario: ChaosScenario) -> ChaosResult:
        """カオスを注入"""
        result = ChaosResult(
            scenario=scenario,
            started_at=datetime.now()
        )
        
        # 発生確率チェック
        if random.random() > scenario.probability:
            self.logger.info(f"カオス '{scenario.name}' はスキップされました（確率: {scenario.probability}）")
            result.ended_at = datetime.now()
            result.system_recovered = True
            return result
        
        self.logger.warning(f"🔥 カオス注入開始: {scenario.name}")
        self.logger.warning(f"   タイプ: {scenario.chaos_type.value}")
        self.logger.warning(f"   影響度: {scenario.impact.value}")
        self.logger.warning(f"   期間: {scenario.duration}秒")
        
        # メトリクス取得（前）
        result.metrics_before = self._collect_system_metrics()
        
        try:
            self._chaos_active = True
            
            # カオスタイプに応じた注入
            if scenario.chaos_type == ChaosType.NETWORK_DELAY:
                await self._inject_network_delay(scenario, result)
            elif scenario.chaos_type == ChaosType.NETWORK_FAILURE:
                await self._inject_network_failure(scenario, result)
            elif scenario.chaos_type == ChaosType.DISK_FULL:
                await self._inject_disk_full(scenario, result)
            elif scenario.chaos_type == ChaosType.MEMORY_PRESSURE:
                await self._inject_memory_pressure(scenario, result)
            elif scenario.chaos_type == ChaosType.CPU_SPIKE:
                await self._inject_cpu_spike(scenario, result)
            elif scenario.chaos_type == ChaosType.PROCESS_KILL:
                await self._inject_process_kill(scenario, result)
            elif scenario.chaos_type == ChaosType.RANDOM_EXCEPTION:
                await self._inject_random_exception(scenario, result)
            elif scenario.chaos_type == ChaosType.API_RATE_LIMIT:
                await self._inject_api_rate_limit(scenario, result)
            elif scenario.chaos_type == ChaosType.DEPENDENCY_FAILURE:
                await self._inject_dependency_failure(scenario, result)
            elif scenario.chaos_type == ChaosType.FILE_CORRUPTION:
                await self._inject_file_corruption(scenario, result)
            elif scenario.chaos_type == ChaosType.PERMISSION_DENIED:
                await self._inject_permission_denied(scenario, result)
            elif scenario.chaos_type == ChaosType.TIMEOUT:
                await self._inject_timeout(scenario, result)
            else:
                raise ValueError(f"未対応のカオスタイプ: {scenario.chaos_type}")
                
        except Exception as e:
            self.logger.error(f"カオス注入中にエラー: {e}")
            result.errors_caught.append(e)
        finally:
            self._chaos_active = False
            result.ended_at = datetime.now()
            
            # メトリクス取得（後）
            result.metrics_after = self._collect_system_metrics()
            
            # 回復確認
            result.system_recovered = await self._check_system_recovery(scenario)
            if result.system_recovered:
                result.recovery_time = (datetime.now() - result.started_at).total_seconds()
            
            self.logger.info(f"🏁 カオス終了: {scenario.name}")
            self.logger.info(f"   実行時間: {result.duration:.1f}秒")
            self.logger.info(f"   システム回復: {result.system_recovered}")
            
        return result
    
    async def _inject_network_delay(self, scenario: ChaosScenario, result: ChaosResult):
        """ネットワーク遅延を注入"""
        delay_ms = scenario.parameters.get("delay_ms", 1000)
        jitter_ms = scenario.parameters.get("jitter_ms", 100)
        
        # モンキーパッチでネットワーク関数に遅延を追加
        import socket
        original_connect = socket.socket.connect
        
        def delayed_connect(self, address):
            delay = (delay_ms + random.randint(-jitter_ms, jitter_ms)) / 1000.0
            time.sleep(delay)
            return original_connect(self, address)
        
        socket.socket.connect = delayed_connect
        
        try:
            await asyncio.sleep(scenario.duration)
        finally:
            socket.socket.connect = original_connect
    
    async def _inject_network_failure(self, scenario: ChaosScenario, result: ChaosResult):
        """ネットワーク障害を注入"""
        failure_rate = scenario.parameters.get("failure_rate", 0.5)
        
        import socket
        original_connect = socket.socket.connect
        
        def failing_connect(self, address):
            if random.random() < failure_rate:
                raise ConnectionError("Chaos: Network connection failed")
            return original_connect(self, address)
        
        socket.socket.connect = failing_connect
        
        try:
            await asyncio.sleep(scenario.duration)
        finally:
            socket.socket.connect = original_connect
    
    async def _inject_disk_full(self, scenario: ChaosScenario, result: ChaosResult):
        """ディスクフルを注入"""
        # 一時ファイルで容量を消費
        temp_files = []
        target_size_mb = scenario.parameters.get("size_mb", 1000)
        chunk_size_mb = 100
        
        try:
            temp_dir = tempfile.mkdtemp(prefix="chaos_disk_")
            
            for i in range(0, target_size_mb, chunk_size_mb):
                temp_file = os.path.join(temp_dir, f"chaos_{i}.dat")
                with open(temp_file, "wb") as f:
                    f.write(os.urandom(chunk_size_mb * 1024 * 1024))
                temp_files.append(temp_file)
                
                # ディスク使用率をチェック
                disk_usage = psutil.disk_usage("/").percent
                if disk_usage > 95:
                    break
            
            await asyncio.sleep(scenario.duration)
            
        finally:
            # クリーンアップ
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except:
                    pass
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
    async def _inject_memory_pressure(self, scenario: ChaosScenario, result: ChaosResult):
        """メモリ圧迫を注入"""
        target_mb = scenario.parameters.get("size_mb", 500)
        memory_hog = []
        
        try:
            # メモリを確保
            chunk_size = 10 * 1024 * 1024  # 10MB
            for _ in range(target_mb // 10):
                memory_hog.append(bytearray(chunk_size))
                
                # メモリ使用率をチェック
                memory_usage = psutil.virtual_memory().percent
                if memory_usage > 90:
                    break
            
            await asyncio.sleep(scenario.duration)
            
        finally:
            # メモリ解放
            memory_hog.clear()
    
    async def _inject_cpu_spike(self, scenario: ChaosScenario, result: ChaosResult):
        """CPU高負荷を注入"""
        cpu_percent = scenario.parameters.get("cpu_percent", 80)
        
        def cpu_burn():
            """CPU負荷生成関数"""
            start_time = time.time()
            while time.time() - start_time < scenario.duration:
                # CPU使用率を目標値に調整
                current_cpu = psutil.cpu_percent(interval=0.1)
                if current_cpu < cpu_percent:
                    # 負荷計算
                    _ = sum(i * i for i in range(10000))
                else:
                    time.sleep(0.01)
        
        # 別スレッドでCPU負荷を生成
        thread = threading.Thread(target=cpu_burn)
        thread.start()
        
        await asyncio.sleep(scenario.duration)
        thread.join(timeout=1)
    
    async def _inject_process_kill(self, scenario: ChaosScenario, result: ChaosResult):
        """プロセスキルを注入"""
        process_name = scenario.parameters.get("process_name", "worker")
        signal_type = scenario.parameters.get("signal", signal.SIGTERM)
        
        # 対象プロセスを検索
        for proc in psutil.process_iter(['pid', 'name']):
            if process_name in proc.info['name']:
                try:
                    os.kill(proc.info['pid'], signal_type)
                    result.logs.append(f"Killed process {proc.info['name']} (PID: {proc.info['pid']})")
                except:
                    pass
        
        await asyncio.sleep(scenario.duration)
    
    async def _inject_random_exception(self, scenario: ChaosScenario, result: ChaosResult):
        """ランダムな例外を注入"""
        exception_types = [
            RuntimeError("Chaos: Random runtime error"),
            ValueError("Chaos: Random value error"),
            KeyError("chaos_key"),
            IndexError("Chaos: Index out of range"),
            TimeoutError("Chaos: Operation timed out")
        ]
        
        # グローバル例外ハンドラを一時的に置き換え
        import builtins
        original_import = builtins.__import__
        
        def chaos_import(name, *args, **kwargs):
            if random.random() < 0.1:  # 10%の確率で例外
                raise random.choice(exception_types)
            return original_import(name, *args, **kwargs)
        
        builtins.__import__ = chaos_import
        
        try:
            await asyncio.sleep(scenario.duration)
        finally:
            builtins.__import__ = original_import
    
    async def _inject_api_rate_limit(self, scenario: ChaosScenario, result: ChaosResult):
        """APIレート制限を注入"""
        # GitHub APIのレスポンスをモック
        import requests
        original_get = requests.get
        
        def rate_limited_get(url, *args, **kwargs):
            if "api.github.com" in url and random.random() < 0.8:
                response = requests.Response()
                response.status_code = 403
                response._content = b'{"message": "API rate limit exceeded"}'
                return response
            return original_get(url, *args, **kwargs)
        
        requests.get = rate_limited_get
        
        try:
            await asyncio.sleep(scenario.duration)
        finally:
            requests.get = original_get
    
    async def _inject_dependency_failure(self, scenario: ChaosScenario, result: ChaosResult):
        """依存関係の障害を注入"""
        module_name = scenario.parameters.get("module", "libs.rag_manager")
        
        # モジュールのインポートを一時的に失敗させる
        import sys
        if module_name in sys.modules:
            original_module = sys.modules[module_name]
            sys.modules[module_name] = None
            
            try:
                await asyncio.sleep(scenario.duration)
            finally:
                sys.modules[module_name] = original_module
    
    async def _inject_file_corruption(self, scenario: ChaosScenario, result: ChaosResult):
        """ファイル破損を注入"""
        target_pattern = scenario.parameters.get("pattern", "*.json")
        corruption_type = scenario.parameters.get("type", "truncate")
        
        # 一時的にファイルを破損（実際のファイルは触らず、読み込み時にエラーを注入）
        import builtins
        original_open = builtins.open
        
        def corrupted_open(file, *args, **kwargs):
            if target_pattern in str(file):
                if corruption_type == "truncate":
                    raise IOError("Chaos: File truncated")
                elif corruption_type == "permission":
                    raise PermissionError("Chaos: Permission denied")
            return original_open(file, *args, **kwargs)
        
        builtins.open = corrupted_open
        
        try:
            await asyncio.sleep(scenario.duration)
        finally:
            builtins.open = original_open
    
    async def _inject_permission_denied(self, scenario: ChaosScenario, result: ChaosResult):
        """権限エラーを注入"""
        import os
        original_access = os.access
        
        def denied_access(path, mode):
            if random.random() < 0.3:  # 30%の確率で権限拒否
                return False
            return original_access(path, mode)
        
        os.access = denied_access
        
        try:
            await asyncio.sleep(scenario.duration)
        finally:
            os.access = original_access
    
    async def _inject_timeout(self, scenario: ChaosScenario, result: ChaosResult):
        """タイムアウトを注入"""
        timeout_probability = scenario.parameters.get("probability", 0.5)
        
        # asyncio.sleepを遅延させる
        original_sleep = asyncio.sleep
        
        async def delayed_sleep(delay):
            if random.random() < timeout_probability:
                # タイムアウトをシミュレート（10倍遅延）
                await original_sleep(delay * 10)
            else:
                await original_sleep(delay)
        
        asyncio.sleep = delayed_sleep
        
        try:
            await asyncio.sleep(scenario.duration)
        finally:
            asyncio.sleep = original_sleep
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクスを収集"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage_percent": psutil.disk_usage("/").percent,
                "open_files": len(psutil.Process().open_files()),
                "num_threads": threading.active_count(),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            # フォールバック: psutilエラー時のデフォルト値
            self.logger.warning(f"システムメトリクス収集エラー: {e}")
            return {
                "cpu_percent": 50.0,
                "memory_percent": 60.0,
                "disk_usage_percent": 70.0,
                "open_files": 10,
                "num_threads": 5,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_system_recovery(self, scenario: ChaosScenario) -> bool:
        """システムが回復したかチェック"""
        # 基本的なヘルスチェック
        try:
            # CPU使用率が正常範囲か
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                return False
            
            # メモリ使用率が正常範囲か
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 90:
                return False
            
            # ディスク使用率が正常範囲か
            disk_percent = psutil.disk_usage("/").percent  
            if disk_percent > 95:
                return False
            
            # 基本的なネットワーク接続確認
            import socket
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=5)
            except:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"回復チェック中にエラー: {e}")
            return False


class ChaosTestRunner:
    """カオステストを実行するランナー"""
    
    def __init__(self, target_system: Any = None):
        self.target_system = target_system
        self.chaos_monkey = ChaosMonkey()
        self.results: List[ChaosResult] = []
        self.logger = logging.getLogger(__name__)
        
    async def run_scenario(self, scenario: ChaosScenario) -> ChaosResult:
        """単一のカオスシナリオを実行"""
        self.logger.info(f"🎯 カオスシナリオ実行: {scenario.name}")
        
        # ターゲットシステムがある場合は並行実行
        if self.target_system:
            # システムとカオスを並行実行
            system_task = asyncio.create_task(self._run_target_system())
            chaos_task = asyncio.create_task(self.chaos_monkey.inject_chaos(scenario))
            
            # カオス実行を待つ
            result = await chaos_task
            
            # システムタスクをキャンセル
            system_task.cancel()
            try:
                await system_task
            except asyncio.CancelledError:
                pass
        else:
            # カオスのみ実行
            result = await self.chaos_monkey.inject_chaos(scenario)
        
        self.results.append(result)
        return result
    
    async def run_scenarios(self, scenarios: List[ChaosScenario]) -> List[ChaosResult]:
        """複数のカオスシナリオを順次実行"""
        for scenario in scenarios:
            await self.run_scenario(scenario)
            
            # シナリオ間で回復時間を設ける
            self.logger.info("⏳ 次のシナリオまで10秒待機...")
            await asyncio.sleep(10)
        
        return self.results
    
    async def _run_target_system(self):
        """ターゲットシステムを実行（モック）"""
        while True:
            try:
                # ターゲットシステムの処理をシミュレート
                if hasattr(self.target_system, "process"):
                    await self.target_system.process()
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger.warning(f"ターゲットシステムエラー: {e}")
                await asyncio.sleep(5)
    
    def generate_report(self) -> str:
        """テスト結果レポートを生成"""
        if not self.results:
            return "カオステストは実行されていません"
        
        report = ["# カオスエンジニアリングテストレポート\n"]
        report.append(f"実行日時: {datetime.now().isoformat()}\n")
        report.append(f"総シナリオ数: {len(self.results)}\n")
        
        # サマリー
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        report.append(f"## サマリー")
        report.append(f"- 成功: {passed}")
        report.append(f"- 失敗: {failed}")
        report.append(f"- 成功率: {passed/len(self.results)*100:.1f}%\n")
        
        # 詳細結果
        report.append("## 詳細結果\n")
        for i, result in enumerate(self.results, 1):
            report.append(f"### {i}. {result.scenario.name}")
            report.append(f"- **タイプ**: {result.scenario.chaos_type.value}")
            report.append(f"- **影響度**: {result.scenario.impact.value}")
            report.append(f"- **結果**: {'✅ PASS' if result.passed else '❌ FAIL'}")
            report.append(f"- **実行時間**: {result.duration:.1f}秒")
            report.append(f"- **システム回復**: {result.system_recovered}")
            if result.recovery_time:
                report.append(f"- **回復時間**: {result.recovery_time:.1f}秒")
            if result.errors_caught:
                report.append(f"- **捕捉エラー**: {len(result.errors_caught)}件")
            report.append("")
        
        # メトリクス変化
        report.append("## システムメトリクス変化\n")
        for result in self.results:
            if result.metrics_before and result.metrics_after:
                report.append(f"### {result.scenario.name}")
                report.append(f"- CPU: {result.metrics_before['cpu_percent']:.1f}% → {result.metrics_after['cpu_percent']:.1f}%")
                report.append(f"- メモリ: {result.metrics_before['memory_percent']:.1f}% → {result.metrics_after['memory_percent']:.1f}%")
                report.append(f"- ディスク: {result.metrics_before['disk_usage_percent']:.1f}% → {result.metrics_after['disk_usage_percent']:.1f}%")
                report.append("")
        
        return "\n".join(report)


# プリセットシナリオ
PRESET_SCENARIOS = [
    ChaosScenario(
        name="軽微なネットワーク遅延",
        chaos_type=ChaosType.NETWORK_DELAY,
        impact=ChaosImpact.LOW,
        duration=30,
        parameters={"delay_ms": 500, "jitter_ms": 100},
        description="500msのネットワーク遅延を注入",
        expected_behavior="リトライにより正常処理継続"
    ),
    ChaosScenario(
        name="一時的なネットワーク障害",
        chaos_type=ChaosType.NETWORK_FAILURE,
        impact=ChaosImpact.MEDIUM,
        duration=60,
        parameters={"failure_rate": 0.5},
        description="50%の確率でネットワーク接続失敗",
        expected_behavior="エラーハンドリングとリトライで回復"
    ),
    ChaosScenario(
        name="ディスク容量逼迫",
        chaos_type=ChaosType.DISK_FULL,
        impact=ChaosImpact.HIGH,
        duration=120,
        parameters={"size_mb": 500},
        description="500MBの一時ファイルでディスクを圧迫",
        expected_behavior="ディスク容量エラーの適切な処理"
    ),
    ChaosScenario(
        name="メモリ不足",
        chaos_type=ChaosType.MEMORY_PRESSURE,
        impact=ChaosImpact.HIGH,
        duration=90,
        parameters={"size_mb": 300},
        description="300MBのメモリを消費",
        expected_behavior="メモリ不足エラーの適切な処理"
    ),
    ChaosScenario(
        name="CPU高負荷",
        chaos_type=ChaosType.CPU_SPIKE,
        impact=ChaosImpact.MEDIUM,
        duration=60,
        parameters={"cpu_percent": 80},
        description="CPU使用率を80%に上昇",
        expected_behavior="処理遅延はあるが継続動作"
    ),
    ChaosScenario(
        name="GitHub APIレート制限",
        chaos_type=ChaosType.API_RATE_LIMIT,
        impact=ChaosImpact.LOW,
        duration=300,
        parameters={},
        description="GitHub APIのレート制限をシミュレート",
        expected_behavior="適切な待機とリトライ"
    ),
    ChaosScenario(
        name="依存モジュール障害",
        chaos_type=ChaosType.DEPENDENCY_FAILURE,
        impact=ChaosImpact.MEDIUM,
        duration=120,
        parameters={"module": "libs.rag_manager"},
        description="RAGManagerモジュールの一時的な利用不可",
        expected_behavior="フォールバック処理で継続"
    ),
    ChaosScenario(
        name="ランダム例外発生",
        chaos_type=ChaosType.RANDOM_EXCEPTION,
        impact=ChaosImpact.LOW,
        duration=60,
        probability=0.7,
        parameters={},
        description="様々な例外をランダムに発生",
        expected_behavior="例外捕捉と適切なエラー処理"
    )
]


if __name__ == "__main__":
    # スタンドアロンテスト実行
    async def main():
        logging.basicConfig(level=logging.INFO)
        
        runner = ChaosTestRunner()
        
        # 基本的なシナリオを実行
        test_scenarios = [
            PRESET_SCENARIOS[0],  # ネットワーク遅延
            PRESET_SCENARIOS[5],  # APIレート制限
            PRESET_SCENARIOS[7],  # ランダム例外
        ]
        
        await runner.run_scenarios(test_scenarios)
        
        # レポート生成
        report = runner.generate_report()
        print("\n" + report)
        
        # レポートファイル保存
        report_path = f"chaos_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nレポート保存: {report_path}")
    
    asyncio.run(main())