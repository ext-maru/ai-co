#!/usr/bin/env python3
"""
AI Todoシステムの現在の状態を簡潔に表示
"""

import sys
from pathlib import Path
from datetime import datetime
import json

PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

print(f"\n🤖 AI Todoシステム状態 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# 1. ai_todoディレクトリ
todo_dir = PROJECT_ROOT / "ai_todo"
if todo_dir.exists():
    files = list(todo_dir.glob("*"))
    print(f"\n📂 ai_todoディレクトリ: ✅ 存在 ({len(files)}ファイル)")
    
    # ToDoリスト
    todo_lists = [f for f in files if not "_result_" in f.name]
    results = [f for f in files if "_result_" in f.name]
    
    print(f"  📋 ToDoリスト: {len(todo_lists)}個")
    for f in todo_lists:
        print(f"    - {f.name}")
    
    print(f"  📊 実行結果: {len(results)}個")
    for f in results:
        print(f"    - {f.name}")
else:
    print("\n📂 ai_todoディレクトリ: ❌ 未作成")

# 2. 知識ベース
kb_dir = PROJECT_ROOT / "knowledge_base" / "ai_learning"
if kb_dir.exists():
    kb_files = list(kb_dir.glob("*"))
    print(f"\n🧠 知識ベース: ✅ 存在 ({len(kb_files)}ファイル)")
    for f in kb_files[:3]:
        print(f"  - {f.name} ({f.stat().st_size} bytes)")
else:
    print("\n🧠 知識ベース: ❌ 未作成")

# 3. 最新のログ (todo関連)
log_dir = PROJECT_ROOT / "ai_commands" / "logs"
todo_logs = sorted([f for f in log_dir.glob("*todo*.log") if f.is_file()], 
                  key=lambda x: x.stat().st_mtime, reverse=True)[:3]

print(f"\n📋 最新のTodo関連ログ:")
for log in todo_logs:
    mtime = datetime.fromtimestamp(log.stat().st_mtime)
    print(f"  - {log.name} ({mtime.strftime('%H:%M:%S')})")

# 4. ai-todoコマンドの存在確認
ai_todo_cmd = PROJECT_ROOT / "scripts" / "ai-todo"
print(f"\n🔧 ai-todoコマンド: {'✅ 利用可能' if ai_todo_cmd.exists() else '❌ 未設定'}")

# 5. 実行中のタスク
pending_dir = PROJECT_ROOT / "ai_commands" / "pending"
todo_pending = list(pending_dir.glob("*todo*"))
print(f"\n⏳ Pending Todoタスク: {len(todo_pending)}個")

print("\n✨ 状態確認完了")
