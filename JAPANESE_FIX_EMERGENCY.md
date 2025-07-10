# 🚨 ResultWorker日本語化 - 緊急対応手順

## 問題
Slack通知がまだ英語のままで、フォーマットも簡素化されている

## 緊急対応方法

### 方法1: 自動修正（推奨）
```bash
cd /home/aicompany/ai_co
chmod +x emergency_apply_japanese_patch.sh
./emergency_apply_japanese_patch.sh
```

### 方法2: 手動で確認と修正
```bash
# 1. 現在の状態確認
cd /home/aicompany/ai_co
python3 check_result_worker_japanese.py

# 2. パッチ適用（必要な場合）
python3 scripts/patch_result_worker_japanese.py
python3 scripts/patch_pm_worker_japanese.py

# 3. ワーカー再起動
pkill -f result_worker.py
pkill -f pm_worker.py
sleep 3

# 4. ワーカー起動
nohup python3 workers/result_worker.py > logs/result_worker.log 2>&1 &
nohup python3 workers/pm_worker.py > logs/pm_worker.log 2>&1 &

# 5. 確認
ps aux | grep -E "(result|pm)_worker.py" | grep -v grep
```

### 方法3: 完全再起動
```bash
# すべてのワーカーを再起動
ai-restart

# または個別に
ai-stop
sleep 5
ai-start
```

## 期待される結果

### Before（現在）:
```
**Elders Guild タスク完了ID:** general_20250703_015105 **ワーカー:** worker-1...
```

### After（修正後）:
```
✅ **Elders Guild タスク完了**

**タスクID:** general_20250703_015105
**ワーカー:** worker-1
**RAG:** 適用済み

**種別:** general | **処理時間:** 2.34秒 | **ファイル数:** 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**プロンプト:**
明日の神奈川の天気はなんだろな

**応答:**
明日（7月3日）の神奈川県の天気予報：

**曇り時々晴れ**
- 午後から晴れ間が出る予想
- 一部地域で雨や雷雨の可能性あり
...（最大1500文字）

**📊 パフォーマンス指標:**
• 成功率: 98.5% (197/200)
• 平均処理時間: 1.85秒

*Elders Guild RAGシステム*
```

## トラブルシューティング

1. **パッチが適用されない**
   - scripts/ディレクトリの権限確認
   - Pythonのインポートエラーがないか確認

2. **ワーカーが起動しない**
   - RabbitMQが動作しているか確認: `sudo systemctl status rabbitmq-server`
   - ログを確認: `tail -f logs/result_worker.log`

3. **通知が変わらない**
   - 古いメッセージがキューに残っている可能性
   - 新しいタスクを送信: `ai-send "日本語テスト" general`
