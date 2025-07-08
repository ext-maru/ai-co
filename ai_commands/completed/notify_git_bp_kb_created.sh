#!/bin/bash
cd /home/aicompany/ai_co
echo "📚 AI Git コミットベストプラクティス - ナレッジベース作成通知"
echo "================================================"

# SlackにナレッジベースURL通知
source venv/bin/activate
python3 << 'EOF'
from libs.slack_notifier import SlackNotifier
import json

try:
    notifier = SlackNotifier()
    
    message = """📚 新しいナレッジベースが作成されました

*AI Git コミットベストプラクティス ナレッジベース v1.0*

📋 内容:
• Conventional Commits形式の自動生成システム
• CommitMessageGeneratorの詳細仕様
• ai-gitコマンドの使用方法
• 設定ファイルとカスタマイズ方法
• 実装例とトラブルシューティング

📍 場所: `knowledge_base/07_ai_git_best_practices_kb.md`

🎯 主な機能:
• 変更内容から自動的にコミットタイプを判定
• プロフェッショナルなメッセージ構造
• Breaking Change検出
• CHANGELOG自動生成

✨ 今後、全ての自動コミットがConventional Commits形式で生成されます！

例:
```
feat(workers): implement notification system

Add comprehensive notification worker with multi-channel
support and retry mechanism.

Refs: code_20250703_123456
```
"""
    
    notifier.send_message(message)
    print("✅ Slack通知を送信しました")
    
except Exception as e:
    print(f"Slack通知エラー: {e}")

# ナレッジベース一覧も更新
print("\n📚 現在のナレッジベース一覧:")
import os
kb_dir = "knowledge_base"
if os.path.exists(kb_dir):
    kb_files = sorted([f for f in os.listdir(kb_dir) if f.endswith('.md')])
    for kb in kb_files:
        print(f"  - {kb}")
EOF

echo ""
echo "================================================"
echo "✅ ナレッジベース作成完了"
echo ""
echo "📝 参照方法:"
echo "  cat knowledge_base/07_ai_git_best_practices_kb.md"
echo ""
echo "🚀 これで全ての実装とドキュメント化が完了しました！"
