#!/usr/bin/env python3
"""
AI Elder-PM管理コマンド v1.0
Elder CouncilとPMワーカー間の統合管理
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from libs.pm_elder_integration import PMElderIntegration
    from libs.elder_council_summoner import ElderCouncilSummoner
    from libs.slack_notifier import SlackNotifier
    from libs.env_config import get_config
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class ElderPMCommand:
    """Elder-PM管理コマンドクラス"""
    
    def __init__(self):
        self.pm_elder = PMElderIntegration()
        self.elder_summoner = ElderCouncilSummoner()
        self.slack = SlackNotifier()
        self.config = get_config()
    
    def list_pending_approvals(self):
        """保留中承認要求一覧"""
        approvals = self.pm_elder.get_pending_approvals()
        
        if not approvals:
            print("📋 保留中の承認要求はありません。")
            return
        
        print(f"📋 保留中の承認要求: {len(approvals)}件")
        print("=" * 60)
        
        for approval in approvals:
            print(f"🔹 承認ID: {approval.approval_id}")
            print(f"   プロジェクトID: {approval.project_id}")
            print(f"   複雑度: {approval.complexity.value}")
            print(f"   要求日時: {approval.expires_at.strftime('%Y-%m-%d %H:%M') if approval.expires_at else '無期限'}")
            print(f"   概要: {approval.request_summary[:100]}...")
            print()
    
    def approve_project(self, approval_id: str, conditions: List[str] = None):
        """プロジェクト承認"""
        success = self.pm_elder.approve_project(approval_id, conditions)
        
        if success:
            print(f"✅ プロジェクト承認完了: {approval_id}")
            
            if conditions:
                print(f"📝 承認条件:")
                for condition in conditions:
                    print(f"   - {condition}")
            
            # Slack通知
            message = f"✅ **Elder承認完了**\n\n承認ID: {approval_id}"
            if conditions:
                message += f"\n\n**承認条件**:\n" + "\n".join(f"- {c}" for c in conditions)
            
            self.slack.send_message(message, channel="#pm-notifications")
        else:
            print(f"❌ 承認に失敗しました: {approval_id}")
    
    def reject_project(self, approval_id: str, reason: str):
        """プロジェクト却下"""
        success = self.pm_elder.reject_project(approval_id, reason)
        
        if success:
            print(f"❌ プロジェクト却下完了: {approval_id}")
            print(f"理由: {reason}")
            
            # Slack通知
            message = f"❌ **Elder却下決定**\n\n承認ID: {approval_id}\n理由: {reason}"
            self.slack.send_message(message, channel="#pm-notifications")
        else:
            print(f"❌ 却下処理に失敗しました: {approval_id}")
    
    def summon_council(self, topic: str, urgency: str = "medium"):
        """Elder Council召集"""
        print(f"🏛️ Elder Council召集中...")
        print(f"議題: {topic}")
        print(f"緊急度: {urgency}")
        
        # Council召集（実際の実装では詳細な議題設定が必要）
        message = f"""
🏛️ **Elder Council召集**

**議題**: {topic}
**緊急度**: {urgency}
**召集時刻**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Elder Councilの開催を要請します。
参加可能なElderの方は応答をお願いいたします。
        """.strip()
        
        self.slack.send_message(message, channel="#elders-council")
        print("✅ Elder Council召集通知を送信しました。")
    
    def show_integration_status(self):
        """統合システム状態表示"""
        status = self.pm_elder.get_integration_status()
        
        print("📊 PM-Elder統合システム状態")
        print("=" * 40)
        print(f"保留中承認: {status['pending_approvals']}件")
        print(f"相談要求: {status['consultation_requests']}件")
        print(f"Elder監視: {'有効' if status['elder_summoner_active'] else '無効'}")
        print(f"最終確認: {status['last_assessment']}")
        
        # 詳細統計
        approvals = self.pm_elder.get_pending_approvals()
        if approvals:
            print("\n📋 承認要求詳細:")
            complexity_count = {}
            for approval in approvals:
                comp = approval.complexity.value
                complexity_count[comp] = complexity_count.get(comp, 0) + 1
            
            for complexity, count in complexity_count.items():
                print(f"   {complexity}: {count}件")
    
    def start_monitoring(self):
        """Elder監視開始"""
        self.elder_summoner.start_monitoring()
        print("👁️ Elder監視システムを開始しました。")
        
        # Slack通知
        self.slack.send_message(
            "👁️ **Elder監視システム開始**\n\nシステム進化メトリクスの監視を開始しました。",
            channel="#elders-notifications"
        )
    
    def stop_monitoring(self):
        """Elder監視停止"""
        self.elder_summoner.stop_monitoring()
        print("🛑 Elder監視システムを停止しました。")
        
        # Slack通知
        self.slack.send_message(
            "🛑 **Elder監視システム停止**\n\nシステム監視を停止しました。",
            channel="#elders-notifications"
        )
    
    def show_help(self):
        """ヘルプ表示"""
        help_text = """
