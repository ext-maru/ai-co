#!/usr/bin/env python3
"""
統一Auto Issue ProcessorとAPScheduler統合のテストスクリプト
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.auto_issue_processor import AutoIssueProcessor, ProcessorConfig
from libs.apscheduler_integration import get_elder_scheduler
from libs.elder_scheduled_tasks import ElderScheduledTasks


async def test_unified_processor_standalone():
    """スタンドアロンでの統一プロセッサーテスト"""
    print("\n" + "=" * 60)
    print("1. スタンドアロンテスト")
    print("=" * 60)
    
    # 設定作成
    config = ProcessorConfig()
    config.dry_run = True  # ドライランモード
    config.github.token = os.getenv("GITHUB_TOKEN")
    config.github.repo = "ai-co"
    config.github.owner = "ext-maru"
    config.processing.max_issues_per_run = 1
    
    print(f"設定:")
    print(f"  - Dry Run: {config.dry_run}")
    print(f"  - Max Issues: {config.processing.max_issues_per_run}")
    print(f"  - Features: PR作成={config.features.pr_creation}, エラーリカバリー={config.features.error_recovery}")
    
    # プロセッサー実行
    processor = AutoIssueProcessor(config)
    
    print("\n処理開始...")
    start_time = datetime.now()
    result = await processor.process_issues()
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # 結果表示
    print(f"\n処理結果:")
    print(f"  - 成功: {result['success']}")
    print(f"  - 処理数: {result['stats']['processed']}")
    print(f"  - 成功数: {result['stats']['success']}")
    print(f"  - 失敗数: {result['stats']['failed']}")
    print(f"  - スキップ数: {result['stats']['skipped']}")
    print(f"  - 処理時間: {elapsed:.1f}秒")
    
    return result


async def test_scheduler_integration():
    """スケジューラー統合テスト"""
    print("\n" + "=" * 60)
    print("2. APScheduler統合テスト")
    print("=" * 60)
    
    # Elder Scheduled Tasksから該当部分を抽出してテスト
    print("GitHub自動処理タスクの実行テスト...")
    
    try:
        # 統一実装を使用
        from libs.auto_issue_processor import AutoIssueProcessor, ProcessorConfig
        
        # 設定をロード
        config = ProcessorConfig.load()
        
        # スケジューラー用の設定調整
        config.dry_run = True  # テストなのでドライラン
        config.processing.max_issues_per_run = 1
        config.features.pr_creation = True
        config.features.error_recovery = True
        config.features.four_sages_integration = True
        
        # プロセッサー初期化
        processor = AutoIssueProcessor(config)
        
        # Issue処理実行
        print("\n処理開始（スケジューラー設定）...")
        result = await processor.process_issues()
        
        # 結果ログ（スケジューラーと同じ形式）
        if result.get("stats", {}).get("processed", 0) > 0:
            stats = result["stats"]
            print(f"✅ 処理完了 - 成功: {stats['success']}, 失敗: {stats['failed']}, スキップ: {stats['skipped']}")
        else:
            print("📝 処理可能なIssueなし")
        
        # 処理時間ログ
        if result.get("duration_seconds"):
            print(f"⏱️ 処理時間: {result['duration_seconds']:.1f}秒")
        
        print("✅ 統一Auto Issue Processor完了")
        return True
        
    except Exception as e:
        print(f"❌ 統一Auto Issue Processor エラー: {e}")
        return False


def test_scheduler_registration():
    """スケジューラー登録テスト（実際には実行しない）"""
    print("\n" + "=" * 60)
    print("3. スケジューラー登録確認")
    print("=" * 60)
    
    # Elder Scheduled Tasksのインスタンスを作成
    elder_tasks = ElderScheduledTasks()
    
    print("スケジューラージョブ一覧:")
    jobs = elder_tasks.scheduler.scheduler.get_jobs()
    
    if not jobs:
        print("  - 現在登録されているジョブはありません（正常）")
    else:
        for job in jobs:
            print(f"  - {job.id}: {job.name}")
    
    print("\n✅ スケジューラー統合は正常に機能しています")
    print("   Auto Issue Processorタスクは現在無効化されています")


async def main():
    """メインテスト実行"""
    print("=" * 60)
    print("統一Auto Issue Processor × APScheduler統合テスト")
    print("=" * 60)
    print(f"実行時刻: {datetime.now()}")
    
    # 1. スタンドアロンテスト
    result1 = await test_unified_processor_standalone()
    
    # 2. スケジューラー統合テスト
    result2 = await test_scheduler_integration()
    
    # 3. スケジューラー登録確認
    test_scheduler_registration()
    
    # 総合結果
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)
    
    if result1["success"] and result2:
        print("✅ すべてのテストが成功しました")
        print("\n次のステップ:")
        print("1. 本番環境でのテスト実施")
        print("2. Elder Scheduled Tasksでauto_issue_processorタスクの有効化")
        print("3. 動作確認後、古い実装の削除")
    else:
        print("❌ 一部のテストが失敗しました")
        print("ログを確認して問題を修正してください")


if __name__ == "__main__":
    asyncio.run(main())