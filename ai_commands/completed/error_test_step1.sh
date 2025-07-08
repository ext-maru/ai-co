#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "=== エラーテスト実行 ==="
python3 run_error_test.py
