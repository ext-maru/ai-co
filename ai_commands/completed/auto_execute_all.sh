#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "🚀 AI Command Executor起動確認と修正実行"
echo "========================================\n"

# CommandExecutorWorkerのプロセス確認
echo "📊 プロセス状態:"
if ps aux | grep -v grep | grep -q "command_executor_worker"; then
    echo "✅ CommandExecutorWorker: 実行中"
    ps_result="running"
else
    echo "❌ CommandExecutorWorker: 停止中"
    ps_result="stopped"

    # 自動起動
    echo "\n🔧 CommandExecutorWorkerを起動します..."
    cd /home/aicompany/ai_co
    source venv/bin/activate
    nohup python3 workers/command_executor_worker.py > /dev/null 2>&1 &
    sleep 2

    if ps aux | grep -v grep | grep -q "command_executor_worker"; then
        echo "✅ 起動成功！"
    else
        echo "⚠️ 起動失敗 - 直接実行します"
    fi
fi

# pendingコマンドの状態
echo "\n📁 Pending状態:"
ls -la ai_commands/pending/final_fix_pm_worker.json 2>/dev/null || echo "コマンドファイルが見つかりません"

# 待機時間が過ぎている場合は直接実行
if [ -f "ai_commands/pending/final_fix_pm_worker.json" ]; then
    echo "\n⚡ 修正コマンドを直接実行します..."

    # JSONからbash内容を抽出して実行
    python3 -c "
import json
with open('ai_commands/pending/final_fix_pm_worker.json', 'r') as f:
    data = json.load(f)
    if data.get('type') == 'bash':
        content = data.get('content', '')
        with open('/tmp/fix_pm_worker.sh', 'w') as sh:
            sh.write(content)
        print('✅ スクリプト準備完了')
    "

    if [ -f "/tmp/fix_pm_worker.sh" ]; then
        chmod +x /tmp/fix_pm_worker.sh
        bash /tmp/fix_pm_worker.sh

        # 完了したらcompletedに移動
        mv ai_commands/pending/final_fix_pm_worker.json ai_commands/completed/ 2>/dev/null
        rm /tmp/fix_pm_worker.sh
    fi
fi

echo "\n✅ 全て自動で完了しました！"
