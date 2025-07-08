#!/usr/bin/env python3
"""
AI Company ログマネージャー
ログ出力を統一管理するヘルパーモジュール
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

class LogManager:
    """統一ログ管理クラス"""
    
    def __init__(self, name: str, log_type: str = 'general'):
        """
        Args:
            name: ロガー名（通常は__name__）
            log_type: ログタイプ（slack, worker, error等）
        """
        self.name = name
        self.log_type = log_type
        self.project_root = Path("/home/aicompany/ai_co")
        self.log_dir = self._get_log_dir()
        self.logger = self._setup_logger()
    
    def _get_log_dir(self) -> Path:
        """ログディレクトリを取得（自動作成）"""
        log_dir = self.project_root / 'logs' / self.log_type
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    
    def _setup_logger(self) -> logging.Logger:
        """ロガーを設定"""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)
        
        # 既存のハンドラーをクリア
        logger.handlers.clear()
        
        # コンソール出力
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # ファイル出力（日付別）
        today = datetime.now().strftime('%Y%m%d')
        log_file = self.log_dir / f"{self.log_type}_{today}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        
        return logger
    
    def get_logger(self) -> logging.Logger:
        """ロガーインスタンスを取得"""
        return self.logger
    
    @classmethod
    def get_slack_logger(cls, name: str) -> logging.Logger:
        """Slack専用ロガーを取得"""
        manager = cls(name, 'slack')
        return manager.get_logger()
    
    @classmethod
    def get_worker_logger(cls, name: str) -> logging.Logger:
        """ワーカー専用ロガーを取得"""
        manager = cls(name, 'worker')
        return manager.get_logger()
    
    @classmethod
    def get_error_logger(cls, name: str) -> logging.Logger:
        """エラー専用ロガーを取得"""
        manager = cls(name, 'error')
        return manager.get_logger()

def cleanup_old_logs(days: int = 7, log_type: Optional[str] = None):
    """古いログファイルをクリーンアップ"""
    from datetime import timedelta
    
    project_root = Path("/home/aicompany/ai_co")
    
    if log_type:
        log_dirs = [project_root / 'logs' / log_type]
    else:
        log_dirs = list((project_root / 'logs').glob('*/'))
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for log_dir in log_dirs:
        if not log_dir.is_dir():
            continue
            
        for log_file in log_dir.glob('*.log'):
            try:
                # ファイルの更新日時をチェック
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_mtime < cutoff_date:
                    # アーカイブディレクトリに移動
                    archive_dir = project_root / 'logs' / 'archive' / log_dir.name
                    archive_dir.mkdir(parents=True, exist_ok=True)
                    
                    archive_path = archive_dir / log_file.name
                    log_file.rename(archive_path)
                    
            except Exception as e:
                print(f"Error processing {log_file}: {e}")

# 使用例:
if __name__ == "__main__":
    # Slackログの例
    slack_logger = LogManager.get_slack_logger(__name__)
    slack_logger.info("This is a Slack log message")
    
    # ワーカーログの例
    worker_logger = LogManager.get_worker_logger(__name__)
    worker_logger.info("This is a worker log message")
    
    # 古いログのクリーンアップ（7日以上前のログをアーカイブ）
    cleanup_old_logs(days=7)
