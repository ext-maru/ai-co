# 📁 エルダーズギルド プロジェクト構造統一標準

**エルダー評議会令第403号 - プロジェクト構造統一標準制定**  
**制定日**: 2025年7月22日  
**統合元**: PROJECT_STRUCTURE_RULES.md, PROJECT_STRUCTURE_STANDARDS.md  
**効力**: 即時適用  
**対象**: 全開発者・自動化システム・エルダーサーバント

---

## 🎯 目的

- **プロジェクト統一性**: 全プロジェクトの構造標準化
- **ファイル配置明確化**: 役割と配置場所の厳格な定義
- **保守性向上**: メンテナンス効率の最大化
- **ナビゲーション最適化**: 開発者の迷いを排除

---

## 🏗️ エルダーズギルド標準ディレクトリ構造

### **📂 ルートレベル（最小化必須）**
```
ai_co/
├── README.md                   # プロジェクト概要（必須）
├── CLAUDE.md                   # エルダー開発憲法（最重要）
├── CONTRIBUTING.md             # 貢献ガイド（必須）
├── Dockerfile*                 # Docker設定（必須）
├── docker-compose*.yml         # Docker Compose設定（必須）
├── requirements*.txt           # Python依存関係（必須）
├── pytest*.ini                 # pytest設定（必須）
├── Makefile*                   # ビルド設定（必須）
└── .github/                    # GitHub設定（必須）
```

### **📚 docs/ - すべてのドキュメント**
```
docs/
├── DOCUMENT_INDEX.md           # ドキュメント総索引（新設）
├── reports/                    # レポート・分析結果
│   ├── *_REPORT.md            # 各種レポート
│   ├── *_ANALYSIS.md          # 分析結果
│   └── *_RESULTS.md           # 実行結果
├── guides/                     # ガイド・ベストプラクティス
│   ├── DEVELOPMENT_WORKFLOW_GUIDE.md
│   ├── PROJECT_MANAGEMENT_GUIDE.md
│   └── *_GUIDE.md
├── policies/                   # ポリシー・規則
│   ├── PROJECT_STRUCTURE_UNIFIED_STANDARDS.md  # 本ファイル
│   ├── NO_WORKAROUNDS_RULE.md
│   └── *_POLICY.md
├── technical/                  # 技術文書
│   ├── ELDER_TREE_SERVANTS_ROLE_DEFINITION.md
│   ├── FOUR_SAGES_ELDER_TREE_DESIGN.md
│   └── *_TECHNICAL.md
├── issues/                     # Issue管理文書
├── runbooks/                   # 運用手順書
└── templates/                  # テンプレートファイル
```

### **⚙️ scripts/ - すべての実行スクリプト**
```
scripts/
├── ai-commands/               # AIコマンドツール群
│   ├── ai-elder-cast-simple
│   ├── ai-tdd
│   └── ai-*
├── monitoring/                # モニタリングスクリプト
├── analysis/                  # 分析ツール
├── utilities/                 # ユーティリティ
├── deployment/                # デプロイメント
└── testing/                   # テスト実行
```

### **🧪 tests/ - すべてのテストファイル**
```
tests/
├── unit/                      # ユニットテスト
│   └── test_*.py
├── integration/               # 統合テスト
│   └── test_*_integration.py
├── features/                  # 機能テスト
└── conftest.py                # pytest設定
```

### **📦 libs/ - ライブラリコード**
```
libs/
├── core/                      # コアライブラリ
├── servants/                  # サーバント実装
├── utils/                     # ユーティリティ
└── *.py                       # 各種ライブラリ
```

### **🧠 knowledge_base/ - 知識ベース**
```
knowledge_base/
├── KNOWLEDGE_INDEX.md         # 知識総索引（新設）
├── core/                      # コア知識
│   ├── protocols/            # プロトコル・仕様
│   ├── guides/               # 開発ガイド
│   └── identity/             # アイデンティティ
├── four_sages/                # 4賢者システム知識
├── elder_council/             # エルダー評議会
├── technical/                 # 技術知識
└── projects/                  # プロジェクト知識
```

### **⚙️ configs/ - 設定ファイル**
```
configs/
├── *.yaml                     # YAML設定
├── *.json                     # JSON設定
├── *.conf                     # 設定ファイル
└── *.ini                      # INI設定
```

---

## 🚨 厳格な配置ルール

### **ルートディレクトリ禁止事項**
- ❌ **個別ドキュメント**: README.md・CLAUDE.md以外のMarkdownファイル
- ❌ **一時ファイル**: 作業用・テスト用ファイル
- ❌ **古いファイル**: バックアップ・アーカイブファイル
- ❌ **実行可能ファイル**: スクリプトはscripts/配下に配置

