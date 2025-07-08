#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "🌏 AI Company 日本語化を開始します..."

# 1. 既存ワーカーの日本語化パッチ
echo "📝 ワーカーの日本語化..."
python3 scripts/apply_japanese_patch.py

# 2. Claude CLI日本語設定
echo "🤖 Claude CLI日本語設定..."  
python3 scripts/setup_claude_japanese.py

# 3. system.json更新（存在しない場合は作成）
echo "⚙️ システム設定更新..."
if [ ! -f config/system.json ]; then
    echo '{"language": "ja"}' > config/system.json
else
    # jqがない場合はPythonで処理
    python3 -c "
import json
with open('config/system.json', 'r') as f:
    config = json.load(f)
config['language'] = 'ja'
with open('config/system.json', 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
"
fi

# 4. テスト実行
echo "🧪 日本語化テスト..."
python3 -c "
from core import msg
print('✅ メッセージシステム: ' + msg('task_completed', task_id='test_001', duration=1.23, files=3))
"

echo ""
echo "🎉 日本語化が完了しました！"
echo "以下の機能が日本語対応になりました："
echo "  - ワーカーのログメッセージ"
echo "  - Slack通知"
echo "  - エラーメッセージ"  
echo "  - Claude CLIの応答（コメント、ログ等）"
echo ""
echo "設定を変更する場合は config/system.json の language を編集してください"
