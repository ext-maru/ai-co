#!/usr/bin/env python3
"""
Elders Guild ログ出力基準
プロフェッショナルで客観的なログ出力を実現
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

class LoggingStandards:
    """ログ出力の標準化クラス"""
    
    # ログレベル別の推奨形式
    LOG_FORMATS = {
        'DEBUG': '[{timestamp}] DEBUG: {component} - {message}',
        'INFO': '[{timestamp}] INFO: {component} - {message}',
        'WARNING': '[{timestamp}] WARN: {component} - {message}',
        'ERROR': '[{timestamp}] ERROR: {component} - {message} - {error_details}',
        'CRITICAL': '[{timestamp}] CRITICAL: {component} - {message} - Action required'
    }
    
    # 絵文字使用ガイドライン（最小限に）
    EMOJI_GUIDE = {
        'start': '',      # 開始時は絵文字不要
        'success': '✓',   # シンプルなチェックマーク
        'error': '✗',     # シンプルなエラーマーク
        'warning': '!',   # 警告は記号で十分
        'info': '',       # 情報レベルは絵文字不要
    }
    
    @staticmethod
    def format_task_start(task_id: str, task_type: str) -> str:
        """タスク開始ログ（客観的）"""
        return f"Task started: {task_id} (type: {task_type})"
    
    @staticmethod
    def format_task_complete(task_id: str, duration_seconds: float) -> str:
        """タスク完了ログ（数値データ含む）"""
        return f"Task completed: {task_id} (duration: {duration_seconds:.2f}s)"
    
    @staticmethod
    def format_error(task_id: str, error: Exception, context: str) -> str:
        """エラーログ（技術的詳細）"""
        return f"Task failed: {task_id} in {context} - {type(error).__name__}: {str(error)}"
    
    @staticmethod
    def format_metric(metric_name: str, value: Any, unit: str = "") -> str:
        """メトリクスログ（数値中心）"""
        return f"Metric: {metric_name}={value}{unit}"


class ProfessionalLogger:
    """プロフェッショナルなログ出力を行うロガー"""
    
    def __init__(self, component_name: str):
        self.component = component_name
        self.logger = logging.getLogger(component_name)
        self.start_times: Dict[str, datetime] = {}
    
    def task_start(self, task_id: str, task_type: str, details: Optional[Dict] = None):
        """タスク開始を記録"""
        self.start_times[task_id] = datetime.now()
        
        message = f"Task {task_id} started (type: {task_type})"
        if details:
            # 重要な詳細のみを追加
            relevant_details = {k: v for k, v in details.items() 
                              if k in ['priority', 'retry_count', 'queue']}
            if relevant_details:
                message += f" - {relevant_details}"
        
        self.logger.info(message)
    
    def task_complete(self, task_id: str, result_summary: Optional[str] = None):
        """タスク完了を記録"""
        duration = None
        if task_id in self.start_times:
            duration = (datetime.now() - self.start_times[task_id]).total_seconds()
            del self.start_times[task_id]
        
        message = f"Task {task_id} completed"
        if duration:
            message += f" (duration: {duration:.2f}s)"
        if result_summary:
            # 結果の要約は簡潔に
            message += f" - {result_summary[:50]}"
        
        self.logger.info(message)
    
    def task_error(self, task_id: str, error: Exception, recoverable: bool = True):
        """タスクエラーを記録"""
        message = f"Task {task_id} error: {type(error).__name__}: {str(error)}"
        if recoverable:
            message += " (will retry)"
        
        if recoverable:
            self.logger.warning(message)
        else:
            self.logger.error(message)
    
    def metric(self, name: str, value: Any, unit: str = ""):
        """メトリクスを記録"""
        self.logger.info(f"Metric: {name}={value}{unit}")
    
    def system_state(self, state: Dict[str, Any]):
        """システム状態を記録"""
        # 重要な状態情報のみ
        important_states = ['queue_length', 'active_workers', 'memory_usage', 'error_rate']
        filtered_state = {k: v for k, v in state.items() if k in important_states}
        
        self.logger.info(f"System state: {filtered_state}")


# ログ出力のベストプラクティス
LOG_BEST_PRACTICES = """
# Elders Guild ログ出力ベストプラクティス

## 原則
1. 客観的で技術的な情報を優先
2. 数値データを含める（処理時間、件数、サイズ等）
3. 誇張表現を避ける
4. 絵文字は最小限（成功/失敗の記号程度）

## 推奨フォーマット

### INFO レベル
- "Task {id} started (type: {type})"
- "Task {id} completed (duration: {time}s)"
- "Processing {count} items"
- "Queue length: {length}"

### WARNING レベル
- "Retry attempt {n} for task {id}"
- "High memory usage: {percent}%"
- "Slow response time: {time}s"

### ERROR レベル
- "Task {id} failed: {error_type}: {message}"
- "Connection lost to {service}"
- "Invalid data format in {file}"

## 避けるべき表現
- "革新的な"、"素晴らしい"、"完璧な"
- "🚀"、"✨"、"🎉"などの装飾的絵文字
- "！！！"などの過度な強調
- 主観的な評価

## Slack通知の改善

### Before
"🚀 革新的なAIタスクが完璧に成功しました！✨"

### After
"Task completed: code_20250702_123456 (duration: 2.3s, files: 3)"
"""


if __name__ == "__main__":
    # 使用例
    logger = ProfessionalLogger("TaskWorker")
    
    # タスク処理の例
    task_id = "code_20250702_123456"
    logger.task_start(task_id, "code", {"priority": "normal"})
    
    # 処理中のメトリクス
    logger.metric("files_processed", 5)
    logger.metric("memory_usage", 156.2, "MB")
    
    # 完了
    logger.task_complete(task_id, "Created 3 files")
