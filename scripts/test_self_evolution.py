#!/usr/bin/env python3
"""
自己進化機能テストスクリプト
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from libs.self_evolution_manager import SelfEvolutionManager

def test_evolution():
    evolution = SelfEvolutionManager()
    
    # テスト用コード
    test_code = '''#!/usr/bin/env python3
"""
テスト用の新しいワーカー
"""

import pika
import json
from datetime import datetime

class TestWorker:
    def __init__(self):
        self.name = "test_worker"
    
    def process_message(self, message):
        return f"処理完了: {message}"

if __name__ == "__main__":
    worker = TestWorker()
    print(worker.process_message("Hello"))
'''
    
    # 配置プレビュー
    preview = evolution.get_placement_preview(test_code)
    print("配置プレビュー:")
    print(f"ファイル名: {preview['filename']}")
    print(f"配置先: {preview['target_dir']}")
    print(f"フルパス: {preview['full_path']}")
    
    # 実際の配置
    result = evolution.auto_place_file(test_code, task_id="evolution_test")
    print("\n配置結果:")
    print(result)

if __name__ == "__main__":
    test_evolution()
