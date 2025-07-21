#!/usr/bin/env python3
"""
Task Sage Phase 23 検証スクリプト
A2Aマルチプロセスエルダーフローによる検証
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from libs.four_sages.task.enhanced_task_sage import EnhancedTaskSage
from libs.four_sages.task.task_sage import TaskPriority, TaskStatus

async def validate_task_sage():
    """Task Sage Phase 23実装の検証"""
    
    print("=" * 60)
    print("Task Sage Phase 23 実装検証開始")
    print("=" * 60)
    
    # Enhanced Task Sage インスタンス作成
    try:
        sage = EnhancedTaskSage()
        print("✅ Enhanced Task Sage インスタンス作成成功")
    except Exception as e:
        print(f"❌ インスタンス作成エラー: {e}")
        return
    
    # 1. 機能確認
    print("\n1. 実装機能の確認:")
    features = {
        "基本Task Sage": hasattr(sage, 'task_repository'),
        "動的優先度エンジン": hasattr(sage, 'priority_engine'),
        "実行時間予測": hasattr(sage, 'time_predictor'),
        "リソース最適化": hasattr(sage, 'resource_engine'),
        "スケジューリング最適化": hasattr(sage, 'scheduling_optimizer'),
        "トラッキングDB統合": hasattr(sage, 'tracking_db')
    }
    
    for feature, exists in features.items():
        status = "✅" if exists else "❌"
        print(f"  {status} {feature}")
    
    # 2. テストタスク作成
    print("\n2. テストタスク作成:")
    test_task = {
        "type": "create_task",
        "title": "Phase 23 検証タスク",
        "description": "Task Sage トラッキング統合の検証",
        "task_type": "development",  # 正しいタスクタイプに変更
        "priority": "high",
        "assignee": "claude_elder"
    }
    
    try:
        result = await sage.process_request(test_task)
        if result.get("success"):
            task_id = result.get("task_id")
            print(f"  ✅ タスク作成成功: ID={task_id}")
        else:
            print(f"  ❌ タスク作成失敗: {result.get('error')}")
            return
    except Exception as e:
        print(f"  ❌ エラー発生: {e}")
        return
    
    # 3. 動的優先度計算
    print("\n3. 動的優先度計算テスト:")
    try:
        predict_result = await sage.process_request({
            "type": "predict_completion",
            "task_id": task_id
        })
        
        if predict_result.get("success"):
            prediction = predict_result.get("prediction", {})
            print(f"  ✅ 動的優先度: {prediction.get('dynamic_priority', 'N/A')}")
            print(f"  ✅ 予測実行時間: {prediction.get('predicted_hours', 'N/A')}時間")
            print(f"  ✅ 信頼区間: ±{prediction.get('confidence_interval', 'N/A')}時間")
        else:
            print(f"  ❌ 予測失敗: {predict_result.get('error')}")
    except Exception as e:
        print(f"  ❌ エラー発生: {e}")
    
    # 4. リソース分析
    print("\n4. リソース分析テスト:")
    try:
        resource_result = await sage.process_request({
            "type": "analyze_resources"
        })
        
        if resource_result.get("success"):
            analysis = resource_result.get("analysis", {})
            print(f"  ✅ 現在のリソース使用状況:")
            print(f"     - CPU: {analysis.get('current_usage', {}).get('cpu', 'N/A')}%")
            print(f"     - メモリ: {analysis.get('current_usage', {}).get('memory', 'N/A')}%")
            print(f"  ✅ 最適化提案: {len(analysis.get('optimization_suggestions', []))}件")
        else:
            print(f"  ❌ リソース分析失敗: {resource_result.get('error')}")
    except Exception as e:
        print(f"  ❌ エラー発生: {e}")
    
    # 5. 能力一覧
    print("\n5. Task Sage 能力一覧:")
    try:
        capabilities = await sage.get_capabilities()
        print(f"  ✅ 総能力数: {len(capabilities)}")
        
        # 新機能の確認
        new_capabilities = [
            "dynamic_priority_calculation",
            "execution_time_prediction", 
            "resource_optimization",
            "schedule_optimization"
        ]
        
        for cap in new_capabilities:
            found = any(cap in str(c) for c in capabilities)
            status = "✅" if found else "❌"
            print(f"  {status} {cap}")
    except Exception as e:
        print(f"  ❌ エラー発生: {e}")
    
    print("\n" + "=" * 60)
    print("検証完了")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(validate_task_sage())