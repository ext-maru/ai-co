#!/usr/bin/env python3
"""
Simple TaskWorker for AI Company - Direct Claude CLI Execution
テンプレート機能なしのシンプルなTaskWorker
"""

import json
import subprocess
import os
from datetime import datetime
from pathlib import Path
import sys

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.base_worker import BaseWorker
from libs.env_config import get_config
import requests

# 絵文字定義
EMOJI = {
    'start': '🚀',
    'success': '✅',
    'error': '❌',
    'task': '📋',
    'robot': '🤖'
}

class SimpleTaskWorker(BaseWorker):
    """シンプルなTaskWorker - 直接Claude CLI実行"""
    
    def __init__(self, worker_id=None):
        super().__init__(worker_type='task', worker_id=worker_id)
        
        # キュー設定をオーバーライド
        self.input_queue = 'ai_tasks'
        self.output_queue = 'ai_pm'
        
        self.config = get_config()
        self.output_dir = PROJECT_ROOT / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # 拡張ツール設定
        self.allowed_tools = [
            'Edit', 'Write', 'Read', 'MultiEdit', 'Glob', 'Grep', 'LS',
            'Bash', 'Task', 'WebFetch', 'WebSearch',
            'NotebookRead', 'NotebookEdit', 'TodoRead', 'TodoWrite',
            'exit_plan_mode'
        ]
        
        self.logger.info(f"{EMOJI['start']} SimpleTaskWorker initialized")

    def process_message(self, ch, method, properties, body):
        """メッセージを処理"""
        try:
            # メッセージをパース
            task = json.loads(body.decode('utf-8'))
            task_id = task.get('task_id', task.get('id', 'unknown'))
            task_type = task.get('task_type', task.get('type', 'general'))
            prompt = task.get('prompt', '')
            priority = task.get('priority', 'normal')
            
            self.logger.info(f"{EMOJI['task']} Processing task {task_id}")
            self.logger.info(f"  Type: {task_type}, Priority: {priority}")
            
            # Claude実行
            result = self._execute_claude(task_id, prompt)
            
            if result['success']:
                self.logger.info(f"{EMOJI['success']} Task {task_id} completed")
                
                # 結果をPM-Workerに送信（本格モード）
                self.send_result({
                    'task_id': task_id,
                    'status': 'completed',
                    'output': result['output'],
                    'error': None,
                    'original_prompt': prompt,
                    'task_type': task_type,
                    'is_slack_task': task_id.startswith('slack_')
                })
            else:
                self.logger.error(f"{EMOJI['error']} Task {task_id} failed")
                self.logger.error(f"Error details: {result['error']}")
                if result.get('output'):
                    self.logger.error(f"Output: {result.get('output')}")
                
                # 失敗時もPM-Workerに送信（PM-Workerが代替応答を生成）
                self.send_result({
                    'task_id': task_id,
                    'status': 'failed',
                    'output': result.get('output'),
                    'error': result['error'],
                    'original_prompt': prompt,
                    'task_type': task_type,
                    'is_slack_task': task_id.startswith('slack_'),
                    'needs_pm_fallback': True  # PM-Workerに代替処理を要求
                })
                
        except Exception as e:
            self.logger.error(f"{EMOJI['error']} Error processing message: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _execute_claude(self, task_id: str, prompt: str):
        """Claude CLIを実行（シミュレーションモード対応）"""
        
        # シミュレーションモードチェック
        import os
        simulation_mode = os.getenv('TASK_WORKER_SIMULATION_MODE', 'false').lower() in ('true', '1', 'yes', 'on')
        
        if simulation_mode:
            self.logger.info(f"🎭 シミュレーションモードで応答生成")
            return self._generate_simulation_response(prompt)
        
        # 実際のClaude CLI実行
        cmd = [
            "claude",
            "--print",
            "--allowedTools", ",".join(self.allowed_tools)
        ]
        
        self.logger.info(f"{EMOJI['robot']} Executing Claude CLI")
        
        try:
            # 環境変数の設定
            env = os.environ.copy()
            env.update({
                'PYTHONPATH': str(PROJECT_ROOT),
                'ANTHROPIC_API_KEY': self.config.ANTHROPIC_API_KEY
            })
            
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
                timeout=600,
                env=env
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'output': result.stdout,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'output': result.stdout,
                    'error': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': None,
                'error': "Execution timeout after 600 seconds"
            }
    
    def _generate_simulation_response(self, prompt: str):
        """シミュレーション応答生成"""
        prompt_lower = prompt.lower()
        
        # 日本語入力の検出
        has_japanese = any(ord(char) > 127 for char in prompt)
        
        # 基本的な挨拶
        if any(word in prompt_lower for word in ['hello', 'hi', 'こんにちは', 'はじめまして', 'やっと']):
            if has_japanese:
                return {
                    'success': True,
                    'output': 'こんにちは！私はPM-AI、プロジェクト管理のAIアシスタントです。今日はどのようなお手伝いができますか？',
                    'error': None
                }
            else:
                return {
                    'success': True,
                    'output': 'Hello! I am PM-AI, your AI assistant for project management. How can I help you today?',
                    'error': None
                }
        
        # コード生成リクエスト
        if any(word in prompt_lower for word in ['code', 'コード', 'create', '作成', 'implement', '実装']):
            if has_japanese:
                return {
                    'success': True,
                    'output': '''コードの作成をお手伝いします！例えばこんなPython関数が書けます：

    def cleanup(self):
        """TODO: cleanupメソッドを実装してください"""
        pass

    def stop(self):
        """TODO: stopメソッドを実装してください"""
        pass

    def initialize(self) -> None:
        """ワーカーの初期化処理"""
        # TODO: 初期化ロジックを実装してください
        logger.info(f"{self.__class__.__name__} initialized")
        pass

    def handle_error(self):
        """TODO: handle_errorメソッドを実装してください"""
        pass

    def get_status(self):
        """TODO: get_statusメソッドを実装してください"""
        pass

    def validate_config(self):
        """TODO: validate_configメソッドを実装してください"""
        pass

```python
def hello_world():
    """シンプルなHello World関数"""
    print("PM-AIからこんにちは！")
    return "成功"

if __name__ == "__main__":
    result = hello_world()
    print(f"結果: {result}")
```

これはシミュレーション応答です。完全なClaude機能を使うにはAnthropic APIキーを設定してください。''',
                    'error': None
                }
            else:
                return {
                    'success': True,
                    'output': '''I can help you create code! Here's an example Python function:

```python
def hello_world():
    """A simple hello world function"""
    print("Hello from PM-AI!")
    return "Success"

if __name__ == "__main__":
    result = hello_world()
    print(f"Result: {result}")
```

This is a simulation response. Please set up your Anthropic API key for full Claude functionality.''',
                    'error': None
                }
        
        # プロジェクト管理関連
        if any(word in prompt_lower for word in ['project', 'プロジェクト', 'task', 'タスク', 'manage', '管理']):
            if has_japanese:
                return {
                    'success': True,
                    'output': '''PM-AIとして、以下の分野でお手伝いできます：

🎯 **プロジェクト管理**
- タスク分割と優先順位付け
- ワークフロー自動化
- 品質ゲート管理
- 進捗追跡

📊 **データドリブンな意思決定**
- プロジェクト健全性分析
- リスク特定
- リソース最適化提案

🔄 **プロセス自動化**
- 並列タスク実行
- 依存関係管理
- フェーズベースワークフロー制御

これはシミュレーション応答です。完全なAI駆動プロジェクト管理機能を使うにはAnthropic APIキーを設定してください！''',
                    'error': None
                }
            else:
                return {
                    'success': True,
                    'output': '''As PM-AI, I can help you with:

🎯 **Project Management**
- Task splitting and prioritization
- Workflow automation
- Quality gate management
- Progress tracking

📊 **Data-Driven Decisions**
- Project health analysis
- Risk identification
- Resource optimization recommendations

🔄 **Process Automation**
- Parallel task execution
- Dependency management
- Phase-based workflow control

This is a simulation response. Connect your Anthropic API key for full AI-powered project management capabilities!''',
                    'error': None
                }
        
        # デフォルト応答
        if has_japanese:
            return {
                'success': True,
                'output': f'''メッセージを受信しました： "{prompt[:100]}..."

🤖 **PM-AI シミュレーションモード**
Slack統合が正常に動作していることを確認するためのテスト応答です。

**利用可能な機能:**
- 知的タスク分割
- 並列実行管理
- ワークフロー自動化
- 意思決定支援

完全なAI応答を有効にするには、.envファイルでAnthropic APIキーを設定してください。

プロジェクト管理、コード作成、タスク整理のお手伝いをしましょうか？''',
                'error': None
            }
        else:
            return {
                'success': True,
                'output': f'''I received your message: "{prompt[:100]}..."

🤖 **PM-AI Simulation Mode**
This is a test response to confirm the Slack integration is working properly.

**Available Features:**
- Intelligent task splitting
- Parallel execution management  
- Workflow automation
- Decision support

To enable full AI responses, please configure your Anthropic API key in the .env file.

Would you like me to help with project management, code creation, or task organization?''',
                'error': None
            }
    
    def _send_direct_slack_response(self, task_id: str, response: str):
        """直接Slackに応答を送信"""
        try:
            # Slack設定を取得
            slack_config = self.config.get_slack_config()
            bot_token = slack_config.get('bot_token')
            channel_id = self.config.SLACK_POLLING_CHANNEL_ID
            
            if not bot_token:
                self.logger.warning("Slack bot token not found - skipping direct response")
                return
                
            # Slack Web API経由で応答送信
            url = "https://slack.com/api/chat.postMessage"
            headers = {
                "Authorization": f"Bearer {bot_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "channel": channel_id,
                "text": f"🤖 **PM-AI Response**\n\n{response}",
                "username": "PM-AI",
                "icon_emoji": ":robot_face:"
            }
            
            response_obj = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response_obj.status_code == 200:
                result = response_obj.json()
                if result.get('ok'):
                    self.logger.info(f"✅ 直接Slack応答送信成功: {task_id}")
                else:
                    self.logger.error(f"❌ Slack API Error: {result.get('error', 'Unknown')}")
            else:
                self.logger.error(f"❌ HTTP Error: {response_obj.status_code}")
                
        except Exception as e:
            self.logger.error(f"❌ 直接Slack応答送信エラー: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple TaskWorker')
    parser.add_argument('--worker-id', help='Worker ID')
    
    args = parser.parse_args()
    
    worker = SimpleTaskWorker(worker_id=args.worker_id)
    print(f"{EMOJI['start']} SimpleTaskWorker starting...")
    print(f"📥 Input queue: {worker.input_queue}")
    print(f"📤 Output queue: {worker.output_queue}")
    
    try:
        worker.start()
    except KeyboardInterrupt:
        print(f"\n{EMOJI['error']} Worker stopped by user")