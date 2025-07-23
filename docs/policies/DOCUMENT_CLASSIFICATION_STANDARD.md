# 🏛️ エルダーズギルド ドキュメント分類標準

**エルダー評議会令第500号 - ドキュメント分類標準化令**  
**制定日**: 2025年7月22日  
**実装責任者**: クロードエルダー  
**承認**: 4賢者評議会（全員一致）

## 🎯 **基本原則**

### **Iron Will原則**
1. **目的明確化**: すべてのドキュメントは用途・対象者・更新頻度が明確
2. **階層統一**: 3階層を超えない構造（root/category/subcategory/document）
3. **命名統一**: 統一的命名規則に厳格準拠
4. **単一責任**: 1ドキュメント = 1目的
5. **依存関係明示**: 関連ドキュメントとの関係性を明記

### **nWo戦略目標**
- **検索効率**: 目標ドキュメントを30秒以内で発見
- **メンテナンス性**: 更新作業の70%削減
- **一元管理**: 散在情報の完全統合
- **品質保証**: 全ドキュメントのIron Will基準遵守

---

## 📁 **統一ディレクトリ構造**

### **🌍 Tier 1: ルートレベル（必須ドキュメント）**
```
/
├── README.md                    # プロジェクト概要（英語）
├── CLAUDE.md                    # エルダーズギルド操作マニュアル（日本語）
├── CHANGELOG.md                 # バージョン履歴
├── LICENSE                      # ライセンス
├── CONTRIBUTING.md              # 貢献ガイドライン
└── .github/                     # GitHub設定
    ├── ISSUE_TEMPLATE/
    ├── PULL_REQUEST_TEMPLATE/
    └── workflows/
```

### **📚 Tier 2: docsディレクトリ（主要分類）**

#### **🎯 Core Categories (6分類)**
```
docs/
├── guides/                      # 利用者向けガイド
├── technical/                   # 技術ドキュメント
├── reports/                     # レポート・分析結果
├── policies/                    # ポリシー・規約
├── api/                         # API仕様・リファレンス
└── projects/                    # プロジェクト固有ドキュメント
```

### **🗃️ Tier 3: 専門ディレクトリ（特定用途）**
```
knowledge_base/                  # 知識管理システム
archives/                        # 完了・廃止ファイル
elder_tree_v2/docs/              # Elder Tree v2専用
deployment/docs/                 # デプロイ関連
scripts/docs/                    # スクリプト関連
```

---

## 📋 **詳細分類ルール**

### **📖 guides/ - ユーザーガイド**
```
guides/
├── user-guides/                 # 一般利用者向け
│   ├── quickstart.md            # クイックスタート
│   ├── basic-usage-guide.md     # 基本操作
│   ├── advanced-features.md     # 高度な機能
│   └── troubleshooting.md       # トラブルシューティング
├── developer-guides/            # 開発者向け
│   ├── contribution-guide.md    # 貢献ガイド
│   ├── architecture-overview.md # アーキテクチャ
│   ├── coding-standards.md      # コーディング規約
│   └── testing-guide.md         # テストガイド
├── administrator-guides/        # 管理者向け
│   ├── deployment-guide.md      # デプロイガイド
│   ├── maintenance-guide.md     # メンテナンス
│   ├── security-guide.md        # セキュリティ
│   └── backup-recovery.md       # バックアップ・復旧
└── workflow-guides/             # ワークフロー
    ├── github-workflow.md       # GitHubフロー
    ├── issue-management.md      # Issue管理
    ├── code-review-process.md   # コードレビュー
    └── release-process.md       # リリースプロセス
```

### **🔧 technical/ - 技術ドキュメント**
```
technical/
├── architecture/                # アーキテクチャ
│   ├── system-overview.md       # システム全体図
│   ├── component-design.md      # コンポーネント設計
│   ├── data-flow.md             # データフロー
│   └── integration-patterns.md  # 統合パターン
├── implementation/              # 実装詳細
│   ├── elder-tree-v2.md         # Elder Tree v2実装
│   ├── four-sages-system.md     # 4賢者システム
│   ├── unified-systems.md       # 統合システム
│   └── database-design.md       # データベース設計
├── specifications/              # 仕様書
│   ├── requirements.md          # 要件定義
│   ├── functional-spec.md       # 機能仕様
│   ├── non-functional-spec.md   # 非機能要件
│   └── interface-spec.md        # インターフェース仕様
├── deployment/                  # デプロイ・運用
│   ├── infrastructure.md        # インフラ構成
│   ├── monitoring.md            # 監視設計
│   ├── logging.md               # ログ設計
│   └── security-design.md       # セキュリティ設計
└── research/                    # 技術調査
    ├── technology-selection.md  # 技術選定
    ├── performance-analysis.md  # 性能分析
    ├── security-analysis.md     # セキュリティ分析
    └── feasibility-studies.md   # 実現可能性調査
```

