#!/bin/bash
# Update GitHub token across all configurations

# Get token from environment or prompt
if [ -z "$NEW_GITHUB_TOKEN" ]; then
    echo "Please set NEW_GITHUB_TOKEN environment variable with your valid token"
    echo "Example: export NEW_GITHUB_TOKEN='your-token-here'"
    exit 1
fi
NEW_TOKEN="$NEW_GITHUB_TOKEN"
OLD_TOKENS=(
    "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"
    # Add more old tokens here as needed
)

echo "🔄 Updating GitHub tokens..."

# Update environment variable
export GITHUB_TOKEN="$NEW_TOKEN"

# Update git credentials
if [ -f ~/.git-credentials ]; then
    for OLD_TOKEN in "${OLD_TOKENS[@]}"; do
        sed -i "s/$OLD_TOKEN/$NEW_TOKEN/g" ~/.git-credentials
    done
    echo "✅ Updated ~/.git-credentials"
fi

# Update gh CLI config
if [ -f ~/.config/gh/hosts.yml ]; then
    for OLD_TOKEN in "${OLD_TOKENS[@]}"; do
        sed -i "s/$OLD_TOKEN/$NEW_TOKEN/g" ~/.config/gh/hosts.yml
    done
    echo "✅ Updated GitHub CLI config"
fi

# Update shell config files
for config_file in ~/.bashrc ~/.profile ~/.zshrc; do
    if [ -f "$config_file" ]; then
        for OLD_TOKEN in "${OLD_TOKENS[@]}"; do
            if grep -q "$OLD_TOKEN" "$config_file"; then
                sed -i "s/$OLD_TOKEN/$NEW_TOKEN/g" "$config_file"
                echo "✅ Updated $config_file"
            fi
        done
    fi
done

# Update project .env files
find /home/aicompany/ai_co -name ".env*" -type f 2>/dev/null | while read -r env_file; do
    for OLD_TOKEN in "${OLD_TOKENS[@]}"; do
        if grep -q "$OLD_TOKEN" "$env_file"; then
            sed -i "s/$OLD_TOKEN/$NEW_TOKEN/g" "$env_file"
            echo "✅ Updated $env_file"
        fi
    done
done

# Update git remote URLs if they contain old tokens
cd /home/aicompany/ai_co
CURRENT_URL=$(git remote get-url origin 2>/dev/null)
if [[ "$CURRENT_URL" == *"@github.com"* ]]; then
    # Using SSH, keep it
    echo "✅ Git remote using SSH (good)"
else
    # Using HTTPS, update with new token
    git remote set-url origin "https://ext-maru:$NEW_TOKEN@github.com/ext-maru/ai-co.git"
    echo "✅ Updated git remote URL with new token"
fi

echo "✅ Token update complete!"
echo ""
echo "📌 Current token: ${NEW_TOKEN:0:20}..."
echo "📌 To make permanent, add to your shell profile:"
echo "   export GITHUB_TOKEN=\"$NEW_TOKEN\""