# 📚 Elders Guild Knowledge Base

## 🏛️ 概要

Elders Guild Knowledge Baseは、プロジェクトの全知識を体系的に整理した中央リポジトリです。
2025年7月21日に大規模な再編成を実施し、検索性と保守性が大幅に向上しました。

## 🗂️ ディレクトリ構造

```
knowledge_base/
├── 📚 core/                     # コア知識（統合済み、最新版のみ）
│   ├── identity/               # アイデンティティ・組織構造
│   ├── protocols/              # プロトコル・ルール・標準
│   │   └── ELDERS_GUILD_MASTER_KB.md  # ⭐ マスターナレッジベース v6.2
│   └── guides/                 # 開発ガイド・ベストプラクティス
│
├── 🏛️ elder_council/            # エルダー評議会関連
│   ├── decisions/              # 決定事項
│   ├── requests/               # リクエスト
│   ├── reports/                # レポート
│   └── archives/               # 過去の評議会記録（2025年7月）
│
├── 🧙‍♂️ four_sages/              # 4賢者システム
│   ├── knowledge_sage/         # ナレッジ賢者
│   ├── task_sage/              # タスク賢者
│   ├── incident_sage/          # インシデント賢者
│   ├── rag_sage/               # RAG賢者
│   ├── consultations/          # 相談記録
│   ├── grimoires/              # 魔法書（実装ガイド）
│   └── meetings/               # 会議記録
│
├── 🔧 technical/                # 技術文書
│   ├── infrastructure/         # インフラ関連
│   │   ├── docker/            # Docker関連（11ファイル）
│   │   └── postgresql/        # PostgreSQL関連（5ファイル）
│   ├── implementations/        # 実装詳細
│   ├── architecture/           # アーキテクチャ設計
│   └── integrations/           # 統合・連携
│
├── 📈 projects/                 # プロジェクト管理
│   ├── phases/                 # フェーズ管理
│   ├── progress/               # 進捗レポート
│   ├── reports/                # プロジェクトレポート
│   └── retrospectives/         # 振り返り
│
├── 🗃️ archives/                 # アーカイブ（古いバージョン、非アクティブ）
│   ├── versions/               # 過去バージョン（MASTER_KB v5.3-v6.1）
│   ├── deprecated/             # 非推奨・廃止
│   └── historical/             # 歴史的記録（elder_greetings等）
│
└── 📊 data/                     # データファイル
    ├── databases/              # .dbファイル（3個）
    └── configs/                # 設定・JSON等
```

## 🌟 主要ドキュメント

### コア知識
- **[ELDERS_GUILD_MASTER_KB.md](core/protocols/ELDERS_GUILD_MASTER_KB.md)** - システム全体の統合知識（v6.2）
- **[CLAUDE_ELDER_IDENTITY_CORE.md](core/identity/CLAUDE_ELDER_IDENTITY_CORE.md)** - クロードエルダーのアイデンティティ
- **[CLAUDE_TDD_GUIDE.md](core/guides/CLAUDE_TDD_GUIDE.md)** - TDD開発完全ガイド

### 4賢者システム
- **[README.md](four_sages/README.md)** - 4賢者システム概要
- **[MASTER_INDEX.md](four_sages/MASTER_INDEX.md)** - 4賢者関連の総合インデックス

### 技術インフラ
- **[Docker Best Practices](technical/infrastructure/docker/)** - Docker運用ガイド
- **[PostgreSQL Integration](technical/infrastructure/postgresql/)** - PostgreSQL統合ガイド

## 📊 整理統計（2025年7月21日）

### 整理前
- **総ファイル数**: 527ファイル
- **ルート散乱**: 約250ファイル
- **重複率**: 約30%

### 整理後
- **構造化率**: 95%以上
- **重複排除**: 100%完了
- **検索性向上**: 体系的分類により大幅改善

## 🔍 検索ガイド

### トピック別検索
- **評議会決定**: `elder_council/decisions/`
- **技術仕様**: `technical/*/`
- **開発ガイド**: `core/guides/`
- **プロジェクト進捗**: `projects/reports/`

### 時系列検索
- **最新**: `core/` ディレクトリ
- **2025年7月**: 各ディレクトリ内の日付付きファイル
- **過去バージョン**: `archives/versions/`

## 🛠️ メンテナンスガイド

### 新規ドキュメント追加時
1. 適切なディレクトリを選択（上記構造参照）
2. 命名規則に従う（下記参照）
3. 既存ドキュメントとの重複を確認
4. 必要に応じてインデックスを更新

### 命名規則
- **日付フォーマット**: `YYYY-MM-DD` (例: 2025-07-21)
- **ファイル名**: `snake_case` 推奨
- **ディレクトリ名**: 小文字、アンダースコア区切り

## 📝 更新履歴

- **2025-07-21**: 大規模再編成実施
  - 527ファイルを体系的に整理
  - 重複ファイルを完全排除
  - 新ディレクトリ構造の確立
  
- **2025-07-20**: MASTER_KB v6.2統合
  - AI_COMPANY版とELDERS_GUILD版を統合
  - プロジェクト個別管理体制の追加

## 🔗 関連リンク

- [プロジェクトルート](../)
- [CLAUDE.md](../CLAUDE.md) - Claude CLI開発ガイド
- [ワーカーディレクトリ](../workers/)
- [ライブラリディレクトリ](../libs/)

---

最終更新: 2025年7月21日 01:17 JST