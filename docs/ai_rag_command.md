# ai-rag コマンド ドキュメント

## 概要
`ai-rag`は、RAG（Retrieval-Augmented Generation）賢者と統合したコマンドラインツールです。知識ベースの検索、コンテキスト分析、プロンプト強化などの機能を提供します。

## 🔍 RAG賢者について
RAG賢者は、Elders Guild 4賢者システムの一員として、以下の役割を担っています：
- **情報検索**: 知識ベースから関連情報を高速検索
- **最適解探索**: 複数の選択肢から最適な解決策を発見
- **コンテキスト強化**: プロンプトに関連情報を追加して精度向上
- **継続学習**: 新しい知識を蓄積し、検索精度を改善

## インストール
```bash
# 実行権限の付与
chmod +x /home/aicompany/ai_co/commands/ai_rag.py

# エイリアスの設定（オプション）
alias ai-rag='python3 /home/aicompany/ai_co/commands/ai_rag.py'
```

## 使用方法

### 基本構文
```bash
ai-rag <サブコマンド> [オプション]
```

### サブコマンド一覧

#### 1. search - 知識ベース検索
```bash
# 基本検索
ai-rag search "Docker コンテナ管理"

# オプション付き検索
ai-rag search "エラー処理" --limit 10 --threshold 0.8

# JSON形式で出力
ai-rag search "4賢者システム" --format json
```

**オプション:**
- `--limit, -l`: 結果数制限（デフォルト: 5）
- `--threshold, -t`: 類似度閾値（デフォルト: 0.7）
- `--format, -f`: 出力形式 [text|json]（デフォルト: text）

#### 2. analyze - コンテキスト分析
```bash
# テキスト分析
ai-rag analyze "タスクワーカーがエラーで停止しました"

# 深い分析
ai-rag analyze "システムのパフォーマンスが低下" --depth 5
```

**オプション:**
- `--depth, -d`: 分析深度（デフォルト: 3）

#### 3. enhance - プロンプト強化
```bash
# プロンプト強化
ai-rag enhance "Dockerコンテナの作成方法を教えて"

# モデル指定
ai-rag enhance "エラーの解決方法" --model claude-sonnet-4-20250514
```

**オプション:**
- `--model, -m`: 使用モデル（デフォルト: claude-sonnet-4-20250514）

#### 4. summary - 要約生成
```bash
# テキスト要約
ai-rag summary "長い文章..."

# ファイルから要約
ai-rag summary /path/to/document.txt

# 文字数指定
ai-rag summary report.md --length 200
```

**オプション:**
- `--length, -l`: 要約文字数（デフォルト: 100）

#### 5. learn - 新しい知識を学習
```bash
# テキストを学習
ai-rag learn "RAG賢者は検索拡張生成を担当します" --category sage_info --tags rag sage

# ファイルから学習
ai-rag learn /path/to/knowledge.txt --category docker --tags container api
```

**オプション:**
- `--category, -c`: 知識カテゴリ
- `--tags`: タグリスト（スペース区切り）

#### 6. status - RAG賢者ステータス
```bash
# ステータス表示
ai-rag status
```

出力例：
```
🔍 RAG賢者ステータス
========================================
役割: 情報検索と最適解探索
状態: Active

知識ベース統計:
  総エントリ数: 1,234
  カテゴリ数: 15

カテゴリ別:
  - docker: 234件
  - error_handling: 189件
  - sage_info: 156件

機能:
  ✓ セマンティック検索
  ✓ コンテキスト分析
  ✓ プロンプト強化
  ✓ 要約生成
  ✓ 継続学習
```

#### 7. optimize - 検索最適化
```bash
# インデックス再構築
ai-rag optimize --rebuild-index
```

**オプション:**
- `--rebuild-index`: 検索インデックスを再構築

## 実装詳細

### 依存関係
- `RAGManager`: 基本的なRAG機能を提供
- `EnhancedRAGManager`: 高度な検索・分析機能を提供
- Claude CLI: 要約生成に使用（要インストール）

### データ保存場所
- 学習データ: `/home/aicompany/ai_co/knowledge_base/rag_learned/`
- 知識ベース: `/home/aicompany/ai_co/knowledge_base/`

## 使用例

### 例1: エラー解決のワークフロー
```bash
# 1. エラーメッセージを分析
ai-rag analyze "ModuleNotFoundError: No module named 'docker'"

# 2. 関連する知識を検索
ai-rag search "docker module installation" --limit 10

# 3. 解決策をプロンプトとして強化
ai-rag enhance "Dockerモジュールのインストール方法"

# 4. 解決後、新しい知識として学習
ai-rag learn "pip install dockerでDockerライブラリをインストールできます" --category error_solution --tags docker pip
```

### 例2: ドキュメント処理
```bash
# 長いドキュメントを要約
ai-rag summary /home/aicompany/ai_co/docs/README.md --length 300

# 要約を知識として保存
ai-rag learn "$(ai-rag summary README.md)" --category documentation
```

### 例3: 4賢者システムとの連携
```bash
# RAG賢者のステータス確認
ai-rag status

# 他の賢者に関する情報を検索
ai-rag search "ナレッジ賢者 タスク賢者 インシデント賢者"

# 賢者間の協調に関する分析
ai-rag analyze "4賢者システムの協調メカニズム" --depth 5
```

## トラブルシューティング

### よくある問題

1. **"マネージャーの初期化に失敗"**
   - 依存ライブラリが不足している可能性があります
   - `pip install -r requirements.txt`を実行してください

2. **"要約生成に失敗"**
   - Claude CLIがインストールされていない可能性があります
   - Claude CLIのセットアップを確認してください

3. **"検索結果が0件"**
   - 知識ベースが空の可能性があります
   - `ai-rag learn`で知識を追加してください

## 今後の拡張予定
- ベクトルデータベース統合
- マルチモーダル検索（画像、音声）
- リアルタイム学習機能
- 他の賢者との深い統合

## 関連コマンド
- `ai-report`: 4賢者システムレポート生成
- `ai-knowledge`: ナレッジ賢者インターフェース
- `ai-task`: タスク賢者インターフェース
- `ai-incident`: インシデント賢者インターフェース

---
*このドキュメントは Elders Guild 4賢者システムの一部です*