#!/bin/bash
# 日本語化システム状態確認

cd /home/aicompany/ai_co
source venv/bin/activate

python3 -c "
import sys
import json
from pathlib import Path

print('🌏 AI Company 日本語化システム状態確認')
print('=' * 50)

# 1. core/messages.py の存在確認
messages_path = Path('/home/aicompany/ai_co/core/messages.py')
if messages_path.exists():
    print('✅ メッセージシステム: インストール済み')
else:
    print('❌ メッセージシステム: 未インストール')

# 2. system.json の言語設定確認
config_path = Path('/home/aicompany/ai_co/config/system.json')
if config_path.exists():
    try:
        config = json.loads(config_path.read_text())
        lang = config.get('language', '未設定')
        print(f'✅ 言語設定: {lang}')
    except:
        print('❌ 言語設定: 読み込みエラー')
else:
    print('❌ 言語設定: 設定ファイルなし')

# 3. 日本語プロンプトヘルパー確認
prompt_path = Path('/home/aicompany/ai_co/libs/japanese_prompt.py')
if prompt_path.exists():
    print('✅ Claude日本語設定: インストール済み')
else:
    print('❌ Claude日本語設定: 未インストール')

# 4. メッセージテスト
try:
    sys.path.insert(0, '/home/aicompany/ai_co')
    from core import msg
    test_msg = msg('task_completed', task_id='test', duration=1.0, files=3)
    print(f'✅ メッセージテスト: {test_msg}')
except Exception as e:
    print(f'❌ メッセージテスト: エラー - {str(e)}')

print('=' * 50)
print('🎯 診断完了')
"
