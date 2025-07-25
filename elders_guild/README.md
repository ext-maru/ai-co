# 🏛️ 新エルダーズギルド (New Elders Guild)

**AIは判断役、人間は実行役** - 新しい開発パラダイム

## 📁 ディレクトリ構造

```
new_system/
├── cli/                    # Elder CLIコマンドシステム
├── quality/               # 品質チェックエンジン（自動実行）
├── quality_servants/      # AIサーバント（判断専門）
├── docs/                  # ドキュメント
├── scripts/              # セットアップ・実行スクリプト
└── tests/                # テスト
```

## 🚀 クイックスタート

### 1. Elder CLIのセットアップ
```bash
cd elders_guild/new_system
./elder_tree/elder_servants/dwarf_tribe/tools/setup-elder-commands.sh
```

### 2. 基本コマンド
```bash
# AIと対話
elder send "OAuth2.0認証を実装して"

# 品質チェック実行
elder flow execute "コード品質チェック"

# ヘルプ
elder help
```

## 🎯 コアコンセプト

### Execute & Judge パターン
1. **Execute（実行）**: プログラムが確実に実行
2. **Judge（判断）**: AIが結果を評価
3. **Human Approval（承認）**: 人間が最終決定

### 品質パイプライン
- **Block A**: 静的解析（QualityWatcherServant）
- **Block B**: テスト品質（TestForgeServant）
- **Block C**: 総合評価（ComprehensiveGuardianServant）

## 📚 主要ドキュメント

- [新エルダーズギルド概要](docs/NEW_ELDERS_GUILD_OVERVIEW.md)
- [AI意思決定者の考え方](docs/philosophy/AI_DECISION_MAKER_PARADIGM.md)
- [Elder Commandガイド](docs/guides/ELDER_COMMAND_GUIDE.md)

## 🧪 テスト実行

```bash
# 品質サーバントのテスト
python3 -m pytest tests/quality/test_quality_servants_mock.py -v
```

## ⚠️ 重要な注意

これは**新エルダーズギルド**です。旧システム（4賢者、古代魔法など）は`archives/old_system/`にあります。

---

**"Execute with Certainty, Judge with Intelligence"**