# 🔰 Auto Issue Processor A2A 初心者向けステップバイステップガイド

## 👋 はじめに

このガイドでは、Auto Issue Processor A2Aを初めて使用する方を対象に、ゼロから実際の運用まで段階的に説明します。

## 📚 前提知識

### 必要最小限の知識
- GitHubの基本操作（Issue作成、PR確認）
- コマンドライン（ターミナル）の基本的な使い方
- テキストエディタの使用

### あると良い知識
- Python基礎
- Git基本操作
- クラウドサービス（GitHub Actions、API）

## 🎯 学習目標

このガイドを完了すると以下ができるようになります：
1. Auto Issue Processorの基本概念理解
2. 環境セットアップの完了
3. 最初のIssue処理の実行
4. 基本的なトラブルシューティング

## 📖 ステップ1: 基本概念の理解

### Auto Issue Processor A2Aとは？

**A2A（Agent to Agent）**は、GitHubのIssueを完全自動で処理するシステムです。

```
Issue作成 → 自動分析 → コード生成 → テスト → PR作成
```

### 🧙‍♂️ 4賢者システム

システムの中核となる4つのAI「賢者」があります：

1. **📚 ナレッジ賢者**: 過去の知識を参照
2. **📋 タスク賢者**: 作業計画を立案
3. **🚨 インシデント賢者**: 問題を予防・解決
4. **🔍 RAG賢者**: 関連情報を検索

### 処理の流れ

```
1. 📊 Issue スキャン
   ↓
2. 🔍 複雑度評価
   ↓
3. 🧙‍♂️ 4賢者会議
   ↓
4. ⚡ Elder Flow実行
   ↓
5. 🛡️ 品質ゲート
   ↓
6. 📤 PR作成
```

## 🛠️ ステップ2: 環境セットアップ

### 2.1 必要なアカウント・ツール

#### GitHubアカウント
```bash
# GitHub CLIインストール（推奨）
# macOS
brew install gh

# Ubuntu/Debian
sudo apt install gh

# 認証
gh auth login
```

