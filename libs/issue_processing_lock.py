#!/usr/bin/env python3
"""
Issue処理ロック管理システム
重複処理防止とファイル上書き防止のためのロック機能
"""

import os
import time
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class IssueLock:
    """Issue処理ロック情報"""
    issue_number: int
    locked_at: float
    process_id: int
    operation: str
    estimated_duration: int  # 秒
    
    @property
    def is_expired(self) -> bool:
        """ロックが期限切れかどうか"""
        max_duration = max(self.estimated_duration, 300)  # 最低5分
        return time.time() - self.locked_at > max_duration
    
    @property
    def age_seconds(self) -> int:
        """ロック経過時間（秒）"""
        return int(time.time() - self.locked_at)


class IssueProcessingLockManager:
    """Issue処理ロック管理"""
    
    def __init__(self, lock_dir: Optional[str] = None):
        """
        初期化
        
        Args:
            lock_dir: ロックファイル保存ディレクトリ
        """
        if lock_dir is None:
            lock_dir = Path(__file__).parent.parent / ".issue_processing_locks"
        
        self.lock_dir = Path(lock_dir)
        self.lock_dir.mkdir(exist_ok=True)
        
        # アクティブなロック情報（メモリ内）
        self.active_locks: Dict[int, IssueLock] = {}
        
        # 処理間隔制限
        self.min_processing_interval = 300  # 5分間隔
        self.processing_history: Dict[int, float] = {}
        
        # 起動時にロック状態を復元
        self._restore_locks()
        
        logger.info(f"IssueProcessingLockManager initialized: {self.lock_dir}")
    
    def _restore_locks(self):
        """起動時にロック状態を復元"""
        try:
            for lock_file in self.lock_dir.glob("issue_*.lock"):
                try:
                    with open(lock_file, 'r') as f:
                        lock_data = json.load(f)
                    
                    lock = IssueLock(
                        issue_number=lock_data['issue_number'],
                        locked_at=lock_data['locked_at'],
                        process_id=lock_data['process_id'],
                        operation=lock_data['operation'],
                        estimated_duration=lock_data.get('estimated_duration', 300)
                    )
                    
                    # 期限切れでない場合のみ復元
                    if not lock.is_expired:
                        self.active_locks[lock.issue_number] = lock
                        logger.info(f"Restored lock for issue #{lock.issue_number}")
                    else:
                        # 期限切れロックファイルを削除
                        lock_file.unlink()
                        logger.info(f"Removed expired lock file: {lock_file}")
                        
                except Exception as e:
                    logger.warning(f"Failed to restore lock from {lock_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Error restoring locks: {e}")
    
    def acquire_lock(self, 
                    issue_number: int, 
                    operation: str = "processing", 
                    estimated_duration: int = 300) -> bool:
        """
        Issue処理ロックを取得
        
        Args:
            issue_number: Issue番号
            operation: 実行する操作
            estimated_duration: 推定実行時間（秒）
            
        Returns:
            ロック取得成功かどうか
        """
        try:
            # 既存ロックのチェック
            if issue_number in self.active_locks:
                existing_lock = self.active_locks[issue_number]
                
                # 期限切れチェック
                if existing_lock.is_expired:
                    logger.info(f"Expired lock found for issue #{issue_number}, removing")
                    self.release_lock(issue_number)
                else:
                    logger.warning(f"Issue #{issue_number} is already locked by PID {existing_lock.process_id}")
                    return False
            
            # 処理間隔チェック
            if not self._can_process_now(issue_number):
                logger.warning(f"Issue #{issue_number} processed too recently")
                return False
            
            # 新しいロックを作成
            lock = IssueLock(
                issue_number=issue_number,
                locked_at=time.time(),
                process_id=os.getpid(),
                operation=operation,
                estimated_duration=estimated_duration
            )
            
            # メモリとファイルにロック情報を保存
            self.active_locks[issue_number] = lock
            self._save_lock_file(lock)
            
            logger.info(f"Lock acquired for issue #{issue_number} (PID: {os.getpid()}, operation: {operation})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to acquire lock for issue #{issue_number}: {e}")
            return False
    
    def release_lock(self, issue_number: int) -> bool:
        """
        Issue処理ロックを解放
        
        Args:
            issue_number: Issue番号
            
        Returns:
            ロック解放成功かどうか
        """
        try:
            if issue_number not in self.active_locks:
                logger.warning(f"No active lock found for issue #{issue_number}")
                return False
            
            lock = self.active_locks[issue_number]
            
            # 自分のプロセスのロックかチェック
            if lock.process_id != os.getpid():
                logger.warning(f"Cannot release lock for issue #{issue_number}: different process (expected: {lock.process_id}, current: {os.getpid()})")
                return False
            
            # ロック情報を削除
            del self.active_locks[issue_number]
            
            # ロックファイルを削除
            lock_file = self.lock_dir / f"issue_{issue_number}.lock"
            if lock_file.exists():
                lock_file.unlink()
            
            # 処理履歴を更新
            self.processing_history[issue_number] = time.time()
            
            logger.info(f"Lock released for issue #{issue_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to release lock for issue #{issue_number}: {e}")
            return False
    
    def is_locked(self, issue_number: int) -> bool:
        """
        Issueがロックされているかチェック
        
        Args:
            issue_number: Issue番号
            
        Returns:
            ロック状態
        """
        if issue_number not in self.active_locks:
            return False
        
        lock = self.active_locks[issue_number]
        
        # 期限切れチェック
        if lock.is_expired:
            logger.info(f"Lock for issue #{issue_number} has expired, removing")
            self.release_lock(issue_number)
            return False
        
        return True
    
    def get_lock_info(self, issue_number: int) -> Optional[IssueLock]:
        """
        ロック情報を取得
        
        Args:
            issue_number: Issue番号
            
        Returns:
            ロック情報（存在しない場合はNone）
        """
        return self.active_locks.get(issue_number)
    
    def get_all_active_locks(self) -> Dict[int, IssueLock]:
        """全てのアクティブなロック情報を取得"""
        # 期限切れロックをクリーンアップ
        expired_issues = []
        for issue_number, lock in self.active_locks.items():
            if lock.is_expired:
                expired_issues.append(issue_number)
        
        for issue_number in expired_issues:
            self.release_lock(issue_number)
        
        return self.active_locks.copy()
    
    def force_release_lock(self, issue_number: int, reason: str = "forced") -> bool:
        """
        強制的にロックを解放（管理用）
        
        Args:
            issue_number: Issue番号
            reason: 強制解放の理由
            
        Returns:
            解放成功かどうか
        """
        try:
            if issue_number in self.active_locks:
                lock = self.active_locks[issue_number]
                logger.warning(f"Force releasing lock for issue #{issue_number} (reason: {reason}, was held by PID: {lock.process_id})")
                
                del self.active_locks[issue_number]
                
                lock_file = self.lock_dir / f"issue_{issue_number}.lock"
                if lock_file.exists():
                    lock_file.unlink()
                
                return True
            else:
                logger.warning(f"No active lock found for issue #{issue_number} to force release")
                return False
                
        except Exception as e:
            logger.error(f"Failed to force release lock for issue #{issue_number}: {e}")
            return False
    
    def _can_process_now(self, issue_number: int) -> bool:
        """処理間隔制限をチェック"""
        if issue_number not in self.processing_history:
            return True
        
        last_processed = self.processing_history[issue_number]
        elapsed = time.time() - last_processed
        
        return elapsed >= self.min_processing_interval
    
    def _save_lock_file(self, lock: IssueLock):
        """ロック情報をファイルに保存"""
        lock_file = self.lock_dir / f"issue_{lock.issue_number}.lock"
        
        lock_data = {
            'issue_number': lock.issue_number,
            'locked_at': lock.locked_at,
            'process_id': lock.process_id,
            'operation': lock.operation,
            'estimated_duration': lock.estimated_duration,
            'created_at': datetime.now().isoformat()
        }
        
        with open(lock_file, 'w') as f:
            json.dump(lock_data, f, indent=2)
    
    def cleanup_expired_locks(self) -> int:
        """期限切れロックをクリーンアップ"""
        cleaned = 0
        expired_issues = []
        
        for issue_number, lock in self.active_locks.items():
            if lock.is_expired:
                expired_issues.append(issue_number)
        
        for issue_number in expired_issues:
            if self.release_lock(issue_number):
                cleaned += 1
        
        logger.info(f"Cleaned up {cleaned} expired locks")
        return cleaned
    
    def get_status_report(self) -> Dict[str, any]:
        """ロック管理の状態レポート"""
        active_locks = self.get_all_active_locks()
        
        return {
            "active_locks_count": len(active_locks),
            "active_locks": {
                issue_num: {
                    "operation": lock.operation,
                    "process_id": lock.process_id,
                    "age_seconds": lock.age_seconds,
                    "estimated_duration": lock.estimated_duration
                }
                for issue_num, lock in active_locks.items()
            },
            "processing_history_count": len(self.processing_history),
            "min_processing_interval": self.min_processing_interval,
            "lock_dir": str(self.lock_dir)
        }


