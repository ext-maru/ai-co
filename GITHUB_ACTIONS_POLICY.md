# ⚠️ GitHub Actions 無効化ポリシー

## 🚨 重要指示

**GitHub Actionsは、グランドエルダーmaruの明示的な許可があるまで、完全無効化を維持すること。**

## 📅 制定日
2025年1月19日

## 🔴 現在の状態
- **状態**: 完全無効化
- **理由**: 不要なメール通知の防止
- **保存場所**: `.github/workflows.disabled/`

## 📋 ポリシー詳細

### 1. 無効化を維持すべきワークフロー
```
.github/workflows.disabled/
├── ci.yml
├── elder-flow-complete.yml
├── elders-guild-ci.yml
├── elders-guild-deploy.yml
├── enhanced-ci.yml
├── incident-knights-autofix.yml
├── incident-knights.yml
├── issue_auto_management.yml
├── sub_issue_automation.yml
├── test-coverage.yml
├── test.yml
└── week4-final-cicd.yml
```

### 2. 禁止事項
- ❌ `.github/workflows/`へのファイル移動
- ❌ 新規ワークフローの作成
- ❌ 既存ワークフローの有効化
- ❌ `on:`トリガーの追加

### 3. 許可事項
- ✅ ローカルでの自動化スクリプト実行
- ✅ 手動でのGitHub API呼び出し
- ✅ CLIツールの使用

## 🤖 クロードエルダーへの指示

**この指示は最優先事項として扱い、以下を厳守すること：**

1. GitHub Actionsに関する作業要求があった場合、このポリシーを参照
2. 「GitHub Actionsを有効化しましょう」などの提案は一切しない
3. 代替手段（ローカルスクリプト、手動実行）を提案する

## 📝 変更履歴

- 2025/01/19: 初版作成 - 完全無効化ポリシー制定

---

**最終更新**: 2025年1月19日
**承認者**: グランドエルダーmaru
**ステータス**: 有効