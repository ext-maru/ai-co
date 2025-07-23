# Elder Tree v2 プロジェクトドキュメント

**最終更新**: 2025年7月23日  
**バージョン**: 2.0.0  
**ステータス**: ✅ **本番環境準備完了**

## 📋 プロジェクト概要

Elder Tree v2は、4賢者システムとElder Flowを中心とした分散AIアーキテクチャです。python-a2a 0.5.9への移行に伴い、Flaskベースの統一アーキテクチャに全面移行しました。

## 🏗️ アーキテクチャ

```
Elder Tree v2
├── インフラ層（PostgreSQL, Redis, Consul）
├── 4賢者層（Knowledge, Task, Incident, RAG）
├── ワークフロー層（Elder Flow）
├── サーバント層（Code Crafter等）
└── モニタリング層（Prometheus, Grafana）
```

## 📊 現在の状態

- **動作状況**: 11/11サービス正常動作（100%）
- **品質基準**: Iron Will 100%準拠
- **テストカバレッジ**: 実装予定
- **ドキュメント**: 完備

## 🚀 クイックスタート

```bash
# セットアップ
git clone <repository>
cd elder-tree-v2
docker-compose up -d

# 動作確認
curl http://localhost:50051/health
```

詳細は[完全セットアップガイド](../../guides/elder-tree-v2/complete-setup-guide.md)を参照してください。

## 📁 ドキュメント構成

### セットアップ・運用
- [完全セットアップガイド](../../guides/elder-tree-v2/complete-setup-guide.md)
- [トラブルシューティング](../../guides/troubleshooting/docker-container-restart-loop.md)

### 技術ドキュメント
- [Flask移行ノウハウ集](../../guides/migration/flask-migration-knowhow.md)
- [アーキテクチャ設計書](architecture.md)
- [API仕様書](api-specification.md)

### プロジェクト履歴
- [Issue #310: Flask移行大改修](issues/issue-310-summary.md)
- [Issue #311: Docker環境修正](issues/issue-311-summary.md)

### 品質レポート
- [完全動作報告書](reports/complete-operation-report.md)
- [最終品質監査報告書](reports/final-quality-audit.md)

## 🔧 主要コンポーネント

### 4賢者システム
| サービス | ポート | 役割 |
|---------|-------|------|
| Knowledge Sage | 50051 | 知識管理・学習 |
| Task Sage | 50052 | タスク管理・優先順位付け |
| Incident Sage | 50053 | インシデント対応 |
| RAG Sage | 50054 | 検索・情報取得 |

### ワークフロー
| サービス | ポート | 役割 |
|---------|-------|------|
| Elder Flow | 50100 | 5段階自動化ワークフロー |

### サーバント層
| サービス | ポート | 役割 |
|---------|-------|------|
| Code Crafter | 50201 | コード生成 |

## 🛠️ 技術スタック

- **言語**: Python 3.11
- **フレームワーク**: Flask
- **コンテナ**: Docker, Docker Compose
- **データベース**: PostgreSQL 16
- **キャッシュ**: Redis 7
- **モニタリング**: Prometheus, Grafana
- **サービスディスカバリ**: Consul

## 📈 今後の計画

1. **Phase 1**: テストカバレッジ向上（目標: 90%）
2. **Phase 2**: Kubernetes対応
3. **Phase 3**: 本番環境展開
4. **Phase 4**: パフォーマンス最適化

## 🤝 貢献方法

1. Issueの作成
2. Feature Branchでの開発
3. TDD（Red-Green-Refactor）の実践
4. Iron Will原則の遵守
5. Pull Requestの作成

## 📞 サポート

- **技術サポート**: エルダーズギルド技術部門
- **Issue管理**: GitHub Issues
- **ドキュメント**: 本ディレクトリ

---

**プロジェクトオーナー**: グランドエルダーmaru  
**技術責任者**: クロードエルダー（Claude Elder）  
**品質保証**: Iron Will 100%準拠