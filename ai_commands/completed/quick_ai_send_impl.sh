#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "📝 ai-send拡張を実装中..."

# implement_ai_send_extension.shを実行
if [ -f implement_ai_send_extension.sh ]; then
    chmod +x implement_ai_send_extension.sh
    ./implement_ai_send_extension.sh
    echo "✅ 実装完了"
else
    echo "❌ implement_ai_send_extension.sh が見つかりません"
fi