### **📊 reports/ - レポート・分析**
```
reports/
├── development/                 # 開発レポート
│   ├── sprint-reports/          # スプリントレポート
│   ├── milestone-reports/       # マイルストーンレポート
│   ├── completion-reports/      # 完了レポート
│   └── progress-tracking/       # 進捗追跡
├── quality/                     # 品質レポート
│   ├── code-quality/            # コード品質
│   ├── test-coverage/           # テストカバレッジ
│   ├── security-audit/          # セキュリティ監査
│   └── performance-benchmark/   # 性能ベンチマーク
├── analysis/                    # 分析レポート
│   ├── impact-analysis/         # 影響分析
│   ├── risk-assessment/         # リスク評価
│   ├── cost-benefit/            # 費用対効果
│   └── technical-debt/          # 技術負債
└── operations/                  # 運用レポート
    ├── incident-reports/        # インシデントレポート
    ├── maintenance-logs/        # メンテナンス記録
    ├── usage-analytics/         # 利用分析
    └── capacity-planning/       # キャパシティ計画
```

### **📜 policies/ - ポリシー・規約**
```
policies/
├── development/                 # 開発ポリシー
│   ├── coding-standards.md      # コーディング規約
│   ├── testing-policy.md        # テストポリシー
│   ├── code-review-policy.md    # コードレビュー規約
│   └── git-workflow-policy.md   # Gitワークフロー規約
├── quality/                     # 品質ポリシー
│   ├── quality-standards.md     # 品質基準
│   ├── iron-will-standard.md    # Iron Will基準
│   ├── oss-first-policy.md      # OSS First方針
│   └── security-policy.md       # セキュリティポリシー
├── operations/                  # 運用ポリシー
│   ├── deployment-policy.md     # デプロイポリシー
│   ├── incident-response.md     # インシデント対応
│   ├── backup-policy.md         # バックアップポリシー
│   └── monitoring-policy.md     # 監視ポリシー
└── governance/                  # ガバナンス
    ├── elder-council-charter.md # エルダー評議会憲章
    ├── decision-process.md      # 意思決定プロセス
    ├── escalation-matrix.md     # エスカレーションマトリクス
    └── compliance-requirements.md # コンプライアンス要件
```

### **🔗 api/ - API・インターフェース**
```
api/
├── reference/                   # APIリファレンス
│   ├── rest-api.md              # REST API
│   ├── graphql-api.md           # GraphQL API
│   ├── websocket-api.md         # WebSocket API
│   └── rpc-api.md               # RPC API
├── guides/                      # APIガイド
│   ├── getting-started.md       # API利用開始
│   ├── authentication.md       # 認証・認可
│   ├── rate-limiting.md         # レート制限
│   └── error-handling.md        # エラーハンドリング
├── schemas/                     # スキーマ定義
│   ├── openapi.yaml             # OpenAPI仕様
│   ├── graphql.schema           # GraphQLスキーマ
│   ├── json-schema/             # JSONスキーマ
│   └── proto/                   # Protocol Buffers
└── examples/                    # サンプル・例
    ├── curl-examples.md         # cURLサンプル
    ├── sdk-examples/            # SDK使用例
    ├── integration-examples/    # 統合例
    └── postman-collection.json  # Postmanコレクション
```

### **🎯 projects/ - プロジェクト管理**
```
projects/
├── active/                      # アクティブプロジェクト
│   ├── {project-name}/          # プロジェクト別
│   │   ├── README.md            # プロジェクト概要
│   │   ├── requirements.md      # 要件定義
│   │   ├── design-doc.md        # 設計書
│   │   ├── implementation-plan.md # 実装計画
│   │   ├── test-plan.md         # テスト計画
│   │   ├── deployment-plan.md   # デプロイ計画
│   │   └── progress-tracking.md # 進捗管理
│   └── templates/               # プロジェクトテンプレート
├── completed/                   # 完了プロジェクト
│   └── {project-name}/          # 完了プロジェクト（アーカイブ前）
└── planning/                    # 計画中プロジェクト
    └── proposals/               # プロジェクト提案
```

---

## 📝 **命名規則**

### **ファイル名規則**
```bash
# 基本パターン
{category}-{subcategory}-{description}.md

# 例
user-guide-quickstart.md
technical-architecture-overview.md
report-quality-code-analysis.md
policy-development-coding-standards.md
```

### **ディレクトリ名規則**
```bash
# 基本原則
- 小文字のみ
- ハイフン区切り
- 動詞は避ける
- 複数形を使用

# 良い例
user-guides/
api-reference/
test-reports/
security-policies/

# 悪い例
UserGuides/
API_Reference/
testReports/
SecurityPolicies/
```

