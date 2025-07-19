# 🌳 Git ワークフローガイド

## 📋 エルダー評議会令第32号 - Feature Branch戦略

### 🎯 基本原則

1. **1 Issue = 1 Branch = 1 PR** の原則を厳守
2. **mainブランチへの直接プッシュ禁止**
3. **すべての変更はFeature Branch経由**

### 🔧 標準ワークフロー

#### 1. Issue作成
```bash
# GitHub CLIを使用
gh issue create --title "機能の説明" --body "詳細な説明"

# またはPythonスクリプト
export GITHUB_TOKEN=$(gh auth token)
python3 libs/integrations/github/api_implementations/create_issue.py \
  ext-maru/ai-co "タイトル" "本文" --labels enhancement
```

#### 2. Feature Branch作成
```bash
# 専用ツールを使用（推奨）
./scripts/git-feature 31 feature-branch-tools

# 手動の場合
git checkout main
git pull origin main
git checkout -b feature/issue-31-feature-branch-tools
git push -u origin feature/issue-31-feature-branch-tools
```

#### 3. 開発とコミット
```bash
# 開発作業...

# コミット（Issue番号を必ず含める）
git add .
git commit -m "feat: Feature Branch自動化ツール実装 (#31)"

# プッシュ
git push
```

#### 4. Pull Request作成
```bash
# GitHub CLIを使用
gh pr create --title "feat: Issue #31 の実装" \
  --body "$(cat << 'EOF'
## 📋 概要
Issue #31 の実装

## 🔧 変更内容
- [x] git-featureスクリプト作成
- [x] エラーハンドリング実装
- [x] ヘルプメッセージ追加

## 🧪 テスト
- [x] 手動テスト完了

Closes #31
EOF
)"
```

### 🌿 ブランチ命名規則

 < /dev/null |  タイプ | プレフィックス | 用途 |
|--------|---------------|------|
| 新機能 | `feature/` | 新しい機能の追加 |
| バグ修正 | `fix/` | バグの修正 |
| ドキュメント | `docs/` | ドキュメントのみの変更 |
| 雑務 | `chore/` | ビルドプロセスやツールの変更 |

**形式**: `{type}/issue-{number}-{description}`

**例**:
- `feature/issue-31-feature-branch-tools`
- `fix/issue-32-api-error`
- `docs/issue-33-update-readme`
- `chore/issue-34-update-dependencies`

### 📝 コミットメッセージ規則

**形式**: `{type}: {description} (#{issue-number})`

**タイプ**:
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `style`: フォーマット（コードの動作に影響しない）
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: ビルドプロセスやツールの変更

**例**:
- `feat: Feature Branch自動化ツール実装 (#31)`
- `fix: APIエラーハンドリング修正 (#32)`
- `docs: READMEにワークフロー説明追加 (#33)`

### 🔄 マージ戦略

1. **PR作成後**:
   - コードレビューを受ける
   - CIチェックが通ることを確認
   - 承認を得る

2. **マージ方法**:
   - Squash and merge（推奨）: コミット履歴をきれいに保つ
   - Merge commit: 詳細な履歴を保持したい場合

3. **マージ後**:
   - Feature Branchは自動削除される
   - ローカルでも削除する

```bash
# マージ後のローカルブランチ削除
git checkout main
git pull origin main
git branch -d feature/issue-31-feature-branch-tools
```

### 🚨 注意事項

1. **mainブランチの保護**:
   - 直接プッシュは禁止
   - Force pushは絶対に禁止
   - すべての変更はPR経由

2. **コンフリクト解決**:
   ```bash
   # mainの最新を取り込む
   git checkout feature/issue-31-feature-branch-tools
   git pull origin main
   # コンフリクトを解決
   git add .
   git commit -m "chore: resolve merge conflicts"
   git push
   ```

3. **作業中断時**:
   - 必ずコミットしてプッシュ
   - WIP（Work In Progress）でも構わない
   ```bash
   git commit -m "WIP: 作業中断 (#31)"
   git push
   ```

### 🛠️ ツール

#### git-feature スクリプト
Feature Branch作成を自動化するツール

```bash
# 使用方法
./scripts/git-feature <issue-number> <description> [branch-type]

# 例
./scripts/git-feature 31 feature-branch-tools
./scripts/git-feature 32 bug-fix fix
```

#### エイリアス設定（推奨）
```bash
# ~/.bashrc または ~/.zshrc に追加
alias gf='./scripts/git-feature'

# 使用例
gf 31 feature-branch-tools
```

---

**エルダー評議会令第32号**: このワークフローに従わない場合、エルダー評議会による是正指導の対象となります。
