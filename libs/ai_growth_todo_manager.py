#!/usr/bin/env python3
"""
AI Growth Todo Manager
AIが自律的にタスクを処理し、学習していくシステム
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import logging

from libs.ai_command_helper import AICommandHelper
from libs.ai_log_viewer import AILogViewer
from libs.ai_program_runner import AIProgramRunner


class AIGrowthTodoManager:
    """AI自律型ToDoリスト管理システム"""

    def __init__(self):
        self.helper = AICommandHelper()
        self.runner = AIProgramRunner()
        self.viewer = AILogViewer()

        # パス設定
        self.todo_dir = PROJECT_ROOT / "ai_todo"
        self.knowledge_dir = PROJECT_ROOT / "knowledge_base" / "ai_learning"

        # ディレクトリ作成
        self.todo_dir.mkdir(exist_ok=True)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

        # ロガー設定
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler(PROJECT_ROOT / "logs" / "ai_growth_todo.log")
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def create_todo_list(self, name: str, tasks: list) -> dict:
        """ToDoリストを作成"""
        todo_data = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "tasks": [
                {
                    "id": i,
                    "description": task["description"],
                    "type": task.get("type", "command"),
                    "content": task["content"],
                    "priority": task.get("priority", "normal"),
                    "status": "pending",
                    "depends_on": task.get("depends_on", []),
                }
                for i, task in enumerate(tasks)
            ],
        }

        # ToDoリストを保存
        todo_file = (
            self.todo_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(todo_file, "w") as f:
            json.dump(todo_data, f, indent=2)

        self.logger.info(f"Created todo list: {name} with {len(tasks)} tasks")
        return todo_data

    def process_todo_with_learning(self, todo_name: str):
        """ToDoリストを処理し、結果から学習"""

        # 最新のToDoファイルを見つける
        todo_files = list(self.todo_dir.glob(f"{todo_name}_*.json"))
        if not todo_files:
            raise FileNotFoundError(f"Todo list '{todo_name}' not found")

        latest_todo = max(todo_files, key=lambda x: x.stat().st_mtime)

        # 処理スクリプトを生成
        processing_script = f'''#!/usr/bin/env python3
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
with open("{latest_todo}", 'r') as f:
    todo_data = json.load(f)

# 実行ログ
execution_log = []
learning_points = []

print("🤖 AI自律ToDoリスト処理開始！")
print(f"タスク数: {{len(todo_data['tasks'])}}")

# 各タスクを処理
completed_tasks = []
for task in todo_data['tasks']:
    print(f"\\n=== Task {{task['id']+1}}/{{len(todo_data['tasks'])}}: {{task['description']}} ===")

    # 依存関係チェック
    if task['depends_on']:
        pending_deps = [dep for dep in task['depends_on'] if dep not in completed_tasks]
        if pending_deps:
            print(f"⏳ 依存タスク待機中: {{pending_deps}}")
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
            temp_file = Path(f"/tmp/ai_task_{{task['id']}}.py")
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
        execution_log.append({{
            "task_id": task['id'],
            "description": task['description'],
            "status": "success" if success else "failed",
            "duration": duration,
            "output": output,
            "timestamp": datetime.now().isoformat()
        }})

        if success:
            print(f"✅ 成功 ({{duration:.2f}}秒)")
            completed_tasks.append(task['id'])

            # 成功パターンを学習
            if duration < 1.0:
                learning_points.append({{
                    "type": "performance",
                    "task": task['description'],
                    "insight": "高速実行可能なタスク"
                }})
        else:
            print(f"❌ 失敗: {{output[:200]}}")

            # エラーパターンを学習
            error_pattern = analyze_error(output)
            learning_points.append({{
                "type": "error",
                "task": task['description'],
                "error": error_pattern,
                "potential_fix": suggest_fix(error_pattern)
            }})

            # 自動修正を試みる
            if "ModuleNotFoundError" in output:
                print("📦 必要なモジュールをインストール中...")
                module_name = output.split("'")[1]
                subprocess.run([sys.executable, "-m", "pip", "install", module_name])
                learning_points.append({{
                    "type": "auto_fix",
                    "action": f"pip install {{module_name}}"
                }})

    except Exception as e:
        print(f"⚠️ 予期しないエラー: {{str(e)}}")
        execution_log.append({{
            "task_id": task['id'],
            "description": task['description'],
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }})

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
    fixes = {{
        "missing_module": "pip install [module_name]",
        "permission_error": "chmod +x [file] or use sudo",
        "file_not_found": "create required file or check path",
        "syntax_error": "check code syntax",
        "unknown_error": "manual investigation needed"
    }}
    return fixes.get(error_pattern, "manual investigation needed")

# 実行サマリー
total_tasks = len(todo_data['tasks'])
successful_tasks = sum(1 for log in execution_log if log.get('status') == 'success')
failed_tasks = sum(1 for log in execution_log if log.get('status') in ['failed', 'error'])

summary = {{
    "todo_name": todo_data['name'],
    "execution_date": datetime.now().isoformat(),
    "total_tasks": total_tasks,
    "successful": successful_tasks,
    "failed": failed_tasks,
    "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
    "total_duration": sum(log.get('duration', 0) for log in execution_log),
    "learning_points": learning_points,
    "execution_log": execution_log
}}

# 結果を保存
result_file = Path("{self.todo_dir}") / f"{{todo_data['name']}}_result_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}.json"
with open(result_file, 'w') as f:
    json.dump(summary, f, indent=2)

# 学習内容を知識ベースに追加
if learning_points:
    knowledge_file = Path("{self.knowledge_dir}") / f"learning_{{datetime.now().strftime('%Y%m%d')}}.jsonl"
    with open(knowledge_file, 'a') as f:
        for point in learning_points:
            f.write(json.dumps(point) + '\\n')

print(f"\\n🎉 ToDoリスト処理完了！")
print(f"成功: {{successful_tasks}}/{{total_tasks}} タスク")
print(f"学習ポイント: {{len(learning_points)}}個")
print(f"結果保存先: {{result_file}}")

# Slack通知用の出力
if failed_tasks > 0:
    print(f"\\n⚠️ {{failed_tasks}}個のタスクが失敗しました。ログを確認してください。")
'''

        # AI Program Runnerで実行
        result = self.runner.run_python_program(
            processing_script,
            f"process_todo_{todo_name}",
            f"ToDoリスト '{todo_name}' の自律処理",
        )

        self.logger.info(f"Processed todo list: {todo_name}")
        return result

    def get_learning_insights(self, days: int = 7) -> dict:
        """過去n日間の学習内容を取得"""
        insights = {
            "error_patterns": {},
            "performance_tips": [],
            "auto_fixes": [],
            "total_learnings": 0,
        }

        # 学習ファイルを読み込み
        for learning_file in self.knowledge_dir.glob("learning_*.jsonl"):
            with open(learning_file, "r") as f:
                for line in f:
                    try:
                        learning = json.loads(line.strip())
                        insights["total_learnings"] += 1

                        if learning["type"] == "error":
                            error_type = learning.get("error", "unknown")
                            insights["error_patterns"][error_type] = (
                                insights["error_patterns"].get(error_type, 0) + 1
                            )
                        elif learning["type"] == "performance":
                            insights["performance_tips"].append(learning["insight"])
                        elif learning["type"] == "auto_fix":
                            insights["auto_fixes"].append(learning["action"])
                    except:
                        continue

        return insights

    def create_daily_todo(self):
        """日次の自己改善ToDoリストを自動生成"""
        # 過去の学習内容を分析
        insights = self.get_learning_insights()

        # 基本的な日次タスク
        tasks = [
            {
                "description": "システム状態チェック",
                "type": "bash",
                "content": "ps aux | grep worker | wc -l && df -h && free -h",
            },
            {
                "description": "エラーログ分析",
                "type": "python",
                "content": """
