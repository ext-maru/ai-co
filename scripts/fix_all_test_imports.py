#!/usr/bin/env python3
"""
IMPORT FIX KNIGHT - Emergency Test Import Repair System
Fixes all PROJECT_ROOT path issues and import errors in test files
"""
import os
import re
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ImportFixKnight:
    """Elder Servant: Import Fix Knight"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.fixes_applied = 0
        self.files_processed = 0

    def fix_sys_path_insert(self, file_path):
        """Fix sys.path.insert patterns to use consistent PROJECT_ROOT"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Pattern 1: Fix various PROJECT_ROOT calculations
            patterns = [
                # Pattern for Path(__file__).parent.parent...
                (
                    r"PROJECT_ROOT\s*=\s*Path\(__file__\)\.parent\.parent\.parent",
                    "PROJECT_ROOT = Path(__file__).resolve().parent.parent",
                ),
                (
                    r"PROJECT_ROOT\s*=\s*Path\(__file__\)\.parent\.parent",
                    "PROJECT_ROOT = Path(__file__).resolve().parent.parent",
                ),
                # Pattern for os.path.dirname variations
                (
                    r"sys\.path\.insert\(0,\s*os\.path\.dirname\(os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\)\)",
                    "PROJECT_ROOT = Path(__file__).resolve().parent.parent\nsys.path.insert(0, str(PROJECT_ROOT))",
                ),
                # Pattern for direct path insertions
                (
                    r'sys\.path\.insert\(0,\s*[\'"].*?/ai_co[\'"]?\)',
                    "PROJECT_ROOT = Path(__file__).resolve().parent.parent\nsys.path.insert(0, str(PROJECT_ROOT))",
                ),
                # Fix relative imports in tests
                (r"from \.\.\.(\w+)", r"from \1"),
                (r"from \.\.(\w+)", r"from \1"),
            ]

            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)

            # Ensure proper imports at top
            if "from pathlib import Path" not in content and "PROJECT_ROOT" in content:
                # Add Path import after sys import
                content = re.sub(
                    r"(import sys\n)", r"\1from pathlib import Path\n", content
                )

            # Fix duplicate PROJECT_ROOT definitions
            lines = content.split("\n")
            new_lines = []
            has_project_root = False

            for line in lines:
                if "PROJECT_ROOT =" in line and not has_project_root:
                    new_lines.append(line)
                    has_project_root = True
                elif "PROJECT_ROOT =" in line and has_project_root:
                    continue  # Skip duplicate
                else:
                    new_lines.append(line)

            content = "\n".join(new_lines)

            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.fixes_applied += 1
                print(f"✅ Fixed imports in: {file_path}")
                return True

        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")

        return False

    def add_missing_init_files(self):
        """Ensure all test directories have __init__.py files"""
        test_dirs = []
        for root, dirs, files in os.walk(self.project_root / "tests"):
            if "__pycache__" not in root:
                test_dirs.append(root)

        for dir_path in test_dirs:
            init_file = Path(dir_path) / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""Test package initialization"""\n')
                print(f"✅ Created __init__.py in: {dir_path}")
                self.fixes_applied += 1

    def fix_circular_dependencies(self):
        """Fix circular import issues by reorganizing imports"""
        # Create a mock utilities module to break circular dependencies
        mock_utils_path = self.project_root / "tests" / "mock_utils.py"

        mock_utils_content = '''"""
Common mock utilities for all tests
Breaks circular dependencies by providing centralized mocks
"""
from unittest.mock import Mock, MagicMock, patch
import json

def create_mock_rabbitmq():
    """Create mock RabbitMQ connection and channel"""
    mock_connection = Mock()
    mock_channel = Mock()
    mock_connection.channel.return_value = mock_channel

    # Setup channel methods
    mock_channel.queue_declare = Mock()
    mock_channel.basic_publish = Mock()
    mock_channel.basic_consume = Mock()
    mock_channel.start_consuming = Mock()
    mock_channel.stop_consuming = Mock()
    mock_channel.basic_ack = Mock()
    mock_channel.basic_nack = Mock()
    mock_channel.close = Mock()

    return mock_connection, mock_channel

def create_mock_redis():
    """Create mock Redis client"""
    mock_redis = Mock()
    mock_redis.get = Mock(return_value=None)
    mock_redis.set = Mock(return_value=True)
    mock_redis.delete = Mock(return_value=1)
    mock_redis.exists = Mock(return_value=False)
    mock_redis.expire = Mock(return_value=True)
    mock_redis.hget = Mock(return_value=None)
    mock_redis.hset = Mock(return_value=1)
    mock_redis.hdel = Mock(return_value=1)
    mock_redis.hgetall = Mock(return_value={})
    mock_redis.pipeline = Mock(return_value=mock_redis)
    mock_redis.execute = Mock(return_value=[])
    return mock_redis

def create_mock_slack():
    """Create mock Slack client"""
    mock_slack = Mock()
    mock_slack.chat_postMessage = Mock(return_value={'ok': True, 'ts': '1234567890.123456'})
    mock_slack.conversations_list = Mock(return_value={'ok': True, 'channels': []})
    mock_slack.users_list = Mock(return_value={'ok': True, 'members': []})
    mock_slack.conversations_history = Mock(return_value={'ok': True, 'messages': []})
    return mock_slack

def create_mock_logger():
    """Create mock logger"""
    mock_logger = Mock()
    mock_logger.info = Mock()
    mock_logger.debug = Mock()
    mock_logger.warning = Mock()
    mock_logger.error = Mock()
    mock_logger.critical = Mock()
    return mock_logger

def create_test_task_data(task_id='test-123', task_type='test_task'):
    """Create standard test task data"""
    return {
        'task_id': task_id,
        'type': task_type,
        'data': {'test': True},
        'created_at': '2025-01-01T00:00:00Z',
        'priority': 'normal',
        'retry_count': 0,
        'max_retries': 3,
        'status': 'pending'
    }
'''

        if not mock_utils_path.exists():
            mock_utils_path.write_text(mock_utils_content)
            print(f"✅ Created mock_utils.py to break circular dependencies")
            self.fixes_applied += 1

    def run_all_fixes(self):
        """Run all import fixes"""
        print("🛡️ IMPORT FIX KNIGHT DEPLOYED")
        print("=" * 60)

        # Step 1: Add missing __init__.py files
        print("\n📁 Step 1: Adding missing __init__.py files...")
        self.add_missing_init_files()

        # Step 2: Fix circular dependencies
        print("\n🔄 Step 2: Breaking circular dependencies...")
        self.fix_circular_dependencies()

        # Step 3: Fix all test imports
        print("\n🔧 Step 3: Fixing imports in all test files...")
        test_files = list(Path(self.project_root / "tests").rglob("*.py"))

        for test_file in test_files:
            if "__pycache__" not in str(test_file):
                self.files_processed += 1
                self.fix_sys_path_insert(test_file)

        print("\n" + "=" * 60)
        print(f"✅ IMPORT FIX KNIGHT MISSION COMPLETE")
        print(f"📊 Files processed: {self.files_processed}")
        print(f"🔧 Fixes applied: {self.fixes_applied}")
        print("=" * 60)


if __name__ == "__main__":
    knight = ImportFixKnight()
    knight.run_all_fixes()
