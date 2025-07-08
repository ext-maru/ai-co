#!/usr/bin/env python3
"""
実際のワーカー動作をシミュレートしたテスト
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# ワーカー動作シミュレーションテスト
simulation_test = """#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "🎮 ワーカー動作シミュレーションテスト"
echo "===================================="
echo ""
echo "実際のPMWorkerの動作をシミュレートします..."
echo ""

# Pythonでシミュレーション実行
python3 -c "
import time
from datetime import datetime
from libs.slack_channel_notifier import SlackChannelNotifier

notifier = SlackChannelNotifier()

print('📊 シナリオ1: キューが増加してスケールアップ')
print('-' * 40)
time.sleep(1)

# キューが徐々に増加
for queue_len in [3, 5, 8]:
    print(f'キュー長: {queue_len}')
    time.sleep(0.5)

# スケールアップ通知
print('→ スケールアップを実行')
notifier.send_scaling_notification(
    action='up',
    current_workers=1,
    target_workers=2,
    queue_length=8,
    task_id=f'auto_scale_{datetime.now().strftime('%Y%m%d_%H%M%S')}'
)

print('')
print('📊 シナリオ2: ワーカーの健康状態異常を検出')
print('-' * 40)
time.sleep(2)

print('ワーカー task_worker_001 の異常を検出:')
print('  - CPU使用率: 95%')
print('  - 応答時間: 5.2秒（閾値: 3秒）')
print('→ 自動再起動を実行')

notifier.send_health_notification(
    worker_id='task_worker_001',
    action='自動再起動',
    issues=['CPU使用率過高 (95%)', '応答時間超過 (5.2s > 3.0s)'],
    success=True
)

print('')
print('📊 シナリオ3: キューが減少してスケールダウン')
print('-' * 40)
time.sleep(2)

# キューが減少
for queue_len in [3, 1, 0]:
    print(f'キュー長: {queue_len}')
    time.sleep(0.5)

print('→ スケールダウンを実行')
notifier.send_scaling_notification(
    action='down',
    current_workers=2,
    target_workers=1,
    queue_length=0,
    task_id=f'auto_scale_{datetime.now().strftime('%Y%m%d_%H%M%S')}'
)

print('')
print('=' * 50)
print('✅ シミュレーションテスト完了')
print('')
print('📋 Slackで以下の通知を確認してください:')
print('')
print('#ai-company-scaling:')
print('  - スケールアップ通知（1→2 ワーカー）')
print('  - スケールダウン通知（2→1 ワーカー）')
print('')
print('#ai-company-health:')
print('  - ワーカー自動再起動通知')
"

echo ""
echo "✅ シミュレーションテスト完了"
"""

# コマンドを作成
result = helper.create_bash_command(
    content=simulation_test,
    command_id="simulate_worker_scaling"
)

print(f"✅ シミュレーションテストを作成しました: {result['command_id']}")
print("\n6秒後に自動実行されます...")
