# 統一Auto Issue Processor アーキテクチャ

## 概要

統一Auto Issue Processorは、5つの異なる実装を1つに統合した、一貫性のある自動Issue処理システムです。

## 🏗️ アーキテクチャ

```
libs/auto_issue_processor/
├── __init__.py                 # パッケージエントリーポイント
├── core/                       # コア機能
│   ├── __init__.py
│   ├── processor.py            # メインプロセッサー
│   └── config.py               # 設定管理
├── features/                   # 機能モジュール
│   ├── __init__.py
│   ├── error_recovery.py       # エラーリカバリー
│   ├── pr_creation.py          # PR作成
│   ├── parallel_processing.py  # 並列処理
│   └── four_sages.py           # 4賢者統合
└── utils/                      # ユーティリティ
    ├── __init__.py
    └── locking.py              # プロセスロック
```

## 🔧 主要コンポーネント

### 1. Core Processor (`core/processor.py`)

統一プロセッサーは以下の機能を提供：

```python
class AutoIssueProcessor:
    """統一Auto Issue Processor
    
    統合された機能:
    - 基本的なIssue処理（旧auto_issue_processor.py）
    - 堅牢なエラーハンドリング（旧auto_issue_processor_enhanced.py）
    - PR作成機能（旧enhanced_auto_issue_processor.py）
    - 並列処理最適化（旧optimized_auto_issue_processor.py）
    - プロセス間ロック（新規）
    """
```

### 2. Configuration Management (`core/config.py`)

統一設定システム：

- YAML設定ファイルサポート
- 環境変数サポート
- 機能フラグによる制御
- 設定の妥当性検証

```yaml
# configs/auto_issue_processor.yaml
features:
  pr_creation: true
  error_recovery: true
  parallel_processing: false
  four_sages_integration: true
```

### 3. Process Locking (`utils/locking.py`)

複数プロセス間の競合を防ぐロック機構：

- ファイルベースロック（デフォルト）
- メモリベースロック（単一プロセス用）
- Redisベースロック（将来実装）

```python
async with lock.lock_context("issue_123"):
    # ロックされた処理
    await process_issue(issue)
```

### 4. Feature Modules

#### Error Recovery (`features/error_recovery.py`)

- リトライ戦略（指数バックオフ）
- フォールバック戦略
- 部分的リカバリー
- エラーパターン学習

#### PR Creation (`features/pr_creation.py`)

- 自動ブランチ作成
- ファイルコミット
- PR作成とラベル付け
- Issue連携

#### Parallel Processing (`features/parallel_processing.py`)

- ワーカープール管理
- リソース監視
- バッチ処理
- 依存関係解決

#### Four Sages Integration (`features/four_sages.py`)

- ナレッジ賢者：パターン認識と学習
- タスク賢者：優先順位付けと実行管理
- インシデント賢者：リスク検出と監視
- RAG賢者：情報検索と統合

## 📋 使用方法

### 基本的な使用

```python
from libs.auto_issue_processor import AutoIssueProcessor, ProcessorConfig

# 設定をロード
config = ProcessorConfig.load("configs/auto_issue_processor.yaml")

# プロセッサーを初期化
processor = AutoIssueProcessor(config)

# Issueを処理
result = await processor.process_issues([123, 124, 125])
```

### CLI使用

```bash
# 特定のIssueを処理
python3 -m libs.auto_issue_processor.core.processor 123 124

# ドライランモード
python3 -m libs.auto_issue_processor.core.processor --dry-run

# 並列処理を有効化
python3 -m libs.auto_issue_processor.core.processor --parallel
```

## 🔄 処理フロー

1. **Issue選択**
   - 指定されたIssue番号、または優先度順に自動選択
   - スキップラベルと必須ラベルのチェック

2. **ロック取得**
   - プロセス間ロックで重複処理を防止
   - TTL付きでデッドロック対策

3. **4賢者分析**（有効時）
   - 既知パターンの照合
   - リスク評価
   - 処理推奨事項

4. **メイン処理**
   - Issue内容の解析
   - 実装計画の生成
   - コード生成
   - テスト生成

5. **エラーリカバリー**（エラー時）
   - リトライ
   - フォールバック
   - 部分的成功の保存

6. **PR作成**（有効時）
   - ブランチ作成
   - 変更のコミット
   - PR作成

7. **後処理**
   - 成功コメントの追加
   - 統計情報の更新
   - ロックの解放

## 📊 モニタリング

### ログ

```
logs/auto_issue_processor.log     # メインログ
logs/fatal_errors/                 # 致命的エラーレポート
```

### 統計情報

```json
{
  "processed": 10,
  "success": 8,
  "failed": 1,
  "skipped": 1,
  "average_time_per_issue": 45.2,
  "peak_memory_usage": 68.5
}
```

## 🚀 パフォーマンス最適化

### 並列処理

- 最大ワーカー数の動的調整
- リソースベースのスケーリング
- バッチ処理

### メモリ管理

- ストリーミング処理
- ガベージコレクション最適化
- メモリリーク検出

## 🔒 セキュリティ

- GitHubトークンの安全な管理
- プロセス間通信の保護
- ロック情報の暗号化（将来）

## 🐛 トラブルシューティング

### ロックエラー

```bash
# 期限切れロックのクリーンアップ
rm -rf .issue_locks/*.lock
```

### 設定エラー

```python
# 設定の検証
config = ProcessorConfig.load()
if not config.validate():
    print("Configuration errors found")
```

### デバッグモード

```bash
# 詳細ログを有効化
export AUTO_ISSUE_PROCESSOR_LOG_LEVEL=DEBUG
```

## 📚 関連ドキュメント

- [移行ガイド](./MIGRATION_GUIDE.md)
- [API リファレンス](./API_REFERENCE.md)
- [設定リファレンス](./CONFIGURATION_REFERENCE.md)