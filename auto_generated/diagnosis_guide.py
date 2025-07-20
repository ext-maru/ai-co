#!/usr/bin/env python3
"""
Slack PM-AI問題診断と修復 - 実行ガイド
"""

print("""
🔍 Slack PM-AI問題診断と修復
=============================

現在、以下のコマンドがAI Command Executorで自動実行されています:

【診断コマンド】
1. quick_slack_check.sh - 即時状態確認
2. execute_full_diagnosis.sh - 総合診断実行
3. show_results_delayed.sh - 診断結果表示（40秒後）
4. generate_report_delayed.sh - 診断レポート生成（50秒後）
5. show_execution_summary.sh - 実行状況サマリー

【修復コマンド】
6. emergency_fix_slack_pmai.sh - 緊急修復（プロセス再起動、DB初期化、メッセージ処理）

【問題切り分けのポイント】
1. Slack Polling Workerが稼働しているか
2. Bot TokenとChannel IDが正しく設定されているか
3. BotがチャンネルメンバーになっているかSlackで確認
4. メンション形式が正しいか（@pm-ai または @Bot_ID）
5. RabbitMQが正常に動作しているか

【ログ確認方法】
# AI Command Executorログ
tail -f /home/aicompany/ai_co/ai_commands/logs/*.log

# ワーカーログ
tail -f /home/aicompany/ai_co/logs/slack_polling_worker.log
tail -f /home/aicompany/ai_co/logs/task_worker.log

# TMUXセッション確認
tmux attach -t ai_company
→ Ctrl+B, W でウィンドウ一覧
→ slack_polling を選択

【Slackでのテスト方法】
1. Slackチャンネルで以下を送信:
   @pm-ai テストメッセージ
   @pm-ai 簡単なPythonスクリプトを作成して

2. 期待される動作:
   - 👀 リアクション追加
   - タスクがai_tasksキューに投入
   - TaskWorkerが処理開始
   - 結果がSlackに通知

診断完了まで約1分お待ちください。
""")

if __name__ == "__main__":
    pass
