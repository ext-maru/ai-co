#!/usr/bin/env python3
"""
Claude Desktop → AI Company Task送信
Task Tracker統合版
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.rabbit_manager import RabbitManager
from libs.ai_command_helper import AICommandHelper
from datetime import datetime
import json
import uuid

class ClaudeDesktopTaskSender:
    """Claude DesktopからAI Companyへタスク送信（Task Tracker統合）"""
    
    def __init__(self):
        self.rabbit = RabbitManager()
        self.ai_helper = AICommandHelper()
        
    def send_development_task(self, prompt: str, task_type: str = "development", 
                            priority: int = 3, files_context: list = None):
        """開発タスクを送信（Task Trackerで自動追跡）"""
        
        # タスクID生成
        task_id = f"claude_desktop_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # タスクデータ構築
        task_data = {
            'task_id': task_id,
            'task_type': task_type,
            'prompt': prompt,
            'priority': priority,
            'source': 'claude_desktop',
            'created_at': datetime.now().isoformat(),
            'metadata': {
                'requested_by': 'Claude Desktop',
                'context_files': files_context or [],
                'tracking_enabled': True
            }
        }
        
        # ai_tasksキューに送信（pm_workerがTask Trackerに自動登録）
        self.rabbit.publish_message('ai_tasks', task_data, priority=priority)
        
        print(f"📤 タスク送信完了: {task_id}")
        print(f"   タイプ: {task_type}")
        print(f"   優先度: {'★' * priority}")
        print(f"   追跡URL: http://localhost:5555")
        
        return task_id
    
    def send_tracked_command(self, command: str, description: str = ""):
        """コマンド実行をTask Tracker付きで送信"""
        
        # コマンド実行用のbashスクリプト作成
        bash_content = f"""#!/bin/bash
# Task Tracked Command from Claude Desktop
cd /home/aicompany/ai_co

echo "📋 Task Tracker記録付きコマンド実行"
echo "コマンド: {command}"

# Task Trackerに記録
source venv/bin/activate
python3 -c "
from libs.task_tracker_client import TaskTrackerClient
client = TaskTrackerClient()
task_id = client.create_task(
    task_id='cmd_$(date +%Y%m%d_%H%M%S)',
    title='[CMD] {command[:50]}',
    description='{description or command}',
    priority=2,
    assignee='ai_command_executor'
)
print(f'Task ID: {{task_id}}')
"

# コマンド実行
{command}

echo "✅ コマンド実行完了"
"""
        
        cmd_id = self.ai_helper.create_bash_command(
            bash_content, 
            f"tracked_cmd_{datetime.now().strftime('%H%M%S')}"
        )
        
        print(f"📤 追跡付きコマンド送信: {cmd_id}")
        return cmd_id


def create_claude_desktop_helper():
    """Claude Desktop用のヘルパースクリプト作成"""
    
    helper_content = '''#!/usr/bin/env python3
"""
Claude Desktop Helper for AI Company Integration
Task Tracker統合サポート
"""

from claude_desktop_task_sender import ClaudeDesktopTaskSender

# シングルトンインスタンス
sender = ClaudeDesktopTaskSender()

def send_dev_task(prompt: str, priority: int = 3):
    """開発タスクを送信"""
    return sender.send_development_task(prompt, "development", priority)

def send_fix_task(prompt: str):
    """バグ修正タスクを送信（高優先度）"""
    return sender.send_development_task(prompt, "bugfix", 5)

def send_test_task(prompt: str):
    """テストタスクを送信（低優先度）"""
    return sender.send_development_task(prompt, "test", 2)

def track_command(command: str):
    """コマンドを追跡付きで実行"""
    return sender.send_tracked_command(command)

# 使いやすいエイリアス
dev = send_dev_task
fix = send_fix_task
test = send_test_task
cmd = track_command

print("🤖 Claude Desktop Helper loaded!")
print("使い方:")
print("  dev('新機能を実装してください')")
print("  fix('エラーを修正してください')")
print("  test('テストを作成してください')")
print("  cmd('ls -la')")
'''
    
    helper_path = PROJECT_ROOT / "claude_desktop_helper.py"
    with open(helper_path, 'w') as f:
        f.write(helper_content)
    
    print(f"✅ Claude Desktop Helperを作成: {helper_path}")


# テスト関数
def test_claude_desktop_integration():
    """Claude Desktop統合テスト"""
    print("🤖 Claude Desktop × Task Tracker テスト")
    print("=" * 60)
    
    sender = ClaudeDesktopTaskSender()
    
    # テストタスク送信
    test_tasks = [
        ("新しいデータ分析ワーカーを作成してください", "development", 3),
        ("ログローテーション機能にバグがあるので修正してください", "bugfix", 5),
        ("RAGシステムの単体テストを追加してください", "test", 2),
    ]
    
    task_ids = []
    for prompt, task_type, priority in test_tasks:
        print(f"\n📋 送信: {prompt[:50]}...")
        task_id = sender.send_development_task(prompt, task_type, priority)
        task_ids.append(task_id)
    
    print("\n✅ テスト完了!")
    print(f"\n📊 送信されたタスク: {len(task_ids)}個")
    print("\n確認方法:")
    print("1. Task Tracker Web: http://localhost:5555")
    print("2. タスク一覧: ./scripts/task list")
    print("3. pm_workerログ: tail -f logs/pm_worker.log | grep Task")
    
    return task_ids


if __name__ == "__main__":
    # ヘルパー作成
    create_claude_desktop_helper()
    
    # テスト実行
    test_claude_desktop_integration()
