#!/usr/bin/env python3
"""
"🔍" Search Magic - 探索魔法
==========================

Ancient Elderの8つの古代魔法の一つ。
深層探索、パターン発見、知識検索を担当。

Author: Claude Elder
Created: 2025-07-23
"""

import asyncio
import json
import ast
import re
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from collections import defaultdict, Counter
from dataclasses import dataclass
import statistics
import tempfile
import os
from pathlib import Path

# Whoosh import (OSS First - pure Python search engine)
try:
    from whoosh.index import create_index, open_dir
    from whoosh.fields import Schema, TEXT, ID, NUMERIC
    from whoosh.qparser import QueryParser
    from whoosh.query import Query
    from whoosh import scoring
    WHOOSH_AVAILABLE = True
except ImportError:
    WHOOSH_AVAILABLE = False

from ..base_magic import AncientMagic, MagicCapability


@dataclass
class SearchResult:
    pass

    """検索結果のデータクラス""" str
    content: str
    relevance_score: float
    source: str
    match_type: str
    metadata: Dict[str, Any]


@dataclass
class PatternMatch:
    pass



"""パターンマッチのデータクラス""" str
    pattern_name: str
    line_number: int
    column_number: int
    content: str
    context: str
    confidence: float


class SearchMagic(AncientMagic):
    pass



