# Auto Issue Processor カオス問題 - 根本的解決アーキテクチャ

**作成日**: 2025-07-22  
**作成者**: クロードエルダー（Claude Elder）  
**文書種別**: 技術設計書

## 🎯 解決方針

### 基本原則

1. **Single Source of Truth**: 1つの統合実装のみを維持
2. **Explicit over Implicit**: 明示的な設定と動作
3. **Fail Safe**: エラー時は安全側に倒れる
4. **Observable**: すべての動作が監視可能

## 🏗️ 新アーキテクチャ設計

### 1. 統合実装の構造

```
libs/auto_issue_processor/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── processor.py          # メインプロセッサ
│   ├── config.py            # 設定管理
│   └── exceptions.py        # 例外定義
├── features/
│   ├── __init__.py
│   ├── error_handling.py    # エラーハンドリング機能
│   ├── pr_creation.py       # PR作成機能
│   ├── parallel_processing.py # 並列処理機能
│   └── github_integration.py  # GitHub統合
├── utils/
│   ├── __init__.py
│   ├── locking.py           # プロセスロック
│   ├── logging.py           # ロギング
│   └── metrics.py           # メトリクス収集
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

### 2. コア実装

```python
# libs/auto_issue_processor/core/processor.py

from typing import Optional, List, Dict, Any
import asyncio
from ..utils.locking import ProcessLock
from ..features import ErrorHandler, PRCreator, ParallelProcessor
from .config import ProcessorConfig

class UnifiedAutoIssueProcessor:
    """統合されたAuto Issue Processor
    
    すべての機能を統合し、設定により動作を制御する単一の実装。
    """
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        self.config = config or ProcessorConfig.from_env()
        self.lock_manager = ProcessLock(self.config.lock_backend)
        self.error_handler = ErrorHandler(self.config.error_handling)
        self.pr_creator = PRCreator(self.config.pr_creation) if self.config.features.pr_creation else None
        self.parallel_processor = ParallelProcessor(self.config.parallel) if self.config.features.parallel else None
        
    async def process_issue(self, issue_number: int) -> Dict[str, Any]:
        """単一のIssueを処理"""
        
        # プロセスロックの取得
        lock_acquired = await self.lock_manager.acquire(
            f"issue_{issue_number}",
            ttl=self.config.processing_timeout
        )
        
        if not lock_acquired:
            return {
                "success": False,
                "error": "Issue is already being processed",
                "issue_number": issue_number
            }
        
        try:
            # エラーハンドリングでラップ
            async with self.error_handler.context(issue_number):
                result = await self._process_issue_impl(issue_number)
                
                # PR作成が有効な場合
                if self.pr_creator and result.get("success"):
                    pr_result = await self.pr_creator.create_pr(result)
                    result["pr"] = pr_result
                
                return result
                
        finally:
            await self.lock_manager.release(f"issue_{issue_number}")
    
    async def process_issues_batch(self, issue_numbers: List[int]) -> List[Dict[str, Any]]:
        """複数のIssueをバッチ処理"""
        
        if self.parallel_processor:
            return await self.parallel_processor.process_batch(
                issue_numbers,
                self.process_issue
            )
        else:
            # 順次処理
            results = []
            for issue_number in issue_numbers:
                result = await self.process_issue(issue_number)
                results.append(result)
            return results
```

### 3. 設定管理

```python
# libs/auto_issue_processor/core/config.py

from dataclasses import dataclass
from typing import Optional
import yaml
import os

@dataclass
class FeatureFlags:
    """機能フラグ"""
    pr_creation: bool = True
    error_recovery: bool = True
    parallel_processing: bool = False
    smart_merge: bool = False
    four_sages_integration: bool = True

@dataclass
class ProcessorConfig:
    """プロセッサ設定"""
    
    # 基本設定
    enabled: bool = True
    interval_minutes: int = 10
    max_issues_per_run: int = 5
    processing_timeout: int = 300  # 秒
    
    # 機能フラグ
    features: FeatureFlags = None
    
    # ロック設定
    lock_backend: str = "file"  # file, redis, memory
    lock_dir: str = "./.issue_locks"
    
    # GitHub設定
    github_token: Optional[str] = None
    github_repo: Optional[str] = None
    rate_limit_buffer: int = 100
    
    # ログ設定
    log_level: str = "INFO"
    log_file: str = "logs/auto_issue_processor.log"
    
    @classmethod
    def from_file(cls, path: str) -> "ProcessorConfig":
        """YAMLファイルから設定を読み込む"""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    @classmethod
    def from_env(cls) -> "ProcessorConfig":
        """環境変数から設定を読み込む"""
        config = cls()
        
        # 環境変数のオーバーライド
        if os.getenv("AUTO_ISSUE_PROCESSOR_ENABLED"):
            config.enabled = os.getenv("AUTO_ISSUE_PROCESSOR_ENABLED").lower() == "true"
        
        if os.getenv("GITHUB_TOKEN"):
            config.github_token = os.getenv("GITHUB_TOKEN")
            
        return config
```

### 4. プロセスロック実装

```python
# libs/auto_issue_processor/utils/locking.py

import asyncio
import aiofiles
import os
import json
import time
from typing import Optional
from abc import ABC, abstractmethod

class LockBackend(ABC):
    """ロックバックエンドの抽象基底クラス"""
    
    @abstractmethod
    async def acquire(self, key: str, ttl: int) -> bool:
        pass
    
    @abstractmethod
    async def release(self, key: str) -> bool:
        pass
    
    @abstractmethod
    async def is_locked(self, key: str) -> bool:
        pass

