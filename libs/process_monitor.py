#!/usr/bin/env python3
"""
プロセス監視機能
メモリ使用量と実行中プロセス数を監視し、異常時に安全な終了を行う
"""

import logging
import os
import signal
import time
from pathlib import Path

import psutil

logger = logging.getLogger(__name__)


class ProcessMonitor:
    """プロセス監視クラス"""

    def __init__(self, max_processes=10, max_memory_mb=1024, check_interval=1):
        self.max_processes = max_processes
        self.max_memory_mb = max_memory_mb
        self.check_interval = check_interval
        self.process_names = ["ai-todo", "ai-rag-search", "python3"]

    def get_current_processes(self):
        """現在の関連プロセス数を取得"""
        count = 0
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = " ".join(proc.info["cmdline"] or [])
                if any(name in cmdline for name in self.process_names):
                    count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return count

    def get_memory_usage(self):
        """現在のメモリ使用量を取得（MB）"""
        try:
            memory = psutil.virtual_memory()
            return memory.used / (1024 * 1024)  # MB
        except:
            return 0

    def check_system_health(self):
        """システムの健全性をチェック"""
        process_count = self.get_current_processes()
        memory_usage = self.get_memory_usage()

        issues = []

        # プロセス数チェック
        if process_count > self.max_processes:
            issues.append(f"過剰なプロセス数: {process_count} > {self.max_processes}")

        # メモリ使用量チェック
        if memory_usage > self.max_memory_mb:
            issues.append(
                f"メモリ使用量過多: {memory_usage:.1f}MB > {self.max_memory_mb}MB"
            )

        return {
            "healthy": len(issues) == 0,
            "process_count": process_count,
            "memory_usage": memory_usage,
            "issues": issues,
        }

    def kill_related_processes(self):
        """関連プロセスを安全に終了"""
        killed = []
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = " ".join(proc.info["cmdline"] or [])
                if any(name in cmdline for name in self.process_names):
                    if proc.pid != os.getpid():  # 自分自身は除外
                        proc.terminate()
                        killed.append(proc.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # 強制終了の準備
        time.sleep(2)
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = " ".join(proc.info["cmdline"] or [])
                if any(name in cmdline for name in self.process_names):
                    if proc.pid != os.getpid():
                        proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return killed

    def safe_execute(self, func, *args, **kwargs):
        """安全な実行ラッパー"""
        try:
            # 実行前チェック
            health = self.check_system_health()
            if not health["healthy"]:
                logger.warning(f"システム異常検出: {health['issues']}")
                return None

            # 実行
            return func(*args, **kwargs)

        except Exception as e:
            logger.error(f"実行中エラー: {e}")
            # 異常時のクリーンアップ
            self.emergency_cleanup()
            return None

    def emergency_cleanup(self):
        """緊急時のクリーンアップ"""
        logger.warning("緊急クリーンアップ開始")
        try:
            killed = self.kill_related_processes()
            logger.info(f"終了したプロセス: {killed}")
        except Exception as e:
            logger.error(f"クリーンアップエラー: {e}")

    def monitor_and_protect(self, duration=30):
        """指定時間プロセスを監視し、異常時に保護"""
        start_time = time.time()

        while time.time() - start_time < duration:
            health = self.check_system_health()

            if not health["healthy"]:
                logger.warning(f"異常検出: {health['issues']}")
                self.emergency_cleanup()
                return False

            time.sleep(self.check_interval)

        return True


# 使用例
if __name__ == "__main__":
    monitor = ProcessMonitor(max_processes=5, max_memory_mb=512)

    # システムヘルス確認
    health = monitor.check_system_health()
    print(f"システム状態: {health}")

    # 監視開始
    success = monitor.monitor_and_protect(duration=10)
    print(f"監視結果: {'正常' if success else '異常検出'}")
