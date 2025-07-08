"""
Completion Report Tracker

完了報告を追跡・管理するコンポーネント
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ReportStatus(Enum):
    """報告ステータス"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """タスクタイプ"""
    IMPLEMENTATION = "implementation"
    BUG_FIX = "bug_fix"
    ANALYSIS = "analysis"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"


class CompletionReportTracker:
    """完了報告追跡システム"""
    
    def __init__(self, storage_dir: str = '/home/aicompany/ai_co/data/completion_reports'):
        """
        初期化
        
        Args:
            storage_dir: 報告を保存するディレクトリ
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        self.active_tasks = {}
        self.completed_reports = []
        
        # 既存の報告を読み込み
        self._load_existing_reports()
        
        logger.info(f"CompletionReportTracker initialized with directory: {storage_dir}")
    
    def _load_existing_reports(self):
        """既存の報告を読み込み"""
        try:
            # アクティブタスクファイル
            active_file = os.path.join(self.storage_dir, 'active_tasks.json')
            if os.path.exists(active_file):
                with open(active_file, 'r') as f:
                    self.active_tasks = json.load(f)
            
            # 完了報告の読み込み
            import glob
            report_files = glob.glob(os.path.join(self.storage_dir, 'report_*.json'))
            
            for report_file in sorted(report_files)[-100:]:  # 最新100件
                try:
                    with open(report_file, 'r') as f:
                        report = json.load(f)
                        self.completed_reports.append(report)
                except Exception as e:
                    logger.error(f"Failed to load report {report_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to load existing reports: {e}")
    
    def register_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        新しいタスクを登録
        
        Args:
            task_id: タスクID
            task_data: タスクデータ
            
        Returns:
            登録結果
        """
        try:
            # タスク情報を構築
            task_info = {
                'task_id': task_id,
                'type': task_data.get('type', TaskType.IMPLEMENTATION.value),
                'title': task_data.get('title', 'Untitled Task'),
                'description': task_data.get('description', ''),
                'requester': task_data.get('requester', 'Unknown'),
                'assignee': task_data.get('assignee', 'Incident Knights'),
                'priority': task_data.get('priority', 'MEDIUM'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'status': ReportStatus.PENDING.value,
                'expected_completion': task_data.get('expected_completion'),
                'requirements': task_data.get('requirements', {}),
                'metadata': task_data.get('metadata', {})
            }
            
            # アクティブタスクに追加
            self.active_tasks[task_id] = task_info
            
            # 保存
            self._save_active_tasks()
            
            logger.info(f"Task registered: {task_id} - {task_info['title']}")
            
            return {
                'success': True,
                'task_id': task_id,
                'message': 'Task registered successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to register task: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_task_status(self, task_id: str, status: str, 
                          update_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        タスクステータスを更新
        
        Args:
            task_id: タスクID
            status: 新しいステータス
            update_data: 追加の更新データ
            
        Returns:
            更新結果
        """
        if task_id not in self.active_tasks:
            return {
                'success': False,
                'error': f'Task {task_id} not found'
            }
        
        try:
            # ステータス更新
            self.active_tasks[task_id]['status'] = status
            self.active_tasks[task_id]['updated_at'] = datetime.now().isoformat()
            
            # 追加データの更新
            if update_data:
                for key, value in update_data.items():
                    if key not in ['task_id', 'created_at']:  # 保護されたフィールド
                        self.active_tasks[task_id][key] = value
            
            # 保存
            self._save_active_tasks()
            
            logger.info(f"Task status updated: {task_id} -> {status}")
            
            return {
                'success': True,
                'task_id': task_id,
                'new_status': status
            }
            
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def submit_completion_report(self, task_id: str, 
                               report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        完了報告を提出
        
        Args:
            task_id: タスクID
            report_data: 報告データ
            
        Returns:
            提出結果
        """
        if task_id not in self.active_tasks:
            return {
                'success': False,
                'error': f'Task {task_id} not found'
            }
        
        try:
            # 完了報告を構築
            completion_report = {
                'report_id': f"report_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'task_id': task_id,
                'task_info': self.active_tasks[task_id].copy(),
                'completion_time': datetime.now().isoformat(),
                'status': report_data.get('status', ReportStatus.COMPLETED.value),
                'summary': report_data.get('summary', ''),
                'deliverables': report_data.get('deliverables', []),
                'issues_encountered': report_data.get('issues_encountered', []),
                'lessons_learned': report_data.get('lessons_learned', []),
                'next_steps': report_data.get('next_steps', []),
                'metrics': report_data.get('metrics', {}),
                'attachments': report_data.get('attachments', [])
            }
            
            # 報告を保存
            report_file = os.path.join(
                self.storage_dir, 
                f"{completion_report['report_id']}.json"
            )
            
            with open(report_file, 'w') as f:
                json.dump(completion_report, f, indent=2, ensure_ascii=False)
            
            # 完了報告リストに追加
            self.completed_reports.append(completion_report)
            
            # タスクのステータスを更新
            self.active_tasks[task_id]['status'] = completion_report['status']
            self.active_tasks[task_id]['completion_report'] = completion_report['report_id']
            
            # 完了したタスクをアクティブリストから移動
            if completion_report['status'] in [ReportStatus.COMPLETED.value, 
                                              ReportStatus.FAILED.value,
                                              ReportStatus.CANCELLED.value]:
                del self.active_tasks[task_id]
            
            self._save_active_tasks()
            
            logger.info(f"Completion report submitted: {completion_report['report_id']}")
            
            return {
                'success': True,
                'report_id': completion_report['report_id'],
                'message': 'Completion report submitted successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to submit completion report: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        タスクのステータスを取得
        
        Args:
            task_id: タスクID
            
        Returns:
            タスク情報
        """
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        
        # 完了報告から検索
        for report in self.completed_reports:
            if report['task_id'] == task_id:
                return report['task_info']
        
        return None
    
    def get_active_tasks(self, assignee: Optional[str] = None,
                        task_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        アクティブなタスクを取得
        
        Args:
            assignee: 担当者でフィルタ
            task_type: タスクタイプでフィルタ
            
        Returns:
            タスクリスト
        """
        tasks = list(self.active_tasks.values())
        
        if assignee:
            tasks = [t for t in tasks if t.get('assignee') == assignee]
        
        if task_type:
            tasks = [t for t in tasks if t.get('type') == task_type]
        
        # 優先度と作成日でソート
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        tasks.sort(key=lambda t: (
            priority_order.get(t.get('priority', 'MEDIUM'), 2),
            t.get('created_at', '')
        ))
        
        return tasks
    
    def get_completion_reports(self, 
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None,
                             status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        完了報告を取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
            status: ステータスでフィルタ
            
        Returns:
            報告リスト
        """
        reports = self.completed_reports.copy()
        
        # 日付でフィルタ
        if start_date:
            reports = [
                r for r in reports
                if datetime.fromisoformat(r['completion_time']) >= start_date
            ]
        
        if end_date:
            reports = [
                r for r in reports
                if datetime.fromisoformat(r['completion_time']) <= end_date
            ]
        
        # ステータスでフィルタ
        if status:
            reports = [r for r in reports if r.get('status') == status]
        
        # 完了時刻でソート（新しい順）
        reports.sort(key=lambda r: r['completion_time'], reverse=True)
        
        return reports
    
    def _save_active_tasks(self):
        """アクティブタスクを保存"""
        try:
            active_file = os.path.join(self.storage_dir, 'active_tasks.json')
            with open(active_file, 'w') as f:
                json.dump(self.active_tasks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save active tasks: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            統計データ
        """
        total_tasks = len(self.active_tasks) + len(self.completed_reports)
        
        # ステータス別カウント
        status_counts = {}
        for task in self.active_tasks.values():
            status = task.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for report in self.completed_reports:
            status = report.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # タイプ別カウント
        type_counts = {}
        for task in self.active_tasks.values():
            task_type = task.get('type', 'unknown')
            type_counts[task_type] = type_counts.get(task_type, 0) + 1
        
        for report in self.completed_reports:
            task_type = report.get('task_info', {}).get('type', 'unknown')
            type_counts[task_type] = type_counts.get(task_type, 0) + 1
        
        return {
            'total_tasks': total_tasks,
            'active_tasks': len(self.active_tasks),
            'completed_reports': len(self.completed_reports),
            'status_distribution': status_counts,
            'type_distribution': type_counts,
            'last_updated': datetime.now().isoformat()
        }