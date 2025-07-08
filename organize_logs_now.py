#!/usr/bin/env python3
"""
AI Company ログ整理ツール
自動生成日時: 2025-01-04 16:58:00
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import logging

# プロジェクトルート
PROJECT_ROOT = Path("/home/aicompany/ai_co")

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def organize_logs():
    """ログファイルを整理する"""
    
    # 1. ログ専用ディレクトリを作成
    log_dirs = {
        'slack': PROJECT_ROOT / 'logs' / 'slack',
        'archive': PROJECT_ROOT / 'logs' / 'archive' / 'slack',
        'temp': PROJECT_ROOT / 'logs' / 'temp'
    }
    
    for dir_path in log_dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")
    
    # 2. すべてのslack_project_status_*.logファイルを検索
    log_files = list(PROJECT_ROOT.glob("slack_project_status_*.log"))
    logger.info(f"Found {len(log_files)} log files to organize")
    
    # 3. ファイルを日付で分類
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    stats = {
        'moved_today': 0,
        'moved_yesterday': 0,
        'archived': 0,
        'deleted': 0,
        'errors': 0
    }
    
    for log_file in log_files:
        try:
            # ファイル名から日付を抽出
            # slack_project_status_YYYYMMDD_HHMMSS.log
            filename = log_file.name
            date_str = filename.split('_')[3]  # YYYYMMDD部分
            file_date = datetime.strptime(date_str, '%Y%m%d').date()
            
            # 今日のログ -> logs/slack/へ移動
            if file_date == today:
                dest = log_dirs['slack'] / filename
                shutil.move(str(log_file), str(dest))
                stats['moved_today'] += 1
                logger.info(f"Moved today's log: {filename}")
            
            # 昨日のログ -> logs/slack/へ移動（まだ参照する可能性）
            elif file_date == yesterday:
                dest = log_dirs['slack'] / filename
                shutil.move(str(log_file), str(dest))
                stats['moved_yesterday'] += 1
                logger.info(f"Moved yesterday's log: {filename}")
            
            # それ以前のログ -> アーカイブへ
            else:
                dest = log_dirs['archive'] / filename
                shutil.move(str(log_file), str(dest))
                stats['archived'] += 1
                logger.info(f"Archived old log: {filename}")
                
        except Exception as e:
            logger.error(f"Error processing {log_file}: {str(e)}")
            stats['errors'] += 1
    
    # 4. 統計を表示
    logger.info("\n=== Log Organization Complete ===")
    logger.info(f"Today's logs moved: {stats['moved_today']}")
    logger.info(f"Yesterday's logs moved: {stats['moved_yesterday']}")
    logger.info(f"Old logs archived: {stats['archived']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info(f"Total processed: {len(log_files)}")
    
    # 5. 今後のログ出力設定を更新
    update_log_configs()
    
    # 6. Slack通知
    notify_slack(stats)

def update_log_configs():
    """各設定ファイルのログ出力先を更新"""
    
    # config.yamlを更新
    config_file = PROJECT_ROOT / 'config' / 'config.yaml'
    if config_file.exists():
        with open(config_file, 'r') as f:
            content = f.read()
        
        # ログディレクトリのパスを更新
        if 'log_dir:' in content:
            content = content.replace(
                'log_dir: .',
                'log_dir: logs/slack'
            )
        else:
            # log_dir設定がない場合は追加
            content += '\n\nlogging:\n  log_dir: logs/slack\n'
        
        with open(config_file, 'w') as f:
            f.write(content)
        
        logger.info("Updated config.yaml log directory")
    
    # .gitignoreにログディレクトリを追加
    gitignore_file = PROJECT_ROOT / '.gitignore'
    if gitignore_file.exists():
        with open(gitignore_file, 'r') as f:
            gitignore_content = f.read()
        
        if 'logs/' not in gitignore_content:
            with open(gitignore_file, 'a') as f:
                f.write('\n# Organized log directories\nlogs/\n')
            logger.info("Updated .gitignore")

def notify_slack(stats):
    """Slack通知を送信"""
    try:
        from libs.slack_notifier import SlackNotifier
        notifier = SlackNotifier()
        
        message = f"""
🗂️ **ログファイル整理完了**

📊 **処理結果:**
• 今日のログ: {stats['moved_today']}件
• 昨日のログ: {stats['moved_yesterday']}件  
• アーカイブ: {stats['archived']}件
• エラー: {stats['errors']}件

📁 **新しいログ構造:**
```
/home/aicompany/ai_co/logs/
├── slack/        # 最新のログ（今日・昨日）
├── archive/      # 古いログのアーカイブ
│   └── slack/
└── temp/         # 一時ファイル用
```

今後のログは自動的に `logs/slack/` に保存されます。
        """
        
        notifier.send_message(message)
        logger.info("Slack notification sent")
        
    except Exception as e:
        logger.warning(f"Failed to send Slack notification: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting log organization...")
    organize_logs()
    logger.info("Log organization complete!")
