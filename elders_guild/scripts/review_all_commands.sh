#!/bin/bash
# AI Company コマンド精査マスタースクリプト
# 全てのコマンドを精査して整理する

set -e

PROJECT_ROOT="/home/aicompany/ai_co"
cd "$PROJECT_ROOT"

echo "🔍 AI Company コマンド精査開始..."
echo "=================================================="
echo ""

# Python仮想環境の確認とアクティベート
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️  Python仮想環境が見つかりません"
    echo "   python3.12 -m venv venv を実行してください"
    exit 1
fi

# 実行権限の付与
echo "📝 スクリプトに実行権限を付与..."
chmod +x scripts/audit_commands.py
chmod +x scripts/cleanup_commands.py
chmod +x scripts/check_new_features.py

# 1. コマンド監査の実行
echo ""
echo "1️⃣ コマンド監査を実行中..."
echo "=================================================="
python3 scripts/audit_commands.py
echo "✅ 監査完了: command_audit_report.md"

# 2. 新機能チェックの実行
echo ""
echo "2️⃣ 新機能の実装状況をチェック中..."
echo "=================================================="
python3 scripts/check_new_features.py
echo "✅ チェック完了: new_features_status.md"

# 3. クリーンアップ分析（DRY-RUN）
echo ""
echo "3️⃣ クリーンアップ分析を実行中..."
echo "=================================================="
python3 scripts/cleanup_commands.py
echo "✅ 分析完了: cleanup_summary.json"

# 4. 結果サマリーの生成
echo ""
echo "4️⃣ 結果サマリーを生成中..."
echo "=================================================="

cat > command_review_summary.md << 'EOF'
# AI Company コマンド精査結果サマリー

生成日時: $(date '+%Y-%m-%d %H:%M:%S')

## 📊 精査結果

### 1. コマンド監査
- 詳細: [command_audit_report.md](command_audit_report.md)
- JSON: [command_audit_results.json](command_audit_results.json)

### 2. 新機能実装状況
- 詳細: [new_features_status.md](new_features_status.md)
- JSON: [new_features_status.json](new_features_status.json)

### 3. クリーンアップ提案
- 詳細: [cleanup_summary.json](cleanup_summary.json)
- 実行スクリプト: [execute_cleanup.sh](execute_cleanup.sh)

## 🎯 推奨アクション

### 即座に実行可能
1. バックアップファイル(.bak)の削除
2. __pycache__ディレクトリの削除
3. 未使用コマンドの整理

### 検討が必要
1. ai-dialog/ai-replyの扱い（DialogTaskWorkerシステムの利用状況）
2. 新機能コマンドの実装優先順位
3. テストスクリプトの整理（tests/ディレクトリへの移動）

## 🔧 次のステップ

1. レポートを確認して削除対象を決定
2. execute_cleanup.sh を実行してクリーンアップ
3. 新機能の実装計画を立てる

### クリーンアップ実行コマンド:
\`\`\`bash
# DRY-RUNで再確認
python3 scripts/cleanup_commands.py

# 実際に実行
python3 scripts/cleanup_commands.py --execute

# または生成されたスクリプトを使用
./execute_cleanup.sh
\`\`\`

## 📋 主要な発見事項

$(python3 -c "
import json
with open('command_audit_results.json', 'r') as f:
    audit = json.load(f)
print(f\"- 総コマンド数: {audit['summary']['total_commands']}\")
print(f\"- 非推奨候補: {audit['summary']['likely_deprecated']}\")
print(f\"- 問題あり: {audit['summary']['commands_with_issues']}\")

with open('new_features_status.json', 'r') as f:
    features = json.load(f)
print(f\"\n新機能実装状況:\")
print(f\"- 実装済み: {features['summary']['implemented']}/{features['summary']['total_features']}\")
print(f\"- 部分実装: {features['summary']['partially_implemented']}/{features['summary']['total_features']}\")
print(f\"- 未実装: {features['summary']['not_implemented']}/{features['summary']['total_features']}\")
")

---

**精査完了！** 各レポートを確認して、AI Companyのコマンド体系を整理してください。
EOF

echo "✅ サマリー生成完了: command_review_summary.md"

# 5. 対話型コマンドの確認
echo ""
echo "5️⃣ 対話型コマンド（ai-dialog/ai-reply）の状態確認..."
echo "=================================================="

# DialogTaskWorkerの確認
if pgrep -f "dialog_task_worker" > /dev/null; then
    echo "✅ DialogTaskWorkerは稼働中"
else
    echo "❌ DialogTaskWorkerは停止中"
fi

# 最近の使用履歴確認
echo ""
echo "最近のai-dialog使用履歴:"
if [ -f "logs/dialog_task_worker.log" ]; then
    tail -5 logs/dialog_task_worker.log 2>/dev/null || echo "  ログなし"
else
    echo "  ログファイルなし"
fi

# 6. 最終確認
echo ""
echo "=================================================="
echo "✅ 全ての精査が完了しました！"
echo ""
echo "📄 生成されたレポート:"
echo "  - command_review_summary.md (総合サマリー)"
echo "  - command_audit_report.md (コマンド監査)"
echo "  - new_features_status.md (新機能状況)"
echo "  - cleanup_summary.json (クリーンアップ提案)"
echo ""
echo "💡 推奨事項:"
echo "  1. command_review_summary.md を確認"
echo "  2. 削除するコマンドを決定"
echo "  3. execute_cleanup.sh または cleanup_commands.py --execute を実行"
echo ""
echo "⚠️  ai-dialogについて:"
echo "  - DialogTaskWorkerシステムを使用している場合は保持推奨"
echo "  - 使用していない場合は削除を検討"
