# 🔮 AI Elder Cast コマンド体系（最終版）

## 📋 利用可能コマンド

### 1. **ai-elder-cast** (標準版)
```bash
ai-elder-cast
```
- **用途**: 日常的な開発作業
- **サイズ**: 中間版（8KB）
- **内容**: バランス良い必須知識

### 2. **ai-elder-cast-modular** (柔軟版)
```bash
# 使用例
ai-elder-cast-modular                    # デフォルト
ai-elder-cast-modular medium             # 中間版
ai-elder-cast-modular core sages tdd     # 複数セクション組み合わせ
ai-elder-cast-modular --list             # 利用可能セクション一覧
```

#### 利用可能セクション
- **core**: 最小限のアイデンティティ
- **medium**: バランス版（推奨）
- **identity**: 詳細アイデンティティ
- **flow**: Elder Flow設計
- **sages**: 4賢者システム
- **tdd**: TDDガイド
- **dev**: 開発ガイド（大容量注意）

## 🎯 推奨使用パターン

### 軽作業・質問
```bash
ai-elder-cast-modular core
```

### 通常開発
```bash
ai-elder-cast
```

### TDD開発
```bash
ai-elder-cast-modular medium tdd
```

### Elder Flow開発
```bash
ai-elder-cast-modular medium flow sages
```

### 複雑な開発
```bash
ai-elder-cast-modular medium flow sages tdd
```

## 📊 削除されたコマンド

以下は削除されました（読み込み不可能なため）：
- ~~ai-elder-cast-optimized full~~
- ~~ELDER_KNOWLEDGE_CONTEXT.md~~ (144KB版)

## 🚀 移行完了

これで、**実際に動作する**コマンドのみが残りました！
