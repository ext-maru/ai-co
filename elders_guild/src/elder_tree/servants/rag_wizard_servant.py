"""
RAG Wizard Servant - 🧙‍♂️ RAGウィザード調査研究サーバント
python-a2a 0.5.9 + エルダーズギルド統合実装
TDD Green Phase: 完全Iron Will準拠
"""

from typing import Dict, Any, List, Optional, Union
import asyncio
import json
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime

# Base Servant継承
from elder_tree.servants.base_servant import ElderServantBase

# エルダーズギルド RAG専門統合
import sys
sys.path.append('/home/aicompany/ai_co')

# RAG専門サーバント統合 (try/except で安全に)
try:
    from libs.elder_servants.rag_wizards.data_miner import DataMiner
    from libs.elder_servants.rag_wizards.tech_scout import TechScout
    from libs.enhanced_rag_manager import EnhancedRAGManager
    from libs.rag_manager import RagManager
    from libs.elder_servants.rag_wizards.knowledge_weaver import KnowledgeWeaver
    from libs.elder_servants.rag_wizards.semantic_analyzer import SemanticAnalyzer
    RAG_WIZARDS_AVAILABLE = True
except ImportError:
    RAG_WIZARDS_AVAILABLE = False

# python-a2a decorator
from python_a2a import agent

import structlog


