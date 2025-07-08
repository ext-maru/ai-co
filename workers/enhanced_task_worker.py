#!/usr/bin/env python3
"""
AI Company Enhanced TaskWorker with Prompt Template Support
プロンプトテンプレート機能を統合した強化版TaskWorker
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

# 絵文字定義
EMOJI = {
    'start': '🚀',
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'task': '📋',
    'thinking': '🤔',
    'complete': '🎉',
    'process': '⚙️',
    'robot': '🤖'
}
from core import ErrorSeverity, with_error_handling
from core import msg
from core.prompt_template_mixin import PromptTemplateMixin
from libs.rag_grimoire_integration import RagGrimoireIntegration, RagGrimoireConfig
from libs.slack_notifier import SlackNotifier
import logging


class EnhancedTaskWorker(BaseWorker, PromptTemplateMixin):
    """プロンプトテンプレート対応の強化版TaskWorker"""
    
    def __init__(self, worker_id=None):
        # BaseWorker初期化
        BaseWorker.__init__(self, worker_type='task', worker_id=worker_id)
        
        # キュー設定をオーバーライド
        self.input_queue = 'ai_tasks'
        self.output_queue = 'ai_pm'
        
        # PromptTemplateMixin初期化
        PromptTemplateMixin.__init__(self)
        
        self.config = get_config()
        self.output_dir = PROJECT_ROOT / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # ツールの設定（開発用に大幅拡張）
        self.model = getattr(self.config, 'WORKER_DEFAULT_MODEL', 'claude-sonnet-4-20250514')
        self.allowed_tools = getattr(self.config, 'WORKER_ALLOWED_TOOLS', [
            # ファイル操作
            'Edit', 'Write', 'Read', 'MultiEdit', 'Glob', 'Grep', 'LS',
            # システム操作
            'Bash', 'Task', 
            # Web操作
            'WebFetch', 'WebSearch',
            # ノートブック操作
            'NotebookRead', 'NotebookEdit',
            # タスク管理
            'TodoRead', 'TodoWrite',
            # 計画モード
            'exit_plan_mode'
        ])
        
        # 通知設定
        self.slack_notifier = SlackNotifier()
        
        # RAG Grimoire Integration
        self.rag_integration = None
        self.rag_config = RagGrimoireConfig(
            database_url=getattr(self.config, 'GRIMOIRE_DATABASE_URL', 'postgresql://localhost/grimoire'),
            search_threshold=getattr(self.config, 'RAG_SEARCH_THRESHOLD', 0.7),
            max_search_results=getattr(self.config, 'RAG_MAX_RESULTS', 10)
        )
        
        self.logger.info(f"{EMOJI['start']} Enhanced TaskWorker initialized with prompt templates")
        
        # Initialize RAG Grimoire Integration asynchronously
        self._initialize_rag_integration()

    def process_message(self, ch, method, properties, body):
        """メッセージを処理（プロンプトテンプレート使用）"""
        try:
            # メッセージをパース
            task = json.loads(body.decode('utf-8'))
            task_id = task.get('id', 'unknown')
            task_type = task.get('type', 'general')
            user_prompt = task.get('prompt', '')
            priority = task.get('priority', 'normal')
            
            self.logger.info(f"{EMOJI['task']} Processing task {task_id} with priority: {priority}")
            
            # テンプレート選択
            template_name = self._select_template(task_type, user_prompt)
            
            # プロンプト生成（RAG含む）
            generated_prompt = self.generate_prompt(
                template_name=template_name,
                variables={
                    'task_id': task_id,
                    'task_type': task_type,
                    'user_prompt': user_prompt,
                    'priority': priority,
                    'additional_instructions': self._get_additional_instructions(task),
                    'rag_context': self._get_rag_context(user_prompt)
                },
                include_rag=True
            )
            
            if not generated_prompt:
                raise Exception("Failed to generate prompt from template")
            
            # タスク履歴に記録開始
            self._record_task_start(task_id, task_type, user_prompt, generated_prompt)
            
            # Claude実行
            result = self._execute_claude(task_id, generated_prompt)
            
            if result['success']:
                # 成功時の処理
                self._handle_success(task_id, task, result)
                
                # プロンプトパフォーマンス評価
                self.evaluate_last_prompt(task_id, 0.9)  # 成功は高スコア
            else:
                # 失敗時の処理
                self._handle_failure(task_id, task, result)
                
                # プロンプトパフォーマンス評価
                self.evaluate_last_prompt(task_id, 0.3)  # 失敗は低スコア
                
            # ACK送信
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            # メッセージ処理エラー
            context = {
                'operation': 'process_message',
                'task_id': task.get('id', 'unknown') if 'task' in locals() else 'unknown',
                'task_type': task.get('type', 'unknown') if 'task' in locals() else 'unknown',
                'template_name': template_name if 'template_name' in locals() else 'unknown'
            }
            self.handle_error(e, context, severity=ErrorSeverity.HIGH)
            
            # エラー時もACK（無限ループ防止）
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
            # エラー結果を送信
            if 'task_id' in locals():
                self._send_error_result(task_id, str(e))
    
    def _initialize_rag_integration(self):
        """RAG Grimoire Integration を初期化"""
        try:
            import asyncio
            self.rag_integration = RagGrimoireIntegration(self.rag_config)
            # Create a new event loop for async initialization
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.rag_integration.initialize())
            loop.close()
            self.logger.info(f"{EMOJI['success']} RAG Grimoire Integration initialized successfully")
        except Exception as e:
            self.logger.error(f"{EMOJI['error']} Failed to initialize RAG Grimoire Integration: {e}")
            self.rag_integration = None
    
    def _get_rag_context(self, user_prompt: str) -> str:
        """RAG統合システムからコンテキストを取得"""
        if not self.rag_integration:
            return ""
        
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Unified search using grimoire integration
            results = loop.run_until_complete(
                self.rag_integration.search_unified(
                    query=user_prompt,
                    limit=5,
                    threshold=self.rag_config.search_threshold
                )
            )
            loop.close()
            
            if not results:
                return ""
            
            # Format RAG context
            context = "\n\n## Related Knowledge:\n"
            for result in results:
                context += f"- {result['content'][:200]}...\n"
                context += f"  Source: {result['source']} (Score: {result['similarity_score']:.2f})\n"
            
            return context
            
        except Exception as e:
            self.logger.warning(f"{EMOJI['warning']} RAG context retrieval failed: {e}")
            return ""
    
    def _select_template(self, task_type: str, user_prompt: str) -> str:
        """タスクに応じてテンプレートを選択"""
        # コード生成タスクの判定
        code_keywords = ['コード', 'プログラム', '実装', 'code', 'implement', 'create', 'build']
        if task_type == 'code' or any(keyword in user_prompt.lower() for keyword in code_keywords):
            return 'code_generation'
        
        # 高度なタスクの判定
        advanced_keywords = ['complex', '複雑', 'advanced', '高度', 'comprehensive']
        if any(keyword in user_prompt.lower() for keyword in advanced_keywords):
            return 'advanced'
        
        # デフォルト
        return 'default'
    
    def _get_additional_instructions(self, task: dict) -> str:
        """タスクから追加指示を生成"""
        instructions = []
        
        # 優先度に応じた指示
        priority = task.get('priority', 'normal')
        if priority == 'critical':
            instructions.append("This is a CRITICAL priority task. Focus on reliability and quick completion.")
        elif priority == 'high':
            instructions.append("This is a high priority task. Ensure quality and timely completion.")
        
        # 特定の要件
        if task.get('require_tests'):
            instructions.append("Include comprehensive unit tests for all functionality.")
        
        if task.get('require_docs'):
            instructions.append("Include detailed documentation and usage examples.")
        
        return '\n'.join(instructions)
    
    def _execute_claude(self, task_id: str, prompt: str):
        """Claude CLIを実行（既存のロジックを維持）"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = f"claude_session_{task_id}_{timestamp}"
        
        # ツールパラメータ構築
        tools_param = f"--allowedTools {','.join(self.allowed_tools)}"
        
        # コマンド構築（開発用に拡張）
        cmd = [
            "claude",
            "--model", self.model,
            "--profile", "aicompany", 
            "--chat-name", session_name,
            "--print",
            "--continue", "10",  # より多くの継続実行
            "--no-confirm",      # 確認プロンプトをスキップ
        ] + tools_param.split()
        
        # 開発環境用の追加設定
        if getattr(self.config, 'WORKER_DEV_MODE', True):
            cmd.extend([
                "--debug",           # デバッグモード
                "--verbose",         # 詳細ログ
            ])
        
        # --print フラグ使用時はプロンプトをコマンドライン引数として追加
        cmd.append(prompt)
        
        self.logger.info(f"{EMOJI['robot']} Executing Claude with template-generated prompt")
        self.logger.debug(f"Command: {' '.join(cmd[:20])}...")  # コマンドの最初の部分のみログ出力
        
        try:
            # 作業ディレクトリを設定（プロジェクトルートで実行）
            work_dir = getattr(self.config, 'WORKER_WORK_DIR', str(PROJECT_ROOT))
            
            # 環境変数の設定
            env = os.environ.copy()
            env.update({
                'PYTHONPATH': str(PROJECT_ROOT),
                'AI_VENV_ACTIVE': '1',
                'AI_AUTO_GIT_DISABLED': 'false',  # 開発用はGit有効
                'ANTHROPIC_API_KEY': self.config.ANTHROPIC_API_KEY
            })
            
            # --print フラグ使用時はstdinを使わない
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=work_dir,
                timeout=600,  # タイムアウトを10分に延長
                env=env
            )
            
            if result.returncode == 0:
                self.logger.info(f"{EMOJI['success']} Claude execution completed")
                return {
                    'success': True,
                    'output': result.stdout,
                    'error': None,
                    'session_name': session_name
                }
            else:
                self.logger.error(f"{EMOJI['error']} Claude execution failed")
                return {
                    'success': False,
                    'output': result.stdout,
                    'error': result.stderr,
                    'session_name': session_name
                }
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"{EMOJI['error']} Claude execution timeout")
            return {
                'success': False,
                'output': None,
                'error': "Execution timeout after 300 seconds",
                'session_name': session_name
            }
        except Exception as e:
            self.logger.error(f"{EMOJI['error']} Claude execution error: {str(e)}")
            return {
                'success': False,
                'output': None,
                'error': str(e),
                'session_name': session_name
            }
    
    def _record_task_start(self, task_id: str, task_type: str, prompt: str, generated_prompt: str):
        """タスク開始を記録"""
        from libs.task_history_db import TaskHistoryDB
        
        try:
            db = TaskHistoryDB()
            db.add_task(
                task_id=task_id,
                task_type=task_type,
                prompt=prompt,
                worker=self.worker_id,
                model=self.model,
                request_content=generated_prompt
            )
        except Exception as e:
            self.logger.warning(f"Failed to record task start: {e}")
    
    def _handle_success(self, task_id: str, task: dict, result: dict):
        """成功時の処理"""
        # 作成されたファイルを収集
        created_files = self._collect_created_files(task_id)
        
        # タスク履歴を更新
        self._update_task_history(task_id, 'completed', result['output'], created_files)
        
        # PMWorkerに送信
        pm_message = {
            'task_id': task_id,
            'status': 'completed',
            'files': created_files,
            'output': result['output'],
            'template_used': task.get('template_name', 'default')
        }
        
        self.send_result(pm_message)
        
        # Slack通知（エラー時でも処理を続行）
        try:
            self.slack_notifier.send_success(
                f"Task {task_id} completed successfully using template",
                details={
                    'Files created': len(created_files),
                    'Template': task.get('template_name', 'default')
                }
            )
        except Exception as notification_error:
            self.logger.warning(f"Failed to send Slack success notification: {notification_error}")
        
        self.logger.info(f"{EMOJI['success']} Task {task_id} completed with {len(created_files)} files")
    
    def _handle_failure(self, task_id: str, task: dict, result: dict):
        """失敗時の処理"""
        # タスク履歴を更新
        self._update_task_history(task_id, 'failed', result.get('output'), [], result['error'])
        
        # エラー結果を送信
        error_message = {
            'task_id': task_id,
            'status': 'failed',
            'error': result['error'],
            'output': result.get('output'),
            'template_used': task.get('template_name', 'default')
        }
        
        self.send_result(error_message)
        
        # Slack通知（エラー時でも処理を続行）
        try:
            self.slack_notifier.send_error(
                f"Task {task_id} failed",
                error=result['error']
            )
        except Exception as notification_error:
            self.logger.warning(f"Failed to send Slack error notification: {notification_error}")
        
        self.logger.error(f"{EMOJI['error']} Task {task_id} failed: {result['error']}")
    
    def _collect_created_files(self, task_id: str) -> list:
        """作成されたファイルを収集"""
        created_files = []
        
        try:
            # outputディレクトリ内のファイルを検索
            for file_path in self.output_dir.rglob("*"):
                try:
                    if file_path.is_file():
                        # 最近作成されたファイルをチェック
                        if (datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)).seconds < 600:
                            created_files.append({
                                'path': str(file_path.relative_to(PROJECT_ROOT)),
                                'size': file_path.stat().st_size,
                                'created': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                            })
                except (OSError, PermissionError) as e:
                    # 権限エラーや読み取りエラーを無視して継続
                    self.logger.warning(f"Unable to access file {file_path}: {e}")
                    continue
        except Exception as e:
            self.logger.warning(f"Error collecting files: {e}")
            
        return created_files
    
    def _update_task_history(self, task_id: str, status: str, response: str, 
                           files: list, error: str = None):
        """タスク履歴を更新"""
        from libs.task_history_db import TaskHistoryDB
        
        try:
            db = TaskHistoryDB()
            
            # Claudeの要約を抽出
            summary = self._extract_summary(response) if response else None
            
            db.update_task(
                task_id=task_id,
                status=status,
                response=response,
                files_created=json.dumps(files) if files else None,
                summary=summary,
                error=error
            )
        except Exception as e:
            self.logger.warning(f"Failed to update task history: {e}")
    
    def _extract_summary(self, response: str) -> str:
        """レスポンスから要約を抽出"""
        if not response:
            return "No response"
        
        # 最初の数行を要約として使用
        lines = response.strip().split('\n')
        summary_lines = []
        
        for line in lines[:5]:
            if line.strip():
                summary_lines.append(line.strip())
        
        return ' '.join(summary_lines)[:200]
    
    def _send_error_result(self, task_id: str, error: str):
        """エラー結果を送信"""
        error_message = {
            'task_id': task_id,
            'status': 'error',
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        
        self.send_result(error_message)


# 実行
    def cleanup(self):
        """Cleanup resources including RAG integration"""
        if self.rag_integration:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.rag_integration.cleanup())
                loop.close()
                self.logger.info(f"{EMOJI['info']} RAG Grimoire Integration cleaned up")
            except Exception as e:
                self.logger.error(f"{EMOJI['error']} Error during RAG cleanup: {e}")
        
        # Additional cleanup logic can be added here
        pass

    def stop(self):
        """TODO: stopメソッドを実装してください"""
        pass

    def initialize(self) -> None:
        """ワーカーの初期化処理"""
        # TODO: 初期化ロジックを実装してください
        self.logger.info(f"{self.__class__.__name__} initialized")
        pass

    def handle_error(self, error: Exception, context: dict = None, severity=None):
        """エラー処理メソッド"""
        if context is None:
            context = {}
        
        # エラー情報をログに記録
        self.logger.error(f"Error in {context.get('operation', 'unknown')}: {str(error)}")
        
        # Slack通知を送信（エラー発生時でも処理を続行）
        try:
            self.slack_notifier.send_error(
                f"Enhanced TaskWorker Error",
                error=str(error),
                context=context
            )
        except Exception as notification_error:
            self.logger.warning(f"Failed to send Slack notification: {notification_error}")
        
        # 重要度に応じた処理
        if severity and hasattr(severity, 'value'):
            if severity.value >= 3:  # HIGH以上
                self.logger.critical(f"High severity error: {str(error)}")
        
        return False

    def get_status(self):
        """TODO: get_statusメソッドを実装してください"""
        pass

    def validate_config(self):
        """TODO: validate_configメソッドを実装してください"""
        pass

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced TaskWorker with Prompt Templates')
    parser.add_argument('--worker-id', help='Worker ID')
    parser.add_argument('--test', action='store_true', help='Test mode')
    
    args = parser.parse_args()
    
    if args.test:
        # テストモード
        print(f"{EMOJI['info']} Running in test mode...")
        worker = EnhancedTaskWorker(worker_id='test-worker')
        
        # 利用可能なテンプレート表示
        print("\nAvailable templates:")
        for template in worker.list_available_templates():
            print(f"  - {template['template_name']} v{template['version']}: {template['description']}")
        
        # テストプロンプト生成
        test_prompt = worker.generate_prompt(
            template_name='code_generation',
            variables={
                'task_id': 'test_001',
                'task_type': 'code',
                'user_prompt': 'Create a Python web scraper',
                'language': 'Python'
            },
            include_rag=False
        )
        
        print(f"\nGenerated test prompt:\n{test_prompt[:300]}...")
        print(f"\n{EMOJI['success']} Test completed successfully")
    else:
        # 本番モード
        worker = EnhancedTaskWorker(worker_id=args.worker_id)
        print(f"{EMOJI['start']} Enhanced TaskWorker starting with prompt template support...")
        print(f"{EMOJI['info']} Worker ID: {worker.worker_id}")
        print(f"{EMOJI['info']} Input queue: {worker.input_queue}")
        print(f"{EMOJI['info']} Output queue: {worker.output_queue}")
        
        try:
            worker.start()
        except KeyboardInterrupt:
            print(f"\n{EMOJI['warning']} Worker stopped by user")
        except Exception as e:
            print(f"{EMOJI['error']} Worker error: {str(e)}")
            raise
