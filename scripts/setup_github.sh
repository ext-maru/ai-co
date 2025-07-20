#!/bin/bash
# GitHub連携設定ヘルパー

echo "=== 🐙 GitHub連携設定 ==="
echo ""

# 1. トークン設定
if [ -z "$GITHUB_TOKEN" ]; then
    echo "GitHubトークンが未設定です"
    echo "1. https://github.com/settings/tokens にアクセス"
    echo "2. Generate new token (classic) をクリック"
    echo "3. repo, workflow 権限を選択"
    echo "4. トークンをコピー"
    echo ""
    read -p "GitHubトークンを入力: " token
    export GITHUB_TOKEN="$token"
    echo "export GITHUB_TOKEN='$token'" >> ~/.bashrc
fi

# 2. Git設定
echo ""
echo "Git設定中..."
git config user.name "AI Company Bot" 2>/dev/null || true
git config user.email "ai-company@example.com" 2>/dev/null || true

# 3. リポジトリ確認
cd /root/ai_co
repo_url=$(git config --get remote.origin.url 2>/dev/null || echo "")
if [ -z "$repo_url" ]; then
    echo "⚠️ Gitリポジトリが設定されていません"
    read -p "GitHubリポジトリURL (例: git@github.com:user/repo.git): " repo_url
    git remote add origin "$repo_url" 2>/dev/null || true
fi

# 4. 設定ファイル更新
sed -i "s|GITHUB_REPO_URL=.*|GITHUB_REPO_URL=\"$repo_url\"|" config/github.conf
sed -i "s|GITHUB_TOKEN=.*|GITHUB_TOKEN=\"$GITHUB_TOKEN\"|" config/github.conf

echo ""
echo "✅ GitHub連携設定完了"
echo "テスト: python3 scripts/test_github_integration.py"
