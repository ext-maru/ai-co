# AI Company ディレクトリ構造

## 概要
AI Companyのコードベースは機能別に整理された構造になっています。

```
/root/ai_co/
├── core/              # コアシステム
│   ├── workers/       # ワーカー群
│   ├── queue/         # キュー管理
│   └── monitoring/    # 監視・ヘルスチェック
├── features/          # 機能別モジュール
│   ├── ai/           # AI処理（RAG、自己進化）
│   ├── conversation/  # 会話管理
│   ├── database/     # データベース関連
│   ├── notification/ # 通知（Slack、Email）
│   └── integration/  # 外部連携（GitHub等）
├── utils/            # ユーティリティ
│   ├── scripts/      # 実行スクリプト
│   └── helpers/      # ヘルパー関数
├── tests/            # テストコード
├── config/           # 設定ファイル
├── data/             # データストレージ
├── db/               # データベースファイル
├── output/           # 生成された出力
├── logs/             # ログファイル
└── venv/             # Python仮想環境
```

## ディレクトリ詳細

### core/ - コアシステム
システムの中核となるコンポーネント

#### core/workers/
- `pm_worker.py` - プロジェクトマネージャーワーカー
- `task_worker.py` - タスク実行ワーカー  
- `result_worker.py` - 結果処理ワーカー
- `dialog_*.py` - 対話系ワーカー

#### core/monitoring/
- `health_checker.py` - ヘルスチェック
- `worker_monitor.py` - ワーカー監視
- `worker_controller.py` - ワーカー制御
- `scaling_policy.py` - スケーリングポリシー

### features/ - 機能モジュール

#### features/ai/
- `rag_manager.py` - RAG（Retrieval-Augmented Generation）管理
- `self_evolution_manager.py` - 自己進化機能
- `ai_learning_interface.py` - AI学習インターフェース
- `github_aware_rag.py` - GitHub連携RAG

#### features/conversation/
- `conversation_manager.py` - 会話管理
- `conversation_db.py` - 会話データベース
- `conversation_recovery.py` - 会話復旧
- `conversation_search.py` - 会話検索
- `conversation_summarizer.py` - 会話要約

#### features/database/
- `database_manager.py` - データベース管理
- `task_history_db.py` - タスク履歴DB

#### features/notification/
- `slack_notifier.py` - Slack通知（v1）
- `slack_notifier_v2.py` - Slack通知（拡張版）

#### features/integration/
- `github_integration.py` - GitHub統合
- `ai_git_assistant.py` - AI Git アシスタント

### utils/ - ユーティリティ

#### utils/scripts/
実行可能なスクリプト群
- `start_company.sh` - システム起動
- `status.sh` - ステータス確認
- `send_task.py` - タスク送信
- `pm_cli.py` - PMコマンドライン

### tests/
すべてのテストコード
- `test_*.py` - 各機能のテスト

## 重要なファイル

### 設定ファイル（config/）
- `system.conf` - システム全体の設定
- `slack.conf` - Slack通知設定
- `database.conf` - データベース設定
- `github.conf` - GitHub連携設定

### ナレッジベース
- `KNOWLEDGE_BASE.md` - バグ修正履歴と解決方法

## シンボリックリンク（後方互換性）
- `scripts` → `utils/scripts`
- `workers` → `core/workers`

## 使用方法

### システム起動
```bash
bash utils/scripts/start_company.sh
```

### タスク送信
```bash
python3 utils/scripts/send_task.py
```

### ログ確認
```bash
tail -f logs/*.log
```

---
最終更新: 2025-07-05