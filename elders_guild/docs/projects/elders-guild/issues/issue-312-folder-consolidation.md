# Issue #312: エルダーズギルド フォルダ統合計画

**作成日**: 2025年7月23日  
**完了日**: 2025年7月23日  
**担当者**: クロードエルダー（Claude Elder）  
**ステータス**: ✅ **完了**

## 🎯 概要

`elders_guild_dev`と`elder_tree_v2`に分かれていたプロジェクトを統合し、単一の`elders_guild`ディレクトリで管理。

## 📋 背景

### 問題点
1. **コードの重複**: 同じ機能が複数箇所に存在
2. **管理の複雑化**: 2つのディレクトリを別々に管理
3. **開発者の混乱**: どちらで開発すべきか不明確

### 旧構造
- `elders_guild_dev/`: 開発用の一時配置
- `elder_tree_v2/`: Docker環境での本番実装

## 🔧 実施内容

### 1. 新ディレクトリ作成
```bash
/home/aicompany/ai_co/elders_guild/
├── src/          # 統合されたソースコード
├── docker/       # Docker設定
├── tests/        # テストスイート
├── scripts/      # ヘルパースクリプト
├── config/       # 設定ファイル
└── docs/         # ドキュメント
```

### 2. ファイル移行
- elder_tree_v2のDocker環境を移行
- elders_guild_devの実装を統合
- 重複コードの整理

### 3. 設定更新
- データベース名: `elders_guild_db`
- ネットワーク名: `elders_guild_network`
- コンテナプレフィックス: `elders_guild_`

### 4. クリーンアップ
- 旧ディレクトリの削除
- シンボリックリンクの除去

## 📊 成果

- **統合前**: 2つの分散したディレクトリ
- **統合後**: 1つの統一されたディレクトリ
- **動作確認**: 11/11サービス正常動作

## 🚀 技術的詳細

### Docker Compose更新
```yaml
# ビルドコンテキストを親ディレクトリに
build: ..

# 環境に合わせたパス修正
volumes:
  - ../scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
```

### ポート変更
- Task Sage: 50052 → 50062（競合回避）

## 📚 関連ドキュメント

- [統合後のREADME](../README.md)
- [セットアップガイド](../../../guides/elders-guild/complete-setup-guide.md)
- [フォルダ構造説明](../../../architecture/elders-guild-folder-structure.md)
- [統合サマリー](../integration-summary.md)

## 🏷️ ラベル

- enhancement
- architecture
- refactoring
- completed