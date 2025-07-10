# 🎯 AI Git コミットベストプラクティス ナレッジベース v1.0

## 📋 概要

AI Git コミットベストプラクティスは、Elders Guildの全ての自動コミットをConventional Commits形式で生成するシステムです。これにより、コミット履歴の可読性が向上し、自動化ツールとの連携が容易になります。

### **システムの特徴**
- ✅ **Conventional Commits準拠**: 業界標準のコミットメッセージ形式
- ✅ **自動タイプ検出**: 変更内容から適切なコミットタイプを推測
- ✅ **スコープ抽出**: 変更ファイルからスコープを自動決定
- ✅ **Breaking Change検出**: 重大な変更を識別してフッターに記載
- ✅ **多言語対応**: 英語でのプロフェッショナルなメッセージ生成
- ✅ **CHANGELOG生成**: コミット履歴から自動的にCHANGELOGを作成

### **実装日**: 2025-07-03

## 🏗️ システムアーキテクチャ

### **コンポーネント構成**

```
┌─────────────────────────┐
│     PMWorker            │
│  (ファイル変更検出)      │
└──────────┬──────────────┘
           │ use_best_practices=True
           ▼
┌─────────────────────────┐
│   GitFlowManager        │
│  (コミット管理)          │
└──────────┬──────────────┘
           │ 
           ▼
┌─────────────────────────┐
│ CommitMessageGenerator  │
│  (メッセージ生成)        │
└─────────────────────────┘
           │
           ▼
    Conventional Commits
         形式で出力
```

### **主要コンポーネント**

#### 1. CommitMessageGenerator
- **場所**: `libs/commit_message_generator.py`
- **機能**: 
  - 変更内容の分析
  - コミットタイプの自動判定
  - メッセージの構造化
  - 検証機能

#### 2. GitFlowManager（拡張版）
- **場所**: `libs/git_flow_manager.py`
- **追加機能**:
  - `use_best_practices`パラメータ
  - CommitMessageGeneratorとの統合
  - CHANGELOG生成

#### 3. PMWorker（更新版）
- **場所**: `workers/pm_worker.py`
- **変更内容**:
  - ベストプラクティス対応のコミット呼び出し
  - タスクIDの自動参照追加

#### 4. ai-gitコマンド（拡張版）
- **場所**: `scripts/ai-git`
- **新機能**:
  - preview: メッセージプレビュー
  - analyze: 変更分析
  - best-practices: ガイド表示
  - changelog: CHANGELOG生成

## 📝 Conventional Commits形式

### **基本構造**

```
<type>(<scope>): <subject>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>
```

### **要素の説明**

1. **type**: 変更の種類（必須）
2. **scope**: 変更の影響範囲（オプション）
3. **subject**: 変更の要約（必須、50文字以内）
4. **body**: 詳細な説明（オプション、72文字で改行）
5. **footer**: 追加情報（オプション、Breaking ChangesやIssue参照）

### **コミットタイプ**

| タイプ | 説明 | 例 |
|--------|------|-----|
| `feat` | 新機能 | 新しいワーカーの追加 |
| `fix` | バグ修正 | エラーハンドリングの修正 |
| `docs` | ドキュメントのみ | READMEの更新 |
| `style` | コードスタイル | フォーマット調整 |
| `refactor` | リファクタリング | コード構造の改善 |
| `perf` | パフォーマンス改善 | 処理速度の最適化 |
| `test` | テスト | ユニットテストの追加 |
| `build` | ビルドシステム | 依存関係の更新 |
| `ci` | CI/CD | GitHub Actions設定 |
| `chore` | その他 | 設定ファイルの更新 |
| `revert` | リバート | 以前のコミットを取り消し |

## 🚀 使用方法

### 1. **自動生成（PMWorker経由）**

PMWorkerが新しいファイルを検出すると自動的に実行されます：

```python
# PMWorker内部での呼び出し（自動）
if self.git_flow.commit_changes(None, new_files, use_best_practices=True):
    logger.info("✅ ベストプラクティスに従ってコミット")
```

### 2. **手動でのコミット**

