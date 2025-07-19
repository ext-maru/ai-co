#!/usr/bin/env python3
"""
PROJECT ELDERZAN統合API
SessionContext + HybridStorage + SecurityLayer + 4賢者システム完全統合
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...security_layer.core.security_layer import ElderZanSecurityLayer

# PROJECT ELDERZAN統合インポート
from ...session_management.models import SessionContext, SessionStatus
from ...session_management.storage import HybridStorage
from ..sages.incident_sage import IncidentSageIntegration

# 4賢者統合インポート
from ..sages.knowledge_sage import KnowledgeSageIntegration
from ..sages.rag_sage import RAGSageIntegration
from ..sages.task_sage import TaskSageIntegration

# 最適化・監視インポート
from .cost_optimizer import CostOptimizedProcessor
from .error_handler import UnifiedErrorHandler
from .performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class ElderZanIntegratedAPI:
    """
    PROJECT ELDERZAN統合API

    80%コストカット実現のための統合APIシステム
    - SessionContext + HybridStorage + SecurityLayer統合
    - 4賢者システム完全連携
    - コスト最適化・パフォーマンス監視
    - 統合エラーハンドリング
    """

    def __init__(self):
        """統合API初期化"""
        logger.info("PROJECT ELDERZAN統合API初期化開始")

        # コア統合コンポーネント
        self.session_context = SessionContext()
        self.hybrid_storage = HybridStorage()
        self.security_layer = ElderZanSecurityLayer()

        # 4賢者システム統合
        self.knowledge_sage = KnowledgeSageIntegration(
            self.session_context, self.hybrid_storage, self.security_layer
        )
        self.task_sage = TaskSageIntegration(
            self.session_context, self.hybrid_storage, self.security_layer
        )
        self.incident_sage = IncidentSageIntegration(
            self.session_context, self.hybrid_storage, self.security_layer
        )
        self.rag_sage = RAGSageIntegration(
            self.session_context, self.hybrid_storage, self.security_layer
        )

        # 最適化・監視システム
        self.cost_optimizer = CostOptimizedProcessor()
        self.error_handler = UnifiedErrorHandler()
        self.performance_monitor = PerformanceMonitor()

        logger.info("PROJECT ELDERZAN統合API初期化完了")

    async def create_session(
        self, user_id: str, project_path: str, context: Dict[str, Any]
    ) -> str:
        """
        セッション作成API

        Args:
            user_id: ユーザーID
            project_path: プロジェクトパス
            context: 実行コンテキスト

        Returns:
            str: セッションID

        Raises:
            PermissionError: 権限不足
            Exception: その他のエラー
        """
        operation_id = str(uuid.uuid4())

        try:
            # パフォーマンス監視開始
            await self.performance_monitor.start_operation(
                operation_id, "create_session"
            )

            # セキュリティチェック
            if not await self.security_layer.check_permission(
                context, "session_create"
            ):
                raise PermissionError("Session creation permission denied")

            # コスト最適化適用
            optimized_data = await self.cost_optimizer.optimize_request(
                {
                    "user_id": user_id,
                    "project_path": project_path,
                    "operation": "create_session",
                },
                context,
            )

            # セッション作成
            session = await self.session_context.create_new_session(
                user_id=optimized_data.get("user_id", user_id),
                project_path=optimized_data.get("project_path", project_path),
            )

            # HybridStorageに保存
            await self.hybrid_storage.store_session(session, context)

            # 4賢者システムに通知
            await self._notify_sages("session_created", session.session_id, context)

            # パフォーマンス監視終了
            await self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"セッション作成完了: {session.session_id}")
            return session.session_id

        except Exception as e:
            # エラーハンドリング
            await self.error_handler.handle_error(e, context)
            await self.performance_monitor.end_operation(operation_id, success=False)
            raise

    async def get_session(
        self, session_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        セッション取得API

        Args:
            session_id: セッションID
            context: 実行コンテキスト

        Returns:
            Dict[str, Any]: セッション情報

        Raises:
            PermissionError: 権限不足
            Exception: その他のエラー
        """
        operation_id = str(uuid.uuid4())

        try:
            # パフォーマンス監視開始
            await self.performance_monitor.start_operation(operation_id, "get_session")

            # セキュリティチェック
            if not await self.security_layer.check_permission(context, "session_read"):
                raise PermissionError("Session access permission denied")

            # セッション取得
            session = await self.hybrid_storage.get_session(session_id, context)

            # 4賢者システムに通知
            await self._notify_sages("session_accessed", session_id, context)

            # パフォーマンス監視終了
            await self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"セッション取得完了: {session_id}")
            return session.to_dict()

        except Exception as e:
            # エラーハンドリング
            await self.error_handler.handle_error(e, context)
            await self.performance_monitor.end_operation(operation_id, success=False)
            raise

    async def update_session(
        self, session_id: str, update_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        セッション更新API

        Args:
            session_id: セッションID
            update_data: 更新データ
            context: 実行コンテキスト

        Returns:
            Dict[str, Any]: 更新後セッション情報

        Raises:
            PermissionError: 権限不足
            Exception: その他のエラー
        """
        operation_id = str(uuid.uuid4())

        try:
            # パフォーマンス監視開始
            await self.performance_monitor.start_operation(
                operation_id, "update_session"
            )

            # セキュリティチェック
            if not await self.security_layer.check_permission(
                context, "session_update"
            ):
                raise PermissionError("Session update permission denied")

            # コスト最適化適用
            optimized_data = await self.cost_optimizer.optimize_request(
                {
                    "session_id": session_id,
                    "update_data": update_data,
                    "operation": "update_session",
                },
                context,
            )

            # セッション更新
            updated_session = await self.hybrid_storage.update_session(
                session_id, optimized_data.get("update_data", update_data), context
            )

            # 4賢者システムに通知
            await self._notify_sages("session_updated", session_id, context)

            # パフォーマンス監視終了
            await self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"セッション更新完了: {session_id}")
            return updated_session.to_dict()

        except Exception as e:
            # エラーハンドリング
            await self.error_handler.handle_error(e, context)
            await self.performance_monitor.end_operation(operation_id, success=False)
            raise

    async def delete_session(self, session_id: str, context: Dict[str, Any]) -> bool:
        """
        セッション削除API

        Args:
            session_id: セッションID
            context: 実行コンテキスト

        Returns:
            bool: 削除成功フラグ

        Raises:
            PermissionError: 権限不足
            Exception: その他のエラー
        """
        operation_id = str(uuid.uuid4())

        try:
            # パフォーマンス監視開始
            await self.performance_monitor.start_operation(
                operation_id, "delete_session"
            )

            # セキュリティチェック
            if not await self.security_layer.check_permission(
                context, "session_delete"
            ):
                raise PermissionError("Session deletion permission denied")

            # セッション削除
            result = await self.hybrid_storage.delete_session(session_id, context)

            # 4賢者システムに通知
            await self._notify_sages("session_deleted", session_id, context)

            # パフォーマンス監視終了
            await self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"セッション削除完了: {session_id}")
            return result

        except Exception as e:
            # エラーハンドリング
            await self.error_handler.handle_error(e, context)
            await self.performance_monitor.end_operation(operation_id, success=False)
            raise

    async def list_sessions(
        self,
        user_id: str,
        context: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        セッション一覧取得API

        Args:
            user_id: ユーザーID
            context: 実行コンテキスト
            filters: フィルター条件

        Returns:
            List[Dict[str, Any]]: セッション一覧

        Raises:
            PermissionError: 権限不足
            Exception: その他のエラー
        """
        operation_id = str(uuid.uuid4())

        try:
            # パフォーマンス監視開始
            await self.performance_monitor.start_operation(
                operation_id, "list_sessions"
            )

            # セキュリティチェック
            if not await self.security_layer.check_permission(context, "session_read"):
                raise PermissionError("Session list permission denied")

            # セッション一覧取得
            sessions = await self.hybrid_storage.list_sessions(
                user_id, context, filters
            )

            # 4賢者システムに通知
            await self._notify_sages("sessions_listed", user_id, context)

            # パフォーマンス監視終了
            await self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"セッション一覧取得完了: {user_id}, {len(sessions)}件")
            return [session.to_dict() for session in sessions]

        except Exception as e:
            # エラーハンドリング
            await self.error_handler.handle_error(e, context)
            await self.performance_monitor.end_operation(operation_id, success=False)
            raise

    async def get_session_metrics(
        self, session_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        セッションメトリクス取得API

        Args:
            session_id: セッションID
            context: 実行コンテキスト

        Returns:
            Dict[str, Any]: メトリクス情報

        Raises:
            PermissionError: 権限不足
            Exception: その他のエラー
        """
        operation_id = str(uuid.uuid4())

        try:
            # パフォーマンス監視開始
            await self.performance_monitor.start_operation(
                operation_id, "get_session_metrics"
            )

            # セキュリティチェック
            if not await self.security_layer.check_permission(context, "session_read"):
                raise PermissionError("Session metrics permission denied")

            # メトリクス取得
            metrics = await self.performance_monitor.get_session_metrics(session_id)

            # 4賢者システムに通知
            await self._notify_sages("metrics_accessed", session_id, context)

            # パフォーマンス監視終了
            await self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"セッションメトリクス取得完了: {session_id}")
            return metrics

        except Exception as e:
            # エラーハンドリング
            await self.error_handler.handle_error(e, context)
            await self.performance_monitor.end_operation(operation_id, success=False)
            raise

    async def _notify_sages(
        self, event_type: str, session_id: str, context: Dict[str, Any]
    ):
        """
        4賢者システムへの通知

        Args:
            event_type: イベントタイプ
            session_id: セッションID
            context: 実行コンテキスト
        """
        notification_data = {
            "event_type": event_type,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "context": context,
        }

        try:
            # 各賢者に並行通知
            sage_notifications = [
                self.knowledge_sage.handle_notification(notification_data),
                self.task_sage.handle_notification(notification_data),
                self.incident_sage.handle_notification(notification_data),
                self.rag_sage.handle_notification(notification_data),
            ]

            # 非同期実行
            await asyncio.gather(*sage_notifications, return_exceptions=True)

        except Exception as e:
            logger.error(f"4賢者通知エラー: {e}")
            # 通知エラーは全体の処理を止めない

    async def get_sage_status(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        4賢者システム状態取得API

        Args:
            context: 実行コンテキスト

        Returns:
            Dict[str, Any]: 4賢者システム状態

        Raises:
            PermissionError: 権限不足
            Exception: その他のエラー
        """
        try:
            # セキュリティチェック
            if not await self.security_layer.check_permission(context, "sage_status"):
                raise PermissionError("Sage status permission denied")

            # 各賢者の状態取得
            sage_status = {
                "knowledge_sage": await self.knowledge_sage.get_status(),
                "task_sage": await self.task_sage.get_status(),
                "incident_sage": await self.incident_sage.get_status(),
                "rag_sage": await self.rag_sage.get_status(),
                "timestamp": datetime.now().isoformat(),
            }

            logger.info("4賢者システム状態取得完了")
            return sage_status

        except Exception as e:
            # エラーハンドリング
            await self.error_handler.handle_error(e, context)
            raise

    async def get_system_health(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        システム健全性取得API

        Args:
            context: 実行コンテキスト

        Returns:
            Dict[str, Any]: システム健全性情報

        Raises:
            PermissionError: 権限不足
            Exception: その他のエラー
        """
        try:
            # セキュリティチェック
            if not await self.security_layer.check_permission(context, "system_health"):
                raise PermissionError("System health permission denied")

            # システム健全性取得
            health_info = {
                "session_context": await self.session_context.get_health_status(),
                "hybrid_storage": await self.hybrid_storage.get_health_status(),
                "security_layer": await self.security_layer.get_health_status(),
                "performance_monitor": await self.performance_monitor.get_health_status(),
                "sage_system": await self.get_sage_status(context),
                "timestamp": datetime.now().isoformat(),
            }

            logger.info("システム健全性取得完了")
            return health_info

        except Exception as e:
            # エラーハンドリング
            await self.error_handler.handle_error(e, context)
            raise

    async def get_cost_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        コストメトリクス取得API

        Args:
            context: 実行コンテキスト

        Returns:
            Dict[str, Any]: コストメトリクス情報

        Raises:
            PermissionError: 権限不足
            Exception: その他のエラー
        """
        try:
            # セキュリティチェック
            if not await self.security_layer.check_permission(context, "cost_metrics"):
                raise PermissionError("Cost metrics permission denied")

            # コストメトリクス取得
            cost_metrics = await self.cost_optimizer.get_cost_metrics()

            logger.info("コストメトリクス取得完了")
            return cost_metrics

        except Exception as e:
            # エラーハンドリング
            await self.error_handler.handle_error(e, context)
            raise

    async def close(self):
        """リソースクリーンアップ"""
        try:
            # 各コンポーネントのクリーンアップ
            cleanup_tasks = [
                self.session_context.close(),
                self.hybrid_storage.close(),
                self.security_layer.close(),
                self.performance_monitor.close(),
            ]

            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

            logger.info("PROJECT ELDERZAN統合APIクリーンアップ完了")

        except Exception as e:
            logger.error(f"クリーンアップエラー: {e}")
            raise


# 便利な関数
async def create_elderzan_api() -> ElderZanIntegratedAPI:
    """ElderZan統合API作成"""
    return ElderZanIntegratedAPI()


# エクスポート
__all__ = ["ElderZanIntegratedAPI", "create_elderzan_api"]
