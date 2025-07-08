# AI Company System Architecture (TDD対応版)

## システム概要

AI Companyは、Claude APIを活用した**TDD（テスト駆動開発）ベース**の自律的タスク処理システムです。RabbitMQベースのメッセージキューアーキテクチャを採用し、複数の専門ワーカーが協調して動作します。

### 開発手法
- **メソドロジー**: Test Driven Development (TDD)
- **サイクル**: Red → Green → Refactor
- **カバレッジ目標**: 全体 80%以上、コアモジュール 95%以上

## 基本構成

### 環境情報
- **OS**: Ubuntu 24.04 LTS (WSL2)
- **Python**: 3.12.3
- **ユーザー**: aicompany (パスワード: aicompany)
- **プロジェクトルート**: `/home/aicompany/ai_co`

### 主要コンポーネント
- **メッセージキュー**: RabbitMQ
- **API**: Claude API (Anthropic)
- **通知システム**: Slack Integration
- **データベース**: SQLite3 (タスク管理用)
- **Webダッシュボード**: Task Tracker (ポート5555)
- **テストフレームワーク**: pytest, coverage
- **品質管理**: pre-commit, flake8, black, mypy

## Core基盤

### BaseWorker
すべてのワーカーの基底クラスとして、以下の共通機能を提供：
- RabbitMQ接続管理
- エラーハンドリング
- ロギング機能
- Slack通知
- 自動リトライ機構
- **テストカバレッジ**: 95%以上（TDDで実装）

### BaseManager
マネージャークラスの基底クラスとして、以下を提供：
- 共通設定管理
- ロギング
- エラーハンドリング
- **テストカバレッジ**: 95%以上（TDDで実装）

## ワーカーアーキテクチャ

### 1. PM Worker (pm_worker.py)
- **役割**: タスクの分解と他のワーカーへの振り分け
- **キュー**: `ai_tasks`, `pm_task_queue`, `result_queue`
- **主要機能**:
  - タスク分析と優先度設定
  - ワーカー選定とルーティング
  - GitHub Flow自動処理（テスト実行付き）
  - 自動スケーリング管理
  - ヘルスチェック監視

### 2. Task Worker (task_worker.py)
- **役割**: 実際のタスク処理
- **キュー**: `worker_tasks`
- **主要機能**:
  - Claude APIを使用したタスク実行
  - ファイル操作
  - コード生成

### 3. Result Worker (result_worker.py)
- **役割**: 結果の集約とSlack通知
- **キュー**: `results`, `ai_results`
- **主要機能**:
  - 結果フォーマット
  - 通知送信
  - ログ記録

### 4. Dialog Task Worker (dialog_task_worker.py)
- **役割**: 対話型タスクの処理
- **キュー**: `dialog_tasks`
- **主要機能**:
  - マルチターン対話
  - コンテキスト管理
  - 会話履歴保持

### 5. Error Intelligence Worker (error_intelligence_worker.py)
- **役割**: エラーの自動解析と修正
- **キュー**: `error_intelligence`
- **主要機能**:
  - エラーパターン認識
  - 自動修正提案
  - インシデント管理

## ディレクトリ構造

```
/home/aicompany/ai_co/
├── workers/          # ワーカー実装
│   ├── pm_worker.py
│   ├── task_worker.py
│   ├── result_worker.py
│   ├── dialog_task_worker.py
│   └── error_intelligence_worker.py
├── libs/            # 共通ライブラリ
│   ├── slack_notifier.py
│   ├── rag_manager.py
│   ├── conversation_manager.py
│   ├── github_flow_manager.py
│   └── test_manager.py
├── core/            # Core基盤
│   ├── base_worker.py
│   └── base_manager.py
├── scripts/         # スクリプト
│   ├── ai-tdd          # TDDヘルパー
│   ├── setup-tdd.sh    # TDD環境セットアップ
│   ├── generate-tdd-worker.py  # ワーカー自動生成
│   └── run-tdd-tests.sh # テスト実行
├── commands/        # AIコマンド実装
│   └── ai-test-coverage # カバレッジ確認
├── config/          # 設定ファイル
│   ├── config.json
│   └── pm_test.json
├── tests/           # テスト（TDD必須）
│   ├── unit/          # ユニットテスト
│   ├── integration/   # 統合テスト
│   ├── e2e/           # E2Eテスト
│   └── TDD_TEST_RULES.md # TDDテストルール
├── templates/       # TDDテンプレート
│   ├── tdd_worker_template.py
│   └── tdd_worker_test_template.py
├── logs/            # ログファイル
├── knowledge_base/  # ナレッジベース
├── web/             # Web UI
├── data/            # データファイル
│   └── tasks.db
├── db/              # データベース
├── .pre-commit-config.yaml  # pre-commit設定
├── test-requirements.txt    # テスト依存関係
└── pytest.ini              # pytest設定
```

