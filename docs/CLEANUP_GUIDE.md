# 🧹 Elders Guild クリーンアップガイド v1.0

## 📋 概要

Elders Guildプロジェクトの定期的なクリーンアップ手順と、不要ファイルの判断基準をまとめたガイドです。プロジェクトの見通しを良くし、開発効率を向上させるための重要なメンテナンス作業です。

### **クリーンアップの目的**
- ✅ **可視性向上**: 重要なファイルが見つけやすくなる
- ✅ **効率化**: 不要なファイルによる混乱を防ぐ
- ✅ **容量節約**: ディスク使用量を最適化
- ✅ **保守性**: プロジェクト構造を整理整頓

## 🗂️ ディレクトリ別整理ガイド

### 1. **workers/ ディレクトリ**

#### 削除対象
```
- test_worker.py, test_worker_refactored.py（古いテスト用）
- example_*.py（サンプルコード）
- simple_dialog_worker.py, dialog_only_worker.py（機能重複）
- se_worker.py, se_worker_v2.py（se_tester_workerに統合）
- improved_pm_worker.py（pm_worker_enhancedがあるため）
- *.backup.*（バックアップファイル）
```

#### 残すべきワーカー
```
【コアシステム】
- task_worker.py, pm_worker.py, result_worker.py
- dialog_task_worker.py, command_executor_worker.py

【拡張機能】
- pm_worker_enhanced.py, pm_worker_gitflow.py
- quality_pm_worker.py, quality_task_worker.py
- se_tester_worker.py, test_generator_worker.py

【特殊機能】
- slack_monitor_worker.py, email_notification_worker.py
- image_pipeline_worker.py
```

### 2. **scripts/ ディレクトリ**

#### 削除対象カテゴリ
```
【診断・修正系】
- diagnose_*.sh, diagnose_*.py
- fix_*.sh, fix_*.py
- check_*_issue.sh

【古いテスト関連】
- test-system-check.sh
- test_pm_*.py
- setup-and-test.sh
- ai-test-fixed（ai-testがあるため）

【完了済みセットアップ】
- setup_github.sh
- migrate_to_gitflow.sh
- update_*_with_*.sh
- evolution_code_*.sh（自動生成）

【Slack設定（完了済み）】
- slack_setup_*.py
- debug_slack.py
- detect_slack_config.py

【一時的なスクリプト】
- quick_*.sh
- send_test_*.py
- conversation_health_check.py
```

#### 残すべきスクリプト
```
【ai-* コマンド】
全てのai-*コマンドは重要（約25個）

【重要なセットアップ】
- start-command-executor.sh
- start-quality-system-v2.sh
- setup_commands.sh
- setup_test_framework.py

【有用なツール】
- generate_test.py
- analyze_logs.py
- auto_summarize.py
- test_diagnostic.py
- pm_cli.py
- recovery_daemon.py
```

### 3. **ルートディレクトリ**

#### 削除対象パターン
```
test_*.sh, test_*.py（テスト実行スクリプト）
FIX_*.sh, fix_*.sh（修正スクリプト）
setup_*.sh, SETUP_*.sh（セットアップ済み）
install_*.sh（インストール済み）
check_*.py, verify_*.py（確認スクリプト）
run_*.py, execute_*.py（実行スクリプト）
*_report.md, *_status.json（古いレポート）
ai_launcher_*.py（テスト用ランチャー）
```

### 4. **libs/ ディレクトリ**

#### 削除対象
```
- evolution_code_*.py（自動生成ファイル）
- task_history_db.py（_refactoredがあるため）
- 明らかに使われていない実験的なマネージャー
```

## 🛠️ クリーンアップ手順

### 1. **自動クリーンアップスクリプトの使用**

