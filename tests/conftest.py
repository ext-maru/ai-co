"""
pytest設定 - エルダー評議会承認
"""
import os
import sys
from pathlib import Path

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 環境変数設定
os.environ['PROJECT_ROOT'] = str(PROJECT_ROOT)
os.environ['TESTING'] = 'true'
os.environ['AI_COMPANY_ENV'] = 'test'

# pytest設定
def pytest_configure(config):
    """pytest設定時の処理"""
    # カスタムマーカー登録
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "timeout: Timeout tests")