## 開発プロセス（TDDベース）

### TDDサイクル
1. **Red Phase**: 失敗するテストを書く
   ```bash
   ai-tdd new FeatureName "機能要件"
   pytest tests/unit/test_feature_name.py -v  # 失敗を確認
   ```

2. **Green Phase**: 最小限の実装でテストを通す
   ```bash
   # 実装を追加
   pytest tests/unit/test_feature_name.py -v  # 成功を確認
   ```

3. **Refactor Phase**: コードを改善
   ```bash
   ai-test-coverage --html  # カバレッジ確認
   pre-commit run --all-files  # 品質チェック
   ```

### Claude CLIでのTDD
```bash
# TDD開発を明示的に依頼
 ai-send "UserManagerをTDDで開発：
 1. ユーザー登録機能
 2. メールアドレス検証
 3. 重複チェック
 まずテストから書いてください"

# 専用コマンドを使用
ai-tdd new UserManager "ユーザー管理機能"
```

## デプロイメントアーキテクチャ

### 起動プロセス
1. **環境準備**
   ```bash
   cd /home/aicompany/ai_co
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r test-requirements.txt  # TDD用
   ```

2. **TDD環境セットアップ**
   ```bash
   ./scripts/setup-tdd.sh
   pre-commit install  # コミット時の自動テスト
   ```

3. **設定**
   ```bash
   cp .env.example .env
   # .envファイルを編集して必要な環境変数を設定
   ```

4. **データベース初期化**
   ```bash
   ./scripts/setup_database.sh
   ```

5. **システム起動**
   ```bash
   ai-start
   ```

### プロセス管理
- **tmux**を使用した各ワーカーのセッション管理
- 各ワーカーは独立したプロセスとして動作
- `ai-status`コマンドで全体の稼働状況を確認

### スケーリング機構
- PM Workerによる自動スケーリング
- キュー長とCPU使用率に基づく動的調整
- 最小1、最大10ワーカーまでのスケール

## セキュリティアーキテクチャ

### 認証・認可
- 環境変数による秘密情報管理（.env）
- APIキーの安全な保管
- Slackトークンの保護

### データ保護
- ローカルファイルシステムでの処理
- センシティブ情報のログ除外
- Git履歴への秘密情報混入防止

## パフォーマンス特性

### システム指標
- タスク処理時間: 平均30秒
- 同時処理数: 最大10タスク
- メモリ使用量: 約500MB/ワーカー
- エラー率: < 1%

### 最適化戦略
- キューベースの非同期処理
- ワーカープールによる並列処理
- 自動リトライによる信頼性向上
- ヘルスチェックによる異常検知

## 監視とロギング

### ログ管理
- 各ワーカーごとの個別ログファイル
- 統合ログビューア（ai-logs）
- リアルタイム監視（ai-monitor）

### メトリクス
- システム統計（ai-stats）
- 品質メトリクス（ai-metrics）
- キュー状態監視（ai-queue-status）

## 障害復旧

### 自動復旧機能
- ワーカーの自動再起動
- Dead Letter Queueによるエラー処理
- タスクの自動リトライ

### 手動復旧手順
1. システム停止: `ai-stop`
2. ログ確認: `ai-logs`
3. キュー状態確認: `ai-queue-status`
4. システム再起動: `ai-restart`

## 品質保証（TDD）

### テストカバレッジ目標
| コンポーネント | 最小 | 推奨 | TDD目標 |
|--------------|-----|------|--------|
| Core (BaseWorker/Manager) | 90% | 95% | 100% |
| Workers | 80% | 90% | 95% |
| Libs/Managers | 80% | 90% | 95% |
| Commands | 70% | 85% | 90% |
| 全体 | 80% | 90% | 95% |

### 自動品質チェック
- **pre-commitフック**: コミット時に自動テスト
- **GitHub Actions**: PR時に自動テスト・カバレッジチェック
- **コード品質**: black, flake8, mypyによる自動チェック

## 更新履歴

### v5.4 (2025-01-06)
- TDD（テスト駆動開発）全面導入
- pre-commitフック設定
- ai-tddコマンド追加
- BaseWorker/BaseManagerテスト強化（95%以上）
- TDDワークフロー文書化
- Claude CLI用TDDガイド作成

### v5.3 (2025-01-05)
- Task Tracker システム追加
- メモリ急上昇問題の修正
- 68個のAIコマンド体系整備
- 大規模クリーンアップ実施