# 📋 GitHub Issue完全自動化ガイド

## 🎯 概要

エルダーズギルド GitHub Issue完全自動化システムは、Issue管理を完全に自動化し、4賢者システムと連携して効率的な開発を実現します。

## 🚀 主要機能

### 1. 自動化されたワークフロー

#### Sub Issue自動管理 (`sub_issue_automation.yml`)
- **自動トリガー**: Issue/PR/コメントイベント、6時間毎の定期実行
- **進捗自動更新**: チェックリストから進捗率を自動計算
- **PRマージ時の自動クローズ**: `fixes #123` パターンを検出
- **進捗ラベル自動更新**: `progress:XX%` ラベルの自動管理

#### Issue自動管理 (`issue_auto_management.yml`)
- **自動ラベリング**: タイトル・本文から適切なラベルを付与
- **エルダーサーバント自動アサイン**: 作業内容に応じた担当部隊の自動割り当て
- **4賢者システム同期**: 全Issueを賢者システムと連携
- **日次レポート生成**: 活動サマリーと洞察を自動作成

### 2. エルダーズギルド専用Issue管理システム

#### EldersIssueManager
```python
from libs.integrations.github.elders_issue_manager import EldersIssueManager

manager = EldersIssueManager()
manager.set_repository('owner/repo')

# EpicからSub Issue作成
await manager.create_sub_issues_from_epic(epic_issue)

# 自動アサイン
await manager.auto_assign_to_servants(issue)

# 進捗更新
await manager.update_progress_chart(master_issue)

# 4賢者同期
await manager.sync_with_four_sages(issue)
```

### 3. CLI ツール

#### 基本使用法
```bash
# 全Issueを4賢者と同期
python3 scripts/elders_issue_cli.py --repo owner/repo sync

# 日次レポート生成
python3 scripts/elders_issue_cli.py --repo owner/repo report

# EpicからSub Issue作成
python3 scripts/elders_issue_cli.py --repo owner/repo epic --issue 123

# 自動アサイン
python3 scripts/elders_issue_cli.py --repo owner/repo auto-assign

# 対話モード
python3 scripts/elders_issue_cli.py --repo owner/repo interactive
```

## 🔧 セットアップ

### 1. 環境変数設定
```bash
# .envファイルを作成
cp .env.example .env

# GitHubトークンを設定
GITHUB_TOKEN=your_personal_access_token_here
```

### 2. 必要な権限
- `repo` - リポジトリへのフルアクセス
- `workflow` - GitHub Actionsワークフローの管理

### 3. ラベル設定
以下のラベルを事前に作成してください：
- `epic` - Master Issue用
- `sub-issue` - Sub Issue用
- `bug`, `enhancement`, `research` - タイプ別
- `priority:high`, `priority:medium`, `priority:low` - 優先度
- `progress:0%` 〜 `progress:100%` - 進捗率
- `incident-knights`, `dwarf-workshop`, `rag-wizards`, `elf-forest` - サーバント部隊

## 📊 自動化フロー

### Issue作成時
1. タイトル・本文を解析して自動ラベリング
2. Epicの場合はSub Issue作成を提案
3. 4賢者システムと同期
4. 適切なエルダーサーバントに自動アサイン

### コメント投稿時
1. 進捗キーワードを検出
2. ステータスラベルを自動更新
3. Master Issueの進捗を再計算

### PRマージ時
1. 関連Issue番号を抽出
2. 該当Issueを自動クローズ
3. 完了コメントを投稿
4. Elder Flowに通知

### 定期実行（6時間毎）
1. 全オープンIssueの進捗を再計算
2. 進捗ラベルを更新
3. 遅延タスクを検出
4. レポートを生成

## 🧙‍♂️ 4賢者連携

### ナレッジ賢者
- Issue履歴から学習
- パターン認識と提案
- ベストプラクティスの蓄積

### タスク賢者
- 優先順位の自動調整
- 依存関係の管理
- 進捗の追跡

### インシデント賢者
- バグ・障害の即座検知
- 緊急度の判定
- 自動エスカレーション

### RAG賢者
- 類似Issue検索
- 解決策の提案
- 技術調査

## 📈 メトリクス

自動生成される日次レポートには以下が含まれます：
- 作成・クローズされたIssue数
- アクティブIssue数
- 完了率
- 平均解決時間
- ベロシティ
- 4賢者からの洞察

## 🛡️ セキュリティ

### トークン管理
- GitHub Secretsを使用
- 環境変数での管理
- 最小権限の原則

### 監査ログ
- 全アクションの記録
- 変更履歴の追跡
- 定期的なレビュー

## 🚨 トラブルシューティング

### ワークフローが実行されない
1. Actions設定を確認
2. ワークフロー権限を確認
3. YAMLシンタックスを検証

### 自動クローズが機能しない
1. PR本文のキーワードを確認
2. Issue番号の形式を確認（`#123`）
3. 権限設定を確認

### 4賢者同期エラー
1. 各賢者システムの稼働状況を確認
2. APIレート制限を確認
3. ログを確認

## 📚 関連ドキュメント

- [エルダーズギルド階層構造](ELDERS_GUILD_HIERARCHY_MASTER.md)
- [4賢者システムガイド](FOUR_SAGES_SYSTEM_GUIDE.md)
- [Elder Flow実装ガイド](ELDER_FLOW_IMPLEMENTATION_GUIDE.md)

---
🤖 Powered by Elders Guild Automation System