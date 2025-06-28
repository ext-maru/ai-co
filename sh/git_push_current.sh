#!/bin/bash
# git_push_current.sh
# 現状の ~/ai_co ディレクトリをGit管理下に置き、
# 初回コミット＆GitHubにプッシュするシェルスクリプト

set -e

REPO_SSH="git@github.com:ext-maru/ai-co.git"
LOCAL_DIR="$HOME/ai_co"
BRANCH="master"  # 必要に応じ main などに変更してください

cd "$LOCAL_DIR"

# gitリポジトリ初期化
if [ ! -d ".git" ]; then
  echo "Gitリポジトリを初期化します。"
  git init
  git remote add origin "$REPO_SSH"
else
  echo "既にGitリポジトリがあります。"
fi

# 変更追加
git add .

# コミット作成（変更なければスキップ）
git commit -m "Initial commit of current ai_co state" || echo "コミットする変更はありません。"

# リモートにプッシュ（強制プッシュ注意）
git push -u origin "$BRANCH" --force

echo "GitHubへプッシュ完了。"