```bash
# プレビューしてからコミット
ai-git commit --preview
ai-git commit -m "カスタムメッセージ"

# シンプルモード（従来形式）
ai-git commit --simple -m "Quick fix"
```

### 3. **変更の分析**

```bash
# 現在の変更を分析
ai-git analyze

# 出力例：
# 📊 Change Analysis:
# Files changed: 3
# 
# Modified files:
#   - workers/email_worker.py
#   - libs/email_manager.py
#   - config/email.json
# 
# Suggested commit type: feat
# Suggested scope: workers
```

### 4. **CHANGELOG生成**

```bash
# 全履歴からCHANGELOG生成
ai-git changelog --output CHANGELOG.md

# 特定のタグ間
ai-git changelog --from v1.0.0 --to v2.0.0 --output CHANGELOG.md
```

### 5. **ベストプラクティスガイド**

```bash
# ガイドライン表示
ai-git best-practices
```

## ⚙️ 設定ファイル

### **commit_best_practices.json**

```json
{
  "types": {
    "feat": {
      "description": "新機能",
      "emoji": "✨"
    },
    "fix": {
      "description": "バグ修正",
      "emoji": "🐛"
    },
    "docs": {
      "description": "ドキュメントのみの変更",
      "emoji": "📚"
    },
    "style": {
      "description": "コードの意味に影響しない変更",
      "emoji": "💎"
    },
    "refactor": {
      "description": "バグ修正や機能追加を含まないコード変更",
      "emoji": "📦"
    },
    "perf": {
      "description": "パフォーマンス改善",
      "emoji": "🚀"
    },
    "test": {
      "description": "テストの追加や修正",
      "emoji": "🚨"
    },
    "build": {
      "description": "ビルドシステムや外部依存関係の変更",
      "emoji": "🛠"
    },
    "ci": {
      "description": "CI設定ファイルとスクリプトの変更",
      "emoji": "⚙️"
    },
    "chore": {
      "description": "その他の変更",
      "emoji": "♻️"
    },
    "revert": {
      "description": "以前のコミットをリバート",
      "emoji": "⏪"
    }
  },
  "scopes": {
    "suggested": ["workers", "libs", "core", "scripts", "config", "docs", "tests"],
    "allow_custom": true
  },
  "rules": {
    "subject_max_length": 50,
    "body_max_line_length": 72,
    "type_case": "lowercase",
    "scope_case": "lowercase",
    "subject_case": "sentence",
    "subject_no_period": true,
    "body_leading_blank": true,
    "footer_leading_blank": true
  }
}
```

### **.gitmessage テンプレート**

```
# <type>(<scope>): <subject>
# 
# <body>
# 
# <footer>

# Type: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
# Scope: workers, libs, core, scripts, config, etc.
# Subject: use imperative mood, no period at the end, max 50 chars
# Body: explain what and why, not how, wrap at 72 chars
# Footer: breaking changes, issue references
```

## 📊 実装例

### **例1: 新機能の追加**

```
feat(workers): implement email notification worker

Add EmailWorker to handle asynchronous email notifications
with support for multiple SMTP providers and templates.

- Support Gmail, SendGrid, and custom SMTP servers
- Add HTML and plain text template support
- Implement retry mechanism with exponential backoff
- Add email queue management with priority support

The worker processes emails asynchronously to avoid blocking
the main application flow and ensures delivery reliability
through automatic retries.

Refs: code_20250703_095423
```

### **例2: バグ修正**

```
fix(api): resolve timeout issue in data processing endpoint

Increase timeout limit from 30s to 120s for large dataset
processing. The previous timeout was causing failures for
datasets over 10MB.

- Adjust timeout in request handler
- Add progress callback for long operations
- Implement chunked processing for large files

Fixes #456
Refs: code_20250703_101234
```

### **例3: Breaking Change**

```
refactor(core)!: change BaseWorker initialization parameters

BREAKING CHANGE: BaseWorker now requires explicit worker_type
parameter in constructor. This change improves type safety
and prevents runtime errors.

Migration guide:
- Before: BaseWorker()
- After: BaseWorker(worker_type='task')

All existing workers have been updated to use the new
constructor signature.

Refs: code_20250703_103045
```

