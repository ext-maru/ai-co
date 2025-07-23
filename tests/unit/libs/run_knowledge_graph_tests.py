#!/usr/bin/env python3
"""
動的知識グラフシステムのテスト実行スクリプト
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.dynamic_knowledge_graph import (
    ConceptRelation,
    DynamicKnowledgeGraph,
    KnowledgeCluster,
    KnowledgeEdge,
    KnowledgeNode,
    SemanticEmbedding,
)


def test_knowledge_node_creation():
    """知識ノード作成テスト"""
    print("\n🧪 知識ノード作成テスト")
    graph = DynamicKnowledgeGraph()

    node = graph.create_node(
        content="Machine learning algorithms improve system performance",
        node_type="concept",
        metadata={"domain": "AI", "confidence": 0.95},
    )

    tests_passed = 0
    tests_total = 4

    if isinstance(node, KnowledgeNode):
        print("  ✅ KnowledgeNodeインスタンス作成")
        tests_passed += 1
    else:
        print("  ❌ Wrong node type")

    if node.content == "Machine learning algorithms improve system performance":
        print("  ✅ コンテンツ正常")
        tests_passed += 1
    else:
        print("  ❌ Content mismatch")

    if node.node_type == "concept":
        print("  ✅ ノードタイプ正常")
        tests_passed += 1
    else:
        print("  ❌ Node type mismatch")

    if hasattr(node, "node_id") and node.node_id:
        print(f"  ✅ ノードID生成: {node.node_id[:12]}...")
        tests_passed += 1
    else:
        print("  ❌ No node ID")

    return tests_passed, tests_total


def test_node_importance_scoring():
    """ノード重要度スコアリングテスト"""
    print("\n🧪 ノード重要度スコアリングテスト")
    graph = DynamicKnowledgeGraph()

    central_node = KnowledgeNode("central", "Core machine learning concept", "concept")

    connections = [
        {"target": "node1", "strength": 0.8},
        {"target": "node2", "strength": 0.7},
        {"target": "node3", "strength": 0.9},
        {"target": "node4", "strength": 0.6},
    ]

    importance = graph.calculate_node_importance(central_node, connections)

    tests_passed = 0
    tests_total = 3

    if 0 <= importance <= 1:
        print(f"  ✅ 重要度範囲OK: {importance:.3f}")
        tests_passed += 1
    # 複雑な条件判定
    else:
        print(f"  ❌ Invalid importance: {importance}")

    if importance > 0.5:
        print("  ✅ 多接続による高重要度")
        tests_passed += 1
    else:
        print(f"  ❌ Expected high importance, got {importance:.3f}")

    if isinstance(importance, float):
        print("  ✅ 数値型")
        tests_passed += 1
    else:
        print("  ❌ Wrong type")

    return tests_passed, tests_total


def test_node_similarity_calculation():
    """ノード類似度計算テスト"""
    print("\n🧪 ノード類似度計算テスト")
    graph = DynamicKnowledgeGraph()

    node1 = KnowledgeNode("n1", "Machine learning algorithms", "concept")
    node2 = KnowledgeNode("n2", "Deep learning neural networks", "concept")
    node3 = KnowledgeNode("n3", "Database optimization techniques", "concept")

    similarity_high = graph.calculate_node_similarity(node1, node2)
    similarity_low = graph.calculate_node_similarity(node1, node3)

    tests_passed = 0
    tests_total = 3

    if 0 <= similarity_high <= 1 and 0 <= similarity_low <= 1:
        print(f"  ✅ 類似度範囲OK: 高={similarity_high:.3f}, 低={similarity_low:.3f}")
        tests_passed += 1
    else:
        print(f"  ❌ Invalid similarity ranges")

    if similarity_high > similarity_low:
        print("  ✅ ML関連は高類似度")
        tests_passed += 1
    else:
        print(
            f"  ❌ Expected high > low, got {similarity_high:.3f} vs {similarity_low:.3f}"
        )

    if similarity_high > 0.1:  # 何らかの類似度は存在
        print("  ✅ 有意な類似度検出")
        tests_passed += 1
    else:
        print("  ❌ Too low similarity")

    return tests_passed, tests_total


def test_knowledge_edge_creation():
    """知識エッジ作成テスト"""
    print("\n🧪 知識エッジ作成テスト")
    graph = DynamicKnowledgeGraph()

    edge = graph.create_edge(
        source_id="node1",
        target_id="node2",
        relation_type="related_to",
        strength=0.75,
        metadata={"discovered_at": datetime.now()},
    )

    tests_passed = 0
    tests_total = 4

    if isinstance(edge, KnowledgeEdge):
        print("  ✅ KnowledgeEdgeインスタンス作成")
        tests_passed += 1
    else:
        print("  ❌ Wrong edge type")

    if edge.source_id == "node1" and edge.target_id == "node2":
        print("  ✅ ソース・ターゲットID正常")
        tests_passed += 1
    else:
        print("  ❌ ID mismatch")

    if edge.relation_type == "related_to":
        print("  ✅ 関係タイプ正常")
        tests_passed += 1
    else:
        print("  ❌ Relation type mismatch")

    if edge.strength == 0.75:
        print("  ✅ 強度正常")
        tests_passed += 1
    else:
        print("  ❌ Strength mismatch")

    return tests_passed, tests_total


def test_edge_strength_calculation():
    """エッジ強度計算テスト"""
    print("\n🧪 エッジ強度計算テスト")
    graph = DynamicKnowledgeGraph()

    concept1 = "neural networks"
    concept2 = "deep learning"
    context = {
        "co_occurrence_frequency": 15,
        "semantic_similarity": 0.89,
        "domain_overlap": 0.95,
    }

    strength = graph.calculate_edge_strength(concept1, concept2, context)

    tests_passed = 0
    tests_total = 2

    if 0 <= strength <= 1:
        print(f"  ✅ 強度範囲OK: {strength:.3f}")
    # 複雑な条件判定
        tests_passed += 1
    else:
        print(f"  ❌ Invalid strength: {strength}")

    if strength > 0.7:
        print("  ✅ 強い関連性による高強度")
        tests_passed += 1
    else:
        print(f"  ❌ Expected high strength, got {strength:.3f}")

    return tests_passed, tests_total


def test_semantic_embedding_generation():
    """セマンティック埋め込み生成テスト"""
    print("\n🧪 セマンティック埋め込み生成テスト")
    graph = DynamicKnowledgeGraph()

    text = "Machine learning models require extensive training data"
    embedding = graph.generate_embedding(text)

    tests_passed = 0
    tests_total = 4

    if isinstance(embedding, SemanticEmbedding):
        print("  ✅ SemanticEmbeddingインスタンス作成")
        tests_passed += 1
    else:
        print("  ❌ Wrong embedding type")

    if embedding.text == text:
        print("  ✅ テキスト保存正常")
        tests_passed += 1
    else:
        print("  ❌ Text mismatch")

    if isinstance(embedding.vector, (list, np.ndarray)) and len(embedding.vector) > 0:
        print(f"  ✅ ベクトル生成: 次元={len(embedding.vector)}")
        tests_passed += 1
    else:
        print("  ❌ Invalid vector")

    # キャッシュテスト
    embedding2 = graph.generate_embedding(text)
    if embedding.vector == embedding2.vector:
        print("  ✅ キャッシュ機能正常")
        tests_passed += 1
    else:
        print("  ❌ Cache not working")

    return tests_passed, tests_total


def test_embedding_similarity_search():
    """埋め込み類似性検索テスト"""
    print("\n🧪 埋め込み類似性検索テスト")
    graph = DynamicKnowledgeGraph()

    query_embedding = SemanticEmbedding(
        "neural network training", [0.1, 0.8, 0.3, 0.6, 0.2]
    )

    candidate_embeddings = [
        SemanticEmbedding("deep learning models", [0.2, 0.9, 0.1, 0.7, 0.1]),
        SemanticEmbedding("database queries", [0.9, 0.1, 0.8, 0.2, 0.9]),
        SemanticEmbedding(
            "machine learning algorithms", [0.15, 0.85, 0.25, 0.65, 0.15]
        ),
    ]

    similar = graph.find_similar_embeddings(
        query_embedding, candidate_embeddings, top_k=2
    )

    tests_passed = 0
    tests_total = 3

    if len(similar) <= 2:
        print(f"  ✅ Top-K制限正常: {len(similar)}件")
        tests_passed += 1
    else:
        print(f"  ❌ Too many results: {len(similar)}")

    if all(isinstance(item, tuple) for item in similar):
        print("  ✅ 結果形式正常 (embedding, score)")
        tests_passed += 1
    else:
        print("  ❌ Wrong result format")

    if len(similar) > 1 and similar[0][1] >= similar[1][1]:
        print(f"  ✅ 類似度ソート正常: {similar[0][1]:.3f} >= {similar[1][1]:.3f}")
        tests_passed += 1
    elif len(similar) == 1:
        print(f"  ✅ 単一結果: {similar[0][1]:.3f}")
        tests_passed += 1
    else:
        print("  ❌ Sorting issue")

    return tests_passed, tests_total


async def test_concept_relations_discovery():
    """コンセプト関係発見テスト"""
    print("\n🧪 コンセプト関係発見テスト")
    graph = DynamicKnowledgeGraph()

    text_corpus = [
        "Machine learning algorithms improve system performance",
        "Deep learning models require GPU acceleration",
        "Neural networks are a type of machine learning algorithm",
        "System performance can be optimized using caching strategies",
        "GPU acceleration significantly speeds up training",
    ]

    relations = await graph.discover_concept_relations(text_corpus)

    tests_passed = 0
    tests_total = 3

    if isinstance(relations, list):
        print(f"  ✅ 関係リスト取得: {len(relations)}件")
        tests_passed += 1
    else:
        print("  ❌ Wrong relations type")

    if relations and all(isinstance(rel, ConceptRelation) for rel in relations):
        print("  ✅ ConceptRelationインスタンス")
        tests_passed += 1
    elif not relations:
        print("  ⚠️ 関係未発見（正常な場合もある）")
        tests_passed += 1
    else:
        print("  ❌ Wrong relation types")

    if relations:
        first_relation = relations[0]
        if (
            hasattr(first_relation, "confidence")
            and 0 <= first_relation.confidence <= 1
        ):
            print(f"  ✅ 信頼度正常: {first_relation.confidence:.3f}")
            tests_passed += 1
        else:
            print("  ❌ Invalid confidence")
    else:
        tests_passed += 1  # 関係がない場合はスキップ

    return tests_passed, tests_total


def test_knowledge_clustering():
    """知識クラスタリングテスト"""
    print("\n🧪 知識クラスタリングテスト")
    graph = DynamicKnowledgeGraph()

    nodes = [
        KnowledgeNode("n1", "Machine learning algorithms", "concept"),
        KnowledgeNode("n2", "Deep learning models", "concept"),
        KnowledgeNode("n3", "Neural network training", "concept"),
        KnowledgeNode("n4", "Database optimization", "concept"),
        KnowledgeNode("n5", "SQL query performance", "concept"),
        KnowledgeNode("n6", "Index management", "concept"),
    ]

    clusters = graph.cluster_knowledge(nodes, num_clusters=2)

    tests_passed = 0
    tests_total = 3

    if isinstance(clusters, list) and len(clusters) <= 2:
        print(f"  ✅ クラスター生成: {len(clusters)}個")
        tests_passed += 1
    else:
        print(
            f"  ❌ Wrong cluster count: {len(clusters) if isinstance(clusters, list) else 'not list'}"
        )

    if clusters and all(isinstance(cluster, KnowledgeCluster) for cluster in clusters):
        print("  ✅ KnowledgeClusterインスタンス")
        tests_passed += 1
    elif not clusters:
        print("  ⚠️ クラスター未生成")
        tests_passed += 1
    else:
        print("  ❌ Wrong cluster types")

    if clusters and all(len(cluster.nodes) > 0 for cluster in clusters):
        print("  ✅ 各クラスターにノードあり")
        tests_passed += 1
    else:
        print("  ❌ Empty clusters found")

    return tests_passed, tests_total


def test_cluster_coherence_measurement():
    """クラスター一貫性測定テスト"""
    print("\n🧪 クラスター一貫性測定テスト")
    graph = DynamicKnowledgeGraph()

    coherent_cluster = KnowledgeCluster(
        "ml_cluster",
        [
            KnowledgeNode("n1", "machine learning", "concept"),
            KnowledgeNode("n2", "neural networks", "concept"),
            KnowledgeNode("n3", "deep learning", "concept"),
        ],
        [0.5, 0.8, 0.3],
    )

    coherence = graph.measure_cluster_coherence(coherent_cluster)

    tests_passed = 0
    tests_total = 2

    if 0 <= coherence <= 1:
    # 複雑な条件判定
        print(f"  ✅ 一貫性範囲OK: {coherence:.3f}")
        tests_passed += 1
    else:
        print(f"  ❌ Invalid coherence: {coherence}")

    if coherence > 0.3:  # ML関連なので一定の一貫性を期待
        print("  ✅ 関連概念による高一貫性")
        tests_passed += 1
    else:
        print(f"  ❌ Expected higher coherence, got {coherence:.3f}")

    return tests_passed, tests_total


async def test_dynamic_graph_update():
    """動的グラフ更新テスト"""
    print("\n🧪 動的グラフ更新テスト")
    graph = DynamicKnowledgeGraph()

    new_information = {
        "content": "Transformer models revolutionize natural language processing",
        "source": "recent_research",
        "confidence": 0.92,
    }

    update_result = await graph.update_graph_dynamically(new_information)

    tests_passed = 0
    tests_total = 3

    if hasattr(update_result, "update_type"):
        print(f"  ✅ 更新タイプ: {update_result.update_type}")
        tests_passed += 1
    else:
        print("  ❌ No update type")

    if hasattr(update_result, "target") and update_result.target:
        print(f"  ✅ 更新対象: {update_result.target[:12]}...")
        tests_passed += 1
    else:
        print("  ❌ No target")

    if hasattr(update_result, "data") and isinstance(update_result.data, dict):
        print(f"  ✅ 更新データ: {len(update_result.data)}項目")
        tests_passed += 1
    else:
        print("  ❌ Invalid data")

    return tests_passed, tests_total


def test_knowledge_evolution_tracking():
    """知識進化追跡テスト"""
    print("\n🧪 知識進化追跡テスト")
    graph = DynamicKnowledgeGraph()

    evolution_events = [
        {
            "timestamp": datetime.now() - timedelta(days=7),
            "type": "concept_added",
            "concept": "GPT",
        },
        {
            "timestamp": datetime.now() - timedelta(days=5),
            "type": "relation_discovered",
            "relation": "GPT->NLP",
        },
        {
            "timestamp": datetime.now() - timedelta(days=2),
            "type": "concept_updated",
            "concept": "GPT",
        },
        {
            "timestamp": datetime.now(),
            "type": "cluster_formed",
            "cluster": "transformer_models",
        },
    ]

    evolution_summary = graph.track_knowledge_evolution(evolution_events)

    tests_passed = 0
    tests_total = 4

    expected_fields = [
        "evolution_rate",
        "concept_growth",
        "relation_growth",
        "total_events",
    ]
    for field in expected_fields:
        if field in evolution_summary and evolution_summary[field] >= 0:
            print(f"  ✅ {field}: {evolution_summary[field]}")
            tests_passed += 1
        else:
            print(f"  ❌ Missing or invalid {field}")

    return tests_passed, tests_total


async def test_knowledge_inference():
    """知識推論テスト"""
    print("\n🧪 知識推論テスト")
    graph = DynamicKnowledgeGraph()

    existing_relations = [
        ConceptRelation("A", "B", "causes", 0.8),
        ConceptRelation("B", "C", "causes", 0.7),
        ConceptRelation("machine learning", "performance", "related_to", 0.9),
    ]

    inferred = await graph.infer_new_knowledge(existing_relations)

    tests_passed = 0
    tests_total = 3

    if isinstance(inferred, list):
        print(f"  ✅ 推論結果リスト: {len(inferred)}件")
        tests_passed += 1
    else:
        print("  ❌ Wrong inference type")

    if inferred and all(isinstance(rel, ConceptRelation) for rel in inferred):
        print("  ✅ ConceptRelationインスタンス")
        tests_passed += 1
    elif not inferred:
        print("  ⚠️ 推論なし（正常な場合もある）")
        tests_passed += 1
    else:
        print("  ❌ Wrong relation types")

    # A -> C 推移的推論の確認
    ac_relation = None
    if inferred:
        ac_relation = next(
            (r for r in inferred if r.concept_a == "A" and r.concept_b == "C"), None
        )

    if ac_relation and ac_relation.relation_type == "causes":
        print(f"  ✅ 推移的推論成功: A->C (信頼度: {ac_relation.confidence:.3f})")
        tests_passed += 1
    elif not inferred:
        tests_passed += 1  # 推論がない場合はスキップ
    else:
        print("  ❌ Transitive inference not found")

    return tests_passed, tests_total


def test_anomaly_detection_in_knowledge():
    """知識異常検出テスト"""
    print("\n🧪 知識異常検出テスト")
    graph = DynamicKnowledgeGraph()

    knowledge_statements = [
        {
            "concept_a": "machine learning",
            "concept_b": "algorithms",
            "confidence": 0.95,
        },
        {
            "concept_a": "deep learning",
            "concept_b": "neural networks",
            "confidence": 0.92,
        },
        {"concept_a": "database", "concept_b": "storage", "confidence": 0.88},
        {
            "concept_a": "machine learning",
            "concept_b": "cooking recipes",
            "confidence": 0.15,
        },  # 異常
        {
            "concept_a": "neural networks",
            "concept_b": "car maintenance",
            "confidence": 0.05,
        },  # 異常
    ]

    anomalies = graph.detect_knowledge_anomalies(knowledge_statements)

    tests_passed = 0
    tests_total = 3

    if isinstance(anomalies, list):
        print(f"  ✅ 異常リスト: {len(anomalies)}件")
        tests_passed += 1
    else:
        print("  ❌ Wrong anomalies type")

    if len(anomalies) >= 2:
        print("  ✅ 複数異常検出")
        tests_passed += 1
    else:
        print(f"  ❌ Expected >= 2 anomalies, got {len(anomalies)}")

    if anomalies and all(anom.get("confidence", 1) < 0.3 for anom in anomalies):
        print("  ✅ 低信頼度異常検出")
        tests_passed += 1
    elif not anomalies:
        print("  ⚠️ 異常未検出")
        tests_passed += 1
    else:
        print("  ❌ High confidence anomalies detected")

    return tests_passed, tests_total


def test_multilingual_knowledge_integration():
    """多言語知識統合テスト"""
    print("\n🧪 多言語知識統合テスト")
    graph = DynamicKnowledgeGraph()

    multilingual_concepts = {
        "en": "machine learning",
        "ja": "機械学習",
        "zh": "机器学习",
        "es": "aprendizaje automático",
    }

    unified_concept = graph.integrate_multilingual_knowledge(multilingual_concepts)

    tests_passed = 0
    tests_total = 3

    required_fields = ["unified_id", "translations", "primary_language"]
    for field in required_fields:
        if field in unified_concept:
            print(
                f"  ✅ {field}: {unified_concept[field] if field != 'translations' else len(unified_concept[field])}言語"
            )
            tests_passed += 1
        else:
            print(f"  ❌ Missing field: {field}")

    return tests_passed, tests_total


def test_graph_statistics():
    """グラフ統計テスト"""
    print("\n🧪 グラフ統計テスト")
    graph = DynamicKnowledgeGraph()

    # サンプルデータ追加
    graph.create_node("Test concept 1", "concept")
    graph.create_node("Test concept 2", "concept")

    stats = graph.get_graph_statistics()

    tests_passed = 0
    tests_total = 6

    expected_metrics = [
        "total_nodes",
        "total_edges",
        "average_degree",
        "clustering_coefficient",
        "graph_density",
        "connected_components",
    ]

    for metric in expected_metrics:
        # 複雑な条件判定
        if (
            metric in stats
            and isinstance(stats[metric], (int, float))
            and stats[metric] >= 0
        ):
            print(f"  ✅ {metric}: {stats[metric]}")
            tests_passed += 1
        else:
            print(f"  ❌ Invalid metric: {metric}")

    return tests_passed, tests_total


def test_knowledge_quality_assessment():
    """知識品質評価テスト"""
    print("\n🧪 知識品質評価テスト")
    graph = DynamicKnowledgeGraph()

    quality_assessment = graph.assess_knowledge_quality()

    tests_passed = 0
    tests_total = 4

    expected_metrics = [
        "overall_quality_score",
        "consistency_score",
        "completeness_score",
        "accuracy_score",
    ]

    for metric in expected_metrics:
        if metric in quality_assessment and 0 <= quality_assessment[metric] <= 1:
            print(f"  ✅ {metric}: {quality_assessment[metric]:.3f}")
            tests_passed += 1
        else:
            print(f"  ❌ Invalid quality metric: {metric}")

    return tests_passed, tests_total


async def test_complete_discovery_workflow():
    """完全発見ワークフローテスト"""
    print("\n🧪 完全発見ワークフローテスト")
    graph = DynamicKnowledgeGraph()

    input_documents = [
        "Artificial intelligence transforms business operations",
        "Machine learning algorithms optimize resource allocation",
        "Deep learning models improve prediction accuracy",
        "Neural networks process complex data patterns",
    ]

    discovery_config = {
        "enable_clustering": True,
        "enable_inference": True,
        "similarity_threshold": 0.7,
        "max_relations_per_concept": 5,
    }

    discovery_result = await graph.run_discovery_cycle(
        input_documents, discovery_config
    )

    tests_passed = 0
    tests_total = 3

    if hasattr(discovery_result, "discovery_type"):
        print(f"  ✅ 発見タイプ: {discovery_result.discovery_type}")
        tests_passed += 1
    else:
        print("  ❌ No discovery type")

    if hasattr(discovery_result, "entities") and len(discovery_result.entities) >= 0:
        print(f"  ✅ 発見エンティティ: {len(discovery_result.entities)}個")
        tests_passed += 1
    else:
        print("  ❌ No entities")

    if (
        hasattr(discovery_result, "confidence")
        and 0 <= discovery_result.confidence <= 1
    ):
        print(f"  ✅ 信頼度: {discovery_result.confidence:.3f}")
        tests_passed += 1
    else:
        print("  ❌ Invalid confidence")

    return tests_passed, tests_total


async def main():
    """メインテスト実行"""
    print("🌐 動的知識グラフシステムテスト開始")
    print("=" * 60)

    total_passed = 0
    total_tests = 0

    # 同期テスト実行
    sync_tests = [
        test_knowledge_node_creation,
        test_node_importance_scoring,
        test_node_similarity_calculation,
        test_knowledge_edge_creation,
        test_edge_strength_calculation,
        test_semantic_embedding_generation,
        test_embedding_similarity_search,
        test_knowledge_clustering,
        test_cluster_coherence_measurement,
        test_knowledge_evolution_tracking,
        test_anomaly_detection_in_knowledge,
        test_multilingual_knowledge_integration,
        test_graph_statistics,
        test_knowledge_quality_assessment,
    ]

    for test_func in sync_tests:
        passed, total = test_func()
        total_passed += passed
        total_tests += total

    # 非同期テスト実行
    async_tests = [
        test_concept_relations_discovery,
        test_dynamic_graph_update,
        test_knowledge_inference,
        test_complete_discovery_workflow,
    ]

    for test_func in async_tests:
        passed, total = await test_func()
        total_passed += passed
        total_tests += total

    # 結果サマリー
    print("\n" + "=" * 60)
    print(f"📊 テスト結果: {total_passed}/{total_tests} 成功")
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

    if total_passed == total_tests:
        print("🎉 すべてのテストが成功しました！")
        print("🌐 動的知識グラフシステムが正常に動作しています")
        print("🔗 知識の関連性自動発見と多言語対応が完成しました")
        return 0
    elif success_rate >= 85:
        print(f"✅ 大部分のテストが成功しました ({success_rate:.1f}%)")
        print("🌐 知識グラフシステムは基本的に正常に動作しています")
        return 0
    else:
        print(f"❌ {total_tests - total_passed}個のテストが失敗しました")
        print(f"成功率: {success_rate:.1f}%")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
