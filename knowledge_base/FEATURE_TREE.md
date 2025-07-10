# Elders Guild 機能一覧ツリー

最終更新: 2025-01-06

## 概要
Elders Guildシステムの全機能を階層的に整理したリファレンスです。新機能追加時は必ず更新してください。

## 機能ツリー

```
Elders Guild System
├── 🤖 ワーカーシステム
│   ├── PM Worker (タスク管理・振り分け)
│   │   ├── タスク分析・優先度設定
│   │   ├── ワーカー選定・ルーティング
│   │   ├── GitHub Flow自動処理
│   │   ├── 自動スケーリング管理
│   │   └── ヘルスチェック監視
│   ├── Task Worker (タスク実行)
│   │   ├── Claude API連携
│   │   ├── ファイル操作
│   │   └── コード生成
│   ├── Result Worker (結果処理)
│   │   ├── 結果集約
│   │   ├── Slack通知
│   │   └── ログ記録
│   ├── Dialog Task Worker (対話処理)
│   │   ├── マルチターン対話
│   │   ├── コンテキスト管理
│   │   └── 会話履歴保持
│   └── Error Intelligence Worker (エラー解析)
│       ├── エラーパターン認識
│       ├── 自動修正提案
│       └── インシデント管理
│
├── 🧪 TDD開発ツール
│   ├── ai-tdd (TDD開発支援)
│   │   ├── new (新機能TDD開発)
│   │   ├── test (テスト追加)
│   │   ├── coverage (カバレッジ分析)
│   │   └── session (対話型TDD)
│   ├── ai-test-coverage (カバレッジ確認)
│   ├── generate-tdd-worker.py (ワーカー自動生成)
│   └── pre-commitフック (自動品質チェック)
│
├── 🛠️ AIコマンド (68個)
│   ├── コア機能
│   │   ├── ai-status (システム状態)
│   │   ├── ai-send (タスク送信)
│   │   ├── ai-start/stop/restart
│   │   ├── ai-logs (ログ確認)
│   │   ├── ai-help (ヘルプ)
│   │   └── ai-version
│   ├── 開発・管理
│   │   ├── ai-todo (ToDoリスト管理)
│   │   ├── ai-rag-search (RAG検索)
│   │   ├── ai-workers (ワーカー状態)
│   │   ├── ai-tasks (タスク履歴)
│   │   ├── ai-scale (スケーリング)
│   │   └── ai-git (Git操作)
│   ├── 対話・通信
│   │   ├── ai-code (コード生成)
│   │   ├── ai-dialog (対話開始)
│   │   ├── ai-reply (応答送信)
│   │   └── ai-slack (Slack統合)
│   ├── 設定・監視
│   │   ├── ai-config (設定確認)
│   │   ├── ai-monitor (リアルタイム監視)
│   │   ├── ai-metrics (統計情報)
│   │   └── ai-stats (システム統計)
│   └── 高度な機能
│       ├── ai-worker-* (ワーカー管理)
│       ├── ai-task-* (タスク管理)
│       ├── ai-queue* (キュー管理)
│       └── ai-dlq (Dead Letter Queue)
│
├── 📚 ライブラリ
│   ├── SlackNotifier (Slack通知)
│   ├── RAGManager (ナレッジベース管理)
│   ├── ConversationManager (対話管理)
│   ├── GitHubFlowManager (Git操作)
│   ├── TestManager (テスト実行)
│   └── CommitMessageGenerator (コミットメッセージ生成)
│
├── 🌐 Web機能
│   └── Task Tracker (ポート5555)
│       ├── カンバン風タスク表示
│       ├── ステータス管理
│       ├── 優先度システム
│       └── タスク履歴
│
├── 💾 データ管理
│   ├── SQLite DB (tasks.db)
│   │   ├── tasksテーブル
│   │   └── task_logsテーブル
│   ├── ナレッジベース
│   │   ├── Markdownドキュメント
│   │   ├── JSONデータ
│   │   └── ベクトル埋め込み
│   └── ログファイル
│       ├── ワーカー別ログ
│       └── システムログ
│
├── 🔧 Core基盤
│   ├── BaseWorker (ワーカー基底クラス)
│   │   ├── RabbitMQ接続管理
│   │   ├── エラーハンドリング
│   │   ├── ロギング
│   │   ├── Slack通知
│   │   └── 自動リトライ
│   └── BaseManager (マネージャー基底クラス)
│       ├── 共通設定管理
│       ├── ロギング
│       └── エラーハンドリング
│
└── ⚙️ システム機能
    ├── メッセージキュー (RabbitMQ)
    │   ├── ai_tasks
    │   ├── worker_tasks
    │   ├── results
    │   ├── dialog_tasks
    │   └── error_intelligence
    ├── 外部API連携
    │   ├── Claude API
    │   └── Slack API
    └── 自動化機能
        ├── 自動スケーリング
        ├── ヘルスチェック
        ├── エラー自動修正
        └── GitHub Flow自動化
```

## 更新ルール

### 更新が必要なタイミング
- 新しいワーカーの追加時
- 新しいAIコマンドの追加時
- 新しいライブラリの追加時
- 既存機能の大幅な変更時
- システムアーキテクチャの変更時

### 更新方法
1. 変更内容を上記ツリーに反映
2. 最終更新日を更新
3. 必要に応じて関連ドキュメントも更新:
   - `system_architecture.md`
   - `component_catalog.md`
   - `AI_COMPANY_MASTER_KB_v5.3.md`

### 自動更新トリガー
- `ai-knowledge consolidate`実行時
- システムバージョンアップ時
- 月次メンテナンス時

## 参照
- [システムアーキテクチャ](./system_architecture.md)
- [コンポーネントカタログ](./component_catalog.md)
- [マスターナレッジベース](./AI_COMPANY_MASTER_KB_v5.3.md)