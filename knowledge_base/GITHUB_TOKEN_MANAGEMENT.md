# GitHub Token管理ガイド

## 🔑 現在の有効トークン
```
環境変数 GITHUB_TOKEN に保存
~/.git-credentials に保存
```

## ⚠️ 無効な古いトークン
- `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` (期限切れ)

## 🔄 トークン更新方法

### 自動更新スクリプト
```bash
/home/aicompany/ai_co/scripts/update-github-token.sh
```

### トークンが保存される場所
1. **環境変数**: `GITHUB_TOKEN`
2. **Git認証**: `~/.git-credentials`
3. **GitHub CLI**: `~/.config/gh/hosts.yml`
4. **プロジェクト設定**: `/home/aicompany/ai_co/.env`
5. **シェル設定**: `~/.bashrc`, `~/.profile`

### トークンエラー時の対処法
```bash
# 1. 環境変数を更新
export GITHUB_TOKEN="<your-valid-token>"

# 2. Git remote URLを更新
git remote set-url origin https://ext-maru:$GITHUB_TOKEN@github.com/ext-maru/ai-co.git

# 3. 自動更新スクリプトを実行
/home/aicompany/ai_co/scripts/update-github-token.sh
```

## 📌 重要な注意事項
- **古いトークンを見つけたら即座に新しいトークンに置き換える**
- **環境変数の`GITHUB_TOKEN`が最も頻繁に問題を起こす**
- **pushできない時は最初にトークンを確認する**

## 🤖 クロードエルダーへの指示
1. Git push時に認証エラーが出たら、まずこのドキュメントを確認
2. 自動更新スクリプトを実行
3. それでも解決しない場合は、各設定ファイルを手動確認

---
最終更新: 2025-01-25