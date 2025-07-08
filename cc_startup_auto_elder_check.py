#!/usr/bin/env python3
"""
Claude Code起動時自動エルダーズ状況把握システム
CC startup automatic elder council status check system
"""

import sys
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.elder_council_summoner import ElderCouncilSummoner
from commands.ai_elder_council import cli as elder_cli

console = Console()
logger = logging.getLogger(__name__)

class CCStartupElderCheck:
    """CC起動時エルダーズチェック"""
    
    def __init__(self):
        self.summoner = ElderCouncilSummoner()
        self.console = Console()
        
    def perform_startup_check(self) -> dict:
        """起動時チェック実行"""
        console.print(Panel(
            "[bold blue]🏛️ Claude Code 起動時エルダーズ状況確認[/bold blue]",
            border_style="blue"
        ))
        
        # 1. システム状況取得
        status = self.summoner.get_system_status()
        
        # 2. 緊急トリガーチェック
        critical_issues = self._check_critical_triggers(status)
        
        # 3. 4賢者健康状態
        sages_health = self._check_four_sages_health()
        
        # 4. システムメトリクス
        system_metrics = self._get_system_metrics()
        
        # 5. 状況サマリー表示
        self._display_startup_summary({
            'elder_status': status,
            'critical_issues': critical_issues,
            'sages_health': sages_health,
            'system_metrics': system_metrics
        })
        
        return {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'critical_issues': critical_issues,
            'sages_health': sages_health,
            'recommendation': self._generate_startup_recommendation(status, critical_issues)
        }
    
    def _check_critical_triggers(self, status: dict) -> list:
        """緊急トリガーチェック"""
        critical_issues = []
        
        # Critical/High urgency triggers
        if status.get('urgency_distribution', {}).get('critical', 0) > 0:
            critical_issues.append({
                'type': 'critical_triggers',
                'count': status['urgency_distribution']['critical'],
                'message': f"{status['urgency_distribution']['critical']}件のCRITICALトリガーが発生中"
            })
        
        if status.get('urgency_distribution', {}).get('high', 0) > 2:
            critical_issues.append({
                'type': 'high_triggers',
                'count': status['urgency_distribution']['high'],
                'message': f"{status['urgency_distribution']['high']}件のHIGHトリガーが発生中"
            })
        
        # Pending councils check
        if status.get('pending_councils', 0) > 0:
            critical_issues.append({
                'type': 'pending_councils',
                'count': status['pending_councils'],
                'message': f"{status['pending_councils']}件のエルダー会議が保留中"
            })
        
        return critical_issues
    
    def _check_four_sages_health(self) -> dict:
        """4賢者健康状態チェック"""
        sages_health = {
            'knowledge_sage': {'status': 'healthy', 'last_update': 'recent'},
            'task_sage': {'status': 'healthy', 'last_activity': 'active'},
            'crisis_sage': {'status': 'healthy', 'alerts': 0},
            'rag_sage': {'status': 'healthy', 'search_performance': 'good'}
        }
        
        # Knowledge base health
        kb_path = PROJECT_ROOT / 'knowledge_base'
        if not kb_path.exists():
            sages_health['knowledge_sage']['status'] = 'warning'
            sages_health['knowledge_sage']['issue'] = 'Knowledge base not found'
        
        # Task tracking health
        task_files = list(PROJECT_ROOT.glob('**/task_*.db'))
        if not task_files:
            sages_health['task_sage']['status'] = 'warning'
            sages_health['task_sage']['issue'] = 'No task databases found'
        
        return sages_health
    
    def _get_system_metrics(self) -> dict:
        """システムメトリクス取得"""
        try:
            metrics = self.summoner._collect_system_metrics()
            return {
                'test_coverage': f"{metrics.test_coverage:.1%}",
                'worker_health': f"{metrics.worker_health_score:.1%}",
                'memory_usage': f"{metrics.memory_usage:.1%}",
                'queue_backlog': metrics.queue_backlog,
                'four_sages_consensus': f"{metrics.four_sages_consensus_rate:.1%}"
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {'error': str(e)}
    
    def _display_startup_summary(self, data: dict):
        """起動サマリー表示"""
        status = data['elder_status']
        critical = data['critical_issues']
        sages = data['sages_health']
        metrics = data['system_metrics']
        
        # Main status table
        status_table = Table(title="🏛️ エルダーズ & システム状況", box=box.ROUNDED)
        status_table.add_column("項目", style="cyan")
        status_table.add_column("状況", style="green")
        status_table.add_column("詳細", style="yellow")
        
        # Elder Council Status
        status_table.add_row(
            "エルダー監視",
            "✅ アクティブ" if status.get('monitoring_active') else "❌ 停止",
            f"トリガー: {status.get('total_triggers', 0)}件"
        )
        
        # Critical Issues
        if critical:
            for issue in critical:
                status_table.add_row(
                    "🚨 緊急事項",
                    "要対応",
                    issue['message']
                )
        else:
            status_table.add_row("緊急事項", "✅ なし", "システム安定")
        
        # 4 Sages Health
        for sage_name, sage_data in sages.items():
            status_icon = "✅" if sage_data['status'] == 'healthy' else "⚠️"
            status_table.add_row(
                f"🧙‍♂️ {sage_name}",
                f"{status_icon} {sage_data['status']}",
                sage_data.get('issue', '正常')
            )
        
        console.print(status_table)
        
        # System Metrics
        if not metrics.get('error'):
            metrics_table = Table(title="📊 システムメトリクス", box=box.SIMPLE)
            metrics_table.add_column("メトリクス", style="blue")
            metrics_table.add_column("値", style="green")
            
            for metric, value in metrics.items():
                metrics_table.add_row(metric, str(value))
            
            console.print(metrics_table)
    
    def _generate_startup_recommendation(self, status: dict, critical_issues: list) -> str:
        """起動時推奨事項生成"""
        if critical_issues:
            return f"🚨 {len(critical_issues)}件の緊急事項があります。`ai-elder-council status`で詳細確認してください。"
        elif status.get('total_triggers', 0) > 5:
            return f"⚠️ {status['total_triggers']}件のトリガーが発生中。`ai-elder-council triggers`で確認をお勧めします。"
        elif not status.get('monitoring_active'):
            return "💡 エルダー監視が停止中です。`ai-elder-council start`で監視を開始できます。"
        else:
            return "✅ システムは安定しています。開発を開始できます！"

def startup_hook():
    """CC起動時フック関数"""
    try:
        checker = CCStartupElderCheck()
        result = checker.perform_startup_check()
        
        # 緊急事項がある場合は詳細表示
        if result['critical_issues']:
            console.print(Panel(
                f"[bold red]🚨 緊急対応推奨[/bold red]\n\n" + 
                result['recommendation'] + "\n\n" +
                "[dim]詳細: ai-elder-council status[/dim]",
                border_style="red"
            ))
        else:
            console.print(Panel(
                f"[bold green]✅ システム健全[/bold green]\n\n" + 
                result['recommendation'],
                border_style="green"
            ))
        
        return result
        
    except Exception as e:
        console.print(Panel(
            f"[bold red]❌ エルダーズチェック失敗[/bold red]\n\n" +
            f"エラー: {e}\n\n" +
            "[dim]手動確認: ai-elder-council status[/dim]",
            border_style="red"
        ))
        return {'error': str(e)}

def main():
    """メイン実行（テスト用）"""
    logging.basicConfig(level=logging.INFO)
    result = startup_hook()
    print(f"\n結果: {json.dumps(result, indent=2, default=str, ensure_ascii=False)}")

if __name__ == "__main__":
    main()