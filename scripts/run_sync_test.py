#!/usr/bin/env python3
"""実際の同期テスト（1つの計画書のみ）"""

import sys
sys.path.insert(0, '/home/aicompany/ai_co/libs')

import asyncio
import os
from task_elder.plan_projects_sync import PlanProjectsSync

async def main():
    """テスト同期実行"""
    print("🔄 同期テスト開始")
    
    # GitHub トークン確認
    github_token = os.environ.get('GITHUB_TOKEN')
    if github_token:
        print(f"✅ GitHub Token: {github_token[:10]}...{github_token[-4:]}")
    
    # システムを初期化
    sync_system = PlanProjectsSync(github_token)
    
    # テスト用に1つの計画書だけ同期を試す
    test_plan = "PLANNING_DOCUMENT_MANAGEMENT_RULES.md"
    
    print(f"\n📋 テスト計画書: {test_plan}")
    
    # 変更を検出
    changes = await sync_system.detect_changes(test_plan)
    if changes:
        print(f"✅ 変更検出: {[c.value for c in changes]}")
        
        # プロジェクトIDを仮設定（実際にはGitHub Projectsから取得）
        test_project_id = "test_project_001"
        
        # 同期を実行（ドライラン）
        print("\n🔄 同期実行（ドライラン）...")
        # 実際の同期はGitHub Projects APIが必要なのでスキップ
        print("ℹ️  実際の同期はGitHub Projects設定が必要です")
    else:
        print("ℹ️  変更なし")
    
    # システム状況を表示
    status = await sync_system.get_sync_status()
    print(f"\n📊 最終状況:")
    print(f"   監視中: {status['monitored_plans']}計画書")
    print(f"   健全性: {status['health_status']}")

if __name__ == "__main__":
    asyncio.run(main())