## 🎨 カスタマイズ

### **新しいコミットタイプの追加**

1. `config/commit_best_practices.json`を編集：

```json
{
  "types": {
    "security": {
      "description": "セキュリティ改善",
      "emoji": "🔒"
    }
  }
}
```

2. CommitMessageGeneratorが自動的に認識

### **カスタムスコープの設定**

```json
{
  "scopes": {
    "suggested": ["workers", "libs", "api", "frontend", "backend"],
    "allow_custom": true
  }
}
```

### **ルールの調整**

```json
{
  "rules": {
    "subject_max_length": 72,  // より長い件名を許可
    "require_scope": true,      // スコープを必須に
    "require_body": true        // 本文を必須に
  }
}
```

## 🛠️ CommitMessageGeneratorの内部動作

### **1. 変更分析**

```python
def analyze_changes(self) -> dict:
    # git diffで変更内容を取得
    # ファイルリスト、追加/削除行数を分析
    # 変更の性質を判定
```

### **2. タイプ検出ロジック**

```python
def detect_commit_type(self, files: List[str], content: str) -> str:
    # ファイルパスとコンテンツから推測
    if any('test' in f for f in files):
        return 'test'
    elif any(f.endswith('.md') for f in files):
        return 'docs'
    # ... その他のロジック
```

### **3. メッセージ生成**

```python
def generate_commit_message(self, 
                          files_created: List[str] = None,
                          files_updated: List[str] = None,
                          task_id: str = None) -> str:
    # 1. 変更を分析
    # 2. タイプとスコープを決定
    # 3. サブジェクトを生成
    # 4. 本文を構築
    # 5. フッターを追加
```

## 🚨 トラブルシューティング

### **メッセージが生成されない**

```bash
# 手動でテスト
cd /home/aicompany/ai_co
python3 -c "from libs.commit_message_generator import CommitMessageGenerator; g = CommitMessageGenerator(); print(g.generate_commit_message())"
```

### **コミットタイプが適切でない**

1. 変更内容を確認：
   ```bash
   ai-git analyze
   ```

2. 手動で指定：
   ```bash
   ai-git commit -m "fix(api): correct endpoint response"
   ```

### **PMWorkerが旧形式を使用**

```bash
# PMWorkerの実装確認
grep -n "use_best_practices" workers/pm_worker.py

# 期待される出力:
# 136: if self.git_flow.commit_changes(None, new_files, use_best_practices=True):
```

## 📈 効果とメリット

### **1. 可読性の向上**
- 一目で変更の種類が分かる
- 影響範囲が明確
- 詳細な説明で背景を理解

### **2. 自動化の促進**
- セマンティックバージョニング
- 自動CHANGELOG生成
- リリースノート作成

### **3. チーム開発**
- コミュニケーションの改善
- レビューの効率化
- 履歴の追跡性向上

## 🚀 今後の拡張案

### **Phase 1: 基本拡張**
- [ ] 日本語メッセージ対応
- [ ] コミットフック統合
- [ ] VSCode拡張機能

### **Phase 2: AI機能強化**
- [ ] より賢い変更分析
- [ ] 自然言語からのメッセージ生成
- [ ] コードレビューコメント統合

### **Phase 3: エンタープライズ機能**
- [ ] チーム別カスタマイズ
- [ ] コンプライアンスルール
- [ ] 監査ログ統合

## 📋 リファレンス

### **関連ファイル**
- `libs/commit_message_generator.py` - メッセージ生成エンジン
- `libs/git_flow_manager.py` - Git操作管理（拡張版）
- `workers/pm_worker.py` - 自動コミット実装
- `scripts/ai-git` - CLIツール
- `config/commit_best_practices.json` - 設定ファイル
- `.gitmessage` - Gitテンプレート

### **外部リンク**
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)

---

**🎯 このナレッジベースは、Elders Guildのコミット品質向上の基礎となります**

*最終更新: 2025-07-03*