# 🚀 Elders Guild 日本語化クイックスタート

## 🎯 3秒でできる日本語化

AI Command Executorがすでに設定済みです！**6秒後に自動で日本語化が開始されます。**

以下のファイルがすでに `ai_commands/pending/` に配置されています：
- `japanese_setup.sh` - メインセットアップ
- `test_japanese.sh` - 動作確認用

## ✅ 何が日本語化されるか

1. **ワーカーのログ**
   - `Task started` → `タスク開始`
   - `Task completed` → `タスク完了`
   - `Error occurred` → `エラーが発生しました`

2. **Slack通知**
   - すべての通知が日本語に
   - エラー内容も日本語で説明

3. **Claude CLIの応答**
   - コード内のコメントが日本語
   - 生成されるログメッセージも日本語

## 📝 使い方

既存のコードはそのまま動作します！新しく作る場合：

```python
from core import BaseWorker, msg

# ログは自動的に日本語に
self.log_task_start(task_id)  # → "タスク開始: xxx"
self.log_task_complete(task_id, duration=1.5)  # → "タスク完了: xxx | 処理時間: 1.50秒"

# カスタムメッセージも使える
self.logger.info(msg('file_created', path='test.py'))  # → "ファイル作成: test.py"
```

## 🔧 カスタマイズ

メッセージを追加したい場合は `core/messages.py` を編集：
```python
'ja': {
    'my_message': '私のメッセージ: {param}',
}
```

## 🎉 完了！

これで、Elders Guildは完全に日本語対応になりました。
エラーが出た場合も、日本語でわかりやすく表示されます。
