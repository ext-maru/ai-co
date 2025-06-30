#!/usr/bin/env python3
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
