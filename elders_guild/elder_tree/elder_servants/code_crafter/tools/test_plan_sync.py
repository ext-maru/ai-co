#!/usr/bin/env python3
"""Plan Projects Sync テストスクリプト"""

import sys
import os

# プロジェクトのルートパスを追加
sys.path.insert(0, '/home/aicompany/ai_co/libs')

import asyncio
from task_elder.plan_projects_sync import PlanProjectsSync

async def main():
    """メイン実行関数"""
    print("🔄 Plan Projects Sync システムテスト開始")
    
    try:
        # GitHub トークンの確認
        github_token = os.environ.get('GITHUB_TOKEN')
        if not github_token:
            print("⚠️  警告: GITHUB_TOKEN が設定されていません")
            print("   GitHub Projects同期は制限されます")
        
        # システムを初期化
        sync_system = PlanProjectsSync(github_token)
        
        # システム状況を確認
        status = await sync_system.get_sync_status()
        print(f"\n📊 システム状況:")
        print(f"   📋 監視中の計画書: {status['monitored_plans']}")
        print(f"   ⏰ アクティブスケジュール: {status['active_schedules']}")
        print(f"   🏥 健全性: {status['health_status']}")
        print(f"   📊 総同期数: {status['stats']['total_syncs']}")
        
        # 計画書ディレクトリの確認
        plans_path = sync_system.plans_path
        if plans_path.exists():
            plan_files = list(plans_path.glob("*.md"))
            print(f"\n📁 計画書ディレクトリ: {plans_path}")
            print(f"   📋 計画書ファイル数: {len(plan_files)}")
            if plan_files:
                print("   📄 計画書リスト:")
                for i, plan in enumerate(plan_files[:5]):  # 最初の5件のみ表示
                    print(f"      {i+1}. {plan.name}")
                if len(plan_files) > 5:
                    print(f"      ... 他 {len(plan_files) - 5} ファイル")
        else:
            print(f"\n❌ エラー: 計画書ディレクトリが存在しません: {plans_path}")
            return
        
        # 変更検出テスト
        print("\n🔍 変更検出テストを実行...")
        changes = await sync_system.scan_all_plans()
        if changes:
            print(f"   ✅ {len(changes)}件の変更を検出")
            for plan_file, change_types in list(changes.items())[:3]:  # 最初の3件のみ表示
                print(f"      📋 {plan_file}: {[c.value for c in change_types]}")
        else:
            print("   ℹ️  変更は検出されませんでした")
        
        print("\n✅ テスト完了")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())