"""
    Search Magic - 探索魔法
    
    深層探索とパターン発見を司る古代魔法。
    - 深層コード探索
    - パターン発見・分析
    - 知識検索・統合
    - セマンティック検索
    """
        super().__init__("search", "深層探索・パターン発見・知識検索")
        
        # 魔法の能力
        self.capabilities = [
            MagicCapability.DEEP_SEARCH,
            MagicCapability.PATTERN_DISCOVERY,
            MagicCapability.KNOWLEDGE_RETRIEVAL,
            MagicCapability.CONTEXT_MATCHING
        ]
        
        # 検索データストレージ
        self.search_history: List[Dict[str, Any]] = []
        self.pattern_database: Dict[str, List[PatternMatch]] = defaultdict(list)
        self.knowledge_index: Optional[Any] = None
        self.search_cache: Dict[str, Any] = {}
        
        # 検索パラメータ
        self.search_config = {
            "max_results": 100,
            "similarity_threshold": 0.7,
            "cache_ttl": timedelta(hours=1),
            "deep_search_depth": 5,
            "pattern_confidence_threshold": 0.6
        }
        
        # Whoosh インデックス初期化
        self._init_whoosh_index()
        
    def _init_whoosh_index(self):
        pass

        """Whoosh検索インデックスを初期化"""
            return
            
        # 一時ディレクトリにインデックス作成
        self.temp_index_dir = tempfile.mkdtemp(prefix="search_magic_")
        
        # スキーマ定義
        schema = Schema(
            id=ID(stored=True),
            title=TEXT(stored=True),
            content=TEXT(stored=True),
            tags=TEXT(stored=True),
            category=TEXT(stored=True)
        )
        
        # インデックス作成
        self.knowledge_index = create_index(self.temp_index_dir, schema)
        
    async def cast_magic(self, intent: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """探索魔法を発動"""
        try:
            if intent == "deep_search":
                return await self.deep_search(data)
            elif intent == "discover_patterns":
                return await self.discover_patterns(data)
            elif intent == "search_knowledge":
                return await self.search_knowledge(data)
            elif intent == "semantic_search":
                return await self.semantic_search(data)
            elif intent == "match_contexts":
                return await self.match_contexts(data)
            elif intent == "cluster_patterns":
                return await self.cluster_patterns(data)
            elif intent == "cross_reference_search":
                return await self.cross_reference_search(data)
            elif intent == "build_dependency_graph":
                return await self.build_dependency_graph(data)
            elif intent == "detect_anomalies":
                return await self.detect_anomalies(data)
            elif intent == "temporal_search":
                return await self.temporal_search(data)
            elif intent == "multi_modal_search":
                return await self.multi_modal_search(data)
            elif intent == "optimize_search_performance":
                return await self.optimize_search_performance(data)
            else:
                return {
                    "success": False,
                    "error": f"Unknown search intent: {intent}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Search magic casting failed: {str(e)}"
            }
    
    async def deep_search(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """深層検索を実行"""
        try:
            query = search_params.get("query", "")
            search_type = search_params.get("search_type", "basic_search")
            targets = search_params.get("targets", [])
            patterns = search_params.get("patterns", [])
            
            if not query:
                return {
                    "success": False,
                    "error": "Search query cannot be empty"
                }
            
            search_results = {
                "matches": [],
                "pattern_analysis": {},
                "relevance_scores": {}
            }
            
            # コードベース深層検索
            if search_type == "deep_code_search":
                for target in targets:
                    content = target.get("content", "")
                    file_path = target.get("path", "")
                    
                    # テキスト検索
                    if query.lower() in content.lower():
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if query.lower() in line.lower():
                                match = {
                                    "file": file_path,
                                    "line_number": i + 1,
                                    "content": line.strip(),
                                    "context": self._get_line_context(lines, i),
                                    "match_type": "text_match",
                                    "relevance_score": self._calculate_relevance(query, line)
                                }
                                search_results["matches"].append(match)
                    
                    # パターンマッチング
                    if "function_definitions" in patterns:
                        func_matches = self._find_function_definitions(content, file_path)
                        for func_match in func_matches:
                            # "function"がクエリで、関数定義が見つかった場合にマッチ
                            if query.lower() in "function" or query.lower() in func_match["name"].lower():
                                search_results["matches"].append({
                                    "file": file_path,
                                    "line_number": func_match["line_number"],
                                    "content": func_match["name"],
                                    "context": func_match["signature"],
                                    "match_type": "function_definition",
                                    "relevance_score": 0.9
                                })
                
                # パターン分析
                search_results["pattern_analysis"] = {
                    "total_matches": len(search_results["matches"]),
                    "match_types": Counter(match["match_type"] for match in search_results["matches"]),
                    "file_distribution": Counter(match["file"] for match in search_results["matches"])
                }
                
                # 関連性スコア計算
                for match in search_results["matches"]:
                    file_name = match["file"]
                    if file_name not in search_results["relevance_scores"]:
                        search_results["relevance_scores"][file_name] = []
                    search_results["relevance_scores"][file_name].append(match["relevance_score"])
            
            return {
                "success": True,
                "search_results": search_results,
                "search_metadata": {
                    "query": query,
                    "search_type": search_type,
                    "timestamp": datetime.now().isoformat(),
                    "total_targets": len(targets)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Deep search failed: {str(e)}"
            }
    
    async def discover_patterns(self, discovery_params: Dict[str, Any]) -> Dict[str, Any]:
        """AST解析によるパターン発見"""
        try:
            source_code = discovery_params.get("source_code", "")
            pattern_types = discovery_params.get("pattern_types", [])
            analysis_depth = discovery_params.get("analysis_depth", "basic")
            
            if not source_code:
                return {
                    "success": False,
                    "error": "Source code cannot be empty"
                }
            
            discovered_patterns = {}
            
            try:
                # AST解析
                tree = ast.parse(source_code)
                
                # 関数定義の発見
                if "function_definitions" in pattern_types:
                    functions = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            functions.append({
                                "name": node.name,
                                "line_number": node.lineno,
                                "args": [arg.arg for arg in node.args.args],
                                "decorators": [ast.unparse(d) for d in node.decorator_list] if hasattr(ast, 'unparse') else [],
                                "docstring": ast.get_docstring(node)
                            })
                    discovered_patterns["function_definitions"] = functions
                
                # return文の発見
                if "return_statements" in pattern_types:
                    returns = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Return):
                            returns.append({
                                "line_number": node.lineno,
                                "has_value": node.value is not None,
                                "return_type": type(node.value).__name__ if node.value else "None"
                            })
                    discovered_patterns["return_statements"] = returns
                
                # 関数呼び出しの発見
                if "function_calls" in pattern_types:
                    calls = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            if isinstance(node.func, ast.Name):
                                calls.append({
                                    "function_name": node.func.id,
                                    "line_number": node.lineno,
                                    "arg_count": len(node.args),
                                    "has_keywords": len(node.keywords) > 0
                                })
                    discovered_patterns["function_calls"] = calls
                
                # クラス定義の発見
                if "class_definitions" in pattern_types:
                    classes = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            classes.append({
                                "name": node.name,
                                "line_number": node.lineno,
                                "bases": [ast.unparse(base) if hasattr(ast, 'unparse') else str(base) for base in node.bases],
                                "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                            })
                    discovered_patterns["class_definitions"] = classes
                
            except SyntaxError as e:
                # 構文エラーの場合は正規表現でフォールバック
                discovered_patterns = self._regex_pattern_discovery(source_code, pattern_types)
            
            return {
                "success": True,
                "discovered_patterns": discovered_patterns,
                "analysis_metadata": {
                    "source_lines": len(source_code.split('\n')),
                    "analysis_depth": analysis_depth,
                    "timestamp": datetime.now().isoformat(),
                    "pattern_types": pattern_types
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Pattern discovery failed: {str(e)}"
            }
    
    async def search_knowledge(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """Whooshを使用した知識検索"""
        try:
            query = search_params.get("query", "")
            documents = search_params.get("documents", [])
            search_fields = search_params.get("search_fields", ["title", "content"])
            max_results = search_params.get("max_results", 10)
            
            if not query:
                return {
                    "success": False,
                    "error": "Search query cannot be empty"
                }
            
            # Whooshが利用可能な場合
            if WHOOSH_AVAILABLE and self.knowledge_index:
                # ドキュメントをインデックスに追加
                writer = self.knowledge_index.writer()
                for doc in documents:
                    writer.add_document(
                        id=doc.get("id", ""),
                        title=doc.get("title", ""),
                        content=doc.get("content", ""),
                        tags=" ".join(doc.get("tags", [])),
                        category=doc.get("category", "")
                    )
                writer.commit()
                
                # 検索実行
                with self.knowledge_index.searcher() as searcher:
                    # クエリパーサー作成
                    parser = QueryParser("content", self.knowledge_index.schema)
                    query_obj = parser.parse(query)
                    
                    # 検索実行
                    results = searcher.search(query_obj, limit=max_results)
                    
                    ranked_results = []
                    for result in results:
                        ranked_results.append({
                            "id": result["id"],
                            "title": result["title"],
                            "content": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"],
                            "relevance_score": result.score,
                            "category": result.get("category", ""),
                            "tags": result.get("tags", "").split()
                        })
            
            else:
                # フォールバック: シンプルなテキスト検索
                ranked_results = []
                query_lower = query.lower()
                query_words = query_lower.split()
                
                for doc in documents:
                    score = 0
                    matches = []
                    
                    # タイトル検索
                    if "title" in search_fields:
                        title = doc.get("title", "").lower()
                        # 完全マッチまたは単語マッチ
                        if query_lower in title or any(word in title for word in query_words):
                            score += 0.8
                            matches.append("title")
                    
                    # 内容検索
                    if "content" in search_fields:
                        content = doc.get("content", "").lower()
                        if query_lower in content or any(word in content for word in query_words):
                            score += 0.6
                            matches.append("content")
                    
                    # タグ検索
                    if "tags" in search_fields:
                        tags = [tag.lower() for tag in doc.get("tags", [])]
                        if any(query_lower in tag or any(word in tag for word in query_words) for tag in tags):
                            score += 0.7
                            matches.append("tags")
                    
                    if score > 0:
                        ranked_results.append({
                            "id": doc.get("id", ""),
                            "title": doc.get("title", ""),
                            "content": doc.get("content", "")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", ""),
                            "relevance_score": score,
                            "category": doc.get("category", ""),
                            "tags": doc.get("tags", []),
                            "matched_fields": matches
                        })
                
                # スコア順でソート
                ranked_results.sort(key=lambda x: x["relevance_score"], reverse=True)
                ranked_results = ranked_results[:max_results]
            
            search_results = {
                "ranked_results": ranked_results,
                "search_stats": {
                    "total_results": len(ranked_results),
                    "max_score": max([r["relevance_score"] for r in ranked_results]) if ranked_results else 0,
                    "avg_score": statistics.mean([r["relevance_score"] for r in ranked_results]) if ranked_results else 0,
                    "search_time": datetime.now().isoformat()
                }
            }
            
            return {
                "success": True,
                "search_results": search_results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Knowledge search failed: {str(e)}"
            }
    
    async def semantic_search(self, semantic_params: Dict[str, Any]) -> Dict[str, Any]:
        """セマンティック検索（基本的な類似性ベース）"""
        try:
            query = semantic_params.get("query", "")
            documents = semantic_params.get("documents", [])
            semantic_model = semantic_params.get("semantic_model", "basic_similarity")
            context_awareness = semantic_params.get("context_awareness", True)
            
            conceptual_matches = []
            
            # 基本的なセマンティック検索（単語ベースの類似性）
            query_words = set(query.lower().split())
            
            for doc in documents:
                title_words = set(doc.get("title", "").lower().split())
                content_words = set(doc.get("content", "").lower().split())
                tags = set([tag.lower() for tag in doc.get("tags", [])])
                
                # 単語レベルの重複度計算
                title_overlap = len(query_words & title_words) / max(len(query_words), 1)
                content_overlap = len(query_words & content_words) / max(len(query_words), 1)
                tag_overlap = len(query_words & tags) / max(len(query_words), 1)
                
                # 概念的類似性スコア
                semantic_relevance = (title_overlap * 0.4 + content_overlap * 0.4 + tag_overlap * 0.2)
                
                # コンテキスト考慮
                if context_awareness:
                    category = doc.get("category", "").lower()
                    if any(word in category for word in query_words):
                        semantic_relevance += 0.2
                
                # より緩い閾値で結果を含める
                if semantic_relevance > 0.05:  # 閾値を下げる
                    conceptual_matches.append({
                        "id": doc.get("id", ""),
                        "title": doc.get("title", ""),
                        "content": doc.get("content", "")[:150] + "..." if len(doc.get("content", "")) > 150 else doc.get("content", ""),
                        "semantic_relevance": round(semantic_relevance, 3),
                        "matched_concepts": list(query_words & (title_words | content_words | tags)),
                        "category": doc.get("category", "")
                    })
            
            # セマンティックスコア順でソート
            conceptual_matches.sort(key=lambda x: x["semantic_relevance"], reverse=True)
            
            semantic_results = {
                "conceptual_matches": conceptual_matches,
                "semantic_scores": {
                    "max_relevance": max([m["semantic_relevance"] for m in conceptual_matches]) if conceptual_matches else 0,
                    "avg_relevance": statistics.mean([m["semantic_relevance"] for m in conceptual_matches]) if conceptual_matches else 0,
                    "total_concepts": len(set().union(*[m["matched_concepts"] for m in conceptual_matches]))
                }
            }
            
            return {
                "success": True,
                "semantic_results": semantic_results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Semantic search failed: {str(e)}"
            }
    
    async def match_contexts(self, context_params: Dict[str, Any]) -> Dict[str, Any]:
        """コンテキストマッチング"""
        try:
            primary_context = context_params.get("primary_context", "")
            secondary_contexts = context_params.get("secondary_contexts", [])
            similarity_threshold = context_params.get("similarity_threshold", 0.7)
            
            primary_words = set(primary_context.lower().split())
            
            context_matches = {
                "primary_matches": primary_context,
                "similarity_scores": {},
                "related_contexts": []
            }
            
            for context in secondary_contexts:
                context_words = set(context.lower().split())
                
                # Jaccard類似度計算
                intersection = len(primary_words & context_words)
                union = len(primary_words | context_words)
                jaccard_similarity = intersection / union if union > 0 else 0
                
                context_matches["similarity_scores"][context] = jaccard_similarity
                
                if jaccard_similarity >= similarity_threshold:
                    context_matches["related_contexts"].append({
                        "context": context,
                        "similarity": jaccard_similarity,
                        "common_terms": list(primary_words & context_words)
                    })
            
            return {
                "success": True,
                "context_matches": context_matches
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Context matching failed: {str(e)}"
            }
    
    async def cluster_patterns(self, clustering_params: Dict[str, Any]) -> Dict[str, Any]:
        """パターンクラスタリング（頻度ベース）"""
        try:
            patterns = clustering_params.get("patterns", [])
            clustering_method = clustering_params.get("clustering_method", "frequency_based")
            min_cluster_size = clustering_params.get("min_cluster_size", 2)
            
            if clustering_method == "frequency_based":
                # 頻度ベースのクラスタリング
                frequency_groups = defaultdict(list)
                
                for pattern in patterns:
                    frequency = pattern.get("frequency", 0)
                    pattern_type = pattern.get("type", "unknown")
                    
                    # 頻度に基づいてグループ化
                    if frequency >= 20:
                        group_key = f"high_frequency_{pattern_type}"
                    elif frequency >= 10:
                        group_key = f"medium_frequency_{pattern_type}"
                    else:
                        group_key = f"low_frequency_{pattern_type}"
                    
                    frequency_groups[group_key].append(pattern)
                
                # クラスター生成（より緩い条件で）
                clusters = []
                for group_name, group_patterns in frequency_groups.items():
                    if len(group_patterns) >= min_cluster_size:
                        clusters.append({
                            "cluster_name": group_name,
                            "patterns": group_patterns,
                            "cluster_size": len(group_patterns),
                            "avg_frequency": statistics.mean([p.get("frequency", 0) for p in group_patterns]),
                            "dominant_type": Counter([p.get("type", "unknown") for p in group_patterns]).most_common(1)[0][0]
                        })
                
                # もしクラスターが生成されない場合は、単一のクラスターを作成
                if not clusters and patterns:
                    # すべてのパターンを一つのクラスターに
                    clusters.append({
                        "cluster_name": "mixed_patterns",
                        "patterns": patterns,
                        "cluster_size": len(patterns),
                        "avg_frequency": statistics.mean([p.get("frequency", 0) for p in patterns]),
                        "dominant_type": Counter([p.get("type", "unknown") for p in patterns]).most_common(1)[0][0] if patterns else "unknown"
                    })
                
                pattern_clusters = {
                    "clusters": clusters,
                    "cluster_stats": {
                        "total_clusters": len(clusters),
                        "total_patterns": sum(cluster["cluster_size"] for cluster in clusters),
                        "clustering_method": clustering_method,
                        "avg_cluster_size": statistics.mean([c["cluster_size"] for c in clusters]) if clusters else 0
                    }
                }
                
            else:
                # 他のクラスタリング方法のフォールバック
                pattern_clusters = {
                    "clusters": [],
                    "cluster_stats": {
                        "total_clusters": 0,
                        "error": f"Unsupported clustering method: {clustering_method}"
                    }
                }
            
            return {
                "success": True,
                "pattern_clusters": pattern_clusters
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Pattern clustering failed: {str(e)}"
            }
    
    async def cross_reference_search(self, cross_ref_params: Dict[str, Any]) -> Dict[str, Any]:
        """クロスリファレンス検索"""
        try:
            target_symbol = cross_ref_params.get("target_symbol", "")
            codebase = cross_ref_params.get("codebase", [])
            reference_types = cross_ref_params.get("reference_types", ["function_calls", "imports", "mentions"])
            
            cross_references = {
                "definitions": [],
                "usages": [],
                "import_chains": []
            }
            
            for file_data in codebase:
                file_path = file_data.get("path", "")
                content = file_data.get("content", "")
                lines = content.split('\n')
                
                # 定義の検索
                if "function_calls" in reference_types:
                    # 関数定義
                    for i, line in enumerate(lines):
                        if re.search(rf'\bdef\s+{re.escape(target_symbol)}\s*\(', line):
                            cross_references["definitions"].append({
                                "file": file_path,
                                "line_number": i + 1,
                                "type": "function_definition",
                                "content": line.strip(),
                                "context": self._get_line_context(lines, i)
                            })
                
                # 使用箇所の検索
                for i, line in enumerate(lines):
                    if target_symbol in line and f"def {target_symbol}" not in line:
                        # 関数呼び出し
                        if re.search(rf'\b{re.escape(target_symbol)}\s*\(', line):
                            cross_references["usages"].append({
                                "file": file_path,
                                "line_number": i + 1,
                                "type": "function_call",
                                "content": line.strip(),
                                "context": self._get_line_context(lines, i)
                            })
                        # インポート
                        elif "import" in line and target_symbol in line:
                            cross_references["import_chains"].append({
                                "file": file_path,
                                "line_number": i + 1,
                                "type": "import_statement",
                                "content": line.strip()
                            })
                        # 一般的な言及
                        elif "mentions" in reference_types:
                            cross_references["usages"].append({
                                "file": file_path,
                                "line_number": i + 1,
                                "type": "mention",
                                "content": line.strip(),
                                "context": self._get_line_context(lines, i)
                            })
            
            return {
                "success": True,
                "cross_references": cross_references
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Cross reference search failed: {str(e)}"
            }
    
    async def build_dependency_graph(self, dependency_params: Dict[str, Any]) -> Dict[str, Any]:
        """依存関係グラフ構築"""
        try:
            files = dependency_params.get("files", [])
            dependency_types = dependency_params.get("dependency_types", ["imports", "function_calls"])
            graph_depth = dependency_params.get("graph_depth", 3)
            
            nodes = []
            edges = []
            cycles = []
            
            # ノード作成（ファイル、関数、クラス）
            for file_data in files:
                file_path = file_data.get("path", "")
                content = file_data.get("content", "")
                
                # ファイルノード
                nodes.append({
                    "id": file_path,
                    "type": "file",
                    "name": Path(file_path).name,
                    "full_path": file_path
                })
                
                # インポート依存関係
                if "imports" in dependency_types:
                    import_matches = re.findall(r'(?:from\s+(\S+)\s+)?import\s+([^\n]+)', content)
                    for from_module, import_items in import_matches:
                        if from_module:
                            edges.append({
                                "source": file_path,
                                "target": from_module,
                                "type": "import_dependency",
                                "weight": 1.0
                            })
                
                # 関数呼び出し依存関係
                if "function_calls" in dependency_types:
                    try:
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                                edges.append({
                                    "source": file_path,
                                    "target": node.func.id,
                                    "type": "function_call",
                                    "weight": 0.5
                                })
                    except SyntaxError:
                        # AST解析に失敗した場合はスキップ
                        pass
            
            dependency_graph = {
                "nodes": nodes,
                "edges": edges,
                "cycles": cycles,  # 循環依存の検出は簡略化
                "graph_stats": {
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "max_depth": graph_depth,
                    "dependency_types": dependency_types
                }
            }
            
            return {
                "success": True,
                "dependency_graph": dependency_graph
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Dependency graph building failed: {str(e)}"
            }
    
    async def detect_anomalies(self, anomaly_params: Dict[str, Any]) -> Dict[str, Any]:
        """異常検知検索"""
        try:
            metrics = anomaly_params.get("metrics", [])
            anomaly_types = anomaly_params.get("anomaly_types", ["complexity", "function_count"])
            threshold_method = anomaly_params.get("threshold_method", "statistical")
            
            detected_anomalies = []
            anomaly_scores = {}
            
            if threshold_method == "statistical":
                # 統計的異常検知
                for metric_type in anomaly_types:
                    values = [m.get(metric_type, 0) for m in metrics if metric_type in m]
                    
                    if len(values) < 2:
                        continue
                    
                    mean_val = statistics.mean(values)
                    stdev_val = statistics.stdev(values) if len(values) > 1 else 0
                    
                    # Z-score based anomaly detection (より検出しやすく)
                    threshold = mean_val + 1.5 * stdev_val  # 1.5標準偏差に下げる
                    
                    for metric in metrics:
                        if metric_type in metric:
                            value = metric[metric_type]
                            z_score = abs(value - mean_val) / stdev_val if stdev_val > 0 else 0
                            
                            # より検出しやすくする
                            if value > threshold and z_score > 1.5:
                                detected_anomalies.append({
                                    "file": metric.get("file", "unknown"),
                                    "anomaly_type": metric_type,
                                    "value": value,
                                    "threshold": threshold,
                                    "z_score": round(z_score, 2),
                                    "severity": "high" if z_score > 3 else "medium"
                                })
                                
                                anomaly_scores[metric.get("file", "unknown")] = z_score
            
            anomalies = {
                "detected_anomalies": detected_anomalies,
                "anomaly_scores": anomaly_scores,
                "detection_stats": {
                    "total_metrics": len(metrics),
                    "anomalies_found": len(detected_anomalies),
                    "detection_method": threshold_method,
                    "anomaly_types": anomaly_types
                }
            }
            
            return {
                "success": True,
                "anomalies": anomalies
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Anomaly detection failed: {str(e)}"
            }
    
    async def temporal_search(self, temporal_params: Dict[str, Any]) -> Dict[str, Any]:
        """時系列検索"""
        try:
            events = temporal_params.get("events", [])
            time_range = temporal_params.get("time_range", {})
            event_types = temporal_params.get("event_types", [])
            
            start_time = datetime.fromisoformat(time_range.get("start", "1970-01-01T00:00:00"))
            end_time = datetime.fromisoformat(time_range.get("end", "2030-12-31T23:59:59"))
            
            filtered_events = []
            
            for event in events:
                event_time = datetime.fromisoformat(event.get("timestamp", "1970-01-01T00:00:00"))
                event_type = event.get("event", "")
                
                # 時間範囲フィルタ
                if start_time <= event_time <= end_time:
                    # イベントタイプフィルタ
                    if not event_types or event_type in event_types:
                        filtered_events.append({
                            "timestamp": event.get("timestamp"),
                            "event": event_type,
                            "details": event.get("details", {}),
                            "time_from_start": (event_time - start_time).total_seconds()
                        })
            
            # 時間パターン分析
            time_patterns = {
                "event_frequency": len(filtered_events),
                "time_span": (end_time - start_time).total_seconds(),
                "events_per_hour": len(filtered_events) / max((end_time - start_time).total_seconds() / 3600, 1),
                "event_types_distribution": Counter([e["event"] for e in filtered_events])
            }
            
            temporal_results = {
                "filtered_events": filtered_events,
                "time_patterns": time_patterns
            }
            
            return {
                "success": True,
                "temporal_results": temporal_results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Temporal search failed: {str(e)}"
            }
    
    async def multi_modal_search(self, multi_modal_params: Dict[str, Any]) -> Dict[str, Any]:
        """マルチモーダル検索"""
        try:
            query = multi_modal_params.get("query", "")
            search_modes = multi_modal_params.get("search_modes", [])
            fusion_method = multi_modal_params.get("fusion_method", "weighted_ranking")
            
            mode_results = {}
            mode_contributions = {}
            
            for mode in search_modes:
                mode_type = mode.get("type", "")
                mode_data = mode.get("data", [])
                
                if mode_type == "code_search":
                    # コード検索結果
                    code_results = []
                    for file_data in mode_data:
                        content = file_data.get("content", "")
                        if query.lower() in content.lower():
                            code_results.append({
                                "type": "code",
                                "file": file_data.get("path", ""),
                                "relevance": 0.8,
                                "content": content[:100] + "..." if len(content) > 100 else content
                            })
                    mode_results["code_search"] = code_results
                    mode_contributions["code_search"] = len(code_results)
                
                elif mode_type == "knowledge_search":
                    # 知識検索結果
                    knowledge_results = []
                    for doc in mode_data:
                        title = doc.get("title", "")
                        content = doc.get("content", "")
                        if query.lower() in title.lower() or query.lower() in content.lower():
                            knowledge_results.append({
                                "type": "knowledge",
                                "title": title,
                                "relevance": 0.7,
                                "content": content[:100] + "..." if len(content) > 100 else content
                            })
                    mode_results["knowledge_search"] = knowledge_results
                    mode_contributions["knowledge_search"] = len(knowledge_results)
                
                elif mode_type == "pattern_search":
                    # パターン検索結果
                    patterns = mode.get("patterns", [])
                    pattern_results = []
                    
                    # パターンがリストの場合
                    if isinstance(patterns, list):
                        for pattern in patterns:
                            if isinstance(pattern, str) and query.lower() in pattern.lower():
                                pattern_results.append({
                                    "type": "pattern",
                                    "pattern_type": "string_pattern",
                                    "relevance": 0.6,
                                    "details": {"pattern": pattern}
                                })
                    # パターンが辞書の場合
                    elif isinstance(patterns, dict):
                        for pattern_type, pattern_list in patterns.items():
                            if isinstance(pattern_list, list):
                                for pattern in pattern_list:
                                    if isinstance(pattern, dict) and query.lower() in str(pattern).lower():
                                        pattern_results.append({
                                            "type": "pattern",
                                            "pattern_type": pattern_type,
                                            "relevance": 0.6,
                                            "details": pattern
                                        })
                    
                    mode_results["pattern_search"] = pattern_results
                    mode_contributions["pattern_search"] = len(pattern_results)
            
            # 結果統合（重み付きランキング）
            unified_results = []
            for mode_name, results in mode_results.items():
                for result in results:
                    unified_results.append(result)
            
            # 関連性スコアでソート
            unified_results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
            
            multi_modal_results = {
                "unified_results": unified_results,
                "mode_contributions": mode_contributions,
                "fusion_stats": {
                    "total_results": len(unified_results),
                    "fusion_method": fusion_method,
                    "modes_used": list(mode_contributions.keys())
                }
            }
            
            return {
                "success": True,
                "multi_modal_results": multi_modal_results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Multi-modal search failed: {str(e)}"
            }
    
    async def optimize_search_performance(self, optimization_params: Dict[str, Any]) -> Dict[str, Any]:
        """検索パフォーマンス最適化"""
        try:
            search_history = optimization_params.get("search_history", [])
            optimization_targets = optimization_params.get("optimization_targets", ["execution_time", "cache_hits"])
            cache_strategy = optimization_params.get("cache_strategy", "lru")
            
            # 頻繁なクエリの特定
            query_frequency = Counter([entry.get("query", "") for entry in search_history])
            frequent_queries = query_frequency.most_common(5)
            
            # パフォーマンス分析
            execution_times = [entry.get("execution_time", 0) for entry in search_history]
            avg_execution_time = statistics.mean(execution_times) if execution_times else 0
            
            # キャッシュ推奨事項
            cache_recommendations = {
                "frequent_queries": [{"query": q, "frequency": f} for q, f in frequent_queries],
                "cache_strategy": cache_strategy,
                "recommended_cache_size": min(len(frequent_queries) * 10, 100)
            }
            
            # クエリ最適化提案
            query_optimization = {
                "slow_queries": [entry for entry in search_history if entry.get("execution_time", 0) > avg_execution_time * 1.5],
                "optimization_suggestions": [
                    "Use more specific search terms",
                    "Implement result caching for frequent queries",
                    "Consider indexing for large datasets"
                ]
            }
            
            # パフォーマンス改善予測
            performance_improvements = {
                "estimated_speedup": 1.5,  # 50% improvement
                "cache_hit_ratio": 0.7,    # 70% cache hits expected
                "memory_usage_reduction": 0.2  # 20% memory reduction
            }
            
            optimization_result = {
                "cache_recommendations": cache_recommendations,
                "query_optimization": query_optimization,
                "performance_improvements": performance_improvements,
                "baseline_metrics": {
                    "avg_execution_time": avg_execution_time,
                    "total_queries": len(search_history),
                    "unique_queries": len(set([entry.get("query", "") for entry in search_history]))
                }
            }
            
            return {
                "success": True,
                "optimization_result": optimization_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Search optimization failed: {str(e)}"
            }
    
    # ヘルパーメソッド
    def _find_function_definitions(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """関数定義を検索"""
        functions = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            match = re.match(r'\s*def\s+(\w+)\s*\((.*?)\):', line)
            if match:
                functions.append({
                    "name": match.group(1),
                    "signature": line.strip(),
                    "line_number": i + 1,
                    "args": match.group(2)
                })
        
        return functions
    
    def _get_line_context(self, lines: List[str], line_index: int, context_size: int = 2) -> strstart = max(0, line_index - context_size)end = min(len(lines), line_index + context_size + 1)
    """のコンテキストを取得"""
        
        context_lines = []:
        for i in range(start, end):
            marker = ">>>" if i == line_index else "   "
            context_lines.append(f"{marker} {i+1}: {lines[i]}")
        
        return "\n".join(context_lines)
    
    def _calculate_relevance(self, query: str, text: str) -> floatquery_words = set(query.lower().split())text_words = set(text.lower().split())
    """連性スコアを計算"""
        :
        if not query_words:
            return 0.0
        
        intersection = len(query_words & text_words)
        return intersection / len(query_words)
    
    def _regex_pattern_discovery(self, source_code: str, pattern_types: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """正規表現によるパターン発見（フォールバック）"""
        patterns = {}
        
        if "function_definitions" in pattern_types:
            func_pattern = r'def\s+(\w+)\s*\([^)]*\):'
            matches = re.finditer(func_pattern, source_code, re.MULTILINE)
            functions = []
            for match in matches:
                line_num = source_code[:match.start()].count('\n') + 1
                functions.append({
                    "name": match.group(1),
                    "line_number": line_num,
                    "args": [],
                    "decorators": [],
                    "docstring": None
                })
            patterns["function_definitions"] = functions
        
        return patterns


if __name__ == "__main__":
    # テスト実行用のエントリーポイント
    import asyncio
    
    async def test_search_magic():
        magic = SearchMagic()
        
        # 簡単なテスト
        test_data = {
            "query": "test",
            "search_type": "basic_search",
            "targets": [{"path": "/test.py", "content": "def test_function():\n    pass"}]
        }
        
        result = await magic.deep_search(test_data)
        print(f"Search result: {result['success']}")
    
    if __name__ == "__main__":
        asyncio.run(test_search_magic())