# グローバルインスタンス
_global_lock_manager = None


def get_global_lock_manager() -> IssueProcessingLockManager:
    """グローバルなロック管理インスタンスを取得"""
    global _global_lock_manager
    if _global_lock_manager is None:
        _global_lock_manager = IssueProcessingLockManager()
    return _global_lock_manager


def with_issue_lock(issue_number: int, operation: str = "processing", estimated_duration: int = 300):
    """
    Issue処理ロックデコレータ
    
    Usage:
        @with_issue_lock(189, "code_generation", 600)
        def process_issue_189():
            # 処理内容
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            lock_manager = get_global_lock_manager()
            
            if not lock_manager.acquire_lock(issue_number, operation, estimated_duration):
                raise Exception(f"Failed to acquire lock for issue #{issue_number}")
            
            try:
                return func(*args, **kwargs)
            finally:
                lock_manager.release_lock(issue_number)
        
        return wrapper
    return decorator


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    lock_manager = IssueProcessingLockManager()
    
    # テスト用のロック取得・解放
    print("Testing lock acquisition...")
    success = lock_manager.acquire_lock(999, "test", 60)
    print(f"Lock acquired: {success}")
    
    print("\nCurrent status:")
    status = lock_manager.get_status_report()
    print(json.dumps(status, indent=2))
    
    print("\nReleasing lock...")
    released = lock_manager.release_lock(999)
    print(f"Lock released: {released}")