### **文書内セクション規則**
```markdown
# Level 1: ドキュメントタイトル（絵文字 + タイトル）
## Level 2: 主要セクション（絵文字 + セクション名）
### Level 3: サブセクション（**太字** + セクション名）
#### Level 4: 詳細項目（通常テキスト）
```

---

## 🔍 **メタデータ標準**

### **すべてのドキュメントに必須**
```markdown
---
title: "ドキュメントタイトル"
description: "ドキュメントの説明（1-2行）"
category: "primary-category"
subcategory: "secondary-category"
audience: "target-audience"  # developers, users, administrators, all
difficulty: "beginner|intermediate|advanced"
last_updated: "YYYY-MM-DD"
version: "X.Y.Z"
status: "draft|review|approved|deprecated"
related_docs:
  - "path/to/related-doc.md"
  - "path/to/another-doc.md"
dependencies:
  - "required-system-or-knowledge"
author: "author-name"
reviewers:
  - "reviewer-1"
  - "reviewer-2"
tags:
  - "tag1"
  - "tag2"
---
```

### **レポート固有メタデータ**
```markdown
report_type: "sprint|milestone|quality|security|performance"
period: "YYYY-MM-DD to YYYY-MM-DD"
scope: "component|system|project"
stakeholders:
  - "stakeholder-1"
  - "stakeholder-2"
metrics:
  - name: "metric-name"
    value: "metric-value"
    target: "target-value"
```

---

## 🔄 **移行戦略**

### **Phase 1: 緊急整理（1週間）**
1. **ルートディレクトリクリーンアップ**
   - 基本ドキュメント以外を適切なディレクトリに移動
   - 重複ファイルの統合

2. **アーカイブ整理**
   - 明確に廃止されたファイルをarchives/deprecatedに移動
   - 完了プロジェクトをarchives/completedに整理

3. **危険ファイル除去**
   - 機密情報・個人情報を含むファイルの除去
   - 不要なバックアップファイルの削除

### **Phase 2: 構造再構築（2週間）**
1. **新ディレクトリ構造作成**
2. **既存ドキュメントの分類・移動**
3. **命名規則適用**
4. **メタデータ追加**

### **Phase 3: 品質向上（1週間）**
1. **リンク修正**
2. **内容レビュー**
3. **重複除去**
4. **検索インデックス構築**

---

## 🛠️ **実装ツール**

### **自動化スクリプト**
```bash
# ドキュメント分類自動化
scripts/docs/classify-documents.py

# メタデータ自動生成
scripts/docs/generate-metadata.py

# リンク検証
scripts/docs/validate-links.py

# 構造検証
scripts/docs/validate-structure.py
```

### **継続的メンテナンス**
```bash
# 日次チェック
scripts/docs/daily-doc-health-check.sh

# 週次レポート
scripts/docs/weekly-doc-report.sh

# 月次最適化
scripts/docs/monthly-doc-optimization.sh
```

---

## 📊 **成功指標**

### **定量指標**
- **検索時間**: 平均30秒以内でドキュメント発見
- **メンテナンス工数**: 70%削減
- **重複率**: 5%以下
- **リンク切れ率**: 1%以下
- **メタデータ完成度**: 95%以上

### **定性指標**
- **開発者満足度**: 4.5/5.0以上
- **新規メンバー学習速度**: 50%向上
- **ドキュメント品質**: Iron Will基準100%遵守

---

## 🚨 **違反対応**

### **自動検知システム**
- **構造違反**: CI/CDで自動検出
- **命名規則違反**: pre-commitフックで阻止
- **メタデータ不足**: GitHub Actionsで検出
- **リンク切れ**: 日次自動チェック

### **是正プロセス**
1. **自動警告**: 違反発生時の即座通知
2. **修正支援**: 自動修正提案
3. **エスカレーション**: 重大違反時の評議会報告
4. **強制修正**: 品質基準未満時の自動修正

---

## 🎯 **継続的改善**

### **定期見直し**
- **月次レビュー**: 分類効果の検証
- **四半期改善**: ユーザーフィードバック反映
- **年次更新**: 大幅構造見直し

### **フィードバック収集**
- **開発者アンケート**: 月次実施
- **利用統計分析**: 週次レポート
- **改善提案システム**: 継続的収集

---

**エルダーズギルドは、このドキュメント分類標準により、知識の統一管理と効率的な情報アクセスを実現します。**

**Iron Will**: No Workarounds! 🗡️  
**Elders Legacy**: Think it, Rule it, Own it! 🏛️

---

**最終更新**: 2025年7月22日  
**次回見直し予定**: 2025年10月22日  
**承認**: エルダー評議会（全員一致）