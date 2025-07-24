#!/usr/bin/env python3
"""
Mind Reading + RAG Elder 統合システム
精度向上のための協力フレームワーク

🧠 Mind Reading Protocol + "🔍" RAG Elder Wizards = 🌟 Ultimate Understanding
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict

# Mind Reading Protocol
try:
    from libs.mind_reading_core import MindReadingCore, IntentResult, IntentType
    from libs.intent_parser import IntentParser, ParsedCommand
    from libs.learning_data_collector import LearningDataCollector
except ImportError:
    print("⚠️ Mind Reading Protocol not available")
    MindReadingCore = None

# RAG Elder Wizards
try:
    from libs.rag_elder_wizards import (
        RAGElderWizardsOrchestrator,
        KnowledgeGap,
        KnowledgeGapType,
        InformationHunterWizard
    )
except ImportError:
    print("⚠️ RAG Elder Wizards not available")
    RAGElderWizardsOrchestrator = None


@dataclass
class AccuracyImprovement:
    """精度向上記録"""
    improvement_id: str
    original_confidence: float
    enhanced_confidence: float
    improvement_factor: float
    rag_context: Dict[str, Any]
    timestamp: str


@dataclass
class RAGEnhancedIntent:
    """RAG強化された意図理解結果"""
    original_intent: IntentResult
    rag_context: Dict[str, Any]
    enhanced_confidence: float
    contextual_keywords: List[str]
    related_patterns: List[str]
    improvement: AccuracyImprovement


class MindReadingRAGIntegration:
    """Mind Reading Protocol + RAG Elder統合システム"""

    def __init__(self):
        self.logger = self._setup_logger()

        # コンポーネント初期化
        self.mind_reader = None
        self.intent_parser = None
        self.learning_collector = None
        self.rag_orchestrator = None

        # 統合統計
        self.integration_stats = {
            "total_enhancements": 0,
            "successful_improvements": 0,
            "average_improvement": 0.0,
            "context_hit_rate": 0.0
        }

        self.improvement_history: List[AccuracyImprovement] = []

        self.logger.info("🌟 Mind Reading + RAG Integration initialized")

    def _setup_logger(self) -> logging.Loggerlogger = logging.getLogger("mind_reading_rag_integration")
    """ロガー設定"""
        logger.setLevel(logging.INFO)
:
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - MR+RAG Integration - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def initialize_components(self)self.logger.info("🚀 Initializing integrated components...")
    """全コンポーネントを初期化"""

        # Mind Reading Protocol初期化
        if MindReadingCore:
            self.mind_reader = MindReadingCore()
            self.intent_parser = IntentParser()
            self.learning_collector = LearningDataCollector()
            self.logger.info("✅ Mind Reading Protocol initialized")
        else:
            self.logger.warning("❌ Mind Reading Protocol not available")

        # RAG Elder Wizards初期化
        if RAGElderWizardsOrchestrator:
            self.rag_orchestrator = RAGElderWizardsOrchestrator()
            await self.rag_orchestrator.start()
            self.logger.info("✅ RAG Elder Wizards initialized")
        else:
            self.logger.warning("❌ RAG Elder Wizards not available")

        return self.mind_reader is not None and self.rag_orchestrator is not None

    async def enhanced_intent_understanding(self, text: str) -> RAGEnhancedIntent:
        """
        RAG強化された意図理解

        Args:
            text: グランドエルダーmaruからの入力テキスト

        Returns:
            RAGEnhancedIntent: RAG強化された意図理解結果
        """
        self.logger.info(f"🧠🔍 Enhanced understanding: {text[:50]}...")

        # 1.0 基本的な意図理解
        original_intent = await self.mind_reader.understand_intent(text)
        self.logger.info(f"Original confidence: {original_intent.confidence:0.2%}")

        # 2.0 RAGによる文脈検索・補強
        rag_context = await self._gather_rag_context(text, original_intent)

        # 3.0 文脈を考慮した信頼度再計算
        enhanced_confidence = await self._calculate_enhanced_confidence(
            original_intent, rag_context
        )

        # 4.0 文脈キーワードと関連パターンの抽出
        contextual_keywords = await self._extract_contextual_keywords(rag_context)
        related_patterns = await self._find_related_patterns(rag_context)

        # 5.0 改善度の記録
        improvement = AccuracyImprovement(
            improvement_id=f"improve_{datetime.now().timestamp()}",
            original_confidence=original_intent.confidence,
            enhanced_confidence=enhanced_confidence,
            improvement_factor=enhanced_confidence / max(original_intent.confidence, 0.1),
            rag_context=rag_context,
            timestamp=datetime.now().isoformat()
        )

        # 6.0 統計更新
        self._update_integration_stats(improvement)

        enhanced_intent = RAGEnhancedIntent(
            original_intent=original_intent,
            rag_context=rag_context,
            enhanced_confidence=enhanced_confidence,
            contextual_keywords=contextual_keywords,
            related_patterns=related_patterns,
            improvement=improvement
        )

                self.logger.info(f"Enhanced confidence: {enhanced_confidence:0.2%} \
            (improvement: {improvement.improvement_factor:0.2f}x)")

        return enhanced_intent

    async def _gather_rag_context(self, text: str, intent: IntentResult) -> Dict[str, Any]:
        """RAGによる文脈情報収集"""
        context = {
            "historical_patterns": [],
            "similar_intents": [],
            "contextual_knowledge": [],
            "execution_history": [],
            "success_patterns": []
        }

        try:
            # 1.0 類似意図の履歴検索
            if self.learning_collector:
                similar_executions = await self.learning_collector.get_similar_executions(
                    intent.intent_type,
                    None,  # command_type未定のため
                    limit=5
                )
                context["similar_intents"] = similar_executions

            # 2.0 RAGエルダーによる知識検索
            if self.rag_orchestrator:
                # 意図タイプに関連する知識を検索
                knowledge_gap = KnowledgeGap(
                    gap_id=f"context_{intent.intent_type.value}",
                    gap_type=KnowledgeGapType.MISSING_CONTEXT,
                    topic=f"{intent.intent_type.value} patterns",
                    description=f"Context search for {intent.intent_type.value}",
                    priority=0.8,
                    detected_at=datetime.now(),
                    context={"original_text": text}
                )

                # 利用可能なハンターウィザードで情報収集
                available_wizard = next(
                    (w for w in self.rag_orchestrator.hunter_wizards
                     if hasattr(w, 'state') and w.state.value == 'idle'),
                    None
                )

                if available_wizard:
                    hunt_results = await available_wizard.hunt_for_information(knowledge_gap)
                    context["contextual_knowledge"] = hunt_results.get("findings", [])

            # 3.0 キーワードベースの履歴検索
            historical_patterns = await self._search_historical_patterns(intent.extracted_keywords)
            context["historical_patterns"] = historical_patterns

            # 4.0 成功パターンの取得
            if self.learning_collector:
                success_patterns = await self.learning_collector.get_success_patterns(intent.intent_type)
                context["success_patterns"] = success_patterns[:3]  # 上位3パターン

        except Exception as e:
            self.logger.error(f"RAG context gathering error: {e}")

        return context

    async def _search_historical_patterns(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """履歴パターンの検索"""
        patterns = []

        try:
            # グランドエルダーmaruの過去の指示パターンを検索
            knowledge_base_path = Path("/home/aicompany/ai_co/knowledge_base")

            # キーワードマッチングで関連ドキュメントを検索
            for doc_path in knowledge_base_path.rglob("*.md"):
                try:
                    content = doc_path.read_text(encoding='utf-8')

                    # キーワードとのマッチング
                    matches = sum(1 for keyword in keywords if keyword.lower() in content.lower())

                    if matches > 0:
                        patterns.append({
                            "document": doc_path.name,
                            "path": str(doc_path),
                            "keyword_matches": matches,
                            "content_preview": content[:200] + "..." if len(content) > 200 else content
                        })

                except Exception as e:
                    self.logger.debug(f"Pattern search error for {doc_path}: {e}")

            # マッチ数でソート
            patterns.sort(key=lambda x: x["keyword_matches"], reverse=True)

        except Exception as e:
            self.logger.error(f"Historical pattern search error: {e}")

        return patterns[:5]  # 上位5件

    async def _calculate_enhanced_confidence(self, intent: IntentResult, rag_context: Dict[str, Any]) -> float:
        """RAG文脈を考慮した信頼度計算"""
        base_confidence = intent.confidence
        enhancement_factor = 1.0

        try:
            # 1.0 類似意図の成功率による補正
            similar_intents = rag_context.get("similar_intents", [])
            if similar_intents:
                success_count = sum(1 for s in similar_intents if hasattr(s, 'status') and s.status.value == 'success')
                success_rate = success_count / len(similar_intents)
                enhancement_factor *= (1 + success_rate * 0.2)  # 最大20%向上

            # 2.0 文脈知識の豊富さによる補正
            contextual_knowledge = rag_context.get("contextual_knowledge", [])
            if contextual_knowledge:
                knowledge_confidence = sum(
                    k.get("confidence",
                    0.5) for k in contextual_knowledge) / len(contextual_knowledge
                )
                enhancement_factor *= (1 + knowledge_confidence * 0.15)  # 最大15%向上

            # 3.0 歴史パターンマッチによる補正
            historical_patterns = rag_context.get("historical_patterns", [])
            if historical_patterns:
                max_matches = max((p.get("keyword_matches", 0) for p in historical_patterns), default=0)
                if max_matches > 2:
                    enhancement_factor *= (1 + min(max_matches * 0.05, 0.25))  # 最大25%向上

            # 4.0 成功パターンによる補正
            success_patterns = rag_context.get("success_patterns", [])
            if success_patterns:
                avg_success_rate = sum(p.success_count / max(p.success_count + p.failure_count, 1)
                                     for p in success_patterns) / len(success_patterns)
                enhancement_factor *= (1 + avg_success_rate * 0.1)  # 最大10%向上

        except Exception as e:
            self.logger.error(f"Enhanced confidence calculation error: {e}")

        # 最終信頼度計算（最大1.0に制限）
        enhanced_confidence = min(base_confidence * enhancement_factor, 1.0)
        return enhanced_confidence

    async def _extract_contextual_keywords(self, rag_context: Dict[str, Any]) -> List[str]keywords = set()
    """文脈キーワードの抽出"""
:
        try:
            # 文脈知識からキーワード抽出
            contextual_knowledge = rag_context.get("contextual_knowledge", [])
            for knowledge in contextual_knowledge:
                content = knowledge.get("content", "")
                # 簡易キーワード抽出（実際の実装ではより高度な処理）
                words = content.lower().split()
                keywords.update(w for w in words if len(w) > 3 and w.isalnum())

            # 履歴パターンからキーワード抽出
            historical_patterns = rag_context.get("historical_patterns", [])
            for pattern in historical_patterns:
                content = pattern.get("content_preview", "")
                words = content.lower().split()
                keywords.update(w for w in words if len(w) > 3 and w.isalnum())

        except Exception as e:
            self.logger.error(f"Contextual keyword extraction error: {e}")

        return list(keywords)[:10]  # 上位10個

    async def _find_related_patterns(self, rag_context: Dict[str, Any]) -> List[str]:
        """関連パターンの発見"""
        patterns = []

        try:
            # 成功パターンから関連性を抽出
            success_patterns = rag_context.get("success_patterns", [])
            for pattern in success_patterns:
                if hasattr(pattern, 'common_parameters') and pattern.common_parameters:
                    patterns.append(f"Success pattern: {pattern.pattern_type}")

            # 履歴パターンから関連性を抽出
            historical_patterns = rag_context.get("historical_patterns", [])
            for pattern in historical_patterns[:3]:  # 上位3件
                patterns.append(f"Historical: {pattern.get('document', 'unknown')}")

        except Exception as e:
            self.logger.error(f"Related pattern discovery error: {e}")

        return patterns

    def _update_integration_stats(self, improvement: AccuracyImprovement):
        """統合統計の更新"""
        self.integration_stats["total_enhancements"] += 1

        if improvement.improvement_factor > 1.0:
            self.integration_stats["successful_improvements"] += 1

        # 平均改善度の更新
        total = self.integration_stats["total_enhancements"]
        if total > 0:
            old_avg = self.integration_stats["average_improvement"]
            new_improvement = improvement.improvement_factor
            self.integration_stats["average_improvement"] = (old_avg * (total - 1) + new_improvement) / total

        # 文脈ヒット率の更新（簡易版）
        context_items = len(improvement.rag_context.get("contextual_knowledge", []))
        if context_items > 0:
            hit_count = sum(
                1 for _ in self.improvement_history if len(_.rag_context.get("contextual_knowledge",
                [])) > 0
            )
            self.integration_stats["context_hit_rate"] = hit_count / total

        # 履歴に追加
        self.improvement_history.append(improvement)

    async def get_precision_enhancement_report(self) -> Dict[str, Any]:
        """精度向上レポートの生成"""
        if not self.improvement_history:
            return {"message": "No enhancement data available"}

        # 統計計算
        improvements = [i.improvement_factor for i in self.improvement_history]
        successful_improvements = [i for i in improvements if i > 1.0]

        report = {
            "total_enhancements": len(self.improvement_history),
            "successful_enhancements": len(successful_improvements),
            "success_rate": len(successful_improvements) / len(improvements) if improvements else 0,
            "average_improvement": sum(improvements) / len(improvements) if improvements else 0,
            "max_improvement": max(improvements) if improvements else 0,
            "latest_improvements": [
                {
                    "timestamp": i.timestamp,
                    "original_confidence": i.original_confidence,
                    "enhanced_confidence": i.enhanced_confidence,
                    "improvement_factor": i.improvement_factor
                }
                for i in self.improvement_history[-5:]  # 最新5件
            ],
            "integration_stats": self.integration_stats
        }

        return report

    async def suggest_accuracy_improvements(self) -> List[str]:
        """精度向上のための提案"""
        suggestions = []

        try:
            # 1.0 データ不足の分析
            if self.integration_stats["total_enhancements"] < 10:
                suggestions.append("More training data needed - collect diverse intent examples")

            # 2.0 文脈ヒット率の分析
            if self.integration_stats["context_hit_rate"] < 0.5:
                suggestions.append("Improve RAG knowledge base - add more contextual documents")

            # 3.0 改善率の分析
            if self.integration_stats["average_improvement"] < 1.1:
                suggestions.append("Enhance RAG search algorithms - implement semantic search")

            # 4.0 失敗パターンの分析
            recent_failures = [
                i for i in self.improvement_history[-10:]
                if i.improvement_factor <= 1.0
            ]

            if len(recent_failures) > 5:
                suggestions.append("Analyze failure patterns - improve intent classification rules")

            # 5.0 成功パターンの活用
            if self.integration_stats["successful_improvements"] > 0:
                suggestions.append("Leverage successful patterns - create template-based enhancements")

        except Exception as e:
            self.logger.error(f"Suggestion generation error: {e}")
            suggestions.append("System analysis error - manual review needed")

        return suggestions if suggestions else ["System performing well - continue current approach"]

    async def close(self):
        """リソースのクリーンアップ"""
        if self.rag_orchestrator:
            await self.rag_orchestrator.stop()

        self.logger.info("Mind Reading + RAG Integration closed")


# デモンストレーション
async def demo_integration()print("🌟 Mind Reading + RAG Elder Integration Demo")
"""統合システムのデモ"""
    print("=" * 60)

    integration = MindReadingRAGIntegration()

    try:
        # 初期化
        if not await integration.initialize_components():
            print("❌ Component initialization failed")
            return

        print("✅ All components initialized successfully!")
        print()

        # テストケース
        test_cases = [
            "Elder FlowでOAuth2.0認証システムを実装してください",
            "今すぐ重要なバグを修正して",
            "パフォーマンス最適化を行いたい",
            "素晴らしい実装ですね！継続してください",
            "AIシステムの監視機能を強化"
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"[Test {i}] \"{test_case}\"")

            # RAG強化された意図理解
            enhanced_intent = await integration.enhanced_intent_understanding(test_case)

            print(f"   🧠 Original: {enhanced_intent.original_intent." \
                "intent_type.value} ({enhanced_intent.original_intent.confidence:0.2%})")
            print(f"   🌟 Enhanced: {enhanced_intent.enhanced_confidence:." \
                "2%} (x{enhanced_intent.improvement.improvement_factor:0.2f})")
            print(f"   🔍 Context: {len(enhanced_intent.rag_context['contextual_knowledge'])} items")
            print(f"   📊 Keywords: {len(enhanced_intent.contextual_keywords)} contextual")
            print()

        # 精度向上レポート
        print("📊 Precision Enhancement Report:")
        report = await integration.get_precision_enhancement_report()

        print(f"   Total Enhancements: {report['total_enhancements']}")
        print(f"   Success Rate: {report['success_rate']:0.1%}")
        print(f"   Average Improvement: {report['average_improvement']:0.2f}x")
        print(f"   Max Improvement: {report['max_improvement']:0.2f}x")
        print()

        # 改善提案
        print("💡 Accuracy Improvement Suggestions:")
        suggestions = await integration.suggest_accuracy_improvements()
        for suggestion in suggestions:
            print(f"   • {suggestion}")

    finally:
        await integration.close()

    print("\n✨ Integration Demo Complete!")


if __name__ == "__main__":
    asyncio.run(demo_integration())
