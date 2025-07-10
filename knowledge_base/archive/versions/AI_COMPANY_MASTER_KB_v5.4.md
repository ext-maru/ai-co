# Elders Guild Master Knowledge Base v5.4

## 🏢 システム概要

Elders Guildは、Claude APIを活用した**TDD駆動**の自律的タスク処理システムです。

### 基本構成
- **環境**: Ubuntu 24.04 LTS (WSL2)
- **Python**: 3.12.3
- **ユーザー**: aicompany (パスワード: aicompany)
- **プロジェクトルート**: `/home/aicompany/ai_co`
- **開発手法**: Test Driven Development (TDD)

## 🧪 TDD開発フロー

### 基本原則: Red → Green → Refactor
```bash
# 1. Red: テストを先に書く（失敗）
ai-tdd new FeatureName "機能の要件"

# 2. Green: 最小限の実装でテストを通す
pytest tests/unit/test_feature_name.py -v

# 3. Refactor: コードを改善
ai-test-coverage --html
```

### Claude CLIでのTDD開発
```bash
# TDD専用コマンド
ai-tdd new EmailValidator "メールアドレス検証"
ai-tdd test libs/existing_module.py
ai-tdd coverage workers
ai-tdd session "新機能の設計"

# 直接依頼する場合
ai-send "DataProcessorをTDDで開発してください。まずテストから"
```

## 🔧 Core基盤

### BaseWorker
すべてのワーカーの基底クラス。共通機能を提供：
- RabbitMQ接続管理
- エラーハンドリング
- ロギング
- Slack通知
- 自動リトライ
- **テストカバレッジ**: 95%以上（TDD実装済み）

### BaseManager
マネージャークラスの基底クラス：
- 共通設定管理
- ロギング
- エラーハンドリング
- **テストカバレッジ**: 95%以上（TDD実装済み）

## 🤖 ワーカー一覧

### 1. PM Worker (pm_worker.py)
- **役割**: タスクの分解と他のワーカーへの振り分け
- **キュー**: `ai_tasks`
- **機能**: タスク分析、優先度設定、ワーカー選定
- **テスト**: `tests/unit/test_pm_worker.py`

### 2. Task Worker (task_worker.py)
- **役割**: 実際のタスク処理
- **キュー**: `worker_tasks`
- **機能**: Claude APIを使用したタスク実行
- **テスト**: `tests/unit/test_task_worker.py`

### 3. Result Worker (result_worker.py)
- **役割**: 結果の集約とSlack通知
- **キュー**: `results`
- **機能**: 結果フォーマット、通知送信
- **テスト**: `tests/unit/test_result_worker.py`

### 4. Dialog Task Worker (dialog_task_worker.py)
- **役割**: 対話型タスクの処理
- **キュー**: `dialog_tasks`
- **機能**: マルチターン対話、コンテキスト管理
- **テスト**: `tests/unit/test_dialog_task_worker.py`

### 5. Error Intelligence Worker (error_intelligence_worker.py)
- **役割**: エラーの自動解析と修正
- **キュー**: `error_intelligence`
- **機能**: エラーパターン認識、自動修正提案
- **テスト**: `tests/unit/test_error_intelligence_worker.py`

## 📦 ライブラリ

### SlackNotifier
```python
from libs.slack_notifier import SlackNotifier
notifier = SlackNotifier()
notifier.send_message("メッセージ")
```
**テスト**: `tests/unit/test_managers/test_slack_notifier.py`

### RAGManager
```python
from libs.rag_manager import RAGManager
rag = RAGManager()
rag.add_knowledge("知識", metadata={})
results = rag.search("クエリ")
```
**テスト**: `tests/unit/test_managers/test_rag_manager.py`

### ConversationManager
```python
from libs.conversation_manager import ConversationManager
cm = ConversationManager()
cm.add_message(conv_id, role, content)
history = cm.get_conversation(conv_id)
```
**テスト**: `tests/unit/test_managers/test_conversation_manager.py`

