#!/usr/bin/env python3
"""
プロセス間ロック機能
ファイルベース、Redis、メモリベースのロックバックエンドをサポート
"""

import asyncio
import aiofiles
import os
import json
import time
import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class LockInfo:
    """ロック情報"""
    
    def __init__(self, key: str, pid: int, acquired_at: float, ttl: int, metadata: Optional[Dict[str, Any]] = None):
        self.key = key
        self.pid = pid
        self.acquired_at = acquired_at
        self.ttl = ttl
        self.metadata = metadata or {}
    
    @property
    def is_expired(self) -> bool:
        """ロックが期限切れかチェック"""
        return time.time() - self.acquired_at > self.ttl
    
    @property
    def remaining_ttl(self) -> float:
        """残りTTL（秒）"""
        remaining = self.ttl - (time.time() - self.acquired_at)
        return max(0, remaining)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "key": self.key,
            "pid": self.pid,
            "acquired_at": self.acquired_at,
            "ttl": self.ttl,
            "metadata": self.metadata,
            "acquired_at_iso": datetime.fromtimestamp(self.acquired_at).isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LockInfo":
        """辞書から作成"""
        return cls(
            key=data["key"],
            pid=data["pid"],
            acquired_at=data["acquired_at"],
            ttl=data["ttl"],
            metadata=data.get("metadata", {})
        )


