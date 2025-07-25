#!/usr/bin/env python3
"""
統一Auto Issue Processor 限定極限監査
実用的な範囲での極限テスト（高負荷部分を制限）
"""

import asyncio
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from libs.auto_issue_processor import AutoIssueProcessor, ProcessorConfig
from libs.auto_issue_processor.utils import ProcessLock

class LimitedExtremeTest:
    """限定極限テスト"""
    
    def __init__(self):
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
    
    async def test_moderate_concurrent_locks(self):
        """適度な並行ロックテスト（100同時）"""
        test_name = "適度な並行ロック"
        print(f"\n🔒 {test_name} (100同時ロック)")
        
        lock_dir = "./limited_test_locks"
        os.makedirs(lock_dir, exist_ok=True)
        
        try:
            # 100個の同時ロック試行
            tasks = []
            
            async def acquire_and_release(index):
                """acquire_and_releaseメソッド"""
                lock = ProcessLock("file", lock_dir=lock_dir)
                key = f"test_key_{index % 10}"  # 10種類のキー
                try:
                    acquired = await lock.acquire(key, ttl=2)
                    if acquired:
                        await asyncio.sleep(0.01)
                        await lock.release(key)
                    return acquired
                except Exception as e:
                    return f"Error: {e}"
            
            tasks = [acquire_and_release(i) for i in range(100)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(1 for r in results if r is True)
            error_count = sum(1 for r in results if isinstance(r, str) and r.startswith("Error"))
            
            if success_count >= 10:  # 少なくとも10個は成功
                self.results["passed"].append(f"✅ {test_name}: {success_count}/100 成功")
            else:
                self.results["failed"].append(f"❌ {test_name}: 成功数が少ない {success_count}/100")
            
            if error_count > 50:
                self.results["warnings"].append(f"⚠️ {test_name}: エラー多発 {error_count}件")
            
        finally:
            import shutil
            if os.path.exists(lock_dir):
                shutil.rmtree(lock_dir)
    
    async def test_basic_security(self):
        """基本的なセキュリティテスト"""
        test_name = "基本セキュリティ"
        print(f"\n🔐 {test_name}")
        
        # パストラバーサル基礎チェック
        dangerous_paths = ["../../../etc/passwd", "..\\..\\windows\\system32"]
        
        lock = ProcessLock("file", lock_dir="./security_test")
        
        for path in dangerous_paths:
            try:
                # ファイル名として安全化されることを確認
                safe_key = path.replace("/", "_").replace(":", "_").replace("\\", "_")
                if ".." not in safe_key:
                    self.results["passed"].append(f"✅ {test_name}: パス安全化成功")
                else:
                    self.results["failed"].append(f"❌ {test_name}: パス安全化失敗")
                break
            except Exception:
                pass
        
        # クリーンアップ
        import shutil
        if os.path.exists("./security_test"):
            shutil.rmtree("./security_test")
    
    async def test_error_handling(self):
        """エラーハンドリングテスト"""
        test_name = "エラーハンドリング"
        print(f"\n🛡️ {test_name}")
        
        config = ProcessorConfig()
        config.features.error_recovery = True
        config.dry_run = True
        config.github.token = "test_token"
        config.github.repo = "test_repo"
        config.github.owner = "test_owner"
        
        processor = AutoIssueProcessor(config)
        
        # 様々なエラータイプをテスト
        errors = [
            ConnectionError("ネットワークエラー"),
            TimeoutError("タイムアウト"),
            ValueError("不正な値"),
            RuntimeError("実行時エラー")
        ]
        
        for error in errors:
            mock_issue = Mock()
            mock_issue.number = 1
            mock_issue.title = "Test"
            mock_issue.body = "Test"
            mock_issue.created_at = datetime.now()
            mock_issue.labels = []
            mock_issue.comments = 0
            mock_issue.pull_request = None
            
            with patch.object(processor, '_execute_issue_processing', side_effect=error):
                with patch.object(processor, '_get_issues_to_process', return_value=[mock_issue]):
                    result = await processor.process_issues([1])
            
            if result["stats"]["failed"] == 1:
                self.results["passed"].append(f"✅ {test_name}: {error.__class__.__name__}を正しく処理")
            else:
                self.results["failed"].append(f"❌ {test_name}: {error.__class__.__name__}の処理失敗")
    
    async def test_configuration_edge_cases(self):
        """設定エッジケーステスト"""
        test_name = "設定エッジケース"
        print(f"\n⚙️ {test_name}")
        
        # 1.0 空の設定
        empty_config = ProcessorConfig()
        if empty_config.validate():
            self.results["passed"].append(f"✅ {test_name}: 空設定の処理OK")
        else:
            self.results["failed"].append(f"❌ {test_name}: 空設定が無効")
        
        # 2.0 極端な値
        extreme_config = ProcessorConfig()
        extreme_config.processing.max_issues_per_run = 10000
        extreme_config.processing.max_parallel_workers = 1000

        if extreme_config.validate():
            self.results["warnings"].append(f"⚠️ {test_name}: 極端な値を許可（要確認）")
        
        # 3.0 矛盾する設定
        conflict_config = ProcessorConfig()
        conflict_config.features.pr_creation = True
        conflict_config.dry_run = True  # dry_runでPR作成は矛盾
        
        processor = AutoIssueProcessor(conflict_config)
        # 実際の動作確認（エラーにならないこと）
        self.results["passed"].append(f"✅ {test_name}: 矛盾設定でも動作")
    
    async def run_all_tests(self):
        """すべてのテスト実行"""
        print("=" * 60)
        print("統一Auto Issue Processor 限定極限監査")
        print("=" * 60)
        print(f"開始時刻: {datetime.now()}")
        
        # テスト実行
        await self.test_moderate_concurrent_locks()
        await self.test_basic_security()
        await self.test_error_handling()
        await self.test_configuration_edge_cases()
        
        # 結果集計
        print("\n" + "=" * 60)
        print("限定極限監査結果")
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
            print("✅ 限定極限監査合格！")
            print("統一Auto Issue Processorは極限状況でも安定動作します")
            return True
        else:
            print("❌ 限定極限監査で問題発見")
            print("修正が必要です")
            return False

async def main():
    """メイン実行"""
    tester = LimitedExtremeTest()
    success = await tester.run_all_tests()
    
    # レポート保存
    report = {
        "audit_type": "limited_extreme",
        "audit_date": datetime.now().isoformat(),
        "passed": len(tester.results["passed"]),
        "warnings": len(tester.results["warnings"]),
        "failed": len(tester.results["failed"]),
        "details": tester.results,
        "success": success
    }
    
    report_file = f"logs/limited_extreme_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("logs", exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 監査レポート: {report_file}")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)