#!/usr/bin/env python3
"""
タスク詳細表示
"""
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime
sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult

class AITaskInfoCommand(BaseCommand):
    """タスク詳細表示"""
    
    def __init__(self):
        super().__init__(
            name="ai-task-info",
            description="タスク詳細表示",
            version="1.0.0"
        )
    
    def add_arguments(self, parser: argparse.ArgumentParser):
        """引数定義"""
        parser.add_argument(
            '--task-id', '-t',
            type=str,
            required=True,
            help='表示するタスクID'
        )
        parser.add_argument(
            '--format', '-f',
            choices=['text', 'json', 'table'],
            default='text',
            help='表示形式'
        )
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='詳細情報を表示'
        )
    
    def execute(self, args) -> CommandResult:
        """実行"""
        try:
            # タスクトラッカーを使用してタスク情報を取得
            from libs.claude_task_tracker import TaskTracker
            
            tracker = TaskTracker()
            
            # タスク情報取得
            task = tracker.get_task(args.task_id)
            if not task:
                return CommandResult(
                    success=False,
                    message=f"タスク '{args.task_id}' が見つかりません"
                )
            
            # フォーマットに応じた出力
            if args.format == 'json':
                return CommandResult(
                    success=True,
                    message=json.dumps(task, indent=2, ensure_ascii=False, default=str)
                )
            
            elif args.format == 'table':
                return self._format_table(task, args.verbose)
            
            else:  # text format
                return self._format_text(task, args.verbose)
            
        except ImportError:
            return CommandResult(
                success=False,
                message="タスクトラッカーが利用できません"
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"タスク情報取得エラー: {str(e)}"
            )
    
    def _format_text(self, task, verbose=False) -> CommandResult:
        """テキスト形式でタスク情報をフォーマット"""
        lines = []
        lines.append(f"タスクID: {task.get('task_id', 'N/A')}")
        lines.append(f"タイトル: {task.get('title', 'N/A')}")
        lines.append(f"ステータス: {task.get('status', 'N/A')}")
        lines.append(f"優先度: {task.get('priority', 'N/A')}")
        lines.append(f"作成日時: {task.get('created_at', 'N/A')}")
        lines.append(f"更新日時: {task.get('updated_at', 'N/A')}")
        
        if task.get('description'):
            lines.append(f"説明: {task['description']}")
        
        if verbose:
            if task.get('tags'):
                lines.append(f"タグ: {', '.join(task['tags'])}")
            if task.get('assigned_to'):
                lines.append(f"担当者: {task['assigned_to']}")
            if task.get('due_date'):
                lines.append(f"期限: {task['due_date']}")
            if task.get('completion_time'):
                lines.append(f"完了日時: {task['completion_time']}")
            if task.get('notes'):
                lines.append(f"ノート: {task['notes']}")
        
        return CommandResult(
            success=True,
            message='\n'.join(lines)
        )
    
    def _format_table(self, task, verbose=False) -> CommandResult:
        """テーブル形式でタスク情報をフォーマット"""
        lines = []
        lines.append("─" * 50)
        lines.append(f"|タスクID       | {task.get('task_id', 'N/A'):<30} |")
        lines.append(f"|タイトル       | {task.get('title', 'N/A'):<30} |")
        lines.append(f"|ステータス     | {task.get('status', 'N/A'):<30} |")
        lines.append(f"|優先度       | {task.get('priority', 'N/A'):<30} |")
        lines.append(f"|作成日時     | {task.get('created_at', 'N/A'):<30} |")
        lines.append(f"|更新日時     | {task.get('updated_at', 'N/A'):<30} |")
        
        if verbose:
            if task.get('assigned_to'):
                lines.append(f"|担当者       | {task['assigned_to']:<30} |")
            if task.get('due_date'):
                lines.append(f"|期限         | {task['due_date']:<30} |")
        
        lines.append("─" * 50)
        
        return CommandResult(
            success=True,
            message='\n'.join(lines)
        )

def main():
    command = AITaskInfoCommand()
    sys.exit(command.run())

if __name__ == "__main__":
    main()
