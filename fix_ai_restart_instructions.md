# AI Company ai-restart 修正指示書

## 問題の概要
`ai-restart` コマンドが以下のエラーで失敗しています：
1. `No module named 'base_command'` - Pythonのインポートエラー
2. `create window failed: index 5 in use` - tmuxウィンドウの競合
3. 不要な確認プロンプトが表示される

## 修正内容

### 1. まずナレッジベースを確認
```bash
# 必要に応じて以下のナレッジベースを参照してください
cat /home/aicompany/ai_co/knowledge_base/AI_COMPANY_MASTER_KB_v5.2.md | grep -A 20 "コマンド一覧"
```

### 2. 新しいai-restartスクリプトを作成
```bash
# 完全なbashスクリプト版を作成
sudo tee /usr/local/bin/ai-restart > /dev/null << 'EOF'
#!/bin/bash
echo "=================================================="
echo "🚀 AI Company システム再起動 - $(date '+%H:%M:%S')"
echo "=================================================="

# システム停止
echo -e "\n--- システム停止 ---"
echo "ℹ️  現在のシステムを停止しています..."
tmux kill-session -t ai_company 2>/dev/null && echo "✅ tmuxセッション停止完了" || echo "ℹ️  tmuxセッションは既に停止しています"
pkill -f "worker.py" 2>/dev/null
pkill -f "task_worker" 2>/dev/null
pkill -f "pm_worker" 2>/dev/null
pkill -f "result_worker" 2>/dev/null
rm -f /tmp/ai_command_executor.pid 2>/dev/null
echo "✅ プロセス停止完了"

# 3秒待機
echo -e "\nℹ️  3秒待機中..."
sleep 3

# システム起動
echo -e "\n--- システム起動 ---"
echo "ℹ️  システムを起動しています..."
cd /home/aicompany/ai_co
bash scripts/start_company.sh

echo -e "\n--- 再起動完了 ---"
echo "✅ システム再起動が完了しました！"
EOF

# 実行権限を付与
sudo chmod +x /usr/local/bin/ai-restart
```

### 3. start_company.shを修正
```bash
# TestGeneratorWorkerの行を削除
cd /home/aicompany/ai_co/scripts
cp start_company.sh start_company.sh.backup_$(date +%Y%m%d_%H%M%S)
sed -i '/TestGeneratorWorker/,/C-m/d' start_company.sh
```

### 4. 他のコマンドも同様にbash化（オプション）
```bash
# ai-start
sudo tee /usr/local/bin/ai-start > /dev/null << 'EOF'
#!/bin/bash
echo "🏢 AI Company を起動中..."
cd /home/aicompany/ai_co
if tmux has-session -t ai_company 2>/dev/null; then
    echo "⚠️  既にAI Companyが起動しています"
    exit 0
fi
bash scripts/start_company.sh
EOF

# ai-stop
sudo tee /usr/local/bin/ai-stop > /dev/null << 'EOF'
#!/bin/bash
echo "🛑 AI Company を停止中..."
tmux kill-session -t ai_company 2>/dev/null && echo "✅ tmuxセッション停止完了" || echo "ℹ️  tmuxセッションは既に停止しています"
pkill -f "worker.py" 2>/dev/null
rm -f /tmp/ai_command_executor.pid 2>/dev/null
echo "✅ AI Company 停止完了"
EOF

# 実行権限を付与
sudo chmod +x /usr/local/bin/ai-start
sudo chmod +x /usr/local/bin/ai-stop
```

### 5. 動作確認
```bash
# 新しいai-restartをテスト
ai-restart
```

### 6. GitHub Flow でコミット（必要に応じて）
```bash
cd /home/aicompany/ai_co
gf fix ai-restart-to-bash

# 変更をステージング
git add scripts/start_company.sh

# コミット
git commit -m "🔧 [Commands] ai-restartを完全なbashスクリプトに変換

- Pythonのbase_commandインポートエラーを解決
- 確認プロンプトを削除
- TestGeneratorWorkerの起動を削除
- tmuxウィンドウの競合を解消"

# PR作成
gf pr
```

## 成功基準
- `ai-restart` コマンドが確認なしで即実行される
- エラーが表示されない
- システムが正常に再起動される

## トラブルシューティング
もし権限エラーが出る場合：
```bash
# sudoパスワードが必要な場合
echo "aicompany" | sudo -S chmod +x /usr/local/bin/ai-restart
```

## 補足
- この修正により、PythonのモジュールインポートエラーとPATHの問題を完全に回避できます
- bashスクリプトのみで動作するため、より確実です
- 将来的にPython版に戻したい場合は、base_command.pyのPATH設定を見直してください
