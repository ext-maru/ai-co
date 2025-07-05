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

### Pattern #015: ディレクトリ構造の再編成 (2025-07-05)

#### 背景
プロジェクトが成長し、libs/に21個、scripts/に20個のファイルが混在。機能別の整理が必要になった。

#### 実施内容
1. **新しいディレクトリ構造**
   ```
   core/       - システムコア（workers, monitoring, queue）
   features/   - 機能別モジュール（ai, conversation, database, notification, integration）
   utils/      - ユーティリティ（scripts, helpers）
   tests/      - テストコード
   ```

2. **移動したファイル**
   - workers/* → core/workers/
   - libs/health_checker.py等 → core/monitoring/
   - libs/rag_manager.py等 → features/ai/
   - libs/conversation_*.py → features/conversation/
   - libs/slack_notifier*.py → features/notification/
   - scripts/test_*.py → tests/

3. **import文の自動更新**
   - update_imports.pyスクリプトで24ファイルを一括更新
   - sys.path.append('/root/ai_co')を追加

4. **設定ファイルパスの修正**
   - SlackNotifierのconfig pathを絶対パスに変更
   - Path("/root/ai_co/config/slack.conf")

5. **後方互換性**
   - シンボリックリンク作成
   - scripts → utils/scripts
   - workers → core/workers

#### 注意点
- PYTHONPATH=/root/ai_co の設定が必要
- 新しいファイルは適切なディレクトリに配置
- DIRECTORY_STRUCTURE.mdを参照

---

### Pattern #016: Slack通知V2デグレ修正 (2025-07-05)

#### 問題の症状
- `'NoneType' object has no attribute 'get'` エラーが発生
- 拡張版Slack通知が送信されない
- result_worker.pyでSlack通知処理が失敗

#### 原因
1. **データ検証不足**
   - `result_worker.py`でNoneデータが渡される
   - `slack_notifier_v2.py`でデータ型チェックが不十分

2. **時刻データ処理の問題**
   - datetime型とstring型の混在
   - end_timeのNone処理が不適切

3. **エラー処理の脆弱性**
   - 例外発生時のフォールバック機能なし

#### 解決方法
1. **データ検証の強化**
   ```python
   # result_worker.py:53-55
   if not result or not isinstance(result, dict):
       logger.error("Slack通知送信エラー: 無効な結果データ")
       return
   ```

2. **安全な時刻処理**
   ```python
   # slack_notifier_v2.py:109-118
   end_time = task_data.get('end_time')
   if not end_time:
       end_time = datetime.now()
   elif isinstance(end_time, str):
       try:
           end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
       except ValueError:
           end_time = datetime.now()
   ```

3. **フォールバック機能の実装**
   ```python
   # result_worker.py:106-116
   if not success and self.slack_notifier_v1.enabled:
       fallback_message = f"タスク {task_data['task_id']} が完了しました"
       self.slack_notifier_v1.send_notification(fallback_message)
   ```

#### 関連ファイル
- `/root/ai_co/core/workers/result_worker.py` - データ検証とフォールバック機能
- `/root/ai_co/features/notification/slack_notifier_v2.py` - 例外処理強化

#### テスト方法
```bash
# 修正後のテスト
python3 -c "
from features.notification.slack_notifier_v2 import SlackNotifierV2
from datetime import datetime
notifier = SlackNotifierV2()
test_data = {'task_id': 'test_001', 'status': 'completed', 'end_time': datetime.now()}
print('✅ Success' if notifier.send_enhanced_task_notification(test_data) else '❌ Failed')
"
```

---

## 📚 その他のパターン

### Pattern #001-013
（以前のパターンはここに記載）

---

最終更新: 2025-07-05 21:00