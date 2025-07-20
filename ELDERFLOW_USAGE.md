# Elder Flow使用ガイド

## 🌊 自動適用されるコミット方法

### 方法1: Git エイリアス使用
```bash
git commit "feat: 新機能実装"
# または
git ci "fix: バグ修正"
```

### 方法2: bashエイリアス使用
```bash
gec "feat: 認証システム実装"
# または
eldercommit "fix: エラー修正"
```

### 方法3: 直接実行
```bash
git-elder-commit "feat: セキュリティ改善"
```

## 🚨 重要
以下のキーワードを含むコミットは自動的にElder Flowが適用されます：
- 実装, implement, add, create, build, develop, 新機能
- 修正, fix, bug, エラー, error, 問題, issue
- 最適化, optimize, リファクタリング, refactor, 改善
- セキュリティ, security, 認証, authentication

## 📋 Elder Flow適用を確認する方法
```bash
git log --oneline --grep="Elder Flow"
```
