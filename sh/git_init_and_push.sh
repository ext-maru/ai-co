#!/bin/bash
# git_init_and_push.sh
# 既存フォルダをGit管理化し、GitHubに初回コミット＆プッシュするスクリプト

set -e

GIT_REPO_SSH="git@github.com:ext-maru/ai-co.git"
LOCAL_DIR="/root/ai_co"
BRANCH="master"  # 必要に応じて main に変更してください

cd "$LOCAL_DIR"

if [ ! -d .git ]; then
  echo "Gitリポジトリが存在しません。初期化します。"
  git init
  git remote add origin "$GIT_REPO_SSH"
else
  echo "既にGitリポジトリが存在します。リモートを確認します。"
  git remote set-url origin "$GIT_REPO_SSH"
fi

echo "変更をステージングします。"
git add .

echo "コミットを作成します。"
git commit -m "Initial commit of existing ai_co files" || echo "コミットする変更がありません。"

echo "リモートにプッシュします。"
git push -u origin "$BRANCH" --force

echo "初期化とプッシュが完了しました。"

