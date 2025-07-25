# Elders Guild プロジェクトドキュメント

**最終更新**: 2025年7月23日  
**バージョン**: 3.0.0  
**ステータス**: ✅ **統合完了**

## 📋 プロジェクト概要

Elders Guildは、`elder_tree_v2`と`elders_guild_dev`を統合した統一プロジェクトです。
4賢者システムとElder Flowを中心とした分散AIアーキテクチャを実装しています。

## 🏗️ 統合履歴

### 2025年7月23日 - 統合完了
- `elder_tree_v2`と`elders_guild_dev`を`elders_guild`に統合
- Docker環境の統一
- ドキュメントの整理

### 統合前の構成
- `elder_tree_v2/`: Docker Compose環境での本番実装
- `elders_guild_dev/`: 開発中の個別実装（Task Sage等）

## 📁 新ディレクトリ構造

```
/home/aicompany/ai_co/elders_guild/
├── src/                    # 統合されたソースコード
│   ├── elder_tree/        # Elder Tree実装
│   ├── shared_libs/       # 共有ライブラリ
│   ├── task_sage/         # Task Sage実装
│   ├── knowledge_sage/    # Knowledge Sage実装
│   ├── incident_sage/     # Incident Sage実装
│   └── rag_sage/          # RAG Sage実装
├── docker/                # Docker設定
├── tests/                 # テストスイート
├── scripts/               # ヘルパースクリプト
├── config/                # 設定ファイル
└── docs/                  # プロジェクトドキュメント
```

## 🚀 使用方法

プロジェクトルートは `/home/aicompany/ai_co/elders_guild/` です。

```bash
cd /home/aicompany/ai_co/elders_guild/

# Docker環境の起動
cd docker
docker-compose up -d

# 開発環境
poetry install
poetry run pytest
```

## 📊 移行ガイド

### 旧パスから新パスへ

| 旧パス | 新パス |
|--------|--------|
| `elder_tree_v2/src/` | `elders_guild/src/elder_tree/` |
| `elders_guild_dev/task_sage/` | `elders_guild/src/task_sage/` |
| `elder_tree_v2/docker-compose.yml` | `elders_guild/docker/docker-compose.yml` |

### 設定ファイルの更新
- PostgreSQLデータベース名: `elders_guild_db`
- ネットワーク名: `elders_guild_network`
- コンテナプレフィックス: `elders_guild_`

## 📚 関連ドキュメント

- [統合前のElder Tree v2ドキュメント](../elder-tree-v2/README.md)
- [フォルダ構造説明書](../../architecture/elders-guild-folder-structure.md)
- [Issue #312: フォルダ統合計画](../../issues/issue-312-elders-guild-folder-consolidation.md)

## 🤝 今後の計画

1. **Phase 1**: テストカバレッジ向上（目標: 90%）
2. **Phase 2**: CI/CDパイプライン整備
3. **Phase 3**: Kubernetes対応
4. **Phase 4**: 本番環境展開

---

**プロジェクトオーナー**: グランドエルダーmaru  
**技術責任者**: クロードエルダー（Claude Elder）