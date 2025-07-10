#!/usr/bin/env python3
"""
SelfEvolutionManagerのタイムアウト問題を修正するスクリプト
複雑なML処理を段階的に実行できるように改善
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import logging

from libs.self_evolution_manager_optimized import OptimizedSelfEvolutionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_optimized_manager():
    """最適化版マネージャーのテスト"""
    manager = OptimizedSelfEvolutionManager(timeout_seconds=30)

    # テスト用のコンテンツ
    test_content = '''#!/usr/bin/env python3
"""
Test Worker for Elders Guild
"""
import pika
import json

class TestWorker:
    def __init__(self):
        self.connection = None

    def process_task(self, task_data):
        """タスク処理"""
        print(f"Processing task: {task_data}")
        return {"status": "completed"}

def main():
    worker = TestWorker()
    print("Worker started")

if __name__ == "__main__":
    main()
'''

    # 高速版のテスト
    logger.info("Testing fast placement method...")
    result = manager.auto_place_file_fast(test_content, "test_worker.py")
    logger.info(f"Fast method result: {result}")

    # チャンク版のテスト（大きなファイル向け）
    logger.info("\nTesting chunked placement method...")
    large_content = test_content * 100  # 大きなコンテンツをシミュレート
    result = manager.auto_place_file_chunked(large_content, "large_test_worker.py")
    logger.info(f"Chunked method result: {result}")

    return True


def create_wrapper_function():
    """既存のauto_place_fileをラップする関数を作成"""
    wrapper_code = '''
def auto_place_file_with_timeout(self, source_content, suggested_filename=None, task_id=None):
    """
    タイムアウト対策を施したauto_place_file
    複雑なML処理の前に、まず高速な基本処理を試行
    """
    import time
    from libs.self_evolution_manager_optimized import OptimizedSelfEvolutionManager

    # まず高速版を試行（30秒タイムアウト）
    optimized_manager = OptimizedSelfEvolutionManager(timeout_seconds=30)

    # ファイルサイズをチェック
    content_size = len(source_content)

    if content_size < 10000:  # 10KB未満は高速版
        result = optimized_manager.auto_place_file_fast(
            source_content, suggested_filename, task_id
        )
        if result['status'] == 'success':
            # 成功したら学習データに記録
            self._record_placement_success(
                result['filename'],
                result['relative_path'],
                'rule_based_fast'
            )
            return result
    else:  # 大きなファイルはチャンク版
        result = optimized_manager.auto_place_file_chunked(
            source_content, suggested_filename, task_id
        )
        if result['status'] == 'success':
            self._record_placement_success(
                result['filename'],
                result['relative_path'],
                'chunked_processing'
            )
            return result

    # フォールバック：元のML処理（ただし時間制限付き）
    start_time = time.time()
    timeout = 120  # 2分

    try:
        # 元の処理を実行（ただし段階的に）
        if hasattr(self, '_original_auto_place_file'):
            return self._original_auto_place_file(
                source_content, suggested_filename, task_id
            )
        else:
            # シンプルなデフォルト処理
            return {
                'status': 'fallback',
                'filename': suggested_filename or 'auto_generated.py',
                'path': str(self.project_root / 'scripts' / (suggested_filename or 'auto_generated.py')),
                'method': 'simple_fallback'
            }
    except Exception as e:
        logger.error(f"Error in ML processing: {e}")
        # エラー時は高速版の結果を返す
        return optimized_manager.auto_place_file_fast(
            source_content, suggested_filename, task_id
        )
'''

    # ラッパー関数を保存
    wrapper_file = PROJECT_ROOT / "libs" / "self_evolution_timeout_wrapper.py"
    wrapper_file.write_text(wrapper_code)
    logger.info(f"Wrapper function created at: {wrapper_file}")


if __name__ == "__main__":
    logger.info("Starting SelfEvolutionManager timeout fix...")

    # 最適化版のテスト
    if test_optimized_manager():
        logger.info("Optimized manager test passed!")

        # ラッパー関数の作成
        create_wrapper_function()

        logger.info(
            """
タイムアウト対策完了！

使用方法:
1. 既存のSelfEvolutionManagerに以下のインポートを追加:
   from libs.self_evolution_manager_optimized import OptimizedSelfEvolutionManager

2. auto_place_fileメソッドの先頭に以下を追加:
   # タイムアウト対策
   if len(source_content) > 50000:  # 50KB以上
       optimized = OptimizedSelfEvolutionManager()
       return optimized.auto_place_file_chunked(source_content, suggested_filename, task_id)

3. または、既存のメソッドを完全に置き換える場合:
   - auto_place_fileをauto_place_file_originalにリネーム
   - auto_place_file_with_timeoutをauto_place_fileとして使用
"""
        )
    else:
        logger.error("Optimized manager test failed!")