## 🔄 GitHub Flow運用（TDD統合）

### ブランチ戦略（GitHub Flow + TDD）
- `main`: メインブランチ（テスト必須・カバレッジ80%以上）
- `feature/*`: 機能開発・バグ修正ブランチ（TDDで開発）

### 開発フロー
1. **feature/ブランチ作成**
   ```bash
   gf feature my-feature
   ```

2. **TDDで開発**
   ```bash
   ai-tdd new MyFeature "機能要件"
   ```

3. **コミット（pre-commitフック自動実行）**
   ```bash
   git commit -m "feat: 新機能追加"
   ```

4. **プルリクエスト作成**
   ```bash
   gf pr
   ```

### コミット規約
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, perf, test, chore

## 🛠️ コマンド一覧

### TDD開発コマンド
```bash
# TDD専用
ai-tdd new <feature> <requirements>  # 新機能をTDDで開発
ai-tdd test <file>                   # 既存コードにテスト追加
ai-tdd coverage <module>             # カバレッジ分析・改善
ai-tdd session <topic>               # 対話型TDDセッション

# テスト実行
./scripts/run-tdd-tests.sh unit      # ユニットテスト
./scripts/run-tdd-tests.sh watch     # 監視モード
ai-test-coverage --html              # カバレッジレポート

# ワーカー生成（TDDテンプレート付き）
./scripts/generate-tdd-worker.py DataProcessor data
```

### AI Command Executor
```bash
# タスク送信（TDDで開発されたワーカーが処理）
ai-send "タスクの内容"

# ログ確認
ai-logs

# ステータス確認
ai-status

# TODO管理
ai-todo create "リスト名"
ai-todo add "リスト名" "タスク" bash "コマンド"
ai-todo run "リスト名"
```

### システム管理
```bash
# 起動/停止
ai-start
ai-stop

# GitHub Flow（TDD統合）
gf feature <name>
gf fix <name>
gf commit -m "message"  # pre-commitでテスト自動実行
```

## 📁 ディレクトリ構造

```
/home/aicompany/ai_co/
├── workers/          # ワーカー実装
├── libs/            # 共通ライブラリ
├── core/            # Core基盤
├── scripts/         # スクリプト
│   ├── ai-tdd       # TDDヘルパー
│   ├── setup-tdd.sh # TDD環境セットアップ
│   └── generate-tdd-worker.py # ワーカー生成
├── config/          # 設定ファイル
├── tests/           # テスト（TDD必須）
│   ├── unit/        # ユニットテスト
│   ├── integration/ # 統合テスト
│   └── e2e/         # E2Eテスト
├── logs/            # ログ
├── knowledge_base/  # ナレッジベース
├── web/             # Web UI
├── templates/       # TDDテンプレート
│   ├── tdd_worker_template.py
│   └── tdd_worker_test_template.py
├── docs/            # ドキュメント
│   ├── TDD_WORKFLOW.md
│   └── TDD_WITH_CLAUDE_CLI.md
└── db/              # データベース
```

## 🔐 設定管理

### 環境変数管理ルール
**重要**: 環境変数は必ず `.env` ファイルに集約し、`libs/env_config.py` 経由でアクセスすること。

```python
# 正しい使用方法
from libs.env_config import get_config
config = get_config()
api_key = config.ANTHROPIC_API_KEY
```

### TDD設定
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest tests/unit -x --tb=short
        language: system
        stages: [commit]
```

### 環境変数 (.env)
```bash
# .env.template をコピーして作成
ANTHROPIC_API_KEY=your_key
SLACK_BOT_TOKEN=your_token
SLACK_CHANNEL=your_channel
RABBITMQ_HOST=localhost

