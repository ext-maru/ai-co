#!/usr/bin/env python3
"""
AI Todo システムの初期起動スクリプト
AI Command Executorで自動実行
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_command_helper import AICommandHelper
import time

def setup_ai_todo_system():
    """AI TodoシステムをセットアップしてAI Command Executorで初期実行"""
    
    helper = AICommandHelper()
    
    print("🤖 AI自律型ToDoリストシステムを起動します")
    
    # 1. セットアップスクリプトを実行可能にする
    setup_commands = """#!/bin/bash
# スクリプトを実行可能にする
chmod +x /home/aicompany/ai_co/scripts/setup_ai_todo.sh
chmod +x /home/aicompany/ai_co/scripts/ai-todo

# シンボリックリンクを作成（存在しない場合）
if [ ! -L "/home/aicompany/ai_co/bin/ai-todo" ]; then
    ln -sf /home/aicompany/ai_co/scripts/ai-todo /home/aicompany/ai_co/bin/ai-todo
fi

echo "✅ 実行権限とリンクを設定しました"
"""
    
    helper.create_bash_command(setup_commands, "setup_ai_todo_permissions")
    print("✅ Step 1: 権限設定をAI Command Executorに登録")
    
    # 少し待機
    time.sleep(7)
    
    # 2. 初期ToDoリストを作成して実行
    initial_todo_script = """#!/usr/bin/env python3
import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_growth_todo_manager import AIGrowthTodoManager
from libs.ai_command_helper import AICommandHelper

# マネージャー初期化
manager = AIGrowthTodoManager()
helper = AICommandHelper()

# AI成長用の初期ToDoリスト
ai_growth_tasks = [
    {
        "description": "AI Companyワーカー状態分析",
        "type": "python",
        "content": '''
import subprocess
import json

# ワーカープロセスを確認
result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
workers = [line for line in result.stdout.split('\\\\n') if 'worker' in line.lower()]

print(f"アクティブなワーカー数: {len(workers)}")
for w in workers[:5]:
    print(f"  - {w[:80]}...")

# 分析結果を保存
analysis = {"worker_count": len(workers), "timestamp": str(datetime.now())}
with open("/tmp/worker_analysis.json", "w") as f:
    json.dump(analysis, f)
'''
    },
    {
        "description": "最近のエラーパターン学習",
        "type": "python",
        "content": '''
import re
from pathlib import Path
from collections import Counter

log_dir = Path("/home/aicompany/ai_co/logs")
error_patterns = Counter()

# 最近のログファイルからエラーを抽出
for log_file in sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime)[-10:]:
    try:
        with open(log_file, 'r', errors='ignore') as f:
            content = f.read()
            errors = re.findall(r'ERROR.*?(?=\\\\n|$)', content)
            for error in errors:
                # エラータイプを抽出
                if "ModuleNotFoundError" in error:
                    error_patterns["ModuleNotFoundError"] += 1
                elif "FileNotFoundError" in error:
                    error_patterns["FileNotFoundError"] += 1
                elif "PermissionError" in error:
                    error_patterns["PermissionError"] += 1
                else:
                    error_patterns["Other"] += 1
    except:
        pass

print("エラーパターン分析結果:")
for pattern, count in error_patterns.most_common():
    print(f"  {pattern}: {count}回")

# 学習結果を知識ベースに保存
import json
from datetime import datetime

kb_dir = Path("/home/aicompany/ai_co/knowledge_base/ai_learning")
kb_dir.mkdir(parents=True, exist_ok=True)

learning_entry = {
    "timestamp": datetime.now().isoformat(),
    "type": "error_analysis",
    "patterns": dict(error_patterns),
    "recommendation": "Most common errors should be auto-fixed"
}

with open(kb_dir / "error_patterns.jsonl", "a") as f:
    f.write(json.dumps(learning_entry) + "\\\\n")
'''
    },
    {
        "description": "システム最適化の提案生成",
        "type": "ai-send",
        "content": '"先ほどのワーカー分析とエラーパターンを踏まえて、AI Companyシステムの最適化案を3つ提案してください" general'
    },
    {
        "description": "自己診断レポート作成",
        "type": "python",
        "content": '''
from datetime import datetime
from pathlib import Path
import json

# レポート作成
report = {
    "date": datetime.now().isoformat(),
    "system": "AI Growth Todo System",
    "status": "operational",
    "capabilities": [
        "タスク自動実行",
        "エラーから学習",
        "自己改善提案",
        "知識ベース構築"
    ],
    "next_steps": [
        "エラー自動修正の実装",
        "パフォーマンス最適化",
        "より高度な学習アルゴリズム"
    ]
}

# レポートを保存
report_dir = Path("/home/aicompany/ai_co/ai_todo/reports")
report_dir.mkdir(exist_ok=True)

with open(report_dir / f"self_diagnosis_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
    json.dump(report, f, indent=2)

print("🎯 自己診断レポート作成完了")
print(f"私は学習し、成長しています！")
'''
    }
]

# ToDoリスト作成
todo = manager.create_todo_list("ai_self_growth", ai_growth_tasks)
print(f"✅ AI成長ToDoリスト作成: {len(ai_growth_tasks)}タスク")

# 処理実行をスケジュール
process_script = f'''
from libs.ai_growth_todo_manager import AIGrowthTodoManager
manager = AIGrowthTodoManager()
print("🚀 AI成長ToDoリストを処理開始...")
result = manager.process_todo_with_learning("ai_self_growth")
print("✨ AI成長プロセス完了！")
'''

helper.create_python_command(process_script, "ai_self_growth_execution")
print("✅ AI成長ToDoリストの実行をスケジュール")
"""
    
    helper.create_python_command(initial_todo_script, "create_ai_growth_todo")
    print("✅ Step 2: AI成長ToDoリストの作成をスケジュール")
    
    print("\n🎉 AI自律型ToDoリストシステムの起動完了！")
    print("\n今後の使い方:")
    print("  ai-todo create <name>        - 新しいToDoリスト作成")
    print("  ai-todo run <name>           - ToDoリスト実行")
    print("  ai-todo status               - 状態確認")
    print("  ai-todo learn                - 学習内容表示")
    print("  ai-todo daily                - 日次自己改善タスク実行")
    print("\n💡 AIは自動的に学習し、エラーを修正し、成長していきます！")


if __name__ == "__main__":
    setup_ai_todo_system()
