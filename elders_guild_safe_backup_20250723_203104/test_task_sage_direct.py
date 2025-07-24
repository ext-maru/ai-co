#!/usr/bin/env python3
"""
📋 Task Sage A2A Agent - 直接テスト
Elder Loop Phase 2対応：依存関係なしの直接テスト

python-a2aがない環境でのビジネスロジック動作確認
"""

import asyncio
import json
import sys
import logging
from datetime import datetime

# パス追加
sys.path.append("/home/aicompany/ai_co/elders_guild")

# ビジネスロジックの直接テスト
from task_sage.business_logic import TaskProcessor


async def test_task_processor_direct():
    pass


"""TaskProcessor直接テスト"""
        # 1.0 TaskProcessor初期化テスト
        print("\\n🔧 1.0 TaskProcessor初期化テスト...")
        processor = TaskProcessor()
        print("   ✅ TaskProcessor初期化成功")
        
        # 2.0 タスク作成テスト
        print("\\n📝 2.0 タスク作成テスト...")
        task_data = {
            "title": "Task Sage A2A変換テスト",
            "description": "Elder LoopによるTask Sage実装テスト",
            "estimated_hours": 8.0,
            "priority": 3,  # TaskPriority.HIGH
            "tags": ["a2a", "elder-loop", "task-sage"],
            "complexity_factors": {
                "lines_of_code": 1200,
                "complexity": "medium",
                "dependencies": ["knowledge-sage"]
            }
        }
        
        create_result = await processor.process_action("create_task", task_data)
        
        if create_result["success"]:
            task_id = create_result["data"]["task_id"]
            print(f"   ✅ タスク作成成功: {task_id}")
            print(f"   タイトル: {create_result['data']['title']}")
            print(f"   ステータス: {create_result['data']['status']}")
        else:
            print(f"   ❌ タスク作成失敗: {create_result['error']}")
            return False
        
        # 3.0 タスク取得テスト
        print("\\n🔍 3.0 タスク取得テスト...")
        get_result = await processor.process_action("get_task", {"task_id": task_id})
        
        if get_result["success"]:
            print("   ✅ タスク取得成功")
            print(f"   タイトル: {get_result['data']['title']}")
            print(f"   説明: {get_result['data']['description'][:50]}...")
        else:
            print(f"   ❌ タスク取得失敗: {get_result['error']}")
            return False
        
        # 4.0 タスク更新テスト
        print("\\n✏️ 4.0 タスク更新テスト...")
        update_data = {
            "task_id": task_id,
            "updates": {
                "status": "in_progress",
                "actual_hours": 2.5
            }
        }
        
        update_result = await processor.process_action("update_task", update_data)
        
        if update_result["success"]:
            print("   ✅ タスク更新成功")
            print(f"   ステータス: {update_result['data']['status']}")
        else:
            print(f"   ❌ タスク更新失敗: {update_result['error']}")
            return False
        
        # 5.0 タスク一覧テスト
        print("\\n📋 5.0 タスク一覧テスト...")
        
        # 追加タスクを作成
        for i in range(2):
            additional_task = task_data.copy()
            additional_task["title"] = f"追加テストタスク {i+1}"
            additional_task["priority"] = 2  # MEDIUM
            await processor.process_action("create_task", additional_task)
        
        list_result = await processor.process_action("list_tasks", {})
        
        if list_result["success"]:
            task_count = list_result["data"]["total_count"]
            print(f"   ✅ タスク一覧取得成功: {task_count}件")
            for task in list_result["data"]["tasks"][:3]:  # 最初の3つを表示
                print(f"     - {task['title']} ({task['status']})")
        else:
            print(f"   ❌ タスク一覧取得失敗: {list_result['error']}")
            return False
        
        # 6.0 工数見積もりテスト
        print("\\n⏱️ 6.0 工数見積もりテスト...")
        estimation_data = {
            "complexity_factors": {
                "lines_of_code": 2000,
                "complexity": "high",
                "dependencies": ["knowledge-sage", "rag-sage"]
            }
        }
        
        estimate_result = await processor.process_action("estimate_effort", estimation_data)
        
        if estimate_result["success"]:
            estimated_hours = estimate_result["data"]["estimated_hours"]
            confidence = estimate_result["data"]["confidence"]
            print(f"   ✅ 工数見積もり成功: {estimated_hours:0.2f}時間")
            print(f"   信頼度: {confidence:0.2%}")
            print(f"   内訳: {estimate_result['data']['breakdown']}")
        else:
            print(f"   ❌ 工数見積もり失敗: {estimate_result['error']}")
            return False
        
        # 7.0 依存関係解決テスト
        print("\\n🔗 7.0 依存関係解決テスト...")
        
        # 依存関係のあるタスクを作成
        dependent_tasks = [
            {
                "title": "データベース設計",
                "estimated_hours": 4.0,
                "dependencies": []
            },
            {
                "title": "API実装", 
                "estimated_hours": 6.0,
                "dependencies": []  # 後で設定
            },
            {
                "title": "統合テスト",
                "estimated_hours": 3.0,
                "dependencies": []  # 後で設定
            }
        ]
        
        created_task_ids = []
        for task_spec in dependent_tasks:
            result = await processor.process_action("create_task", task_spec)
            if result["success"]:
                created_task_ids.append(result["data"]["task_id"])
        
        # 依存関係を設定（手動で）
        if len(created_task_ids) >= 3:
            # API実装はデータベース設計に依存
            await processor.process_action("update_task", {
                "task_id": created_task_ids[1],
                "updates": {"dependencies": [created_task_ids[0]]}
            })
            
            # 統合テストはAPI実装に依存
            await processor.process_action("update_task", {
                "task_id": created_task_ids[2], 
                "updates": {"dependencies": [created_task_ids[1]]}
            })
        
        # 依存関係解決実行
        dependency_result = await processor.process_action("resolve_dependencies", {
            "task_ids": created_task_ids
        })
        
        if dependency_result["success"]:
            ordered_tasks = dependency_result["data"]["ordered_tasks"]
            print(f"   ✅ 依存関係解決成功: {len(ordered_tasks)}タスク")
            for i, task in enumerate(ordered_tasks):
                print(f"     {i+1}. {task['title']} ({task['estimated_hours']}h)")
        else:
            print(f"   ❌ 依存関係解決失敗: {dependency_result['error']}")
            return False
        
        # 8.0 統計情報テスト
        print("\\n📊 8.0 統計情報テスト...")
        stats_result = await processor.process_action("get_statistics", {})
        
        if stats_result["success"]:
            stats = stats_result["data"]
            print("   ✅ 統計情報取得成功")
            print(f"   総タスク数: {stats['task_statistics']['total_tasks']}")
            print(f"   ステータス分布: {stats['task_statistics']['status_breakdown']}")
            print(f"   完了率: {stats['task_statistics']['completion_rate']:0.1f}%")
            print(f"   総見積もり時間: {stats['time_statistics']['total_estimated_hours']:0.1f}h")
        else:
            print(f"   ❌ 統計情報取得失敗: {stats_result['error']}")
            return False
        
        # 9.0 プロジェクト管理テスト
        print("\\n📁 9.0 プロジェクト管理テスト...")
        
        # プロジェクト作成
        project_data = {
            "name": "Task Sage A2A変換プロジェクト",
            "description": "Elder LoopによるTask Sage A2A実装プロジェクト",
            "tags": ["a2a", "elder-loop"]
        }
        
        project_result = await processor.process_action("create_project", project_data)
        
        if project_result["success"]:
            project_id = project_result["data"]["project_id"]
            print(f"   ✅ プロジェクト作成成功: {project_id}")
            print(f"   名前: {project_result['data']['name']}")
        else:
            print(f"   ❌ プロジェクト作成失敗: {project_result['error']}")
            return False
        
        # プロジェクト一覧
        projects_result = await processor.process_action("list_projects", {})
        
        if projects_result["success"]:
            project_count = projects_result["data"]["total_count"]
            print(f"   ✅ プロジェクト一覧取得成功: {project_count}件")
        else:
            print(f"   ❌ プロジェクト一覧取得失敗: {projects_result['error']}")
            return False
        
        # 10.0 最終結果サマリー
        print("\\n📊 10.0 テスト結果サマリー")
        print("=" * 60)
        
        final_stats = await processor.process_action("get_statistics", {})
        if final_stats["success"]:
            stats = final_stats["data"]
            print(f"🎉 Task Sage Business Logic テスト完全成功！")
            print(f"   総タスク数: {stats['task_statistics']['total_tasks']}")
            print(f"   総プロジェクト数: {stats['project_statistics']['total_projects']}")
            print(f"   総見積もり時間: {stats['time_statistics']['total_estimated_hours']:0.1f}h")
            print(f"   システム状態: {stats['system_health']['active_processor']}")
            return True
        else:
            print("❌ 最終統計取得でエラーが発生")
            return False
        
    except Exception as e:
        print(f"\\n💥 テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    pass

        """メイン実行"""
        print("\\n🏛️ Task Sage Business Logic - Elder Loop Phase 2完了")
        print("   Knowledge Sageパターン適用成功")
        print("   ビジネスロジック分離完全成功")
        print("   全機能テスト合格")
        return True
    else:
        print("\\n🔧 一部機能で調整が必要")
        print("   Elder Loop Phase 4で修正します")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)