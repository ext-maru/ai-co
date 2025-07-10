#!/usr/bin/env python3
"""
Claude CLI Task Tracker Integration
Claude CLIからTask Trackerを利用するためのライブラリ
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.task_tracker_client import TaskTrackerClient
from core import get_config, EMOJI
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List
import subprocess

logger = logging.getLogger(__name__)

class ClaudeTaskTracker:
    """タスク賢者 (Task Oracle) - 4賢者システム統合
    
    Elders Guildの4賢者システムの一翼を担う、プロジェクト進捗管理専門の賢者。
    最適な実行順序の導出、計画立案、進捗追跡、優先順位判断を行う。
    """
    
    def __init__(self):
        self.client = TaskTrackerClient()
        self.config = get_config()
        self.current_task_id = None
        self.task_start_time = None
        
        # 4賢者システム統合
        self.sage_type = "Task Oracle"
        self.wisdom_level = "project_management"
        self.collaboration_mode = True
        
        logger.info(f"🔮 {self.sage_type} 初期化完了 - 4賢者システム連携モード")
        
    def start_development_task(self, prompt: str, task_type: str = "development") -> str:
        """開発タスクを開始"""
        task_id = f"claude_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # タスクの優先度を判定
        priority = self._determine_priority(prompt, task_type)
        
        # Task Trackerに登録
        self.client.create_task(
            task_id=task_id,
            title=f"[Claude CLI] {task_type}: {prompt[:50]}...",
            description=f"Claude CLIによる自動開発タスク\n\nプロンプト:\n{prompt}",
            priority=priority,
            assignee="claude_cli"
        )
        
        # 現在のタスクとして記録
        self.current_task_id = task_id
        self.task_start_time = datetime.now()
        
        # ステータスを進行中に更新
        self.update_status("in_progress", "Claude CLIが作業を開始しました")
        
        logger.info(f"{EMOJI['robot']} 開発タスク開始: {task_id}")
        return task_id
    
    def update_progress(self, message: str, files_affected: List[str] = None):
        """作業進捗を更新"""
        if not self.current_task_id:
            return
        
        notes = f"進捗: {message}"
        if files_affected:
            notes += f"\n影響ファイル: {', '.join(files_affected)}"
        
        # タスクログとして記録（ステータス変更なし）
        task = self.client.get_task_by_original_id(self.current_task_id)
        if task:
            self.client.update_task_status(
                task['id'], 
                task['status'],  # 現在のステータスを維持
                notes
            )
    
    def complete_task(self, success: bool = True, 
                     files_created: List[str] = None, 
                     files_modified: List[str] = None,
                     error_message: str = None):
        """タスクを完了"""
        if not self.current_task_id:
            return
        
        duration = (datetime.now() - self.task_start_time).total_seconds() if self.task_start_time else 0
        
        if success:
            status = "completed"
            notes = f"作業完了 (所要時間: {duration:.1f}秒)"
            
            if files_created:
                notes += f"\n作成ファイル: {len(files_created)}個"
                for f in files_created[:5]:
                    notes += f"\n  - {f}"
                    
            if files_modified:
                notes += f"\n修正ファイル: {len(files_modified)}個"
                for f in files_modified[:5]:
                    notes += f"\n  - {f}"
        else:
            status = "cancelled"
            notes = f"エラーにより中断 (所要時間: {duration:.1f}秒)"
            if error_message:
                notes += f"\nエラー: {error_message}"
        
        self.update_status(status, notes)
        
        # 現在のタスクをクリア
        self.current_task_id = None
        self.task_start_time = None
    
    def update_status(self, status: str, notes: str = ""):
        """タスクステータスを更新"""
        if not self.current_task_id:
            return
            
        task = self.client.get_task_by_original_id(self.current_task_id)
        if task:
            self.client.update_task_status(task['id'], status, notes)
    
    def _determine_priority(self, prompt: str, task_type: str) -> int:
        """プロンプトとタスクタイプから優先度を決定"""
        priority = 3  # デフォルト
        
        # キーワードによる優先度判定
        high_priority_keywords = ['urgent', '緊急', 'critical', 'fix', 'bug', 'error']
        low_priority_keywords = ['test', 'テスト', 'sample', 'example', 'demo']
        
        prompt_lower = prompt.lower()
        
        if any(keyword in prompt_lower for keyword in high_priority_keywords):
            priority = 5
        elif task_type in ['bugfix', 'hotfix', 'error']:
            priority = 4
        elif any(keyword in prompt_lower for keyword in low_priority_keywords):
            priority = 2
        
        return priority
    
    def create_subtask(self, parent_task_id: str, subtask_name: str, 
                      description: str = "") -> str:
        """サブタスクを作成"""
        subtask_id = f"{parent_task_id}_sub_{datetime.now().strftime('%H%M%S')}"
        
        self.client.create_task(
            task_id=subtask_id,
            title=f"[Sub] {subtask_name}",
            description=f"親タスク: {parent_task_id}\n\n{description}",
            priority=3,
            assignee="claude_cli"
        )
        
        return subtask_id
    
    def log_file_operation(self, operation: str, file_path: str, 
                          success: bool = True, details: str = ""):
        """ファイル操作をログ"""
        if not self.current_task_id:
            return
        
        operation_emoji = {
            'create': '📝',
            'modify': '✏️',
            'delete': '🗑️',
            'read': '👁️'
        }.get(operation, '📄')
        
        status_text = "成功" if success else "失敗"
        message = f"{operation_emoji} ファイル{operation}: {file_path} ({status_text})"
        
        if details:
            message += f"\n詳細: {details}"
        
        self.update_progress(message)
    
    def get_current_task_info(self) -> Optional[Dict]:
        """現在のタスク情報を取得"""
        if not self.current_task_id:
            return None
            
        task = self.client.get_task_by_original_id(self.current_task_id)
        if task:
            task['elapsed_time'] = (datetime.now() - self.task_start_time).total_seconds() if self.task_start_time else 0
        return task


# Claude CLIからの利用を簡単にするヘルパー関数
_tracker_instance = None

def get_tracker() -> ClaudeTaskTracker:
    """シングルトンのTrackerインスタンスを取得"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = ClaudeTaskTracker()
    return _tracker_instance

def track_claude_task(prompt: str, task_type: str = "development"):
    """デコレータ: Claude CLIのタスクをトラッキング"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracker = get_tracker()
            task_id = tracker.start_development_task(prompt, task_type)
            
            try:
                result = func(*args, **kwargs)
                # 成功時の処理
                tracker.complete_task(success=True)
                return result
            except Exception as e:
                # エラー時の処理
                tracker.complete_task(success=False, error_message=str(e))
                raise
        
        return wrapper
    return decorator
