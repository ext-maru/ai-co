#!/usr/bin/env python3
"""
🔒 Issue Lock Manager
Auto Issue Processor並列実行時の重複処理防止システム

ファイルベースの分散ロック機構により、複数のプロセッサが同じIssueを
同時に処理することを防止します。
"""

import asyncio
import os
import time
import json
import hmac
import hashlib
import logging
import psutil
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable, Awaitable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@dataclass
class LockInfo:
    """ロック情報"""
    issue_number: int
    processor_id: str
    acquired_at: datetime
    expires_at: datetime
    heartbeat_at: datetime
    process_pid: int
    hostname: str
    signature: str

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        data = asdict(self)
        # datetime を ISO format に変換
        for key in ['acquired_at', 'expires_at', 'heartbeat_at']:
            if isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LockInfo':
        """辞書から復元"""
        # ISO format から datetime に変換
        for key in ['acquired_at', 'expires_at', 'heartbeat_at']:
            if isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        return cls(**data)


class HeartbeatManager:
    """ハートビート管理"""
    
    def __init__(self, lock_manager:
        """初期化メソッド"""
    'FileLockManager'):
        self.lock_manager = lock_manager
        self.heartbeat_tasks: Dict[int, asyncio.Task] = {}
        self._shutdown = False
    
    async def start_heartbeat(self, issue_number: int, interval: float = 30.0) -> None:
        """ハートビート開始"""
        if issue_number in self.heartbeat_tasks:
            return
        
        async def heartbeat_loop():
            """heartbeat_loopメソッド"""
            while not self._shutdown:
                try:
                    await self.lock_manager.update_heartbeat(issue_number)
                    await asyncio.sleep(interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Heartbeat error for issue {issue_number}: {e}")
                    await asyncio.sleep(interval)
        
        self.heartbeat_tasks[issue_number] = asyncio.create_task(heartbeat_loop())
        logger.debug(f"Heartbeat started for issue {issue_number}")
    
    async def stop_heartbeat(self, issue_number: int) -> None:
        """ハートビート停止"""
        if issue_number in self.heartbeat_tasks:
            task = self.heartbeat_tasks.pop(issue_number)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            logger.debug(f"Heartbeat stopped for issue {issue_number}")
    
    async def shutdown(self) -> None:
        """全ハートビート停止"""
        self._shutdown = True
        tasks = list(self.heartbeat_tasks.values())
        self.heartbeat_tasks.clear()
        
        if tasks:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)


class ProcessMonitor:
    """プロセス監視"""
    
    @staticmethod
    def is_process_alive(pid: int) -> bool:
        """プロセスが生きているかチェック"""
        try:
            return psutil.pid_exists(pid)
        except Exception:
            return False
    
    @staticmethod
    def get_current_process_info() -> Dict[str, Any]:
        """現在のプロセス情報取得"""
        try:
            process = psutil.Process()
            return {
                "pid": process.pid,
                "create_time": process.create_time(),
                "memory_percent": process.memory_percent(),
                "cpu_percent": process.cpu_percent()
            }
        except Exception as e:
            logger.warning(f"Failed to get process info: {e}")
            return {"pid": os.getpid(), "create_time": time.time()}


