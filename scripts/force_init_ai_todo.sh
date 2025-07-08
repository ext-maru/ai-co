#!/bin/bash
# AI Todoシステム状態確認と強制初期化

echo "🔍 AI Todoシステム詳細確認"
echo "=" * 60

# 1. Command Executorプロセス確認
echo -e "\n📊 Command Executorプロセス:"
ps aux | grep -E "command_executor" | grep -v grep

# 2. 最新のCommand Executorログ確認
echo -e "\n📋 最新のCommand Executorログ (最新10件):"
ls -lt /home/aicompany/ai_co/ai_commands/logs/*.log | head -10

# 3. pendingファイル確認
echo -e "\n📁 AI Todo関連のpendingファイル:"
ls -la /home/aicompany/ai_co/ai_commands/pending/*todo*

# 4. runningディレクトリ確認
echo -e "\n🔄 runningディレクトリのファイル数:"
ls /home/aicompany/ai_co/ai_commands/running | wc -l

# 5. AI Todoシステムを強制初期化
echo -e "\n🚀 AI Todoシステムを強制初期化します..."

cd /home/aicompany/ai_co
source venv/bin/activate

# init_ai_todo_system.pyを直接実行
python3 << 'EOF'
import sys
sys.path.append('/home/aicompany/ai_co')

print("AI Todoシステム初期化開始...")

try:
    # init_ai_todo_system.pyの内容を実行
    exec(open('/home/aicompany/ai_co/scripts/init_ai_todo_system.py').read())
    print("✅ 初期化スクリプト実行完了")
except Exception as e:
    print(f"❌ エラー: {e}")

# ai_todoディレクトリ確認
from pathlib import Path
todo_dir = Path("/home/aicompany/ai_co/ai_todo")
if todo_dir.exists():
    print(f"✅ ai_todoディレクトリが作成されました")
    files = list(todo_dir.glob("*"))
    print(f"   ファイル数: {len(files)}")
    for f in files[:5]:
        print(f"   - {f.name}")
else:
    print("❌ ai_todoディレクトリがまだ作成されていません")

# 知識ベース確認
kb_dir = Path("/home/aicompany/ai_co/knowledge_base/ai_learning")
if kb_dir.exists():
    print(f"✅ 知識ベースディレクトリが作成されました")
else:
    print("❌ 知識ベースディレクトリがまだ作成されていません")
EOF

echo -e "\n✨ 確認完了！"
