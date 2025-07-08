#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "=== 自動修正適用 ==="
python3 apply_error_fix.py
