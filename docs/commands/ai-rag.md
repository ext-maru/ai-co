# ai-rag コマンド

## 概要

`ai-rag`は、RAG（Retrieval-Augmented Generation: 検索拡張生成）を管理するコマンドです。🔍 RAGエルダー（Search Elder）との統合インターフェースとして、知識ベースの検索、分析、学習機能を提供します。

## 使用方法

```bash
ai-rag <subcommand> [OPTIONS]
```

## サブコマンド

### search - 知識ベース検索

知識ベースから関連情報を検索します。

```bash
ai-rag search <query> [OPTIONS]
```

**オプション:**
- `--limit, -l`: 結果数制限（デフォルト: 5）
- `--threshold, -t`: 類似度閾値 0.0-1.0（デフォルト: 0.7）
- `--format, -f`: 出力形式 [json|text]（デフォルト: text）

**例:**
```bash
# エラー処理に関する情報を検索
ai-rag search "エラー処理"

# JSON形式で上位10件を取得
ai-rag search "機械学習" --limit 10 --format json

# 高い類似度のみ表示
ai-rag search "デバッグ方法" --threshold 0.8
```

### analyze - コンテキスト分析

テキストのコンテキストを分析し、主要トピック、エンティティ、感情などを抽出します。

```bash
ai-rag analyze <context> [OPTIONS]
```

**オプション:**
- `--depth, -d`: 分析深度（デフォルト: 3）

**例:**
```bash
# コードの分析
ai-rag analyze "このPythonコードはファイル処理を行い、エラーハンドリングも実装しています"

# 深い分析
ai-rag analyze "複雑なシステムアーキテクチャの説明文..." --depth 5
```

### enhance - プロンプト強化

プロンプトにコンテキストを追加して強化します。

```bash
ai-rag enhance <prompt> [OPTIONS]
```

**オプション:**
- `--model, -m`: 使用モデル（デフォルト: claude-sonnet-4-20250514）

**例:**
```bash
# シンプルなプロンプトを強化
ai-rag enhance "Pythonでファイルを読み込む方法"

# 特定のモデルを使用
ai-rag enhance "機械学習モデルの評価" --model claude-opus-3
```

### summary - 要約生成

長いテキストやファイルを要約します。

```bash
ai-rag summary <text|file_path> [OPTIONS]
```

**オプション:**
- `--length, -l`: 要約文字数（デフォルト: 100）

**例:**
```bash
# テキストの要約
ai-rag summary "長い文章がここに入ります..."

# ファイルの要約
ai-rag summary /path/to/document.txt --length 200
```

### learn - 新しい知識を学習

新しい知識を知識ベースに追加します。

```bash
ai-rag learn <knowledge|file_path> [OPTIONS]
```

**オプション:**
- `--category, -c`: 知識カテゴリ
- `--tags`: タグリスト（スペース区切り）

**例:**
```bash
# 新しい知識を追加
ai-rag learn "Pythonの新機能: match文は3.10から利用可能" --category python --tags python syntax

# ファイルから学習
ai-rag learn /path/to/knowledge.md --category documentation
```

### status - RAGエルダーステータス

RAGシステムの現在の状態と統計情報を表示します。

```bash
ai-rag status
```

**出力例:**
```
🔍 RAGエルダーステータス
========================================
役割: 情報検索と最適解探索
状態: Active

知識ベース統計:
  総エントリ数: 1,234
  カテゴリ数: 15

カテゴリ別:
  - programming: 456件
  - ai/ml: 234件
  - documentation: 189件
  - errors: 123件
  - best-practices: 98件

機能:
  ✓ セマンティック検索
  ✓ コンテキスト分析
  ✓ プロンプト強化
  ✓ 要約生成
  ✓ 継続学習
```

### optimize - 検索最適化

検索インデックスを最適化して性能を向上させます。

```bash
ai-rag optimize [OPTIONS]
```

**オプション:**
- `--rebuild-index`: インデックスを完全に再構築

**例:**
```bash
# インデックスの再構築
ai-rag optimize --rebuild-index
```

## 知識ベースの構造

知識は以下の形式でJSON形式で保存されます：

```json
{
  "content": "知識の内容",
  "category": "カテゴリ名",
  "tags": ["タグ1", "タグ2"],
  "learned_at": "2025-07-06T12:00:00",
  "source": "ai-rag command"
}
```

## 統合機能

### エルダーズシステムとの連携

`ai-rag`コマンドは、Elders Guildのエルダーズ（4賢者）システムの一部として動作します：

- **🔍 RAGエルダー**: 情報検索と最適解探索を担当
- **📚 ナレッジエルダー**: 学習した知識の永続化
- **📋 タスクエルダー**: 検索タスクの優先順位付け
- **🚨 インシデントエルダー**: 検索エラーの監視と復旧

### 高度な検索機能

1. **セマンティック検索**: 意味的に関連する情報を検索
2. **多言語対応**: 日本語、英語、中国語など複数言語に対応
3. **コンテキスト認識**: 検索クエリの文脈を理解
4. **類似度ランキング**: 関連度の高い順に結果を表示

## 使用例

### 開発者向けワークフロー

```bash
# 1. エラーに関する情報を検索
ai-rag search "TypeError: 'NoneType' object is not subscriptable"

# 2. エラーコンテキストを分析
ai-rag analyze "関数の戻り値がNoneの場合にこのエラーが発生します"

# 3. 解決策を知識ベースに追加
ai-rag learn "TypeErrorを防ぐには、Noneチェックを追加: if result is not None:" \
  --category errors --tags python error-handling

# 4. ステータス確認
ai-rag status
```

### ドキュメント作成ワークフロー

```bash
# 1. 関連ドキュメントを検索
ai-rag search "APIドキュメントの書き方"

# 2. 長い仕様書を要約
ai-rag summary specification.md --length 300

# 3. プロンプトを強化してより詳細な説明を生成
ai-rag enhance "REST APIのベストプラクティスについて説明"
```

## トラブルシューティング

### マネージャー初期化エラー

RAGマネージャーの初期化に失敗した場合でも、基本的な機能は動作します。以下を確認してください：

1. 必要な依存関係がインストールされているか
2. 知識ベースディレクトリへのアクセス権限があるか
3. ディスク容量が十分にあるか

### 検索結果が見つからない

- 類似度閾値を下げてみる: `--threshold 0.5`
- 検索クエリを別の表現で試す
- `ai-rag status`で知識ベースにデータがあるか確認

### パフォーマンスの問題

- `ai-rag optimize --rebuild-index`でインデックスを再構築
- 大量のデータがある場合は、カテゴリを指定して検索範囲を絞る

## 関連コマンド

- `ai-report`: システムレポート生成（RAGエルダーの活動を含む）
- `ai-send`: タスク送信（検索タスクの実行）
- `ai-learn`: システム全体の学習管理（開発予定）

## 更新履歴

- v2.0.0: エルダーズシステム統合、多機能化
- v1.0.0: 基本的なRAG機能の実装