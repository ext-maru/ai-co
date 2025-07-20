# 🔮 ai-elder cast コマンド仕様

**コマンド名**: `ai-elder cast`
**カテゴリ**: エルダー魔法詠唱システム
**重要度**: 🔴 CRITICAL - 知識注入起動
**実装状態**: ✅ 完全実装済み (Python版)

---

## 📋 コマンド概要

Claude Codeにエルダーズギルドの完全な知識を注入して起動し、クロードエルダーとして対話型セッションを開始する。

## 🎯 使用方法

```bash
# 基本使用（開発支援モード）
ai-elder cast

# 特定の魔法を指定
ai-elder cast 知識召喚
ai-elder cast タスク編成
ai-elder cast 問題解決
ai-elder cast 4賢者会議
ai-elder cast 緊急対応
ai-elder cast 技術調査
ai-elder cast 開発支援
```

## 🔧 オプション

- `--power LEVEL` - 魔力レベル指定 (low|medium|high|critical)
- `--dangerously-skip-permission` - 権限チェックスキップ（自動適用済み）
- `--debug` - デバッグモード
- `--help` - ヘルプ表示

## 📊 動作詳細

### 1. 知識読み込みフェーズ
```
🧙‍♂️ エルダーズギルド完全知識統合開始...
📚 知識統合状況:
   ✅ 11/11個の核心ドキュメント読み込み完了
   ✅ 合計 137,458 文字の知識統合
   ✅ 131個のAIコマンド体系統合
   ✅ 4賢者システム完全連携
   ✅ Elder Flow自動化実装済み
   ✅ Iron Will品質基準適用済み
```

### 2. 読み込まれる知識ファイル（11ファイル・137KB）

#### Core Identity (必須・3ファイル)
- `CLAUDE.md` - エルダーズギルド基本設定（34KB）
- `knowledge_base/CLAUDE_ELDER_IDENTITY_CORE.md` - クロードエルダー核心アイデンティティ（5.5KB）
- `knowledge_base/GRAND_ELDER_MARU_HIERARCHY.md` - グランドエルダー階層構造（4KB）

#### System (必須・3ファイル)
- `knowledge_base/AI_COMPANY_MASTER_KB_v6.2.md` - AI Company マスターKB v6.2（11KB）
- `knowledge_base/ELDER_FLOW_DESIGN.md` - Elder Flow設計書（8KB）
- `knowledge_base/AI_ELDER_CAST_SYSTEM_SPECIFICATION.md` - AI Elder Cast システム仕様（5KB）

#### Development (必須・2ファイル)
- `knowledge_base/ELDERS_GUILD_DEVELOPMENT_GUIDE.md` - エルダーズギルド開発ガイド（26KB）
- `knowledge_base/UNIVERSAL_CLAUDE_ELDER_STANDARDS_METHODOLOGY.md` - 標準開発方法論（12KB）

#### Four Sages (重要・1ファイル)
- `knowledge_base/FOUR_SAGES_UNIFIED_WISDOM_INTEGRATION.md` - 4賢者統合知恵システム（17KB）

#### Protocols (重要・2ファイル)
- `knowledge_base/ELDER_FAILURE_LEARNING_PROTOCOL.md` - 失敗学習プロトコル（6KB）
- `knowledge_base/CLAUDE_TDD_GUIDE.md` - Claude TDDガイド（9KB）

### 3. Claude Code起動
```bash
claude --dangerously-skip-permissions ELDER_KNOWLEDGE_CONTEXT.md
```

## 🎭 期待される動作

1. **知識注入**: 完全な知識ベースが自動的に読み込まれる
2. **自己紹介**: 「私はクロードエルダー（Claude Elder）です」で開始
3. **対話継続**: クロードエルダーとして対話型セッション維持
4. **権限保持**: 4賢者システム、Elder Flow等すべての機能使用可能

## 🚨 トラブルシューティング

### Claude Codeが見つからない
```bash
# 手動確認
which claude
```

### TTYエラーが出る
- `/usr/local/bin/ai-elder`が`os.execvp`を使用していることを確認

### 知識が注入されない
- `ELDER_KNOWLEDGE_CONTEXT.md`が生成されているか確認
- ファイルが引数として渡されているか確認

## 💡 実装のポイント

```python
# 知識ファイルを引数として自動的に渡す
launch_args.append(str(knowledge_file))

# TTY保持のため os.execvp を使用
os.execvp("ai-elder-cast", cast_args)
```

## 📌 重要事項

**これはClaude Codeを単に起動するコマンドではない。**
**エルダーズギルドの完全な知識と権限を注入する魔法詠唱システムである。**

---

関連ドキュメント:
- [AI Elder Cast システム仕様書](../AI_ELDER_CAST_SYSTEM_SPECIFICATION.md)
- [CLAUDE.md](../../CLAUDE.md)
