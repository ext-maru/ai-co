"""
pm_worker.py - Enhanced PM Workerへのエイリアス

既存のテストとの互換性のために作成
"""

from workers.enhanced_pm_worker import EnhancedPMWorker as PMWorker

# Backward compatibility exports
__all__ = ['PMWorker']