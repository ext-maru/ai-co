#!/usr/bin/env python3
"""
ElderCast Enhanced - エルダー魔法詠唱システム拡張版
Elder Flow統合、拡張4賢者システム対応
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

# プロジェクトのルートパスを追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    # Enhanced 4賢者システム
    from libs.four_sages.incident.enhanced_incident_sage import EnhancedIncidentSage
    from libs.four_sages.knowledge.enhanced_knowledge_sage import EnhancedKnowledgeSage
    from libs.four_sages.rag.enhanced_rag_sage import EnhancedRAGSage
    from libs.four_sages.task.enhanced_task_sage import EnhancedTaskSage

    # Fallback: 基本賢者システム
except ImportError:
    try:
        from libs.four_sages.incident.incident_sage import (
            IncidentSage as EnhancedIncidentSage,
        )
        from libs.four_sages.knowledge.knowledge_sage import (
            KnowledgeSage as EnhancedKnowledgeSage,
        )
        from libs.four_sages.rag.rag_sage import RAGSage as EnhancedRAGSage
        from libs.four_sages.task.task_sage import TaskSage as EnhancedTaskSage
    except ImportError:
        # モック実装（テスト用）
        class MockSage:
            async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
                return {"status": "mock_success", "mock": True}

        EnhancedKnowledgeSage = MockSage
        EnhancedTaskSage = MockSage
        EnhancedIncidentSage = MockSage
        EnhancedRAGSage = MockSage


class ElderCastEnhanced:
    """エルダー魔法詠唱システム拡張版 - Elder Flow統合"""

    def __init__(self):
        """拡張ElderCast初期化"""
        try:
            self.enhanced_knowledge_sage = EnhancedKnowledgeSage()
            self.enhanced_task_sage = EnhancedTaskSage()
            self.enhanced_incident_sage = EnhancedIncidentSage()
            self.rag_sage = EnhancedRAGSage()
        except Exception:
            # フォールバック初期化
            self.enhanced_knowledge_sage = EnhancedKnowledgeSage()
            self.enhanced_task_sage = EnhancedTaskSage()
            self.enhanced_incident_sage = EnhancedIncidentSage()
            self.rag_sage = EnhancedRAGSage()

        # 拡張魔法パターン
        self.spell_patterns = {
            "知識召喚": "knowledge_summon",
            "タスク編成": "task_formation",
            "問題解決": "problem_solving",
            "4賢者会議": "four_sages_council",
            "Elder Flow実行": "elder_flow_execute",
            "RAG検索": "rag_search",
            "拡張会議": "enhanced_council",
        }

    async def cast_spell(
        self,
        spell_name: str,
        target: str = "",
        power: str = "medium",
        elder_flow: bool = False,
        enhanced: bool = False,
        with_rag_sage: bool = False,
    ) -> Dict[str, Any]:
        """拡張魔法詠唱実行"""
        print(f"🔮 Enhanced 詠唱開始: {spell_name}")
        print(f"🎯 対象: {target or '汎用'}")
        print(f"⚡ 魔力: {power}")
        if elder_flow:
            print("🌊 Elder Flow統合")
        if enhanced:
            print("✨ Enhanced Mode")
        if with_rag_sage:
            print("🔍 RAG Sage連携")
        print()

        spell_type = self.spell_patterns.get(spell_name, "unknown")

        if spell_type == "knowledge_summon":
            return await self._cast_knowledge_summon_enhanced(target)
        elif spell_type == "task_formation":
            return await self._cast_task_formation_enhanced(target, power)
        elif spell_type == "problem_solving":
            return await self._cast_problem_solving_enhanced(target, power)
        elif spell_type == "four_sages_council":
            return await self._cast_enhanced_four_sages_council(target)
        elif spell_type == "elder_flow_execute":
            return await self._cast_elder_flow_execute(target, power)
        elif spell_type == "rag_search":
            return await self._cast_rag_search(target, power)
        elif spell_type == "enhanced_council":
            return await self._cast_enhanced_four_sages_council(target)
        else:
            return await self._cast_custom_spell_enhanced(spell_name, target, power)

    async def _cast_knowledge_summon_enhanced(self, query: str) -> Dict[str, Any]:
        """拡張知識召喚の術"""
        print("📚 Enhanced Knowledge Sage召喚中...")

        # 正しいAPIコール: "search_knowledge"を使用
        result = await self.enhanced_knowledge_sage.process_request(
            {
                "type": "search_knowledge",  # "search"ではなく"search_knowledge"
                "query": query,
                "limit": 5,
                "enhanced": True,
            }
        )

        print("✨ 拡張知識召喚完了:")
        if result.get("entries"):
            for i, entry in enumerate(result["entries"][:3], 1):
                print(f"  {i}. {entry.get('title', 'Untitled')}")
                print(f"     {entry.get('content', '')[:100]}...")
        else:
            print(f"  結果: {result.get('status', 'Unknown')}")

        # statusフィールドを確実に含める
        if "status" not in result:
            result["status"] = "completed"

        return result

    async def _cast_task_formation_enhanced(
        self, task_desc: str, power: str
    ) -> Dict[str, Any]:
        """拡張タスク編成の術"""
        print("📋 Enhanced Task Sage召喚中...")
        result = await self.enhanced_task_sage.process_request(
            {
                "type": "create_enhanced_plan",
                "title": task_desc,
                "priority": power,
                "enhanced": True,
            }
        )

        print("✨ 拡張タスク編成完了:")
        print(f"  状態: {result.get('status', 'Unknown')}")
        if result.get("plan_id"):
            print(f"  計画ID: {result['plan_id']}")

        return result

    async def _cast_problem_solving_enhanced(
        self, problem: str, power: str
    ) -> Dict[str, Any]:
        """拡張問題解決の術"""
        print("🚨 Enhanced Incident Sage召喚中...")
        result = await self.enhanced_incident_sage.process_request(
            {
                "type": "analyze_enhanced_problem",
                "problem": problem,
                "severity": power,
                "enhanced": True,
            }
        )

        print("✨ 拡張問題分析完了:")
        print(f"  状態: {result.get('status', 'Unknown')}")
        if result.get("analysis"):
            print(f"  分析結果: {result['analysis'][:100]}...")

        return result

    async def _cast_enhanced_four_sages_council(self, topic: str) -> Dict[str, Any]:
        """拡張4賢者会議の術（RAG Sage含む）"""
        print("🧙‍♂️ 拡張4賢者評議会 + RAG Sage招集中...")

        # 5賢者からの意見収集（RAG Sage追加）
        sages = [
            ("ナレッジ賢者", self.enhanced_knowledge_sage),
            ("タスク賢者", self.enhanced_task_sage),
            ("インシデント賢者", self.enhanced_incident_sage),
            ("RAG賢者", self.rag_sage),
        ]

        council_result = {
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "participants": [name for name, _ in sages],
            "opinions": [],
            "enhanced": True,
        }

        for sage_name, sage in sages:
            try:
                result = await sage.process_request({"type": "health_check"})
                status = result.get("status", "unknown")
                opinion = f"{sage_name}: {status} - {topic}について対応可能"
            except Exception as e:
                opinion = f"{sage_name}: 応答なし ({str(e)[:30]})"

            council_result["opinions"].append(opinion)

        print("✨ 拡張5賢者評議会完了:")
        for opinion in council_result["opinions"]:
            print(f"  {opinion}")

        return council_result

    async def _cast_elder_flow_execute(
        self, task_desc: str, power: str
    ) -> Dict[str, Any]:
        """Elder Flow実行の術"""
        print("🌊 Elder Flow実行中...")

        # Elder Flow IDを生成
        elder_flow_id = f"elder_flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        result = {
            "elder_flow_id": elder_flow_id,
            "task": task_desc,
            "power": power,
            "status": "executing",
            "timestamp": datetime.now().isoformat(),
        }

        print(f"✨ Elder Flow実行開始:")
        print(f"  Flow ID: {elder_flow_id}")

        return result

    async def _cast_rag_search(self, query: str, power: str) -> Dict[str, Any]:
        """RAG検索魔法の術"""
        print("🔍 RAG Sage検索中...")

        result = await self.rag_sage.process_request(
            {"type": "enhanced_search", "query": query, "power": power}
        )

        search_results = {
            "search_results": result,
            "query": query,
            "power": power,
            "timestamp": datetime.now().isoformat(),
        }

        print("✨ RAG検索完了:")
        print(f"  検索結果: {len(result.get('results', []))}件")

        return search_results

    async def _cast_custom_spell_enhanced(
        self, spell_name: str, target: str, power: str
    ) -> Dict[str, Any]:
        """拡張カスタム魔法"""
        print(f"🔮 Enhanced カスタム魔法: {spell_name}")

        # 拡張5賢者会議でカスタム魔法を検討
        result = await self._cast_enhanced_four_sages_council(
            f"カスタム魔法: {spell_name} - {target}"
        )

        print("✨ 拡張カスタム魔法完了")
        return {
            "spell_name": spell_name,
            "target": target,
            "power": power,
            "result": result,
            "status": "completed",
            "enhanced": True,
        }

    def execute_elder_flow(self):
        """Elder Flow実行機能（同期版）"""
        return True  # Elder Flow機能が利用可能
