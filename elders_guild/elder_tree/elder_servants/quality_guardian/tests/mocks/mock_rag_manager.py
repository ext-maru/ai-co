"""Mock RAG Manager for testing"""
from pathlib import Path

# Add project root to Python path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from unittest.mock import MagicMock

class MockRAGManager:
    """MockRAGManager管理クラス"""
    def __init__(self):
        self.search_context = MagicMock(return_value="Mocked context")
        self.save_history = MagicMock()

def create_mock_rag_manager():
    return MockRAGManager()
