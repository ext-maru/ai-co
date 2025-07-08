#!/bin/bash
#!/bin/bash
# Daily log cleanup script

cd /home/aicompany/ai_co
source venv/bin/activate

# Pythonスクリプトでクリーンアップ
python3 -c "
from libs.log_manager import cleanup_old_logs
cleanup_old_logs(days=3)  # 3日以上前のログをアーカイブ
print('✅ Old logs cleaned up')
"