```bash
# 総合クリーンアップスクリプトを作成
cat > cleanup_all.sh << 'EOF'
#!/bin/bash
cd /home/aicompany/ai_co

# アーカイブディレクトリ作成
mkdir -p {workers,scripts,libs,config}/_archived
mkdir -p _archived/{test_scripts,setup_scripts,fix_scripts,reports,temp_files}

# 各ディレクトリのクリーンアップ実行
# ... (詳細は実装参照)
EOF

chmod +x cleanup_all.sh
./cleanup_all.sh
```

### 2. **AI Command Executorでの自動実行**

```python
from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()
helper.create_bash_command("""
cd /home/aicompany/ai_co
./cleanup_all.sh
""", "cleanup_project")
```

## 📊 判断基準

### **削除すべきファイル**

1. **一時的な修正・診断ファイル**
   - 問題解決後は不要
   - fix_*, diagnose_* パターン

2. **古いバージョン・バックアップ**
   - _v2があればv1は不要
   - .backup.* ファイル

3. **完了済みセットアップ**
   - 一度実行すれば不要
   - migrate_*, setup_* パターン

4. **重複機能**
   - 同じ機能の複数実装
   - 新しい統合版を優先

5. **自動生成ファイル**
   - evolution_code_*
   - 再生成可能なもの

### **残すべきファイル**

1. **コアシステム**
   - メインのワーカー群
   - Core基盤モジュール

2. **現役のコマンド**
   - ai-* コマンド全般
   - 日常的に使用するツール

3. **ドキュメント**
   - README.md
   - ナレッジベース
   - 重要な設計文書

4. **設定ファイル**
   - *.conf, *.json
   - .gitignore等

## 🗄️ アーカイブ方針

### **アーカイブ構造**
```
_archived/
├── test_scripts/      # テスト関連
├── setup_scripts/     # セットアップ関連
├── fix_scripts/       # 修正スクリプト
├── reports/           # 古いレポート
└── temp_files/        # その他一時ファイル

各ディレクトリ/_archived/  # ディレクトリ別アーカイブ
```

### **復元方法**
```bash
# 特定ファイルの復元
mv _archived/test_scripts/test_system.sh ./

# 全体の復元（緊急時）
find _archived -type f -exec mv {} . \;
```

## 📈 クリーンアップ効果

### **2025年1月実施結果**
- Workers: 30個 → 17個（-43%）
- Scripts: 100個以上 → 約50個（-50%）
- ルート: 150個以上 → 約30個（-80%）
- 合計: 約150個のファイルをアーカイブ

### **ディスク使用量**
- クリーンアップ前: 推定200MB+
- クリーンアップ後: 推定150MB
- 削減率: 約25%

## 🔄 定期メンテナンス

### **推奨頻度**
- **週次**: __pycache__の削除
- **月次**: 総合クリーンアップ
- **四半期**: アーカイブの見直し

### **自動化**
```bash
# crontab設定例
0 3 * * 0 /home/aicompany/ai_co/weekly_cleanup.sh
0 3 1 * * /home/aicompany/ai_co/monthly_cleanup.sh
```

## ⚠️ 注意事項

1. **削除前の確認**
   - 重要なファイルでないか確認
   - 他で参照されていないか確認

2. **アーカイブ優先**
   - 完全削除より_archivedへ移動
   - 復元可能な状態を維持

3. **実行中の影響**
   - ワーカー停止中に実行推奨
   - Git操作前に実行

## 🎯 ベストプラクティス

1. **命名規則の統一**
   - 一時ファイルは明確な prefix を付ける
   - test_, temp_, fix_ など

2. **ディレクトリ構造の維持**
   - 適切なディレクトリに配置
   - ルートディレクトリを汚さない

3. **ドキュメント化**
   - 重要なスクリプトには説明を記載
   - 削除可能かどうかを明記

4. **定期的な見直し**
   - 不要になったら即アーカイブ
   - アーカイブも定期的に確認

---

**🧹 このガイドに従って、Elders Guildプロジェクトを常にクリーンに保ちましょう**