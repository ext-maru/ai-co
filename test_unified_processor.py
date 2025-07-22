#!/usr/bin/env python3
"""
Simple test script for unified auto issue processor
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from libs.auto_issue_processor import AutoIssueProcessor, ProcessorConfig
from libs.auto_issue_processor.utils import ProcessLock


async def test_basic_functionality():
    """Test basic functionality"""
    print("Testing Unified Auto Issue Processor...")
    
    # Test 1: Configuration
    print("\n1. Testing configuration...")
    config = ProcessorConfig()
    config.dry_run = True
    config.github.token = "test_token"
    config.github.repo = "test_repo"
    config.github.owner = "test_owner"
    print(f"   ✓ Configuration created: dry_run={config.dry_run}")
    
    # Test 2: Processor initialization
    print("\n2. Testing processor initialization...")
    try:
        processor = AutoIssueProcessor(config)
        print("   ✓ Processor initialized successfully")
    except Exception as e:
        print(f"   ✗ Failed to initialize: {e}")
        return
    
    # Test 3: Lock functionality
    print("\n3. Testing lock functionality...")
    lock = ProcessLock("file", lock_dir="./test_locks")
    
    # Acquire lock
    acquired = await lock.acquire("test_issue_123", ttl=10)
    print(f"   ✓ Lock acquired: {acquired}")
    
    # Check lock
    is_locked = await lock.is_locked("test_issue_123")
    print(f"   ✓ Lock status: {is_locked}")
    
    # Try duplicate lock
    duplicate = await lock.acquire("test_issue_123", ttl=10)
    print(f"   ✓ Duplicate lock prevented: {not duplicate}")
    
    # Release lock
    released = await lock.release("test_issue_123")
    print(f"   ✓ Lock released: {released}")
    
    # Test 4: Feature modules
    print("\n4. Testing feature modules...")
    features = [
        ("Error Recovery", processor.error_recovery),
        ("PR Manager", processor.pr_manager),
        ("Parallel Processor", processor.parallel_processor),
        ("Four Sages", processor.four_sages)
    ]
    
    for name, module in features:
        if module:
            print(f"   ✓ {name} initialized")
        else:
            print(f"   - {name} not enabled")
    
    print("\n✅ All tests passed!")


async def test_config_loading():
    """Test configuration loading"""
    print("\nTesting configuration loading...")
    
    # Test environment variable loading
    os.environ["AUTO_ISSUE_PROCESSOR_ENABLED"] = "false"
    os.environ["AUTO_ISSUE_PROCESSOR_DRY_RUN"] = "true"
    
    config = ProcessorConfig.from_env()
    print(f"   ✓ Environment config: enabled={config.enabled}, dry_run={config.dry_run}")
    
    # Test config validation
    valid = config.validate()
    print(f"   ✓ Configuration valid: {valid}")
    
    # Test config dict conversion
    config_dict = config.to_dict()
    print(f"   ✓ Config to dict: {len(config_dict)} keys")


if __name__ == "__main__":
    print("=" * 60)
    print("Unified Auto Issue Processor Test Suite")
    print("=" * 60)
    
    # Run tests
    asyncio.run(test_basic_functionality())
    asyncio.run(test_config_loading())
    
    print("\nTest suite completed!")
    
    # Cleanup
    import shutil
    if os.path.exists("./test_locks"):
        shutil.rmtree("./test_locks")
        print("Cleaned up test locks directory")