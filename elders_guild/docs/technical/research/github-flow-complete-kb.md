---
audience: users
author: claude-elder
category: technical
dependencies: []
description: No description available
difficulty: intermediate
last_updated: '2025-07-23'
related_docs: []
reviewers: []
status: draft
subcategory: research
tags:
- technical
title: GitHub Flow Complete Knowledge Base
version: 1.0.0
---

# GitHub Flow Complete Knowledge Base

## 🔄 概要

GitHub Flowは、Elders Guildプロジェクトの開発フローを標準化するためのシステムです。

## 📋 ブランチ戦略

### メインブランチ
- **main**: 本番環境のコード
- **develop**: 開発環境のコード（統合ブランチ）

### 作業ブランチ
- **feature/**: 新機能開発
- **fix/**: バグ修正
- **docs/**: ドキュメント更新
- **refactor/**: リファクタリング

## 🎯 コミット規約

### Conventional Commits形式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### タイプ一覧
| タイプ | 説明 | 絵文字 |
|-------|------|--------|
| feat | 新機能 | ✨ |
| fix | バグ修正 | 🐛 |
| docs | ドキュメント | 📝 |
| style | コードスタイル | 💄 |
| refactor | リファクタリング | ♻️ |
| perf | パフォーマンス改善 | ⚡ |
| test | テスト | ✅ |
| build | ビルドシステム | 🏗️ |
| ci | CI/CD | 👷 |
| chore | その他 | 🔧 |
| revert | リバート | ⏪ |

### スコープ例
- workers: ワーカー関連
- libs: ライブラリ関連
- core: Core基盤関連
- config: 設定関連
- tests: テスト関連

### コミットメッセージ例
```
feat(workers): ✨ add error intelligence worker

Implement a new worker for automatic error analysis and resolution.
This worker monitors error queues and applies intelligent fixes.

- Add error pattern recognition
- Implement auto-fix strategies
- Add incident reporting

Closes #123
```

## 🛠️ GitHub Flowコマンド

### 基本コマンド（gfエイリアス）
```bash
# 機能ブランチ作成
gf feature <name>

# バグ修正ブランチ作成
gf fix <name>

# コミット（ベストプラクティス適用）
gf commit -m "message"

# ステータス確認
gf status

# PR作成手順表示
gf pr
```

### ai-gitコマンド（詳細版）
```bash
# ステータス確認
ai-git status

# コミット（自動メッセージ生成）
ai-git commit

# メッセージプレビュー
ai-git commit --preview

# メッセージ検証
ai-git commit --validate

# CHANGELOG生成
ai-git changelog --from v5.1 --to HEAD

# ベストプラクティス表示
ai-git best-practices

# 変更分析
ai-git analyze
```

## 📊 ワークフロー

### 1. 新機能開発
```bash
# 1. featureブランチ作成
gf feature user-authentication

# 2. 開発作業
# ... コード編集 ...

# 3. 変更を確認
gf status

# 4. コミット
gf commit -m "feat(auth): add user login functionality"

# 5. プッシュ
git push -u origin feature/user-authentication

# 6. PR作成（GitHub UI）
```

### 2. バグ修正
```bash
# 1. fixブランチ作成
gf fix login-error

# 2. 修正作業
# ... バグ修正 ...

# 3. コミット
gf commit -m "fix(auth): resolve login timeout error"

# 4. プッシュとPR
git push -u origin fix/login-error
```

### 3. 緊急修正（Hotfix）
```bash
# 1. mainから直接ブランチ作成
git checkout main
git pull origin main
git checkout -b hotfix/critical-security-issue

# 2. 修正とコミット
gf commit -m "fix(security): patch SQL injection vulnerability"

# 3. mainとdevelopへマージ
git checkout main
git merge hotfix/critical-security-issue
git checkout develop
git merge hotfix/critical-security-issue
```

## 🔍 コード レビュー

### PR作成時のチェックリスト
- [ ] コミットメッセージが規約に従っている
- [ ] テストが通っている
- [ ] ドキュメントが更新されている
- [ ] Breaking changesが明記されている
- [ ] 関連するIssueがリンクされている

### レビューポイント
1. **コード品質**
   - 可読性
   - 保守性
   - パフォーマンス

2. **テスト**
   - 単体テスト
   - 統合テスト
   - カバレッジ

3. **ドキュメント**
   - コメント
   - README更新
   - API仕様

## 🚀 自動化

### pre-commitフック
```bash
# セットアップ
cp scripts/git-hooks/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit
```

### CI/CD統合
- コミット時：自動テスト実行
- PR時：コードレビュー自動化
- マージ時：自動デプロイ

## 📈 メトリクス

### コミット頻度
- 理想：1日3-5コミット
- 最大：1コミット/1機能

### PR サイズ
- 小：~100行
- 中：100-500行
- 大：500行以上（要分割検討）

## 🎓 ベストプラクティス

### Do's ✅
- 小さく頻繁にコミット
- 明確で説明的なメッセージ
- 1コミット1目的
- テストを含める
- ドキュメントを更新

### Don'ts ❌
- 巨大なコミット
- 曖昧なメッセージ（"fix", "update"）
- 複数の変更を1コミットに
- テストなしのコミット
- 破壊的変更の非明記

## 🔧 トラブルシューティング

### コンフリクト解決
```bash
# 最新のdevelopを取得
git checkout develop
git pull origin develop

# 自分のブランチに戻ってリベース
git checkout feature/my-feature
git rebase develop

# コンフリクト解決
# ... 手動で解決 ...
git add .
git rebase --continue
```

### コミットの修正
```bash
# 直前のコミットメッセージ修正
git commit --amend

# 複数のコミットをまとめる
git rebase -i HEAD~3
```

## 📚 参考資料

- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Git Best Practices](https://git-scm.com/book/en/v2)

## 🔄 更新履歴

### 2025-01-04
- GitHub Flowコマンド体系の確立
- gfエイリアスの実装
- ベストプラクティスの文書化