# TDD関連
AI_TDD_ENABLED=true
AI_TDD_COVERAGE_THRESHOLD=80
```

### config.json
```json
{
  "workers": {
    "timeout": 300,
    "retry_count": 3,
    "retry_delay": 60
  },
  "claude": {
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 4096
  },
  "slack": {
    "enabled": true,
    "rate_limit": 1
  },
  "tdd": {
    "enabled": true,
    "coverage_threshold": 80,
    "pre_commit_test": true
  }
}
```

## 🚀 デプロイ手順（TDD対応）

1. 環境準備
```bash
cd /home/aicompany/ai_co
source venv/bin/activate
pip install -r requirements.txt
pip install -r test-requirements.txt  # TDD用
```

2. TDD環境セットアップ
```bash
./scripts/setup-tdd.sh
```

3. pre-commitフック設定
```bash
pre-commit install
```

4. データベース初期化
```bash
./scripts/setup_database.sh
```

5. 起動
```bash
ai-start
```

## 🐛 トラブルシューティング

### TDD関連の問題

#### テストが見つからない
```bash
# pytestの設定確認
cat pytest.ini

# テストディレクトリ確認
ls -la tests/unit/
```

#### カバレッジが低い
```bash
# カバレッジ詳細確認
ai-test-coverage --html

# 未カバー部分の特定
coverage report -m
```

#### pre-commitが失敗
```bash
# 手動でpre-commit実行
pre-commit run --all-files

# 特定のフックをスキップ
SKIP=pytest-check git commit -m "message"
```

### RabbitMQ接続エラー
```bash
sudo systemctl restart rabbitmq-server
```

### Python依存関係エラー
```bash
pip install -r requirements.txt --force-reinstall
pip install -r test-requirements.txt --force-reinstall
```

## 🎯 AIコマンド完全ガイド（TDD統合）

### ✅ コア機能（TDDテスト済み）
- `ai-status`: システム状態確認
- `ai-send`: タスク送信
- `ai-start/ai-stop`: システム起動/停止
- `ai-logs`: ログ確認
- `ai-help`: ヘルプ表示
- `ai-version`: バージョン表示
- `ai-restart`: システム再起動

### 🧪 TDD開発機能（新規追加）
- `ai-tdd`: TDD開発ヘルパー
- `ai-test-coverage`: カバレッジ確認・可視化
- `./scripts/generate-tdd-worker.py`: ワーカー自動生成
- `./scripts/run-tdd-tests.sh`: テスト実行

### 🔧 開発・管理機能
- `ai-todo`: ToDoリスト管理
- `ai-rag-search`: RAG検索
- `ai-workers`: ワーカー状態確認
- `ai-tasks`: タスク履歴確認
- `ai-scale`: オートスケーリング管理
- `ai-git`: Git操作管理（pre-commit統合）

## 📊 パフォーマンス指標

### テスト指標
- ユニットテスト実行時間: < 30秒
- 統合テスト実行時間: < 2分
- テストカバレッジ目標: 80%以上
- コアモジュールカバレッジ: 95%以上

### システム指標
- タスク処理時間: 平均30秒
- 同時処理数: 最大10タスク
- メモリ使用量: 約500MB/ワーカー
- エラー率: < 1%

## 📋 Task Tracker システム

### 概要
簡易Redmine風のタスク管理システム。全てのAIタスクを追跡・管理。**TDDで開発されたワーカーが処理**。

### アクセス方法
- **Webダッシュボード**: http://localhost:5555
- **CLIコマンド**: `./scripts/task`

## 🔄 更新履歴

### v5.4 (2025-01-06)
- TDD（テスト駆動開発）全面導入
- pre-commitフック設定
- ai-tddコマンド追加
- BaseWorker/BaseManagerテスト強化
- TDDワークフロー文書化
- Claude CLI用TDDガイド作成

### v5.3 (2025-01-05)
- Task Tracker システム追加
- メモリ急上昇問題の修正
- 68個のAIコマンド体系整備
- 大規模クリーンアップ実施