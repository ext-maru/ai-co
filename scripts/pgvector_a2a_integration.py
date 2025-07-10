#!/usr/bin/env python3
"""
pgvector統合A2Aセマンティック分析システム
リアルタイムでA2A通信を分析し、pgvectorを使用してセマンティック検索を実行
"""

import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from enum import Enum
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# OpenAI import
try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """分析タイプ"""

    SIMILARITY_SEARCH = "similarity_search"
    ANOMALY_DETECTION = "anomaly_detection"
    PATTERN_MATCHING = "pattern_matching"
    AGENT_BEHAVIOR = "agent_behavior"
    TEMPORAL_ANALYSIS = "temporal_analysis"


@dataclass
class SemanticQuery:
    """セマンティッククエリ"""

    query_text: str
    query_type: AnalysisType
    limit: int = 10
    threshold: float = 0.7
    time_window: Optional[timedelta] = None
    filters: Optional[Dict[str, Any]] = None


@dataclass
class AnalysisResult:
    """分析結果"""

    query: SemanticQuery
    results: List[Dict[str, Any]]
    insights: Dict[str, Any]
    performance_metrics: Dict[str, float]
    timestamp: datetime


class PgVectorA2AAnalyzer:
    """pgvectorを使用したA2A分析システム"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_default_config()
        self.connection = None
        self.cursor = None
        self.openai_client = None

        # 分析キャッシュ
        self.cache = {}
        self.cache_ttl = 300  # 5分

    def _load_default_config(self) -> Dict[str, Any]:
        """デフォルト設定の読み込み"""
        return {
            "database": {
                "host": os.getenv("PGHOST", "localhost"),
                "port": int(os.getenv("PGPORT", 5432)),
                "database": os.getenv("PGDATABASE", "ai_company_db"),
                "user": os.getenv("PGUSER", "aicompany"),
                "password": os.getenv("PGPASSWORD", ""),
            },
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "model": "text-embedding-3-small",
                "dimension": 1536,
            },
            "analysis": {"default_limit": 20, "similarity_threshold": 0.7, "anomaly_threshold": 0.3, "batch_size": 100},
        }

    def connect(self):
        """データベース接続"""
        try:
            self.connection = psycopg2.connect(**self.config["database"], cursor_factory=RealDictCursor)
            self.cursor = self.connection.cursor()

            # pgvector拡張の確認
            self.cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector';")
            if not self.cursor.fetchone():
                raise Exception("pgvector extension not installed")

            logger.info("Connected to pgvector database")

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise

    def setup_openai(self):
        """OpenAI APIのセットアップ"""
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI library not available")
            return False

        api_key = self.config["openai"]["api_key"]
        if not api_key:
            logger.warning("OpenAI API key not configured")
            return False

        try:
            self.openai_client = openai.OpenAI(api_key=api_key)
            logger.info("OpenAI API configured")
            return True
        except Exception as e:
            logger.error(f"Failed to setup OpenAI: {e}")
            return False

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """テキストからベクトル埋め込みを生成"""
        if not self.openai_client:
            return None

        try:
            response = self.openai_client.embeddings.create(
                model=self.config["openai"]["model"], input=text, dimensions=self.config["openai"]["dimension"]
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    def semantic_search(self, query: SemanticQuery) -> List[Dict[str, Any]]:
        """セマンティック検索の実行"""
        # キャッシュチェック
        cache_key = f"search_{query.query_text}_{query.limit}"
        if cache_key in self.cache:
            cached_result, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=self.cache_ttl):
                logger.info("Returning cached result")
                return cached_result

        # 埋め込み生成
        query_embedding = self.generate_embedding(query.query_text)
        if not query_embedding:
            logger.error("Failed to generate query embedding")
            return []

        # SQLクエリ構築
        sql = """
            SELECT
                c.id,
                c.timestamp,
                c.sender,
                c.receiver,
                c.message_type,
                c.content,
                c.metadata,
                1 - (c.embedding <=> %s::vector) as similarity
            FROM a2a.communications c
            WHERE c.embedding IS NOT NULL
        """

        params = [query_embedding]

        # フィルター追加
        if query.filters:
            if "sender" in query.filters:
                sql += " AND c.sender = %s"
                params.append(query.filters["sender"])
            if "receiver" in query.filters:
                sql += " AND c.receiver = %s"
                params.append(query.filters["receiver"])
            if "message_type" in query.filters:
                sql += " AND c.message_type = %s"
                params.append(query.filters["message_type"])

        # 時間窓フィルター
        if query.time_window:
            sql += " AND c.timestamp >= %s"
            params.append(datetime.now() - query.time_window)

        # 類似度閾値
        sql += " AND 1 - (c.embedding <=> %s::vector) >= %s"
        params.extend([query_embedding, query.threshold])

        # ソートと制限
        sql += " ORDER BY similarity DESC LIMIT %s"
        params.append(query.limit)

        try:
            self.cursor.execute(sql, params)
            results = self.cursor.fetchall()

            # キャッシュ保存
            self.cache[cache_key] = (results, datetime.now())

            return results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def detect_anomalies(self, query: SemanticQuery) -> List[Dict[str, Any]]:
        """異常検出の実行"""
        # 最近の通信パターンを取得
        recent_window = query.time_window or timedelta(hours=1)

        sql = """
            WITH recent_communications AS (
                SELECT
                    c.*,
                    ap.pattern_name,
                    ap.severity,
                    1 - (c.embedding <=> ap.embedding) as anomaly_similarity
                FROM a2a.communications c
                CROSS JOIN a2a.anomaly_patterns ap
                WHERE c.timestamp >= %s
                  AND c.embedding IS NOT NULL
                  AND ap.embedding IS NOT NULL
            )
            SELECT
                rc.*
            FROM recent_communications rc
            WHERE rc.anomaly_similarity >= %s
            ORDER BY rc.timestamp DESC, rc.anomaly_similarity DESC
            LIMIT %s
        """

        try:
            self.cursor.execute(sql, [datetime.now() - recent_window, query.threshold, query.limit])

            anomalies = self.cursor.fetchall()

            # 異常パターンでグループ化
            grouped_anomalies = {}
            for anomaly in anomalies:
                pattern = anomaly["pattern_name"]
                if pattern not in grouped_anomalies:
                    grouped_anomalies[pattern] = []
                grouped_anomalies[pattern].append(anomaly)

            return anomalies

        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return []

    def analyze_agent_behavior(self, agent_name: str, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """エージェント行動分析"""
        time_window = time_window or timedelta(days=1)

        analysis = {
            "agent": agent_name,
            "time_window": str(time_window),
            "communication_stats": {},
            "interaction_patterns": {},
            "anomalies": [],
            "embeddings_cluster": [],
        }

        try:
            # 通信統計
            stats_sql = """
                SELECT
                    COUNT(*) as total_messages,
                    COUNT(DISTINCT CASE WHEN sender = %s THEN receiver ELSE sender END) as unique_interactions,
                    COUNT(CASE WHEN sender = %s THEN 1 END) as sent_messages,
                    COUNT(CASE WHEN receiver = %s THEN 1 END) as received_messages,
                    COUNT(DISTINCT message_type) as message_types,
                    MAX(timestamp) as last_activity
                FROM a2a.communications
                WHERE (sender = %s OR receiver = %s)
                  AND timestamp >= %s
            """

            self.cursor.execute(
                stats_sql, [agent_name, agent_name, agent_name, agent_name, agent_name, datetime.now() - time_window]
            )

            stats = self.cursor.fetchone()
            analysis["communication_stats"] = dict(stats) if stats else {}

            # インタラクションパターン
            pattern_sql = """
                SELECT
                    CASE
                        WHEN sender = %s THEN receiver
                        ELSE sender
                    END as counterpart,
                    message_type,
                    COUNT(*) as message_count,
                    AVG(CASE WHEN metadata->>'priority' IS NOT NULL
                        THEN (metadata->>'priority')::int ELSE 0 END) as avg_priority
                FROM a2a.communications
                WHERE (sender = %s OR receiver = %s)
                  AND timestamp >= %s
                GROUP BY counterpart, message_type
                ORDER BY message_count DESC
                LIMIT 20
            """

            self.cursor.execute(pattern_sql, [agent_name, agent_name, agent_name, datetime.now() - time_window])

            patterns = self.cursor.fetchall()
            analysis["interaction_patterns"] = [dict(p) for p in patterns]

            # 異常検出
            anomaly_query = SemanticQuery(
                query_text=f"Agent {agent_name} unusual behavior",
                query_type=AnalysisType.ANOMALY_DETECTION,
                limit=5,
                time_window=time_window,
                filters={"sender": agent_name},
            )

            analysis["anomalies"] = self.detect_anomalies(anomaly_query)

            return analysis

        except Exception as e:
            logger.error(f"Agent behavior analysis failed: {e}")
            return analysis

    def find_communication_patterns(self, pattern_description: str, limit: int = 10) -> List[Dict[str, Any]]:
        """通信パターンの検索"""
        # パターン説明から埋め込みを生成
        pattern_embedding = self.generate_embedding(pattern_description)
        if not pattern_embedding:
            return []

        sql = """
            WITH pattern_matches AS (
                SELECT
                    sender,
                    receiver,
                    message_type,
                    COUNT(*) as occurrence_count,
                    AVG(1 - (embedding <=> %s::vector)) as avg_similarity,
                    ARRAY_AGG(id ORDER BY timestamp DESC LIMIT 5) as sample_ids
                FROM a2a.communications
                WHERE embedding IS NOT NULL
                  AND 1 - (embedding <=> %s::vector) >= %s
                GROUP BY sender, receiver, message_type
                HAVING COUNT(*) >= 3
            )
            SELECT
                pm.*,
                (
                    SELECT json_agg(c.*)
                    FROM a2a.communications c
                    WHERE c.id = ANY(pm.sample_ids)
                ) as sample_communications
            FROM pattern_matches pm
            ORDER BY pm.avg_similarity DESC, pm.occurrence_count DESC
            LIMIT %s
        """

        try:
            self.cursor.execute(
                sql, [pattern_embedding, pattern_embedding, self.config["analysis"]["similarity_threshold"], limit]
            )

            patterns = self.cursor.fetchall()
            return [dict(p) for p in patterns]

        except Exception as e:
            logger.error(f"Pattern search failed: {e}")
            return []

    def temporal_analysis(self, time_buckets: str = "1 hour") -> Dict[str, Any]:
        """時系列分析"""
        sql = f"""
            SELECT
                date_trunc('{time_buckets}', timestamp) as time_bucket,
                COUNT(*) as message_count,
                COUNT(DISTINCT sender) as unique_senders,
                COUNT(DISTINCT receiver) as unique_receivers,
                COUNT(DISTINCT message_type) as message_types,
                AVG(CASE WHEN metadata->>'priority' IS NOT NULL
                    THEN (metadata->>'priority')::int ELSE 0 END) as avg_priority
            FROM a2a.communications
            WHERE timestamp >= NOW() - INTERVAL '7 days'
            GROUP BY time_bucket
            ORDER BY time_bucket DESC
        """

        try:
            self.cursor.execute(sql)
            time_series = self.cursor.fetchall()

            # トレンド分析
            if len(time_series) > 1:
                counts = [row["message_count"] for row in time_series]
                trend = "increasing" if counts[0] > counts[-1] else "decreasing"

                # 異常なスパイクの検出
                mean_count = np.mean(counts)
                std_count = np.std(counts)
                spikes = []

                for row in time_series:
                    if abs(row["message_count"] - mean_count) > 2 * std_count:
                        spikes.append(
                            {
                                "time": row["time_bucket"],
                                "count": row["message_count"],
                                "deviation": (row["message_count"] - mean_count) / std_count,
                            }
                        )

                return {
                    "time_series": [dict(row) for row in time_series],
                    "trend": trend,
                    "spikes": spikes,
                    "statistics": {
                        "mean_messages": mean_count,
                        "std_messages": std_count,
                        "total_periods": len(time_series),
                    },
                }

            return {"time_series": [dict(row) for row in time_series]}

        except Exception as e:
            logger.error(f"Temporal analysis failed: {e}")
            return {}

    def execute_analysis(self, query: SemanticQuery) -> AnalysisResult:
        """統合分析の実行"""
        start_time = datetime.now()

        results = []
        insights = {}

        try:
            if query.query_type == AnalysisType.SIMILARITY_SEARCH:
                results = self.semantic_search(query)
                insights["similar_count"] = len(results)
                insights["avg_similarity"] = np.mean([r["similarity"] for r in results]) if results else 0

            elif query.query_type == AnalysisType.ANOMALY_DETECTION:
                results = self.detect_anomalies(query)
                insights["anomaly_count"] = len(results)
                insights["severity_distribution"] = {}
                for r in results:
                    severity = r.get("severity", "unknown")
                    insights["severity_distribution"][severity] = insights["severity_distribution"].get(severity, 0) + 1

            elif query.query_type == AnalysisType.PATTERN_MATCHING:
                results = self.find_communication_patterns(query.query_text, query.limit)
                insights["pattern_count"] = len(results)
                insights["total_occurrences"] = sum(r["occurrence_count"] for r in results)

            elif query.query_type == AnalysisType.AGENT_BEHAVIOR:
                agent_name = query.filters.get("agent") if query.filters else None
                if agent_name:
                    agent_analysis = self.analyze_agent_behavior(agent_name, query.time_window)
                    results = [agent_analysis]
                    insights = agent_analysis.get("communication_stats", {})

            elif query.query_type == AnalysisType.TEMPORAL_ANALYSIS:
                temporal_data = self.temporal_analysis()
                results = temporal_data.get("time_series", [])
                insights = temporal_data.get("statistics", {})
                insights["trend"] = temporal_data.get("trend")
                insights["spike_count"] = len(temporal_data.get("spikes", []))

            # パフォーマンスメトリクス
            end_time = datetime.now()
            performance_metrics = {
                "query_time_ms": (end_time - start_time).total_seconds() * 1000,
                "result_count": len(results),
                "cache_hit": cache_key in self.cache if "cache_key" in locals() else False,
            }

            return AnalysisResult(
                query=query,
                results=results,
                insights=insights,
                performance_metrics=performance_metrics,
                timestamp=end_time,
            )

        except Exception as e:
            logger.error(f"Analysis execution failed: {e}")
            return AnalysisResult(
                query=query,
                results=[],
                insights={"error": str(e)},
                performance_metrics={"error": True},
                timestamp=datetime.now(),
            )

    def close(self):
        """接続のクローズ"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()


