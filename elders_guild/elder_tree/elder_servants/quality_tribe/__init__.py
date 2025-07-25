"""
🏛️ 品質保証サーバント群 - python-a2a統合
One Servant, One Command原則に基づく実装
"""

# エンジンは常にインポート可能
from .engines import *

# サーバントは依存関係がある場合のみインポート
try:
    from .quality_watcher.quality_watcher_servant import QualityWatcherServant
    from .test_forge.test_forge_servant import TestForgeServant
    from .comprehensive_guardian.comprehensive_guardian_servant import ComprehensiveGuardianServant
    
    __all__ = [
        "QualityWatcherServant",
        "TestForgeServant", 
        "ComprehensiveGuardianServant"
    ]
except ImportError:
    # python_a2aが不在の場合はエンジンのみ利用可能
    __all__ = []