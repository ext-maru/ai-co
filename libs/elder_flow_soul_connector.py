#!/usr/bin/env python3
"""
🌊 Elder Flow + Elder Soul 連携システム
Elder Flow Soul Connector - A2A Integration Bridge

Elder FlowとElder Soulの統合により真のA2A協調を実現
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.elder_registry import ElderRegistry, AgentType, AgentStatus
from libs.elder_enforcement import ElderTreeEnforcement


class SoulSummonMode(Enum):
    """魂召喚モード"""

    COUNCIL = "council"  # 評議会モード（合議制）
    TEAM = "team"  # チームモード（協調作業）
    PARALLEL = "parallel"  # 並列モード（独立実行）
    SEQUENTIAL = "sequential"  # 逐次モード（順次実行）


@dataclass
class SoulTask:
    """魂への依頼タスク"""

    task_id: str
    description: str
    priority: str
    agent_type: str
    payload: Dict[str, Any]
    timeout: int = 30
    retry_count: int = 3


@dataclass
class SoulResponse:
    """魂からの応答"""

    task_id: str
    agent_id: str
    status: str
    result: Dict[str, Any]
    execution_time: float
    timestamp: datetime
    error_message: Optional[str] = None


class ElderFlowSoulConnector:
    """
    Elder Flow + Elder Soul 連携コネクター

    Elder FlowのステップごとにElder Soulのエージェント（魂）を
    呼び出し、A2A通信による真の協調作業を実現
    """

    def __init__(self):
        self.registry = ElderRegistry()
        self.enforcement = ElderTreeEnforcement()
        self.logger = self._setup_logger()

        # 活動中の魂セッション
        self.active_souls: Dict[str, Dict[str, Any]] = {}

        # Elder Flow専用エージェントマッピング
        self.soul_mapping = {
            # Phase 1: 4賢者会議
            "phase1_analysis": {
                "knowledge_sage": "技術知識分析・アーキテクチャ検討",
                "task_sage": "タスク分解・計画立案",
                "rag_sage": "関連情報検索・ベストプラクティス調査",
                "incident_sage": "リスク分析・障害予測",
            },
            # Phase 2: サーバント実行
            "phase2_execution": {
                "code_servant": "コード実装・アルゴリズム開発",
                "test_guardian": "テスト実装・品質保証",
                "quality_inspector": "コード品質検査・メトリクス分析",
            },
            # Phase 3: 品質ゲート
            "phase3_quality": {
                "security_auditor": "セキュリティ監査・脆弱性検査",
                "performance_monitor": "パフォーマンス測定・最適化",
                "documentation_keeper": "ドキュメント生成・維持",
            },
            # Phase 4: 評議会報告
            "phase4_reporting": {
                "council_secretary": "評議会記録・議事録作成",
                "report_generator": "レポート生成・メトリクス集約",
                "approval_manager": "承認処理・ワークフロー管理",
            },
            # Phase 5: Git自動化
            "phase5_git": {
                "git_master": "Git操作・バージョン管理",
                "version_guardian": "リリース管理・変更履歴",
                "deploy_manager": "デプロイ管理・環境制御",
            },
        }

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("elder_flow_soul")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            # ファイルハンドラー
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            file_handler = logging.FileHandler(log_dir / "elder_flow_soul.log")

            # コンソールハンドラー
            console_handler = logging.StreamHandler()

            # フォーマッター
            formatter = logging.Formatter(
                "%(asctime)s - ElderFlowSoul - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger

    async def initialize(self):
        """初期化"""
        self.logger.info("🌊 Initializing Elder Flow Soul Connector...")

        await self.registry.initialize()
        await self.enforcement.initialize()

        # Elder Flow専用エージェントの確認・作成
        await self._ensure_elder_flow_agents()

        self.logger.info("✅ Elder Flow Soul Connector initialized")

    async def summon_souls_for_phase(
        self, phase: str, task_description: str, priority: str = "medium"
    ) -> Dict[str, Any]:
        """
        Elder Flowフェーズ用魂召喚

        Args:
            phase: フェーズ名（phase1_analysis, phase2_execution, etc.）
            task_description: タスク説明
            priority: 優先度

        Returns:
            Dict: 召喚結果とセッション情報
        """
        self.logger.info(f"🌟 Summoning souls for {phase}: {task_description}")

        if phase not in self.soul_mapping:
            raise ValueError(f"Unknown phase: {phase}")

        required_souls = self.soul_mapping[phase]
        session_id = f"{phase}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 魂セッション開始
        session = {
            "session_id": session_id,
            "phase": phase,
            "task_description": task_description,
            "priority": priority,
            "souls": {},
            "started_at": datetime.now(),
            "status": "summoning",
        }

        # 各魂を召喚・起動
        summoned_souls = {}
        for soul_id, soul_purpose in required_souls.items():
            try:
                soul_info = await self._summon_soul(soul_id, soul_purpose, priority)
                summoned_souls[soul_id] = soul_info
                self.logger.info(f"  ✅ {soul_id} summoned: {soul_purpose}")

            except Exception as e:
                self.logger.error(f"  ❌ Failed to summon {soul_id}: {e}")
                summoned_souls[soul_id] = {"status": "failed", "error": str(e)}

        session["souls"] = summoned_souls
        session["status"] = (
            "active"
            if any(s.get("status") == "active" for s in summoned_souls.values())
            else "failed"
        )

        self.active_souls[session_id] = session

        return {
            "session_id": session_id,
            "phase": phase,
            "summoned_count": len(
                [s for s in summoned_souls.values() if s.get("status") == "active"]
            ),
            "total_souls": len(required_souls),
            "souls": summoned_souls,
        }

    async def execute_phase_with_souls(
        self,
        session_id: str,
        task_details: Dict[str, Any],
        execution_mode: SoulSummonMode = SoulSummonMode.TEAM,
    ) -> Dict[str, Any]:
        """
        魂を使用したフェーズ実行

        Args:
            session_id: 魂セッションID
            task_details: 実行タスクの詳細
            execution_mode: 実行モード

        Returns:
            Dict: 実行結果
        """
        if session_id not in self.active_souls:
            raise ValueError(f"Soul session not found: {session_id}")

        session = self.active_souls[session_id]
        phase = session["phase"]

        self.logger.info(
            f"🚀 Executing {phase} with {len(session['souls'])} souls in {execution_mode.value} mode"
        )

        execution_start = datetime.now()
        results = {}

        if execution_mode == SoulSummonMode.COUNCIL:
            # 評議会モード: 全魂で合議
            results = await self._execute_council_mode(session, task_details)

        elif execution_mode == SoulSummonMode.TEAM:
            # チームモード: 協調作業
            results = await self._execute_team_mode(session, task_details)

        elif execution_mode == SoulSummonMode.PARALLEL:
            # 並列モード: 独立並列実行
            results = await self._execute_parallel_mode(session, task_details)

        elif execution_mode == SoulSummonMode.SEQUENTIAL:
            # 逐次モード: 順次実行
            results = await self._execute_sequential_mode(session, task_details)

        execution_time = (datetime.now() - execution_start).total_seconds()

        # 実行結果をセッションに記録
        session["execution_result"] = {
            "mode": execution_mode.value,
            "execution_time": execution_time,
            "results": results,
            "completed_at": datetime.now(),
        }

        self.logger.info(f"✅ Phase {phase} completed in {execution_time:.2f}s")

        return {
            "session_id": session_id,
            "phase": phase,
            "execution_mode": execution_mode.value,
            "execution_time": execution_time,
            "success_count": len(
                [r for r in results.values() if r.get("status") == "success"]
            ),
            "total_tasks": len(results),
            "results": results,
        }

    async def dismiss_souls(self, session_id: str) -> Dict[str, Any]:
        """
        魂セッション終了

        Args:
            session_id: セッションID

        Returns:
            Dict: 終了結果
        """
        if session_id not in self.active_souls:
            return {"error": f"Session not found: {session_id}"}

        session = self.active_souls[session_id]

        self.logger.info(f"🌅 Dismissing souls for session {session_id}")

        # 各魂の状態記録とクリーンアップ
        dismiss_results = {}
        for soul_id, soul_info in session["souls"].items():
            if soul_info.get("status") == "active":
                try:
                    # エージェント停止は自動的に処理される（プロセス終了時）
                    dismiss_results[soul_id] = {
                        "status": "dismissed",
                        "timestamp": datetime.now(),
                    }
                    self.logger.info(f"  ✅ {soul_id} dismissed")
                except Exception as e:
                    dismiss_results[soul_id] = {"status": "error", "error": str(e)}
                    self.logger.error(f"  ❌ Error dismissing {soul_id}: {e}")

        # セッション記録保存
        await self._save_session_record(session_id, session)

        # アクティブセッションから削除
        del self.active_souls[session_id]

        return {
            "session_id": session_id,
            "dismissed_souls": len(dismiss_results),
            "dismiss_results": dismiss_results,
        }

    async def get_soul_session_status(
        self, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """魂セッション状態取得"""
        if session_id not in self.active_souls:
            return None

        session = self.active_souls[session_id]

        # 各魂の最新状態を確認
        soul_statuses = {}
        for soul_id, soul_info in session["souls"].items():
            if "agent_id" in soul_info:
                agent_status = await self.registry.get_agent_status(
                    soul_info["agent_id"]
                )
                soul_statuses[soul_id] = {
                    "status": agent_status.get("status", "unknown"),
                    "purpose": soul_info.get("purpose", ""),
                    "port": agent_status.get("port"),
                    "uptime": agent_status.get("uptime", 0),
                }

        return {
            "session_id": session_id,
            "phase": session["phase"],
            "status": session["status"],
            "task_description": session["task_description"],
            "started_at": session["started_at"],
            "souls": soul_statuses,
            "execution_result": session.get("execution_result"),
        }

    async def list_active_soul_sessions(self) -> List[Dict[str, Any]]:
        """アクティブ魂セッション一覧"""
        sessions = []
        for session_id, session in self.active_souls.items():
            sessions.append(
                {
                    "session_id": session_id,
                    "phase": session["phase"],
                    "status": session["status"],
                    "soul_count": len(session["souls"]),
                    "started_at": session["started_at"],
                }
            )
        return sessions

    # プライベートメソッド

    async def _ensure_elder_flow_agents(self):
        """Elder Flow専用エージェントの確認・作成"""
        required_agents = set()
        for phase_souls in self.soul_mapping.values():
            required_agents.update(phase_souls.keys())

        existing_agents = await self.registry.list_agents()
        existing_ids = {agent["agent_id"] for agent in existing_agents}

        missing_agents = required_agents - existing_ids

        if missing_agents:
            self.logger.info(
                f"Creating {len(missing_agents)} missing Elder Flow agents..."
            )

            for agent_id in missing_agents:
                await self._create_elder_flow_agent(agent_id)

    async def _create_elder_flow_agent(self, agent_id: str):
        """Elder Flow専用エージェント作成"""
        agent_configs = {
            # 賢者系
            "knowledge_sage": {
                "type": AgentType.SAGE,
                "desc": "Elder Flow技術知識分析エージェント",
            },
            "task_sage": {
                "type": AgentType.SAGE,
                "desc": "Elder Flowタスク管理エージェント",
            },
            "rag_sage": {
                "type": AgentType.SAGE,
                "desc": "Elder Flow情報検索エージェント",
            },
            "incident_sage": {
                "type": AgentType.SAGE,
                "desc": "Elder Flowリスク分析エージェント",
            },
            # サーバント系
            "code_servant": {
                "type": AgentType.SERVANT,
                "desc": "Elder Flowコード実装エージェント",
            },
            "test_guardian": {
                "type": AgentType.SERVANT,
                "desc": "Elder Flowテスト実装エージェント",
            },
            "quality_inspector": {
                "type": AgentType.SERVANT,
                "desc": "Elder Flow品質検査エージェント",
            },
            "documentation_keeper": {
                "type": AgentType.SERVANT,
                "desc": "Elder Flowドキュメント管理エージェント",
            },
            # 騎士系
            "security_auditor": {
                "type": AgentType.KNIGHT,
                "desc": "Elder Flowセキュリティ監査エージェント",
            },
            # エルフ系
            "performance_monitor": {
                "type": AgentType.ELF,
                "desc": "Elder Flowパフォーマンス監視エージェント",
            },
            # 評議会系
            "council_secretary": {
                "type": AgentType.COUNCIL,
                "desc": "Elder Flow評議会記録エージェント",
            },
            "report_generator": {
                "type": AgentType.SERVANT,
                "desc": "Elder Flowレポート生成エージェント",
            },
            "approval_manager": {
                "type": AgentType.COUNCIL,
                "desc": "Elder Flow承認管理エージェント",
            },
            "git_master": {
                "type": AgentType.SERVANT,
                "desc": "Elder Flow Git管理エージェント",
            },
            "version_guardian": {
                "type": AgentType.SERVANT,
                "desc": "Elder Flowバージョン管理エージェント",
            },
            "deploy_manager": {
                "type": AgentType.SERVANT,
                "desc": "Elder Flowデプロイ管理エージェント",
            },
        }

        if agent_id not in agent_configs:
            return

        config = agent_configs[agent_id]

        try:
            await self.registry.register_agent(
                agent_id=agent_id,
                name=agent_id.replace("_", " ").title(),
                description=config["desc"],
                agent_type=config["type"],
                capabilities=["elder_flow", "automation", "a2a_communication"],
                dependencies=[],
                auto_start=False,  # Elder Flow実行時に動的起動
            )
            self.logger.info(f"✅ Created Elder Flow agent: {agent_id}")

        except Exception as e:
            self.logger.error(f"❌ Failed to create agent {agent_id}: {e}")

    async def _summon_soul(
        self, soul_id: str, purpose: str, priority: str
    ) -> Dict[str, Any]:
        """個別魂召喚"""
        try:
            # エージェント起動
            success = await self.registry.start_agent(soul_id)

            if success:
                agent_status = await self.registry.get_agent_status(soul_id)
                return {
                    "agent_id": soul_id,
                    "purpose": purpose,
                    "status": "active",
                    "port": agent_status.get("port"),
                    "summoned_at": datetime.now(),
                }
            else:
                raise Exception(f"Failed to start agent {soul_id}")

        except Exception as e:
            self.logger.error(f"Failed to summon soul {soul_id}: {e}")
            return {
                "agent_id": soul_id,
                "status": "failed",
                "error": str(e),
                "summoned_at": datetime.now(),
            }

    async def _execute_council_mode(
        self, session: Dict[str, Any], task_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """評議会モード実行"""
        self.logger.info("🏛️ Executing in Council mode (consensus-based)")

        # すべての魂で合議制の処理
        active_souls = [
            s for s in session["souls"].values() if s.get("status") == "active"
        ]

        if not active_souls:
            return {"error": "No active souls for council"}

        # シミュレート: 各魂からの提案と合議
        proposals = {}
        for soul in active_souls:
            soul_id = soul["agent_id"]
            # 実際の実装では各エージェントとA2A通信
            proposals[soul_id] = {
                "proposal": f"Proposal from {soul_id} for {task_details.get(
                    'description',
                    'task'
                )}",
                "confidence": 0.8,
                "estimated_time": 30,
                "resources_needed": ["time", "compute"],
            }

        # 合議による最終決定
        consensus = {
            "decision": "Proceed with implementation",
            "participating_souls": list(proposals.keys()),
            "consensus_score": 0.85,
            "action_plan": task_details,
        }

        return {"mode": "council", "proposals": proposals, "consensus": consensus}

    async def _execute_team_mode(
        self, session: Dict[str, Any], task_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """チームモード実行"""
        self.logger.info("👥 Executing in Team mode (collaborative)")

        # 協調作業での実行
        active_souls = [
            s for s in session["souls"].values() if s.get("status") == "active"
        ]

        team_results = {}
        for soul in active_souls:
            soul_id = soul["agent_id"]
            # 実際の実装では各エージェントに協調タスクを配布
            team_results[soul_id] = {
                "task_assigned": f"Collaborative task for {soul_id}",
                "status": "completed",
                "contribution": f"Contribution from {soul_id}",
                "collaboration_score": 0.9,
            }

        return {"mode": "team", "team_results": team_results}

    async def _execute_parallel_mode(
        self, session: Dict[str, Any], task_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """並列モード実行"""
        self.logger.info("⚡ Executing in Parallel mode (independent)")

        # 並列独立実行
        active_souls = [
            s for s in session["souls"].values() if s.get("status") == "active"
        ]

        parallel_tasks = []
        for soul in active_souls:
            soul_id = soul["agent_id"]
            # 実際の実装では各エージェントに並列タスクを送信
            task = asyncio.create_task(self._execute_soul_task(soul_id, task_details))
            parallel_tasks.append((soul_id, task))

        # 並列実行完了を待機
        parallel_results = {}
        for soul_id, task in parallel_tasks:
            try:
                result = await task
                parallel_results[soul_id] = result
            except Exception as e:
                parallel_results[soul_id] = {"status": "failed", "error": str(e)}

        return {"mode": "parallel", "parallel_results": parallel_results}

    async def _execute_sequential_mode(
        self, session: Dict[str, Any], task_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """逐次モード実行"""
        self.logger.info("📋 Executing in Sequential mode (ordered)")

        # 順次実行
        active_souls = [
            s for s in session["souls"].values() if s.get("status") == "active"
        ]

        sequential_results = {}
        previous_result = None

        for soul in active_souls:
            soul_id = soul["agent_id"]

            # 前の結果を次のタスクに引き継ぎ
            enhanced_task = {**task_details}
            if previous_result:
                enhanced_task["previous_result"] = previous_result

            result = await self._execute_soul_task(soul_id, enhanced_task)
            sequential_results[soul_id] = result
            previous_result = result

        return {"mode": "sequential", "sequential_results": sequential_results}

    async def _execute_soul_task(
        self, soul_id: str, task_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """個別魂タスク実行"""
        # シミュレーション: 実際の実装ではA2A通信でタスク実行
        await asyncio.sleep(0.1)  # 処理時間シミュレート

        return {
            "soul_id": soul_id,
            "status": "completed",
            "result": f"Task completed by {soul_id}",
            "execution_time": 0.1,
            "timestamp": datetime.now(),
        }

    async def _save_session_record(self, session_id: str, session: Dict[str, Any]):
        """セッション記録保存"""
        try:
            records_dir = Path("data/elder_flow_sessions")
            records_dir.mkdir(parents=True, exist_ok=True)

            record_file = records_dir / f"{session_id}.json"

            # JSON保存用にdatetimeを文字列に変換
            session_copy = session.copy()
            session_copy["started_at"] = session_copy["started_at"].isoformat()

            if (
                "execution_result" in session_copy
                and "completed_at" in session_copy["execution_result"]
            ):
                session_copy["execution_result"]["completed_at"] = session_copy[
                    "execution_result"
                ]["completed_at"].isoformat()

            with open(record_file, "w", encoding="utf-8") as f:
                json.dump(session_copy, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"📝 Session record saved: {record_file}")

        except Exception as e:
            self.logger.error(f"Failed to save session record: {e}")


# グローバルインスタンス
_connector_instance: Optional[ElderFlowSoulConnector] = None


async def get_elder_flow_soul_connector() -> ElderFlowSoulConnector:
    """Elder Flow Soul Connector取得"""
    global _connector_instance

    if _connector_instance is None:
        _connector_instance = ElderFlowSoulConnector()
        await _connector_instance.initialize()

    return _connector_instance


# 便利な関数


async def summon_souls_for_elder_flow(
    phase: str, task_description: str, priority: str = "medium"
) -> Dict[str, Any]:
    """Elder Flow用魂召喚（便利関数）"""
    connector = await get_elder_flow_soul_connector()
    return await connector.summon_souls_for_phase(phase, task_description, priority)


async def execute_elder_flow_phase(
    session_id: str, task_details: Dict[str, Any], mode: str = "team"
) -> Dict[str, Any]:
    """Elder Flowフェーズ実行（便利関数）"""
    connector = await get_elder_flow_soul_connector()
    execution_mode = SoulSummonMode(mode)
    return await connector.execute_phase_with_souls(
        session_id, task_details, execution_mode
    )


async def dismiss_elder_flow_souls(session_id: str) -> Dict[str, Any]:
    """Elder Flow魂解散（便利関数）"""
    connector = await get_elder_flow_soul_connector()
    return await connector.dismiss_souls(session_id)


# デモ・テスト用の関数
async def demo_elder_flow_soul_integration():
    """Elder Flow + Elder Soul統合デモ"""
    print("🌊 Elder Flow + Elder Soul Integration Demo")
    print("=" * 50)

    connector = await get_elder_flow_soul_connector()

    # Phase 1: 4賢者会議召喚
    print("\n🧙‍♂️ Phase 1: Summoning 4 Sages for Analysis...")
    session_result = await connector.summon_souls_for_phase(
        "phase1_analysis", "OAuth2.0認証システム実装", "high"
    )

    print(
        f"✅ Summoned {session_result['summoned_count']}/{session_result['total_souls']} souls"
    )
    session_id = session_result["session_id"]

    # 実行
    print("\n🚀 Executing analysis phase...")
    execution_result = await connector.execute_phase_with_souls(
        session_id,
        {
            "description": "OAuth2.0システム分析",
            "requirements": ["security", "scalability"],
        },
        SoulSummonMode.COUNCIL,
    )

    print(
        f"✅ Analysis completed: {execution_result['success_count']}/{execution_result['total_tasks']} tasks successful"
    )

    # 状態確認
    print("\n📊 Session Status:")
    status = await connector.get_soul_session_status(session_id)
    if status:
        print(f"  Phase: {status['phase']}")
        print(
            f"  Active Souls: {len([s for s in status['souls'].values() if s.get('status') == 'active'])}"
        )

    # 解散
    print("\n🌅 Dismissing souls...")
    dismiss_result = await connector.dismiss_souls(session_id)
    print(f"✅ Dismissed {dismiss_result['dismissed_souls']} souls")

    print("\n🎉 Elder Flow + Elder Soul Integration Demo Completed!")


if __name__ == "__main__":
    asyncio.run(demo_elder_flow_soul_integration())
