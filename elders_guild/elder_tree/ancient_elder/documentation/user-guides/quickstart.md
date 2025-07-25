# 🚀 Auto Issue Processor A2A クイックスタートガイド

このガイドでは、15分以内にAuto Issue Processor A2Aをセットアップして動作確認する手順を説明します。

## 📋 前提条件

- Python 3.8以上
- GitHubアカウントとPersonal Access Token
- Claude API Key（Anthropic）
- Git（最新版）

## 🔧 セットアップ手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/ext-maru/ai-co.git
cd ai-co
```

### 2. 環境変数の設定

`.env`ファイルを作成：

```bash
cat > .env << 'EOF'
# GitHub設定
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO_OWNER=ext-maru
GITHUB_REPO_NAME=ai-co

# Claude API設定
CLAUDE_API_KEY=your_claude_api_key

# Auto Issue Processor設定
AUTO_ISSUE_PROCESSOR_ENABLED=true
AUTO_ISSUE_USE_TIMESTAMP=false
EOF
```

### 3. 依存関係のインストール

```bash
# Python仮想環境の作成
python3 -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 4. 初期動作確認

```bash
# システムの起動確認
python3 libs/integrations/github/auto_issue_processor.py --test

# 4賢者システムの確認
python3 -c "from libs.knowledge_sage import KnowledgeSage; print('Knowledge Sage: OK')"
python3 -c "from libs.task_sage import TaskSage; print('Task Sage: OK')"
python3 -c "from libs.incident_sage import IncidentSage; print('Incident Sage: OK')"
python3 -c "from libs.rag_manager import RagManager; print('RAG Sage: OK')"
```

## 🎯 基本的な使用方法

### 手動実行

```bash
# 処理可能なIssueをスキャン
python3 scripts/run_auto_issue_processor.py --mode scan

# 特定のIssueを処理（ドライラン）
python3 scripts/run_auto_issue_processor.py --mode dry_run --issue 123

# 実際に処理を実行
python3 scripts/run_auto_issue_processor.py --mode process
```

### 自動実行（Cron設定）

```bash
# Cron設定の追加
crontab -e

# 以下を追加（15分ごとに実行）
*/15 * * * * cd /path/to/ai-co && ./scripts/run_auto_issue_processor.sh >> logs/cron.log 2>&1
```

## 📊 監視とログ

### リアルタイム監視

```bash
# 監視ツールの起動
./scripts/monitor_auto_issue_processor.sh
```

### ログ確認

```bash
# 処理ログ
tail -f logs/auto_issue_processor.log

# エラーログのみ
grep ERROR logs/auto_issue_processor.log
```

## ⚡ トラブルシューティング

### よくある問題

#### 1. GitHub認証エラー
```
Error: Bad credentials
```
**解決**: GITHUB_TOKENが正しく設定されているか確認

#### 2. Claude API エラー
```
Error: Invalid API key
```
**解決**: CLAUDE_API_KEYが正しく設定されているか確認

#### 3. 依存関係エラー
```
ModuleNotFoundError: No module named 'xxx'
```
**解決**: `pip install -r requirements.txt`を再実行

## 🎉 動作確認

以下のコマンドで正常に動作していることを確認：

```bash
# 最近のPRを確認
gh pr list --search "Auto-fix" --limit 5

# 処理履歴を確認
cat logs/auto_issue_processing.json | jq '.recent_issues'
```

## 📚 次のステップ

- [基本使用ガイド](basic-usage-guide.md) - より詳細な使用方法
- [運用ガイド](../runbooks/) - 日常的な運用手順
- [開発者ガイド](../developer-guides/) - カスタマイズと拡張

## 🆘 サポート

問題が解決しない場合は、[Issue](https://github.com/ext-maru/ai-co/issues)を作成してください。

---
*最終更新: 2025年7月21日*