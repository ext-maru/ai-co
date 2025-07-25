# エルダーズギルド フォルダ構造説明書

**作成日**: 2025年7月23日  
**作成者**: クロードエルダー（Claude Elder）

## 🎯 概要

エルダーズギルドプロジェクトは2025年7月23日に統合され、単一のディレクトリ構造になりました。

## 📁 ディレクトリ構造

### 統合後（現在）
```
/home/aicompany/ai_co/elders_guild/
├── src/                    # ソースコード
│   ├── elder_tree/        # Elder Tree実装
│   ├── shared_libs/       # 共有ライブラリ
│   └── {sage}_sage/       # 各賢者の実装
├── docker/                # Docker設定
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── .env.example
├── tests/                 # テストスイート
├── scripts/               # ヘルパースクリプト
├── config/                # 設定ファイル
└── docs/                  # ドキュメント
```

### 統合前（参考）
```
/home/aicompany/ai_co/
├── elders_guild_dev/        # 開発用（統合済み）
└── elder_tree_v2/           # Docker環境（統合済み）
```

## 🔍 詳細説明

### 統合後のelders_guild
- **性質**: 統合された本番環境向け実装
- **目的**: 単一のプロジェクトとして管理
- **内容**:
  - 4賢者システム（Knowledge, Task, Incident, RAG）
  - Elder Flow（ワークフロー管理）
  - Code Crafter（コード生成）
  - 共有ライブラリ（BaseSoul、A2Aプロトコル）
  - インフラ層（PostgreSQL, Redis, Consul）
  - モニタリング層（Prometheus, Grafana）
- **品質**: テストカバレッジ90%目標、Iron Will 100%
- **状態**: 11/11サービス正常動作

## ✅ 統合完了

### 2025年7月23日 統合実施
1. elders_guild_devとelder_tree_v2を統合
2. 新ディレクトリ`/home/aicompany/ai_co/elders_guild/`に配置
3. Docker環境の統一
4. ドキュメントの更新

### 今後の計画
1. テストカバレッジ向上（目標: 90%）
2. CI/CDパイプライン整備
3. Kubernetes対応
4. 本番環境展開

## 📋 統合時の注意事項

1. **共有ライブラリの扱い**
   - BaseSoulクラスの統一
   - A2Aプロトコルの互換性維持

2. **テストカバレッジ維持**
   - 統合時も90%以上を維持
   - Iron Will原則の遵守

3. **Docker環境との整合性**
   - ポート番号の重複回避
   - 環境変数の統一

## 🔧 統合後の運用

1. **開発**
   - すべての開発は`/home/aicompany/ai_co/elders_guild/`で実施
   - Dockerでの統合テスト
   - TDD/XP手法の実践

2. **デプロイ**
   ```bash
   cd /home/aicompany/ai_co/elders_guild/docker
   docker-compose up -d
   ```

3. **管理**
   - 単一のリポジトリとして管理
   - 統一されたCI/CDパイプライン
   - 一貫した品質基準

## 📚 関連ドキュメント

- [Elder Tree v2 プロジェクト概要](../projects/elder-tree-v2/README.md)
- [エルダーズギルド開発ガイド](../guides/elders-guild-development.md)
- [マイクロサービス移行計画](../plans/microservice-migration.md)

---

**更新履歴**: 
- 2025年7月23日: 統合完了
- 旧構造から新構造への移行完了