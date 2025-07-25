"""
Report Management System

完了報告を受け取り、分析し、次のアクションを提案するシステム
"""

from .decision_support import DecisionSupportSystem
from .report_analyzer import ReportAnalyzer
from .report_manager import ReportManager
from .report_tracker import CompletionReportTracker

__all__ = [
    "CompletionReportTracker",
    "ReportAnalyzer",
    "DecisionSupportSystem",
    "ReportManager",
]

__version__ = "1.0.0"
