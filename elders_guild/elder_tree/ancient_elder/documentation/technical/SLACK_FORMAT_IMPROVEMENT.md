# 📢 Slack通知フォーマット改善ガイド

## 🎯 改善内容

### 1. **脳みそ絵文字の削除**
- 🧠 → 削除
- RAG適用情報は「RAG: Applied」または「RAG: Not Applied」で表示

### 2. **応答内容の完全表示**
- 以前: 200文字で切り詰め
- 現在: 1500文字まで表示（大幅に拡張）

### 3. **プロフェッショナルなフォーマット**
```
✅ **Task Completed**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**ID:** `general_20250703_000617`
**Worker:** `worker-1`
**Type:** `general`
**Status:** `RAG: Applied`

**Request:**
`テストタスクのプロンプト...`

**Response:**
完全な応答内容がここに表示されます。
最大1500文字まで表示可能で、見切れることがありません。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*Elders Guild System*
```

## 🚀 適用方法

### 1. **ワーカー再起動（AI Command Executor経由）**
```bash
# AI Command Executorが自動実行（6秒後）
# ファイル: ai_commands/pending/restart_slack_workers.json
```

### 2. **動作確認**
```bash
# テスト通知送信（AI Command Executor経由）
# ファイル: ai_commands/pending/test_slack_format.json
```

### 3. **フォーマット確認**
```bash
cd /home/aicompany/ai_co
python3 scripts/check_slack_format.py
```

## 📊 改善効果

| 項目 | 改善前 | 改善後 |
|------|--------|--------|
| 絵文字 | 🧠 脳みそ絵文字 | ✅ シンプルな成功マーク |
| 応答表示 | 200文字（見切れ） | 1500文字（完全表示） |
| フォーマット | 基本的 | プロフェッショナル |
| 可読性 | 普通 | 高い |

## 🔧 技術詳細

### 変更ファイル
1. `libs/slack_notifier.py`
   - `send_task_completion_simple`メソッドを追加
   - プロフェッショナルなフォーマット実装

2. `workers/result_worker.py`
   - `_format_success_message`メソッドを改善
   - 応答表示を1000文字に拡張

### AI Command Executor統合
- 全ての操作を自動化
- 手動作業不要
- 結果はSlackで確認可能

## 📝 注意事項

- Slack通知の文字数制限（約4000文字）は維持
- 1500文字を超える応答は「...」で省略
- プロンプトは500文字まで表示

---

**🎉 これでSlack通知がより見やすく、プロフェッショナルになりました！**
