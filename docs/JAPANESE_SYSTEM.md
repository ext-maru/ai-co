# 🌏 AI Company 日本語化システム

## 概要
AI Companyのすべてのメッセージ、ログ、通知を日本語化するシステムです。

## 機能
- ✅ ワーカーのログメッセージ日本語化
- ✅ Slack通知の日本語化
- ✅ エラーメッセージの日本語化
- ✅ Claude CLIの応答（コメント、ログ）日本語化
- ✅ 言語切り替え機能（ja/en）

## セットアップ方法

### 自動セットアップ（推奨）
AI Command Executorが自動的に実行します：
```bash
# すでに ai_commands/pending/ に配置済み
# 6秒後に自動実行されます
```

### 手動セットアップ
```bash
cd /home/aicompany/ai_co
chmod +x scripts/start_japanese_setup.sh
./scripts/start_japanese_setup.sh
```

## 使用方法

### 1. ワーカーでの使用
```python
from core import BaseWorker, msg

class MyWorker(BaseWorker):
    def process_message(self, ch, method, properties, body):
        # 日本語ログ
        self.log_task_start(task_id, 'データ処理')
        
        # カスタムメッセージ
        self.logger.info(msg('file_created', path='/path/to/file'))
        
        # 完了通知
        self.log_task_complete(task_id, duration=2.5, files=3)
```

### 2. メッセージのカスタマイズ
`core/messages.py` でメッセージを追加・編集できます：
```python
'ja': {
    'custom_message': 'カスタム: {param}',
    # 新しいメッセージを追加
}
```

### 3. 言語の切り替え
`config/system.json` を編集：
```json
{
  "language": "ja"  // "en" に変更で英語
}
```

## メッセージ一覧

### ワーカー関連
- `worker_started`: ワーカー開始
- `worker_stopped`: ワーカー停止
- `worker_error`: ワーカーエラー

### タスク関連
- `task_started`: タスク開始
- `task_completed`: タスク完了
- `task_failed`: タスク失敗
- `task_processing`: タスク処理中

### ファイル操作
- `file_created`: ファイル作成
- `file_updated`: ファイル更新
- `file_deployed`: ファイル配置

### Git操作
- `git_commit`: Gitコミット
- `git_push`: Gitプッシュ
- `git_merge`: Gitマージ

## トラブルシューティング

### メッセージが英語のまま
1. `config/system.json` の `language` が `"ja"` か確認
2. ワーカーを再起動
3. `from core import msg` がインポートされているか確認

### 新しいワーカーが日本語化されない
```bash
python3 scripts/apply_japanese_patch.py
```

### Claude CLIが英語で応答する
```bash
python3 scripts/setup_claude_japanese.py
ai-restart  # ワーカー再起動
```

## 拡張方法

### 新しいメッセージの追加
1. `core/messages.py` の `_load_messages()` メソッドに追加
2. 使用例：`msg('new_message_key', param1=value1)`

### 新しい言語の追加
1. `core/messages.py` に新しい言語コードを追加
2. すべてのメッセージを翻訳
3. `config/system.json` で言語を指定

---

🎉 これで、AI Companyは完全に日本語対応になりました！
