#!/usr/bin/env python3
"""
グランドエルダープロセス
Grand Elder Process - 最高指揮プロセス

エルダーズツリーの頂点に立つ最高権限プロセス
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List

from libs.elder_process_base import (
    ElderProcessBase, ElderRole, MessageType, ElderMessage
)

class GrandElderProcess(ElderProcessBase):
    """
    グランドエルダーmaru - 最高指揮プロセス

    責務:
    - 全体戦略の決定
    - 緊急時の最終判断
    - エルダーズツリー全体の監督
    - 重要な承認の最終決定
    """

    def __init__(self):
        """初期化メソッド"""
        super().__init__(
            elder_name="grand_elder_maru",
            elder_role=ElderRole.GRAND_ELDER,
            port=5000
        )

        # グランドエルダー固有の状態
        self.emergency_mode = False
        self.global_directives: List[Dict[str, Any]] = []
        self.elder_tree_status: Dict[str, Dict] = {}
        self.approval_queue: List[Dict[str, Any]] = []

    async def initialize(self):
        """初期化処理"""
        self.logger.info("🌟 Initializing Grand Elder maru...")

        # 全体設定の読み込み
        await self._load_global_config()

        # エルダーツリーの初期状態確認
        await self._check_elder_tree_status()

        self.logger.info("✅ Grand Elder initialization completed")

    async def process(self):
        """メイン処理"""
        # 承認待ちの処理
        if self.approval_queue:
            await self._process_approvals()

        # エルダーツリーの健全性チェック
        await self._monitor_elder_tree_health()

        # 緊急モードチェック
        if self.emergency_mode:
            await self._handle_emergency_mode()

    async def handle_message(self, message: ElderMessage):
        """メッセージ処理"""
        self.logger.info(f"Received {message.message_type.value} from {message.source_elder}")

        if message.message_type == MessageType.REPORT:
            await self._handle_report(message)
        elif message.message_type == MessageType.QUERY:
            await self._handle_query(message)
        elif message.message_type == MessageType.EMERGENCY:
            await self._handle_emergency(message)

    def register_handlers(self):
        """追加のメッセージハンドラー登録"""
        self.message_handlers[MessageType.EMERGENCY] = self._handle_emergency

    async def on_cleanup(self):
        """クリーンアップ処理"""
        # 最終指示の発行
        await self._issue_final_directives()

    # プライベートメソッド

    async def _load_global_config(self):
        """グローバル設定の読み込み"""

        self.global_config = {
            "emergency_threshold": 0.8,
            "approval_timeout": 300,  # 5分
            "health_check_interval": 60  # 1分
        }

    async def _check_elder_tree_status(self):
        """エルダーツリーの状態確認"""
        # 各エルダーにステータス要求
        status_query = ElderMessage(
            message_id=f"status_check_{datetime.now().timestamp()}",
            source_elder=self.elder_name,
            target_elder="broadcast",
            message_type=MessageType.QUERY,
            payload={"query_type": "status"},
            priority=8
        )

        await self.send_message(status_query)

    async def _process_approvals(self):
        """承認処理"""
        for approval in self.approval_queue[:]:
            try:
                decision = await self._make_approval_decision(approval)

                # 決定を通知
                response_msg = ElderMessage(
                    message_id=f"approval_response_{approval['request_id']}",
                    source_elder=self.elder_name,
                    target_elder=approval['requester'],
                    message_type=MessageType.COMMAND,
                    payload={
                        "request_id": approval['request_id'],
                        "approved": decision['approved'],
                        "reason": decision['reason'],
                        "conditions": decision.get('conditions', [])
                    },
                    priority=9
                )

                await self.send_message(response_msg)
                self.approval_queue.remove(approval)

            except Exception as e:
                self.logger.error(f"Approval processing error: {e}")

    async def _make_approval_decision(self, approval: Dict[str, Any]) -> Dict[str, Any]:
        """承認決定のロジック"""
        # シンプルな承認ロジック（実際はより複雑）
        if approval.get('type') == 'emergency':
            return {
                "approved": True,
                "reason": "Emergency approval granted",
                "conditions": ["Report results within 1 hour"]
            }

        if approval.get('risk_level', 0) > 0.7:
            return {
                "approved": False,
                "reason": "Risk level too high"
            }

        return {
            "approved": True,
            "reason": "Standard approval granted"
        }

    async def _monitor_elder_tree_health(self):
        """エルダーツリーの健全性監視"""
        now = datetime.now()

        # 各エルダーの最終ハートビート確認
        for elder_name, status in self.elder_tree_status.items():
            last_heartbeat = status.get('last_heartbeat')
            if last_heartbeat:
                time_diff = (now - last_heartbeat).total_seconds()
                if time_diff > 120:  # 2分以上応答なし
                    self.logger.warning(f"Elder {elder_name} is unresponsive")
                    await self._handle_unresponsive_elder(elder_name)

    async def _handle_emergency_mode(self):
        """緊急モード処理"""
        self.logger.warning("🚨 Emergency mode active")

        # 全エルダーに緊急指示
        emergency_directive = ElderMessage(
            message_id=f"emergency_directive_{datetime.now().timestamp()}",
            source_elder=self.elder_name,
            target_elder="broadcast",
            message_type=MessageType.EMERGENCY,
            payload={
                "directive": "emergency_protocol",
                "priority": "maximum",
                "actions": [
                    "Suspend non-critical operations",
                    "Focus on emergency resolution",
                    "Report status every 30 seconds"
                ]
            },
            priority=10
        )

        await self.send_message(emergency_directive)

    async def _handle_report(self, message: ElderMessage):
        """レポート処理"""
        report_type = message.payload.get('type')

        if report_type == 'status':
            # ステータス更新
            self.elder_tree_status[message.source_elder] = {
                'status': message.payload.get('status'),
                'last_heartbeat': datetime.now(),
                'metrics': message.payload.get('metrics', {})
            }

        elif report_type == 'incident':
            # インシデント報告
            severity = message.payload.get('severity', 0)
            if severity > self.global_config['emergency_threshold']:
                self.emergency_mode = True
                self.logger.error(f"Emergency triggered by {message.source_elder}")

        elif report_type == 'completion':
            # 完了報告
            self.logger.info(f"Task completed by {message.source_elder}: {message.payload.get('task_id')}")

    async def _handle_query(self, message: ElderMessage):
        """クエリ処理"""
        query_type = message.payload.get('query_type')

        if query_type == 'approval':
            # 承認要求をキューに追加
            self.approval_queue.append({
                'request_id': message.message_id,
                'requester': message.source_elder,
                'type': message.payload.get('approval_type'),
                'details': message.payload.get('details'),
                'risk_level': message.payload.get('risk_level', 0.5),
                'timestamp': datetime.now()
            })

        elif query_type == 'directive':
            # 指示要求
            response = await self._generate_directive(message.payload)

            response_msg = ElderMessage(
                message_id=f"directive_response_{message.message_id}",
                source_elder=self.elder_name,
                target_elder=message.source_elder,
                message_type=MessageType.COMMAND,
                payload=response,
                priority=8
            )

            await self.send_message(response_msg)

    async def _handle_emergency(self, message: ElderMessage):
        """緊急メッセージ処理"""
        self.logger.error(f"🚨 EMERGENCY from {message.source_elder}: {message.payload}")

        # 緊急モード有効化
        self.emergency_mode = True

        # 緊急対応プロトコル起動
        await self._initiate_emergency_protocol(message)

    async def _handle_unresponsive_elder(self, elder_name: str):
        """応答のないエルダーの処理"""
        # 他のエルダーに確認要請
        check_msg = ElderMessage(
            message_id=f"health_check_{elder_name}_{datetime.now().timestamp()}",
            source_elder=self.elder_name,
            target_elder="broadcast",
            message_type=MessageType.QUERY,
            payload={
                "query_type": "peer_check",
                "target_elder": elder_name
            },
            priority=9
        )

        await self.send_message(check_msg)

    async def _generate_directive(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """指示生成"""
        # シンプルな指示生成ロジック
        return {
            "directive_id": f"dir_{datetime.now().timestamp()}",
            "actions": [
                "Proceed with standard protocol",
                "Report progress every hour",
                "Escalate if issues arise"
            ],
            "priority": request.get('priority', 5),
            "deadline": "24 hours"
        }

    async def _initiate_emergency_protocol(self, emergency_msg: ElderMessage):
        """緊急プロトコル起動"""
        # 全エルダーに緊急通知
        alert_msg = ElderMessage(
            message_id=f"emergency_alert_{datetime.now().timestamp()}",
            source_elder=self.elder_name,
            target_elder="broadcast",
            message_type=MessageType.EMERGENCY,
            payload={
                "alert_level": "critical",
                "source": emergency_msg.source_elder,
                "details": emergency_msg.payload,
                "protocol": "emergency_response_v1"
            },
            priority=10,
            requires_ack=True
        )

        await self.send_message(alert_msg)

        # 緊急対応チームの招集
        await self._summon_emergency_team()

    async def _summon_emergency_team(self):
        """緊急対応チーム招集"""
        # インシデント賢者を最優先で召喚
        summon_msg = ElderMessage(
            message_id=f"summon_incident_sage_{datetime.now().timestamp()}",
            source_elder=self.elder_name,
            target_elder="incident_sage",
            message_type=MessageType.COMMAND,
            payload={
                "command": "activate_emergency_mode",
                "priority": "maximum"
            },
            priority=10
        )

        await self.send_message(summon_msg)

    async def _issue_final_directives(self):
        """最終指示の発行"""
        if self.global_directives:
            final_msg = ElderMessage(
                message_id=f"final_directives_{datetime.now().timestamp()}",
                source_elder=self.elder_name,
                target_elder="broadcast",
                message_type=MessageType.COMMAND,
                payload={
                    "directives": self.global_directives,
                    "message": "Grand Elder signing off"
                },
                priority=10
            )

            await self.send_message(final_msg)

# プロセス起動
if __name__ == "__main__":
    from libs.elder_process_base import run_elder_process
    run_elder_process(GrandElderProcess)
