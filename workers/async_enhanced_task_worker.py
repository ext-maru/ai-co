#!/usr/bin/env python3
"""
非同期対応Enhanced Task Worker
セキュリティ強化とパフォーマンス改善版
"""

import json
import asyncio
import os
import shlex
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import aiofiles
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
# プロジェクトルートをPythonパスに追加
import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.async_base_worker_v2 import AsyncBaseWorkerV2
from core.lightweight_logger import get_logger
from core.security_module import SecureTaskExecutor, InputSanitizer
from core.rate_limiter import RateLimiter, CacheManager, CachedFunction
from libs.rag_grimoire_integration import RagGrimoireIntegration, RagGrimoireConfig
from libs.slack_notifier import SlackNotifier
from libs.task_history_db import TaskHistoryDB

class FileChangeHandler(FileSystemEventHandler):
    """ファイル変更検出ハンドラ"""
    
    def __init__(self):
        self.created_files = []
        self.modified_files = []
    
    def on_created(self, event):
        if not event.is_directory:
            self.created_files.append(event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            self.modified_files.append(event.src_path)

class AsyncEnhancedTaskWorker(AsyncBaseWorkerV2):
    """
    非同期対応の強化版Task Worker
    
    Features:
    - セキュアなコマンド実行
    - 非同期Claude API呼び出し
    - 効率的なファイル監視
    - レート制限対応
    - キャッシング機能
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(
            worker_name="async_enhanced_task_worker",
            config=config,
            input_queues=['ai_tasks'],
            output_queues=['ai_pm']
        )
        
        self.logger = get_logger("async_enhanced_task_worker")
        
        # セキュリティモジュール
        self.secure_executor = SecureTaskExecutor(config)
        self.input_sanitizer = InputSanitizer()
        
        # レート制限（Claude API用）
        self.rate_limiter = RateLimiter(
            rate=config.get('claude_rate_limit', 10),
            period=60
        )
        
        # キャッシュマネージャ
        self.cache_manager = CacheManager(
            default_ttl=config.get('cache_ttl', 3600)
        )
        
        # RAG Grimoire Integration
        self.rag_config = RagGrimoireConfig(
            database_url=config.get('grimoire_database_url', 'postgresql://localhost/grimoire'),
            search_threshold=config.get('rag_search_threshold', 0.7),
            max_search_results=config.get('rag_max_results', 10)
        )
        self.rag_integration = None
        
        # 通知
        self.slack_notifier = SlackNotifier()
        
        # タスク履歴DB
        self.task_history = TaskHistoryDB()
        
        # 出力ディレクトリ
        self.output_dir = Path(config.get('output_dir', '/home/aicompany/ai_co/output'))
        self.output_dir.mkdir(exist_ok=True)
        
        # テンプレート設定
        self.templates = self._load_templates()
        
        # Initialize RAG Grimoire Integration
        self._initialize_rag_integration_task = None
    
    def _load_templates(self) -> Dict[str, str]:
        """プロンプトテンプレートの読み込み"""
        templates = {}
        template_dir = PROJECT_ROOT / "templates" / "prompts"
        
        if template_dir.exists():
            for template_file in template_dir.glob("*.txt"):
                template_name = template_file.stem
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        templates[template_name] = f.read()
                except Exception as e:
                    self.logger.error(
                        "Failed to load template",
                        template=template_name,
                        error=str(e)
                    )
        
        return templates
    
    async def _initialize_rag_integration(self):
        """RAG Grimoire Integration を非同期初期化"""
        try:
            self.rag_integration = RagGrimoireIntegration(self.rag_config)
            await self.rag_integration.initialize()
            self.logger.info("RAG Grimoire Integration initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG Grimoire Integration: {e}")
            self.rag_integration = None
    
    async def start(self):
        """Start the async worker with RAG integration"""
        # Initialize RAG integration first
        await self._initialize_rag_integration()
        
        # Start the base worker
        await super().start()
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        メッセージ処理のメイン実装
        """
        task_id = message.get('task_id', 'unknown')
        start_time = datetime.utcnow()
        
        try:
            # 入力のサニタイズ
            sanitized_prompt = self.input_sanitizer.sanitize_json_input(
                message.get('prompt', {})
            )
            
            # テンプレート選択とプロンプト生成
            template_name = self._select_template(message)
            prompt = await self._generate_prompt(
                template_name,
                message,
                sanitized_prompt
            )
            
            # レート制限チェック
            await self.rate_limiter.wait_if_needed(f"claude_{task_id}")
            
            # Claudeへのタスク実行
            result = await self._execute_claude(prompt, task_id)
            
            # ファイル変更の検出
            created_files = await self._detect_file_changes(task_id)
            
            # 結果の整形
            output_data = {
                'task_id': task_id,
                'status': 'completed',
                'result': result,
                'created_files': created_files,
                'duration': (datetime.utcnow() - start_time).total_seconds()
            }
            
            # 成功処理
            await self._handle_success(message, output_data)
            
            return output_data
            
        except Exception as e:
            # エラー処理
            error_data = {
                'task_id': task_id,
                'status': 'failed',
                'error': str(e),
                'error_type': type(e).__name__,
                'duration': (datetime.utcnow() - start_time).total_seconds()
            }
            
            await self._handle_failure(message, error_data)
            
            raise
    
    def _select_template(self, message: Dict[str, Any]) -> str:
        """テンプレート選択ロジック"""
        task_type = message.get('task_type', 'general')
        prompt = message.get('prompt', '').lower()
        
        # タスクタイプベースの選択
        if task_type in self.templates:
            return task_type
        
        # キーワードベースの選択
        keyword_mapping = {
            'code': ['コード', 'プログラム', '実装', 'implement'],
            'test': ['テスト', 'test', 'spec'],
            'debug': ['デバッグ', 'エラー', 'error', 'fix'],
            'refactor': ['リファクタリング', 'refactor', '改善'],
            'documentation': ['ドキュメント', 'doc', '説明']
        }
        
        for template_name, keywords in keyword_mapping.items():
            if any(keyword in prompt for keyword in keywords):
                if template_name in self.templates:
                    return template_name
        
        return 'general'
    
    @CachedFunction(cache_manager=None, ttl=300)  # 5分間キャッシュ
    async def _generate_prompt(
        self,
        template_name: str,
        message: Dict[str, Any],
        sanitized_prompt: Any
    ) -> str:
        """プロンプト生成（RAG統合）"""
        # RAG検索 using unified grimoire integration
        rag_context = ""
        if self.config.get('enable_rag', True) and self.rag_integration:
            try:
                search_query = str(sanitized_prompt)[:200]
                rag_results = await self.rag_integration.search_unified(
                    query=search_query,
                    limit=3,
                    threshold=self.rag_config.search_threshold
                )
                
                if rag_results:
                    rag_context = "\n\n## 関連知識:\n"
                    for result in rag_results:
                        rag_context += f"- {result['content'][:200]}...\n"
                        rag_context += f"  Source: {result['source']} (Score: {result['similarity_score']:.2f})\n"
            except Exception as e:
                self.logger.warning(
                    "RAG search failed",
                    error=str(e)
                )
        
        # テンプレート適用
        template = self.templates.get(template_name, "{prompt}")
        
        # 変数置換
        variables = {
            'task_id': message.get('task_id'),
            'prompt': sanitized_prompt,
            'rag_context': rag_context,
            'timestamp': datetime.utcnow().isoformat(),
            'priority': message.get('priority', 'normal')
        }
        
        try:
            final_prompt = template.format(**variables)
        except KeyError as e:
            self.logger.warning(
                "Template variable missing",
                template=template_name,
                missing_var=str(e)
            )
            final_prompt = str(sanitized_prompt)
        
        return final_prompt
    
    async def _execute_claude(self, prompt: str, task_id: str) -> Dict[str, Any]:
        """Claude APIの非同期実行"""
        # コマンド構築
        command = [
            "claude-cli",
            "execute",
            "--model", self.config.get('claude_model', 'claude-3-5-sonnet-20241022'),
            "--max-tokens", str(self.config.get('max_tokens', 4096)),
            "--temperature", str(self.config.get('temperature', 0.7))
        ]
        
        # 許可されたツールの追加
        allowed_tools = self.config.get('allowed_tools', ['Edit', 'Write', 'Read'])
        for tool in allowed_tools:
            command.extend(["--tool", tool])
        
        # プロンプトをファイルに保存（大きなプロンプト対応）
        prompt_file = self.output_dir / f"{task_id}_prompt.txt"
        async with aiofiles.open(prompt_file, 'w', encoding='utf-8') as f:
            await f.write(prompt)
        
        command.extend(["--prompt-file", str(prompt_file)])
        
        try:
            # セキュアな実行
            result = await self.secure_executor.execute_secure(
                " ".join(shlex.quote(arg) for arg in command),
                timeout=self.config.get('claude_timeout', 300)
            )
            
            # 結果のパース
            return {
                'stdout': result['stdout'],
                'stderr': result['stderr'],
                'return_code': result['return_code'],
                'output_files': result.get('output_files', [])
            }
            
        finally:
            # プロンプトファイルのクリーンアップ
            try:
                prompt_file.unlink()
            except:
                pass
    
    async def _detect_file_changes(self, task_id: str) -> List[str]:
        """ファイル変更の効率的な検出"""
        # watchdogを使用した監視
        handler = FileChangeHandler()
        observer = Observer()
        
        # 監視対象ディレクトリ
        watch_dirs = [
            self.output_dir,
            Path.cwd(),  # カレントディレクトリ
        ]
        
        for watch_dir in watch_dirs:
            if watch_dir.exists():
                observer.schedule(handler, str(watch_dir), recursive=True)
        
        observer.start()
        
        # 5秒間監視
        await asyncio.sleep(5)
        
        observer.stop()
        observer.join()
        
        # 作成されたファイルを返す
        return handler.created_files
    
    async def _handle_success(self, message: Dict[str, Any], result: Dict[str, Any]):
        """成功時の処理"""
        # タスク履歴に記録
        await self.task_history.add_task(
            task_id=result['task_id'],
            status='completed',
            prompt=message.get('prompt'),
            result=result
        )
        
        # Slack通知
        if self.config.get('slack_notifications', True):
            await self.slack_notifier.send_task_completion(
                task_id=result['task_id'],
                duration=result['duration'],
                files_created=result.get('created_files', [])
            )
        
        # キャッシュ更新
        await self.cache_manager.set(
            f"task_result:{result['task_id']}",
            result,
            ttl=86400  # 24時間
        )
        
        # Store knowledge in RAG integration if available
        if self.rag_integration and result.get('created_files'):
            try:
                await self._store_task_knowledge(result)
            except Exception as e:
                self.logger.warning(f"Failed to store task knowledge: {e}")
    
    async def _handle_failure(self, message: Dict[str, Any], error_data: Dict[str, Any]):
        """失敗時の処理"""
        # タスク履歴に記録
        await self.task_history.add_task(
            task_id=error_data['task_id'],
            status='failed',
            prompt=message.get('prompt'),
            error=error_data
        )
        
        # エラー通知
        if self.config.get('slack_notifications', True):
            await self.slack_notifier.send_error_notification(
                task_id=error_data['task_id'],
                error=error_data['error'],
                error_type=error_data['error_type']
            )
    
    async def _store_task_knowledge(self, result: Dict[str, Any]):
        """Store successful task results as knowledge in RAG system"""
        if not self.rag_integration:
            return
        
        try:
            task_id = result['task_id']
            created_files = result.get('created_files', [])
            
            # Create knowledge entry for the task
            knowledge_content = f"Task {task_id} completed successfully.\n"
            knowledge_content += f"Files created: {', '.join(created_files)}\n"
            knowledge_content += f"Duration: {result.get('duration', 0):.2f} seconds\n"
            
            if result.get('result', {}).get('stdout'):
                knowledge_content += f"Output: {result['result']['stdout'][:500]}...\n"
            
            # Store in grimoire system
            await self.rag_integration.add_knowledge_unified(
                spell_name=f"task_{task_id}_completion",
                content=knowledge_content,
                metadata={
                    'task_id': task_id,
                    'completion_time': result.get('duration', 0),
                    'files_created': created_files,
                    'worker_type': 'async_enhanced_task_worker',
                    'success': True
                },
                category='task_completion',
                tags=['task', 'completion', 'automated']
            )
            
            self.logger.info(f"Task knowledge stored for task {task_id}")
            
        except Exception as e:
            self.logger.error(f"Error storing task knowledge: {e}")
    
    async def cleanup(self):
        """Cleanup resources including RAG integration"""
        if self.rag_integration:
            try:
                await self.rag_integration.cleanup()
                self.logger.info("RAG Grimoire Integration cleaned up")
            except Exception as e:
                self.logger.error(f"Error during RAG cleanup: {e}")
        
        # Call parent cleanup if available
        if hasattr(super(), 'cleanup'):
            await super().cleanup()


# 実行用のメイン関数
async def main():
    """ワーカーのエントリーポイント"""
    import yaml
    
    # 設定読み込み
    config_path = PROJECT_ROOT / "config" / "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # ワーカー起動
    worker = AsyncEnhancedTaskWorker(config)
    await worker.start()

if __name__ == "__main__":
    asyncio.run(main())