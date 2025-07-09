#!/usr/bin/env python3
"""
Simple test to check if basic pytest execution works
"""
import sys
from pathlib import Path

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_basic():
    """Basic test that should always pass"""
    assert 1 + 1 == 2

def test_import():
    """Test that basic imports work"""
    import os
    import sys
    assert os is not None
    assert sys is not None

if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])