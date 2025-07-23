#!/usr/bin/env python3
"""
Elder Tree Base Soul Implementation
すべての魂（Soul）の基底クラス
"""

import asyncio
import logging
import os
import signal
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from uuid import uuid4

# 基本的な構造化ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class SoulContext:


"""魂のコンテキスト管理""" str):
        self.soul_name = soul_name
        self.session_id = str(uuid4())
        self.start_time = datetime.now()
        self.process_id = os.getpid()
        self.context_data: Dict[str, Any] = {}
        self.active_tasks: Set[str] = set()
        
    def add_context(self, key: str, value: Any):
        """コンテキストデータの追加"""
        self.context_data[key] = value
        
    def get_context(self, key: str, default: Any = None) -> Any:
        """コンテキストデータの取得"""
        return self.context_data.get(key, default)
        
    def register_task(self, task_id: str):
        """アクティブタスクの登録"""
        self.active_tasks.add(task_id)
        
    def complete_task(self, task_id: str):
        """タスクの完了"""
        self.active_tasks.discard(task_id)
        
    def get_runtime(self) -> float:

        """実行時間の取得（秒）"""
    """
    Elder Tree魂の基底クラス
    
    すべての魂（Elder、Sage、Servant、Magic）はこのクラスを継承する
    """
    
    def __init__(self, soul_type: str, domain: str, soul_name: Optional[str] = None):
        """
        Args:
            soul_type: 魂の種類（elder, sage, servant, magic）
            domain: 担当ドメイン
            soul_name: 魂の名前（省略時はクラス名から生成）
        """
        self.soul_type = soul_type
        self.domain = domain
        self.soul_name = soul_name or self.__class__.__name__
        
        # コンテキスト管理
        self.context = SoulContext(self.soul_name)
        
        # 状態管理
        self._running = False
        self._initialized = False
        self._shutdown_event = asyncio.Event()
        
        # 能力リスト
        self.abilities: List[str] = []
        
        # メトリクス
        self.metrics = {
            "messages_processed": 0,
            "errors_encountered": 0,
            "tasks_completed": 0,
            "uptime_seconds": 0
        }
        
        logger.info(f"BaseSoul initialized: {self.soul_name} (type: {self.soul_type}, domain: {self.domain})")
        
    @abstractmethod
    async def initialize(self) -> bool:

        
    """
        魂の初期化処理
        
        Returns:
            初期化成功時True
        """ Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        メッセージ処理（A2A通信）
        
        Args:
            message: 受信メッセージ
            
        Returns:
            応答メッセージ（必要な場合）
        """
        pass
        
    @abstractmethod
    async def shutdown(self):

            """
        魂のシャットダウン処理
        """
        """魂のメインループ開始"""
        try:
            # 初期化
            logger.info(f"Starting soul: {self.soul_name}")
            self._initialized = await self.initialize()
            
            if not self._initialized:
                logger.error(f"Failed to initialize soul: {self.soul_name}")
                return
                
            self._running = True
            
            # シグナルハンドラー設定
            self._setup_signal_handlers()
            
            # メインループ
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"Soul crashed: {self.soul_name} - {str(e)}", exc_info=True)
            
        finally:
            await self.shutdown()
            logger.info(f"Soul stopped: {self.soul_name}")
            
    async def _main_loop(self):

            
    """メインイベントループ"""
            try:
                # シャットダウンイベントを待機（タイムアウト付き）
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=1.0
                )
                # シャットダウンイベントが発生したらループを抜ける
                self._running = False
                
            except asyncio.TimeoutError:
                # 定期的な処理（ヘルスチェック、メトリクス更新など）
                await self._periodic_tasks()
                
    async def _periodic_tasks(self):

                """定期実行タスク"""
        """
        ヘルスチェック（サブクラスでオーバーライド可能）
        """
        pass
        
    def _setup_signal_handlers(self):

        """シグナルハンドラーの設定"""
            logger.info(f"Soul {self.soul_name} received signal: {signum}")
            asyncio.create_task(self.request_shutdown())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    async def request_shutdown(self):

            """シャットダウンリクエスト""" {self.soul_name}")
        self._running = False
        self._shutdown_event.set()
        
    def register_ability(self, ability_name: str):
        """能力の登録"""
        if ability_name not in self.abilities:
            self.abilities.append(ability_name)
            logger.info(f"Soul {self.soul_name} registered ability: {ability_name}")
            
    def get_soul_info(self) -> Dict[str, Any]:

            
    """魂の情報を取得""" self.soul_name,
            "soul_type": self.soul_type,
            "domain": self.domain,
            "process_id": self.context.process_id,
            "session_id": self.context.session_id,
            "uptime": self.context.get_runtime(),
            "abilities": self.abilities,
            "metrics": self.metrics,
            "active_tasks": list(self.context.active_tasks)
        }
        
    # ユーティリティメソッド
    
    def _create_error_response(
        self,
        original_message: Dict[str,
        Any],
        error: str
    ) -> Dict[str, Any]:

    """エラーレスポンスの生成""" "error",
            "error": error,
            "original_message_id": original_message.get("message_id"),
            "soul_name": self.soul_name,
            "timestamp": datetime.now().isoformat()
        }
        
    def _create_success_response(
        self,
        original_message: Dict[str,
        Any],
        result: Any
    ) -> Dict[str, Any]:

    """成功レスポンスの生成""" "response",
            "result": result,
            "original_message_id": original_message.get("message_id"),
            "soul_name": self.soul_name,
            "timestamp": datetime.now().isoformat()
        }