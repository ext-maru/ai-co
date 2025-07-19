#!/usr/bin/env python3
"""
ワーカー追加
"""
import sys
import argparse
import json
import uuid
from pathlib import Path
from datetime import datetime
sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult

class AIWorkerAddCommand(BaseCommand):
    """ワーカー追加"""
    
    def __init__(self):
        super().__init__(
            name="ai-worker-add",
            description="ワーカー追加",
            version="1.0.0"
        )
    
    def add_arguments(self, parser: argparse.ArgumentParser):
        """引数定義"""
        parser.add_argument(
            '--worker-type', '-t',
            choices=['elder_servant', 'task_worker', 'rag_worker', 'pm_worker', 'dwarf', 'wizard', 'knight'],
            required=True,
            help='ワーカータイプ'
        )
        parser.add_argument(
            '--worker-name', '-n',
            type=str,
            required=True,
            help='ワーカー名'
        )
        parser.add_argument(
            '--config-file', '-c',
            type=str,
            help='ワーカー設定ファイル'
        )
        parser.add_argument(
            '--auto-start',
            action='store_true',
            help='作成後に自動開始'
        )
        parser.add_argument(
            '--worker-role', '-r',
            type=str,
            help='ワーカーの役割'
        )
        parser.add_argument(
            '--max-tasks',
            type=int,
            default=10,
            help='最大タスク数'
        )
        parser.add_argument(
            '--priority',
            choices=['low', 'medium', 'high', 'critical'],
            default='medium',
            help='ワーカー優先度'
        )
    
    def execute(self, args) -> CommandResult:
        """実行"""
        try:
            # ワーカーID生成
            worker_id = f"{args.worker_type}_{args.worker_name}_{uuid.uuid4().hex[:8]}"
            
            # ワーカー設定作成
            worker_config = self._create_worker_config(args, worker_id)
            
            # ワーカーレジストリに登録
            registry_result = self._register_worker(worker_config)
            if not registry_result['success']:
                return CommandResult(
                    success=False,
                    message=f"ワーカー登録失敗: {registry_result['error']}"
                )
            
            # ワーカーファイル作成
            worker_file_result = self._create_worker_file(args, worker_id, worker_config)
            if not worker_file_result['success']:
                return CommandResult(
                    success=False,
                    message=f"ワーカーファイル作成失敗: {worker_file_result['error']}"
                )
            
            # 自動開始
            if args.auto_start:
                start_result = self._start_worker(worker_id)
                if start_result['success']:
                    status_msg = " (自動開始済み)"
                else:
                    status_msg = f" (開始失敗: {start_result['error']})"
            else:
                status_msg = ""
            
            return CommandResult(
                success=True,
                message=f"ワーカー '{args.worker_name}' (ID: {worker_id}) を追加しました{status_msg}\nファイル: {worker_file_result['file_path']}"
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"ワーカー追加エラー: {str(e)}"
            )
    
    def _create_worker_config(self, args, worker_id: str) -> dict:
        """ワーカー設定作成"""
        config = {
            'worker_id': worker_id,
            'worker_name': args.worker_name,
            'worker_type': args.worker_type,
            'role': args.worker_role or f"Auto-generated {args.worker_type}",
            'max_tasks': args.max_tasks,
            'priority': args.priority,
            'created_at': datetime.now().isoformat(),
            'status': 'created',
            'auto_restart': True,
            'config': {
                'rabbitmq_enabled': True,
                'logging_enabled': True,
                'performance_monitoring': True
            }
        }
        
        # タイプ別設定
        if args.worker_type == 'elder_servant':
            config['elder_integration'] = True
            config['capabilities'] = ['code_generation', 'testing', 'quality_check']
        elif args.worker_type == 'rag_worker':
            config['vector_search_enabled'] = True
            config['embedding_model'] = 'openai'
        elif args.worker_type == 'task_worker':
            config['task_scheduling'] = True
            config['parallel_execution'] = True
        
        # 設定ファイルから追加設定読み込み
        if args.config_file:
            try:
                with open(args.config_file, 'r', encoding='utf-8') as f:
                    custom_config = json.load(f)
                    config.update(custom_config)
            except Exception as e:
                print(f"警告: 設定ファイル読み込み失敗: {e}")
        
        return config
    
    def _register_worker(self, worker_config: dict) -> dict:
        """ワーカーレジストリに登録"""
        try:
            # ワーカーレジストリファイルに保存
            registry_path = Path('/home/aicompany/ai_co/data/worker_registry.json')
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 既存レジストリ読み込み
            if registry_path.exists():
                with open(registry_path, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
            else:
                registry = {'workers': []}
            
            # 同名ワーカーチェック
            for worker in registry['workers']:
                if worker['worker_name'] == worker_config['worker_name']:
                    return {
                        'success': False,
                        'error': f"同名のワーカー '{worker_config['worker_name']}' が既に存在します"
                    }
            
            # ワーカー追加
            registry['workers'].append(worker_config)
            
            # レジストリ保存
            with open(registry_path, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _create_worker_file(self, args, worker_id: str, worker_config: dict) -> dict:
        """ワーカーファイル作成"""
        try:
            # ワーカーファイルパス
            workers_dir = Path(f'/home/aicompany/ai_co/workers/{args.worker_type}')
            workers_dir.mkdir(parents=True, exist_ok=True)
            worker_file = workers_dir / f"{args.worker_name}.py"
            
            # ワーカーコードテンプレート生成
            worker_code = self._generate_worker_code(args, worker_id, worker_config)
            
            # ファイル書き込み
            with open(worker_file, 'w', encoding='utf-8') as f:
                f.write(worker_code)
            
            return {
                'success': True,
                'file_path': str(worker_file)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _generate_worker_code(self, args, worker_id: str, worker_config: dict) -> str:
        """ワーカーコードテンプレート生成"""
        template = f'''#!/usr/bin/env python3
"""
{args.worker_name} Worker
Auto-generated by ai-worker-add command

Worker ID: {worker_id}
Worker Type: {args.worker_type}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import sys
import asyncio
import logging
from pathlib import Path

# Project root path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.base_worker import BaseWorker
from libs.elder_flow_servant_executor import ElderFlowServantExecutor

logger = logging.getLogger(__name__)

class {args.worker_name.replace('-', '_').title()}Worker(BaseWorker):
    """{args.worker_name} Worker"""
    
    def __init__(self):
        super().__init__(
            worker_id="{worker_id}",
            worker_name="{args.worker_name}",
            worker_type="{args.worker_type}",
            max_concurrent_tasks={args.max_tasks}
        )
        self.config = {json.dumps(worker_config, indent=8)}
    
    async def process_task(self, task_data):
        """タスク処理"""
        try:
            logger.info(f"Processing task: {{task_data.get('task_id', 'unknown')}}")
            
            # タイプ別処理
            if self.worker_type == "elder_servant":
                return await self._process_elder_servant_task(task_data)
            elif self.worker_type == "rag_worker":
                return await self._process_rag_task(task_data)
            elif self.worker_type == "task_worker":
                return await self._process_task_worker_task(task_data)
            else:
                return await self._process_generic_task(task_data)
            
        except Exception as e:
            logger.error(f"Task processing error: {{e}}")
            return {{
                'success': False,
                'error': str(e),
                'task_id': task_data.get('task_id')
            }}
    
    async def _process_elder_servant_task(self, task_data):
        """エルダーサーバントタスク処理"""
        # Elder Flow Servant Executorを使用
        executor = ElderFlowServantExecutor()
        return await executor.execute_task(task_data)
    
    async def _process_rag_task(self, task_data):
        """RAGタスク処理"""
        # RAG処理ロジックを実装
        return {{
            'success': True,
            'result': 'RAG task processed',
            'task_id': task_data.get('task_id')
        }}
    
    async def _process_task_worker_task(self, task_data):
        """タスクワーカータスク処理"""
        # タスクワーカー処理ロジックを実装
        return {{
            'success': True,
            'result': 'Task worker task processed',
            'task_id': task_data.get('task_id')
        }}
    
    async def _process_generic_task(self, task_data):
        """汎用タスク処理"""
        # 汎用タスク処理ロジック
        return {{
            'success': True,
            'result': 'Generic task processed',
            'task_id': task_data.get('task_id')
        }}
    
    def get_worker_info(self):
        """ワーカー情報取得"""
        return {{
            'worker_id': self.worker_id,
            'worker_name': self.worker_name,
            'worker_type': self.worker_type,
            'status': self.status,
            'max_tasks': self.max_concurrent_tasks,
            'current_tasks': len(self.current_tasks),
            'config': self.config
        }}

def main():
    """メイン関数"""
    worker = {args.worker_name.replace('-', '_').title()}Worker()
    asyncio.run(worker.run())

if __name__ == "__main__":
    main()
'''
        return template
    
    def _start_worker(self, worker_id: str) -> dict:
        """ワーカー開始"""
        try:
            # ワーカーマネージャーを使用して開始
            from libs.worker_manager import WorkerManager
            manager = WorkerManager()
            result = manager.start_worker(worker_id)
            return {'success': result}
        except ImportError:
            return {
                'success': False,
                'error': 'ワーカーマネージャーが利用できません'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

def main():
    command = AIWorkerAddCommand()
    sys.exit(command.run())

if __name__ == "__main__":
    main()
