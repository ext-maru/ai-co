#!/usr/bin/env python3
"""
エラーリカバリー機能
処理中のエラーから自動的に回復を試みる
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import traceback
import json
from pathlib import Path

from github.Issue import Issue

from ..core.config import ProcessorConfig

logger = logging.getLogger(__name__)


class RecoveryStrategy:
    """リカバリー戦略の基底クラス"""
    
    def __init__(self, name: str, priority: int = 0):
        self.name = name
        self.priority = priority
    
    async def can_handle(self, error: Exception, context: Dict[str, Any]) -> bool:
        """このエラーを処理できるか判定"""
        return False
    
    async def recover(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """リカバリーを実行"""
        return {"recovered": False}


class RetryStrategy(RecoveryStrategy):
    """リトライ戦略"""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        super().__init__("retry", priority=10)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    async def can_handle(self, error: Exception, context: Dict[str, Any]) -> bool:
        """一時的なエラーをリトライで処理"""
        error_types = (
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        )
        
        # GitHub API rate limitエラー
        if "rate limit" in str(error).lower():
            return True
        
        return isinstance(error, error_types)
    
    async def recover(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """指数バックオフでリトライ"""
        retry_count = context.get("retry_count", 0)
        
        if retry_count >= self.max_retries:
            return {"recovered": False, "reason": "Max retries exceeded"}
        
        # バックオフ時間を計算
        wait_time = self.backoff_factor ** retry_count
        logger.info(f"Retrying after {wait_time:.1f} seconds (attempt {retry_count + 1}/{self.max_retries})")
        
        await asyncio.sleep(wait_time)
        
        # リトライコンテキストを更新
        context["retry_count"] = retry_count + 1
        
        # 実行関数が提供されている場合は再実行
        if "retry_func" in context:
            try:
                result = await context["retry_func"]()
                return {"recovered": True, "result": result, "retries": retry_count + 1}
            except Exception as e:
                logger.error(f"Retry failed: {e}")
                return await self.recover(e, context)
        
        return {"recovered": True, "action": "retry", "retries": retry_count + 1}


class FallbackStrategy(RecoveryStrategy):
    """フォールバック戦略"""
    
    def __init__(self):
        super().__init__("fallback", priority=20)
    
    async def can_handle(self, error: Exception, context: Dict[str, Any]) -> bool:
        """データ処理エラーをフォールバックで処理"""
        error_types = (
            ValueError,
            KeyError,
            AttributeError,
            json.JSONDecodeError,
        )
        return isinstance(error, error_types)
    
    async def recover(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """簡略化した処理にフォールバック"""
        logger.warning(f"Applying fallback strategy for {error.__class__.__name__}")
        
        # Issue処理のフォールバック
        if "issue" in context:
            issue = context["issue"]
            return {
                "recovered": True,
                "action": "fallback",
                "fallback_result": {
                    "issue_number": issue.number,
                    "title": issue.title,
                    "simplified": True,
                    "error_class": error.__class__.__name__
                }
            }
        
        return {"recovered": False, "reason": "No fallback available"}


class PartialRecoveryStrategy(RecoveryStrategy):
    """部分的リカバリー戦略"""
    
    def __init__(self):
        super().__init__("partial", priority=30)
    
    async def can_handle(self, error: Exception, context: Dict[str, Any]) -> bool:
        """処理の一部が失敗した場合"""
        # 複数の成果物のうち一部が生成できた場合
        return "artifacts" in context and context.get("partial_success", False)
    
    async def recover(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """成功した部分だけを保持"""
        artifacts = context.get("artifacts", {})
        successful_parts = {k: v for k, v in artifacts.items() if v is not None}
        
        if successful_parts:
            logger.info(f"Partial recovery: saved {len(successful_parts)}/{len(artifacts)} artifacts")
            return {
                "recovered": True,
                "action": "partial",
                "successful_artifacts": successful_parts,
                "failed_artifacts": [k for k, v in artifacts.items() if v is None]
            }
        
        return {"recovered": False, "reason": "No successful parts to recover"}


class ErrorRecoveryHandler:
    """エラーリカバリーハンドラー"""
    
    def __init__(self, config: ProcessorConfig):
        self.config = config
        self.strategies: List[RecoveryStrategy] = []
        self._init_strategies()
        
        # エラー履歴
        self.error_history: List[Dict[str, Any]] = []
        self.max_history = 100
        
        # エラーパターン学習
        self.error_patterns = self._load_error_patterns()
    
    def _init_strategies(self):
        """リカバリー戦略を初期化"""
        self.strategies = [
            RetryStrategy(
                max_retries=self.config.github.retry_attempts,
                backoff_factor=2.0
            ),
            FallbackStrategy(),
            PartialRecoveryStrategy(),
        ]
        
        # 優先度順にソート
        self.strategies.sort(key=lambda s: s.priority)
    
    def _load_error_patterns(self) -> Dict[str, Any]:
        """既知のエラーパターンを読み込み"""
        patterns_file = Path("knowledge_base/error_patterns.json")
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load error patterns: {e}")
        
        return {
            "known_errors": {},
            "recovery_success_rate": {}
        }
    
    async def handle_processing_error(self, issue: Issue, error: Exception) -> Dict[str, Any]:
        """Issue処理中のエラーを処理"""
        logger.error(f"Handling error for Issue #{issue.number}: {error}")
        
        context = {
            "issue": issue,
            "error_time": datetime.now().isoformat(),
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc()
        }
        
        # エラー履歴に記録
        self._record_error(context)
        
        # 既知のエラーパターンをチェック
        known_recovery = self._check_known_patterns(error)
        if known_recovery:
            logger.info(f"Applying known recovery pattern: {known_recovery['pattern']}")
            return known_recovery["recovery"]
        
        # リカバリー戦略を試行
        for strategy in self.strategies:
            if await strategy.can_handle(error, context):
                logger.info(f"Trying recovery strategy: {strategy.name}")
                result = await strategy.recover(error, context)
                
                if result.get("recovered"):
                    logger.info(f"Recovery successful with strategy: {strategy.name}")
                    self._learn_from_recovery(error, strategy, result)
                    return result
        
        # リカバリー失敗
        logger.error("All recovery strategies failed")
        return {
            "recovered": False,
            "strategies_tried": [s.name for s in self.strategies],
            "error": str(error)
        }
    
    async def handle_fatal_error(self, error: Exception) -> Dict[str, Any]:
        """致命的エラーを処理"""
        logger.critical(f"Fatal error occurred: {error}")
        
        # 緊急シャットダウン前の処理
        emergency_context = {
            "error_time": datetime.now().isoformat(),
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "fatal": True
        }
        
        # エラー情報を保存
        await self._save_fatal_error_report(emergency_context)
        
        # 4賢者への緊急報告（設定されている場合）
        if self.config.features.four_sages_integration:
            try:
                from ..features.four_sages import FourSagesIntegration
                sages = FourSagesIntegration(self.config)
                await sages.report_critical_error(error, emergency_context)
            except Exception as sage_error:
                logger.error(f"Failed to report to 4 Sages: {sage_error}")
        
        return {
            "recovered": False,
            "fatal": True,
            "report_saved": True
        }
    
    def _record_error(self, context: Dict[str, Any]):
        """エラーを履歴に記録"""
        self.error_history.append(context)
        
        # 最大履歴数を超えたら古いものを削除
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
    
    def _check_known_patterns(self, error: Exception) -> Optional[Dict[str, Any]]:
        """既知のエラーパターンをチェック"""
        error_key = f"{error.__class__.__name__}:{str(error)[:100]}"
        
        if error_key in self.error_patterns.get("known_errors", {}):
            pattern = self.error_patterns["known_errors"][error_key]
            if pattern.get("recovery_success_rate", 0) > 0.7:
                return pattern
        
        return None
    
    def _learn_from_recovery(self, error: Exception, strategy: RecoveryStrategy, result: Dict[str, Any]):
        """成功したリカバリーから学習"""
        error_key = f"{error.__class__.__name__}:{str(error)[:100]}"
        
        if error_key not in self.error_patterns["known_errors"]:
            self.error_patterns["known_errors"][error_key] = {
                "pattern": error_key,
                "strategy": strategy.name,
                "recovery": result,
                "success_count": 0,
                "total_count": 0
            }
        
        pattern = self.error_patterns["known_errors"][error_key]
        pattern["total_count"] += 1
        if result.get("recovered"):
            pattern["success_count"] += 1
        
        pattern["recovery_success_rate"] = pattern["success_count"] / pattern["total_count"]
        
        # パターンを保存
        self._save_error_patterns()
    
    def _save_error_patterns(self):
        """エラーパターンを保存"""
        patterns_file = Path("knowledge_base/error_patterns.json")
        patterns_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(patterns_file, 'w') as f:
                json.dump(self.error_patterns, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save error patterns: {e}")
    
    async def _save_fatal_error_report(self, context: Dict[str, Any]):
        """致命的エラーレポートを保存"""
        report_dir = Path("logs/fatal_errors")
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"fatal_error_{timestamp}.json"
        
        try:
            with open(report_file, 'w') as f:
                json.dump(context, f, indent=2)
            logger.info(f"Fatal error report saved to: {report_file}")
        except Exception as e:
            logger.error(f"Failed to save fatal error report: {e}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """エラー統計を取得"""
        if not self.error_history:
            return {"total_errors": 0}
        
        error_types = {}
        for error in self.error_history:
            error_type = error.get("error_type", "Unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "error_types": error_types,
            "most_common": max(error_types.items(), key=lambda x: x[1])[0] if error_types else None,
            "recovery_patterns": len(self.error_patterns.get("known_errors", {}))
        }