#!/usr/bin/env python3
"""
Advanced RAG Precision Engine
最新の論文・研究に基づくRAG精度向上システム

🎯 実装手法:
1. ハイブリッド検索アルゴリズム (Cosine + BM25)
2. 動的信頼度計算式 (Multi-factor Confidence)
3. RAGAS拡張メトリクス (5指標統合)
4. O1-Embedder方式 (推論拡張埋め込み)
5. 多段階フィルタリング (Position-weighted Ranking)
"""

import asyncio
import json
import logging
import math
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import numpy as np
from collections import Counter, defaultdict
import sqlite3

# 必要に応じてインストール可能な科学計算ライブラリ
try:
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.feature_extraction.text import TfidfVectorizer

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️ scikit-learn not available, using manual implementations")


@dataclass
class SearchResult:
    """検索結果"""

    doc_id: str
    content: str
    title: str
    hybrid_score: float
    cosine_score: float
    bm25_score: float
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class RAGASMetrics:
    """RAGAS拡張メトリクス"""

    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float
    groundedness: float
    overall_score: float


class AdvancedRAGPrecisionEngine:
    """Advanced RAG Precision Engine - 最新手法統合システム"""

    def __init__(self):
        self.logger = self._setup_logger()

        # データベース設定
        self.db_path = "/home/aicompany/ai_co/data/advanced_rag_precision.db"
        self._setup_database()

        # 検索パラメータ
        self.search_config = {
            "hybrid_alpha": 0.7,  # ベクトル検索重み
            "hybrid_beta": 0.3,  # キーワード検索重み
            "max_results": 10,
            "confidence_threshold": 0.6,
            "position_decay": 0.85,  # 順位減衰率
        }

        # RAGAS重み設定
        self.ragas_weights = {
            "faithfulness": 0.25,
            "answer_relevancy": 0.25,
            "context_precision": 0.20,
            "context_recall": 0.20,
            "groundedness": 0.10,
        }

        # 文書データベース
        self.document_store: Dict[str, Dict[str, Any]] = {}
        self.document_embeddings: Dict[str, List[float]] = {}
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None

        self.logger.info("🎯 Advanced RAG Precision Engine initialized")

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("advanced_rag_precision")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - RAG Precision - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _setup_database(self):
        """データベース設定"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 検索結果テーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS search_results (
                result_id TEXT PRIMARY KEY,
                query TEXT,
                doc_id TEXT,
                hybrid_score REAL,
                cosine_score REAL,
                bm25_score REAL,
                confidence REAL,
                timestamp TEXT
            )
        """
        )

        # RAGASメトリクステーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ragas_metrics (
                metric_id TEXT PRIMARY KEY,
                query TEXT,
                generated_answer TEXT,
                faithfulness REAL,
                answer_relevancy REAL,
                context_precision REAL,
                context_recall REAL,
                groundedness REAL,
                overall_score REAL,
                timestamp TEXT
            )
        """
        )

        # 改善履歴テーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS improvement_history (
                improvement_id TEXT PRIMARY KEY,
                method_name TEXT,
                baseline_score REAL,
                improved_score REAL,
                improvement_rate REAL,
                test_cases_count INTEGER,
                timestamp TEXT
            )
        """
        )

        conn.commit()
        conn.close()

    async def initialize_document_store(self, documents: List[Dict[str, Any]]):
        """文書ストアの初期化"""
        self.logger.info(
            f"🔄 Initializing document store with {len(documents)} documents..."
        )

        # 文書の格納
        for doc in documents:
            doc_id = doc.get("id", f"doc_{len(self.document_store)}")
            self.document_store[doc_id] = {
                "title": doc.get("title", ""),
                "content": doc.get("content", ""),
                "metadata": doc.get("metadata", {}),
            }

        # 埋め込みとTF-IDFの生成
        await self._generate_embeddings()
        await self._build_tfidf_index()

        self.logger.info(
            f"✅ Document store initialized with {len(self.document_store)} documents"
        )

    async def _generate_embeddings(self):
        """文書埋め込みの生成（シミュレーション）"""
        self.logger.info("🧠 Generating document embeddings...")

        for doc_id, doc_data in self.document_store.items():
            # 実際の実装では高度な埋め込みモデルを使用
            content = doc_data["content"]

            # シミュレーション用の埋め込み生成
            embedding = await self._simulate_embedding(content)
            self.document_embeddings[doc_id] = embedding

        self.logger.info(
            f"✅ Generated embeddings for {len(self.document_embeddings)} documents"
        )

    async def _simulate_embedding(self, text: str, dim: int = 384) -> List[float]:
        """埋め込みシミュレーション"""
        # テキストベースのシード値でランダム性を固定
        seed = sum(ord(c) for c in text[:100]) % (2**32)
        np.random.seed(seed)

        # 正規化されたランダムベクトル
        vector = np.random.randn(dim)
        vector = vector / np.linalg.norm(vector)

        return vector.tolist()

    async def _build_tfidf_index(self):
        """TF-IDFインデックスの構築"""
        self.logger.info("📊 Building TF-IDF index...")

        if not SKLEARN_AVAILABLE:
            self.logger.warning("scikit-learn not available, skipping TF-IDF indexing")
            return

        # 全文書のコンテンツを取得
        documents = [doc_data["content"] for doc_data in self.document_store.values()]

        # TF-IDFベクトル化
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000, stop_words="english", ngram_range=(1, 2)
        )

        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(documents)
        self.logger.info("✅ TF-IDF index built successfully")

    async def hybrid_search(self, query: str, top_k: int = None) -> List[SearchResult]:
        """
        ハイブリッド検索アルゴリズム (Cosine + BM25)

        Args:
            query: 検索クエリ
            top_k: 返す結果数

        Returns:
            List[SearchResult]: ハイブリッドスコアでソートされた検索結果
        """
        if top_k is None:
            top_k = self.search_config["max_results"]

        self.logger.info(f"🔍 Hybrid search for: '{query[:50]}...'")

        # 1. クエリ埋め込み生成
        query_embedding = await self._simulate_embedding(query)

        # 2. 各文書のスコア計算
        results = []

        for doc_id, doc_data in self.document_store.items():
            # コサイン類似度計算
            cosine_score = await self._calculate_cosine_similarity(
                query_embedding, self.document_embeddings[doc_id]
            )

            # BM25スコア計算
            bm25_score = await self._calculate_bm25_score(query, doc_data["content"])

            # ハイブリッドスコア計算
            hybrid_score = (
                self.search_config["hybrid_alpha"] * cosine_score
                + self.search_config["hybrid_beta"] * bm25_score
            )

            # 信頼度計算
            confidence = await self._calculate_multi_factor_confidence(
                cosine_score, bm25_score, doc_data["content"], query
            )

            if hybrid_score > 0.05:  # 最小閾値を下げて結果を取得
                results.append(
                    SearchResult(
                        doc_id=doc_id,
                        content=doc_data["content"][:500] + "...",
                        title=doc_data["title"],
                        hybrid_score=hybrid_score,
                        cosine_score=cosine_score,
                        bm25_score=bm25_score,
                        confidence=confidence,
                        metadata=doc_data["metadata"],
                    )
                )

        # 3. ハイブリッドスコアでソート
        results.sort(key=lambda x: x.hybrid_score, reverse=True)

        # 4. 順位による重み付け（Position-weighted Ranking）
        for i, result in enumerate(results):
            position_weight = self.search_config["position_decay"] ** i
            result.hybrid_score *= position_weight

        # 5. 結果を記録
        await self._record_search_results(query, results[:top_k])

        self.logger.info(f"✅ Found {len(results[:top_k])} relevant results")
        return results[:top_k]

    async def _calculate_cosine_similarity(
        self, vec1: List[float], vec2: List[float]
    ) -> float:
        """コサイン類似度計算"""
        if SKLEARN_AVAILABLE:
            return float(cosine_similarity([vec1], [vec2])[0][0])
        else:
            # 手動実装
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(b * b for b in vec2))

            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0

            return dot_product / (magnitude1 * magnitude2)

    async def _calculate_bm25_score(self, query: str, document: str) -> float:
        """BM25スコア計算"""
        # BM25パラメータ
        k1 = 1.2
        b = 0.75

        # クエリとドキュメントの前処理
        query_terms = set(query.lower().split())
        doc_terms = document.lower().split()
        doc_length = len(doc_terms)

        if doc_length == 0:
            return 0.0

        # 平均文書長（簡易計算）
        avg_doc_length = sum(
            len(doc["content"].split()) for doc in self.document_store.values()
        ) / len(self.document_store)

        score = 0.0
        for term in query_terms:
            # 語の出現頻度
            tf = doc_terms.count(term)
            if tf == 0:
                continue

            # 文書頻度（簡易版: 全文書での出現率）
            df = sum(
                1
                for doc in self.document_store.values()
                if term in doc["content"].lower()
            )

            # IDF計算
            idf = math.log((len(self.document_store) - df + 0.5) / (df + 0.5))

            # BM25スコア計算
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))

            score += idf * (numerator / denominator)

        # 正規化
        return min(score / len(query_terms), 1.0) if query_terms else 0.0

    async def _calculate_multi_factor_confidence(
        self, cosine_score: float, bm25_score: float, document: str, query: str
    ) -> float:
        """
        多要素信頼度計算

        Args:
            cosine_score: コサイン類似度
            bm25_score: BM25スコア
            document: 文書内容
            query: クエリ

        Returns:
            float: 統合信頼度スコア
        """
        # 1. 基本信頼度 (ハイブリッドスコアベース)
        base_confidence = 0.7 * cosine_score + 0.3 * bm25_score

        # 2. 検索文書との整合性
        query_terms = set(query.lower().split())
        doc_terms = set(document.lower().split())

        if query_terms:
            alignment_score = len(query_terms.intersection(doc_terms)) / len(
                query_terms
            )
        else:
            alignment_score = 0.0

        # 3. 応答の一貫性（文書内での語の分布）
        doc_words = document.lower().split()
        if doc_words:
            # 重要語の密度
            important_words = [word for word in doc_words if len(word) > 4]
            density_score = len(important_words) / len(doc_words)
        else:
            density_score = 0.0

        # 4. 統合信頼度計算
        confidence_weights = [0.5, 0.3, 0.2]
        final_confidence = (
            confidence_weights[0] * base_confidence
            + confidence_weights[1] * alignment_score
            + confidence_weights[2] * density_score
        )

        return min(final_confidence, 1.0)

    async def calculate_ragas_metrics(
        self,
        query: str,
        generated_answer: str,
        retrieved_contexts: List[str],
        ground_truth: str = None,
    ) -> RAGASMetrics:
        """
        RAGAS拡張メトリクス計算

        Args:
            query: 質問
            generated_answer: 生成された回答
            retrieved_contexts: 検索されたコンテキスト
            ground_truth: 正解回答（オプション）

        Returns:
            RAGASMetrics: 拡張RAGAS評価メトリクス
        """
        self.logger.info("📊 Calculating enhanced RAGAS metrics...")

        # 1. Faithfulness (忠実性)
        faithfulness = await self._calculate_faithfulness(
            generated_answer, retrieved_contexts
        )

        # 2. Answer Relevancy (回答関連性)
        answer_relevancy = await self._calculate_answer_relevancy(
            generated_answer, query
        )

        # 3. Context Precision (コンテキスト精度)
        context_precision = await self._calculate_context_precision(
            retrieved_contexts, ground_truth
        )

        # 4. Context Recall (コンテキスト再現率)
        context_recall = await self._calculate_context_recall(
            retrieved_contexts, ground_truth
        )

        # 5. Response Groundedness (応答根拠性) - 新指標
        groundedness = await self._calculate_response_groundedness(
            generated_answer, retrieved_contexts
        )

        # 6. 総合スコア計算
        overall_score = (
            self.ragas_weights["faithfulness"] * faithfulness
            + self.ragas_weights["answer_relevancy"] * answer_relevancy
            + self.ragas_weights["context_precision"] * context_precision
            + self.ragas_weights["context_recall"] * context_recall
            + self.ragas_weights["groundedness"] * groundedness
        )

        metrics = RAGASMetrics(
            faithfulness=faithfulness,
            answer_relevancy=answer_relevancy,
            context_precision=context_precision,
            context_recall=context_recall,
            groundedness=groundedness,
            overall_score=overall_score,
        )

        # メトリクスを記録
        await self._record_ragas_metrics(query, generated_answer, metrics)

        self.logger.info(
            f"✅ RAGAS metrics calculated: Overall score = {overall_score:.3f}"
        )
        return metrics

    async def _calculate_faithfulness(self, answer: str, contexts: List[str]) -> float:
        """忠実性計算"""
        if not contexts or not answer:
            return 0.0

        # answerが文字列でない場合の対応
        if isinstance(answer, (list, tuple)):
            answer = " ".join(str(item) for item in answer)
        elif not isinstance(answer, str):
            answer = str(answer)

        # 回答の各文について、コンテキストで支持されているかチェック
        answer_sentences = re.split(r"[.!?]+", answer)
        supported_count = 0

        for sentence in answer_sentences:
            if len(sentence.strip()) < 10:  # 短すぎる文はスキップ
                continue

            # コンテキストでの支持度チェック
            sentence_words = set(sentence.lower().split())

            for context in contexts:
                context_words = set(context.lower().split())
                overlap = len(sentence_words.intersection(context_words))

                if overlap >= len(sentence_words) * 0.5:  # 50%以上の重複で支持とみなす
                    supported_count += 1
                    break

        return supported_count / max(len(answer_sentences), 1)

    async def _calculate_answer_relevancy(self, answer: str, query: str) -> float:
        """回答関連性計算"""
        if not answer or not query:
            return 0.0

        # answerが文字列でない場合の対応
        if isinstance(answer, (list, tuple)):
            answer = " ".join(str(item) for item in answer)
        elif not isinstance(answer, str):
            answer = str(answer)

        # クエリと回答の語彙重複度
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())

        if not query_words:
            return 0.0

        overlap = len(query_words.intersection(answer_words))
        return overlap / len(query_words)

    async def _calculate_context_precision(
        self, contexts: List[str], ground_truth: str
    ) -> float:
        """コンテキスト精度計算"""
        if not contexts or not ground_truth:
            return 0.0

        relevant_count = 0
        for i, context in enumerate(contexts):
            # 順位による重み付け
            position_weight = 1.0 / (i + 1)

            # 正解との関連度チェック
            context_words = set(context.lower().split())
            truth_words = set(ground_truth.lower().split())

            overlap = len(context_words.intersection(truth_words))
            if overlap >= len(truth_words) * 0.3:  # 30%以上の重複で関連とみなす
                relevant_count += position_weight

        return relevant_count / len(contexts)

    async def _calculate_context_recall(
        self, contexts: List[str], ground_truth: str
    ) -> float:
        """コンテキスト再現率計算"""
        if not contexts or not ground_truth:
            return 0.0

        # 正解情報がコンテキストでどの程度カバーされているか
        truth_words = set(ground_truth.lower().split())
        covered_words = set()

        for context in contexts:
            context_words = set(context.lower().split())
            covered_words.update(context_words.intersection(truth_words))

        return len(covered_words) / max(len(truth_words), 1)

    async def _calculate_response_groundedness(
        self, answer: str, contexts: List[str]
    ) -> float:
        """応答根拠性計算（新指標）"""
        if not answer or not contexts:
            return 0.0

        # answerが文字列でない場合の対応
        if isinstance(answer, (list, tuple)):
            answer = " ".join(str(item) for item in answer)
        elif not isinstance(answer, str):
            answer = str(answer)

        # 回答の各重要語について、コンテキストでの根拠を確認
        answer_words = [word for word in answer.lower().split() if len(word) > 3]
        grounded_words = 0

        all_context_words = set()
        for context in contexts:
            all_context_words.update(context.lower().split())

        for word in answer_words:
            if word in all_context_words:
                grounded_words += 1

        return grounded_words / max(len(answer_words), 1)

    async def o1_embedder_reasoning(self, query: str) -> str:
        """
        O1-Embedder方式: 推論拡張埋め込み

        Args:
            query: 元のクエリ

        Returns:
            str: 推論プロセスで拡張されたクエリ
        """
        self.logger.info(f"🧠 O1-Embedder reasoning for: '{query}'")

        # 推論プロセス生成（簡易版）
        thinking_steps = []

        # 1. クエリ分析
        if "実装" in query or "開発" in query:
            thinking_steps.append("これは開発・実装に関する質問です。")
            thinking_steps.append("技術仕様、設計パターン、実装例が必要です。")

        if "最適化" in query or "パフォーマンス" in query:
            thinking_steps.append("これは性能改善に関する質問です。")
            thinking_steps.append("ボトルネック分析、改善手法、測定方法が重要です。")

        if "エラー" in query or "バグ" in query or "修正" in query:
            thinking_steps.append("これは問題解決に関する質問です。")
            thinking_steps.append("原因分析、解決策、予防策が必要です。")

        # 2. 関連技術の推論
        tech_keywords = [
            "Elder",
            "Flow",
            "RAG",
            "API",
            "OAuth",
            "WebSocket",
            "データベース",
        ]
        found_tech = [tech for tech in tech_keywords if tech.lower() in query.lower()]

        if found_tech:
            thinking_steps.append(f"関連技術: {', '.join(found_tech)}")
            thinking_steps.append("これらの技術に特化した情報を検索すべきです。")

        # 3. 拡張クエリ生成
        thinking_text = " ".join(thinking_steps)
        enhanced_query = f"{query} [THINKING] {thinking_text}"

        self.logger.info(
            f"✅ Enhanced query with reasoning: {len(enhanced_query)} chars"
        )
        return enhanced_query

    async def adaptive_retrieval_strategy(self, query: str) -> str:
        """
        適応的検索戦略選択

        Args:
            query: 検索クエリ

        Returns:
            str: 選択された検索戦略
        """
        # クエリ複雑度の計算
        complexity_factors = {
            "length": len(query.split()) / 20,  # 語数による複雑度
            "technical_terms": sum(1 for word in query.split() if len(word) > 6)
            / len(query.split()),
            "question_depth": query.count("なぜ")
            + query.count("どのように")
            + query.count("why")
            + query.count("how"),
        }

        complexity = sum(complexity_factors.values()) / len(complexity_factors)

        if complexity < 0.3:
            strategy = "simple_vector_search"
        elif complexity < 0.7:
            strategy = "hybrid_search"
        else:
            strategy = "multi_hop_reasoning"

        self.logger.info(
            f"🎯 Selected strategy: {strategy} (complexity: {complexity:.2f})"
        )
        return strategy

    async def _record_search_results(self, query: str, results: List[SearchResult]):
        """検索結果の記録"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for i, result in enumerate(results):
                cursor.execute(
                    """
                    INSERT INTO search_results
                    (result_id, query, doc_id, hybrid_score, cosine_score, bm25_score, confidence, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        f"result_{datetime.now().timestamp()}_{i}",
                        query,
                        result.doc_id,
                        result.hybrid_score,
                        result.cosine_score,
                        result.bm25_score,
                        result.confidence,
                        datetime.now().isoformat(),
                    ),
                )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to record search results: {e}")

    async def _record_ragas_metrics(
        self, query: str, answer: str, metrics: RAGASMetrics
    ):
        """RAGASメトリクスの記録"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO ragas_metrics
                (metric_id, query, generated_answer, faithfulness, answer_relevancy,
                 context_precision, context_recall, groundedness, overall_score, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    f"metric_{datetime.now().timestamp()}",
                    query,
                    answer,
                    metrics.faithfulness,
                    metrics.answer_relevancy,
                    metrics.context_precision,
                    metrics.context_recall,
                    metrics.groundedness,
                    metrics.overall_score,
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to record RAGAS metrics: {e}")

    async def benchmark_improvements(
        self, test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        改善効果のベンチマーク

        Args:
            test_cases: テストケースリスト

        Returns:
            Dict[str, Any]: ベンチマーク結果
        """
        self.logger.info(f"🔬 Running benchmark with {len(test_cases)} test cases...")

        baseline_scores = []
        improved_scores = []

        for test_case in test_cases:
            query = test_case["query"]
            expected_docs = test_case.get("expected_docs", [])

            # ベースライン検索（単純コサイン類似度）
            baseline_results = await self._baseline_search(query)
            baseline_score = self._calculate_relevance_score(
                baseline_results, expected_docs
            )
            baseline_scores.append(baseline_score)

            # 改善版検索（ハイブリッド）
            improved_results = await self.hybrid_search(query)
            improved_score = self._calculate_relevance_score(
                improved_results, expected_docs
            )
            improved_scores.append(improved_score)

        # 統計計算
        avg_baseline = sum(baseline_scores) / len(baseline_scores)
        avg_improved = sum(improved_scores) / len(improved_scores)
        improvement_rate = (
            (avg_improved - avg_baseline) / max(avg_baseline, 0.001)
        ) * 100  # ゼロ除算対策

        benchmark_result = {
            "test_cases_count": len(test_cases),
            "baseline_average": avg_baseline,
            "improved_average": avg_improved,
            "improvement_rate_percent": improvement_rate,
            "individual_results": [
                {
                    "query": test_cases[i]["query"],
                    "baseline": baseline_scores[i],
                    "improved": improved_scores[i],
                    "improvement": (
                        (improved_scores[i] - baseline_scores[i])
                        / max(baseline_scores[i], 0.001)
                    )
                    * 100,
                }
                for i in range(len(test_cases))
            ],
        }

        # 結果を記録
        await self._record_improvement_history(
            "hybrid_search", avg_baseline, avg_improved, len(test_cases)
        )

        self.logger.info(f"✅ Benchmark complete: {improvement_rate:.1f}% improvement")
        return benchmark_result

    async def _baseline_search(self, query: str) -> List[SearchResult]:
        """ベースライン検索（単純コサイン類似度）"""
        query_embedding = await self._simulate_embedding(query)
        results = []

        for doc_id, doc_data in self.document_store.items():
            cosine_score = await self._calculate_cosine_similarity(
                query_embedding, self.document_embeddings[doc_id]
            )

            if cosine_score > 0.05:  # 閾値を下げて結果を取得
                results.append(
                    SearchResult(
                        doc_id=doc_id,
                        content=doc_data["content"][:500] + "...",
                        title=doc_data["title"],
                        hybrid_score=cosine_score,
                        cosine_score=cosine_score,
                        bm25_score=0.0,
                        confidence=cosine_score,
                        metadata=doc_data["metadata"],
                    )
                )

        results.sort(key=lambda x: x.cosine_score, reverse=True)
        return results[: self.search_config["max_results"]]

    def _calculate_relevance_score(
        self, results: List[SearchResult], expected_docs: List[str]
    ) -> float:
        """関連性スコア計算"""
        if not expected_docs:
            return 0.5  # デフォルトスコア

        found_relevant = 0
        for result in results[:5]:  # 上位5件で評価
            if result.doc_id in expected_docs:
                found_relevant += 1

        return found_relevant / min(len(expected_docs), 5)

    async def _record_improvement_history(
        self, method_name: str, baseline: float, improved: float, test_count: int
    ):
        """改善履歴の記録"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            improvement_rate = (
                ((improved - baseline) / baseline) * 100 if baseline > 0 else 0
            )

            cursor.execute(
                """
                INSERT INTO improvement_history
                (improvement_id, method_name, baseline_score, improved_score,
                 improvement_rate, test_cases_count, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    f"improvement_{datetime.now().timestamp()}",
                    method_name,
                    baseline,
                    improved,
                    improvement_rate,
                    test_count,
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to record improvement history: {e}")


# デモンストレーション
async def demo_advanced_rag_precision():
    """Advanced RAG Precision Engine デモ"""
    print("🎯 Advanced RAG Precision Engine Demo")
    print("=" * 60)

    engine = AdvancedRAGPrecisionEngine()

    # サンプル文書の準備
    sample_documents = [
        {
            "id": "doc_elder_flow",
            "title": "Elder Flow開発ガイド",
            "content": "Elder Flowは自動化開発フローシステムです。4賢者との連携によりMind Reading Protocolと統合し、グランドエルダーmaruの意図を理解して自動実行します。OAuth2.0認証システムやWebSocket通信の実装を支援します。",
            "metadata": {"category": "development", "importance": "high"},
        },
        {
            "id": "doc_rag_system",
            "title": "RAG検索システム実装",
            "content": "RAGシステムはRetrieval-Augmented Generationの略で、検索技術と生成AIを組み合わせたシステムです。ベクトル検索とキーワード検索を統合し、文脈理解を深化させます。BM25アルゴリズムとコサイン類似度を併用します。",
            "metadata": {"category": "rag", "importance": "high"},
        },
        {
            "id": "doc_performance",
            "title": "パフォーマンス最適化ガイド",
            "content": "システムのパフォーマンス最適化には複数のアプローチがあります。データベースクエリの最適化、キャッシュの活用、非同期処理の導入などが効果的です。監視システムでボトルネックを特定し、段階的に改善します。",
            "metadata": {"category": "optimization", "importance": "medium"},
        },
        {
            "id": "doc_security",
            "title": "セキュリティ監査システム",
            "content": "セキュリティ監査システムは脆弱性の検出と対策を自動化します。OAuth2.0認証、API セキュリティ、データ暗号化を実装し、リアルタイム監視により不正アクセスを防止します。",
            "metadata": {"category": "security", "importance": "high"},
        },
        {
            "id": "doc_websocket",
            "title": "WebSocket実装ガイド",
            "content": "WebSocketを使用したリアルタイム通信機能の実装方法。接続管理、メッセージングプロトコル、エラーハンドリングを含む完全なガイドです。マイクロサービス間の通信最適化にも対応します。",
            "metadata": {"category": "websocket", "importance": "medium"},
        },
    ]

    # 文書ストア初期化
    await engine.initialize_document_store(sample_documents)

    # テストクエリ
    test_queries = [
        "Elder FlowでOAuth2.0認証システムを実装してください",
        "RAGシステムの検索精度を向上させる方法",
        "WebSocketを使ったリアルタイム通信の最適化",
        "パフォーマンス問題の特定と解決策",
        "セキュリティ監査の自動化手法",
    ]

    print("\n🔍 Hybrid Search Results:")
    print("-" * 40)

    all_results = []

    for i, query in enumerate(test_queries, 1):
        print(f"\n[Query {i}] {query}")

        # O1-Embedder推論拡張
        enhanced_query = await engine.o1_embedder_reasoning(query)

        # 適応的検索戦略
        strategy = await engine.adaptive_retrieval_strategy(query)

        # ハイブリッド検索実行
        results = await engine.hybrid_search(query, top_k=3)

        print(f"   🧠 Enhanced Query: {len(enhanced_query)} chars")
        print(f"   🎯 Strategy: {strategy}")
        print(f"   📊 Results: {len(results)} documents")

        for j, result in enumerate(results, 1):
            print(f"     [{j}] {result.title}")
            print(
                f"         Hybrid: {result.hybrid_score:.3f} | "
                f"Cosine: {result.cosine_score:.3f} | "
                f"BM25: {result.bm25_score:.3f} | "
                f"Confidence: {result.confidence:.3f}"
            )

        all_results.extend(results)

    # RAGASメトリクス計算デモ
    print(f"\n📊 RAGAS Metrics Demo:")
    print("-" * 40)

    sample_query = "RAGシステムの精度向上方法を教えて"
    sample_answer = "RAGシステムの精度向上には、ハイブリッド検索アルゴリズムの採用、動的信頼度計算、RAGAS拡張メトリクスの活用が効果的です。"
    sample_contexts = [doc["content"] for doc in sample_documents[:3]]

    ragas_metrics = await engine.calculate_ragas_metrics(
        query=sample_query,
        generated_answer=sample_answer,
        retrieved_contexts=sample_contexts,
    )

    print(f"   Faithfulness: {ragas_metrics.faithfulness:.3f}")
    print(f"   Answer Relevancy: {ragas_metrics.answer_relevancy:.3f}")
    print(f"   Context Precision: {ragas_metrics.context_precision:.3f}")
    print(f"   Context Recall: {ragas_metrics.context_recall:.3f}")
    print(f"   Groundedness: {ragas_metrics.groundedness:.3f}")
    print(f"   🎯 Overall Score: {ragas_metrics.overall_score:.3f}")

    # ベンチマークテスト
    print(f"\n🔬 Benchmark Test:")
    print("-" * 40)

    test_cases = [
        {"query": "Elder Flow実装", "expected_docs": ["doc_elder_flow"]},
        {"query": "RAG検索精度向上", "expected_docs": ["doc_rag_system"]},
        {"query": "WebSocket最適化", "expected_docs": ["doc_websocket"]},
        {"query": "セキュリティ強化", "expected_docs": ["doc_security"]},
        {"query": "パフォーマンス改善", "expected_docs": ["doc_performance"]},
    ]

    benchmark_results = await engine.benchmark_improvements(test_cases)

    print(f"   Test Cases: {benchmark_results['test_cases_count']}")
    print(f"   Baseline Average: {benchmark_results['baseline_average']:.3f}")
    print(f"   Improved Average: {benchmark_results['improved_average']:.3f}")
    print(
        f"   🎯 Improvement Rate: {benchmark_results['improvement_rate_percent']:.1f}%"
    )

    # 個別結果
    print(f"\n   Individual Results:")
    for result in benchmark_results["individual_results"]:
        print(f"     '{result['query']}': {result['improvement']:.1f}% improvement")

    print(f"\n✨ Advanced RAG Precision Engine Demo Complete!")
    print(f"🎯 Successfully demonstrated:")
    print(f"   • Hybrid Search Algorithm (Cosine + BM25)")
    print(f"   • Multi-factor Confidence Calculation")
    print(f"   • Enhanced RAGAS Metrics (5 indicators)")
    print(f"   • O1-Embedder Reasoning Enhancement")
    print(f"   • Adaptive Retrieval Strategy")
    print(f"   • Comprehensive Benchmarking")


if __name__ == "__main__":
    asyncio.run(demo_advanced_rag_precision())
