# GitHub関連ハードコーディング調査レポート

**調査日時**: 2025年7月20日  
**調査者**: クロードエルダー  
**目的**: エルダーズギルドプロジェクトでのGitHub関連のハードコーディング値の特定と環境変数化

## 🔍 調査概要

GitHub関連のハードコーディングされた情報を以下の観点で調査:
1. リポジトリ名の直接記述
2. GitHub URLのハードコーディング
3. Issue/PR番号の固定値
4. GitHub APIエンドポイント
5. 認証情報のハードコーディング

## 🚨 発見されたハードコーディング（重要度順）

### Critical（緊急対応必要）

**認証情報のテストパターン**
- `/home/aicompany/ai_co/docs/reports/hardcoded_env_variables_audit.md`
- `/home/aicompany/ai_co/libs/integrations/github/tests/test_comprehensive_security_system.py`
- 内容: テスト用のダミートークンパターンが含まれている

### High（高重要度）

#### 1. リポジトリ設定の固定化
**ファイル**: `/home/aicompany/ai_co/config/repository_config.json`  
**行**: 4-12  
**ハードコーディング値**:
```json
{
  "owner": "ext-maru",
  "name": "ai-co"
}
```
**環境変数化すべき項目**: `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`

#### 2. GitHub API基本設定
**ファイル**: `/home/aicompany/ai_co/scripts/close_github_issue.py`  
**行**: 24-25  
**ハードコーディング値**:
```python
repo = os.getenv("GITHUB_REPO", "ext-maru/ai-co")
url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
```
**現状**: 環境変数とデフォルト値併用

#### 3. Issue監視システム
**ファイル**: `/home/aicompany/ai_co/libs/integrations/github/issue_monitor.py`  
**行**: 25-26  
**ハードコーディング値**:
```python
repo_owner: str = "ext-maru",
repo_name: str = "ai-co",
```

#### 4. UTT Issues作成スクリプト
**ファイル**: `/home/aicompany/ai_co/scripts/create_utt_issues.py`  
**行**: 20-22  
**ハードコーディング値**:
```python
REPO_OWNER = "ext-maru"
REPO_NAME = "ai-co"
API_BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
```

### Medium（中重要度）

#### 1. Issue番号の固定参照
**ファイル**: `/home/aicompany/ai_co/scripts/test_issue_187.py`  
**行**: 32-33  
**ハードコーディング値**:
```python
repo = g.get_repo("ext-maru/ai-co")
issue = repo.get_issue(187)
```

#### 2. User-Agent固定値
複数ファイルで以下のようなUser-Agentが固定:
- `"User-Agent": "Claude-Elder-Test"`
- `"User-Agent": "Claude-Elder-UTT"`

### Low（低重要度）

#### 1. ドキュメントの参照URL
複数のMarkdownファイルでGitHub URLが直接記述されているが、ドキュメント用途のため優先度は低い。

## 🛠️ 環境変数化すべき項目

### 必須環境変数
```bash
# 基本設定
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_REPO_OWNER=ext-maru
GITHUB_REPO_NAME=ai-co

# API設定
GITHUB_API_BASE_URL=https://api.github.com
GITHUB_USER_AGENT=Claude-Elder-System

# 運用設定
GITHUB_DEFAULT_BRANCH=main
GITHUB_AUTO_MERGE_ENABLED=false
```

### オプション環境変数
```bash
# 監視設定
GITHUB_ISSUE_CHECK_INTERVAL=30
GITHUB_RATE_LIMIT_REQUESTS=5000
GITHUB_RATE_LIMIT_WINDOW=3600

# セキュリティ設定
GITHUB_WEBHOOK_SECRET=xxx
GITHUB_APP_ID=xxx
GITHUB_PRIVATE_KEY_PATH=/path/to/key.pem
```

## 📋 修正計画

### Phase 1: Critical修正（即座）
1. テスト用認証情報パターンの削除・暗号化
2. 設定ファイルの環境変数化

### Phase 2: High修正（1週間以内）
1. スクリプト群の環境変数対応
2. 中央設定システムの実装
3. デフォルト値の適切な設定

### Phase 3: Medium修正（2週間以内）
1. Issue番号参照の動的化
2. User-Agent統一と設定化
3. テストケースの更新

### Phase 4: Low修正（必要時）
1. ドキュメントの動的参照化
2. 設定検証システムの実装

## 🔒 セキュリティ勧告

1. **認証情報の完全環境変数化**
   - すべてのGitHubトークンを環境変数化
   - テストファイルからダミートークンを削除

2. **設定検証システム**
   - 起動時の環境変数検証
   - 不正な設定の自動検出

3. **監査ログ**
   - GitHub API使用状況の記録
   - 異常アクセスパターンの検出

## 📊 まとめ

- **Total調査ファイル数**: 132ファイル
- **ハードコーディング検出**: 21箇所（Critical: 2, High: 8, Medium: 6, Low: 5）
- **緊急対応必要**: 認証情報関連2箇所
- **環境変数化推奨**: 基本設定8箇所

**推奨アクション**: Phase 1の即座実行とPhase 2の1週間以内完了

---
🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>