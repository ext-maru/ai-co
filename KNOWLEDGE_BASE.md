# AI Company ナレッジベース

## 🐛 バグ修正履歴

### Pattern #014: Slack通知とワーカー安定性問題 (2025-07-05)

#### 問題の症状
- Slack通知が送信されない、または大幅に遅延する
- "Connection reset by peer" エラーが頻発（73回以上）
- TaskWorkerが時々停止する
- ResultWorkerのログに「Slack通知: 有効」と表示されるが実際には送信されない

#### 原因
1. **SlackNotifierの実装問題**
   - HTTPレスポンスの詳細をログに記録していない
   - エラー時でも常にTrueを返していた可能性

2. **RabbitMQ接続の不安定性**
   - ハートビート設定が不適切
   - 接続が切れた際の再接続処理が不十分

3. **二重通知の問題**
   - TaskWorkerとResultWorkerの両方でSlack通知を送信
   - 処理の遅延と競合状態を引き起こす

#### 解決方法
1. **SlackNotifierの修正**
   ```python
   # libs/slack_notifier.py を修正
   - HTTPステータスコードの適切なチェック
   - レスポンスボディのログ記録
   - タイムアウトと接続エラーの個別処理
   ```

2. **ワーカー安定性の改善**
   ```bash
   # RabbitMQのハートビート設定を60秒に変更
   sudo rabbitmqctl eval 'application:set_env(rabbit, heartbeat, 60).'
   
   # AI Companyを再起動
   bash scripts/fix_worker_stability.sh
   ```

3. **自動監視の実装**
   ```bash
   # ワーカーの健全性を5分ごとにチェック
   nohup python3 scripts/monitor_workers.py > logs/monitor.log 2>&1 &
   ```

#### 関連ファイル
- `/root/ai_co/libs/slack_notifier.py` - 修正版SlackNotifier
- `/root/ai_co/scripts/fix_worker_stability.sh` - 安定性改善スクリプト
- `/root/ai_co/scripts/monitor_workers.py` - ワーカー監視スクリプト
- `/root/ai_co/scripts/monitor_slack_notifications.py` - Slack通知監視スクリプト

#### 予防策
1. ワーカーの定期的な監視を継続
2. ログファイルのエラーパターンを定期的にチェック
3. TaskWorkerの二重通知を無効化することを検討
4. RabbitMQの接続パラメータを適切に設定

#### テスト方法
```bash
# Slack通知のテスト
python3 << 'EOF'
from libs.slack_notifier import SlackNotifier
notifier = SlackNotifier()
result = notifier.test_notification()
print(result)
EOF

# ワーカーの状態確認
ps aux | grep -E "(task_worker|result_worker|pm_worker)" | grep -v grep

# エラーログの確認
tail -f logs/*.log | grep -E '(ERROR|Exception|Connection reset)'
```

---

## 📚 その他のパターン

### Pattern #001-013
（以前のパターンはここに記載）

---

最終更新: 2025-07-05 20:00