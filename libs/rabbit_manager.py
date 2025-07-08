#!/usr/bin/env python3
"""
RabbitManager - RabbitMQ接続管理のエイリアス
実際の実装はqueue_manager.pyを使用
"""

# queue_managerをrabbit_managerとして公開
from libs.queue_manager import QueueManager as RabbitManager

__all__ = ['RabbitManager']