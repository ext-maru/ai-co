#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

# データベースディレクトリ確認
mkdir -p db
mkdir -p backups/autofix

# Phase 2のデータベース初期化（テスト実行）
python3 -c "
from libs.auto_fix_executor import AutoFixExecutor
executor = AutoFixExecutor()
print('✅ AutoFixExecutor データベース初期化完了')
"

echo "✅ データベース初期化完了"
