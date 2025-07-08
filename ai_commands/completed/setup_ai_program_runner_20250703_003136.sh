#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "🚀 AI Program Runner 自動セットアップ開始"
echo "Time: $(date)"
echo "=================================="

# 1. ディレクトリ作成
echo "📁 ディレクトリ構造を作成..."
mkdir -p ai_programs/{inbox,archive,ai_logs,failed}
chmod -R 755 ai_programs/

# 2. 動作確認
echo ""
echo "🧪 動作確認..."
source venv/bin/activate
python3 libs/ai_program_runner.py

# 3. デモ実行
echo ""
echo "🎯 デモプログラム実行..."
python3 demo_ai_program_runner.py

echo ""
echo "=================================="
echo "✅ セットアップ完了！"
echo ""
echo "📊 作成されたディレクトリ:"
find ai_programs -type d | sort

echo ""
echo "🚀 使い方:"
echo "from libs.ai_program_runner import AIProgramRunner"
echo "runner = AIProgramRunner()"
echo "runner.run_python_program(code, 'task_name')"
