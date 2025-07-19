#!/usr/bin/env python3
"""
Elders Guild 統合RAG検索マネージャー v1.0
統一検索インターフェースによる横断的情報検索
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

# プロジェクトルートの設定
PROJECT_ROOT = Path(__file__).parent.parent

try:
    # 統合エンティティマネージャーをインポート
    from integration.unified_entity_manager import (
        BaseEntity,
        IncidentEntity,
        KnowledgeEntity,
        TaskEntity,
        UnifiedEntityManager,
    )
except ImportError:
    # フォールバック: 相対インポート
    from .unified_entity_manager import (
        BaseEntity,
        IncidentEntity,
        KnowledgeEntity,
        TaskEntity,
        UnifiedEntityManager,
    )

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SearchQuery:
    """検索クエリ"""

    text: str
    entity_types: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    limit: int = 20
    include_relationships: bool = True
    max_relationship_depth: int = 2
    semantic_threshold: float = 0.7
    intent: Optional[
        str
    ] = None  # 'problem_solving', 'knowledge_acquisition', 'history_lookup'


@dataclass
class SearchResult:
    """検索結果"""

    query: SearchQuery
    primary_results: List[BaseEntity]
    related_entities: List[BaseEntity]
    relationships: List[Dict[str, Any]]
    confidence_scores: Dict[str, float]
    assembled_context: str
    total_found: int
    search_time_ms: float
    suggestions: List[str] = None


@dataclass
class ContextAssemblyConfig:
    """コンテキスト組み立て設定"""

    max_context_length: int = 4000
    include_metadata: bool = True
    include_relationships: bool = True
    prioritize_recent: bool = True
    group_by_type: bool = True


class SearchPreprocessor:
    """検索前処理"""

    def __init__(self):
        self.intent_keywords = {
            "problem_solving": ["エラー", "問題", "解決", "修正", "エラー", "バグ", "失敗", "trouble"],
            "knowledge_acquisition": ["とは", "について", "方法", "やり方", "howto", "説明", "理解"],
            "history_lookup": ["前回", "過去", "履歴", "history", "以前", "先日", "before"],
        }

    def process(self, query: SearchQuery) -> SearchQuery:
        """クエリ前処理"""
        processed_query = SearchQuery(
            text=query.text,
            entity_types=query.entity_types,
            filters=query.filters,
            limit=query.limit,
            include_relationships=query.include_relationships,
            max_relationship_depth=query.max_relationship_depth,
            semantic_threshold=query.semantic_threshold,
            intent=query.intent,
        )

        # 意図分析
        if not processed_query.intent:
            processed_query.intent = self._detect_intent(query.text)

        # キーワード正規化
        processed_query.text = self._normalize_text(query.text)

        # フィルタ調整
        processed_query.filters = self._adjust_filters(
            processed_query.filters, processed_query.intent
        )

        return processed_query

    def _detect_intent(self, text: str) -> str:
        """意図検出"""
        text_lower = text.lower()

        intent_scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                intent_scores[intent] = score

        if intent_scores:
            return max(intent_scores.items(), key=lambda x: x[1])[0]

        return "general"

    def _normalize_text(self, text: str) -> str:
        """テキスト正規化"""
        # 基本的な正規化（将来的にはより高度な処理を追加）
        normalized = text.strip()
        # 全角英数字を半角に変換等の処理を追加可能
        return normalized

    def _adjust_filters(
        self, filters: Optional[Dict[str, Any]], intent: str
    ) -> Dict[str, Any]:
        """意図に基づくフィルタ調整"""
        if filters is None:
            filters = {}

        # 意図に基づく調整
        if intent == "problem_solving":
            # 問題解決時はインシデントと解決済み知識を優先
            if "priority" not in filters:
                filters["priority"] = ["high", "medium"]
        elif intent == "history_lookup":
            # 履歴参照時は時系列順を重視
            filters["sort_by"] = "created_at"
            filters["sort_order"] = "desc"

        return filters


class ContextAssembler:
    """コンテキスト組み立て"""

    def __init__(self, config: ContextAssemblyConfig = None):
        self.config = config or ContextAssemblyConfig()

    def assemble(
        self,
        primary_results: List[BaseEntity],
        related_entities: List[BaseEntity],
        relationships: List[Dict[str, Any]],
        query_intent: str,
    ) -> str:
        """コンテキスト組み立て"""

        context_parts = []
        current_length = 0

        # クエリ意図に基づく構成順序決定
        if query_intent == "problem_solving":
            # 問題解決: インシデント → 解決策 → 関連知識
            ordered_results = self._order_for_problem_solving(
                primary_results, related_entities
            )
        elif query_intent == "knowledge_acquisition":
            # 知識獲得: 知識 → 例 → 関連情報
            ordered_results = self._order_for_knowledge_acquisition(
                primary_results, related_entities
            )
        else:
            # 一般: 関連度順
            ordered_results = primary_results + related_entities

        # メインコンテンツ組み立て
        for entity in ordered_results:
            if current_length >= self.config.max_context_length:
                break

            part = self._format_entity(entity, relationships)
            if current_length + len(part) <= self.config.max_context_length:
                context_parts.append(part)
                current_length += len(part)

        # 関係性情報追加
        if self.config.include_relationships and relationships:
            rel_summary = self._format_relationship_summary(relationships)
            if current_length + len(rel_summary) <= self.config.max_context_length:
                context_parts.append("\n## 関連性情報\n" + rel_summary)

        return "\n\n".join(context_parts)

    def _order_for_problem_solving(
        self, primary: List[BaseEntity], related: List[BaseEntity]
    ) -> List[BaseEntity]:
        """問題解決向けの順序付け"""
        # インシデント → 解決策となる知識 → その他
        incidents = [e for e in primary + related if isinstance(e, IncidentEntity)]
        knowledge = [e for e in primary + related if isinstance(e, KnowledgeEntity)]
        others = [
            e
            for e in primary + related
            if not isinstance(e, (IncidentEntity, KnowledgeEntity))
        ]

        return incidents + knowledge + others

    def _order_for_knowledge_acquisition(
        self, primary: List[BaseEntity], related: List[BaseEntity]
    ) -> List[BaseEntity]:
        """知識獲得向けの順序付け"""
        # 信頼度の高い知識 → その他
        all_entities = primary + related
        knowledge_entities = [e for e in all_entities if isinstance(e, KnowledgeEntity)]
        other_entities = [e for e in all_entities if not isinstance(e, KnowledgeEntity)]

        # 知識エンティティを信頼度順にソート
        knowledge_entities.sort(
            key=lambda e: e.knowledge_data.get("confidence_score", 0.0), reverse=True
        )

        return knowledge_entities + other_entities

    def _format_entity(
        self, entity: BaseEntity, relationships: List[Dict[str, Any]]
    ) -> str:
        """エンティティのフォーマット"""
        formatted = f"### {entity.title}\n"
        formatted += f"**タイプ**: {entity.type}\n"

        if entity.content:
            formatted += f"**内容**: {entity.content}\n"

        # エンティティ固有情報
        if isinstance(entity, KnowledgeEntity):
            formatted += (
                f"**信頼度**: {entity.knowledge_data.get('confidence_score', 0.0):.2f}\n"
            )
            formatted += f"**ドメイン**: {entity.knowledge_data.get('domain', 'general')}\n"
        elif isinstance(entity, IncidentEntity):
            formatted += f"**重要度**: {entity.incident_data.get('severity', 'unknown')}\n"
            formatted += f"**ステータス**: {entity.incident_data.get('status', 'unknown')}\n"
        elif isinstance(entity, TaskEntity):
            formatted += f"**タスクタイプ**: {entity.task_data.get('task_type', 'general')}\n"
            formatted += (
                f"**進捗**: {entity.task_data.get('completion_percentage', 0)}%\n"
            )

        # メタデータ
        if self.config.include_metadata and entity.metadata:
            formatted += f"**作成日**: {entity.created_at.strftime('%Y-%m-%d %H:%M') if entity.created_at else 'unknown'}\n"
            if entity.metadata.get("tags"):
                formatted += f"**タグ**: {', '.join(entity.metadata['tags'])}\n"

        return formatted

    def _format_relationship_summary(self, relationships: List[Dict[str, Any]]) -> str:
        """関係性サマリーのフォーマット"""
        rel_counts = {}
        for rel in relationships:
            rel_type = rel.get("relationship_type", "unknown")
            rel_counts[rel_type] = rel_counts.get(rel_type, 0) + 1

        summary = "- " + "\n- ".join(
            [f"{rel_type}: {count}件" for rel_type, count in rel_counts.items()]
        )

        return summary


class UnifiedRAGManager:
    """統合RAG検索マネージャー"""

    def __init__(self, entity_manager: UnifiedEntityManager = None):
        self.entity_manager = entity_manager or UnifiedEntityManager()
        self.preprocessor = SearchPreprocessor()
        self.context_assembler = ContextAssembler()

        # 検索履歴とキャッシュ
        self.search_history: List[Dict[str, Any]] = []
        self.search_cache: Dict[str, SearchResult] = {}
        self.cache_max_size = 100

        logger.info("UnifiedRAGManager initialized")

    async def search(self, query: Union[str, SearchQuery]) -> SearchResult:
        """統合検索実行"""
        start_time = datetime.now()

        try:
            # クエリ正規化
            if isinstance(query, str):
                search_query = SearchQuery(text=query)
            else:
                search_query = query

            # キャッシュチェック
            cache_key = self._generate_cache_key(search_query)
            if cache_key in self.search_cache:
                logger.info(f"Cache hit for query: {search_query.text[:50]}...")
                return self.search_cache[cache_key]

            # 前処理
            processed_query = self.preprocessor.process(search_query)

            # メイン検索実行
            primary_results = await self._execute_primary_search(processed_query)

            # 関連エンティティ検索
            related_entities = []
            relationships = []

            if processed_query.include_relationships and primary_results:
                (
                    related_entities,
                    relationships,
                ) = await self._execute_relationship_search(
                    primary_results, processed_query
                )

            # 信頼度スコア計算
            confidence_scores = self._calculate_confidence_scores(
                primary_results, related_entities, processed_query
            )

            # コンテキスト組み立て
            assembled_context = self.context_assembler.assemble(
                primary_results, related_entities, relationships, processed_query.intent
            )

            # 検索結果作成
            search_time = (datetime.now() - start_time).total_seconds() * 1000

            result = SearchResult(
                query=processed_query,
                primary_results=primary_results,
                related_entities=related_entities,
                relationships=relationships,
                confidence_scores=confidence_scores,
                assembled_context=assembled_context,
                total_found=len(primary_results) + len(related_entities),
                search_time_ms=search_time,
                suggestions=self._generate_suggestions(
                    processed_query, primary_results
                ),
            )

            # キャッシュ保存
            self._cache_result(cache_key, result)

            # 検索履歴記録
            self._record_search_history(processed_query, result)

            logger.info(
                f"Search completed: {len(primary_results)} primary, {len(related_entities)} related"
            )
            return result

        except Exception as e:
            logger.error(f"Search failed: {e}")
            # エラー時は空の結果を返す
            search_time = (datetime.now() - start_time).total_seconds() * 1000
            return SearchResult(
                query=search_query,
                primary_results=[],
                related_entities=[],
                relationships=[],
                confidence_scores={},
                assembled_context="検索中にエラーが発生しました。",
                total_found=0,
                search_time_ms=search_time,
                suggestions=[],
            )

    async def _execute_primary_search(self, query: SearchQuery) -> List[BaseEntity]:
        """メイン検索実行"""
        try:
            # エンティティマネージャーを使用した検索
            results = self.entity_manager.search_entities(
                query=query.text, entity_types=query.entity_types, limit=query.limit
            )

            # フィルタ適用
            if query.filters:
                results = self._apply_filters(results, query.filters)

            return results

        except Exception as e:
            logger.error(f"Primary search failed: {e}")
            return []

    async def _execute_relationship_search(
        self, primary_results: List[BaseEntity], query: SearchQuery
    ) -> Tuple[List[BaseEntity], List[Dict[str, Any]]]:
        """関係性検索実行"""
        try:
            related_entities = []
            all_relationships = []

            for entity in primary_results:
                # 関連エンティティ取得
                entity_related = self.entity_manager.find_related_entities(
                    entity.id, max_depth=query.max_relationship_depth
                )
                related_entities.extend(entity_related)

                # 関係性取得
                entity_rels = self.entity_manager.get_relationships(entity.id)
                for rel in entity_rels:
                    all_relationships.append(
                        {
                            "source_id": rel.source_id,
                            "target_id": rel.target_id,
                            "relationship_type": rel.relationship_type,
                            "weight": rel.weight,
                            "metadata": rel.metadata,
                        }
                    )

            # 重複除去
            seen_ids = {e.id for e in primary_results}
            unique_related = []
            for entity in related_entities:
                if entity.id not in seen_ids:
                    unique_related.append(entity)
                    seen_ids.add(entity.id)

            return unique_related, all_relationships

        except Exception as e:
            logger.error(f"Relationship search failed: {e}")
            return [], []

    def _apply_filters(
        self, entities: List[BaseEntity], filters: Dict[str, Any]
    ) -> List[BaseEntity]:
        """フィルタ適用"""
        filtered = entities

        for filter_key, filter_value in filters.items():
            if filter_key == "status":
                filtered = [
                    e for e in filtered if e.metadata.get("status") == filter_value
                ]
            elif filter_key == "priority":
                if isinstance(filter_value, list):
                    filtered = [
                        e
                        for e in filtered
                        if e.metadata.get("priority") in filter_value
                    ]
                else:
                    filtered = [
                        e
                        for e in filtered
                        if e.metadata.get("priority") == filter_value
                    ]
            elif filter_key == "category":
                filtered = [
                    e for e in filtered if e.metadata.get("category") == filter_value
                ]
            elif filter_key == "tags":
                if isinstance(filter_value, list):
                    filtered = [
                        e
                        for e in filtered
                        if any(
                            tag in e.metadata.get("tags", []) for tag in filter_value
                        )
                    ]
                else:
                    filtered = [
                        e
                        for e in filtered
                        if filter_value in e.metadata.get("tags", [])
                    ]

        return filtered

    def _calculate_confidence_scores(
        self,
        primary_results: List[BaseEntity],
        related_entities: List[BaseEntity],
        query: SearchQuery,
    ) -> Dict[str, float]:
        """信頼度スコア計算"""
        scores = {}

        # プライマリ結果は基本スコア高め
        for entity in primary_results:
            base_score = 0.8

            # エンティティタイプ別調整
            if isinstance(entity, KnowledgeEntity):
                base_score *= entity.knowledge_data.get("confidence_score", 0.8)
            elif isinstance(entity, IncidentEntity):
                # 解決済みインシデントは高スコア
                if entity.incident_data.get("status") == "resolved":
                    base_score *= 0.9
                else:
                    base_score *= 0.7

            scores[entity.id] = min(1.0, base_score)

        # 関連エンティティは距離に応じて減衰
        for entity in related_entities:
            base_score = 0.6  # 関連エンティティは少し低め

            if isinstance(entity, KnowledgeEntity):
                base_score *= entity.knowledge_data.get("confidence_score", 0.8)

            scores[entity.id] = min(1.0, base_score)

        return scores

    def _generate_suggestions(
        self, query: SearchQuery, results: List[BaseEntity]
    ) -> List[str]:
        """検索提案生成"""
        suggestions = []

        # 結果が少ない場合の提案
        if len(results) < 3:
            suggestions.append("より一般的なキーワードで検索してみてください")

            # エンティティタイプ制限がある場合
            if query.entity_types:
                suggestions.append("検索対象を全エンティティタイプに拡張してみてください")

        # 結果からの関連提案
        if results:
            # よく使われるタグを抽出
            all_tags = []
            for entity in results:
                all_tags.extend(entity.metadata.get("tags", []))

            if all_tags:
                from collections import Counter

                common_tags = Counter(all_tags).most_common(3)
                tag_suggestions = [f"'{tag}' での検索" for tag, _ in common_tags]
                suggestions.extend(tag_suggestions)

        return suggestions[:5]  # 最大5個

    def _generate_cache_key(self, query: SearchQuery) -> str:
        """キャッシュキー生成"""
        key_data = {
            "text": query.text,
            "entity_types": query.entity_types,
            "filters": query.filters,
            "limit": query.limit,
        }
        return str(hash(json.dumps(key_data, sort_keys=True)))

    def _cache_result(self, cache_key: str, result: SearchResult):
        """結果のキャッシュ"""
        if len(self.search_cache) >= self.cache_max_size:
            # 古いキャッシュを削除
            oldest_key = next(iter(self.search_cache))
            del self.search_cache[oldest_key]

        self.search_cache[cache_key] = result

    def _record_search_history(self, query: SearchQuery, result: SearchResult):
        """検索履歴記録"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "query_text": query.text,
            "intent": query.intent,
            "results_count": result.total_found,
            "search_time_ms": result.search_time_ms,
        }

        self.search_history.append(history_entry)

        # 履歴サイズ制限
        if len(self.search_history) > 1000:
            self.search_history = self.search_history[-500:]  # 半分に削減

    # ============================================
    # 高度な検索機能
    # ============================================

    async def search_by_intent(self, query: str, intent: str) -> SearchResult:
        """意図別検索"""
        search_query = SearchQuery(text=query, intent=intent)
        return await self.search(search_query)

    async def search_knowledge(self, query: str, domain: str = None) -> SearchResult:
        """知識特化検索"""
        filters = {}
        if domain:
            filters["domain"] = domain

        search_query = SearchQuery(
            text=query,
            entity_types=["knowledge"],
            filters=filters,
            intent="knowledge_acquisition",
        )
        return await self.search(search_query)

    async def search_incidents(self, query: str, severity: str = None) -> SearchResult:
        """インシデント特化検索"""
        filters = {}
        if severity:
            filters["severity"] = severity

        search_query = SearchQuery(
            text=query,
            entity_types=["incident"],
            filters=filters,
            intent="problem_solving",
        )
        return await self.search(search_query)

    async def search_similar_problems(self, problem_description: str) -> SearchResult:
        """類似問題検索"""
        # インシデントと関連する解決策知識を検索
        search_query = SearchQuery(
            text=problem_description,
            entity_types=["incident", "knowledge"],
            intent="problem_solving",
            include_relationships=True,
            max_relationship_depth=3,
        )
        return await self.search(search_query)

    def get_search_analytics(self) -> Dict[str, Any]:
        """検索分析データ取得"""
        if not self.search_history:
            return {}

        from collections import Counter

        # 意図別統計
        intents = [entry.get("intent", "unknown") for entry in self.search_history]
        intent_stats = Counter(intents)

        # 検索時間統計
        search_times = [entry.get("search_time_ms", 0) for entry in self.search_history]
        avg_search_time = sum(search_times) / len(search_times) if search_times else 0

        # 結果数統計
        result_counts = [entry.get("results_count", 0) for entry in self.search_history]
        avg_results = sum(result_counts) / len(result_counts) if result_counts else 0

        return {
            "total_searches": len(self.search_history),
            "intent_distribution": dict(intent_stats),
            "avg_search_time_ms": avg_search_time,
            "avg_results_count": avg_results,
            "cache_hit_rate": len(self.search_cache) / max(len(self.search_history), 1),
        }


# ============================================
# テスト用サンプル実行
# ============================================


async def main():
    """サンプル実行"""
    rag_manager = UnifiedRAGManager()

    # サンプル検索
    result = await rag_manager.search("APIエラーの解決方法")

    print(f"検索結果: {result.total_found}件")
    print(f"検索時間: {result.search_time_ms:.2f}ms")
    print(f"意図: {result.query.intent}")
    print("\n=== 組み立てられたコンテキスト ===")
    print(result.assembled_context)

    if result.suggestions:
        print("\n=== 検索提案 ===")
        for suggestion in result.suggestions:
            print(f"- {suggestion}")


if __name__ == "__main__":
    asyncio.run(main())