class FileLockManager:
    """ファイルベース分散ロックマネージャー"""
    
    def __init__(self, lock_dir: Path, secret_key: str = None, lock_timeout: int = 300):
        """
        初期化
        
        Args:
            lock_dir: ロックファイル保存ディレクトリ
            secret_key: HMAC署名用の秘密鍵
            lock_timeout: ロックタイムアウト（秒）
        """
        self.lock_dir = Path(lock_dir)
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self.secret_key = secret_key or "default_secret_key"
        self.lock_timeout = lock_timeout
        self.heartbeat_manager = HeartbeatManager(self)
        
        # セキュリティ: ディレクトリ権限を制限
        try:
            os.chmod(self.lock_dir, 0o750)
        except Exception as e:
            logger.warning(f"Failed to set directory permissions: {e}")
        
        logger.info(f"FileLockManager initialized: {lock_dir}")
    
    def _generate_signature(self, data: str) -> str:
        """HMAC署名生成"""
        return hmac.new(
            self.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _verify_signature(self, data: str, signature: str) -> bool:
        """HMAC署名検証"""
        expected = self._generate_signature(data)
        return hmac.compare_digest(expected, signature)
    
    def _get_lock_file(self, issue_number: int) -> Path:
        """ロックファイルパス取得"""
        return self.lock_dir / f"issue_{issue_number}.lock"
    
    async def acquire_lock(self, issue_number: int, processor_id: str) -> bool:
        """ロック取得"""
        lock_file = self._get_lock_file(issue_number)
        
        # 既存のロックをチェック
        if await self._is_lock_active(lock_file):
            logger.debug(f"Lock already held for issue {issue_number}")
            return False
        
        # 新しいロック作成
        now = datetime.now()
        process_info = ProcessMonitor.get_current_process_info()
        
        lock_info = LockInfo(
            issue_number=issue_number,
            processor_id=processor_id,
            acquired_at=now,
            expires_at=now + timedelta(seconds=self.lock_timeout),
            heartbeat_at=now,
            process_pid=process_info["pid"],
            hostname=os.uname().nodename,
            signature=""
        )
        
        # 署名生成
        data_to_sign = f"{issue_number}:{processor_id}:{lock_info.acquired_at.isoformat()}"
        lock_info.signature = self._generate_signature(data_to_sign)
        
        # アトミックな書き込み
        try:
            temp_file = lock_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(lock_info.to_dict(), f, indent=2)
            
            # アトミックな rename
            os.rename(temp_file, lock_file)
            
            # ファイル権限設定
            os.chmod(lock_file, 0o640)
            
            # ハートビート開始
            await self.heartbeat_manager.start_heartbeat(issue_number)
            
            logger.info(f"Lock acquired for issue {issue_number} by {processor_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to acquire lock for issue {issue_number}: {e}")
            # クリーンアップ
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception:
                pass
            return False
    
    async def release_lock(self, issue_number: int, processor_id: str) -> bool:
        """ロック解放"""
        lock_file = self._get_lock_file(issue_number)
        
        try:
            if not lock_file.exists():
                logger.debug(f"No lock file exists for issue {issue_number}")
                return True
            
            # ロック情報読み取り
            with open(lock_file, 'r') as f:
                lock_data = json.load(f)
            
            lock_info = LockInfo.from_dict(lock_data)
            
            # 所有権確認
            if lock_info.processor_id != processor_id:
                logger.warning(f"Lock owned by different processor: {lock_info.processor_id} vs " \
                    "{processor_id}")
                return False
            
            # ハートビート停止
            await self.heartbeat_manager.stop_heartbeat(issue_number)
            
            # ロックファイル削除
            lock_file.unlink()
            
            logger.info(f"Lock released for issue {issue_number} by {processor_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to release lock for issue {issue_number}: {e}")
            return False
    
    async def update_heartbeat(self, issue_number: int) -> bool:
        """ハートビート更新"""
        lock_file = self._get_lock_file(issue_number)
        
        try:
            if not lock_file.exists():
                return False
            
            with open(lock_file, 'r') as f:
                lock_data = json.load(f)
            
            lock_info = LockInfo.from_dict(lock_data)
            lock_info.heartbeat_at = datetime.now()
            
            # アトミック更新
            temp_file = lock_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(lock_info.to_dict(), f, indent=2)
            
            os.rename(temp_file, lock_file)
            
            logger.debug(f"Heartbeat updated for issue {issue_number}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to update heartbeat for issue {issue_number}: {e}")
            return False
    
    async def _is_lock_active(self, lock_file: Path) -> bool:
        """ロックがアクティブかチェック"""
        if not lock_file.exists():
            return False
        
        try:
            with open(lock_file, 'r') as f:
                lock_data = json.load(f)
            
            lock_info = LockInfo.from_dict(lock_data)
            now = datetime.now()
            
            # タイムアウトチェック
            if now > lock_info.expires_at:
                logger.info(f"Lock expired for issue {lock_info.issue_number}")
                await self._cleanup_expired_lock(lock_file, lock_info)
                return False
            
            # プロセス生存チェック
            if not ProcessMonitor.is_process_alive(lock_info.process_pid):
                logger.info(f"Process {lock_info.process_pid} is dead, cleaning up lock")
                await self._cleanup_dead_lock(lock_file, lock_info)
                return False
            
            # ハートビートチェック（5分以上更新されていない場合）
            heartbeat_timeout = timedelta(minutes=5)
            if now - lock_info.heartbeat_at > heartbeat_timeout:
                logger.info(f"Heartbeat timeout for issue {lock_info.issue_number}")
                await self._cleanup_stale_lock(lock_file, lock_info)
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error checking lock status: {e}")
            return False
    
    async def _cleanup_expired_lock(self, lock_file: Path, lock_info: LockInfo) -> None:
        """期限切れロッククリーンアップ"""
        try:
            lock_file.unlink()
            logger.info(f"Cleaned up expired lock for issue {lock_info.issue_number}")
        except Exception as e:
            logger.error(f"Failed to cleanup expired lock: {e}")
    
    async def _cleanup_dead_lock(self, lock_file: Path, lock_info: LockInfo) -> None:
        """死んだプロセスのロッククリーンアップ"""
        try:
            lock_file.unlink()
            logger.info(f"Cleaned up dead process lock for issue {lock_info.issue_number}")
        except Exception as e:
            logger.error(f"Failed to cleanup dead process lock: {e}")
    
    async def _cleanup_stale_lock(self, lock_file: Path, lock_info: LockInfo) -> None:
        """古いハートビートのロッククリーンアップ"""
        try:
            lock_file.unlink()
            logger.info(f"Cleaned up stale lock for issue {lock_info.issue_number}")
        except Exception as e:
            logger.error(f"Failed to cleanup stale lock: {e}")
    
    async def list_active_locks(self) -> List[LockInfo]:
        """アクティブなロック一覧"""
        active_locks = []
        
        for lock_file in self.lock_dir.glob("issue_*.lock"):
            if await self._is_lock_active(lock_file):
                try:
                    with open(lock_file, 'r') as f:
                        lock_data = json.load(f)
                    active_locks.append(LockInfo.from_dict(lock_data))
                except Exception as e:
                    logger.error(f"Error reading lock file {lock_file}: {e}")
        
        return active_locks
    
    async def cleanup_all_expired_locks(self) -> int:
        """すべての期限切れロックをクリーンアップ"""
        cleaned_count = 0
        
        for lock_file in self.lock_dir.glob("issue_*.lock"):
            if not await self._is_lock_active(lock_file):
                cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} expired locks")
        return cleaned_count
    
    async def force_release_lock(self, issue_number: int) -> bool:
        """強制ロック解放（管理用）"""
        lock_file = self._get_lock_file(issue_number)
        
        try:
            if lock_file.exists():
                lock_file.unlink()
                await self.heartbeat_manager.stop_heartbeat(issue_number)
                logger.warning(f"Force released lock for issue {issue_number}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to force release lock for issue {issue_number}: {e}")
            return False
    
    async def shutdown(self) -> None:
        """シャットダウン"""
        await self.heartbeat_manager.shutdown()
        logger.info("FileLockManager shutdown complete")


