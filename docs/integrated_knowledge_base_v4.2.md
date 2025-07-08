# 📚 AI Company 統合ナレッジベース v4.2

## 🎯 システム概要

### **基本情報**
- **環境**: Ubuntu 24.04 LTS (WSL2)
- **ユーザー**: aicompany (pass: aicompany) ※rootユーザーでの実行も可能
- **パス**: `/home/aicompany/ai_co`
- **Python**: 3.12.3
- **tmuxセッション**: ai_company, ai_quality

## 🚀 主要システム一覧

### 1. **コアシステム**
- **TaskWorker**: Claude CLI統合によるコード生成
- **PMWorker**: ファイル配置とGit管理
- **ResultWorker**: Slack通知
- **DialogTaskWorker**: 対話型タスク処理

### 2. **品質管理システム** 
- **QualityPMWorker**: コード品質チェックと改善指示
- **品質対応TaskWorker**: フィードバックに基づく改善実装

### 3. **RAGシステム**
- **GitHubAwareRAGManager**: コードベースを含むコンテキスト生成
- **TaskHistoryDB**: タスク履歴の永続化と検索

### 4. **自己進化システム**
- **SelfEvolutionManager**: ファイルの自動配置
- **GitFlowManager**: Git操作の自動化

### 5. **新機能（v4.1）** ✨
- **タスクテンプレート**: 再利用可能なタスク定義
- **ワーカー間通信**: ワーカー協調動作
- **優先度システム**: タスク優先度管理
- **DLQシステム**: 失敗タスク管理

### 6. **AI Command Executor** 🆕
- **自動コマンド実行**: AIが作成したコマンドを自動実行
- **完全非同期**: 手動介入不要
- **ログ管理**: 全実行履歴を保存

## 📋 主要コマンド

### 基本操作
```bash
ai              # インタラクティブメニュー
ai-start        # 通常システム起動
ai-quality      # 品質管理システム起動
ai-cmd-executor # Command Executor管理
```

### タスク実行
```bash
ai-send "要件" code            # コード生成
ai-dialog "複雑な要件"         # 対話型タスク
ai-run <template_name>         # テンプレート実行
```

### 管理・監視
```bash
ai-status       # システム状態
ai-logs         # ログ確認
ai-worker-comm  # ワーカー間通信監視
ai-dlq status   # DLQ状態確認
```

## 🔧 設定ファイル構造

```
config/
├── slack.conf      # Slack通知設定
├── worker.json     # ワーカー詳細設定
├── storage.json    # ストレージ設定
├── git.json        # Git設定
└── quality.json    # 品質基準設定
```

## 📊 データベース

- **task_history.db**: タスク履歴・RAG用
- **conversations.db**: 対話履歴
- **github_code.db**: コード検索用

## 🤖 AI Command Executor

### 概要
AIとユーザー間のコマンド実行を完全自動化

### 使用方法
```python
from libs.ai_command_helper import AICommandHelper
helper = AICommandHelper()

# コマンド作成
helper.create_bash_command("ps aux | grep worker", "check_workers")

# 5秒後に自動実行される
```

### ディレクトリ構造
```
ai_commands/
├── pending/     # 実行待ち
├── running/     # 実行中
├── completed/   # 完了
└── logs/        # ログ
```

## 🎯 ベストプラクティス

1. **タスク送信時**
   - 明確な要件を記載
   - 必要に応じて優先度を指定
   - 複雑なタスクは対話型を使用

2. **品質管理**
   - 品質システムで高品質なコード生成
   - 自動的に最大3回まで改善試行

3. **自動化**
   - AI Command Executorで完全自動化
   - Git Flowで自動コミット・マージ

## 🚨 トラブルシューティング

### ワーカー確認
```bash
ps aux | grep -E "(worker|executor)"
tmux ls
```

### キューリセット
```bash
sudo rabbitmqctl purge_queue ai_tasks
```

### ログ確認
```bash
tail -f logs/*.log
tail -f ai_commands/logs/*.log
```

---

**🎊 AI Company v4.2 - 完全自律型AI開発基盤**