#### Claude APIアカウント
1. [Anthropic Console](https://console.anthropic.com/) でアカウント作成
2. API Keyを生成
3. 安全な場所に保存

### 2.2 リポジトリセットアップ

```bash
# ステップ1: リポジトリクローン
git clone https://github.com/ext-maru/ai-co.git
cd ai-co

# ステップ2: 仮想環境作成
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# ステップ3: 依存関係インストール
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.3 環境変数設定

`.env`ファイルを作成：

```bash
# 安全な方法でファイル作成
cat > .env << 'EOF'
# GitHub設定
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO_OWNER=your-github-username
GITHUB_REPO_NAME=your-repo-name

# Claude API設定
CLAUDE_API_KEY=your_claude_api_key_here

# Auto Issue Processor設定
AUTO_ISSUE_PROCESSOR_ENABLED=true
AUTO_ISSUE_USE_TIMESTAMP=false
AUTO_ISSUE_MAX_PARALLEL=3
EOF
```

#### GitHub Tokenの取得方法

1. GitHub.com → Settings → Developer settings
2. Personal access tokens → Tokens (classic)
3. "Generate new token" → "Generate new token (classic)"
4. スコープを選択：
   - ✅ `repo` (フル権限)
   - ✅ `workflow`
   - ✅ `read:org`
5. トークンをコピーして`.env`に貼り付け

## 🧪 ステップ3: 動作確認

### 3.1 基本テスト

```bash
# Python環境確認
python3 --version  # 3.8以上必要

# 依存関係確認
python3 -c "import anthropic; print('Claude API: OK')"
python3 -c "from github import Github; print('GitHub API: OK')"

# システムテスト
python3 libs/integrations/github/auto_issue_processor.py --test
```

### 3.2 GitHub接続テスト

```bash
# GitHub CLI認証確認
gh auth status

# APIアクセステスト
gh repo view  # 現在のリポジトリ情報表示

# Issue一覧取得テスト
gh issue list --limit 5
```

### 3.3 Claude API接続テスト

```python
# test_claude.py として保存
import os
from anthropic import Anthropic

def test_claude_api():
    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key:
        print("❌ CLAUDE_API_KEY not set")
        return False
    
    try:
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-opus-20240229",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print("✅ Claude API connection successful")
        return True
    except Exception as e:
        print(f"❌ Claude API error: {e}")
        return False

if __name__ == "__main__":
    test_claude_api()
```

```bash
python3 test_claude.py
```

## 🎮 ステップ4: 最初のIssue処理

### 4.1 テスト用Issue作成

GitHub上で新しいIssueを作成：

```markdown
タイトル: [TEST] Simple calculator function

本文:
Create a simple calculator function that can perform basic arithmetic operations.

Requirements:
- Add, subtract, multiply, divide functions
- Input validation
- Return proper error messages for invalid operations
- Include unit tests

Priority: medium
Labels: enhancement, auto-processable
```

### 4.2 ドライラン実行

```bash
# Issue番号を確認
gh issue list --label "auto-processable"

# ドライラン実行（実際の処理はしない）
python3 scripts/run_auto_issue_processor.py \
  --mode dry_run \
  --issue YOUR_ISSUE_NUMBER

# 結果確認
echo "ドライランが成功すれば、実際の処理に進めます"
```

### 4.3 実際の処理実行

```bash
# 実処理実行
python3 scripts/run_auto_issue_processor.py \
  --mode process \
  --issue YOUR_ISSUE_NUMBER

# 処理状況監視
./scripts/monitor_auto_issue_processor.sh
```

### 4.4 結果確認

```bash
# PR一覧確認
gh pr list --search "Auto-fix"

# 最新のPR詳細確認
gh pr view --json title,number,url

# 生成されたファイル確認
ls auto_implementations/
ls tests/auto_generated/
```

## 📊 ステップ5: 結果の理解

### 処理成功の場合

✅ **期待される出力**:
- PRが自動作成される
- 実装ファイル（`auto_implementations/issue_XXX_implementation.py`）
- テストファイル（`tests/auto_generated/test_issue_XXX.py`）
- 設計書（`auto_fixes/issue_XXX_fix.md`）

### 処理失敗の場合

❌ **よくあるエラーと対処**:

```bash
# 1. 認証エラー
Error: Bad credentials
→ GitHub Tokenを確認

# 2. Claude APIエラー
Error: Invalid API key
→ Claude API Keyを確認

# 3. 権限エラー
Error: Permission denied
→ リポジトリの書き込み権限を確認
```

## 🔧 ステップ6: 基本的なカスタマイズ

### 6.1 処理対象の設定

```bash
# 処理する優先度を設定
export AUTO_ISSUE_TARGET_PRIORITIES="high,medium"

# 1日の最大処理数を設定
export AUTO_ISSUE_MAX_DAILY=10

# タイムスタンプ付きブランチ名を使用
export AUTO_ISSUE_USE_TIMESTAMP=true
```

### 6.2 監視設定

```bash
# リアルタイム監視開始
./scripts/monitor_auto_issue_processor.sh &

# ログレベル調整
export AUTO_ISSUE_LOG_LEVEL=DEBUG

# ログ確認
tail -f logs/auto_issue_processor.log
```

## 🆘 ステップ7: トラブルシューティング

### よくある問題と解決方法

#### 問題1: Issueが処理されない
```bash
# 確認項目
1. ラベル「auto-processable」が付いているか
2. 複雑度スコアが基準値以下か
3. 最近処理されていないか

# 診断コマンド
python3 scripts/diagnose_issue.py --issue YOUR_ISSUE_NUMBER
```

#### 問題2: 生成されたコードが期待と違う
```bash
# 1. Issue内容を詳細に記述
# 2. 技術スタックを明記
# 3. 具体的な要件を箇条書きで記載

# 例：
Requirements:
- Use FastAPI framework
- PostgreSQL database
- JWT authentication
- Docker deployment
```

#### 問題3: テストが失敗する
```bash
# 生成されたテストを実行
python3 -m pytest tests/auto_generated/test_issue_XXX.py -v

# カスタマイズが必要な場合は手動で修正
```

## 🎯 ステップ8: 次のレベルへ

### 上級機能の学習

1. **カスタムテンプレート作成**
   - [開発者ガイド](../developer-guides/contribution-guide.md)

2. **運用監視**
   - [日常運用ガイド](../runbooks/daily-operations-guide.md)

3. **API活用**
   - [APIリファレンス](../api/auto-issue-processor-api-reference.md)

### コミュニティ参加

- Issue報告・機能提案
- プルリクエスト作成
- ドキュメント改善

## 📚 参考リソース

### 公式ドキュメント
- [クイックスタートガイド](quickstart.md)
- [基本使用ガイド](basic-usage-guide.md)
- [トラブルシューティング](../runbooks/troubleshooting-guide.md)

### 外部リソース
- [GitHub Issue Templates](https://docs.github.com/ja/communities/using-templates-to-encourage-useful-issues-and-pull-requests)
- [Anthropic Claude API](https://docs.anthropic.com/)

## 🎉 完了チェックリスト

- [ ] 環境セットアップ完了
- [ ] GitHub・Claude API接続確認
- [ ] テストIssue処理成功
- [ ] 生成されたPR確認
- [ ] 基本的なカスタマイズ理解
- [ ] トラブルシューティング方法把握

**おめでとうございます！**  
Auto Issue Processor A2Aの基本的な使い方をマスターしました。

---
*最終更新: 2025年7月21日*