class SafeIssueProcessor:
    """ロック機能付きセーフなIssueプロセッサ"""
    
    def __init__(self, lock_manager:
        """初期化メソッド"""
    FileLockManager, processor_id: str = None):
        self.lock_manager = lock_manager
        self.processor_id = processor_id or f"processor_{os.getpid()}_{int(time.time())}"
        logger.info(f"SafeIssueProcessor initialized: {self.processor_id}")
    
    @asynccontextmanager
    async def acquire_issue_lock(self, issue_number: int):
        """Issue処理用のロックコンテキスト"""
        lock_acquired = await self.lock_manager.acquire_lock(issue_number, self.processor_id)
        
        if not lock_acquired:
            raise RuntimeError(f"Failed to acquire lock for issue {issue_number}")
        
        try:
            yield
        finally:
            await self.lock_manager.release_lock(issue_number, self.processor_id)
    
    async def process_issue_safely(
        self,
        issue_number: int,
        process_func: Callable[..., Awaitable[Any]],
        *args,
        **kwargs
    ) -> Any:
        """安全なIssue処理"""
        try:
            async with self.acquire_issue_lock(issue_number):
                logger.info(f"Processing issue {issue_number} safely")
                result = await process_func(*args, **kwargs)
                logger.info(f"Completed processing issue {issue_number}")
                return result
        except RuntimeError as e:
            if "Failed to acquire lock" in str(e):
                logger.info(f"Issue {issue_number} is already being processed by another processor")
                return {"skipped": True, "reason": "Already being processed"}
            raise
        except Exception as e:
            logger.error(f"Error processing issue {issue_number}: {e}")
            raise
    
    async def shutdown(self) -> None:
        """シャットダウン"""
        await self.lock_manager.shutdown()
        logger.info(f"SafeIssueProcessor {self.processor_id} shutdown complete")


# 使用例とテスト用のヘルパー関数
if __name__ == "__main__":
    async def example_usage():
        """使用例"""
        # ロックマネージャー初期化
        lock_manager = FileLockManager(
            lock_dir=Path("/tmp/issue_locks"),
            secret_key="your_secret_key",
            lock_timeout=300
        )
        
        # セーフプロセッサ初期化
        processor = SafeIssueProcessor(lock_manager)
        
        # Issue処理関数の例
        async def process_issue_example(issue_data):
            """process_issue_example処理メソッド"""
            print(f"Processing: {issue_data}")
            await asyncio.sleep(2)  # 処理のシミュレーション
            return {"status": "completed"}
        
        # 安全なIssue処理
        try:
            result = await processor.process_issue_safely(
                123,
                process_issue_example,
                {"number": 123, "title": "Test issue"}
            )
            print(f"Result: {result}")
        finally:
            await processor.shutdown()
    
    # 例を実行
    asyncio.run(example_usage())