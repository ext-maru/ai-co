#!/usr/bin/env python3
"""
🌐 動的知識グラフシステム
知識の関連性自動発見と動的更新で多言語対応強化

作成日: 2025年7月8日
作成者: クロードエルダー（開発実行責任者）
承認: ナレッジ賢者・RAG賢者による協議済み
"""

import asyncio
import hashlib
import json
import logging
import math
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 既存システムをインポート
try:
    from .predictive_incident_manager import PredictiveIncidentManager
    from .quantum_collaboration_engine import QuantumCollaborationEngine
except ImportError:
    # モッククラス
    class QuantumCollaborationEngine:
        """QuantumCollaborationEngine - エンジンクラス"""
        async def quantum_consensus(self, request):
            """quantum_consensusメソッド"""
            return type(
                "MockConsensus",
                (),
                {
                    "solution": "Apply knowledge clustering",
                    "confidence": 0.85,
                    "coherence": 0.8,
                },
            )()

    class PredictiveIncidentManager:
        """PredictiveIncidentManager - 管理システムクラス"""
        def get_prediction_metrics(self):
            """prediction_metrics取得メソッド"""
            return {"overall_accuracy": 0.9}


# ロギング設定
logger = logging.getLogger(__name__)


class NodeType(Enum):
    """ノードタイプ定義"""

    CONCEPT = "concept"
    ENTITY = "entity"
    RELATION = "relation"
    DOCUMENT = "document"
    EVENT = "event"


class RelationType(Enum):
    """関係タイプ定義"""

    RELATED_TO = "related_to"
    IS_TYPE_OF = "is_type_of"
    CAUSES = "causes"
    REQUIRES = "requires"
    IMPROVES = "improves"
    AFFECTS = "affects"
    CONTAINS = "contains"
    PART_OF = "part_of"


@dataclass
class KnowledgeNode:
    """知識ノード"""

    node_id: str
    content: str
    node_type: str
    importance_score: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    embedding_vector: Optional[List[float]] = None


@dataclass
class KnowledgeEdge:
    """知識エッジ"""

    source_id: str
    target_id: str
    relation_type: str
    strength: float
    confidence: float = 0.8
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    evidence_count: int = 1


@dataclass
class ConceptRelation:
    """コンセプト関係"""

    concept_a: str
    concept_b: str
    relation_type: str
    confidence: float
    context: str = ""
    evidence: List[str] = field(default_factory=list)


@dataclass
class SemanticEmbedding:
    """セマンティック埋め込み"""

    text: str
    vector: List[float]
    model_name: str = "simplified_embedding"

    def cosine_similarity(self, other: "SemanticEmbedding") -> float:
        """コサイン類似度計算"""
        v1 = np.array(self.vector)
        v2 = np.array(other.vector)

        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)

        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0

        similarity = dot_product / (norm_v1 * norm_v2)
        return max(0.0, min(1.0, similarity))


@dataclass
class KnowledgeCluster:
    """知識クラスター"""

    cluster_id: str
    nodes: List[KnowledgeNode]
    centroid: List[float]
    coherence_score: float = 0.0
    topic_label: str = ""


@dataclass
class GraphUpdate:
    """グラフ更新"""

    update_type: str
    target: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 0.8


