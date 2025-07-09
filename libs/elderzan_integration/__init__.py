#!/usr/bin/env python3
"""
PROJECT ELDERZAN統合システム
80%コストカット実現のための統合APIシステム
"""

from .core.integrated_api import ElderZanIntegratedAPI
from .core.cost_optimizer import CostOptimizedProcessor
from .core.error_handler import UnifiedErrorHandler
from .core.performance_monitor import PerformanceMonitor

__version__ = "1.0.0"
__author__ = "AI Company - PROJECT ELDERZAN"
__description__ = "統合API・4賢者システム・80%コストカット実現"

__all__ = [
    "ElderZanIntegratedAPI",
    "CostOptimizedProcessor", 
    "UnifiedErrorHandler",
    "PerformanceMonitor"
]