import re
from pathlib import Path

log_dir = Path("/home/aicompany/ai_co/logs")
errors = []

for log_file in log_dir.glob("*.log"):
    with open(log_file, 'r', errors='ignore') as f:
        content = f.read()
        errors.extend(re.findall(r'ERROR.*', content))

print(f"Found {len(errors)} errors in logs")
if errors:
    print("Most recent errors:")
    for error in errors[-5:]:
        print(f"  - {error[:100]}")
""",
            },
            {
                "description": "パフォーマンスレポート生成",
                "type": "ai-send",
                "content": '"過去24時間のタスク実行パフォーマンスレポートを生成" general',
            },
        ]

        # エラーが多い場合は修正タスクを追加
        if insights["error_patterns"]:
            most_common_error = max(
                insights["error_patterns"].items(), key=lambda x: x[1]
            )[0]
            tasks.append(
                {
                    "description": f"頻出エラー '{most_common_error}' の自動修正実装",
                    "type": "ai-send",
                    "content": f'"{most_common_error}エラーを自動的に検出して修正する仕組みを実装" code',
                    "priority": "high",
                }
            )

        # ToDoリストを作成
        return self.create_todo_list("daily_self_improvement", tasks)


if __name__ == "__main__":
    # テスト実行
    manager = AIGrowthTodoManager()

    # サンプルToDoリスト作成
    sample_tasks = [
        {"description": "ワーカー状態確認", "type": "bash", "content": "ai-status"},
        {
            "description": "最新ログ確認",
            "type": "python",
            "content": """
from libs.ai_log_viewer import AILogViewer
viewer = AILogViewer()
summary = viewer.get_execution_summary()
print(f"Command logs: {summary['command_logs']}")
print(f"Program logs: {summary['program_logs']}")
print(f"Failed programs: {summary['failed_programs']}")
""",
        },
        {
            "description": "システム最適化案の生成",
            "type": "ai-send",
            "content": '"現在のシステム状態を分析して最適化案を提案" general',
        },
    ]

    todo = manager.create_todo_list("test_todo", sample_tasks)
    print(f"Created todo list: {todo['name']}")