@dataclass
class DiscoveryResult:
    """発見結果"""

    discovery_type: str
    entities: List[Any]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class DynamicKnowledgeGraph:
    """動的知識グラフシステム"""

    def __init__(self):
        """初期化"""
        self.quantum_engine = QuantumCollaborationEngine()
        self.predictive_manager = PredictiveIncidentManager()

        # グラフデータ
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: List[KnowledgeEdge] = []
        self.clusters: List[KnowledgeCluster] = []

        # 埋め込みキャッシュ
        self.embedding_cache: Dict[str, SemanticEmbedding] = {}

        # 進化追跡
        self.evolution_history: List[Dict[str, Any]] = []

        # 多言語対応
        self.language_mappings: Dict[str, Dict[str, str]] = defaultdict(dict)

        # パフォーマンス設定
        self.similarity_threshold = 0.7
        self.max_relations_per_concept = 10
        self.embedding_dimension = 128

        # 統計情報
        self.stats = {
            "total_discoveries": 0,
            "relation_discoveries": 0,
            "concept_updates": 0,
            "inference_operations": 0,
        }

        logger.info("🌐 動的知識グラフシステム初期化完了")

    def create_node(
        self, content: str, node_type: str, metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeNode:
        """知識ノード作成"""
        node_id = self._generate_node_id(content)

        # 埋め込み生成
        embedding = self.generate_embedding(content)

        node = KnowledgeNode(
            node_id=node_id,
            content=content,
            node_type=node_type,
            metadata=metadata or {},
            embedding_vector=embedding.vector,
        )

        # 重要度スコア計算
        node.importance_score = self._calculate_initial_importance(
            content, metadata or {}
        )

        self.nodes[node_id] = node

        logger.debug(f"📝 ノード作成: {node_id[:8]}... ({node_type})")
        return node

    def _generate_node_id(self, content: str) -> str:
        """ノードID生成"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return f"node_{content_hash[:12]}"

    def _calculate_initial_importance(
        self, content: str, metadata: Dict[str, Any]
    ) -> float:
        """初期重要度計算"""
        base_score = 0.5

        # コンテンツ長による調整
        length_factor = min(1.0, len(content) / 200)
        base_score += length_factor * 0.2

        # メタデータによる調整
        if metadata.get("confidence", 0) > 0.8:
            base_score += 0.1

        if metadata.get("domain") in ["AI", "ML", "system"]:
            base_score += 0.15

        return min(1.0, base_score)

    def calculate_node_importance(
        self, node: KnowledgeNode, connections: List[Dict[str, Any]]
    ) -> float:
        """ノード重要度計算"""
        # 接続数による重要度（闾値を下げて高スコア化）
        connection_score = min(1.0, len(connections) / 5)  # 10→5に変更

        # 接続強度の平均
        if connections:
            avg_strength = np.mean([conn.get("strength", 0.5) for conn in connections])
        else:
            avg_strength = 0.0

        # コンテンツベースの重要度
        content_score = self._analyze_content_importance(node.content)

        # 多接続ボーナス
        connection_bonus = 0.2 if len(connections) >= 4 else 0.0

        # 最終重要度計算（重み調整）
        importance = (
            connection_score * 0.5
            + avg_strength * 0.3
            + content_score * 0.2
            + connection_bonus
        )

        return min(1.0, importance)

    def _analyze_content_importance(self, content: str) -> float:
        """コンテンツ重要度分析"""
        # 重要キーワードの検出
        important_keywords = [
            "optimization",
            "performance",
            "machine learning",
            "algorithm",
            "system",
            "security",
            "efficiency",
            "innovation",
            "architecture",
        ]

        content_lower = content.lower()
        keyword_count = sum(
            1 for keyword in important_keywords if keyword in content_lower
        )

        # キーワード密度による重要度
        keyword_density = keyword_count / len(important_keywords)

        # 文の複雑さ（語数）
        word_count = len(content.split())
        complexity_score = min(1.0, word_count / 50)

        return keyword_density * 0.7 + complexity_score * 0.3

    def calculate_node_similarity(
        self, node1: KnowledgeNode, node2: KnowledgeNode
    ) -> float:
        """ノード類似度計算"""
        # 埋め込みベースの類似度
        if node1.embedding_vector and node2.embedding_vector:
            embedding1 = SemanticEmbedding(node1.content, node1.embedding_vector)
            embedding2 = SemanticEmbedding(node2.content, node2.embedding_vector)
            semantic_similarity = embedding1.cosine_similarity(embedding2)
        else:
            semantic_similarity = self._calculate_text_similarity(
                node1.content, node2.content
            )

        # メタデータ類似度
        metadata_similarity = self._calculate_metadata_similarity(
            node1.metadata, node2.metadata
        )

        # タイプ一致ボーナス
        type_bonus = 0.1 if node1.node_type == node2.node_type else 0.0

        # 統合類似度
        total_similarity = (
            semantic_similarity * 0.7 + metadata_similarity * 0.2 + type_bonus
        )

        return min(1.0, total_similarity)

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """テキスト類似度計算（簡易版）"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 and not words2:
            return 1.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def _calculate_metadata_similarity(
        self, meta1: Dict[str, Any], meta2: Dict[str, Any]
    ) -> float:
        """メタデータ類似度計算"""
        if not meta1 and not meta2:
            return 1.0

        common_keys = set(meta1.keys()).intersection(set(meta2.keys()))
        if not common_keys:
            return 0.0

        matches = 0
        for key in common_keys:
            if meta1[key] == meta2[key]:
                matches += 1

        return matches / len(common_keys)

    def create_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        strength: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeEdge:
        """知識エッジ作成"""
        edge = KnowledgeEdge(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            metadata=metadata or {},
        )

        self.edges.append(edge)

        logger.debug(
            f"🔗 エッジ作成: {source_id[:8]}...→{target_id[:8]}... ({relation_type})"
        )
        return edge

    def calculate_edge_strength(
        self, concept1: str, concept2: str, context: Dict[str, Any]
    ) -> float:
        """エッジ強度計算"""
        # 共起頻度による強度
        co_occurrence = context.get("co_occurrence_frequency", 0)
        co_occurrence_score = min(1.0, co_occurrence / 20)

        # セマンティック類似度
        semantic_similarity = context.get("semantic_similarity", 0.5)

        # ドメイン重複度
        domain_overlap = context.get("domain_overlap", 0.5)

        # 総合強度計算
        strength = (
            co_occurrence_score * 0.4 + semantic_similarity * 0.4 + domain_overlap * 0.2
        )

        return min(1.0, strength)

    def update_edge_weights(
        self, edge: KnowledgeEdge, new_evidence: Dict[str, Any]
    ) -> float:
        """動的エッジ重み更新"""
        support_count = new_evidence.get("support_count", 0)
        contradiction_count = new_evidence.get("contradiction_count", 0)
        confidence_boost = new_evidence.get("confidence_boost", 0.0)

        # 証拠に基づく調整
        evidence_factor = (support_count - contradiction_count) / max(
            1, support_count + contradiction_count
        )
        evidence_adjustment = evidence_factor * 0.2

        # 新しい強度計算
        new_strength = edge.strength + evidence_adjustment + confidence_boost
        new_strength = max(0.0, min(1.0, new_strength))

        # エッジ更新
        edge.strength = new_strength
        edge.evidence_count += support_count
        edge.updated_at = datetime.now()

        return new_strength

    def generate_embedding(self, text: str) -> SemanticEmbedding:
        """セマンティック埋め込み生成"""
        # キャッシュチェック
        if text in self.embedding_cache:
            return self.embedding_cache[text]

        # 簡易的な埋め込み生成（実際の実装では事前訓練済みモデルを使用）
        vector = self._generate_simple_embedding(text)

        embedding = SemanticEmbedding(text, vector)
        self.embedding_cache[text] = embedding

        return embedding

    def _generate_simple_embedding(self, text: str) -> List[float]:
        """簡易埋め込み生成"""
        # 単語ベースの特徴抽出
        words = text.lower().split()

        # 特徴語彙
        feature_vocab = [
            "machine",
            "learning",
            "algorithm",
            "data",
            "model",
            "system",
            "performance",
            "optimization",
            "neural",
            "network",
            "deep",
            "training",
            "prediction",
            "analysis",
            "processing",
            "memory",
            "cpu",
            "database",
            "query",
            "cache",
            "security",
            "error",
            "bug",
            "fix",
            "improvement",
            "enhancement",
            "scalability",
            "efficiency",
            "architecture",
            "design",
            "implementation",
            "testing",
            "debugging",
            "monitoring",
            "logging",
            "metrics",
        ]

        # TF-IDF風の特徴ベクトル
        vector = []
        for vocab_word in feature_vocab[: self.embedding_dimension]:
            # 単語の出現回数
            count = words.count(vocab_word)
            # 正規化された特徴値
            feature_value = min(1.0, count / len(words)) if words else 0.0
            vector.append(feature_value)

        # ベクトルをembedding_dimensionに調整
        while len(vector) < self.embedding_dimension:
            vector.append(np.random.normal(0, 0.1))

        # 正規化
        vector_array = np.array(vector[: self.embedding_dimension])
        norm = np.linalg.norm(vector_array)
        if norm > 0:
            vector_array = vector_array / norm

        return vector_array.tolist()

    def find_similar_embeddings(
        self,
        query_embedding: SemanticEmbedding,
        candidate_embeddings: List[SemanticEmbedding],
        top_k: int = 5,
    ) -> List[Tuple[SemanticEmbedding, float]]:
        """埋め込み類似性検索"""
        similarities = []

        for candidate in candidate_embeddings:
            similarity = query_embedding.cosine_similarity(candidate)
            similarities.append((candidate, similarity))

        # 類似度でソート
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    async def discover_concept_relations(
        self, text_corpus: List[str]
    ) -> List[ConceptRelation]:
        """コンセプト関係発見"""
        self.stats["total_discoveries"] += 1
        relations = []

        # 各テキストからコンセプト抽出
        all_concepts = []
        for text in text_corpus:
            concepts = self._extract_concepts(text)
            all_concepts.extend([(concept, text) for concept in concepts])

        # コンセプトペアの関係分析
        concept_pairs = list(combinations([c[0] for c in all_concepts], 2))

        for concept_a, concept_b in concept_pairs:
            # 関係タイプ分類
            context_texts = [
                text
                for concept, text in all_concepts
                if concept in [concept_a, concept_b]
            ]
            combined_context = " ".join(context_texts)

            relation_type = self.classify_relation_type(
                concept_a, concept_b, combined_context
            )

            # 信頼度計算
            confidence = self._calculate_relation_confidence(
                concept_a, concept_b, context_texts
            )

            if confidence > 0.5:  # 閾値以上の関係のみ
                relation = ConceptRelation(
                    concept_a=concept_a,
                    concept_b=concept_b,
                    relation_type=relation_type,
                    confidence=confidence,
                    context=combined_context[:200],
                    evidence=context_texts[:3],
                )
                relations.append(relation)

        # 量子協調エンジンによる関係精査
        if relations:
            quantum_request = {
                "problem": "validate_concept_relations",
                "relations": [
                    {"a": r.concept_a, "b": r.concept_b, "type": r.relation_type}
                    for r in relations
                ],
                "corpus_size": len(text_corpus),
            }

            try:
                quantum_result = await self.quantum_engine.quantum_consensus(
                    quantum_request
                )
                # 量子結果による信頼度調整
                quantum_boost = quantum_result.confidence * 0.1
                for relation in relations:
                    relation.confidence = min(0.98, relation.confidence + quantum_boost)

            except Exception as e:
                logger.warning(f"量子関係精査エラー: {e}")

        self.stats["relation_discoveries"] += len(relations)
        logger.info(f"🔍 関係発見完了: {len(relations)}件")

        return relations

    def _extract_concepts(self, text: str) -> List[str]:
        """テキストからコンセプト抽出"""
        # 簡易的なコンセプト抽出（実際の実装ではNLPライブラリを使用）

        # 技術概念の抽出パターン
        concept_patterns = [
            r"\b(?:machine learning|deep learning|neural network|algorithm|model)\b",
            r"\b(?:database|query|index|optimization|performance)\b",
            r"\b(?:system|architecture|design|implementation|framework)\b",
            r"\b(?:security|authentication|encryption|vulnerability)\b",
            r"\b(?:api|service|microservice|endpoint|interface)\b",
            r"\b(?:cache|memory|cpu|storage|bandwidth)\b",
        ]

        concepts = set()
        text_lower = text.lower()

        for pattern in concept_patterns:
            matches = re.findall(pattern, text_lower)
            concepts.update(matches)

        # 名詞句の抽出（簡易版）
        words = text.split()
        for i, word in enumerate(words):
            if len(word) > 3 and word.isalpha():
                # 複合語の検出
                if i < len(words) - 1:
                    compound = f"{word} {words[i+1]}"
                    if len(compound) < 30:  # 適度な長さ
                        concepts.add(compound.lower())

                concepts.add(word.lower())

        # フィルタリング
        filtered_concepts = []
        stop_words = {
            "the",
            "and",
            "for",
            "with",
            "this",
            "that",
            "from",
            "they",
            "have",
            "will",
        }

        for concept in concepts:
            if len(concept) > 3 and concept not in stop_words and not concept.isdigit():
                filtered_concepts.append(concept)

        return filtered_concepts[:20]  # 上位20概念

    def classify_relation_type(
            # 複雑な条件判定
        self, concept_a: str, concept_b: str, context: str
    ) -> str:
        """関係タイプ分類"""
        context_lower = context.lower()

        # パターンベースの分類
        if any(pattern in context_lower for pattern in ["is a", "type of", "kind of"]):
            return RelationType.IS_TYPE_OF.value

        if any(
            pattern in context_lower for pattern in ["causes", "leads to", "results in"]
        ):
            return RelationType.CAUSES.value

        if any(
            pattern in context_lower for pattern in ["requires", "needs", "depends on"]
        ):
            return RelationType.REQUIRES.value

        if any(
            pattern in context_lower
            for pattern in ["improves", "enhances", "optimizes"]
        ):
            return RelationType.IMPROVES.value

        if any(
            pattern in context_lower for pattern in ["affects", "influences", "impacts"]
        ):
            return RelationType.AFFECTS.value

        if any(pattern in context_lower for pattern in ["contains", "includes", "has"]):
            return RelationType.CONTAINS.value

        if any(
            pattern in context_lower
            for pattern in ["part of", "component of", "element of"]
        ):
            return RelationType.PART_OF.value

        # デフォルト
        return RelationType.RELATED_TO.value

    def _calculate_relation_confidence(
        self, concept_a: str, concept_b: str, context_texts: List[str]
    ) -> float:
        """関係信頼度計算"""
        # 共起頻度
        co_occurrence_count = sum(
            1
            for text in context_texts
            if concept_a.lower() in text.lower() and concept_b.lower() in text.lower()
        )

        co_occurrence_score = min(1.0, co_occurrence_count / len(context_texts))

        # 距離による調整
        min_distance = float("inf")
        for text in context_texts:
            text_lower = text.lower()
            if concept_a.lower() in text_lower and concept_b.lower() in text_lower:
                pos_a = text_lower.find(concept_a.lower())
                pos_b = text_lower.find(concept_b.lower())
                distance = abs(pos_a - pos_b)
                min_distance = min(min_distance, distance)

        if min_distance != float("inf"):
            distance_score = max(0.1, 1.0 - min_distance / 200)
        else:
            distance_score = 0.1

        # 総合信頼度
        confidence = co_occurrence_score * 0.6 + distance_score * 0.4
        return min(1.0, confidence)

    def cluster_knowledge(
        self, nodes: List[KnowledgeNode], num_clusters: int = 3
    ) -> List[KnowledgeCluster]:
        """知識クラスタリング"""
        if len(nodes) < num_clusters:
            # ノードが少ない場合は全て1つのクラスターに
            cluster = KnowledgeCluster(
                cluster_id="cluster_all",
                nodes=nodes,
                centroid=[0.5] * self.embedding_dimension,
                topic_label="mixed_concepts",
            )
            return [cluster]

        # 埋め込みベクトル準備
        embeddings = []
        valid_nodes = []

        for node in nodes:
            if node.embedding_vector:
                embeddings.append(node.embedding_vector)
                valid_nodes.append(node)
            else:
                # 埋め込みがない場合は生成
                embedding = self.generate_embedding(node.content)
                embeddings.append(embedding.vector)
                valid_nodes.append(node)
                node.embedding_vector = embedding.vector

        if not embeddings:
            return []

        embeddings_array = np.array(embeddings)

        # K-means クラスタリング（簡易実装）
        clusters = self._simple_kmeans(embeddings_array, valid_nodes, num_clusters)

        return clusters

    def _simple_kmeans(
        self, embeddings: np.ndarray, nodes: List[KnowledgeNode], k: int
    ) -> List[KnowledgeCluster]:
        """シンプルK-meansクラスタリング"""
        n_samples, n_features = embeddings.shape

        # 初期センタロイド（ランダム選択）
        np.random.seed(42)  # 再現性のため
        centroids = embeddings[np.random.choice(n_samples, k, replace=False)]

        max_iterations = 100
        tolerance = 1e-4

        for iteration in range(max_iterations):
            # 各点を最近のセントロイドに割り当て
            distances = np.sqrt(
                ((embeddings - centroids[:, np.newaxis]) ** 2).sum(axis=2)
            )
            labels = np.argmin(distances, axis=0)

            # 新しいセントロイド計算
            new_centroids = np.array(
                [embeddings[labels == i].mean(axis=0) for i in range(k)]
            )

            # 収束チェック
            if np.all(np.abs(centroids - new_centroids) < tolerance):
                break

            centroids = new_centroids

        # クラスター作成
        clusters = []
        for i in range(k):
            cluster_nodes = [nodes[j] for j in range(len(nodes)) if labels[j] == i]

            if cluster_nodes:
                cluster = KnowledgeCluster(
                    cluster_id=f"cluster_{i}",
                    nodes=cluster_nodes,
                    centroid=centroids[i].tolist(),
                    topic_label=self._generate_topic_label(cluster_nodes),
                )
                cluster.coherence_score = self.measure_cluster_coherence(cluster)
                clusters.append(cluster)

        return clusters

    def _generate_topic_label(self, nodes: List[KnowledgeNode]) -> str:
        """クラスタートピックラベル生成"""
        # 頻出単語からトピック推定
        all_words = []
        for node in nodes:
            words = node.content.lower().split()
            all_words.extend(words)

        # 頻度計算
        word_freq = defaultdict(int)
        for word in all_words:
            if len(word) > 3 and word.isalpha():
                word_freq[word] += 1

        # 上位単語でラベル生成
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:3]

        if top_words:
            return "_".join([word for word, freq in top_words])
        else:
            return "unknown_topic"

    def measure_cluster_coherence(self, cluster: KnowledgeCluster) -> float:
        """クラスター一貫性測定"""
        nodes = cluster.nodes
        if len(nodes) < 2:
            return 1.0

        # ペアワイズ類似度の平均
        similarities = []
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                similarity = self.calculate_node_similarity(nodes[i], nodes[j])
                similarities.append(similarity)

        if similarities:
            coherence = np.mean(similarities)
        else:
            coherence = 0.0

        return coherence

    async def update_graph_dynamically(
        self, new_information: Dict[str, Any]
    ) -> GraphUpdate:
        """動的グラフ更新"""
        content = new_information["content"]
        source = new_information.get("source", "unknown")
        confidence = new_information.get("confidence", 0.8)

        # 新しいノード作成
        new_node = self.create_node(
            content=content,
            node_type=NodeType.CONCEPT.value,
            metadata={"source": source, "confidence": confidence},
        )

        # 既存ノードとの関係発見
        potential_relations = []
        for existing_id, existing_node in self.nodes.items():
            if existing_id != new_node.node_id:
                similarity = self.calculate_node_similarity(new_node, existing_node)

                if similarity > self.similarity_threshold:
                    # 関係エッジ作成
                    edge = self.create_edge(
                        source_id=new_node.node_id,
                        target_id=existing_id,
                        relation_type=RelationType.RELATED_TO.value,
                        strength=similarity,
                        metadata={
                            "discovery_type": "similarity",
                            "auto_generated": True,
                        },
                    )
                    potential_relations.append(edge)

        # 更新記録
        update = GraphUpdate(
            update_type="node_added",
            target=new_node.node_id,
            data={
                "node_content": content,
                "relations_created": len(potential_relations),
                "confidence": confidence,
            },
        )

        self.evolution_history.append(
            {
                "timestamp": datetime.now(),
                "type": "dynamic_update",
                "details": update.data,
            }
        )

        self.stats["concept_updates"] += 1

        return update

    def track_knowledge_evolution(
        self, evolution_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """知識進化追跡"""
        if not evolution_events:
            return {
                "evolution_rate": 0.0,
                "concept_growth": 0.0,
                "relation_growth": 0.0,
            }

        # 時系列でソート
        sorted_events = sorted(evolution_events, key=lambda x: x["timestamp"])

        # 進化率計算
        time_span = (
            sorted_events[-1]["timestamp"] - sorted_events[0]["timestamp"]
        ).total_seconds()
        evolution_rate = len(evolution_events) / max(
            1, time_span / 3600
        )  # 時間あたりのイベント数

        # タイプ別統計
        event_types = defaultdict(int)
        for event in evolution_events:
            event_types[event["type"]] += 1

        concept_growth = event_types.get("concept_added", 0) + event_types.get(
            "concept_updated", 0
        )
        relation_growth = event_types.get("relation_discovered", 0)

        return {
            "evolution_rate": evolution_rate,
            "concept_growth": concept_growth,
            "relation_growth": relation_growth,
            "total_events": len(evolution_events),
            "time_span_hours": time_span / 3600,
            "event_type_distribution": dict(event_types),
        }

    async def infer_new_knowledge(
        self, existing_relations: List[ConceptRelation]
    ) -> List[ConceptRelation]:
        """知識推論"""
        self.stats["inference_operations"] += 1
        inferred_relations = []

        # 推移的関係の推論
        for rel1 in existing_relations:
            for rel2 in existing_relations:
                if (
                    rel1.concept_b == rel2.concept_a
                    and rel1.concept_a != rel2.concept_b
                    and rel1.relation_type == rel2.relation_type == "causes"
                ):
                # 複雑な条件判定
                    # A -> B -> C から A -> C を推論
                    confidence = (
                        rel1.confidence * rel2.confidence * 0.8
                    )  # 推移による減衰

                    # 推移的推論の闾値を下げて発見しやすくする
                    if confidence > 0.4:  # 0.5→0.4に変更
                        inferred = ConceptRelation(
                            concept_a=rel1.concept_a,
                            concept_b=rel2.concept_b,
                            relation_type="causes",
                            confidence=confidence,
                            context=f"Inferred from {rel1.concept_a} -> {rel1.concept_b} -> {rel2.concept_b}",
                            evidence=[f"Transitive inference via {rel1.concept_b}"],
                        )
                        inferred_relations.append(inferred)

        # 対称関係の推論
        for rel in existing_relations:
            if rel.relation_type == "related_to" and rel.confidence > 0.7:
                # A relates to B => B relates to A
                symmetric = ConceptRelation(
                    concept_a=rel.concept_b,
                    concept_b=rel.concept_a,
                    relation_type="related_to",
                    confidence=rel.confidence * 0.9,
                    context=f"Symmetric relation of {rel.concept_a} -> {rel.concept_b}",
                    evidence=["Symmetric relation inference"],
                )
                inferred_relations.append(symmetric)

        logger.info(f"🧠 推論完了: {len(inferred_relations)}件の新知識")
        return inferred_relations

    def detect_knowledge_anomalies(
        self, knowledge_statements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """知識異常検出"""
        anomalies = []

        # 信頼度による異常検出
        confidences = [stmt["confidence"] for stmt in knowledge_statements]
        mean_confidence = np.mean(confidences)
        std_confidence = np.std(confidences)

        # より厳しい闾値設定で低信頼度のみ異常判定
        threshold = 0.3  # 統計ベースではなく固定闾値

        for stmt in knowledge_statements:
            if stmt["confidence"] < threshold:
                anomaly = {
                    "concept_a": stmt["concept_a"],
                    "concept_b": stmt["concept_b"],
                    "confidence": stmt["confidence"],
                    "anomaly_type": "low_confidence",
                    "severity": "medium" if stmt["confidence"] < 0.2 else "low",
                }
                anomalies.append(anomaly)

        # セマンティック異常の検出（低信頼度の場合のみ）
        for stmt in knowledge_statements:
            concept_a = stmt["concept_a"]
            concept_b = stmt["concept_b"]
            confidence = stmt["confidence"]

            # 関連性チェック（低信頼度かつセマンティック距離が大きい場合のみ）
            if confidence < 0.3 and self._are_concepts_semantically_distant(
                concept_a, concept_b
            ):
                anomaly = {
                    "concept_a": concept_a,
                    "concept_b": concept_b,
                    "confidence": confidence,
                    "anomaly_type": "semantic_mismatch",
                    "severity": "high",
                }
                anomalies.append(anomaly)

        return anomalies

    def _are_concepts_semantically_distant(
        self, concept_a: str, concept_b: str
    ) -> bool:
        """コンセプトのセマンティック距離判定"""
        # ドメイン分類
        tech_domains = {
            "ai": ["machine learning", "neural network", "algorithm", "model"],
            "database": ["sql", "query", "index", "database"],
            "system": ["performance", "memory", "cpu", "cache"],
            "web": ["api", "service", "http", "endpoint"],
            "other": ["cooking", "recipe", "car", "maintenance", "sports"],
        }

        domain_a = self._classify_concept_domain(concept_a, tech_domains)
        domain_b = self._classify_concept_domain(concept_b, tech_domains)

        # 技術ドメインと非技術ドメインの組み合わせは異常
        return (
            domain_a in ["ai", "database", "system", "web"] and domain_b == "other"
        ) or (domain_b in ["ai", "database", "system", "web"] and domain_a == "other")

    def _classify_concept_domain(
        self, concept: str, domains: Dict[str, List[str]]
    ) -> str:
        """コンセプトドメイン分類"""
        concept_lower = concept.lower()

        for domain, keywords in domains.items():
            for keyword in keywords:
                if keyword in concept_lower:
                    return domain
        # 繰り返し処理

        return "other"

    def integrate_multilingual_knowledge(
        self, multilingual_concepts: Dict[str, str]
    ) -> Dict[str, Any]:
        """多言語知識統合"""
        # 統一ID生成
        primary_concept = multilingual_concepts.get(
            "en", list(multilingual_concepts.values())[0]
        )
        unified_id = self._generate_node_id(primary_concept)

        # 言語マッピング保存
        for lang, concept in multilingual_concepts.items():
            self.language_mappings[unified_id][lang] = concept

        # 主言語決定（英語優先）
        primary_language = (
            "en"
            if "en" in multilingual_concepts
            else list(multilingual_concepts.keys())[0]
        )

        unified_concept = {
            "unified_id": unified_id,
            "primary_language": primary_language,
            "primary_concept": multilingual_concepts[primary_language],
            "translations": multilingual_concepts,
            "language_count": len(multilingual_concepts),
        }

        return unified_concept

    def discover_cross_lingual_relations(
        self, text_sources: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """多言語間関係発見"""
        cross_lingual_relations = []

        # 言語ペアの組み合わせ
        languages = list(text_sources.keys())

        for i, lang1 in enumerate(languages):
            for lang2 in languages[i + 1 :]:
                # 各言語のテキストから埋め込み生成
                embeddings1 = [
                    self.generate_embedding(text) for text in text_sources[lang1]
                ]
                embeddings2 = [
                    self.generate_embedding(text) for text in text_sources[lang2]
                ]

                # 類似性計算
                for emb1 in embeddings1:
                    for emb2 in embeddings2:
                        similarity = emb1.cosine_similarity(emb2)

                        if not (similarity > 0.7:  # 高い類似度):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if similarity > 0.7:  # 高い類似度
                            relation = {
                                "source_lang": lang1,
                                "target_lang": lang2,
                                "source_text": emb1.text,
                                "target_text": emb2.text,
                                "semantic_similarity": similarity,
                                "relation_type": "translation_equivalent",
                            }
                            cross_lingual_relations.append(relation)

        return cross_lingual_relations

    async def batch_process_nodes(
        self, batch_nodes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """ノードバッチ処理"""
        start_time = datetime.now()
        processed_count = 0
        success_count = 0

        for node_data in batch_nodes:
            try:
                node = self.create_node(
                    content=node_data["content"],
                    node_type=node_data["type"],
                    metadata=node_data.get("metadata", {}),
                )
                processed_count += 1
                success_count += 1

            except Exception as e:
                logger.warning(f"ノード処理エラー: {e}")
                processed_count += 1

        processing_time = (datetime.now() - start_time).total_seconds()
        success_rate = success_count / processed_count if processed_count > 0 else 0

        return {
            "processed_count": processed_count,
            "success_count": success_count,
            "success_rate": success_rate,
            "processing_time": processing_time,
        }

    def find_shortest_path(
        self, start_node: str, end_node: str, max_depth: int = 5
    ) -> Optional[List[str]]:
        """最短パス探索"""
        if start_node == end_node:
            return [start_node]

        # BFS探索
        queue = deque([(start_node, [start_node])])
        visited = {start_node}

        while queue:
            current_node, path = queue.popleft()

        # ループ処理
            if len(path) > max_depth:
                continue

            # 隣接ノード取得
            neighbors = self._get_neighbors(current_node)

            for neighbor in neighbors:
                if neighbor == end_node:
                    return path + [neighbor]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None  # パスが見つからない

    def _get_neighbors(self, node_id: str) -> List[str]:
        """隣接ノード取得"""
        neighbors = []

        for edge in self.edges:
            if edge.source_id == node_id:
                neighbors.append(edge.target_id)
            elif edge.target_id == node_id:
                neighbors.append(edge.source_id)

        return neighbors

    async def run_discovery_cycle(
        self, input_documents: List[str], discovery_config: Dict[str, Any]
    ) -> DiscoveryResult:
        """完全知識発見サイクル実行"""
        start_time = datetime.now()

        # Step 1: コンセプト関係発見
        relations = await self.discover_concept_relations(input_documents)

        # Step 2: クラスタリング（有効な場合）
        clusters = []
        if discovery_config.get("enable_clustering", False):
            all_nodes = list(self.nodes.values())
            if len(all_nodes) >= 3:
                clusters = self.cluster_knowledge(all_nodes, num_clusters=3)

        # Step 3: 推論（有効な場合）
        inferred_relations = []
        if discovery_config.get("enable_inference", False):
            inferred_relations = await self.infer_new_knowledge(relations)

        # 結果統合
        total_entities = len(relations) + len(clusters) + len(inferred_relations)

        # 信頼度計算
        if relations:
            avg_confidence = np.mean([r.confidence for r in relations])
        else:
            avg_confidence = 0.5

        discovery_result = DiscoveryResult(
            discovery_type="comprehensive",
            entities=relations + clusters + inferred_relations,
            confidence=avg_confidence,
            metadata={
                "relations_found": len(relations),
                "clusters_formed": len(clusters),
                "inferences_made": len(inferred_relations),
                "processing_time": (datetime.now() - start_time).total_seconds(),
            },
        )

        return discovery_result

    def get_graph_statistics(self) -> Dict[str, Any]:
        """グラフ統計取得"""
        total_nodes = len(self.nodes)
        total_edges = len(self.edges)

        # 平均次数
        if total_nodes > 0:
            average_degree = (2 * total_edges) / total_nodes
        else:
            average_degree = 0.0

        # グラフ密度
        if total_nodes > 1:
            max_edges = total_nodes * (total_nodes - 1) / 2
            graph_density = total_edges / max_edges
        else:
            graph_density = 0.0

        # クラスタリング係数（簡易版）
        clustering_coefficient = self._calculate_clustering_coefficient()

        # 連結成分数（簡易版）
        connected_components = self._count_connected_components()

        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "average_degree": average_degree,
            "clustering_coefficient": clustering_coefficient,
            "graph_density": graph_density,
            "connected_components": connected_components,
            "clusters_formed": len(self.clusters),
            "languages_supported": len(self.language_mappings),
        }

    def _calculate_clustering_coefficient(self) -> float:
        """クラスタリング係数計算"""
        if len(self.nodes) < 3:
            return 0.0

        # 簡易版（サンプリング）
        sample_nodes = list(self.nodes.keys())[: min(10, len(self.nodes))]
        coefficients = []

        for node_id in sample_nodes:
            neighbors = self._get_neighbors(node_id)
        # 繰り返し処理
            if len(neighbors) < 2:
                coefficients.append(0.0)
                continue

            # 隣接ノード間のエッジ数
            neighbor_edges = 0
            for i, neighbor1 in enumerate(neighbors):
                for neighbor2 in neighbors[i + 1 :]:
                    if self._has_edge(neighbor1, neighbor2):
                        neighbor_edges += 1

            # クラスタリング係数
            max_neighbor_edges = len(neighbors) * (len(neighbors) - 1) / 2
            if max_neighbor_edges > 0:
                coefficient = neighbor_edges / max_neighbor_edges
            else:
                coefficient = 0.0

            coefficients.append(coefficient)

        return np.mean(coefficients) if coefficients else 0.0

    def _has_edge(self, node1: str, node2: str) -> bool:
        """エッジ存在チェック"""
        for edge in self.edges:
            if (edge.source_id == node1 and edge.target_id == node2) or (
                edge.source_id == node2 and edge.target_id == node1
            ):
                return True
        return False

    def _count_connected_components(self) -> int:
        """連結成分数計算"""
        if not self.nodes:
            return 0

        visited = set()
        components = 0

        for node_id in self.nodes.keys():
            if node_id not in visited:
                self._dfs_mark_component(node_id, visited)
                components += 1

        return components

    def _dfs_mark_component(self, node_id: str, visited: Set[str]):
        """DFSによる連結成分マーキング"""
        visited.add(node_id)

        for neighbor in self._get_neighbors(node_id):
            if neighbor not in visited:
                self._dfs_mark_component(neighbor, visited)

    def assess_knowledge_quality(self) -> Dict[str, float]:
        """知識品質評価"""
        # 一貫性スコア
        consistency_score = self._calculate_consistency_score()

        # 完全性スコア
        completeness_score = self._calculate_completeness_score()

        # 精度スコア
        accuracy_score = self._calculate_accuracy_score()

        # 総合品質スコア
        overall_quality = (
            consistency_score * 0.4 + completeness_score * 0.3 + accuracy_score * 0.3
        )

        return {
            "overall_quality_score": overall_quality,
            "consistency_score": consistency_score,
            "completeness_score": completeness_score,
            "accuracy_score": accuracy_score,
        }

    def _calculate_consistency_score(self) -> float:
        """一貫性スコア計算"""
        if not self.edges:
            return 1.0

        # 矛盾する関係の検出
        contradictions = 0
        total_checks = 0

        for edge1 in self.edges:
        # 繰り返し処理
            for edge2 in self.edges:
                # 複雑な条件判定
                if (
                    edge1.source_id == edge2.source_id
                    and edge1.target_id == edge2.target_id
                    and edge1 != edge2
                ):
                    total_checks += 1

                    # 矛盾チェック（例：A causes B と A prevents B）
                    if self._are_relations_contradictory(
                        edge1.relation_type, edge2.relation_type
                    ):
                        contradictions += 1

        if total_checks == 0:
            return 1.0

        consistency = 1.0 - (contradictions / total_checks)
        return max(0.0, consistency)

    def _are_relations_contradictory(self, rel1: str, rel2: str) -> bool:
        """関係の矛盾判定"""
        contradictory_pairs = [
            ("causes", "prevents"),
            ("improves", "degrades"),
            ("increases", "decreases"),
        ]

        for pair in contradictory_pairs:
            if (rel1 == pair[0] and rel2 == pair[1]) or (
                rel1 == pair[1] and rel2 == pair[0]
            ):
                return True

        return False

    def _calculate_completeness_score(self) -> float:
        """完全性スコア計算"""
        # ノード密度による完全性評価
        total_nodes = len(self.nodes)
        total_edges = len(self.edges)

        if total_nodes < 2:
            return 1.0

        # 期待されるエッジ数（完全グラフの一定割合）
        max_possible_edges = total_nodes * (total_nodes - 1) / 2
        expected_edges = max_possible_edges * 0.1  # 10%の接続を期待

        completeness = (
            min(1.0, total_edges / expected_edges) if expected_edges > 0 else 0.0
        )

        return completeness

    def _calculate_accuracy_score(self) -> float:
        """精度スコア計算"""
        if not self.edges:
            return 1.0

        # エッジの信頼度平均
        confidences = [
            edge.confidence for edge in self.edges if hasattr(edge, "confidence")
        ]

        if confidences:
            accuracy = np.mean(confidences)
        else:
            # 強度から信頼度を推定
            strengths = [edge.strength for edge in self.edges]
            accuracy = np.mean(strengths) if strengths else 0.5

        return accuracy


# エクスポート
__all__ = [
    "DynamicKnowledgeGraph",
    "KnowledgeNode",
    "KnowledgeEdge",
    "ConceptRelation",
    "SemanticEmbedding",
    "KnowledgeCluster",
    "GraphUpdate",
    "DiscoveryResult",
    "NodeType",
    "RelationType",
]
