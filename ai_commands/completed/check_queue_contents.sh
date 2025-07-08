#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo ""
echo "========================================="
echo "3. キュー内容確認"
echo "========================================="
python3 check_queue_contents.py
