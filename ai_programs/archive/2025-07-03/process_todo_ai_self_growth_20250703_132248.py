#!/usr/bin/env python3
"""
AI Todo Processor with Learning
自律的にタスクを処理し、エラーから学習する
"""

import json
import subprocess
import time
import sys
from pathlib import Path
from datetime import datetime

# ToDoリストを読み込み
with open("/home/aicompany/ai_co/ai_todo/ai_self_growth_20250703_111927.json", 'r') as f:
    todo_data = json.load(f)

# 実行ログ
execution_log = []
learning_points = []

print("🤖 AI自律ToDoリスト処理開始！")
print(f"タスク数: {len(todo_data['tasks'])}")

# 各タスクを処理
completed_tasks = []
for task in todo_data['tasks']:
    print(f"\n=== Task {task['id']+1}/{len(todo_data['tasks'])}: {task['description']} ===")
    
    # 依存関係チェック
    if task['depends_on']:
        pending_deps = [dep for dep in task['depends_on'] if dep not in completed_tasks]
        if pending_deps:
            print(f"⏳ 依存タスク待機中: {pending_deps}")
            continue
    
    start_time = time.time()
    
    try:
        # タスクタイプに応じて実行
        if task['type'] == 'bash':
            result = subprocess.run(task['content'], shell=True, capture_output=True, text=True)
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
        elif task['type'] == 'python':
            # Pythonコードを一時ファイルに保存して実行
            temp_file = Path(f"/tmp/ai_task_{task['id']}.py")
            temp_file.write_text(task['content'])
            result = subprocess.run([sys.executable, str(temp_file)], capture_output=True, text=True)
            success = result.returncode == 0
            output = result.stdout + result.stderr
            temp_file.unlink()
            
        elif task['type'] == 'ai-send':
            # AI-sendコマンドを実行
            cmd_parts = task['content'].split()
            result = subprocess.run(['ai-send'] + cmd_parts, capture_output=True, text=True)
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
        else:
            # デフォルトはコマンドとして実行
            result = subprocess.run(task['content'], shell=True, capture_output=True, text=True)
            success = result.returncode == 0
            output = result.stdout + result.stderr
        
        duration = time.time() - start_time
        
        # 実行結果を記録
        execution_log.append({
            "task_id": task['id'],
            "description": task['description'],
            "status": "success" if success else "failed",
            "duration": duration,
            "output": output,
            "timestamp": datetime.now().isoformat()
        })
        
        if success:
            print(f"✅ 成功 ({duration:.2f}秒)")
            completed_tasks.append(task['id'])
            
            # 成功パターンを学習
            if duration < 1.0:
                learning_points.append({
                    "type": "performance",
                    "task": task['description'],
                    "insight": "高速実行可能なタスク"
                })
        else:
            print(f"❌ 失敗: {output[:200]}")
            
            # エラーパターンを学習
            error_pattern = analyze_error(output)
            learning_points.append({
                "type": "error",
                "task": task['description'],
                "error": error_pattern,
                "potential_fix": suggest_fix(error_pattern)
            })
            
            # 自動修正を試みる
            if "ModuleNotFoundError" in output:
                print("📦 必要なモジュールをインストール中...")
                module_name = output.split("'")[1]
                subprocess.run([sys.executable, "-m", "pip", "install", module_name])
                learning_points.append({
                    "type": "auto_fix",
                    "action": f"pip install {module_name}"
                })
                
    except Exception as e:
        print(f"⚠️ 予期しないエラー: {str(e)}")
        execution_log.append({
            "task_id": task['id'],
            "description": task['description'],
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

# 学習結果をまとめる
def analyze_error(error_output):
    """エラーメッセージを分析"""
    if "ModuleNotFoundError" in error_output:
        return "missing_module"
    elif "Permission denied" in error_output:
        return "permission_error"
    elif "No such file or directory" in error_output:
        return "file_not_found"
    elif "syntax error" in error_output.lower():
        return "syntax_error"
    else:
        return "unknown_error"

def suggest_fix(error_pattern):
    """エラーパターンに基づく修正案"""
    fixes = {
        "missing_module": "pip install [module_name]",
        "permission_error": "chmod +x [file] or use sudo",
        "file_not_found": "create required file or check path",
        "syntax_error": "check code syntax",
        "unknown_error": "manual investigation needed"
    }
    return fixes.get(error_pattern, "manual investigation needed")

# 実行サマリー
total_tasks = len(todo_data['tasks'])
successful_tasks = sum(1 for log in execution_log if log.get('status') == 'success')
failed_tasks = sum(1 for log in execution_log if log.get('status') in ['failed', 'error'])

summary = {
    "todo_name": todo_data['name'],
    "execution_date": datetime.now().isoformat(),
    "total_tasks": total_tasks,
    "successful": successful_tasks,
    "failed": failed_tasks,
    "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
    "total_duration": sum(log.get('duration', 0) for log in execution_log),
    "learning_points": learning_points,
    "execution_log": execution_log
}

# 結果を保存
result_file = Path("/home/aicompany/ai_co/ai_todo") / f"{todo_data['name']}_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(result_file, 'w') as f:
    json.dump(summary, f, indent=2)

# 学習内容を知識ベースに追加
if learning_points:
    knowledge_file = Path("/home/aicompany/ai_co/knowledge_base/ai_learning") / f"learning_{datetime.now().strftime('%Y%m%d')}.jsonl"
    with open(knowledge_file, 'a') as f:
        for point in learning_points:
            f.write(json.dumps(point) + '\n')

print(f"\n🎉 ToDoリスト処理完了！")
print(f"成功: {successful_tasks}/{total_tasks} タスク")
print(f"学習ポイント: {len(learning_points)}個")
print(f"結果保存先: {result_file}")

# Slack通知用の出力
if failed_tasks > 0:
    print(f"\n⚠️ {failed_tasks}個のタスクが失敗しました。ログを確認してください。")
