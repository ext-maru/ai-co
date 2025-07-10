#!/usr/bin/env python3
"""
Todo Worker - Elders Guild Task Management Specialist
ToDoワーカー - エルダー評議会のタスク管理専門家

This worker serves as the task management specialist within the Elder Tree hierarchy,
reporting to the Task Sage and managing todo lists and task organization.
"""

import sys
from pathlib import Path
import json
import os
from datetime import datetime
import logging
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.base_worker_ja import BaseWorker, get_config
from core import msg
from libs.ai_growth_todo_manager import AIGrowthTodoManager

# Elder Tree imports
try:
    from libs.four_sages_integration import FourSagesIntegration
    from libs.elder_council_summoner import ElderCouncilSummoner
    from libs.elder_tree_hierarchy import (
        get_elder_tree, ElderMessage, ElderRank, SageType
    )
    ELDER_SYSTEM_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Elder system not available: {e}")
    ELDER_SYSTEM_AVAILABLE = False
    FourSagesIntegration = None
    ElderCouncilSummoner = None

class TodoWorker(BaseWorker):
    """Todo Worker - Task management specialist of the Elder Tree hierarchy"""
    
    def __init__(self):
        super().__init__(worker_type='todo')
        self.manager = AIGrowthTodoManager()
        self.config = get_config()
        self.created_at = datetime.now()
        self.todos_processed = 0
        self.todos_created = 0
        self.tasks_completed = 0
        
        # Initialize Elder systems
        self.elder_systems_initialized = False
        self._initialize_elder_systems()
        
        self.logger.info(f"TodoWorker initialized as Elder Tree task management specialist (pid: {os.getpid()})")
        
    def _initialize_elder_systems(self):
        """Initialize Elder Tree hierarchy systems with error handling"""
        if not ELDER_SYSTEM_AVAILABLE:
            self.logger.warning("Elder systems not available, running in standalone mode")
            self.four_sages = None
            self.council_summoner = None
            self.elder_tree = None
            return
            
        try:
            # Initialize Four Sages Integration
            self.four_sages = FourSagesIntegration()
            self.logger.info("Four Sages Integration initialized successfully")
            
            # Initialize Elder Council Summoner
            self.council_summoner = ElderCouncilSummoner()
            self.logger.info("Elder Council Summoner initialized successfully")
            
            # Get Elder Tree reference
            self.elder_tree = get_elder_tree()
            self.logger.info("Elder Tree hierarchy connected")
            
            self.elder_systems_initialized = True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Elder systems: {e}")
            self.four_sages = None
            self.council_summoner = None
            self.elder_tree = None
            self.elder_systems_initialized = False
    
    def process_message(self, ch, method, properties, body):
        """ToDoリスト処理メッセージを処理 with Elder Tree integration"""
        task_id = body.get('task_id')
        
        try:
            action = body.get('action')
            
            # Report action start to Task Sage
            if self.elder_systems_initialized:
                self._report_action_start_to_task_sage(action, body)
            
            if action == 'process':
                # ToDoリストを処理
                todo_name = body.get('todo_name')
                self.logger.info(f"Processing todo list: {todo_name}")
                self.todos_processed += 1
                
                result = self.manager.process_todo_with_learning(todo_name)
                
                # Track completed tasks
                if result and isinstance(result, dict):
                    self.tasks_completed += result.get('completed_count', 0)
                
                # Report success to Task Sage
                if self.elder_systems_initialized:
                    self._report_processing_success_to_task_sage(todo_name, result)
                
                # 完了通知
                self._send_to_results({
                    'task_id': task_id,
                    'status': 'completed',
                    'message': f"ToDoリスト '{todo_name}' の処理が完了しました",
                    'details': result
                })
                
            elif action == 'create_daily':
                # 日次ToDoリストを作成
                self.todos_created += 1
                todo = self.manager.create_daily_todo()
                
                # 自動的に処理開始
                process_result = self.manager.process_todo_with_learning("daily_self_improvement")
                
                # Report daily todo creation to Task Sage
                if self.elder_systems_initialized:
                    self._report_daily_todo_creation_to_task_sage(todo, process_result)
                
                self._send_to_results({
                    'task_id': task_id,
                    'status': 'completed',
                    'message': f"日次ToDoリストを作成・実行しました"
                })
                
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            self.logger.error(f"Error processing todo: {str(e)}")
            
            # Report error to Incident Sage
            if self.elder_systems_initialized:
                self._report_error_to_incident_sage(action, e)
            
            self.handle_error(e, "process_todo")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def _send_to_results(self, result_data):
        """結果をResultWorkerに送信"""
        try:
            self.send_to_queue('ai_results', result_data)
        except Exception as e:
            self.logger.warning(f"Failed to send to results: {e}")


    def _report_action_start_to_task_sage(self, action: str, body: Dict[str, Any]):
        """Report action start to Task Sage"""
        if not self.four_sages:
            return
            
        try:
            report = {
                'type': 'todo_action_start',
                'worker': 'todo_worker',
                'action': action,
                'task_id': body.get('task_id'),
                'timestamp': datetime.now().isoformat()
            }
            
            self.four_sages.report_to_task_sage(report)
            
        except Exception as e:
            self.logger.error(f"Failed to report action start to Task Sage: {e}")
    
    def _report_processing_success_to_task_sage(self, todo_name: str, result: Dict[str, Any]):
        """Report todo processing success to Task Sage"""
        if not self.four_sages:
            return
            
        try:
            report = {
                'type': 'todo_processing_success',
                'worker': 'todo_worker',
                'todo_name': todo_name,
                'completed_count': result.get('completed_count', 0) if isinstance(result, dict) else 0,
                'total_tasks': result.get('total_tasks', 0) if isinstance(result, dict) else 0,
                'timestamp': datetime.now().isoformat()
            }
            
            self.four_sages.report_to_task_sage(report)
            
        except Exception as e:
            self.logger.error(f"Failed to report processing success to Task Sage: {e}")
    
    def _report_daily_todo_creation_to_task_sage(self, todo: Any, process_result: Any):
        """Report daily todo creation to Task Sage"""
        if not self.four_sages:
            return
            
        try:
            report = {
                'type': 'daily_todo_created',
                'worker': 'todo_worker',
                'todo_details': str(todo)[:500],  # First 500 chars
                'process_result': str(process_result)[:500] if process_result else None,
                'timestamp': datetime.now().isoformat()
            }
            
            self.four_sages.report_to_task_sage(report)
            
        except Exception as e:
            self.logger.error(f"Failed to report daily todo creation to Task Sage: {e}")
    
    def _report_error_to_incident_sage(self, action: str, error: Exception):
        """Report error to Incident Sage"""
        if not self.four_sages:
            return
            
        try:
            incident_data = {
                'type': 'todo_processing_error',
                'worker': 'todo_worker',
                'action': action,
                'error': str(error),
                'error_type': type(error).__name__,
                'timestamp': datetime.now().isoformat()
            }
            
            self.four_sages.consult_incident_sage(incident_data)
            
        except Exception as e:
            self.logger.error(f"Failed to report error to Incident Sage: {e}")
    
    def get_elder_todo_status(self) -> Dict[str, Any]:
        """Get comprehensive Elder todo management status"""
        status = {
            'worker_type': 'todo_worker',
            'elder_role': 'Task Management Specialist',
            'reporting_to': 'Task Sage',
            'elder_systems': {
                'initialized': self.elder_systems_initialized,
                'four_sages_active': self.four_sages is not None,
                'council_summoner_active': self.council_summoner is not None,
                'elder_tree_connected': self.elder_tree is not None
            },
            'todo_stats': {
                'todos_processed': self.todos_processed,
                'todos_created': self.todos_created,
                'tasks_completed': self.tasks_completed,
                'completion_rate': self.tasks_completed / max(1, self.todos_processed),
                'has_manager': self.manager is not None
            },
            'uptime': (datetime.now() - self.created_at).total_seconds(),
            'status': 'healthy' if self.elder_systems_initialized else 'degraded'
        }
        
        return status
    
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

if __name__ == "__main__":
    import os
    worker = TodoWorker()
    worker.start()
