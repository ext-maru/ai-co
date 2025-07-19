#!/usr/bin/env python3
"""
PID Lock Manager for Elder Flow
================================

マルチプロセス環境でのElder Flow実行を制御するPIDベースのロック管理システム。
同一タスクの重複実行を防ぎ、プロセスの健全性を保証します。

Author: Claude Elder
Created: 2025-01-19
"""

import os
import psutil
import json
import time
import fcntl
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PIDLockManager:
    """Elder Flow用PIDロック管理システム"""
    
    def __init__(self, lock_dir: str = "/tmp/elder_flow_locks"):
        """
        PIDロック管理システムの初期化
        
        Args:
            lock_dir: ロックファイルを保存するディレクトリ
        """
        self.lock_dir = Path(lock_dir)
        self.lock_dir.mkdir(exist_ok=True, mode=0o755)
        self.current_pid = os.getpid()
        
    def _get_lock_file_path(self, task_id: str) -> Path:
        """タスクIDに対応するロックファイルパスを取得"""
        safe_task_id = task_id.replace("/", "_").replace(" ", "_")
        return self.lock_dir / f"elder_flow_{safe_task_id}.lock"
        
    def _is_process_alive(self, pid: int) -> bool:
        """指定されたPIDのプロセスが生きているかチェック"""
        try:
            process = psutil.Process(pid)
            # プロセスが存在し、ゾンビでないことを確認
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
            
    def acquire_lock(self, task_id: str, task_info: Dict[str, Any] = None) -> bool:
        """
        タスクのロックを取得
        
        Args:
            task_id: タスクの一意識別子
            task_info: タスクに関する追加情報
            
        Returns:
            bool: ロック取得成功時True、既に実行中の場合False
        """
        lock_file = self._get_lock_file_path(task_id)
        
        try:
            # ロックファイルが存在する場合
            if lock_file.exists():
                with open(lock_file, 'r') as f:
                    try:
                        lock_data = json.load(f)
                        locked_pid = lock_data.get('pid')
                        
                        # PIDが生きているかチェック
                        if locked_pid and self._is_process_alive(locked_pid):
                            logger.warning(
                                f"Task '{task_id}' is already running "
                                f"(PID: {locked_pid}, started: {lock_data.get('started_at')})"
                            )
                            return False
                        else:
                            # 古いロックファイルをクリーンアップ
                            logger.info(f"Cleaning up stale lock for task '{task_id}' (PID: {locked_pid})")
                            lock_file.unlink()
                    except json.JSONDecodeError:
                        # 破損したロックファイルを削除
                        logger.warning(f"Corrupted lock file for task '{task_id}', removing...")
                        lock_file.unlink()
            
            # 新しいロックファイルを作成
            lock_data = {
                'pid': self.current_pid,
                'task_id': task_id,
                'started_at': datetime.now().isoformat(),
                'task_info': task_info or {}
            }
            
            # アトミックな書き込みを保証
            with open(lock_file, 'w') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                json.dump(lock_data, f, indent=2)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                
            logger.info(f"Successfully acquired lock for task '{task_id}' (PID: {self.current_pid})")
            return True
            
        except IOError as e:
            logger.error(f"Failed to acquire lock for task '{task_id}': {e}")
            return False
            
    def release_lock(self, task_id: str) -> bool:
        """
        タスクのロックを解放
        
        Args:
            task_id: タスクの一意識別子
            
        Returns:
            bool: ロック解放成功時True
        """
        lock_file = self._get_lock_file_path(task_id)
        
        try:
            if lock_file.exists():
                with open(lock_file, 'r') as f:
                    lock_data = json.load(f)
                    
                # 自分のPIDのロックのみ解放
                if lock_data.get('pid') == self.current_pid:
                    lock_file.unlink()
                    logger.info(f"Released lock for task '{task_id}' (PID: {self.current_pid})")
                    return True
                else:
                    logger.warning(
                        f"Cannot release lock for task '{task_id}' - "
                        f"owned by different process (PID: {lock_data.get('pid')})"
                    )
                    return False
            else:
                logger.warning(f"No lock found for task '{task_id}'")
                return True
                
        except Exception as e:
            logger.error(f"Failed to release lock for task '{task_id}': {e}")
            return False
            
    def is_task_locked(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        タスクがロックされているかチェック
        
        Args:
            task_id: タスクの一意識別子
            
        Returns:
            ロック情報の辞書（ロックされている場合）、またはNone
        """
        lock_file = self._get_lock_file_path(task_id)
        
        if lock_file.exists():
            try:
                with open(lock_file, 'r') as f:
                    lock_data = json.load(f)
                    
                # PIDが生きているかチェック
                if self._is_process_alive(lock_data.get('pid')):
                    return lock_data
                else:
                    # 古いロックをクリーンアップ
                    lock_file.unlink()
                    return None
            except Exception:
                return None
        return None
        
    def cleanup_stale_locks(self) -> int:
        """
        すべての古いロックファイルをクリーンアップ
        
        Returns:
            クリーンアップされたロック数
        """
        cleaned = 0
        
        for lock_file in self.lock_dir.glob("elder_flow_*.lock"):
            try:
                with open(lock_file, 'r') as f:
                    lock_data = json.load(f)
                    
                if not self._is_process_alive(lock_data.get('pid')):
                    lock_file.unlink()
                    logger.info(f"Cleaned up stale lock: {lock_file.name}")
                    cleaned += 1
            except Exception as e:
                logger.error(f"Failed to clean up lock {lock_file}: {e}")
                
        return cleaned
        
    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        現在アクティブなタスクのリストを取得
        
        Returns:
            タスクID -> ロック情報のマッピング
        """
        active_tasks = {}
        
        for lock_file in self.lock_dir.glob("elder_flow_*.lock"):
            try:
                with open(lock_file, 'r') as f:
                    lock_data = json.load(f)
                    
                if self._is_process_alive(lock_data.get('pid')):
                    task_id = lock_data.get('task_id', lock_file.stem)
                    active_tasks[task_id] = lock_data
            except Exception:
                continue
                
        return active_tasks


class PIDLockContext:
    """コンテキストマネージャーとしてのPIDロック"""
    
    def __init__(self, lock_manager: PIDLockManager, task_id: str, task_info: Dict[str, Any] = None):
        self.lock_manager = lock_manager
        self.task_id = task_id
        self.task_info = task_info
        self.acquired = False
        
    def __enter__(self):
        self.acquired = self.lock_manager.acquire_lock(self.task_id, self.task_info)
        if not self.acquired:
            raise RuntimeError(f"Failed to acquire lock for task '{self.task_id}' - already running")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.acquired:
            self.lock_manager.release_lock(self.task_id)