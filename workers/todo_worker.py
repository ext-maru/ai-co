#!/usr/bin/env python3
"""
AI Todo Worker
ToDoリストを自律的に処理するワーカー
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.base_worker_ja import BaseWorker, get_config
from core import msg
from libs.ai_growth_todo_manager import AIGrowthTodoManager
import json

class TodoWorker(BaseWorker):
    """ToDoリスト処理ワーカー"""
    
    def __init__(self):
        super().__init__(worker_type='todo')
        self.manager = AIGrowthTodoManager()
        self.config = get_config()
        self.logger.info(f"TodoWorker initialized (pid: {os.getpid()})")
    
    def process_message(self, ch, method, properties, body):
        """ToDoリスト処理メッセージを処理"""
        task_id = body.get('task_id')
        
        try:
            if body.get('action') == 'process':
                # ToDoリストを処理
                todo_name = body.get('todo_name')
                self.logger.info(f"Processing todo list: {todo_name}")
                
                result = self.manager.process_todo_with_learning(todo_name)
                
                # 完了通知
                self._send_to_results({
                    'task_id': task_id,
                    'status': 'completed',
                    'message': f"ToDoリスト '{todo_name}' の処理が完了しました",
                    'details': result
                })
                
            elif body.get('action') == 'create_daily':
                # 日次ToDoリストを作成
                todo = self.manager.create_daily_todo()
                
                # 自動的に処理開始
                self.manager.process_todo_with_learning("daily_self_improvement")
                
                self._send_to_results({
                    'task_id': task_id,
                    'status': 'completed',
                    'message': f"日次ToDoリストを作成・実行しました"
                })
                
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            self.logger.error(f"Error processing todo: {str(e)}")
            self.handle_error(e, "process_todo")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def _send_to_results(self, result_data):
        """結果をResultWorkerに送信"""
        try:
            self.send_to_queue('ai_results', result_data)
        except Exception as e:
            self.logger.warning(f"Failed to send to results: {e}")


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
