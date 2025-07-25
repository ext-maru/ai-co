#!/bin/bash
# Elder Flow強制適用セットアップスクリプト

set -euo pipefail

# カラー定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🏛️ Elder Flow遵守体制セットアップ開始${NC}"

# 1. Git エイリアス設定
echo -e "${YELLOW}📝 Gitエイリアスを設定中...${NC}"
git config --global alias.commit '!git-elder-commit'
git config --global alias.ci '!git-elder-commit'

# 2. bashrcにエイリアス追加
echo -e "${YELLOW}📝 bashエイリアスを設定中...${NC}"
cat >> ~/.bashrc << 'EOF'

# Elder Flow強制適用エイリアス
alias gec='git-elder-commit'
alias eldercommit='git-elder-commit'
EOF

# 3. 使用方法の表示
cat << EOF > /home/aicompany/ai_co/ELDERFLOW_USAGE.md
# Elder Flow使用ガイド

## 🌊 自動適用されるコミット方法

### 方法1: Git エイリアス使用
\`\`\`bash
git commit "feat: 新機能実装"
# または
git ci "fix: バグ修正"
\`\`\`

### 方法2: bashエイリアス使用
\`\`\`bash
gec "feat: 認証システム実装"
# または
eldercommit "fix: エラー修正"
\`\`\`

### 方法3: 直接実行
\`\`\`bash
git-elder-commit "feat: セキュリティ改善"
\`\`\`

## 🚨 重要
以下のキーワードを含むコミットは自動的にElder Flowが適用されます：
- 実装, implement, add, create, build, develop, 新機能
- 修正, fix, bug, エラー, error, 問題, issue
- 最適化, optimize, リファクタリング, refactor, 改善
- セキュリティ, security, 認証, authentication

## 📋 Elder Flow適用を確認する方法
\`\`\`bash
git log --oneline --grep="Elder Flow"
\`\`\`
EOF

echo -e "${GREEN}✅ セットアップ完了！${NC}"
echo ""
echo -e "${BLUE}🎯 今後の使い方:${NC}"
echo -e "  1. ${YELLOW}git commit \"feat: 新機能実装\"${NC} - 自動的にElder Flowが適用されます"
echo -e "  2. ${YELLOW}gec \"fix: バグ修正\"${NC} - bashエイリアス経由でElder Flow適用"
echo -e "  3. ${YELLOW}eldercommit \"改善: パフォーマンス最適化\"${NC} - 明示的なElder Flow適用"
echo ""
echo -e "${GREEN}🏛️ Elder Flow遵守体制が確立されました！${NC}"