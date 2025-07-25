#!/usr/bin/env python3
"""
A2A通信異常パターン詳細分析システム
検出された10件の異常パターンを詳細に分析し、対応策を提案
"""

import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class A2AAnomalyAnalyzer:
    """A2A通信異常パターン分析システム"""

    def __init__(self):
        # データベースパスの確認
        self.a2a_db_path = PROJECT_ROOT / "db" / "a2a_monitoring.db"
        if not self.a2a_db_path.exists():
            self.a2a_db_path = PROJECT_ROOT / "logs" / "a2a_monitoring.db"

        self.analysis_cache = {}

    def analyze_anomaly_patterns(self) -> Dict[str, Any]:
        """異常パターンの詳細分析"""
        print("🔍 異常パターン10件の詳細分析を開始...")

        # データベースから通信データを取得
        conn = sqlite3connect(self.a2a_db_path)
        cursor = conn.cursor()

        # 全通信データを取得
        query = """
        SELECT id, timestamp, source_agent, target_agent, message_type,
               priority, payload_size, response_time, status, error_message, metadata
        FROM a2a_communications
        ORDER BY timestamp DESC
        """

        cursor.execute(query)
        communications = cursor.fetchall()
        conn.close()

        if not communications:
            return {"error": "通信データが見つかりません"}

        # 通信データを特徴ベクトルに変換
        features = self._extract_features(communications)

        # 異常検知を実行
        anomalies = self._detect_anomalies_detailed(features, communications)

        # 異常パターンの分析
        anomaly_analysis = self._analyze_anomaly_characteristics(anomalies)

        # 対応策の提案
        recommendations = self._generate_recommendations(anomaly_analysis)

        return {
            "timestamp": datetime.now().isoformat(),
            "total_communications": len(communications),
            "anomalies_detected": len(anomalies),
            "anomaly_details": anomalies,
            "pattern_analysis": anomaly_analysis,
            "recommendations": recommendations,
            "severity_assessment": self._assess_severity(anomalies),
        }

    def _extract_features(self, communications: List[tuple]) -> np.ndarray:
        """通信データから特徴ベクトルを抽出"""
        features = []

        for comm in communications:
            (
                comm_id,
                timestamp,
                source,
                target,
                msg_type,
                priority,
                payload_size,
                response_time,
                status,
                error_msg,
                metadata,
            ) = comm

            # 基本特徴量（20次元）
            feature_vector = np.zeros(20)

            # 時間的特徴
            dt = datetime.fromisoformat(timestamp)
            feature_vector[0] = dt.hour  # 時間
            feature_vector[1] = dt.weekday()  # 曜日

            # 通信特徴
            feature_vector[2] = len(source) if source else 0
            feature_vector[3] = len(target) if target else 0
            feature_vector[4] = len(msg_type) if msg_type else 0
            feature_vector[5] = priority if priority else 0
            feature_vector[6] = payload_size if payload_size else 0
            feature_vector[7] = response_time if response_time else 0

            # ステータス特徴
            feature_vector[8] = 1 if status == "success" else 0
            feature_vector[9] = 1 if status == "error" else 0
            feature_vector[10] = len(error_msg) if error_msg else 0

            # エージェント特徴
            feature_vector[11] = hash(source) % 100 / 100.0 if source else 0
            feature_vector[12] = hash(target) % 100 / 100.0 if target else 0
            feature_vector[13] = hash(msg_type) % 100 / 100.0 if msg_type else 0

            # メタデータ特徴
            try:
                meta = json.loads(metadata) if metadata else {}
                feature_vector[14] = len(str(meta))
                feature_vector[15] = 1 if "error" in str(meta).lower() else 0
                feature_vector[16] = 1 if "timeout" in str(meta).lower() else 0
                feature_vector[17] = 1 if "retry" in str(meta).lower() else 0
            except:
                pass

            # 追加統計特徴
            feature_vector[18] = (
                np.log1p(response_time) if response_time and response_time > 0 else 0
            )
            feature_vector[19] = 1 if payload_size and payload_size > 10000 else 0

            features.append(feature_vector)

        return np.array(features)

    def _detect_anomalies_detailed(
        self, features: np.ndarray, communications: List[tuple]
    ) -> List[Dict]:
        """詳細な異常検知"""
        if len(features) < 10:
            return []

        try:
            from sklearn.ensemble import IsolationForest
            from sklearn.preprocessing import StandardScaler

            # 特徴量を標準化
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)

            # Isolation Forestで異常検知
            clf = IsolationForest(contamination=0.05, random_state=42)
            predictions = clf.fit_predict(features_scaled)
            anomaly_scores = clf.score_samples(features_scaled)

            # 異常データを抽出
            anomalies = []
            for i, (pred, score) in enumerate(zip(predictions, anomaly_scores)):
                if pred == -1:  # 異常
                    comm = communications[i]
                    anomaly = {
                        "index": i,
                        "anomaly_score": float(score),
                        "communication_id": comm[0],
                        "timestamp": comm[1],
                        "source_agent": comm[2],
                        "target_agent": comm[3],
                        "message_type": comm[4],
                        "priority": comm[5],
                        "payload_size": comm[6],
                        "response_time": comm[7],
                        "status": comm[8],
                        "error_message": comm[9],
                        "metadata": comm[10],
                        "feature_vector": features[i].tolist(),
                    }
                    anomalies.append(anomaly)

            # 異常スコアでソート
            anomalies.sort(key=lambda x: x["anomaly_score"])

            return anomalies[:10]  # 上位10件

        except ImportError:
            print("⚠️ sklearn未インストール - 簡単な統計的異常検知を使用")
            return self._simple_anomaly_detection(features, communications)

    def _simple_anomaly_detection(
        self, features: np.ndarray, communications: List[tuple]
    ) -> List[Dict]:
        """簡単な統計的異常検知"""
        anomalies = []

        # 各特徴量の統計
        means = np.mean(features, axis=0)
        stds = np.std(features, axis=0)

        for i, (feature_vec, comm) in enumerate(zip(features, communications)):
            # Z-scoreベースの異常検知
            z_scores = np.abs((feature_vec - means) / (stds + 1e-8))
            max_z_score = np.max(z_scores)

            if max_z_score > 3.0:  # 異常閾値
                anomaly = {
                    "index": i,
                    "anomaly_score": -float(max_z_score),  # 負の値で統一
                    "communication_id": comm[0],
                    "timestamp": comm[1],
                    "source_agent": comm[2],
                    "target_agent": comm[3],
                    "message_type": comm[4],
                    "priority": comm[5],
                    "payload_size": comm[6],
                    "response_time": comm[7],
                    "status": comm[8],
                    "error_message": comm[9],
                    "metadata": comm[10],
                    "max_z_score": float(max_z_score),
                    "anomalous_features": [
                        j for j, z in enumerate(z_scores) if z > 3.0
                    ],
                }
                anomalies.append(anomaly)

        # 異常スコアでソート
        anomalies.sort(key=lambda x: x["anomaly_score"])

        return anomalies[:10]  # 上位10件

    def _analyze_anomaly_characteristics(self, anomalies: List[Dict]) -> Dict[str, Any]:
        """異常パターンの特徴分析"""
        if not anomalies:
            return {"error": "分析する異常パターンがありません"}

        analysis = {
            "temporal_patterns": self._analyze_temporal_patterns(anomalies),
            "agent_patterns": self._analyze_agent_patterns(anomalies),
            "performance_patterns": self._analyze_performance_patterns(anomalies),
            "error_patterns": self._analyze_error_patterns(anomalies),
            "severity_distribution": self._analyze_severity_distribution(anomalies),
        }

        return analysis

    def _analyze_temporal_patterns(self, anomalies: List[Dict]) -> Dict[str, Any]:
        """時間的パターンの分析"""
        timestamps = [datetime.fromisoformat(a["timestamp"]) for a in anomalies]

        hours = [dt.hour for dt in timestamps]
        weekdays = [dt.weekday() for dt in timestamps]

        return {
            "peak_hours": Counter(hours).most_common(3),
            "peak_weekdays": Counter(weekdays).most_common(3),
            "time_clustering": self._check_time_clustering(timestamps),
        }

    def _analyze_agent_patterns(self, anomalies: List[Dict]) -> Dict[str, Any]:
        """エージェントパターンの分析"""
        sources = [a["source_agent"] for a in anomalies if a["source_agent"]]
        targets = [a["target_agent"] for a in anomalies if a["target_agent"]]
        message_types = [a["message_type"] for a in anomalies if a["message_type"]]

        return {
            "problematic_sources": Counter(sources).most_common(5),
            "problematic_targets": Counter(targets).most_common(5),
            "problematic_message_types": Counter(message_types).most_common(5),
            "communication_flows": Counter(
                [
                    f"{a['source_agent']} -> {a['target_agent']}"
                    for a in anomalies
                    if a["source_agent"] and a["target_agent"]
                ]
            ).most_common(5),
        }

    def _analyze_performance_patterns(self, anomalies: List[Dict]) -> Dict[str, Any]:
        """パフォーマンスパターンの分析"""
        response_times = [a["response_time"] for a in anomalies if a["response_time"]]
        payload_sizes = [a["payload_size"] for a in anomalies if a["payload_size"]]

        return {
            "response_time_stats": {
                "mean": np.mean(response_times) if response_times else 0,
                "median": np.median(response_times) if response_times else 0,
                "max": np.max(response_times) if response_times else 0,
                "min": np.min(response_times) if response_times else 0,
            },
            "payload_size_stats": {
                "mean": np.mean(payload_sizes) if payload_sizes else 0,
                "median": np.median(payload_sizes) if payload_sizes else 0,
                "max": np.max(payload_sizes) if payload_sizes else 0,
                "min": np.min(payload_sizes) if payload_sizes else 0,
            },
            "slow_responses": len([rt for rt in response_times if rt > 1.0]),
            "large_payloads": len([ps for ps in payload_sizes if ps > 10000]),
        }

    def _analyze_error_patterns(self, anomalies: List[Dict]) -> Dict[str, Any]:
        """エラーパターンの分析"""
        error_statuses = [a["status"] for a in anomalies]
        error_messages = [a["error_message"] for a in anomalies if a["error_message"]]

        return {
            "status_distribution": Counter(error_statuses),
            "common_error_keywords": self._extract_error_keywords(error_messages),
            "error_rate": (
                len([s for s in error_statuses if s == "error"]) / len(error_statuses)
                if error_statuses
                else 0
            ),
        }

    def _extract_error_keywords(self, error_messages: List[str]) -> List[tuple]:
        """エラーメッセージからキーワードを抽出"""
        if not error_messages:
            return []

        keywords = []
        for msg in error_messages:
            words = msg.lower().split()
            keywords.extend(words)

        return Counter(keywords).most_common(10)

    def _analyze_severity_distribution(self, anomalies: List[Dict]) -> Dict[str, Any]:
        """重要度分布の分析"""
        priorities = [a["priority"] for a in anomalies if a["priority"]]
        anomaly_scores = [a["anomaly_score"] for a in anomalies]

        return {
            "priority_distribution": Counter(priorities),
            "anomaly_score_stats": {
                "mean": np.mean(anomaly_scores),
                "median": np.median(anomaly_scores),
                "min": np.min(anomaly_scores),
                "max": np.max(anomaly_scores),
            },
        }

    def _check_time_clustering(self, timestamps: List[datetime]) -> bool:
        """時間クラスタリングをチェック"""
        if len(timestamps) < 2:
            return False

        # 時間間隔を計算
        intervals = []
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i - 1]).total_seconds()
            intervals.append(interval)

        # 短い間隔（1分以内）が多い場合はクラスタリング
        short_intervals = [i for i in intervals if i < 60]
        return len(short_intervals) > len(intervals) * 0.5

    def _assess_severity(self, anomalies: List[Dict]) -> Dict[str, Any]:
        """重要度評価"""
        if not anomalies:
            return {"level": "none", "score": 0}

        severity_factors = {
            "error_rate": 0,
            "response_time_issues": 0,
            "agent_concentration": 0,
            "time_clustering": 0,
        }

        # エラー率
        error_count = len([a for a in anomalies if a["status"] == "error"])
        severity_factors["error_rate"] = error_count / len(anomalies)

        # 応答時間問題
        slow_responses = len(
            [a for a in anomalies if a["response_time"] and a["response_time"] > 1.0]
        )
        severity_factors["response_time_issues"] = slow_responses / len(anomalies)

        # エージェント集中度
        sources = [a["source_agent"] for a in anomalies if a["source_agent"]]
        if sources:
            most_common_source_count = Counter(sources).most_common(1)[0][1]
            severity_factors["agent_concentration"] = most_common_source_count / len(
                anomalies
            )

        # 時間クラスタリング
        timestamps = [datetime.fromisoformat(a["timestamp"]) for a in anomalies]
        severity_factors["time_clustering"] = (
            1.0 if self._check_time_clustering(timestamps) else 0.0
        )

        # 総合スコア
        total_score = sum(severity_factors.values()) / len(severity_factors)

        if total_score > 0.7:
            level = "critical"
        elif total_score > 0.5:
            level = "high"
        elif total_score > 0.3:
            level = "medium"
        else:
            level = "low"

        return {"level": level, "score": total_score, "factors": severity_factors}

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """対応策の提案"""
        recommendations = []

        if "error" in analysis:
            return ["異常パターンの分析データが不足しています"]

        # 時間的パターンに基づく推奨
        temporal = analysis.get("temporal_patterns", {})
        if temporal.get("time_clustering"):
            recommendations.append(
                "🕐 短時間での異常集中が検出されました。システム負荷の分散を検討してください。"
            )

        # エージェントパターンに基づく推奨
        agent = analysis.get("agent_patterns", {})
        if agent.get("problematic_sources"):
            top_source = agent["problematic_sources"][0]
            recommendations.append(
                f"🤖 エージェント '{top_source[0]}' が異常の{top_source[1]}件に関与しています。監視を強化してください。"
            )

        # パフォーマンスパターンに基づく推奨
        performance = analysis.get("performance_patterns", {})
        if performance.get("slow_responses", 0) > 5:
            recommendations.append(
                "⏱️ 応答時間の遅延が多発しています。パフォーマンスチューニングを実施してください。"
            )

        # エラーパターンに基づく推奨
        error = analysis.get("error_patterns", {})
        if error.get("error_rate", 0) > 0.5:
            recommendations.append(
                "🚨 エラー率が50%を超えています。緊急の対応が必要です。"
            )

        if not recommendations:
            recommendations.append(
                "✅ 異常パターンは検出されましたが、重大な問題は見つかりませんでした。継続的な監視を推奨します。"
            )

        return recommendations