def demo_analysis():
    """デモ分析の実行"""
    print("🔍 pgvector A2A Semantic Analysis Demo")
    print("=" * 60)

    analyzer = PgVectorA2AAnalyzer()

    try:
        # 接続
        analyzer.connect()
        analyzer.setup_openai()

        # 1. 類似通信検索
        print("\n1. Similarity Search Demo")
        print("-" * 40)

        similarity_query = SemanticQuery(
            query_text="system overload error critical",
            query_type=AnalysisType.SIMILARITY_SEARCH,
            limit=5,
            threshold=0.7,
        )

        result = analyzer.execute_analysis(similarity_query)
        print(f"Found {len(result.results)} similar communications")
        print(f"Average similarity: {result.insights.get('avg_similarity', 0):.3f}")
        print(f"Query time: {result.performance_metrics['query_time_ms']:.2f}ms")

        # 2. 異常検出
        print("\n2. Anomaly Detection Demo")
        print("-" * 40)

        anomaly_query = SemanticQuery(
            query_text="unusual system behavior",
            query_type=AnalysisType.ANOMALY_DETECTION,
            limit=10,
            time_window=timedelta(hours=24),
        )

        result = analyzer.execute_analysis(anomaly_query)
        print(f"Detected {result.insights.get('anomaly_count', 0)} anomalies")
        print(f"Severity distribution: {result.insights.get('severity_distribution', {})}")

        # 3. エージェント行動分析
        print("\n3. Agent Behavior Analysis Demo")
        print("-" * 40)

        # まずエージェントリストを取得
        analyzer.cursor.execute("SELECT DISTINCT agent_name FROM a2a.agents LIMIT 1;")
        agent = analyzer.cursor.fetchone()

        if agent:
            agent_query = SemanticQuery(
                query_text="", query_type=AnalysisType.AGENT_BEHAVIOR, filters={"agent": agent["agent_name"]}
            )

            result = analyzer.execute_analysis(agent_query)
            if result.results:
                stats = result.results[0].get("communication_stats", {})
                print(f"Agent: {agent['agent_name']}")
                print(f"Total messages: {stats.get('total_messages', 0)}")
                print(f"Unique interactions: {stats.get('unique_interactions', 0)}")

        # 4. 時系列分析
        print("\n4. Temporal Analysis Demo")
        print("-" * 40)

        temporal_query = SemanticQuery(query_text="", query_type=AnalysisType.TEMPORAL_ANALYSIS)

        result = analyzer.execute_analysis(temporal_query)
        print(f"Trend: {result.insights.get('trend', 'unknown')}")
        print(f"Spike count: {result.insights.get('spike_count', 0)}")
        print(f"Mean messages per period: {result.insights.get('mean_messages', 0):.2f}")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")

    finally:
        analyzer.close()


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description="pgvector A2A Semantic Analysis")
    parser.add_argument("--demo", action="store_true", help="Run demo analysis")
    parser.add_argument("--query", type=str, help="Semantic search query")
    parser.add_argument(
        "--type", choices=[t.value for t in AnalysisType], default="similarity_search", help="Analysis type"
    )
    parser.add_argument("--limit", type=int, default=10, help="Result limit")
    parser.add_argument("--agent", type=str, help="Agent name for behavior analysis")

    args = parser.parse_args()

    if args.demo:
        demo_analysis()
    else:
        analyzer = PgVectorA2AAnalyzer()

        try:
            analyzer.connect()
            analyzer.setup_openai()

            # クエリ実行
            query = SemanticQuery(query_text=args.query or "", query_type=AnalysisType(args.type), limit=args.limit)

            if args.agent:
                query.filters = {"agent": args.agent}

            result = analyzer.execute_analysis(query)

            # 結果表示
            print("\n📊 Analysis Results")
            print("=" * 60)
            print(f"Query type: {result.query.query_type.value}")
            print(f"Results found: {len(result.results)}")
            print(f"Query time: {result.performance_metrics['query_time_ms']:.2f}ms")

            print("\n💡 Insights:")
            for key, value in result.insights.items():
                print(f"  {key}: {value}")

            if result.results:
                print("\n🔍 Top Results:")
                for i, res in enumerate(result.results[:5], 1):
                    if "sender" in res:
                        print(f"\n{i}. {res.get('sender')} → {res.get('receiver')}")
                        print(f"   Type: {res.get('message_type')}")
                        if "similarity" in res:
                            print(f"   Similarity: {res.get('similarity', 0):.3f}")
                    else:
                        print(f"\n{i}. {res}")

        except Exception as e:
            print(f"\n❌ Analysis failed: {e}")

        finally:
            analyzer.close()


if __name__ == "__main__":
    main()
