# GitHub Flow運用ガイド

## 概要

AI Companyプロジェクトは**GitHub Flow**運用に変更されました。

## GitHub Flowとは

GitHub Flowは軽量なブランチ戦略で、以下の特徴があります：

- **mainブランチのみ**を基準として使用
- 機能開発は**feature/**ブランチで実施
- **Pull Request**を通じてコードレビューとマージ
- 継続的デプロイメントに適したシンプルな運用

## 変更点

### 以前（Git Flow風）
- main/develop の2ブランチ体制
- auto/* プレフィックスの機能ブランチ
- develop中心の開発

### 現在（GitHub Flow）
- **mainブランチ中心**
- **feature/** プレフィックス
- **Pull Request** または直接マージ

## 基本的なワークフロー

### 1. 機能開発開始
```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

### 2. 開発作業
```bash
# 変更を加える
git add .
git commit -m "feat: add new feature"
```

### 3. プッシュとPR作成
```bash
git push origin feature/your-feature-name
gh pr create --title "Add new feature" --body "Description of changes"
```

### 4. マージとクリーンアップ
```bash
# PR承認後、自動でブランチ削除
# またはローカルで削除
git checkout main
git pull origin main
git branch -d feature/your-feature-name
```

## AI自動化システムでの変更

### GitHubFlowManager

- `GitFlowManager` → `GitHubFlowManager` にリネーム
- `auto/*` → `feature/*` ブランチに変更
- `merge_to_develop()` → `create_pull_request()` + `merge_to_main()`

### 自動コミット動作

```python
# 以前
manager.create_feature_branch(task_id)  # auto/task_id
manager.commit_changes()
manager.merge_to_develop(branch_name)

# 現在  
manager.create_feature_branch(task_id)  # feature/task_id
manager.commit_changes()
manager.create_pull_request(branch_name, title, body)  # PR作成試行
# 失敗時は manager.merge_to_main() でフォールバック
```

## GitHub CLI設定

### インストール確認
```bash
gh --version
```

### 認証設定（必要に応じて）
```bash
gh auth login
```

## ブランチ命名規則

### 機能開発
- `feature/task-description`
- `feature/fix-bug-name`
- `feature/add-component-name`

### 例
- `feature/user-authentication`
- `feature/fix-slack-notification`
- `feature/add-health-checker`

## Pull Request

### 自動作成（AI）
- AI Companyシステムが自動でPR作成
- タイトル: `feat: 機能説明`
- 本文: 自動生成された説明

### 手動作成
```bash
gh pr create \
  --title "feat: add user dashboard" \
  --body "Adds user dashboard with metrics display" \
  --base main \
  --head feature/user-dashboard
```

## トラブルシューティング

### GitHub CLI未認証
```bash
gh auth status
gh auth login
```

### PRが作成できない場合
- 自動的に `merge_to_main()` でフォールバック
- 直接mainブランチにマージされる

### 古いブランチの存在
- 旧auto/*ブランチは削除済み
- developブランチも削除済み

## 設定ファイル

### 使用クラス
- `libs/github_flow_manager.py` (旧git_flow_manager.py)
- `GitHubFlowManager` クラス

### 主要メソッド
- `create_feature_branch(task_id)` - feature/ブランチ作成
- `create_pull_request(branch, title, body)` - PR作成
- `merge_to_main(branch)` - 直接マージ（フォールバック）
- `auto_commit_task_result(task_id, files, summary)` - 自動コミット

## まとめ

GitHub Flow導入により：
- ✅ シンプルな運用（mainブランチ中心）
- ✅ Pull Requestによるコードレビュー
- ✅ 継続的デプロイメント対応
- ✅ GitHub標準のワークフロー
- ✅ 不要なブランチ削除とクリーンアップ完了