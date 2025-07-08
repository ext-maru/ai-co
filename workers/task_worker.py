"""
task_worker.py - Enhanced Task Workerへのエイリアス

既存のテストとの互換性のために作成
"""

from workers.enhanced_task_worker import EnhancedTaskWorker as TaskWorker

# Backward compatibility exports
__all__ = ['TaskWorker']