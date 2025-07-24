#!/usr/bin/env python3
"""計画書の内容とタスク抽出をテスト"""

import sys
sys.path.insert(0, '/home/aicompany/ai_co/libs')

from pathlib import Path
import re

def extract_tasks_manually(file_path):
    """計画書からタスクを手動で抽出"""
    tasks = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Markdownのチェックボックスを検索
    # - [ ] タスク名 or - [x] 完了タスク
    pattern = r'^\s*-\s*\[([ x])\]\s+(.+)$'
    
    for line in content.split('\n'):
        match = re.match(pattern, line)
        if match:
            status = 'completed' if match.group(1) == 'x' else 'pending'
            task_title = match.group(2).strip()
            tasks.append({
                'title': task_title,
                'status': status,
                'line': line
            })
    
    return tasks

def main():
    """テスト実行"""
    # テスト用の計画書を選択
    test_files = [
        '/home/aicompany/ai_co/docs/plans/PLANNING_DOCUMENT_MANAGEMENT_RULES.md',
        '/home/aicompany/ai_co/docs/plans/PROJECT_WEB_PORTAL_MASTER_PLAN.md',
        '/home/aicompany/ai_co/docs/plans/PHASE_STABILIZATION_PLAN_2025.0md'
    ]
    
    # 繰り返し処理
    for file_path in test_files:
        if Path(file_path).exists():
            print(f"\n📋 ファイル: {Path(file_path).name}")
            tasks = extract_tasks_manually(file_path)
            
            if tasks:
                print(f"   ✅ タスク数: {len(tasks)}")
                print("   📝 タスク一覧:")
                for i, task in enumerate(tasks[:5]):  # 最初の5個のみ表示
                    status_icon = "✅" if task['status'] == 'completed' else "⬜"
                    print(f"      {i+1}. {status_icon} {task['title']}")
                if len(tasks) > 5:
                    print(f"      ... 他 {len(tasks) - 5} タスク")
            else:
                print("   ℹ️  タスクが見つかりませんでした")

if __name__ == "__main__":
    main()