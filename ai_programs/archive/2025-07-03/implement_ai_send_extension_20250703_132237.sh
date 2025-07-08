#!/bin/bash
cd /home/aicompany/ai_co

echo "📝 implement_ai_send_extension.sh を実行中..."

# 実装スクリプトの実行
chmod +x implement_ai_send_extension.sh
./implement_ai_send_extension.sh

# 結果確認
if [ -f config/task_types.json ]; then
    echo "✅ タスクタイプ設定ファイル作成成功"
else
    echo "❌ タスクタイプ設定ファイル作成失敗"
fi
