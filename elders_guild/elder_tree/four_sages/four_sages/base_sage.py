"""
4賢者システム基盤クラス
全ての賢者が継承する共通機能を提供
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class BaseSage(ABC):
    """4賢者の基盤クラス"""

    def __init__(self, sage_name: str):
        """初期化

        Args:
            sage_name: 賢者名
        """
        self.sage_name = sage_name
        self.logger = logging.getLogger(f"elders.{sage_name}")
        self.capabilities = []
        self.status = "ready"
        self.last_activity = datetime.now()

        # 内部状態
        self._memory = {}
        self._metrics = {
            "requests_processed": 0,
            "errors_count": 0,
            "uptime_start": datetime.now(),
        }

        self.logger.info(f"{sage_name} Sage initialized")

    @abstractmethod
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """リクエスト処理（各賢者で実装）

        Args:
            request: 処理リクエスト

        Returns:
            処理結果
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """この賢者の能力一覧を返す"""
        pass

    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        uptime = datetime.now() - self._metrics["uptime_start"]

        return {
            "sage_name": self.sage_name,
            "status": self.status,
            "uptime_seconds": uptime.total_seconds(),
            "requests_processed": self._metrics["requests_processed"],
            "errors_count": self._metrics["errors_count"],
            "last_activity": self.last_activity.isoformat(),
            "capabilities": self.get_capabilities(),
        }

    async def get_memory(self, key: str) -> Any:
        """メモリから値を取得"""
        return self._memory.get(key)

    async def set_memory(self, key: str, value: Any):
        """メモリに値を保存"""
        self._memory[key] = value

    async def log_request(self, request: Dict[str, Any], result: Dict[str, Any]):
        """リクエストと結果をログに記録"""
        self._metrics["requests_processed"] += 1
        self.last_activity = datetime.now()

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "sage": self.sage_name,
            "request_type": request.get("type", "unknown"),
            "success": result.get("success", True),
            "processing_time_ms": result.get("processing_time_ms", 0),
        }

        self.logger.info(f"Request processed: {json.dumps(log_entry)}")

    async def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """エラーをログに記録"""
        self._metrics["errors_count"] += 1

        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "sage": self.sage_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
        }

        self.logger.error(f"Error occurred: {json.dumps(error_entry)}")

    async def collaborate_with_sage(
        self, target_sage: str, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """他の賢者との連携

        Args:
            target_sage: 連携先の賢者名
            request: 連携リクエスト

        Returns:
            連携結果
        """
        # 実際の実装では賢者間通信システムを使用
        self.logger.info(
            f"Collaborating with {target_sage}: {request.get('type', 'unknown')}"
        )

        # プレースホルダー実装
        return {
            "success": True,
            "message": f"Collaboration request sent to {target_sage}",
            "data": {},
        }

    def __str__(self) -> str:
        """文字列表現取得"""
        return f"{self.sage_name}Sage(status={self.status})"

    def __repr__(self) -> str:
        """オブジェクト表現取得"""
        return f"<{self.sage_name}Sage status={self.status} requests={self._metrics['requests_processed']}>"

class SageRegistry:
    """賢者レジストリ - 4賢者の管理"""

    def __init__(self):
        """初期化メソッド"""
        self._sages: Dict[str, BaseSage] = {}
        self.logger = logging.getLogger("elders.registry")

    def register_sage(self, sage: BaseSage):
        """賢者を登録"""
        self._sages[sage.sage_name] = sage
        self.logger.info(f"Registered {sage.sage_name} Sage")

    def get_sage(self, sage_name: str) -> Optional[BaseSage]:
        """賢者を取得"""
        return self._sages.get(sage_name)

    def get_all_sages(self) -> Dict[str, BaseSage]:
        """全賢者を取得"""
        return self._sages.copy()

    async def broadcast_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """全賢者にリクエストをブロードキャスト"""
        results = {}

        tasks = []
        for sage_name, sage in self._sages.items():
            task = asyncio.create_task(
                sage.process_request(request), name=f"{sage_name}_broadcast"
            )
            tasks.append((sage_name, task))

        for sage_name, task in tasks:
            try:
                results[sage_name] = await task
            except Exception as e:
                results[sage_name] = {"success": False, "error": str(e)}

        return {
            "success": True,
            "broadcast_results": results,
            "responded_sages": len(results),
        }

    async def health_check_all(self) -> Dict[str, Any]:
        """全賢者のヘルスチェック"""
        health_results = {}

        for sage_name, sage in self._sages.items():
            try:
                health_results[sage_name] = await sage.health_check()
            except Exception as e:
                health_results[sage_name] = {
                    "sage_name": sage_name,
                    "status": "error",
                    "error": str(e),
                }

        return {
            "timestamp": datetime.now().isoformat(),
            "total_sages": len(self._sages),
            "sages": health_results,
        }

# グローバルレジストリインスタンス
sage_registry = SageRegistry()
