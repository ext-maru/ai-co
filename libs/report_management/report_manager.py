"""
Report Manager

完了報告管理システムのメインマネージャー
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys

# Elders Guildのライブラリパスを追加
sys.path.append('/home/aicompany/ai_co')

from .report_tracker import CompletionReportTracker
from .report_analyzer import ReportAnalyzer
from .decision_support import DecisionSupportSystem

logger = logging.getLogger(__name__)


class ReportManager:
    """報告管理システムのメインクラス"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config or self._get_default_config()
        
        # コンポーネントの初期化
        self.tracker = CompletionReportTracker(
            self.config.get('storage_dir', '/home/aicompany/ai_co/data/completion_reports')
        )
        self.analyzer = ReportAnalyzer()
        self.decision_support = DecisionSupportSystem()
        
        logger.info("ReportManager initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を取得"""
        return {
            'storage_dir': '/home/aicompany/ai_co/data/completion_reports',
            'auto_analyze': True,
            'auto_decide': True,
            'notification_enabled': True
        }
    
    def register_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        新しいタスクを登録
        
        Args:
            task_id: タスクID
            task_data: タスクデータ
            
        Returns:
            登録結果
        """
        result = self.tracker.register_task(task_id, task_data)
        
        if result['success']:
            logger.info(f"Task registered: {task_id}")
            
            # 通知
            if self.config.get('notification_enabled'):
                self._send_notification(
                    f"New task registered: {task_data.get('title', task_id)}",
                    'info'
                )
        
        return result
    
    def submit_report(self, task_id: str, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        完了報告を提出し、分析と決定を行う
        
        Args:
            task_id: タスクID
            report_data: 報告データ
            
        Returns:
            処理結果
        """
        try:
            # 報告を提出
            submission_result = self.tracker.submit_completion_report(task_id, report_data)
            
            if not submission_result['success']:
                return submission_result
            
            # 報告を取得
            reports = self.tracker.get_completion_reports()
            report = next((r for r in reports if r['report_id'] == submission_result['report_id']), None)
            
            if not report:
                return {
                    'success': False,
                    'error': 'Report not found after submission'
                }
            
            result = {
                'success': True,
                'report_id': submission_result['report_id'],
                'submission': submission_result
            }
            
            # 自動分析
            if self.config.get('auto_analyze'):
                analysis = self.analyzer.analyze_completion_report(report)
                result['analysis'] = analysis
                
                # 自動決定
                if self.config.get('auto_decide'):
                    decision = self.decision_support.generate_decision(report, analysis)
                    result['decision'] = decision
                    
                    # 重要な決定の場合は通知
                    if decision.get('confidence_level', 0) > 0.7:
                        self._send_high_priority_notification(task_id, decision)
            
            # 完了通知
            if self.config.get('notification_enabled'):
                self._send_completion_notification(task_id, report, result.get('analysis'))
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process report: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_task_overview(self, task_id: str) -> Dict[str, Any]:
        """
        タスクの概要を取得（状態、報告、分析、決定を含む）
        
        Args:
            task_id: タスクID
            
        Returns:
            タスク概要
        """
        overview = {
            'task_id': task_id,
            'status': None,
            'report': None,
            'analysis': None,
            'decision': None
        }
        
        # タスク状態を取得
        task_status = self.tracker.get_task_status(task_id)
        if task_status:
            overview['status'] = task_status
        
        # 完了報告を検索
        reports = self.tracker.get_completion_reports()
        for report in reports:
            if report['task_id'] == task_id:
                overview['report'] = report
                
                # 分析を取得または実行
                if report['report_id'] in self.analyzer.analysis_cache:
                    overview['analysis'] = self.analyzer.analysis_cache[report['report_id']]
                else:
                    overview['analysis'] = self.analyzer.analyze_completion_report(report)
                
                # 決定を生成
                if overview['analysis']:
                    overview['decision'] = self.decision_support.generate_decision(
                        report, overview['analysis']
                    )
                
                break
        
        return overview
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        ダッシュボード用のデータを取得
        
        Returns:
            ダッシュボードデータ
        """
        # 統計情報
        statistics = self.tracker.get_statistics()
        
        # アクティブタスク
        active_tasks = self.tracker.get_active_tasks()
        
        # 最近の完了報告
        recent_reports = self.tracker.get_completion_reports()[:5]
        
        # 最近の決定
        recent_decisions = self.decision_support.get_decision_history(5)
        
        # 高リスクタスクを特定
        high_risk_tasks = []
        for task in active_tasks:
            if task.get('priority') == 'CRITICAL':
                high_risk_tasks.append(task)
        
        return {
            'statistics': statistics,
            'active_tasks': {
                'total': len(active_tasks),
                'critical': len([t for t in active_tasks if t.get('priority') == 'CRITICAL']),
                'high': len([t for t in active_tasks if t.get('priority') == 'HIGH']),
                'tasks': active_tasks[:10]  # 最新10件
            },
            'recent_completions': recent_reports,
            'recent_decisions': recent_decisions,
            'high_risk_tasks': high_risk_tasks,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_summary_report(self, start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        サマリーレポートを生成
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            サマリーレポート
        """
        # 期間内の報告を取得
        reports = self.tracker.get_completion_reports(start_date, end_date)
        
        summary = {
            'period': {
                'start': start_date.isoformat() if start_date else 'all',
                'end': end_date.isoformat() if end_date else 'all'
            },
            'total_tasks': len(reports),
            'completion_rate': 0,
            'average_quality_score': 0,
            'common_issues': {},
            'lessons_learned': [],
            'recommended_improvements': []
        }
        
        if not reports:
            return summary
        
        # 完了率
        completed = len([r for r in reports if r.get('status') == 'completed'])
        summary['completion_rate'] = (completed / len(reports)) * 100
        
        # 平均品質スコア
        quality_scores = []
        all_issues = []
        all_lessons = []
        
        for report in reports:
            # 分析を実行
            analysis = self.analyzer.analyze_completion_report(report)
            
            # 品質スコア
            quality = analysis.get('quality_score', {})
            if quality.get('overall'):
                quality_scores.append(quality['overall'])
            
            # 問題を収集
            issues = report.get('issues_encountered', [])
            all_issues.extend(issues)
            
            # 教訓を収集
            lessons = report.get('lessons_learned', [])
            all_lessons.extend(lessons)
        
        if quality_scores:
            summary['average_quality_score'] = sum(quality_scores) / len(quality_scores)
        
        # 共通の問題を特定
        issue_counts = {}
        for issue in all_issues:
            if isinstance(issue, str):
                issue_key = issue.lower()[:50]  # 最初の50文字で集計
                issue_counts[issue_key] = issue_counts.get(issue_key, 0) + 1
        
        # 上位5つの問題
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        summary['common_issues'] = dict(sorted_issues[:5])
        
        # 重要な教訓
        summary['lessons_learned'] = list(set(all_lessons))[:10]  # 重複を除いて最大10個
        
        # 改善提案を生成
        if summary['completion_rate'] < 80:
            summary['recommended_improvements'].append(
                'Improve task completion rate through better planning and resource allocation'
            )
        
        if summary['average_quality_score'] < 70:
            summary['recommended_improvements'].append(
                'Focus on quality improvements through code reviews and testing'
            )
        
        if len(summary['common_issues']) > 3:
            summary['recommended_improvements'].append(
                'Address recurring issues through process improvements'
            )
        
        return summary
    
    def _send_notification(self, message: str, level: str = 'info'):
        """通知を送信"""
        try:
            # TODO: Slack通知やElder Council通知の実装
            logger.info(f"Notification ({level}): {message}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def _send_completion_notification(self, task_id: str, 
                                    report: Dict[str, Any],
                                    analysis: Optional[Dict[str, Any]] = None):
        """完了通知を送信"""
        status = report.get('status', 'unknown')
        title = report.get('task_info', {}).get('title', task_id)
        
        message = f"Task '{title}' completed with status: {status}"
        
        if analysis:
            quality = analysis.get('quality_score', {}).get('overall', 0)
            message += f" (Quality: {quality:.1f}%)"
        
        level = 'info' if status == 'completed' else 'warning'
        self._send_notification(message, level)
    
    def _send_high_priority_notification(self, task_id: str, 
                                       decision: Dict[str, Any]):
        """高優先度の決定通知を送信"""
        actions = decision.get('recommended_actions', [])
        if actions:
            priority_actions = [a['title'] for a in actions[:2]]
            message = f"High confidence decision for {task_id}: {', '.join(priority_actions)}"
            self._send_notification(message, 'important')
    
    def export_reports(self, format: str = 'json', 
                      output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        報告をエクスポート
        
        Args:
            format: エクスポート形式 (json, markdown)
            output_path: 出力パス
            
        Returns:
            エクスポート結果
        """
        try:
            # データを収集
            export_data = {
                'export_time': datetime.now().isoformat(),
                'active_tasks': self.tracker.get_active_tasks(),
                'completion_reports': self.tracker.get_completion_reports(),
                'statistics': self.tracker.get_statistics()
            }
            
            if format == 'json':
                content = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            elif format == 'markdown':
                content = self._generate_markdown_report(export_data)
            
            else:
                return {
                    'success': False,
                    'error': f'Unsupported format: {format}'
                }
            
            # ファイルに保存
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write(content)
            
            return {
                'success': True,
                'format': format,
                'output_path': output_path,
                'content_length': len(content)
            }
            
        except Exception as e:
            logger.error(f"Failed to export reports: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_markdown_report(self, data: Dict[str, Any]) -> str:
        """Markdown形式のレポートを生成"""
        md = f"# Completion Report Summary\n\n"
        md += f"**Generated**: {data['export_time']}\n\n"
        
        # 統計
        stats = data['statistics']
        md += "## Statistics\n\n"
        md += f"- Total Tasks: {stats['total_tasks']}\n"
        md += f"- Active Tasks: {stats['active_tasks']}\n"
        md += f"- Completed Reports: {stats['completed_reports']}\n\n"
        
        # アクティブタスク
        md += "## Active Tasks\n\n"
        for task in data['active_tasks'][:10]:
            md += f"- **{task['title']}** ({task['priority']})\n"
            md += f"  - Status: {task['status']}\n"
            md += f"  - Created: {task['created_at']}\n\n"
        
        # 完了報告
        md += "## Recent Completions\n\n"
        for report in data['completion_reports'][:10]:
            md += f"### {report['task_info']['title']}\n"
            md += f"- Status: {report['status']}\n"
            md += f"- Completed: {report['completion_time']}\n"
            if report.get('summary'):
                md += f"- Summary: {report['summary']}\n"
            md += "\n"
        
        return md


# CLI用エントリーポイント
def main():
    """CLIエントリーポイント"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Report Management System')
    parser.add_argument('command', 
                       choices=['register', 'submit', 'status', 'dashboard', 'export'],
                       help='Command to execute')
    parser.add_argument('--task-id', help='Task ID')
    parser.add_argument('--title', help='Task title')
    parser.add_argument('--format', choices=['json', 'markdown'], default='json',
                       help='Export format')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    manager = ReportManager()
    
    if args.command == 'register':
        if not args.task_id or not args.title:
            print("Task ID and title required for registration")
            return
        
        result = manager.register_task(args.task_id, {'title': args.title})
        print(json.dumps(result, indent=2))
    
    elif args.command == 'status':
        if not args.task_id:
            print("Task ID required for status")
            return
        
        overview = manager.get_task_overview(args.task_id)
        print(json.dumps(overview, indent=2, default=str))
    
    elif args.command == 'dashboard':
        data = manager.get_dashboard_data()
        print(json.dumps(data, indent=2, default=str))
    
    elif args.command == 'export':
        result = manager.export_reports(args.format, args.output)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()