🏛️ AI Elder-PM管理コマンド

【基本コマンド】
  ai-elder-pm status              統合システム状態表示
  ai-elder-pm list               保留中承認要求一覧
  ai-elder-pm approve <ID>       プロジェクト承認
  ai-elder-pm reject <ID> <理由>  プロジェクト却下
  ai-elder-pm council <議題>      Elder Council召集

【監視コマンド】
  ai-elder-pm monitor start     Elder監視開始
  ai-elder-pm monitor stop      Elder監視停止

【使用例】
  # 承認要求確認
  ai-elder-pm list
  
  # プロジェクト承認
  ai-elder-pm approve abc123
  
  # 条件付き承認
  ai-elder-pm approve abc123 --conditions "テストカバレッジ90%以上" "コードレビュー必須"
  
  # プロジェクト却下
  ai-elder-pm reject abc123 "リスクが高すぎる"
  
  # 緊急Council召集
  ai-elder-pm council "システム障害対応" --urgency critical

【Slack連携】
  各操作は自動的にSlackに通知されます:
  - #elders-notifications: 一般通知
  - #elders-urgent: 緊急要請
  - #pm-notifications: PM向け通知
        """.strip()
        
        print(help_text)

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(
        description="AI Elder-PM管理コマンド",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='実行コマンド')
    
    # status サブコマンド
    subparsers.add_parser('status', help='統合システム状態表示')
    
    # list サブコマンド
    subparsers.add_parser('list', help='保留中承認要求一覧')
    
    # approve サブコマンド
    approve_parser = subparsers.add_parser('approve', help='プロジェクト承認')
    approve_parser.add_argument('approval_id', help='承認ID')
    approve_parser.add_argument('--conditions', nargs='*', help='承認条件')
    
    # reject サブコマンド
    reject_parser = subparsers.add_parser('reject', help='プロジェクト却下')
    reject_parser.add_argument('approval_id', help='承認ID')
    reject_parser.add_argument('reason', help='却下理由')
    
    # council サブコマンド
    council_parser = subparsers.add_parser('council', help='Elder Council召集')
    council_parser.add_argument('topic', help='議題')
    council_parser.add_argument('--urgency', choices=['low', 'medium', 'high', 'critical'], 
                               default='medium', help='緊急度')
    
    # monitor サブコマンド
    monitor_parser = subparsers.add_parser('monitor', help='Elder監視管理')
    monitor_parser.add_argument('action', choices=['start', 'stop'], help='開始/停止')
    
    # ヘルプが指定されない場合はヘルプを表示
    if len(sys.argv) == 1:
        args = parser.parse_args(['--help'])
    else:
        args = parser.parse_args()
    
    # コマンド実行
    try:
        elder_pm = ElderPMCommand()
        
        if args.command == 'status':
            elder_pm.show_integration_status()
        
        elif args.command == 'list':
            elder_pm.list_pending_approvals()
        
        elif args.command == 'approve':
            elder_pm.approve_project(args.approval_id, args.conditions)
        
        elif args.command == 'reject':
            elder_pm.reject_project(args.approval_id, args.reason)
        
        elif args.command == 'council':
            elder_pm.summon_council(args.topic, args.urgency)
        
        elif args.command == 'monitor':
            if args.action == 'start':
                elder_pm.start_monitoring()
            elif args.action == 'stop':
                elder_pm.stop_monitoring()
        
        else:
            elder_pm.show_help()
    
    except KeyboardInterrupt:
        print("\n🔸 処理を中断しました。")
        sys.exit(0)
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()