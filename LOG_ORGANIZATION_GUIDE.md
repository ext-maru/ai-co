# AI Company ログシステム整理ガイド

## 🗂️ 概要

プロジェクトルートに散らばっている大量のログファイルを整理し、今後のログ管理を自動化します。

## 🚀 実行方法

上記のアーティファクトのコマンドをコピーして実行：

```bash
# コピーしたコマンドを実行
bash
```

## 📁 新しいログ構造

```
/home/aicompany/ai_co/logs/
├── slack/        # Slack関連のログ（最新）
├── worker/       # ワーカーのログ
├── error/        # エラーログ
├── archive/      # 古いログのアーカイブ
│   ├── slack/
│   ├── worker/
│   └── error/
└── temp/         # 一時ファイル
```

## 🔧 作成されるツール

1. **organize_logs_now.py** - ログ整理メインスクリプト
2. **libs/log_manager.py** - 統一ログ管理モジュール
3. **execute_log_organization.py** - AI Command Executor用
4. **update_log_system.py** - 既存スクリプトの更新

## 📝 今後のログ出力

### Pythonコードでの使用例：

```python
from libs.log_manager import LogManager

# Slack用ログ
logger = LogManager.get_slack_logger(__name__)
logger.info("Slack message processed")

# ワーカー用ログ
logger = LogManager.get_worker_logger(__name__)
logger.info("Task completed")

# エラー用ログ
logger = LogManager.get_error_logger(__name__)
logger.error("Something went wrong")
```

## 🔄 自動クリーンアップ

3日以上前のログを自動的にアーカイブ：

```bash
# crontabに追加
0 2 * * * /home/aicompany/ai_co/ai_commands/daily_log_cleanup.sh
```

## ✅ 効果

- ルートディレクトリがクリーンに
- ログが種類別に整理
- 古いログは自動アーカイブ
- 新しいログは適切な場所に保存
- ディスク容量の節約

## 🎯 実行後の確認

```bash
# ログディレクトリの確認
ls -la /home/aicompany/ai_co/logs/

# 残存ログの確認
ls -1 /home/aicompany/ai_co/slack_project_status_*.log | wc -l
```

0件になっていれば成功です！
