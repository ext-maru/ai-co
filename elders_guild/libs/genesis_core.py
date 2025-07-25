"""
Genesis Core - エルダーズギルドシステム初期化コア

システム全体の初期化と起動を担当するコアモジュール。
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class GenesisCore:
    """エルダーズギルドシステム初期化コア"""

    def __init__(self):
        """Genesis Coreを初期化"""
        self.logger = logger
        self.startup_time = datetime.now()
        self.initialized_components = []
        self.system_status = "initializing"
        
        self.logger.info("🌱 Genesis Core初期化開始")

    def initialize_system(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        システム全体を初期化
        
        Args:
            config: 初期化設定
            
        Returns:
            Dict[str, Any]: 初期化結果
        """
        try:
            self.logger.info("🚀 エルダーズギルドシステム初期化開始")
            
            # 基本環境設定
            self._setup_environment()
            
            # パス設定
            self._setup_paths()
            
            # ログ設定
            self._setup_logging()
            
            # 4賢者システム初期化
            sages_result = self._initialize_four_sages()
            
            # ワーカーシステム初期化
            workers_result = self._initialize_workers()
            
            # データベース初期化
            db_result = self._initialize_database()
            
            # ネットワーク初期化
            network_result = self._initialize_network()
            
            self.system_status = "ready"
            
            result = {
                "status": "success",
                "startup_time": self.startup_time.isoformat(),
                "initialization_duration": (datetime.now() - self.startup_time).total_seconds(),
                "components": {
                    "four_sages": sages_result,
                    "workers": workers_result,
                    "database": db_result,
                    "network": network_result
                },
                "system_status": self.system_status
            }
            
            self.logger.info("✅ エルダーズギルドシステム初期化完了")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ システム初期化エラー: {e}")
            self.system_status = "error"
            return {
                "status": "error",
                "error": str(e),
                "system_status": self.system_status
            }

    def _setup_environment(self):
        """環境設定をセットアップ"""
        try:
            # プロジェクトルートの設定
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
            # 環境変数の確認
            required_env_vars = ["GITHUB_TOKEN", "GITHUB_REPO_OWNER", "GITHUB_REPO_NAME"]
            missing_vars = []
            
            for var in required_env_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                self.logger.warning(f"⚠️ 未設定の環境変数: {missing_vars}")
            
            self.initialized_components.append("environment")
            self.logger.info("✅ 環境設定完了")
            
        except Exception as e:
            self.logger.error(f"環境設定エラー: {e}")
            raise

    def _setup_paths(self):
        """パス設定をセットアップ"""
        try:
            # 重要ディレクトリの確認・作成
            important_dirs = [
                "logs",
                "data",
                "knowledge_base",
                "auto_generated",
                "tests/unit",
                "tests/integration"
            ]
            
            project_root = Path(__file__).parent.parent
            for dir_name in important_dirs:
                dir_path = project_root / dir_name
                dir_path.mkdir(parents=True, exist_ok=True)
            
            self.initialized_components.append("paths")
            self.logger.info("✅ パス設定完了")
            
        except Exception as e:
            self.logger.error(f"パス設定エラー: {e}")
            raise

    def _setup_logging(self):
        """ログ設定をセットアップ"""
        try:
            # ログレベルの設定
            log_level = os.getenv("LOG_LEVEL", "INFO").upper()
            
            # ログフォーマットの設定
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # ファイルハンドラーの設定
            log_file = Path(__file__).parent.parent / "logs" / "genesis.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            
            # ルートロガーの設定
            root_logger = logging.getLogger()
            root_logger.setLevel(getattr(logging, log_level))
            
            if not root_logger.handlers:
                root_logger.addHandler(file_handler)
            
            self.initialized_components.append("logging")
            self.logger.info("✅ ログ設定完了")
            
        except Exception as e:
            self.logger.error(f"ログ設定エラー: {e}")
            raise

    def _initialize_four_sages(self) -> Dict[str, Any]:
        """4賢者システムを初期化"""
        try:
            self.logger.info("🧙‍♂️ 4賢者システム初期化開始")
            
            sages_status = {}
            
            # Knowledge Sage
            try:
                from libs.knowledge_sage import KnowledgeSage
                knowledge_sage = KnowledgeSage()
                sages_status["knowledge"] = "initialized"
            except Exception as e:
                sages_status["knowledge"] = f"error: {e}"
            
            # Task Sage
            try:
                from libs.task_sage import TaskSage
                task_sage = TaskSage()
                sages_status["task"] = "initialized"
            except Exception as e:
                sages_status["task"] = f"error: {e}"
            
            # Incident Sage
            try:
                from libs.incident_sage import IncidentSage
                incident_sage = IncidentSage()
                sages_status["incident"] = "initialized"
            except Exception as e:
                sages_status["incident"] = f"error: {e}"
            
            # RAG Sage
            try:
                from libs.rag_manager import RagManager
                rag_sage = RagManager()
                sages_status["rag"] = "initialized"
            except Exception as e:
                sages_status["rag"] = f"error: {e}"
            
            self.initialized_components.append("four_sages")
            self.logger.info("✅ 4賢者システム初期化完了")
            
            return {
                "status": "success",
                "sages": sages_status,
                "initialized_count": len([s for s in sages_status.values() if s == "initialized"])
            }
            
        except Exception as e:
            self.logger.error(f"4賢者システム初期化エラー: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _initialize_workers(self) -> Dict[str, Any]:
        """ワーカーシステムを初期化"""
        try:
            self.logger.info("⚔️ ワーカーシステム初期化開始")
            
            # BaseWorkerの確認
            try:
                from libs.base_worker import BaseWorker
                worker_base_status = "available"
            except Exception as e:
                worker_base_status = f"error: {e}"
            
            self.initialized_components.append("workers")
            self.logger.info("✅ ワーカーシステム初期化完了")
            
            return {
                "status": "success",
                "base_worker": worker_base_status
            }
            
        except Exception as e:
            self.logger.error(f"ワーカーシステム初期化エラー: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _initialize_database(self) -> Dict[str, Any]:
        """データベースシステムを初期化"""
        try:
            self.logger.info("💾 データベース初期化開始")
            
            # SQLiteの確認
            try:
                import sqlite3
                db_status = "available"
            except Exception as e:
                db_status = f"error: {e}"
            
            self.initialized_components.append("database")
            self.logger.info("✅ データベース初期化完了")
            
            return {
                "status": "success",
                "sqlite": db_status
            }
            
        except Exception as e:
            self.logger.error(f"データベース初期化エラー: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _initialize_network(self) -> Dict[str, Any]:
        """ネットワークシステムを初期化"""
        try:
            self.logger.info("🌐 ネットワーク初期化開始")
            
            # 基本ネットワークライブラリの確認
            network_status = {}
            
            try:
                import requests
                network_status["requests"] = "available"
            except Exception as e:
                network_status["requests"] = f"error: {e}"
            
            try:
                import asyncio
                network_status["asyncio"] = "available"
            except Exception as e:
                network_status["asyncio"] = f"error: {e}"
            
            self.initialized_components.append("network")
            self.logger.info("✅ ネットワーク初期化完了")
            
            return {
                "status": "success",
                "libraries": network_status
            }
            
        except Exception as e:
            self.logger.error(f"ネットワーク初期化エラー: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def get_system_status(self) -> Dict[str, Any]:
        """システム状態を取得"""
        return {
            "status": self.system_status,
            "startup_time": self.startup_time.isoformat(),
            "uptime_seconds": (datetime.now() - self.startup_time).total_seconds(),
            "initialized_components": self.initialized_components
        }

    def shutdown_system(self):
        """システムをシャットダウン"""
        try:
            self.logger.info("🛑 エルダーズギルドシステムシャットダウン開始")
            
            # 各コンポーネントのシャットダウン処理
            for component in reversed(self.initialized_components):
                try:
                    self.logger.info(f"📤 {component} シャットダウン中...")
                    # 実際のシャットダウン処理をここに実装
                except Exception as e:
                    self.logger.error(f"{component} シャットダウンエラー: {e}")
            
            self.system_status = "shutdown"
            self.logger.info("✅ システムシャットダウン完了")
            
        except Exception as e:
            self.logger.error(f"シャットダウンエラー: {e}")


# グローバルインスタンス
_genesis_instance = None


def get_genesis_core() -> GenesisCore:
    """Genesis Coreのシングルトンインスタンスを取得"""
    global _genesis_instance
    if _genesis_instance is None:
        _genesis_instance = GenesisCore()
    return _genesis_instance


def initialize_elders_guild(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """エルダーズギルドシステムを初期化"""
    genesis = get_genesis_core()
    return genesis.initialize_system(config)


def get_system_status() -> Dict[str, Any]:
    """システム状態を取得"""
    genesis = get_genesis_core()
    return genesis.get_system_status()


def shutdown_elders_guild():
    """エルダーズギルドシステムをシャットダウン"""
    genesis = get_genesis_core()
    genesis.shutdown_system()


# 互換性のための関数
def setup(*args, **kwargs):
    """セットアップ関数"""
    logger.info("🌱 Genesis Core セットアップ")
    return get_genesis_core()


def main(*args, **kwargs):
    """メイン関数"""
    logger.info("🌱 Genesis Core 実行")
    return initialize_elders_guild()


# Export
__all__ = [
    "GenesisCore", 
    "get_genesis_core", 
    "initialize_elders_guild", 
    "get_system_status", 
    "shutdown_elders_guild",
    "setup", 
    "main"
]