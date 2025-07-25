# 🤖 Auto Issue Processor 完全ガイド

## 概要

Auto Issue ProcessorはGitHubのIssueを自動的に処理し、PRを作成するシステムです。重複PR防止機能を備え、Elder Flowと4賢者システムと統合されています。

## ✨ 主要機能

### 1. 重複PR防止機能 (2025/7/20実装)
- 既存のPRを自動検出
- オープン・クローズ両方のPRをチェック
- Issueへの自動コメント投稿

### 2. タイムスタンプ付きブランチ名
- 環境変数で制御可能
- 複数の試行をサポート

### 3. 4賢者システム統合
- ナレッジ賢者: 過去の類似事例検索
- タスク賢者: 実行計画立案
- インシデント賢者: リスク評価
- RAG賢者: 最適解探索

## 🔧 設定

### 必須環境変数
```bash
export GITHUB_TOKEN="your-github-token"
export GITHUB_REPO_OWNER="ext-maru"  # デフォルト
export GITHUB_REPO_NAME="ai-co"      # デフォルト
```

### オプション環境変数
```bash
# タイムスタンプ付きブランチ名を使用
export AUTO_ISSUE_USE_TIMESTAMP="true"
```

## 📋 使用方法

### 1. スキャンモード
処理可能なIssueを検索します：

```python
import asyncio
from libs.integrations.github.auto_issue_processor import AutoIssueProcessor

async def scan_issues():
    processor = AutoIssueProcessor()
    result = await processor.process_request({"mode": "scan"})
    print(result)

asyncio.run(scan_issues())
```

### 2. 処理モード
実際にIssueを処理してPRを作成します：

```python
async def process_issue():
    processor = AutoIssueProcessor()
    result = await processor.process_request({"mode": "process"})
    print(result)

asyncio.run(process_issue())
```

### 3. ドライランモード
特定のIssueの処理可能性を確認します：

```python
async def dry_run_issue(issue_number):
    processor = AutoIssueProcessor()
    result = await processor.process_request({
        "mode": "dry_run",
        "issue_number": issue_number
    })
    print(result)

asyncio.run(dry_run_issue(25))
```

## 🔍 重複PR検出の仕組み

### 検出パターン
以下のパターンでIssue番号を検索します：
- `#issue_number`
- `Closes #issue_number`
- `Fixes #issue_number`
- `Resolves #issue_number`
- `issue-issue_number`
- `Issue #issue_number`

### 検索範囲
1. すべてのオープンPR
2. 最近の20件のクローズドPR

## 📊 複雑度評価

### 評価基準
- **パターンマッチ**: typo、documentation、comment等の単純なパターン
- **ラベル評価**: good first issue、bug等のラベル
- **セキュリティチェック**: security、auth、token等のキーワード

### 処理可能条件
- 複雑度スコア < 0.7
- 優先度: critical、high、medium

## 🚦 処理制限

- **1時間あたり**: 最大10 Issue
- **同時実行**: 1件まで
- **クールダウン**: 5分

## 🧪 テスト

### ユニットテスト（モック使用）
```bash
python3 tests/test_auto_issue_processor_duplicate_pr.py
```

### 統合テスト（実際のAPI使用）
```bash
python3 tests/integration/test_auto_issue_processor_real.py
```

## 📝 ログ

処理ログは以下に保存されます：
```
logs/auto_issue_processing.json
```

## 🔧 トラブルシューティング

### PRが重複して作成される
- `AUTO_ISSUE_USE_TIMESTAMP=true`を設定してタイムスタンプ付きブランチ名を使用
- 既存PRの検出が正常に動作しているか確認

### 処理が実行されない
- GitHub TOKENが正しく設定されているか確認
- 処理制限（1時間10件）に達していないか確認
- Issueの複雑度スコアが0.7未満か確認

## 🎯 今後の改善点

1. **非同期処理の最適化**
2. **より詳細な複雑度評価**
3. **自動修正機能の実装**
4. **Webhookによるリアルタイム処理**

---
**Last Updated**: 2025/7/20
**Author**: Claude Elder (クロードエルダー)