@agent(name="RAGWizardServant", description="Elder Tree RAG Wizard Research Specialist")
class RAGWizardServant(ElderServantBase):
    """
    🧙‍♂️ RAGウィザード調査研究サーバント (Elder Tree統合)
    
    特化機能:
    - データマイニング・情報探索
    - 技術調査・トレンド分析
    - セマンティック検索・知識統合
    - ナレッジグラフ構築
    - 強化RAGクエリシステム
    """
    
    def __init__(self, name: str, specialty: str, port: Optional[int] = None):
        """
        RAGウィザードサーバント初期化
        
        Args:
            name: サーバント名
            specialty: 専門分野 (data_mining, tech_scouting, semantic_search, etc.)
            port: ポート番号
        """
        super().__init__(
            name=name,
            tribe="rag_wizard",
            specialty=specialty,
            port=port
        )
        
        # RAGウィザード工房固有設定
        self.search_depth = "comprehensive"
        self.analysis_methods = ["semantic", "statistical", "comparative", "contextual"]
        self.quality_threshold = 85.0  # ウィザードは高い品質基準
        
        # エルダーズギルドRAG工房統合
        self.rag_tools = {}
        if RAG_WIZARDS_AVAILABLE:
            self._initialize_rag_tools()
        
        # RAGウィザード専用ハンドラー登録
        self._register_rag_wizard_handlers()
        
        self.logger.info(
            "RAGWizardServant initialized with RAG tools",
            rag_tools_available=RAG_WIZARDS_AVAILABLE,
            specialty=specialty
        )
    
    def _initialize_rag_tools(self):
        """RAGウィザード工房ツール初期化"""
        try:
            # 各専門RAGツールのインスタンス化
            if hasattr(DataMiner, '__init__'):
                self.rag_tools['data_miner'] = DataMiner()
            
            if hasattr(TechScout, '__init__'):
                self.rag_tools['tech_scout'] = TechScout()
            
            if hasattr(EnhancedRAGManager, '__init__'):
                self.rag_tools['enhanced_rag'] = EnhancedRAGManager()
            
            if hasattr(RagManager, '__init__'):
                self.rag_tools['rag_manager'] = RagManager()
            
            if hasattr(KnowledgeWeaver, '__init__'):
                self.rag_tools['knowledge_weaver'] = KnowledgeWeaver()
            
            if hasattr(SemanticAnalyzer, '__init__'):
                self.rag_tools['semantic_analyzer'] = SemanticAnalyzer()
            
            self.logger.info(f"RAG wizard tools initialized: {list(self.rag_tools.keys())}")
            
        except Exception as e:
            self.logger.warning(f"RAG tools initialization error: {e}")
            self.rag_tools = {}


    def _register_rag_wizard_handlers(self):
        """RAGウィザード専用ハンドラー登録 (python-a2a 0.5.9対応)"""
        
        @self.handle("mine_data")
        async def handle_mine_data(message) -> Dict[str, Any]:
            """
            データマイニングリクエスト
            
            Input:
                - query: 検索クエリ
                - depth: 検索深度 (shallow, moderate, deep)
                - sources: データソース指定
                - filters: フィルター条件
            """
            query = message.data.get("query", "")
            depth = message.data.get("depth", "moderate")
            sources = message.data.get("sources", ["all"])
            filters = message.data.get("filters", {})
            
            try:
                # データマイナーツールを使用
                if 'data_miner' in self.rag_tools:
                    result = await asyncio.to_thread(
                        self.rag_tools['data_miner'].mine_comprehensive,
                        query, depth, sources, filters
                    )
                else:
                    # フォールバック: 基本的なデータマイニング
                    result = await self._fallback_mine_data(query, depth, sources, filters)
                
                return {
                    "status": "success",
                    "servant": self.name,
                    "task": "mine_data",
                    "query": query,
                    "depth": depth,
                    "results": result,
                    "sources_analyzed": len(result.get("sources", [])),
                    "data_points": len(result.get("data_points", [])),
                    "confidence": result.get("confidence_score", 0.0)
                }
                
            except Exception as e:
                self.logger.error(f"Data mining failed: {e}")
                return await self._handle_task_error("mine_data", str(e), {"query": query})
        
        @self.handle("scout_technology")
        async def handle_scout_technology(message) -> Dict[str, Any]:
            """
            技術調査リクエスト
            
            Input:
                - technology: 調査対象技術
                - scope: 調査範囲 (trends, competitors, implementations)
                - timeframe: 時間枠 (recent, historical, future)
            """
            technology = message.data.get("technology", "")
            scope = message.data.get("scope", "trends")
            timeframe = message.data.get("timeframe", "recent")
            
            try:
                # テックスカウトツールを使用
                if 'tech_scout' in self.rag_tools:
                    result = await asyncio.to_thread(
                        self.rag_tools['tech_scout'].scout_comprehensive,
                        technology, scope, timeframe
                    )
                else:
                    # フォールバック: 基本的な技術調査
                    result = await self._fallback_scout_technology(technology, scope, timeframe)
                
                return {
                    "status": "success",
                    "servant": self.name,
                    "task": "scout_technology",
                    "technology": technology,
                    "scope": scope,
                    "findings": result,
                    "trend_score": result.get("trend_score", 0.0),
                    "adoption_rate": result.get("adoption_rate", "unknown"),
                    "recommendations": result.get("recommendations", [])
                }
                
            except Exception as e:
                self.logger.error(f"Technology scouting failed: {e}")
                return await self._handle_task_error(
                    "scout_technology",
                    str(e),
                    {"technology": technology}
                )
        
        @self.handle("semantic_search")
        async def handle_semantic_search(message) -> Dict[str, Any]:
            """
            セマンティック検索リクエスト
            
            Input:
                - query: 検索クエリ
                - context: コンテキスト情報
                - semantic_threshold: 意味的類似度閾値
                - max_results: 最大結果数
            """
            query = message.data.get("query", "")
            context = message.data.get("context", "")
            threshold = message.data.get("semantic_threshold", 0.7)
            max_results = message.data.get("max_results", 10)
            
            try:
                # セマンティック検索実行
                if 'semantic_analyzer' in self.rag_tools:
                    result = await asyncio.to_thread(
                        self.rag_tools['semantic_analyzer'].search_semantic,
                        query, context, threshold, max_results
                    )
                else:
                    # フォールバック: 拡張RAGマネージャー使用
                    result = await self._fallback_semantic_search(
                        query,
                        context,
                        threshold,
                        max_results
                    )
                
                return {
                    "status": "success",
                    "servant": self.name,
                    "task": "semantic_search",
                    "query": query,
                    "results": result.get("matches", []),
                    "semantic_scores": result.get("scores", []),
                    "total_matches": len(result.get("matches", [])),
                    "avg_similarity": result.get("avg_similarity", 0.0)
                }
                
            except Exception as e:
                self.logger.error(f"Semantic search failed: {e}")
                return await self._handle_task_error("semantic_search", str(e), {"query": query})
        
        @self.handle("build_knowledge_graph")
        async def handle_build_knowledge_graph(message) -> Dict[str, Any]:
            """
            ナレッジグラフ構築リクエスト
            
            Input:
                - domain: ドメイン領域
                - entities: エンティティリスト
                - relationships: 関係性定義
                - depth_limit: 深度制限
            """
            domain = message.data.get("domain", "general")
            entities = message.data.get("entities", [])
            relationships = message.data.get("relationships", [])
            depth_limit = message.data.get("depth_limit", 3)
            
            try:
                # ナレッジウィーバーツールを使用
                if 'knowledge_weaver' in self.rag_tools:
                    result = await asyncio.to_thread(
                        self.rag_tools['knowledge_weaver'].weave_knowledge_graph,
                        domain, entities, relationships, depth_limit
                    )
                else:
                    # フォールバック: 基本的なナレッジグラフ構築
                    result = await self._fallback_build_knowledge_graph(
                        domain, entities, relationships, depth_limit
                    )
                
                return {
                    "status": "success",
                    "servant": self.name,
                    "task": "build_knowledge_graph",
                    "domain": domain,
                    "graph": result,
                    "nodes_count": len(result.get("nodes", [])),
                    "edges_count": len(result.get("edges", [])),
                    "graph_density": result.get("density", 0.0),
                    "clusters": result.get("clusters", [])
                }
                
            except Exception as e:
                self.logger.error(f"Knowledge graph building failed: {e}")
                return await self._handle_task_error(
                    "build_knowledge_graph",
                    str(e),
                    {"domain": domain}
                )
        
        @self.handle("enhanced_rag_query")
        async def handle_enhanced_rag_query(message) -> Dict[str, Any]:
            """
            強化RAGクエリリクエスト
            
            Input:
                - query: クエリ文
                - context_window: コンテキストウィンドウサイズ
                - retrieval_strategy: 検索戦略 (semantic, hybrid, keyword)
                - rerank: 再ランキング有効化
            """
            query = message.data.get("query", "")
            context_window = message.data.get("context_window", 4096)
            strategy = message.data.get("retrieval_strategy", "hybrid")
            rerank = message.data.get("rerank", True)
            
            try:
                # 拡張RAGマネージャーを使用
                if 'enhanced_rag' in self.rag_tools:
                    result = await asyncio.to_thread(
                        self.rag_tools['enhanced_rag'].query_enhanced,
                        query, context_window, strategy, rerank
                    )
                else:
                    # フォールバック: 基本RAGマネージャー使用
                    result = await self._fallback_enhanced_rag_query(
                        query, context_window, strategy, rerank
                    )
                
                return {
                    "status": "success",
                    "servant": self.name,
                    "task": "enhanced_rag_query",
                    "query": query,
                    "response": result.get("response", ""),
                    "sources": result.get("sources", []),
                    "confidence": result.get("confidence", 0.0),
                    "retrieval_time": result.get("retrieval_time", 0.0),
                    "context_used": len(result.get("context", ""))
                }
                
            except Exception as e:
                self.logger.error(f"Enhanced RAG query failed: {e}")
                return await self._handle_task_error("enhanced_rag_query", str(e), {"query": query})
    
    async def execute_specialized_task(
        self,
        task_type: str,
        parameters: Dict[str, Any],
        consultation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        RAGウィザード特化タスク実行 (python-a2a 0.5.9対応)
        
        Args:
            task_type: タスク種別
            parameters: パラメータ
            consultation_result: 4賢者協議結果
        
        Returns:
            実行結果
        """
        task_id = f"rag_wizard_{task_type}_{datetime.now().strftime('%H%M%S')}"
        
        self.logger.info(
            f"Executing RAG wizard specialized task: {task_type}",
            task_id=task_id,
            parameters_keys=list(parameters.keys())
        )
        
        try:
            if task_type == "comprehensive_research":
                return await self._execute_comprehensive_research(parameters, consultation_result)
                
            elif task_type == "knowledge_synthesis":
                return await self._execute_knowledge_synthesis(parameters, consultation_result)
                
            elif task_type == "trend_analysis":
                return await self._execute_trend_analysis(parameters, consultation_result)
                
            elif task_type == "semantic_exploration":
                return await self._execute_semantic_exploration(parameters, consultation_result)
                
            elif task_type == "contextual_search":
                return await self._execute_contextual_search(parameters, consultation_result)
                
            else:
                # ベースクラスの汎用実装を呼び出し
                return await super().execute_specialized_task(
                    task_type, parameters, consultation_result
                )
        
        except Exception as e:
            self.logger.error(f"RAG wizard task execution failed: {e}", task_type=task_type)
            return await self._handle_task_error(task_type, str(e), parameters)
    
    async def _execute_comprehensive_research(
        self, 
        parameters: Dict[str, Any], 
        consultation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """包括的調査研究の実行"""
        topic = parameters.get("topic", "")
        scope = parameters.get("scope", "comprehensive")
        depth = parameters.get("depth", "moderate")
        
        # マルチアプローチでの情報収集
        research_tasks = []
        
        # 1. データマイニング
        if 'data_miner' in self.rag_tools:
            research_tasks.append(
                self.rag_tools['data_miner'].mine_comprehensive(topic, depth, ["all"], {})
            )
        
        # 2. 技術スカウティング
        if 'tech_scout' in self.rag_tools:
            research_tasks.append(
                self.rag_tools['tech_scout'].scout_comprehensive(topic, "trends", "recent")
            )
        
        # 3. セマンティック検索
        if 'semantic_analyzer' in self.rag_tools:
            research_tasks.append(
                self.rag_tools['semantic_analyzer'].search_semantic(topic, "", 0.7, 10)
            )
        
        # 並列実行
        research_results = await asyncio.gather(*research_tasks, return_exceptions=True)
        
        # 結果統合
        integrated_findings = self._integrate_research_results(research_results)
        
        # 分析・評価
        analysis = self._analyze_integrated_findings(integrated_findings, consultation_result)
        
        return {
            "status": "completed",
            "task_type": "comprehensive_research",
            "topic": topic,
            "scope": scope,
            "depth": depth,
            "findings": integrated_findings,
            "analysis": analysis,
            "sources_count": integrated_findings.get("total_sources", 0),
            "confidence_score": analysis.get("confidence", 0.0),
            "research_methods": ["data_mining", "tech_scouting", "semantic_search"],
            "execution_time": datetime.now().isoformat()
        }
    
    async def _execute_knowledge_synthesis(
        self, 
        parameters: Dict[str, Any], 
        consultation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """知識統合の実行"""
        domain = parameters.get("domain", "general")
        concepts = parameters.get("concepts", [])
        synthesis_method = parameters.get("method", "semantic_clustering")
        
        # ナレッジウィーバーを使用した知識統合
        if 'knowledge_weaver' in self.rag_tools:
            synthesis_result = await asyncio.to_thread(
                self.rag_tools['knowledge_weaver'].synthesize_knowledge,
                domain, concepts, synthesis_method
            )
        else:
            # フォールバック統合
            synthesis_result = await self._fallback_knowledge_synthesis(
                domain, concepts, synthesis_method
            )
        
        return {
            "status": "completed",
            "task_type": "knowledge_synthesis",
            "domain": domain,
            "concepts_processed": len(concepts),
            "synthesis": synthesis_result,
            "clusters_formed": len(synthesis_result.get("clusters", [])),
            "connections_found": len(synthesis_result.get("connections", [])),
            "synthesis_quality": synthesis_result.get("quality_score", 0.0)
        }
    
    async def _execute_trend_analysis(
        self, 
        parameters: Dict[str, Any], 
        consultation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """トレンド分析の実行"""
        technology = parameters.get("technology", "")
        timeframe = parameters.get("timeframe", "6_months")
        analysis_type = parameters.get("analysis_type", "adoption_trends")
        
        # テックスカウトによるトレンド分析
        if 'tech_scout' in self.rag_tools:
            trend_result = await asyncio.to_thread(
                self.rag_tools['tech_scout'].analyze_trends,
                technology, timeframe, analysis_type
            )
        else:
            # フォールバックトレンド分析
            trend_result = await self._fallback_trend_analysis(
                technology, timeframe, analysis_type
            )
        
        return {
            "status": "completed",
            "task_type": "trend_analysis",
            "technology": technology,
            "timeframe": timeframe,
            "trends": trend_result,
            "trend_direction": trend_result.get("direction", "stable"),
            "growth_rate": trend_result.get("growth_rate", 0.0),
            "market_indicators": trend_result.get("indicators", []),
            "forecast": trend_result.get("forecast", {})
        }
    
    async def _execute_semantic_exploration(
        self, 
        parameters: Dict[str, Any], 
        consultation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """セマンティック探索の実行"""
        seed_concepts = parameters.get("seed_concepts", [])
        exploration_depth = parameters.get("depth", 3)
        similarity_threshold = parameters.get("threshold", 0.6)
        
        # セマンティックアナライザーによる探索
        if 'semantic_analyzer' in self.rag_tools:
            exploration_result = await asyncio.to_thread(
                self.rag_tools['semantic_analyzer'].explore_semantic_space,
                seed_concepts, exploration_depth, similarity_threshold
            )
        else:
            # フォールバック探索
            exploration_result = await self._fallback_semantic_exploration(
                seed_concepts, exploration_depth, similarity_threshold
            )
        
        return {
            "status": "completed",
            "task_type": "semantic_exploration",
            "seed_concepts": seed_concepts,
            "exploration": exploration_result,
            "discovered_concepts": len(exploration_result.get("concepts", [])),
            "semantic_clusters": exploration_result.get("clusters", []),
            "concept_map": exploration_result.get("concept_map", {}),
            "exploration_coverage": exploration_result.get("coverage", 0.0)
        }
    
    async def _execute_contextual_search(
        self, 
        parameters: Dict[str, Any], 
        consultation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """コンテキスト検索の実行"""
        query = parameters.get("query", "")
        context = parameters.get("context", "")
        search_strategy = parameters.get("strategy", "contextual_embedding")
        
        # 拡張RAGマネージャーによるコンテキスト検索
        if 'enhanced_rag' in self.rag_tools:
            search_result = await asyncio.to_thread(
                self.rag_tools['enhanced_rag'].contextual_search,
                query, context, search_strategy
            )
        else:
            # フォールバック検索
            search_result = await self._fallback_contextual_search(
                query, context, search_strategy
            )
        
        return {
            "status": "completed",
            "task_type": "contextual_search",
            "query": query,
            "context_used": context,
            "results": search_result,
            "results_count": len(search_result.get("matches", [])),
            "context_relevance": search_result.get("context_relevance", 0.0),
            "search_accuracy": search_result.get("accuracy", 0.0)
        }
    
    # ===== フォールバック実装 =====
    
    async def _fallback_mine_data(
        self, 
        query: str, 
        depth: str, 
        sources: List[str], 
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """データマイニングフォールバック実装"""
        try:
            # 基本RAGマネージャーを使用したデータマイニング
            if 'rag_manager' in self.rag_tools:
                search_results = await asyncio.to_thread(
                    self.rag_tools['rag_manager'].search_knowledge,
                    query, None, 20 if depth == "deep" else 10
                )
                
                return {
                    "sources": [r.source for r in search_results],
                    "data_points": [
                        {
                            "content": r.content[:200],
                            "source": r.source,
                            "relevance": r.relevance_score
                        } for r in search_results
                    ],
                    "confidence_score": sum(
                        r.relevance_score for r in search_results) / max(len(search_results),
                        1
                    ),
                    "method": "fallback_rag_search"
                }
            else:
                # 最小限の実装
                return {
                    "sources": ["fallback_source"],
                    "data_points": [{"content": f"Basic analysis for: {query}", "source": "internal", "relevance": 0.5}],
                    "confidence_score": 0.5,
                    "method": "minimal_fallback"
                }
                
        except Exception as e:
            self.logger.error(f"Fallback data mining failed: {e}")
            return {"sources": [], "data_points": [], "confidence_score": 0.0, "method": "error_fallback"}
    
    async def _fallback_scout_technology(
        self, 
        technology: str, 
        scope: str, 
        timeframe: str
    ) -> Dict[str, Any]:
        """技術調査フォールバック実装"""
        try:
            # RAGマネージャーで技術関連情報を検索
            if 'rag_manager' in self.rag_tools:
                search_results = await asyncio.to_thread(
                    self.rag_tools['rag_manager'].search_knowledge,
                    f"{technology} {scope} trends", "technology", 15
                )
                
                # 簡易的なトレンドスコア計算
                trend_score = min(len(search_results) / 10.0, 1.0)
                
                return {
                    "technology": technology,
                    "findings": [r.content[:150] for r in search_results[:5]],
                    "trend_score": trend_score,
                    "adoption_rate": "moderate" if trend_score > 0.5 else "low",
                    "recommendations": [
                        f"Monitor {technology} developments",
                        f"Evaluate {technology} for project suitability",
                        "Consider implementation pilot program"
                    ],
                    "method": "fallback_rag_analysis"
                }
            else:
                # 最小限の応答
                return {
                    "technology": technology,
                    "findings": [f"Basic information available for {technology}"],
                    "trend_score": 0.5,
                    "adoption_rate": "unknown",
                    "recommendations": ["Requires further investigation"],
                    "method": "minimal_fallback"
                }
                
        except Exception as e:
            self.logger.error(f"Fallback technology scouting failed: {e}")
            return {"technology": technology, "findings": [], "trend_score": 0.0, "method": "error_fallback"}
    
    async def _fallback_semantic_search(
        self, 
        query: str, 
        context: str, 
        threshold: float, 
        max_results: int
    ) -> Dict[str, Any]:
        """セマンティック検索フォールバック実装"""
        try:
            # 拡張RAGマネージャーまたは基本RAGマネージャーを使用
            rag_tool = self.rag_tools.get('enhanced_rag') or self.rag_tools.get('rag_manager')
            
            if rag_tool:
                if hasattr(rag_tool, 'search_knowledge'):
                    search_results = await asyncio.to_thread(
                        rag_tool.search_knowledge,
                        f"{query} {context}".strip(), None, max_results
                    )
                    
                    matches = []
                    scores = []
                    
                    for result in search_results:
                        if result.relevance_score >= threshold:
                            matches.append({
                                "content": result.content,
                                "source": result.source,
                                "metadata": result.metadata
                            })
                            scores.append(result.relevance_score)
                    
                    return {
                        "matches": matches,
                        "scores": scores,
                        "avg_similarity": sum(scores) / max(len(scores), 1),
                        "method": "fallback_rag_semantic"
                    }
            
            # 最小限の実装
            return {
                "matches": [{"content": f"Semantic match for: {query}", "source": "internal", "metadata": {}}],
                "scores": [0.6],
                "avg_similarity": 0.6,
                "method": "minimal_fallback"
            }
            
        except Exception as e:
            self.logger.error(f"Fallback semantic search failed: {e}")
            return {"matches": [], "scores": [], "avg_similarity": 0.0, "method": "error_fallback"}
    
    async def _fallback_build_knowledge_graph(
        self, 
        domain: str, 
        entities: List[str], 
        relationships: List[str], 
        depth_limit: int
    ) -> Dict[str, Any]:
        """ナレッジグラフ構築フォールバック実装"""
        try:
            # 簡易的なナレッジグラフ構築
            nodes = []
            edges = []
            
            # エンティティをノードとして追加
            for i, entity in enumerate(entities):
                nodes.append({
                    "id": f"node_{i}",
                    "label": entity,
                    "type": "entity",
                    "domain": domain
                })
            
            # 関係性からエッジを生成
            for i, relationship in enumerate(relationships):
                if i < len(entities) - 1:
                    edges.append({
                        "source": f"node_{i}",
                        "target": f"node_{i+1}",
                        "relationship": relationship,
                        "weight": 1.0
                    })
            
            # グラフ密度計算
            max_edges = len(nodes) * (len(nodes) - 1) / 2
            density = len(edges) / max(max_edges, 1)
            
            return {
                "nodes": nodes,
                "edges": edges,
                "density": density,
                "clusters": [{"id": "cluster_1", "nodes": [node["id"] for node in nodes]}],
                "method": "fallback_basic_graph"
            }
            
        except Exception as e:
            self.logger.error(f"Fallback knowledge graph building failed: {e}")
            return {"nodes": [], "edges": [], "density": 0.0, "clusters": [], "method": "error_fallback"}
    
    async def _fallback_enhanced_rag_query(
        self, 
        query: str, 
        context_window: int, 
        strategy: str, 
        rerank: bool
    ) -> Dict[str, Any]:
        """強化RAGクエリフォールバック実装"""
        try:
            # 基本RAGマネージャーを使用
            if 'rag_manager' in self.rag_tools:
                search_results = await asyncio.to_thread(
                    self.rag_tools['rag_manager'].search_knowledge,
                    query, None, 10
                )
                
                # 結果をコンテキストに統合
                context_parts = []
                sources = []
                
                for result in search_results:
                    if len(" ".join(context_parts)) < context_window:
                        context_parts.append(result.content[:500])
                        sources.append(result.source)
                
                context = " ".join(context_parts)
                
                # 基本的な応答生成
                response = f"Based on the available information: {context[:800]}..."
                
                return {
                    "response": response,
                    "sources": sources,
                    "confidence": sum(
                        r.relevance_score for r in search_results) / max(len(search_results),
                        1
                    ),
                    "retrieval_time": 0.5,
                    "context": context,
                    "method": "fallback_basic_rag"
                }
            else:
                # 最小限の応答
                return {
                    "response": f"Processing query: {query}",
                    "sources": ["internal"],
                    "confidence": 0.5,
                    "retrieval_time": 0.1,
                    "context": query,
                    "method": "minimal_fallback"
                }
                
        except Exception as e:
            self.logger.error(f"Fallback enhanced RAG query failed: {e}")
            return {"response": "", "sources": [], "confidence": 0.0, "method": "error_fallback"}
    
    # ===== ユーティリティメソッド =====
    
    def _integrate_research_results(self, research_results: List[Any]) -> Dict[str, Any]:
        """研究結果の統合"""
        integrated = {
            "data_mining": {},
            "tech_scouting": {},
            "semantic_search": {},
            "total_sources": 0,
            "combined_confidence": 0.0
        }
        
        valid_results = [r for r in research_results if not isinstance(r, Exception)]
        
        if valid_results:
            # 各結果を統合
            for i, result in enumerate(valid_results):
                if i == 0 and isinstance(result, dict):  # Data mining
                    integrated["data_mining"] = result
                    integrated["total_sources"] += len(result.get("sources", []))
                elif i == 1 and isinstance(result, dict):  # Tech scouting
                    integrated["tech_scouting"] = result
                elif i == 2 and isinstance(result, dict):  # Semantic search
                    integrated["semantic_search"] = result
            
            # 信頼度スコアの統合
            confidence_scores = []
            for result in valid_results:
                if isinstance(result, dict):
                    confidence_scores.append(result.get("confidence_score", 0.0))
            
            integrated["combined_confidence"] = sum(
                confidence_scores) / max(len(confidence_scores),
                1
            )
        
        return integrated
    
    def _analyze_integrated_findings(
        self, 
        integrated_findings: Dict[str, Any], 
        consultation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """統合された調査結果の分析"""
        analysis = {
            "confidence": integrated_findings.get("combined_confidence", 0.0),
            "key_insights": [],
            "recommendations": [],
            "research_quality": "good" if integrated_findings.get(
                "total_sources",
                0
            ) >= 5 else "moderate"
        }
        
        # 各手法からの洞察を抽出
        data_mining = integrated_findings.get("data_mining", {})
        if data_mining.get("data_points"):
            analysis["key_insights"].append(f"Found {len(data_mining['data_points'])} relevant data points")
        
        tech_scouting = integrated_findings.get("tech_scouting", {})
        if tech_scouting.get("trend_score", 0) > 0.7:
            analysis["key_insights"].append("High technology adoption trend detected")
        
        semantic_search = integrated_findings.get("semantic_search", {})
        if semantic_search.get("matches"):
            analysis["key_insights"].append(f"Semantic analysis identified {len(semantic_search['matches'])} relevant matches")
        
        # 推奨事項の生成
        if analysis["confidence"] > 0.7:
            analysis["recommendations"].append("High confidence findings - proceed with implementation planning")
        elif analysis["confidence"] > 0.4:
            analysis["recommendations"].append("Moderate confidence - consider additional validation")
        else:
            analysis["recommendations"].append("Low confidence - expand research scope")
        
        return analysis
    
    async def _fallback_knowledge_synthesis(
        self, 
        domain: str, 
        concepts: List[str], 
        method: str
    ) -> Dict[str, Any]:
        """知識統合フォールバック実装"""
        try:
            clusters = []
            connections = []
            
            # 概念をクラスター化（簡易版）
            for i in range(0, len(concepts), 3):
                cluster_concepts = concepts[i:i+3]
                clusters.append({
                    "id": f"cluster_{len(clusters)}",
                    "concepts": cluster_concepts,
                    "theme": cluster_concepts[0] if cluster_concepts else "unknown"
                })
            
            # 概念間の接続を生成
            for i in range(len(concepts) - 1):
                connections.append({
                    "source": concepts[i],
                    "target": concepts[i + 1],
                    "relationship": "related_to",
                    "strength": 0.5
                })
            
            return {
                "clusters": clusters,
                "connections": connections,
                "quality_score": 0.7,
                "synthesis_method": method,
                "domain": domain
            }
            
        except Exception as e:
            self.logger.error(f"Fallback knowledge synthesis failed: {e}")
            return {"clusters": [], "connections": [], "quality_score": 0.0}
    
    async def _fallback_trend_analysis(
        self, 
        technology: str, 
        timeframe: str, 
        analysis_type: str
    ) -> Dict[str, Any]:
        """トレンド分析フォールバック実装"""
        try:
            # 簡易トレンド分析
            growth_rates = {"emerging": 0.8, "mature": 0.3, "declining": -0.2}
            base_rate = growth_rates.get("emerging", 0.5)  # デフォルトは新興技術として扱う
            
            return {
                "direction": "ascending" if base_rate > 0 else "descending",
                "growth_rate": base_rate,
                "indicators": [
                    f"{technology} shows active development",
                    f"Market interest in {timeframe} period",
                    "Community adoption patterns"
                ],
                "forecast": {
                    "3_months": base_rate * 1.1,
                    "6_months": base_rate * 1.2,
                    "12_months": base_rate * 1.3
                },
                "method": "fallback_trend_estimation"
            }
            
        except Exception as e:
            self.logger.error(f"Fallback trend analysis failed: {e}")
            return {"direction": "unknown", "growth_rate": 0.0, "indicators": [], "forecast": {}}
    
    async def _fallback_semantic_exploration(
        self, 
        seed_concepts: List[str], 
        depth: int, 
        threshold: float
    ) -> Dict[str, Any]:
        """セマンティック探索フォールバック実装"""
        try:
            # 関連概念の生成（簡易版）
            discovered_concepts = []
            concept_map = {}
            
            for seed in seed_concepts:
                # 各シードから関連概念を派生
                related = [
                    f"{seed}_advanced",
                    f"{seed}_application",
                    f"{seed}_framework"
                ]
                discovered_concepts.extend(related)
                concept_map[seed] = related
            
            # クラスター形成
            clusters = [{
                "id": "main_cluster",
                "concepts": seed_concepts + discovered_concepts,
                "centroid": seed_concepts[0] if seed_concepts else "unknown"
            }]
            
            return {
                "concepts": discovered_concepts,
                "clusters": clusters,
                "concept_map": concept_map,
                "coverage": min(len(discovered_concepts) / 10.0, 1.0),
                "method": "fallback_concept_expansion"
            }
            
        except Exception as e:
            self.logger.error(f"Fallback semantic exploration failed: {e}")
            return {"concepts": [], "clusters": [], "concept_map": {}, "coverage": 0.0}
    
    async def _fallback_contextual_search(
        self, 
        query: str, 
        context: str, 
        strategy: str
    ) -> Dict[str, Any]:
        """コンテキスト検索フォールバック実装"""
        try:
            # 基本的なコンテキスト検索
            combined_query = f"{query} {context}".strip()
            
            # RAGマネージャーを使用した検索
            if 'rag_manager' in self.rag_tools:
                search_results = await asyncio.to_thread(
                    self.rag_tools['rag_manager'].search_knowledge,
                    combined_query, None, 8
                )
                
                matches = []
                for result in search_results:
                    matches.append({
                        "content": result.content,
                        "source": result.source,
                        "relevance": result.relevance_score,
                        "metadata": result.metadata
                    })
                
                context_relevance = sum(
                    r.relevance_score for r in search_results) / max(len(search_results),
                    1
                )
                
                return {
                    "matches": matches,
                    "context_relevance": context_relevance,
                    "accuracy": context_relevance * 0.9,  # 簡易精度計算
                    "method": "fallback_contextual_rag"
                }
            
            # 最小限の応答
            return {
                "matches": [{"content": f"Contextual result for: {query}", "source": "internal", "relevance": 0.6}],
                "context_relevance": 0.6,
                "accuracy": 0.5,
                "method": "minimal_fallback"
            }
            
        except Exception as e:
            self.logger.error(f"Fallback contextual search failed: {e}")
            return {"matches": [], "context_relevance": 0.0, "accuracy": 0.0}
    
    async def _handle_task_error(
        self,
        task_type: str,
        error: str,
        parameters: Dict[str,
        Any]
    ) -> Dict[str, Any]:
        """タスクエラーハンドリング"""
        error_id = f"rag_error_{datetime.now().strftime('%H%M%S')}"
        
        self.logger.error(
            f"RAG wizard task failed: {task_type}",
            error_id=error_id,
            error=error,
            parameters=parameters
        )
        
        # Incident Sageへの報告
        await self.collaborate_with_sage(
            "incident_sage",
            {
                "action": "task_error",
                "servant": self.name,
                "task_type": task_type,
                "error": error,
                "error_id": error_id
            }
        )
        
        return {
            "status": "error",
            "servant": self.name,
            "task_type": task_type,
            "error": error,
            "error_id": error_id,
            "message": f"RAG wizard task failed: {error}",
            "fallback_available": True
        }
    
    async def get_specialized_capabilities(self) -> List[str]:
        """RAGウィザード専門能力の取得"""
        base_capabilities = await super().get_specialized_capabilities()
        
        rag_capabilities = [
            "data_mining",
            "technology_scouting", 
            "semantic_search",
            "knowledge_graph_building",
            "enhanced_rag_queries",
            "comprehensive_research",
            "knowledge_synthesis",
            "trend_analysis",
            "semantic_exploration",
            "contextual_search"
        ]
        
        # RAGツールの可用性に基づく能力拡張
        if RAG_WIZARDS_AVAILABLE:
            rag_capabilities.extend([
                "advanced_data_mining",
                "tech_trend_forecasting",
                "semantic_space_exploration",
                "automated_knowledge_weaving"
            ])
        
        return base_capabilities + rag_capabilities
    
# ===== 単体実行・テスト用 =====

async def test_rag_wizard():
    """RAGウィザードサーバントのテスト実行"""
    wizard = RAGWizardServant(
        name="test_rag_wizard",
        specialty="comprehensive_research",
        port=60102
    )
    
    try:
        await wizard.start()
        print(f"🧙‍♂️ RAG Wizard Servant running: {wizard.name} on port {wizard.port}")
        print(f"RAG Tools Available: {wizard.rag_tools.keys() if wizard.rag_tools else 'None'}")
        
        # テスト実行
        test_result = await wizard.execute_specialized_task(
            "comprehensive_research",
            {
                "topic": "AI development trends",
                "scope": "comprehensive",
                "depth": "moderate"
            },
            {"knowledge_sage": {"status": "success", "recommendations": ["Use AI patterns"]}}
        )
        print(f"✅ Test result: {test_result['status']} - {test_result.get('sources_count', 0)} sources")
        
        # 能力確認
        capabilities = await wizard.get_specialized_capabilities()
        print(f"🔧 RAG Wizard capabilities: {len(capabilities)} total")
        
        # 少し待機
        await asyncio.sleep(3)
        
    except KeyboardInterrupt:
        print("🛑 Shutting down RAG Wizard...")
    except Exception as e:
        print(f"❌ RAG Wizard test error: {e}")
    finally:
        await wizard.stop()


# エクスポート
__all__ = ["RAGWizardServant"]


if __name__ == "__main__":
    asyncio.run(test_rag_wizard())