def main():
    """メイン処理"""
    analyzer = A2AAnomalyAnalyzer()

    print("🚀 A2A通信異常パターン詳細分析システム")
    print("=" * 60)

    # 異常パターン分析実行
    analysis_result = analyzer.analyze_anomaly_patterns()

    if "error" in analysis_result:
        print(f"❌ エラー: {analysis_result['error']}")
        return

    # 結果表示
    print("\n📊 分析結果サマリー")
    print("-" * 40)
    print(f"総通信数: {analysis_result['total_communications']:,}")
    print(f"異常パターン検出: {analysis_result['anomalies_detected']}件")
    print(f"重要度レベル: {analysis_result['severity_assessment']['level'].upper()}")
    print(f"重要度スコア: {analysis_result['severity_assessment']['score']:0.3f}")

    # 異常パターンの詳細
    print("\n🔍 異常パターン詳細")
    print("-" * 40)
    for i, anomaly in enumerate(analysis_result["anomaly_details"][:5], 1):
        print(f"{i}. {anomaly['source_agent']} -> {anomaly['target_agent']}")
        print(f"   時刻: {anomaly['timestamp']}")
        print(f"   スコア: {anomaly['anomaly_score']:0.3f}")
        print(f"   ステータス: {anomaly['status']}")
        if anomaly["error_message"]:
            print(f"   エラー: {anomaly['error_message'][:50]}...")
        print()

    # 推奨事項
    print("\n💡 推奨事項")
    print("-" * 40)
    for i, rec in enumerate(analysis_result["recommendations"], 1):
        print(f"{i}. {rec}")

    # 詳細レポート保存
    report_file = (
        PROJECT_ROOT
        / "logs"
        / f"a2a_anomaly_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n💾 詳細レポートを保存しました: {report_file}")


if __name__ == "__main__":
    main()