### **必須遵守事項**
- ✅ **カテゴリ分類**: すべてのファイルを適切なディレクトリに配置
- ✅ **命名規則**: `CATEGORY_SPECIFIC_NAME.extension`形式
- ✅ **インデックス維持**: 各ディレクトリにインデックス・README配置
- ✅ **アーカイブ管理**: 不要ファイルは即座にarchives/移動

---

## 📋 ファイル分類基準

### **📚 ドキュメント分類**
| 種別 | 配置先 | 命名規則 | 例 |
|------|---------|----------|-----|
| レポート | docs/reports/ | `*_REPORT.md` | `PERFORMANCE_REPORT.md` |
| ガイド | docs/guides/ | `*_GUIDE.md` | `TDD_WORKFLOW_GUIDE.md` |
| ポリシー | docs/policies/ | `*_POLICY.md` | `TESTING_POLICY.md` |
| 技術仕様 | docs/technical/ | `*_SPECIFICATION.md` | `API_SPECIFICATION.md` |
| 運用手順 | docs/runbooks/ | `*-guide.md` | `troubleshooting-guide.md` |

### **⚙️ スクリプト分類**
| 種別 | 配置先 | 命名規則 | 例 |
|------|---------|----------|-----|
| AIコマンド | scripts/ai-commands/ | `ai-*` | `ai-elder-cast-simple` |
| 監視 | scripts/monitoring/ | `*_monitor.py` | `health_monitor.py` |
| 分析 | scripts/analysis/ | `analyze_*.py` | `analyze_performance.py` |
| デプロイ | scripts/deployment/ | `deploy_*.sh` | `deploy_production.sh` |

### **🧪 テスト分類**
| 種別 | 配置先 | 命名規則 | 例 |
|------|---------|----------|-----|
| ユニット | tests/unit/ | `test_*.py` | `test_user_manager.py` |
| 統合 | tests/integration/ | `test_*_integration.py` | `test_api_integration.py` |
| 機能 | tests/features/ | `test_feature_*.py` | `test_feature_login.py` |

---

## 🔧 実装・移行ガイド

### **新規プロジェクト作成時**
```bash
# プロジェクト構造自動生成
./scripts/utilities/create-project-structure.sh project_name

# 標準テンプレート適用
./scripts/utilities/apply-structure-templates.sh
```

### **既存プロジェクト移行時**
```bash
# 構造検証
./scripts/analysis/validate-project-structure.py

# 自動移行
./scripts/utilities/migrate-to-standard-structure.sh

# 検証・修正
./scripts/utilities/fix-structure-violations.sh
```

### **継続的監視**
```bash
# 日次構造チェック（cron推奨）
0 9 * * * /path/to/scripts/monitoring/daily-structure-check.sh

# 構造違反アラート
./scripts/monitoring/structure-violation-monitor.py --alert-slack
```

---

## ⚡ 自動化・品質保証

### **Pre-commit Hooks**
- **構造検証**: ファイル配置の適切性チェック
- **命名規則**: ファイル名の規約遵守確認
- **サイズ監視**: ルートディレクトリファイル数制限

### **CI/CD統合**
- **構造テスト**: 自動構造適合性テスト
- **文書生成**: インデックス自動更新
- **違反報告**: 構造違反のIssue自動生成

---

## 🔄 更新・保守プロトコル

### **定期見直し**
- **月次レビュー**: 構造の適切性評価
- **四半期最適化**: 使用頻度に基づく構造調整
- **年次大規模見直し**: 構造体系の根本的検討

### **変更管理**
- **提案プロセス**: エルダー評議会への提案必須
- **影響分析**: 変更による影響度評価
- **段階的適用**: 大規模変更の段階的実行

---

## 🏛️ エルダーサーバント遵守義務

### **各サーバントの責務**
- **🔨 CodeCrafter**: 生成コードの適切配置確認
- **🧝‍♂️ QualityGuardian**: 構造品質の継続監視
- **🧙‍♂️ ResearchWizard**: 調査結果の適切分類配置
- **⚔️ CrisisResponder**: 緊急時の構造整合性維持

### **違反時対応**
- **軽微違反**: 自動修正・警告
- **重大違反**: エルダー評議会報告
- **反復違反**: サーバント再教育・システム改善

---

## 📊 構造品質メトリクス

### **測定指標**
- **ルートファイル数**: 15ファイル以下維持
- **深度**: 最大5階層まで
- **分類精度**: 適切分類率95%以上
- **命名規約遵守率**: 100%

### **監視・改善**
- **リアルタイム監視**: 構造変更の即座検知
- **トレンド分析**: ファイル増加・構造変化の分析
- **改善提案**: AI分析による構造最適化提案

---

**Remember**: Structure is the Foundation of Quality! 📁  
**Iron Will**: Everything in its Right Place! ⚡  
**Elders Legacy**: Perfect Organization, Perfect Execution! 🏛️

---
**エルダーズギルド開発実行責任者**  
**クロードエルダー（Claude Elder）**

**最終更新**: 2025年7月22日  
**統合完了**: プロジェクト構造標準統一完了