class LockBackend(ABC):
    """ロックバックエンドの抽象基底クラス"""
    
    @abstractmethod
    async def acquire(self, key: str, ttl: int, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """ロックを取得"""
        pass
    
    @abstractmethod
    async def release(self, key: str) -> bool:
        """ロックを解放"""
        pass
    
    @abstractmethod
    async def is_locked(self, key: str) -> bool:
        """ロック状態を確認"""
        pass
    
    @abstractmethod
    async def get_lock_info(self, key: str) -> Optional[LockInfo]:
        """ロック情報を取得"""
        pass
    
    @abstractmethod
    async def cleanup_expired(self) -> int:
        """期限切れロックをクリーンアップ"""
        pass


class FileLockBackend(LockBackend):
    """ファイルベースのロックバックエンド"""
    
    def __init__(self, lock_dir: str = "./.issue_locks"):
        self.lock_dir = Path(lock_dir)
        self.lock_dir.mkdir(exist_ok=True)
        logger.info(f"FileLockBackend initialized with directory: {self.lock_dir}")
    
    def _get_lock_file(self, key: str) -> Path:
        """ロックファイルのパスを取得"""
        # キーをファイル名として安全にする
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.lock_dir / f"{safe_key}.lock"
    
    async def acquire(self, key: str, ttl: int, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """ロックを取得"""
        lock_file = self._get_lock_file(key)
        
        # 既存ロックの確認
        if await self.is_locked(key):
            logger.debug(f"Lock already exists for key: {key}")
            return False
        
        # ロック情報作成
        lock_info = LockInfo(
            key=key,
            pid=os.getpid(),
            acquired_at=time.time(),
            ttl=ttl,
            metadata=metadata or {}
        )
        
        try:
            # アトミックな書き込み
            temp_file = lock_file.with_suffix(".tmp")
            async with aiofiles.open(temp_file, 'w') as f:
                await f.write(json.dumps(lock_info.to_dict(), indent=2))
            
            # アトミックなリネーム
            temp_file.rename(lock_file)
            
            logger.info(f"Lock acquired for key: {key} (PID: {os.getpid()}, TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to acquire lock for key {key}: {e}")
            if temp_file.exists():
                temp_file.unlink()
            return False
    
    async def release(self, key: str) -> bool:
        """ロックを解放"""
        lock_file = self._get_lock_file(key)
        
        try:
            # ロック情報を確認
            lock_info = await self.get_lock_info(key)
            if lock_info and lock_info.pid != os.getpid():
                logger.warning(f"Cannot release lock for key {key}: owned by different process (PID: {lock_info.pid})")
                return False
            
            # ファイル削除
            if lock_file.exists():
                lock_file.unlink()
                logger.info(f"Lock released for key: {key}")
                return True
            else:
                logger.warning(f"No lock file found for key: {key}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to release lock for key {key}: {e}")
            return False
    
    async def is_locked(self, key: str) -> bool:
        """ロック状態を確認"""
        lock_info = await self.get_lock_info(key)
        
        if not lock_info:
            return False
        
        # 期限切れチェック
        if lock_info.is_expired:
            logger.debug(f"Lock for key {key} has expired, removing")
            await self.release(key)
            return False
        
        return True
    
    async def get_lock_info(self, key: str) -> Optional[LockInfo]:
        """ロック情報を取得"""
        lock_file = self._get_lock_file(key)
        
        if not lock_file.exists():
            return None
        
        try:
            async with aiofiles.open(lock_file, 'r') as f:
                data = json.loads(await f.read())
            return LockInfo.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to read lock file for key {key}: {e}")
            return None
    
    async def cleanup_expired(self) -> int:
        """期限切れロックをクリーンアップ"""
        cleaned = 0
        
        for lock_file in self.lock_dir.glob("*.lock"):
            try:
                async with aiofiles.open(lock_file, 'r') as f:
                    data = json.loads(await f.read())
                
                lock_info = LockInfo.from_dict(data)
                
                if lock_info.is_expired:
                    lock_file.unlink()
                    cleaned += 1
                    logger.info(f"Cleaned up expired lock: {lock_info.key}")
                    
            except Exception as e:
                logger.error(f"Error cleaning up lock file {lock_file}: {e}")
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} expired locks")
        
        return cleaned


class MemoryLockBackend(LockBackend):
    """メモリベースのロックバックエンド（単一プロセス用）"""
    
    def __init__(self):
        self._locks: Dict[str, LockInfo] = {}
        self._lock = asyncio.Lock()
        logger.info("MemoryLockBackend initialized")
    
    async def acquire(self, key: str, ttl: int, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """ロックを取得"""
        async with self._lock:
            if await self.is_locked(key):
                return False
            
            lock_info = LockInfo(
                key=key,
                pid=os.getpid(),
                acquired_at=time.time(),
                ttl=ttl,
                metadata=metadata or {}
            )
            
            self._locks[key] = lock_info
            logger.info(f"Lock acquired for key: {key} (TTL: {ttl}s)")
            return True
    
    async def release(self, key: str) -> bool:
        """ロックを解放"""
        async with self._lock:
            if key in self._locks:
                del self._locks[key]
                logger.info(f"Lock released for key: {key}")
                return True
            return False
    
    async def is_locked(self, key: str) -> bool:
        """ロック状態を確認"""
        async with self._lock:
            lock_info = self._locks.get(key)
            
            if not lock_info:
                return False
            
            if lock_info.is_expired:
                del self._locks[key]
                return False
            
            return True
    
    async def get_lock_info(self, key: str) -> Optional[LockInfo]:
        """ロック情報を取得"""
        async with self._lock:
            return self._locks.get(key)
    
    async def cleanup_expired(self) -> int:
        """期限切れロックをクリーンアップ"""
        async with self._lock:
            expired_keys = [
                key for key, lock_info in self._locks.items()
                if lock_info.is_expired
            ]
            
            for key in expired_keys:
                del self._locks[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired locks")
            
            return len(expired_keys)


class ProcessLock:
    """プロセスロック管理クラス"""
    
    def __init__(self, backend: str = "file", **kwargs):
        """
        初期化
        
        Args:
            backend: ロックバックエンドの種類 (file, memory, redis)
            **kwargs: バックエンド固有の設定
        """
        if backend == "file":
            self.backend = FileLockBackend(kwargs.get("lock_dir", "./.issue_locks"))
        elif backend == "memory":
            self.backend = MemoryLockBackend()
        elif backend == "redis":
            raise NotImplementedError("Redis backend is not implemented yet")
        else:
            raise ValueError(f"Unknown lock backend: {backend}")
        
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def acquire(self, key: str, ttl: int = 300, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        ロックを取得
        
        Args:
            key: ロックキー
            ttl: Time To Live（秒）
            metadata: 追加メタデータ
            
        Returns:
            ロック取得成功の場合True
        """
        return await self.backend.acquire(key, ttl, metadata)
    
    async def release(self, key: str) -> bool:
        """
        ロックを解放
        
        Args:
            key: ロックキー
            
        Returns:
            ロック解放成功の場合True
        """
        return await self.backend.release(key)
    
    async def is_locked(self, key: str) -> bool:
        """
        ロック状態を確認
        
        Args:
            key: ロックキー
            
        Returns:
            ロックされている場合True
        """
        return await self.backend.is_locked(key)
    
    async def get_lock_info(self, key: str) -> Optional[LockInfo]:
        """
        ロック情報を取得
        
        Args:
            key: ロックキー
            
        Returns:
            ロック情報（存在しない場合None）
        """
        return await self.backend.get_lock_info(key)
    
    async def cleanup_expired(self) -> int:
        """
        期限切れロックをクリーンアップ
        
        Returns:
            クリーンアップしたロック数
        """
        return await self.backend.cleanup_expired()
    
    async def start_cleanup_task(self, interval: int = 60):
        """
        定期的なクリーンアップタスクを開始
        
        Args:
            interval: クリーンアップ間隔（秒）
        """
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(interval)
                    await self.cleanup_expired()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info(f"Started cleanup task with {interval}s interval")
    
    async def stop_cleanup_task(self):
        """クリーンアップタスクを停止"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Stopped cleanup task")
    
    @asynccontextmanager
    async def lock_context(self, key: str, ttl: int = 300, metadata: Optional[Dict[str, Any]] = None):
        """
        コンテキストマネージャーとしてロックを使用
        
        Usage:
            async with lock.lock_context("issue_123"):
                # ロックされた処理
                pass
        """
        acquired = await self.acquire(key, ttl, metadata)
        if not acquired:
            raise RuntimeError(f"Failed to acquire lock for key: {key}")
        
        try:
            yield
        finally:
            await self.release(key)


async def main():
    """テスト用メイン関数"""
    # ファイルベースロックのテスト
    lock = ProcessLock("file", lock_dir="./test_locks")
    
    # ロック取得
    success = await lock.acquire("test_issue_123", ttl=10, metadata={"user": "test"})
    print(f"Lock acquired: {success}")
    
    # ロック情報確認
    info = await lock.get_lock_info("test_issue_123")
    if info:
        print(f"Lock info: {info.to_dict()}")
    
    # ロック状態確認
    is_locked = await lock.is_locked("test_issue_123")
    print(f"Is locked: {is_locked}")
    
    # ロック解放
    released = await lock.release("test_issue_123")
    print(f"Lock released: {released}")
    
    # コンテキストマネージャーのテスト
    try:
        async with lock.lock_context("test_issue_456", ttl=5):
            print("Inside lock context")
            await asyncio.sleep(1)
    except RuntimeError as e:
        print(f"Lock error: {e}")


if __name__ == "__main__":
    asyncio.run(main())