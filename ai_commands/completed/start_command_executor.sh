#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "=== Command Executor起動 ==="

# 既存のプロセスを確認
if ps aux | grep -E 'command_executor' | grep -v grep > /dev/null; then
    echo "✅ Command Executorは既に起動しています"
    ps aux | grep -E 'command_executor' | grep -v grep
else
    echo "🚀 Command Executorを起動します..."

    # 仮想環境をアクティベート
    source venv/bin/activate

    # バックグラウンドで起動
    nohup python3 workers/command_executor_worker.py > logs/command_executor.log 2>&1 &

    sleep 2

    # 起動確認
    if ps aux | grep -E 'command_executor' | grep -v grep > /dev/null; then
        echo "✅ Command Executorが正常に起動しました"
        ps aux | grep -E 'command_executor' | grep -v grep
    else
        echo "❌ Command Executorの起動に失敗しました"
        echo "ログを確認してください: tail -f logs/command_executor.log"
    fi
fi

echo ""
echo "=== Pending コマンドの実行 ==="
echo "Pendingディレクトリ内のファイル:"
ls -la /home/aicompany/ai_co/ai_commands/pending/
