#!/usr/bin/env python3
"""
🌳 Elder Tree Hierarchy System
完全なエルダー階層構造の実装

階層:
1. 🌟 グランドエルダーmaru（最高位）
2. 🤖 クロードエルダー（開発実行責任者）
3. 🧙‍♂️ 4賢者（ナレッジ・タスク・インシデント・RAG）
4. 🏛️ エルダー評議会（5評議員）
5. 🤖 エルダーサーバント（実行部隊）
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ElderRank(Enum):
    """エルダー階級"""

    GRAND_ELDER = "grand_elder"  # グランドエルダー
    CLAUDE_ELDER = "claude_elder"  # クロードエルダー
    SAGE = "sage"  # 賢者
    COUNCIL_MEMBER = "council_member"  # 評議会メンバー
    SERVANT = "servant"  # サーバント


class SageType(Enum):
    """賢者タイプ"""

    KNOWLEDGE = "knowledge"  # ナレッジ賢者
    TASK = "task"  # タスク賢者
    INCIDENT = "incident"  # インシデント賢者
    RAG = "rag"  # RAG賢者


class CouncilRole(Enum):
    """評議会役職"""

    GRAND_SAGE_OF_KNOWLEDGE = "grand_sage_of_knowledge"
    ORACLE_OF_STRATEGIC_PLANNING = "oracle_of_strategic_planning"
    GUARDIAN_OF_SYSTEM_STABILITY = "guardian_of_system_stability"
    MYSTIC_OF_INNOVATION = "mystic_of_innovation"
    KEEPER_OF_ANCIENT_WISDOM = "keeper_of_ancient_wisdom"


class ServantType(Enum):
    """サーバントタイプ"""

    INCIDENT_KNIGHT = "incident_knight"
    DWARF_CRAFTSMAN = "dwarf_craftsman"
    RAG_WIZARD = "rag_wizard"
    ELF_MONITOR = "elf_monitor"


@dataclass
class ElderMessage:
    """エルダー間メッセージ"""

    sender_rank: ElderRank
    sender_id: str
    recipient_rank: ElderRank
    recipient_id: Optional[str]
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    requires_response: bool = False
    priority: str = "normal"


@dataclass
class ElderDecision:
    """エルダー決定事項"""

    decision_id: str
    decision_type: str
    made_by: ElderRank
    approved_by: List[str]
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    execution_status: str = "pending"


class ElderTreeNode:
    """エルダーツリーのノード"""

    def __init__(self, rank: ElderRank, node_id: str, name: str):
        self.rank = rank
        self.node_id = node_id
        self.name = name
        self.parent: Optional["ElderTreeNode"] = None
        self.children: List["ElderTreeNode"] = []
        self.is_active = True
        self.wisdom_level = self._calculate_wisdom_level()

    def _calculate_wisdom_level(self) -> float:
        """階級に基づく知恵レベル計算"""
        wisdom_map = {
            ElderRank.GRAND_ELDER: 1.0,  # 100%
            ElderRank.CLAUDE_ELDER: 0.95,  # 95%
            ElderRank.SAGE: 0.90,  # 90%
            ElderRank.COUNCIL_MEMBER: 0.85,  # 85%
            ElderRank.SERVANT: 0.70,  # 70%
        }
        return wisdom_map.get(self.rank, 0.5)

    def add_child(self, child: "ElderTreeNode"):
        """子ノード追加"""
        child.parent = self
        self.children.append(child)

    def get_path_to_root(self) -> List["ElderTreeNode"]:
        """ルートまでのパスを取得"""
        path = [self]
        current = self.parent
        while current:
            path.append(current)
            current = current.parent
        return list(reversed(path))

    def can_command(self, target: "ElderTreeNode") -> bool:
        """指揮権限の確認"""
        # 自分より下位の階級には指揮可能
        if self.rank.value < target.rank.value:
            return True
        # 同階級でも直属の部下なら指揮可能
        if target.parent == self:
            return True
        return False


class ElderTreeHierarchy:
    """🌳 エルダーツリー階層システム"""

    def __init__(self):
        self.root: Optional[ElderTreeNode] = None
        self.nodes: Dict[str, ElderTreeNode] = {}
        self.message_queue: List[ElderMessage] = []
        self.decision_log: List[ElderDecision] = []
        self._initialize_hierarchy()

    def _initialize_hierarchy(self):
        """階層構造の初期化"""
        # グランドエルダーmaru（最高位）
        self.root = ElderTreeNode(ElderRank.GRAND_ELDER, "maru", "Grand Elder maru")
        self.nodes["maru"] = self.root

        # クロードエルダー（開発実行責任者）
        claude_elder = ElderTreeNode(ElderRank.CLAUDE_ELDER, "claude", "Claude Elder")
        self.root.add_child(claude_elder)
        self.nodes["claude"] = claude_elder

        # 4賢者
        sages = [
            (SageType.KNOWLEDGE, "knowledge_sage", "Knowledge Sage"),
            (SageType.TASK, "task_sage", "Task Sage"),
            (SageType.INCIDENT, "incident_sage", "Incident Sage"),
            (SageType.RAG, "rag_sage", "RAG Sage"),
        ]

        for sage_type, sage_id, sage_name in sages:
            sage_node = ElderTreeNode(ElderRank.SAGE, sage_id, sage_name)
            claude_elder.add_child(sage_node)
            self.nodes[sage_id] = sage_node

            # 各賢者配下に評議会メンバーを配置
            self._add_council_members_to_sage(sage_node, sage_type)

    def _add_council_members_to_sage(
        self, sage_node: ElderTreeNode, sage_type: SageType
    ):
        """賢者配下に評議会メンバーを追加"""
        # 賢者タイプに応じた評議会メンバー配置
        council_mapping = {
            SageType.KNOWLEDGE: [
                CouncilRole.GRAND_SAGE_OF_KNOWLEDGE,
                CouncilRole.KEEPER_OF_ANCIENT_WISDOM,
            ],
            SageType.TASK: [CouncilRole.ORACLE_OF_STRATEGIC_PLANNING],
            SageType.INCIDENT: [CouncilRole.GUARDIAN_OF_SYSTEM_STABILITY],
            SageType.RAG: [CouncilRole.MYSTIC_OF_INNOVATION],
        }

        council_roles = council_mapping.get(sage_type, [])
        for role in council_roles:
            council_id = f"council_{role.value}"
            council_node = ElderTreeNode(
                ElderRank.COUNCIL_MEMBER, council_id, role.value
            )
            sage_node.add_child(council_node)
            self.nodes[council_id] = council_node

            # 評議会メンバー配下にサーバント配置
            self._add_servants_to_council(council_node, role)

    def _add_servants_to_council(
        self, council_node: ElderTreeNode, council_role: CouncilRole
    ):
        """評議会メンバー配下にサーバント追加"""
        # 評議会役職に応じたサーバント配置
        servant_mapping = {
            CouncilRole.GUARDIAN_OF_SYSTEM_STABILITY: [ServantType.INCIDENT_KNIGHT],
            CouncilRole.ORACLE_OF_STRATEGIC_PLANNING: [ServantType.DWARF_CRAFTSMAN],
            CouncilRole.MYSTIC_OF_INNOVATION: [ServantType.RAG_WIZARD],
            CouncilRole.GRAND_SAGE_OF_KNOWLEDGE: [ServantType.ELF_MONITOR],
            CouncilRole.KEEPER_OF_ANCIENT_WISDOM: [ServantType.ELF_MONITOR],
        }

        servant_types = servant_mapping.get(council_role, [])
        for i, servant_type in enumerate(servant_types):
            servant_id = f"servant_{servant_type.value}_{i}"
            servant_node = ElderTreeNode(
                ElderRank.SERVANT, servant_id, f"{servant_type.value} #{i}"
            )
            council_node.add_child(servant_node)
            self.nodes[servant_id] = servant_node

    async def send_message(self, message: ElderMessage) -> bool:
        """メッセージ送信"""
        try:
            # 権限チェック
            sender = self.nodes.get(message.sender_id)
            if not sender:
                logger.error(f"Sender not found: {message.sender_id}")
                return False

            # 宛先が特定されている場合
            if message.recipient_id:
                recipient = self.nodes.get(message.recipient_id)
                if not recipient:
                    logger.error(f"Recipient not found: {message.recipient_id}")
                    return False

                # 上位への報告か、下位への指令かチェック
                if sender.rank.value > recipient.rank.value:  # 上位への報告
                    logger.info(f"📤 Report from {sender.name} to {recipient.name}")
                elif sender.can_command(recipient):  # 下位への指令
                    logger.info(f"📥 Command from {sender.name} to {recipient.name}")
                else:
                    logger.warning(
                        f"⚠️ Unauthorized message from {sender.name} to {recipient.name}"
                    )
                    return False

            # メッセージをキューに追加
            self.message_queue.append(message)

            # 高優先度メッセージは即座に処理
            if message.priority == "high":
                await self._process_high_priority_message(message)

            return True

        except Exception as e:
            logger.error(f"Message send error: {e}")
            return False

    async def _process_high_priority_message(self, message: ElderMessage):
        """高優先度メッセージの処理"""
        if message.message_type == "emergency":
            # 緊急時は階層を飛び越えてグランドエルダーに直接報告
            await self._escalate_to_grand_elder(message)
        elif message.message_type == "council_summon":
            # 評議会召喚
            await self._summon_elder_council(message)

    async def _escalate_to_grand_elder(self, message: ElderMessage):
        """グランドエルダーへのエスカレーション"""
        logger.critical(f"🚨 ESCALATING TO GRAND ELDER: {message.content}")
        # グランドエルダーの緊急対応をシミュレート
        decision = ElderDecision(
            decision_id=f"emergency_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            decision_type="emergency_response",
            made_by=ElderRank.GRAND_ELDER,
            approved_by=["maru"],
            content={
                "action": "immediate_intervention",
                "original_message": message.content,
                "directive": "All hands on deck - resolve immediately",
            },
        )
        self.decision_log.append(decision)

    async def _summon_elder_council(self, message: ElderMessage):
        """エルダー評議会召喚"""
        logger.info(f"🏛️ SUMMONING ELDER COUNCIL: {message.content}")
        # 評議会メンバーを収集
        council_members = [
            node
            for node in self.nodes.values()
            if node.rank == ElderRank.COUNCIL_MEMBER
        ]

        # 評議会決定のシミュレート
        decision = ElderDecision(
            decision_id=f"council_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            decision_type="council_decision",
            made_by=ElderRank.COUNCIL_MEMBER,
            approved_by=[member.node_id for member in council_members],
            content={
                "topic": message.content.get("topic", "general"),
                "resolution": "Approved by Elder Council",
                "action_items": message.content.get("action_items", []),
            },
        )
        self.decision_log.append(decision)

    def get_command_chain(self, from_id: str, to_id: str) -> List[ElderTreeNode]:
        """指揮系統の取得"""
        from_node = self.nodes.get(from_id)
        to_node = self.nodes.get(to_id)

        if not from_node or not to_node:
            return []

        # 共通の祖先を見つける
        from_path = from_node.get_path_to_root()
        to_path = to_node.get_path_to_root()

        # 最短経路を計算
        command_chain = []

        # 上位への報告ルート
        if from_node.rank.value > to_node.rank.value:
            current = from_node
            while current and current != to_node:
                command_chain.append(current)
                current = current.parent
            if current:
                command_chain.append(current)

        # 下位への指令ルート
        else:
            # 共通祖先まで上がる
            current = from_node
            while current and current not in to_path:
                command_chain.append(current)
                current = current.parent

            # 共通祖先から下る
            if current:
                idx = to_path.index(current)
                command_chain.extend(to_path[idx:])

        return command_chain

    def visualize_hierarchy(self) -> str:
        """階層構造の可視化"""

        def _build_tree_string(
            node: ElderTreeNode, prefix: str = "", is_last: bool = True
        ) -> str:
            # 絵文字マッピング
            emoji_map = {
                ElderRank.GRAND_ELDER: "🌟",
                ElderRank.CLAUDE_ELDER: "🤖",
                ElderRank.SAGE: "🧙‍♂️",
                ElderRank.COUNCIL_MEMBER: "🏛️",
                ElderRank.SERVANT: "⚔️",
            }

            emoji = emoji_map.get(node.rank, "❓")
            connector = "└── " if is_last else "├── "
            result = f"{prefix}{connector}{emoji} {node.name} (Wisdom: {node.wisdom_level*100:.0f}%)\n"

            # 子ノードを追加
            children = node.children
            for i, child in enumerate(children):
                extension = "    " if is_last else "│   "
                result += _build_tree_string(
                    child, prefix + extension, i == len(children) - 1
                )

            return result

        if not self.root:
            return "No hierarchy initialized"

        return _build_tree_string(self.root)


# シングルトンインスタンス
_elder_tree_instance: Optional[ElderTreeHierarchy] = None


def get_elder_tree() -> ElderTreeHierarchy:
    """エルダーツリーのシングルトンインスタンスを取得"""
    global _elder_tree_instance
    if _elder_tree_instance is None:
        _elder_tree_instance = ElderTreeHierarchy()
    return _elder_tree_instance


# デモ実行
if __name__ == "__main__":

    async def demo():
        tree = get_elder_tree()

        print("🌳 Elder Tree Hierarchy:")
        print(tree.visualize_hierarchy())

        # メッセージ送信テスト
        # クロードエルダーからグランドエルダーへの報告
        message1 = ElderMessage(
            sender_rank=ElderRank.CLAUDE_ELDER,
            sender_id="claude",
            recipient_rank=ElderRank.GRAND_ELDER,
            recipient_id="maru",
            message_type="progress_report",
            content={
                "status": "Project World Wake initiated",
                "progress": "Phase 0 - Elder Tree implementation complete",
            },
        )

        await tree.send_message(message1)

        # インシデント賢者から緊急メッセージ
        message2 = ElderMessage(
            sender_rank=ElderRank.SAGE,
            sender_id="incident_sage",
            recipient_rank=ElderRank.GRAND_ELDER,
            recipient_id="maru",
            message_type="emergency",
            content={
                "severity": "critical",
                "issue": "Worker integration failure detected",
                "affected_workers": 10,
            },
            priority="high",
        )

        await tree.send_message(message2)

        # 指揮系統の確認
        chain = tree.get_command_chain("claude", "servant_incident_knight_0")
        print("\n📊 Command chain from Claude Elder to Incident Knight:")
        for node in chain:
            print(f"  → {node.name}")

    asyncio.run(demo())
