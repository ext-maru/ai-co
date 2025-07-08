#!/bin/bash
#!/bin/bash
# スクリプトを実行可能にする
chmod +x /home/aicompany/ai_co/scripts/setup_ai_todo.sh
chmod +x /home/aicompany/ai_co/scripts/ai-todo

# シンボリックリンクを作成（存在しない場合）
if [ ! -L "/home/aicompany/ai_co/bin/ai-todo" ]; then
    ln -sf /home/aicompany/ai_co/scripts/ai-todo /home/aicompany/ai_co/bin/ai-todo
fi

echo "✅ 実行権限とリンクを設定しました"
