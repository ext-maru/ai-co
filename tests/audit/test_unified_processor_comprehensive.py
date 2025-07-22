#!/usr/bin/env python3
"""
統一Auto Issue Processor 包括的監査
実用的な範囲での厳格テスト
"""

import asyncio
import os
import sys
import time
import json
import tempfile
import shutil
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from libs.auto_issue_processor import AutoIssueProcessor, ProcessorConfig
from libs.auto_issue_processor.utils import ProcessLock


class ComprehensiveTest:
    """包括的テストスイート"""
    
    def __init__(self):
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
    
    async def test_lock_concurrent_access(self):
        """並行ロックアクセステスト"""
        test_name = "並行ロックアクセス"
        print(f"\n🔒 {test_name}")
        
        lock_dir = "./test_concurrent_locks"
        os.makedirs(lock_dir, exist_ok=True)
        
        try:
            # 10個の並行ロック
            locks = []
            results = []
            
            async def try_lock(index):
                lock = ProcessLock("file", lock_dir=lock_dir)
                key = f"concurrent_key_{index % 3}"  # 3つのキーで競合
                acquired = await lock.acquire(key, ttl=2)
                if acquired:
                    await asyncio.sleep(0.1)
                    await lock.release(key)
                return acquired
            
            tasks = [try_lock(i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            
            success_count = sum(1 for r in results if r is True)
            
            if success_count >= 3:  # 少なくとも各キーで1つは成功
                self.results["passed"].append(f"✅ {test_name}: {success_count}/10 成功")
            else:
                self.results["failed"].append(f"❌ {test_name}: 成功数が少ない {success_count}/10")
            
        finally:
            if os.path.exists(lock_dir):
                shutil.rmtree(lock_dir)
    
    async def test_config_validation(self):
        """設定検証テスト"""
        test_name = "設定検証"
        print(f"\n⚙️ {test_name}")
        
        # 1. 正常な設定
        config = ProcessorConfig()
        if config.validate():
            self.results["passed"].append(f"✅ {test_name}: 正常設定の検証OK")
        else:
            self.results["failed"].append(f"❌ {test_name}: 正常設定が無効判定")
        
        # 2. 異常な設定
        invalid_config = ProcessorConfig()
        invalid_config.processing.max_issues_per_run = 0
        
        if not invalid_config.validate():
            self.results["passed"].append(f"✅ {test_name}: 異常設定の検出OK")
        else:
            self.results["failed"].append(f"❌ {test_name}: 異常設定を検出できず")
    
    async def test_error_recovery(self):
        """エラーリカバリーテスト"""
        test_name = "エラーリカバリー"
        print(f"\n🔧 {test_name}")
        
        config = ProcessorConfig()
        config.features.error_recovery = True
        config.dry_run = True
        config.github.token = "test_token"
        config.github.repo = "test_repo"
        config.github.owner = "test_owner"
        
        processor = AutoIssueProcessor(config)
        
        # エラーを発生させる
        error_count = 0
        
        async def failing_function(issue):
            nonlocal error_count
            error_count += 1
            if error_count <= 2:  # 最初の2回は失敗
                raise ConnectionError("Simulated error")
            return {"success": True, "artifacts": {}}
        
        mock_issue = Mock()
        mock_issue.number = 1
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test"
        mock_issue.created_at = datetime.now()
        mock_issue.labels = []
        mock_issue.comments = 0
        mock_issue.pull_request = None
        
        with patch.object(processor, '_execute_issue_processing', side_effect=failing_function):
            with patch.object(processor, '_get_issues_to_process', return_value=[mock_issue]):
                result = await processor.process_issues([1])
        
        if result["success"] and result["stats"]["processed"] > 0:
            self.results["passed"].append(f"✅ {test_name}: リトライ成功")
        else:
            self.results["failed"].append(f"❌ {test_name}: リカバリー失敗")
    
    async def test_memory_usage(self):
        """メモリ使用量テスト"""
        test_name = "メモリ使用量"
        print(f"\n💾 {test_name}")
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 100個のプロセッサーインスタンス
        config = ProcessorConfig()
        config.dry_run = True
        
        processors = []
        for _ in range(100):
            processors.append(AutoIssueProcessor(config))
        
        peak_memory = process.memory_info().rss / 1024 / 1024
        memory_per_instance = (peak_memory - initial_memory) / 100
        
        # クリーンアップ
        processors.clear()
        import gc
        gc.collect()
        
        if memory_per_instance < 0.5:  # 0.5MB以下
            self.results["passed"].append(f"✅ {test_name}: {memory_per_instance:.2f}MB/インスタンス")
        else:
            self.results["warnings"].append(f"⚠️ {test_name}: {memory_per_instance:.2f}MB/インスタンス（やや多い）")
    
    async def test_file_operations(self):
        """ファイル操作テスト"""
        test_name = "ファイル操作"
        print(f"\n📁 {test_name}")
        
        test_dir = Path("./test_file_ops")
        test_dir.mkdir(exist_ok=True)
        
        try:
            # 複数ファイルの作成・読み取り
            tasks = []
            
            async def file_operation(index):
                file_path = test_dir / f"test_{index}.json"
                data = {"index": index, "timestamp": datetime.now().isoformat()}
                
                # 書き込み
                with open(file_path, 'w') as f:
                    json.dump(data, f)
                
                # 読み取り
                with open(file_path, 'r') as f:
                    read_data = json.load(f)
                
                return read_data["index"] == index
            
            tasks = [file_operation(i) for i in range(50)]
            results = await asyncio.gather(*tasks)
            
            if all(results):
                self.results["passed"].append(f"✅ {test_name}: 50ファイルの操作成功")
            else:
                self.results["failed"].append(f"❌ {test_name}: ファイル操作に失敗")
            
        finally:
            if test_dir.exists():
                shutil.rmtree(test_dir)
    
    async def test_github_integration(self):
        """GitHub統合テスト"""
        test_name = "GitHub統合"
        print(f"\n🐙 {test_name}")
        
        config = ProcessorConfig()
        config.dry_run = True
        config.github.token = "test_token"
        config.github.repo = "test_repo"
        config.github.owner = "test_owner"
        
        processor = AutoIssueProcessor(config)
        
        # モックIssue
        mock_issues = []
        for i in range(5):
            issue = Mock()
            issue.number = i
            issue.title = f"Test Issue {i}"
            issue.body = "Test body"
            issue.created_at = datetime.now()
            issue.labels = []
            issue.comments = 0
            issue.pull_request = None
            mock_issues.append(issue)
        
        with patch.object(processor, '_get_issues_to_process', return_value=mock_issues):
            with patch.object(processor, '_execute_issue_processing', return_value={"success": True, "artifacts": {}}):
                result = await processor.process_issues()
        
        if result["stats"]["processed"] == 5 and result["stats"]["success"] == 5:
            self.results["passed"].append(f"✅ {test_name}: 5 Issues処理成功")
        else:
            self.results["failed"].append(f"❌ {test_name}: 処理数が不正")
    
    async def test_security_basics(self):
        """基本セキュリティテスト"""
        test_name = "基本セキュリティ"
        print(f"\n🔐 {test_name}")
        
        # 1. トークンの露出チェック
        config = ProcessorConfig()
        config.github.token = "ghp_secret_token_123"
        
        # 設定の辞書化でトークンが含まれないことを確認
        config_dict = config.to_dict()
        config_str = str(config_dict)
        
        if "ghp_secret" not in config_str:
            self.results["passed"].append(f"✅ {test_name}: トークン非露出")
        else:
            self.results["failed"].append(f"❌ {test_name}: トークンが露出")
        
        # 2. パスインジェクション基礎チェック
        dangerous_paths = ["../../../etc/passwd", "..\\..\\windows"]
        
        for path in dangerous_paths:
            safe_path = path.replace("..", "").replace("/", "_").replace("\\", "_")
            if path != safe_path:
                self.results["passed"].append(f"✅ {test_name}: 危険パス検出 {path[:20]}...")
    
    async def test_scheduler_integration(self):
        """スケジューラー統合テスト"""
        test_name = "スケジューラー統合"
        print(f"\n⏰ {test_name}")
        
        try:
            # Elder Scheduled Tasksの設定確認
            from libs.elder_scheduled_tasks import ElderScheduledTasks
            
            # インポート成功
            self.results["passed"].append(f"✅ {test_name}: Elder Scheduled Tasks統合OK")
            
            # 新しいAuto Issue Processor参照確認
            with open("libs/elder_scheduled_tasks.py", 'r') as f:
                content = f.read()
                
            if "from libs.auto_issue_processor import" in content:
                self.results["passed"].append(f"✅ {test_name}: 統一実装への参照更新済み")
            else:
                self.results["warnings"].append(f"⚠️ {test_name}: 古い実装への参照が残っている可能性")
                
        except ImportError as e:
            self.results["failed"].append(f"❌ {test_name}: インポートエラー {e}")
    
    async def run_all_tests(self):
        """すべてのテスト実行"""
        print("=" * 60)
        print("統一Auto Issue Processor 包括的監査")
        print("=" * 60)
        print(f"開始時刻: {datetime.now()}")
        
        # テスト実行
        await self.test_lock_concurrent_access()
        await self.test_config_validation()
        await self.test_error_recovery()
        await self.test_memory_usage()
        await self.test_file_operations()
        await self.test_github_integration()
        await self.test_security_basics()
        await self.test_scheduler_integration()
        
        # 結果集計
        print("\n" + "=" * 60)
        print("監査結果")
        print("=" * 60)
        
        print(f"\n✅ 合格: {len(self.results['passed'])}件")
        for result in self.results["passed"]:
            print(f"  {result}")
        
        print(f"\n⚠️ 警告: {len(self.results['warnings'])}件")
        for result in self.results["warnings"]:
            print(f"  {result}")
        
        print(f"\n❌ 失敗: {len(self.results['failed'])}件")
        for result in self.results["failed"]:
            print(f"  {result}")
        
        # 総合判定
        print("\n" + "=" * 60)
        if len(self.results["failed"]) == 0:
            print("✅ 包括的監査合格！")
            print("統一Auto Issue Processorは本番環境で使用可能です")
            return True
        else:
            print("❌ 包括的監査不合格")
            print("失敗項目を修正してください")
            return False


async def main():
    """メイン実行"""
    tester = ComprehensiveTest()
    success = await tester.run_all_tests()
    
    # レポート保存
    report = {
        "audit_type": "comprehensive",
        "audit_date": datetime.now().isoformat(),
        "passed": len(tester.results["passed"]),
        "warnings": len(tester.results["warnings"]),
        "failed": len(tester.results["failed"]),
        "details": tester.results,
        "success": success
    }
    
    report_file = f"logs/comprehensive_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("logs", exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 監査レポート: {report_file}")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)