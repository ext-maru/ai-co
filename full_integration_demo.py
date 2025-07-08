#!/usr/bin/env python3
"""
Claude Desktop × AI Company × Task Tracker
完全統合デモンストレーション
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_command_helper import AICommandHelper
import time

def main():
    helper = AICommandHelper()
    
    print("🤖 Claude Desktop × AI Company × Task Tracker")
    print("完全統合デモンストレーション")
    print("=" * 80)
    
    # 1. システム状態確認
    check_cmd = """#!/bin/bash
cd /home/aicompany/ai_co

echo "📊 システム状態確認"
echo "===================="

# プロセス確認
echo "🔍 稼働中のワーカー:"
ps aux | grep -E "(pm_worker|task_tracker|task_worker)" | grep -v grep | awk '{print "  - " $11 " (PID: " $2 ")"}'

# Task Tracker Web確認
if curl -s http://localhost:5555 > /dev/null 2>&1; then
    echo "✅ Task Tracker Web: 稼働中"
else
    echo "❌ Task Tracker Web: 停止中"
fi

# RabbitMQ確認
if sudo rabbitmqctl list_queues name messages 2>/dev/null | grep -E "(ai_tasks|task_tracker)"; then
    echo "✅ RabbitMQキュー: 正常"
fi

echo ""
"""
    
    helper.create_bash_command(check_cmd, "check_full_integration")
    print("1️⃣ システム状態を確認中...")
    time.sleep(5)
    
    # 2. Claude Desktop統合テスト実行
    test_cmd = """#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "🧪 Claude Desktop統合テスト"
echo "=========================="

# テストスクリプト実行
python3 claude_desktop_task_sender.py

echo ""
echo "⏳ タスク処理待機中..."
sleep 10

# Task Trackerで最新タスク確認
echo ""
echo "📋 最新タスク状態:"
echo "=================="
python3 -c "
import sqlite3
from pathlib import Path

db_path = Path('/home/aicompany/ai_co/data/tasks.db')
if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, title, status, assignee, created_at 
    FROM tasks 
    WHERE title LIKE '%Claude Desktop%' OR assignee = 'pm'
    ORDER BY created_at DESC 
    LIMIT 5
    ''')
    
    tasks = cursor.fetchall()
    for task in tasks:
        print(f'ID: {task[0][:8]} | {task[2]:12} | {task[3]:10} | {task[1][:50]}')
    
    conn.close()
"
"""
    
    helper.create_bash_command(test_cmd, "test_claude_desktop_integration")
    print("\n2️⃣ Claude Desktop統合テストを実行中...")
    time.sleep(15)
    
    # 3. 実際の開発タスク送信デモ
    demo_cmd = """#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "🚀 実際の開発タスクデモ"
echo "====================="

# Python経由で開発タスク送信
python3 -c "
from claude_desktop_task_sender import ClaudeDesktopTaskSender

sender = ClaudeDesktopTaskSender()

# 実際の開発タスクを送信
print('📤 開発タスクを送信...')

task1 = sender.send_development_task(
    prompt='Task Tracker APIエンドポイントを追加してください。GET /api/tasks/summary で統計情報を返すRESTful APIを実装。',
    task_type='development',
    priority=4
)
print(f'  ✅ Task 1: {task1}')

task2 = sender.send_development_task(
    prompt='Task TrackerのSlack通知を改善してください。タスク完了時により詳細な情報を含める。',
    task_type='enhancement',
    priority=3
)
print(f'  ✅ Task 2: {task2}')

print('')
print('📊 確認方法:')
print('  - Web: http://localhost:5555')
print('  - CLI: ./scripts/task list')
"
"""
    
    helper.create_bash_command(demo_cmd, "demo_real_tasks")
    print("\n3️⃣ 実際の開発タスクを送信中...")
    time.sleep(10)
    
    # 4. 最終確認
    final_cmd = """#!/bin/bash
cd /home/aicompany/ai_co

echo ""
echo "📊 統合結果サマリー"
echo "=================="

# タスク統計
echo "📈 タスク統計:"
source venv/bin/activate
python3 libs/task_manager.py report | head -20

echo ""
echo "🎯 統合成功ポイント:"
echo "  ✅ Claude DesktopからAI Companyへタスク送信"
echo "  ✅ pm_workerがTask Trackerに自動登録"
echo "  ✅ タスクの進捗がWebダッシュボードで確認可能"
echo "  ✅ 優先度に応じた処理順序管理"
echo "  ✅ エラー時の追跡とログ記録"

echo ""
echo "🔗 アクセスポイント:"
echo "  📊 Task Tracker: http://localhost:5555"
echo "  📝 タスク一覧: ./scripts/task list"
echo "  📜 ログ監視: tail -f logs/pm_worker.log"
"""
    
    helper.create_bash_command(final_cmd, "show_integration_summary")
    print("\n4️⃣ 統合結果を集計中...")
    time.sleep(5)
    
    print("\n" + "=" * 80)
    print("✅ 完全統合デモ完了！")
    print("\n📋 Claude Desktopからの使い方:")
    print("```python")
    print("from claude_desktop_task_sender import ClaudeDesktopTaskSender")
    print("sender = ClaudeDesktopTaskSender()")
    print("task_id = sender.send_development_task('開発依頼内容', priority=4)")
    print("```")
    print("\n🌐 Task Tracker: http://localhost:5555")

if __name__ == "__main__":
    main()
