# 🏛️ Elders Guild - 統合版

**最終更新**: 2025年7月23日  
**バージョン**: 3.0.0  
**ステータス**: ✅ **統合完了**

## 📋 プロジェクト概要

Elders Guildは、4賢者システムとElder Flowを中心とした分散AIアーキテクチャです。
`elder_tree_v2`と`elders_guild_dev`を統合し、単一のプロジェクトとして管理します。

## 🏗️ アーキテクチャ

```
Elders Guild
├── インフラ層（PostgreSQL, Redis, Consul）
├── 4賢者層（Knowledge, Task, Incident, RAG）
├── ワークフロー層（Elder Flow）
├── サーバント層（Code Crafter等）
└── モニタリング層（Prometheus, Grafana）
```

## 📁 ディレクトリ構造

```
elders_guild/
├── src/                    # ソースコード
│   ├── elder_tree/        # Elder Tree実装（統合済み）
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

## 🚀 クイックスタート

### Docker環境での起動

```bash
# 環境変数の設定
cd docker
cp .env.example .env
# .envファイルを編集

# 全サービスの起動
docker-compose up -d

# 動作確認
docker-compose ps
```

### 開発環境

```bash
# Poetry環境のセットアップ
poetry install

# テストの実行
poetry run pytest

# 個別サービスの起動
poetry run python -m src.elder_tree.agents.knowledge_sage
```

## 📊 サービス一覧

### インフラストラクチャ
| サービス | ポート | 役割 |
|---------|-------|------|
| PostgreSQL | 15432 | データベース |
| Redis | 16379 | キャッシュ・キュー |
| Consul | 8500 | サービスディスカバリ |

### アプリケーション
| サービス | ポート | 役割 |
|---------|-------|------|
| Knowledge Sage | 50051 | 知識管理・学習 |
| Task Sage | 50052 | タスク管理・優先順位付け |
| Incident Sage | 50053 | インシデント対応 |
| RAG Sage | 50054 | 検索・情報取得 |
| Elder Flow | 50100 | ワークフロー管理 |
| Code Crafter | 50201 | コード生成 |

### モニタリング
| サービス | ポート | 役割 |
|---------|-------|------|
| Prometheus | 9090 | メトリクス収集 |
| Grafana | 3000 | ダッシュボード |

## 🧪 テスト実行

```bash
# ユニットテスト
poetry run pytest tests/unit/

# 統合テスト
poetry run pytest tests/integration/

# カバレッジレポート
poetry run pytest --cov=src --cov-report=html
```

## 📋 品質基準

- **テストカバレッジ**: 90%以上
- **Iron Will準拠**: TODO/FIXME/HACK禁止
- **コードレビュー**: 必須
- **ドキュメント**: 完備

## 🔧 開発ガイドライン

### TDD開発フロー

1. **Red Phase**: 失敗するテストを書く
2. **Green Phase**: 最小限の実装でテストを通す
3. **Refactor Phase**: コードを改善する

### コミット規約

```bash
# Conventional Commits形式
feat: 新機能追加
fix: バグ修正
docs: ドキュメント更新
test: テスト追加・修正
refactor: リファクタリング
chore: その他の変更
```

## 📚 詳細ドキュメント

- [アーキテクチャ設計書](docs/architecture.md)
- [API仕様書](docs/api-specification.md)
- [セットアップガイド](docs/setup-guide.md)
- [トラブルシューティング](docs/troubleshooting.md)

## 🤝 貢献方法

1. Issueの作成
2. Feature Branchでの開発
3. TDDの実践
4. Pull Requestの作成

## 📞 サポート

- **技術サポート**: エルダーズギルド技術部門
- **Issue管理**: GitHub Issues
- **ドキュメント**: 本ディレクトリ

---

**プロジェクトオーナー**: グランドエルダーmaru  
**技術責任者**: クロードエルダー（Claude Elder）  
**品質保証**: Iron Will 100%準拠