"""
テスト用ユーティリティ関数
"""

import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def setup_test_environment():
    """テスト環境をセットアップする統一関数"""
    # プロジェクトルートを確実にパスに追加
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    
    # 必要なディレクトリの存在確認
    libs_dir = PROJECT_ROOT / "libs"
    if not libs_dir.exists():
        libs_dir.mkdir(exist_ok=True)
    
    return PROJECT_ROOT


def create_mock_task(task_id="test-123", prompt="Test task", priority=5, **kwargs):
    """テスト用のタスクデータを作成"""
    task = {
        "task_id": task_id,
        "prompt": prompt,
        "priority": priority,
        "created_at": datetime.now().isoformat(),
        "status": "pending"
    }
    task.update(kwargs)
    return task


def create_test_file(content="Test content", suffix=".txt"):
    """テスト用の一時ファイルを作成"""
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
        f.write(content)
        return Path(f.name)


def wait_for_condition(condition_func, timeout=30, interval=0.1):
    """条件が満たされるまで待機"""
    import time
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    return False


def mock_successful_claude_response():
    """成功レスポンスのモック"""
    return {
        "status": "success",
        "content": "Task completed successfully",
        "files_created": ["test_file.py"],
        "execution_time": 1.5
    }


def mock_failed_claude_response():
    """失敗レスポンスのモック"""
    return {
        "status": "error",
        "error": "Claude API error",
        "error_type": "APIError",
        "execution_time": 0.5
    }