class FileLockBackend(LockBackend):
    """ファイルベースのロックバックエンド"""
    
    def __init__(self, lock_dir: str = "./.issue_locks"):
        self.lock_dir = lock_dir
        os.makedirs(lock_dir, exist_ok=True)
    
    async def acquire(self, key: str, ttl: int) -> bool:
        lock_file = os.path.join(self.lock_dir, f"{key}.lock")
        
        # 既存ロックの確認
        if await self.is_locked(key):
            return False
        
        # ロックファイル作成
        lock_data = {
            "key": key,
            "pid": os.getpid(),
            "acquired_at": time.time(),
            "ttl": ttl
        }
        
        try:
            async with aiofiles.open(lock_file, 'w') as f:
                await f.write(json.dumps(lock_data))
            return True
        except:
            return False
    
    async def release(self, key: str) -> bool:
        lock_file = os.path.join(self.lock_dir, f"{key}.lock")
        try:
            os.remove(lock_file)
            return True
        except:
            return False
    
    async def is_locked(self, key: str) -> bool:
        lock_file = os.path.join(self.lock_dir, f"{key}.lock")
        
        if not os.path.exists(lock_file):
            return False
        
        try:
            async with aiofiles.open(lock_file, 'r') as f:
                data = json.loads(await f.read())
            
            # TTLチェック
            elapsed = time.time() - data["acquired_at"]
            if elapsed > data["ttl"]:
                # 期限切れロックを削除
                await self.release(key)
                return False
            
            return True
        except:
            return False

class ProcessLock:
    """プロセスロック管理"""
    
    def __init__(self, backend: str = "file", **kwargs):
        if backend == "file":
            self.backend = FileLockBackend(**kwargs)
        else:
            raise ValueError(f"Unknown lock backend: {backend}")
    
    async def acquire(self, key: str, ttl: int = 300) -> bool:
        return await self.backend.acquire(key, ttl)
    
    async def release(self, key: str) -> bool:
        return await self.backend.release(key)
    
    async def is_locked(self, key: str) -> bool:
        return await self.backend.is_locked(key)
```

### 5. スケジューラー統合

```python
# libs/auto_issue_processor/scheduler.py

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .core.processor import UnifiedAutoIssueProcessor
from .core.config import ProcessorConfig
import logging

logger = logging.getLogger(__name__)

class AutoIssueProcessorScheduler:
    """Auto Issue Processorのスケジューラー"""
    
    def __init__(self, config: ProcessorConfig):
        self.config = config
        self.processor = UnifiedAutoIssueProcessor(config)
        self.scheduler = AsyncIOScheduler()
        self._job = None
    
    async def process_batch(self):
        """定期実行される処理"""
        if not self.config.enabled:
            logger.info("Auto Issue Processor is disabled")
            return
        
        logger.info("Starting scheduled Auto Issue Processor run")
        
        try:
            # 処理対象のIssueを取得
            issues = await self._get_processable_issues()
            
            if not issues:
                logger.info("No processable issues found")
                return
            
            # バッチ処理
            results = await self.processor.process_issues_batch(
                issues[:self.config.max_issues_per_run]
            )
            
            # 結果のログ
            success_count = sum(1 for r in results if r.get("success"))
            logger.info(f"Processed {len(results)} issues, {success_count} successful")
            
        except Exception as e:
            logger.error(f"Error in scheduled processing: {e}", exc_info=True)
    
    def start(self):
        """スケジューラーを開始"""
        if self._job:
            logger.warning("Scheduler already started")
            return
        
        trigger = IntervalTrigger(minutes=self.config.interval_minutes)
        self._job = self.scheduler.add_job(
            self.process_batch,
            trigger=trigger,
            id="auto_issue_processor",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(f"Scheduler started with {self.config.interval_minutes} minute interval")
    
    def stop(self):
        """スケジューラーを停止"""
        if self._job:
            self._job.remove()
            self._job = None
        
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
```

## 🔧 実装手順

### Phase 1: 基盤構築（Day 1-2）

1. **ディレクトリ構造の作成**
   ```bash
   mkdir -p libs/auto_issue_processor/{core,features,utils,tests}
   ```

2. **既存実装の分析とマッピング**
   - 各実装の機能を抽出
   - 共通部分と独自部分の識別

3. **コア実装の作成**
   - `processor.py`の基本実装
   - `config.py`の設定管理

### Phase 2: 機能移植（Day 3-5）

1. **エラーハンドリング機能**
   - `auto_issue_processor_enhanced.py`から移植

2. **PR作成機能**
   - `enhanced_auto_issue_processor.py`から移植

3. **並列処理機能**
   - `optimized_auto_issue_processor.py`から移植

### Phase 3: 統合とテスト（Day 6-7）

1. **統合テスト作成**
2. **既存システムとの互換性確認**
3. **パフォーマンステスト**

### Phase 4: 移行（Day 8-10）

1. **既存実装の無効化**
2. **新実装への切り替え**
3. **監視とフォローアップ**

## 📊 成功指標

1. **機能的成功**
   - [ ] ファイル上書き問題の解決
   - [ ] 重複処理の防止
   - [ ] すべての既存機能の維持

2. **非機能的成功**
   - [ ] 処理時間の改善（20%以上）
   - [ ] エラー率の低下（50%以上）
   - [ ] リソース使用量の最適化

3. **運用的成功**
   - [ ] 統一されたログ出力
   - [ ] 包括的なモニタリング
   - [ ] 明確なドキュメント

## 🚀 将来の拡張性

1. **プラガブルアーキテクチャ**
   - 新機能の追加が容易
   - 既存機能への影響最小化

2. **スケーラビリティ**
   - 水平スケーリング対応
   - 分散ロック対応

3. **可観測性**
   - OpenTelemetry統合
   - 詳細なメトリクス

---

**この設計により、Auto Issue Processorシステムの混乱を根本的に解決し、持続可能な開発基盤を確立します。**