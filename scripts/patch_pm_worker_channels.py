#!/usr/bin/env python3
"""
PMWorker Slack Channel Integration Patch
スケーリング通知を専用チャンネルに送るための修正パッチ
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def patch_pm_worker():
    """PMWorkerにチャンネル別通知機能を追加"""
    
    pm_worker_path = PROJECT_ROOT / "workers" / "pm_worker.py"
    
    if not pm_worker_path.exists():
        print(f"❌ PMWorkerが見つかりません: {pm_worker_path}")
        return False
    
    # PMWorkerのコードを読み込む
    with open(pm_worker_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 既にパッチ適用済みかチェック
    if "SlackChannelNotifier" in content:
        print("✅ 既にチャンネル別通知機能が適用されています")
        return True
    
    # インポート部分を見つけて追加
    import_section_end = content.find("PROJECT_DIR = Path(__file__).parent.parent")
    if import_section_end == -1:
        print("❌ インポートセクションが見つかりません")
        return False
    
    # インポート追加
    new_import = "from libs.slack_channel_notifier import SlackChannelNotifier\n"
    insert_pos = content.rfind("\n", 0, import_section_end)
    content = content[:insert_pos] + "\n" + new_import + content[insert_pos:]
    
    # __init__メソッドを修正
    init_start = content.find("def __init__(self):")
    init_end = content.find("\n    def ", init_start + 1)
    if init_start == -1:
        print("❌ __init__メソッドが見つかりません")
        return False
    
    init_content = content[init_start:init_end]
    
    # SlackNotifierの初期化部分を見つけて置換
    slack_init_start = init_content.find("try:\n            self.slack = SlackNotifier()")
    slack_init_end = init_content.find("self.slack = None", slack_init_start) + len("self.slack = None")
    
    if slack_init_start != -1:
        new_slack_init = """try:
            # 通常のSlack通知（タスク完了等）
            self.slack = SlackNotifier()
            # チャンネル別通知（スケーリング、ヘルスチェック等）
            self.channel_notifier = SlackChannelNotifier()
        except Exception as e:
            logger.warning(f"Slack通知の初期化に失敗: {e}")
            self.slack = None
            self.channel_notifier = None"""
        
        init_content = init_content[:slack_init_start] + new_slack_init + init_content[slack_init_end:]
        content = content[:init_start] + init_content + content[init_end:]
    
    # start_scaling_monitorメソッドの通知部分を修正
    scaling_notification_start = content.find('if self.slack:\n                                message = f"🔄 ワーカー自動スケーリング')
    if scaling_notification_start != -1:
        # 通知部分の終了位置を見つける
        scaling_notification_end = content.find(')', scaling_notification_start)
        scaling_notification_end = content.find('\n', scaling_notification_end) + 1
        
        new_scaling_notification = """if self.channel_notifier:
                                # 専用チャンネルに通知
                                self.channel_notifier.send_scaling_notification(
                                    action=action,
                                    current_workers=current,
                                    target_workers=target,
                                    queue_length=metrics['queue_length'],
                                    task_id=f"scaling_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                )
                            elif self.slack:
                                # フォールバック（従来の通知）
                                message = f"🔄 ワーカー自動スケーリング\\n"
                                message += f"アクション: {'スケールアップ' if action == 'up' else 'スケールダウン'}\\n"
                                message += f"ワーカー数: {current} → {target}\\n"
                                message += f"キュー長: {metrics['queue_length']}"
                                self.slack.send_task_completion_simple(
                                    task_id=f"scaling_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                    worker="pm_worker",
                                    prompt="自動スケーリング",
                                    response=message
                                )"""
        
        content = content[:scaling_notification_start] + new_scaling_notification + content[scaling_notification_end:]
    
    # start_health_monitorメソッドの通知部分も同様に修正
    health_notification_start = content.find('if self.slack:\n                                        issues_text = ')
    if health_notification_start != -1:
        health_notification_end = content.find(')', health_notification_start)
        health_notification_end = content.find('\n', health_notification_end) + 1
        
        new_health_notification = """if self.channel_notifier:
                                        # 専用チャンネルに通知
                                        self.channel_notifier.send_health_notification(
                                            worker_id=worker_id,
                                            action="ワーカー再起動",
                                            issues=health_status['issues'],
                                            success=True
                                        )
                                    elif self.slack:
                                        # フォールバック（従来の通知）
                                        issues_text = ', '.join(health_status['issues'])
                                        message = f"🔄 ワーカー自動再起動\\n"
                                        message += f"ワーカー: {worker_id}\\n"
                                        message += f"理由: {issues_text}"
                                        self.slack.send_task_completion_simple(
                                            task_id=f"health_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                            worker="pm_worker",
                                            prompt="ヘルスチェック",
                                            response=message
                                        )"""
        
        content = content[:health_notification_start] + new_health_notification + content[health_notification_end:]
    
    # パッチ適用マーカーを追加
    content = content.replace("# BEST_PRACTICES_PATCH_APPLIED", "# BEST_PRACTICES_PATCH_APPLIED\n# CHANNEL_NOTIFIER_PATCH_APPLIED")
    
    # ファイルに書き戻す
    with open(pm_worker_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ PMWorkerにチャンネル別通知機能を追加しました")
    return True

def main():
    """メイン処理"""
    print("🔧 PMWorker Slack Channel Integration Patch")
    print("=" * 50)
    
    success = patch_pm_worker()
    
    if success:
        print("\n✅ パッチ適用完了！")
        print("\n次のステップ:")
        print("1. PMWorkerを再起動してください:")
        print("   ai-restart")
        print("\n2. Slackで以下のチャンネルを作成してください:")
        print("   - #ai-company-scaling (スケーリング通知用)")
        print("   - #ai-company-health (ヘルスチェック通知用)")
        print("\n3. 必要に応じてチャンネル名を変更する場合は、")
        print("   config/slack.conf の以下の設定を編集してください:")
        print("   - SLACK_SCALING_CHANNEL")
        print("   - SLACK_HEALTH_CHANNEL")
    else:
        print("\n❌ パッチ適用に失敗しました")

if __name__ == "__main__":
    main()
