# プロジェクト構造移行ガイド

## 📋 移行概要

このガイドは2025年1月20日に実施されたプロジェクト構造最適化の詳細手順と、今後の開発者向けガイドラインを提供します。

## 🔄 移行された配置ルール

### ディレクトリ移行マップ

| 旧配置 | 新配置 | 理由 |
|--------|--------|------|
| `bin/` | `scripts/` | 実行可能ファイルの統合 |
| `reports/` | `docs/reports/` | ドキュメント類の集約 |
| `test_*` | `tests/` | テストファイルの統一配置 |
| `auto_*` | `docs/` | 自動生成ファイルの整理 |
| `web/` | **削除** | GUI機能不要のため |

### ファイル種別配置ルール

#### 📄 ドキュメント類
```bash
# Before (分散配置)
root/report1.md
reports/report2.md
analysis/report3.md

# After (統合配置)
docs/reports/report1.md
docs/reports/report2.md
docs/reports/report3.md
```

#### 🔧 実行スクリプト
```bash
# Before
bin/script1.py
scripts/script2.py
root/script3.py

# After
scripts/script1.py
scripts/script2.py
scripts/script3.py
```

#### 🧪 テストファイル
```bash
# Before
test_feature1.py
tests/test_feature2.py
libs/test_feature3.py

# After
tests/test_feature1.py
tests/test_feature2.py
tests/test_feature3.py
```

## 🌐 Web機能除去対応

### 削除されたファイルと代替手段

#### 1. Web Dashboard → CLI Dashboard
```bash
# Before
python3 web/project_dashboard.py
open http://localhost:8080

# After
ai-status                    # システム状態確認
ai-logs                      # ログ確認
ai-project dashboard         # CLIベースダッシュボード
```

#### 2. Worker Dashboard → CLI Monitoring
```bash
# Before
python3 web/worker_dashboard.py --coverage-focus

# After
ai-status --coverage-focus   # CLI監視
ai-test-coverage             # カバレッジ確認
```

#### 3. Elder Flow Dashboard → Report Generation
```bash
# Before
web/dashboard/elder_flow_dashboard.html

# After
docs/reports/elder_flow_dashboard.html  # 静的レポート
elder-flow status                       # CLI確認
```

## 👨‍💻 開発者向けガイドライン

### 新規ファイル作成時のルール

#### ✅ 正しい配置
```bash
# ドキュメント作成
docs/guides/new_feature_guide.md
docs/reports/analysis_report.md
docs/technical/architecture_design.md

# スクリプト作成
scripts/automation/deploy_script.py
scripts/monitoring/health_check.py

# テスト作成
tests/unit/test_new_feature.py
tests/integration/test_api_endpoints.py

# 設定ファイル
configs/production.yaml
configs/development.json
```

#### ❌ 避けるべき配置
```bash
# ルート直下への散在
root/new_script.py           # → scripts/ へ
root/analysis.md             # → docs/reports/ へ
root/test_something.py       # → tests/ へ

# 重複ディレクトリ作成
reports/                     # docs/reports/ を使用
bin/                         # scripts/ を使用
documentation/               # docs/ を使用
```

### コマンド置き換えガイド

#### Web Dashboard関連
```bash
# 旧コマンド → 新コマンド
python3 web/project_dashboard.py     → ai-status
python3 web/worker_dashboard.py      → ai-status --workers
python3 web/nwo_unified_dashboard.py → ai-nwo-vision
```

#### 監視・ログ関連
```bash
# Web UI → CLI
http://localhost:8080/status          → ai-status
http://localhost:8080/logs            → ai-logs
http://localhost:8080/coverage        → ai-test-coverage
```

## 🔍 移行チェックリスト

### 開発者セットアップ時の確認事項

#### 1. 環境確認
```bash
# プロジェクト構造の確認
ls -la /home/aicompany/ai_co/
# 期待結果: web/ ディレクトリが存在しないこと

# CLI コマンドの確認
ai-status
ai-logs
elder-flow status
```

#### 2. ドキュメント参照の更新
```bash
# 古い参照を含むファイル検索
grep -r "web/" docs/ --exclude-dir=.git
grep -r "bin/" docs/ --exclude-dir=.git

# 結果: 更新済みファイルのみ表示されること
```

#### 3. スクリプト実行確認
```bash
# scripts/ ディレクトリの実行可能性確認
find scripts/ -name "*.py" -exec python3 -m py_compile {} \;

# 結果: コンパイルエラーがないこと
```

## 🚨 トラブルシューティング

### よくある問題と解決法

#### 1. 古いパス参照エラー
```bash
# エラー例
FileNotFoundError: [Errno 2] No such file or directory: 'web/dashboard.py'

# 解決法
# 1. ドキュメントで新しいパスを確認
cat docs/reports/PROJECT_STRUCTURE_OPTIMIZATION_REPORT_20250120.md

# 2. 代替コマンドを使用
ai-status  # web dashboardの代替
```

#### 2. 実行権限エラー
```bash
# エラー例
PermissionError: [Errno 13] Permission denied: 'scripts/setup.py'

# 解決法
chmod +x scripts/setup.py
```

#### 3. インポートエラー
```bash
# エラー例
ModuleNotFoundError: No module named 'web.dashboard'

# 解決法
# libs/ や scripts/ から適切なモジュールをインポート
from libs.advanced_monitoring_dashboard import MonitoringDashboard
```

## 📚 関連ドキュメント

### 参照すべきドキュメント
1. **[PROJECT_STRUCTURE_OPTIMIZATION_REPORT_20250120.md](../reports/PROJECT_STRUCTURE_OPTIMIZATION_REPORT_20250120.md)** - 詳細な変更レポート
2. **[CLAUDE.md](../../CLAUDE.md)** - 更新されたプロジェクト仕様
3. **[system_architecture.md](../../knowledge_base/system_architecture.md)** - 新しいアーキテクチャ図

### CLI コマンドリファレンス
```bash
# システム関連
ai-status                    # システム状態確認
ai-logs                      # ログ確認
ai-start / ai-stop          # サービス開始/停止

# プロジェクト管理
ai-project dashboard         # プロジェクト状況
ai-test-coverage            # テストカバレッジ

# Elder System
elder-flow status           # Elder Flow状態
ai-elder-council status     # エルダー評議会状況
```

## ✅ 移行完了チェック

### 確認項目
- [ ] web/ ディレクトリが存在しないことを確認
- [ ] CLI コマンドが正常動作することを確認
- [ ] ドキュメント内のパス参照が更新されていることを確認
- [ ] 新しいファイル配置ルールを理解したことを確認
- [ ] 代替コマンドの使用方法を習得したことを確認

### 移行支援
質問や問題が発生した場合:
1. **インシデント賢者**: 自動問題検知・対応
2. **ナレッジ賢者**: ドキュメント検索・参照
3. **エルダー評議会**: 重要な構造変更の承認・サポート

---

**作成日**: 2025年1月20日  
**更新予定**: 継続最適化実施時  
**担当**: クロードエルダー