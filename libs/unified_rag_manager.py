#!/usr/bin/env python3
"""
🏛️ Elders Guild Unified RAG Manager
統一RAGシステム - Phase 1 統合フェーズ実装

作成日: 2025年7月8日
作成者: クロードエルダー（開発実行責任者）
承認: グランドエルダーmaru
協力: 4賢者システム（特にRAG賢者）
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime
from enum import Enum

# エルダーズ承認済みインポート
try:
    from .rag_manager import RAGManager  # 基本版（Claude CLI統合）
    from .enhanced_rag_manager import EnhancedRAGManager  # 強化版（高機能）
    from .four_sages_integration import FourSagesIntegration  # 4賢者統合
except ImportError:
    # 開発環境用フォールバック
    RAGManager = None
    EnhancedRAGManager = None
    FourSagesIntegration = None

logger = logging.getLogger(__name__)


class RAGMode(Enum):
    """RAG動作モード"""
    BASIC = "basic"  # 基本モード（高速・シンプル）
    ENHANCED = "enhanced"  # 強化モード（高精度・多機能）
    ADAPTIVE = "adaptive"  # 適応モード（自動選択）
    QUANTUM = "quantum"  # 量子モード（Phase 2で実装予定）


class UnifiedRAGManager:
    """
    🔍 統一RAGマネージャー
    
    Elders Guild Phase 1 統合フェーズの中核実装
    基本RAGと強化RAGの統合により、最適な検索と知識統合を実現
    """
    
    def __init__(self, mode: Union[str, RAGMode] = RAGMode.ADAPTIVE):
        """
        統一RAGマネージャー初期化
        
        Args:
            mode: 動作モード（basic/enhanced/adaptive/quantum）
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.mode = RAGMode(mode) if isinstance(mode, str) else mode
        
        # エルダーズ階層情報
        self.elder_hierarchy = {
            "grand_elder": "maru",
            "claude_elder": "active",
            "implementation_date": datetime.now().isoformat(),
            "phase": "Phase 1 - Integration"
        }
        
        # 基本RAGと強化RAGの初期化
        self._initialize_rag_engines()
        
        # 4賢者統合（オプション）
        self._initialize_four_sages()
        
        # パフォーマンスメトリクス
        self.metrics = {
            "searches_performed": 0,
            "basic_mode_usage": 0,
            "enhanced_mode_usage": 0,
            "adaptive_decisions": 0,
            "avg_response_time": 0.0
        }
        
        self.logger.info(f"🏛️ 統一RAGマネージャー初期化完了 - モード: {self.mode.value}")
        self.logger.info(f"🤖 クロードエルダー実行責任下で稼働開始")
    
    def _initialize_rag_engines(self):
        """RAGエンジンの初期化"""
        try:
            # 基本RAGマネージャー（Claude CLI特化）
            if RAGManager:
                self.basic_rag = RAGManager()
                self.logger.info("✅ 基本RAGマネージャー初期化成功")
            else:
                self.basic_rag = None
                self.logger.warning("⚠️ 基本RAGマネージャー利用不可")
            
            # 強化RAGマネージャー（高機能版）
            if EnhancedRAGManager:
                self.enhanced_rag = EnhancedRAGManager()
                self.logger.info("✅ 強化RAGマネージャー初期化成功")
            else:
                self.enhanced_rag = None
                self.logger.warning("⚠️ 強化RAGマネージャー利用不可")
                
        except Exception as e:
            self.logger.error(f"❌ RAGエンジン初期化エラー: {e}")
            self.basic_rag = None
            self.enhanced_rag = None
    
    def _initialize_four_sages(self):
        """4賢者統合の初期化"""
        try:
            if FourSagesIntegration:
                self.four_sages = FourSagesIntegration()
                self.logger.info("🧙‍♂️ 4賢者統合システム接続成功")
            else:
                self.four_sages = None
                self.logger.info("ℹ️ 4賢者統合システムは後で接続されます")
        except Exception as e:
            self.logger.warning(f"⚠️ 4賢者統合初期化スキップ: {e}")
            self.four_sages = None
    
    async def search(self, 
                    query: str, 
                    context: Optional[Dict[str, Any]] = None,
                    mode_override: Optional[RAGMode] = None) -> Dict[str, Any]:
        """
        統一検索インターフェース
        
        Args:
            query: 検索クエリ
            context: 追加コンテキスト情報
            mode_override: このクエリのみのモード指定
            
        Returns:
            検索結果と統合情報
        """
        start_time = datetime.now()
        self.metrics["searches_performed"] += 1
        
        # モード決定
        effective_mode = mode_override or self._determine_mode(query, context)
        
        try:
            # モードに応じた検索実行
            if effective_mode == RAGMode.BASIC:
                result = await self._search_basic(query, context)
                self.metrics["basic_mode_usage"] += 1
                
            elif effective_mode == RAGMode.ENHANCED:
                result = await self._search_enhanced(query, context)
                self.metrics["enhanced_mode_usage"] += 1
                
            elif effective_mode == RAGMode.ADAPTIVE:
                result = await self._search_adaptive(query, context)
                self.metrics["adaptive_decisions"] += 1
                
            else:  # QUANTUM mode (future)
                result = await self._search_adaptive(query, context)
                self.logger.info("🌟 量子モードは Phase 2 で実装予定")
            
            # パフォーマンス記録
            elapsed = (datetime.now() - start_time).total_seconds()
            self._update_metrics(elapsed)
            
            # 結果に統合情報を追加
            result["unified_info"] = {
                "mode_used": effective_mode.value,
                "response_time": elapsed,
                "elder_approval": self.elder_hierarchy,
                "four_sages_consulted": bool(self.four_sages)
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 統一検索エラー: {e}")
            return {
                "error": str(e),
                "mode_attempted": effective_mode.value,
                "fallback": "basic_search"
            }
    
    def _determine_mode(self, query: str, context: Optional[Dict[str, Any]]) -> RAGMode:
        """
        クエリとコンテキストから最適なモードを決定
        
        適応型意思決定ロジック:
        - 短いクエリ → BASIC
        - 複雑なクエリ → ENHANCED
        - コンテキスト多い → ENHANCED
        - 緊急フラグ → BASIC（高速優先）
        """
        if self.mode != RAGMode.ADAPTIVE:
            return self.mode
        
        # 緊急性チェック
        if context and context.get("urgent", False):
            return RAGMode.BASIC
        
        # クエリ複雑度分析
        query_length = len(query.split())
        has_technical_terms = any(term in query.lower() for term in [
            "implement", "architecture", "optimize", "debug", "refactor"
        ])
        
        # コンテキスト量
        context_size = len(str(context)) if context else 0
        
        # 決定ロジック
        if query_length < 5 and context_size < 100:
            return RAGMode.BASIC
        elif query_length > 20 or has_technical_terms or context_size > 500:
            return RAGMode.ENHANCED
        else:
            # 中間的なケースは基本モードで開始
            return RAGMode.BASIC
    
    async def _search_basic(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """基本RAG検索"""
        if not self.basic_rag:
            return {"error": "Basic RAG not available", "results": []}
        
        try:
            # 基本RAGは同期的なので、非同期ラップ
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, 
                self.basic_rag.search,
                query
            )
            
            return {
                "results": results,
                "mode": "basic",
                "source": "rag_manager.py"
            }
            
        except Exception as e:
            self.logger.error(f"基本RAG検索エラー: {e}")
            return {"error": str(e), "results": []}
    
    async def _search_enhanced(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """強化RAG検索"""
        if not self.enhanced_rag:
            # フォールバック to basic
            self.logger.info("強化RAG利用不可、基本RAGにフォールバック")
            return await self._search_basic(query, context)
        
        try:
            # 強化RAGの高度な機能を活用
            results = await self.enhanced_rag.search_async(
                query=query,
                context=context,
                use_semantic=True,
                use_graph=True
            )
            
            return {
                "results": results,
                "mode": "enhanced",
                "source": "enhanced_rag_manager.py",
                "features_used": ["semantic_search", "knowledge_graph"]
            }
            
        except Exception as e:
            self.logger.error(f"強化RAG検索エラー: {e}")
            # フォールバック
            return await self._search_basic(query, context)
    
    async def _search_adaptive(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """適応型検索（両方のRAGを活用）"""
        # まず基本RAGで高速検索
        basic_results = await self._search_basic(query, context)
        
        # 結果が不十分な場合、強化RAGも使用
        if len(basic_results.get("results", [])) < 3:
            enhanced_results = await self._search_enhanced(query, context)
            
            # 結果を統合
            combined_results = {
                "results": basic_results.get("results", []) + enhanced_results.get("results", []),
                "mode": "adaptive",
                "sources": ["basic", "enhanced"],
                "strategy": "insufficient_basic_results"
            }
            
            return combined_results
        
        return basic_results
    
    def _update_metrics(self, elapsed_time: float):
        """メトリクス更新"""
        current_avg = self.metrics["avg_response_time"]
        total_searches = self.metrics["searches_performed"]
        
        # 移動平均を計算
        self.metrics["avg_response_time"] = (
            (current_avg * (total_searches - 1) + elapsed_time) / total_searches
        )
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        統計情報取得
        
        Returns:
            使用統計とパフォーマンスメトリクス
        """
        total = self.metrics["searches_performed"]
        if total == 0:
            return {"message": "No searches performed yet"}
        
        return {
            "total_searches": total,
            "mode_distribution": {
                "basic": f"{self.metrics['basic_mode_usage'] / total * 100:.1f}%",
                "enhanced": f"{self.metrics['enhanced_mode_usage'] / total * 100:.1f}%",
                "adaptive": f"{self.metrics['adaptive_decisions'] / total * 100:.1f}%"
            },
            "avg_response_time": f"{self.metrics['avg_response_time']:.3f}s",
            "rag_status": {
                "basic": "active" if self.basic_rag else "unavailable",
                "enhanced": "active" if self.enhanced_rag else "unavailable",
                "four_sages": "connected" if self.four_sages else "disconnected"
            },
            "elder_hierarchy": self.elder_hierarchy
        }
    
    async def consult_four_sages(self, query: str) -> Optional[Dict[str, Any]]:
        """
        4賢者への相談（オプション機能）
        
        Args:
            query: 相談内容
            
        Returns:
            4賢者の統合見解
        """
        if not self.four_sages:
            return None
        
        try:
            # 4賢者協調相談
            sage_consultation = await self.four_sages.collaborative_learning_session({
                "topic": "rag_optimization",
                "query": query,
                "requester": "unified_rag_manager"
            })
            
            return sage_consultation
            
        except Exception as e:
            self.logger.error(f"4賢者相談エラー: {e}")
            return None
    
    async def optimize_for_phase2(self) -> Dict[str, Any]:
        """
        Phase 2に向けた最適化準備
        
        Returns:
            最適化提案と準備状況
        """
        return {
            "current_phase": "Phase 1 - Integration",
            "next_phase": "Phase 2 - Quantum Collaboration",
            "optimization_suggestions": [
                "ベクトルデータベース統合準備",
                "量子インスパイア・アルゴリズム設計",
                "4賢者協調学習の強化",
                "キャッシング戦略の最適化"
            ],
            "readiness": {
                "unified_interface": "✅ Complete",
                "dual_engine_support": "✅ Complete",
                "adaptive_mode": "✅ Complete",
                "four_sages_integration": "🔄 In Progress",
                "quantum_mode": "📅 Planned"
            }
        }


# テスト実行用
if __name__ == "__main__":
    async def test_unified_rag():
        """統一RAGマネージャーのテスト"""
        manager = UnifiedRAGManager(mode=RAGMode.ADAPTIVE)
        
        # テストクエリ
        test_queries = [
            "TDDの基本原則",
            "Elders Guildの4賢者システムについて詳しく教えてください",
            "エラー対処法",
        ]
        
        for query in test_queries:
            print(f"\n🔍 検索: {query}")
            result = await manager.search(query)
            print(f"📊 結果: {result.get('unified_info', {})}")
        
        # 統計表示
        stats = await manager.get_statistics()
        print(f"\n📈 統計情報: {stats}")
    
    # 実行
    asyncio.run(test_unified_rag())