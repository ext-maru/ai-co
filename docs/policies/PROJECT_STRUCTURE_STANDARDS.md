# プロジェクト構造標準規則

## 📋 標準規則概要

**制定日**: 2025年1月20日  
**承認**: エルダーズ評議会  
**効力**: 即時適用  
**対象**: 全開発者・自動化システム

## 🏗️ ディレクトリ構造標準

### 必須ディレクトリ構造
```
ai_co/
├── README.md, CLAUDE.md         # ルート必須ファイルのみ
├── docs/                        # すべてのドキュメント
│   ├── reports/                # レポート・分析結果
│   ├── guides/                 # ガイド・ベストプラクティス
│   ├── policies/               # ポリシー・プロトコル
│   ├── technical/              # 技術文書
│   ├── issues/                 # Issue管理文書
│   └── completed/              # 完了プロジェクト文書
├── scripts/                    # すべての実行スクリプト
│   ├── ai-commands/           # AIコマンドツール
│   ├── monitoring/            # モニタリングスクリプト
│   ├── analysis/              # 分析ツール
│   ├── utilities/             # ユーティリティ
│   ├── deployment/            # デプロイメント
│   └── testing/               # テスト実行
├── tests/                      # すべてのテストファイル
│   ├── unit/                  # ユニットテスト
│   ├── integration/           # 統合テスト
│   └── e2e/                   # E2Eテスト
├── libs/                       # ライブラリコード
├── configs/                    # 設定ファイル
├── data/                       # データファイル
├── knowledge_base/             # ナレッジベース
└── generated_reports/          # 自動生成レポート
```

## 📝 ファイル配置規則

### 1. ドキュメント配置
```bash
# レポート・分析結果
docs/reports/
├── performance_analysis_*.md
├── coverage_reports_*.md
├── security_audit_*.md
└── project_status_*.md

# ガイド・手順書
docs/guides/
├── development_guide.md
├── deployment_guide.md
├── troubleshooting_guide.md
└── api_usage_guide.md

# ポリシー・規則
docs/policies/
├── coding_standards.md
├── security_policy.md
├── review_policy.md
└── project_structure_standards.md

# 技術文書
docs/technical/
├── architecture_design.md
├── api_specifications.md
├── database_schema.md
└── integration_patterns.md
```

### 2. スクリプト配置
```bash
scripts/
├── ai-commands/           # AI関連コマンドツール
│   ├── ai-status
│   ├── ai-logs
│   └── ai-elder-council
├── monitoring/            # 監視スクリプト
│   ├── health_check.py
│   ├── performance_monitor.py
│   └── log_analyzer.py
├── analysis/              # 分析ツール
│   ├── code_analyzer.py
│   ├── dependency_check.py
│   └── security_scan.py
├── utilities/             # ユーティリティ
│   ├── backup_manager.py
│   ├── cleanup_tools.py
│   └── migration_helper.py
├── deployment/            # デプロイメント
│   ├── deploy.py
│   ├── rollback.py
│   └── env_setup.py
└── testing/               # テスト実行
    ├── run_tests.py
    ├── coverage_check.py
    └── integration_tests.py
```

### 3. テスト配置
```bash
tests/
├── unit/                  # ユニットテスト
│   ├── test_libs/        # libsモジュールのテスト
│   ├── test_scripts/     # scriptsのテスト
│   └── test_utils/       # ユーティリティのテスト
├── integration/           # 統合テスト
│   ├── test_api_endpoints.py
│   ├── test_database_integration.py
│   └── test_external_services.py
├── e2e/                   # E2Eテスト
│   ├── test_full_workflow.py
│   ├── test_user_scenarios.py
│   └── test_system_integration.py
└── fixtures/              # テストデータ・フィクスチャ
    ├── sample_data/
    ├── mock_configs/
    └── test_databases/
```

## 🚫 禁止事項

### 1. ルートディレクトリ散在の禁止
```bash
# ❌ 禁止
ai_co/
├── script1.py              # → scripts/ へ移動
├── analysis_report.md      # → docs/reports/ へ移動
├── test_feature.py         # → tests/ へ移動
├── config.yaml            # → configs/ へ移動
└── random_file.txt        # → 適切な場所へ移動

# ✅ 許可（ルート必須ファイルのみ）
ai_co/
├── README.md
├── CLAUDE.md
├── .gitignore
├── requirements.txt
├── setup.py
├── Dockerfile
├── docker-compose.yml
├── .pre-commit-config.yaml
└── pytest.ini
```

### 2. 重複ディレクトリの禁止
```bash
# ❌ 禁止
bin/ AND scripts/           # scripts/ のみ使用
reports/ AND docs/reports/  # docs/reports/ のみ使用
documentation/ AND docs/    # docs/ のみ使用
test_* AND tests/          # tests/ のみ使用
```

### 3. GUI関連ファイルの禁止
```bash
# ❌ 禁止（削除済み）
web/                       # CLI機能で代替
dashboard/                 # CLI monitoring で代替
ui/                        # プロジェクト固有UI以外禁止
frontend/                  # 個別プロジェクト以外禁止
```

## 📏 命名規則

### 1. ディレクトリ命名
- **小文字のみ使用**: `scripts/`, `docs/`, `tests/`
- **アンダースコア区切り**: `generated_reports/`, `knowledge_base/`
- **複数形推奨**: `scripts/`, `tests/`, `configs/`

### 2. ファイル命名
```bash
# レポートファイル
{type}_{subject}_{date}.md
例: performance_analysis_20250120.md
例: security_audit_report_20250120.md

# スクリプトファイル
{purpose}_{function}.py
例: deploy_production.py
例: monitor_system_health.py

# 設定ファイル
{environment}.{format}
例: production.yaml
例: development.json
例: test.env
```

### 3. テストファイル命名
```bash
# ユニットテスト
test_{module_name}.py
例: test_smart_code_generator.py
例: test_elder_flow_engine.py

# 統合テスト
test_{integration_type}.py
例: test_api_integration.py
例: test_database_integration.py

# E2Eテスト
test_{workflow_name}.py
例: test_complete_deployment.py
例: test_user_registration_flow.py
```

## 🔍 監視・検証システム

### 1. 自動構造チェック
```bash
# pre-commit hook での構造チェック
scripts/utilities/structure_validator.py

# 定期チェック（日次）
scripts/monitoring/structure_monitor.py

# 違反検知・自動修正
scripts/utilities/auto_structure_fix.py
```

### 2. 違反時の対応フロー
```bash
# 1. 自動検知
インシデント賢者が構造違反を検知

# 2. 自動警告
開発者への即座通知

# 3. 自動修正提案
適切な配置先の提案

# 4. エルダー評議会報告
重大違反時の評議会招集
```

## 📊 定期レビュー

### 月次構造レビュー
- **実施日**: 毎月第一月曜日
- **担当**: ナレッジ賢者 + タスク賢者
- **対象**: 新規ファイル・ディレクトリの配置確認
- **アクション**: 必要に応じて構造改善提案

### 四半期最適化
- **実施日**: 四半期末
- **担当**: エルダーズ評議会
- **対象**: 構造規則の見直し・更新
- **アクション**: 新しい標準の策定・承認

## 🚀 継続改善

### 1. 自動化推進
- **構造検証の自動化**: CI/CDパイプラインでの構造チェック
- **ドキュメント生成**: 構造変更時の自動ドキュメント更新
- **移行支援**: 古い構造から新構造への自動移行ツール

### 2. 開発者支援
- **IDE統合**: エディタプラグインでの構造ガイド
- **テンプレート**: 新規ファイル作成時のテンプレート提供
- **ヘルプコマンド**: `ai-structure-help` での即座ガイダンス

### 3. 品質向上
- **メトリクス収集**: 構造遵守率の測定
- **効果測定**: 開発効率への影響分析
- **フィードバック**: 開発者からの改善提案収集

## ✅ 遵守確認チェックリスト

### 開発者向けチェックリスト
- [ ] 新規ファイルを適切なディレクトリに配置したか
- [ ] ルートディレクトリに不要なファイルを作成していないか
- [ ] 命名規則に従ってファイル名を付けたか
- [ ] 重複ディレクトリを作成していないか
- [ ] GUI関連ファイルを作成していないか（個別プロジェクト除く）

### 自動システム向けチェックリスト
- [ ] 構造違反検知システムが稼働しているか
- [ ] 自動修正提案システムが機能しているか
- [ ] 定期レビューが実施されているか
- [ ] メトリクス収集が正常に行われているか
- [ ] ドキュメント更新が自動化されているか

## 📞 サポート・連絡先

### 構造に関する質問・提案
- **軽微な質問**: `ai-structure-help` コマンド
- **改善提案**: タスク賢者への提案
- **緊急事態**: インシデント賢者が自動対応
- **重要変更**: エルダーズ評議会での審議

---

**制定**: エルダーズ評議会  
**施行**: 2025年1月20日  
**改定**: 必要に応じて四半期レビュー  
**担当**: クロードエルダー（構造管理責任者）