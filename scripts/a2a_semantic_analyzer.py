#!/usr/bin/env python3
"""
A2A通信セマンティック分析システム
pgvectorを活用してA2A通信ログを意味的に分析・検索
"""

import os
import sys
import json
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import sqlite3

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# A2A分析用に必要最小限のライブラリのみ使用
try:
    from libs.grimoire_database import GrimoireDatabase
    from libs.grimoire_vector_search import GrimoireVectorSearch
    GRIMOIRE_AVAILABLE = True
except ImportError:
    GRIMOIRE_AVAILABLE = False

class A2ASemanticAnalyzer:
    """A2A通信のセマンティック分析"""
    
    def __init__(self):
        # 実際のデータベースパスを確認
        self.a2a_db_path = PROJECT_ROOT / "db" / "a2a_monitoring.db"
        if not self.a2a_db_path.exists():
            self.a2a_db_path = PROJECT_ROOT / "logs" / "a2a_monitoring.db"
        self.embedding_cache = {}
        
        # Grimoire統合が利用可能な場合のみ初期化
        if GRIMOIRE_AVAILABLE:
            try:
                self.db = GrimoireDatabase()
                self.vector_search = GrimoireVectorSearch()
                self.grimoire_enabled = True
            except Exception:
                self.grimoire_enabled = False
        else:
            self.grimoire_enabled = False
        
    def analyze_communication_patterns(self) -> Dict[str, Any]:
        """A2A通信パターンの分析"""
        print("📊 A2A通信パターンを分析中...")
        
        # SQLiteからA2A通信ログを取得
        conn = sqlite3.connect(self.a2a_db_path)
        cursor = conn.cursor()
        
        # 最近の通信を取得
        query = """
        SELECT source_agent, target_agent, message_type, metadata, 
               response_time, timestamp
        FROM a2a_communications
        ORDER BY timestamp DESC
        LIMIT 1000
        """
        
        cursor.execute(query)
        communications = cursor.fetchall()
        conn.close()
        
        # 通信パターンを分析
        patterns = self._extract_patterns(communications)
        
        # パターンをベクトル化して類似性分析
        vectorized_patterns = self._vectorize_patterns(patterns)
        
        # クラスタリング
        clusters = self._cluster_patterns(vectorized_patterns)
        
        return {
            "total_communications": len(communications),
            "unique_patterns": len(patterns),
            "clusters": clusters,
            "top_patterns": self._get_top_patterns(patterns),
            "anomalies": self._detect_anomalies(vectorized_patterns)
        }
    
    def _extract_patterns(self, communications: List[Tuple]) -> List[Dict]:
        """通信からパターンを抽出"""
        patterns = []
        
        for comm in communications:
            source, target, msg_type, metadata, response_time, timestamp = comm
            
            # メタデータをパース
            try:
                meta = json.loads(metadata) if metadata else {}
            except:
                meta = {}
            
            pattern = {
                "flow": f"{source} -> {target}",
                "type": msg_type,
                "response_time": response_time,
                "timestamp": timestamp,
                "context": meta.get("message", ""),
                "session_id": meta.get("session_id", "")
            }
            patterns.append(pattern)
        
        return patterns
    
    def _vectorize_patterns(self, patterns: List[Dict]) -> List[np.ndarray]:
        """パターンをベクトル化"""
        print("🔄 パターンをベクトル化中...")
        vectors = []
        
        for pattern in patterns:
            # パターンの説明文を生成
            description = f"{pattern['flow']} {pattern['type']} {pattern['context']}"
            
            # キャッシュチェック
            if description in self.embedding_cache:
                vector = self.embedding_cache[description]
            else:
                # ベクトル生成 (Grimoire使用可能な場合のみ)
                if self.grimoire_enabled:
                    try:
                        vector = self.vector_search.generate_embedding(description)
                    except (AttributeError, Exception):
                        # Grimoireの埋め込み生成に失敗した場合は簡単な特徴ベクトルを使用
                        vector = self._generate_simple_embedding(description)
                    if vector is not None:
                        self.embedding_cache[description] = vector
                else:
                    # Grimoireが利用できない場合は簡単な特徴ベクトルを生成
                    vector = self._generate_simple_embedding(description)
                    if vector is not None:
                        self.embedding_cache[description] = vector
            
            if vector is not None:
                vectors.append(vector)
        
        return vectors
    
    def _cluster_patterns(self, vectors: List[np.ndarray]) -> List[Dict]:
        """パターンをクラスタリング"""
        if not vectors:
            return []
        
        from sklearn.cluster import DBSCAN
        
        # DBSCANでクラスタリング
        clustering = DBSCAN(eps=0.3, min_samples=5, metric='cosine')
        labels = clustering.fit_predict(vectors)
        
        # クラスタ情報を集計
        clusters = {}
        for i, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(i)
        
        return [
            {
                "cluster_id": label,
                "size": len(indices),
                "is_anomaly": label == -1
            }
            for label, indices in clusters.items()
        ]
    
    def _get_top_patterns(self, patterns: List[Dict], top_n: int = 10) -> List[Dict]:
        """頻出パターンを取得"""
        from collections import Counter
        
        # フローごとにカウント
        flow_counts = Counter(p["flow"] for p in patterns)
        type_counts = Counter(p["type"] for p in patterns)
        
        return {
            "top_flows": flow_counts.most_common(top_n),
            "top_types": type_counts.most_common(top_n)
        }
    
    def _detect_anomalies(self, vectors: List[np.ndarray]) -> List[Dict]:
        """異常パターンを検出"""
        if len(vectors) < 10:
            return []
        
        from sklearn.ensemble import IsolationForest
        
        # Isolation Forestで異常検知
        clf = IsolationForest(contamination=0.1, random_state=42)
        predictions = clf.fit_predict(vectors)
        
        anomalies = []
        for i, pred in enumerate(predictions):
            if pred == -1:  # 異常
                anomalies.append({
                    "index": i,
                    "anomaly_score": clf.score_samples([vectors[i]])[0]
                })
        
        return sorted(anomalies, key=lambda x: x["anomaly_score"])[:10]
    
    def semantic_search_errors(self, query: str) -> List[Dict]:
        """エラーパターンのセマンティック検索"""
        print(f"🔍 エラーパターンを検索中: {query}")
        
        # クエリをベクトル化
        if self.grimoire_enabled:
            try:
                query_vector = self.vector_search.generate_embedding(query)
            except (AttributeError, Exception):
                query_vector = self._generate_simple_embedding(query)
        else:
            query_vector = self._generate_simple_embedding(query)
        
        if query_vector is None:
            return []
        
        # エラーログから類似パターンを検索
        conn = sqlite3.connect(self.a2a_db_path)
        cursor = conn.cursor()
        
        # エラーのみ取得
        query_sql = """
        SELECT id, error_type, error_message, timestamp
        FROM a2a_errors
        ORDER BY timestamp DESC
        LIMIT 100
        """
        
        cursor.execute(query_sql)
        errors = cursor.fetchall()
        conn.close()
        
        # 各エラーとの類似度を計算
        similar_errors = []
        for error in errors:
            error_id, err_type, msg, timestamp = error
            
            # エラーの説明文
            error_desc = f"{err_type}: {msg}"
            if self.grimoire_enabled:
                try:
                    error_vector = self.vector_search.generate_embedding(error_desc)
                except (AttributeError, Exception):
                    error_vector = self._generate_simple_embedding(error_desc)
            else:
                error_vector = self._generate_simple_embedding(error_desc)
            
            if error_vector is not None:
                # コサイン類似度計算
                similarity = np.dot(query_vector, error_vector) / (
                    np.linalg.norm(query_vector) * np.linalg.norm(error_vector)
                )
                
                if similarity > 0.7:  # 閾値
                    similar_errors.append({
                        "id": error_id,
                        "error_type": err_type,
                        "message": msg,
                        "similarity": float(similarity),
                        "timestamp": timestamp
                    })
        
        return sorted(similar_errors, key=lambda x: x["similarity"], reverse=True)
    
    def auto_categorize_communications(self) -> Dict[str, List]:
        """通信を自動的にカテゴリ分類"""
        print("🏷️ 通信を自動カテゴリ分類中...")
        
        # 事前定義カテゴリ
        categories = {
            "knowledge_query": "知識照会・学習",
            "task_coordination": "タスク調整・割り当て",
            "error_handling": "エラー処理・復旧",
            "status_update": "状態更新・報告",
            "urgent_action": "緊急対応・アラート"
        }
        
        # カテゴリごとの代表ベクトルを生成
        category_vectors = {}
        for cat_id, cat_desc in categories.items():
            if self.grimoire_enabled:
                try:
                    vector = self.vector_search.generate_embedding(cat_desc)
                except (AttributeError, Exception):
                    vector = self._generate_simple_embedding(cat_desc)
            else:
                vector = self._generate_simple_embedding(cat_desc)
            if vector is not None:
                category_vectors[cat_id] = vector
        
        # 通信をカテゴリに分類
        categorized = {cat_id: [] for cat_id in categories}
        
        # 最近の通信を取得して分類
        patterns = self._get_recent_patterns(limit=500)
        
        for pattern in patterns:
            # パターンをベクトル化
            pattern_desc = f"{pattern['flow']} {pattern['type']} {pattern.get('context', '')}"
            if self.grimoire_enabled:
                try:
                    pattern_vector = self.vector_search.generate_embedding(pattern_desc)
                except (AttributeError, Exception):
                    pattern_vector = self._generate_simple_embedding(pattern_desc)
            else:
                pattern_vector = self._generate_simple_embedding(pattern_desc)
            
            if pattern_vector is not None:
                # 最も近いカテゴリを見つける
                best_category = None
                best_similarity = -1
                
                for cat_id, cat_vector in category_vectors.items():
                    similarity = np.dot(pattern_vector, cat_vector) / (
                        np.linalg.norm(pattern_vector) * np.linalg.norm(cat_vector)
                    )
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_category = cat_id
                
                if best_category and best_similarity > 0.6:
                    categorized[best_category].append({
                        "pattern": pattern,
                        "similarity": float(best_similarity)
                    })
        
        # 統計情報を追加
        stats = {}
        for cat_id, items in categorized.items():
            stats[cat_id] = {
                "name": categories[cat_id],
                "count": len(items),
                "percentage": len(items) / len(patterns) * 100 if patterns else 0
            }
        
        return {
            "categories": categorized,
            "statistics": stats
        }
    
    def _get_recent_patterns(self, limit: int = 100) -> List[Dict]:
        """最近の通信パターンを取得"""
        conn = sqlite3.connect(self.a2a_db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT source_agent, target_agent, message_type, metadata
        FROM a2a_communications
        ORDER BY timestamp DESC
        LIMIT ?
        """
        
        cursor.execute(query, (limit,))
        results = cursor.fetchall()
        conn.close()
        
        patterns = []
        for row in results:
            source, target, msg_type, metadata = row
            try:
                meta = json.loads(metadata) if metadata else {}
            except:
                meta = {}
            
            patterns.append({
                "flow": f"{source} -> {target}",
                "type": msg_type,
                "context": meta.get("message", "")
            })
        
        return patterns
    
    def _generate_simple_embedding(self, text: str) -> Optional[np.ndarray]:
        """簡単な特徴ベクトルを生成（Grimoire利用不可時）"""
        if not text:
            return None
        
        # 簡単な特徴抽出
        words = text.lower().split()
        
        # 基本的な特徴量（次元数: 50）
        features = np.zeros(50)
        
        # 単語の特徴
        features[0] = len(words)  # 単語数
        features[1] = len(text)   # 文字数
        features[2] = text.count('error')  # エラー関連
        features[3] = text.count('success')  # 成功関連
        features[4] = text.count('timeout')  # タイムアウト関連
        features[5] = text.count('connection')  # 接続関連
        features[6] = text.count('request')  # リクエスト関連
        features[7] = text.count('response')  # レスポンス関連
        features[8] = text.count('sage')  # 賢者関連
        features[9] = text.count('elder')  # エルダー関連
        
        # 矢印の方向（通信フロー）
        features[10] = text.count('->')  # 前向き通信
        features[11] = text.count('<-')  # 後向き通信
        
        # 通信タイプ
        features[12] = text.count('knowledge')  # 知識関連
        features[13] = text.count('task')  # タスク関連
        features[14] = text.count('incident')  # インシデント関連
        features[15] = text.count('rag')  # RAG関連
        
        # 単語のハッシュ特徴（残り35次元）
        for i, word in enumerate(words[:35]):
            features[15 + i] = hash(word) % 100 / 100.0
        
        # 正規化
        norm = np.linalg.norm(features)
        if norm > 0:
            features = features / norm
        
        return features
    
    def generate_insights_report(self) -> Dict:
        """総合的な洞察レポートを生成"""
        print("📊 A2A通信の総合分析レポートを生成中...")
        
        # 各種分析を実行
        pattern_analysis = self.analyze_communication_patterns()
        categories = self.auto_categorize_communications()
        
        # エラーパターン分析
        error_patterns = self.semantic_search_errors("connection error timeout")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_communications": pattern_analysis["total_communications"],
                "unique_patterns": pattern_analysis["unique_patterns"],
                "anomaly_count": len(pattern_analysis["anomalies"]),
                "error_patterns_found": len(error_patterns)
            },
            "pattern_analysis": pattern_analysis,
            "categorization": categories["statistics"],
            "top_error_patterns": error_patterns[:5],
            "recommendations": self._generate_recommendations(
                pattern_analysis, categories, error_patterns
            )
        }
        
        return report
    
    def _generate_recommendations(self, patterns: Dict, categories: Dict, errors: List) -> List[str]:
        """分析結果から推奨事項を生成"""
        recommendations = []
        
        # 異常パターンが多い場合
        if len(patterns["anomalies"]) > 5:
            recommendations.append(
                "⚠️ 異常な通信パターンが検出されました。システム監視を強化してください。"
            )
        
        # 特定カテゴリに偏りがある場合
        stats = categories["statistics"]
        for cat_id, stat in stats.items():
            if stat["percentage"] > 40:
                recommendations.append(
                    f"📊 {stat['name']}の通信が{stat['percentage']:.1f}%を占めています。"
                    f"負荷分散を検討してください。"
                )
        
        # エラーパターンが多い場合
        if len(errors) > 10:
            recommendations.append(
                "🔧 類似エラーパターンが多数検出されました。根本原因の分析が必要です。"
            )
        
        return recommendations

def main():
    """メイン処理"""
    analyzer = A2ASemanticAnalyzer()
    
    print("🚀 A2A通信セマンティック分析システム")
    print("=" * 60)
    
    # 総合レポート生成
    report = analyzer.generate_insights_report()
    
    # レポート表示
    print("\n📊 分析結果サマリー")
    print("-" * 40)
    print(f"総通信数: {report['summary']['total_communications']:,}")
    print(f"ユニークパターン: {report['summary']['unique_patterns']}")
    print(f"異常パターン: {report['summary']['anomaly_count']}")
    print(f"エラーパターン: {report['summary']['error_patterns_found']}")
    
    print("\n📈 通信カテゴリ分布")
    print("-" * 40)
    for cat_id, stat in report['categorization'].items():
        print(f"{stat['name']}: {stat['count']}件 ({stat['percentage']:.1f}%)")
    
    print("\n💡 推奨事項")
    print("-" * 40)
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"{i}. {rec}")
    
    # レポート保存
    report_file = PROJECT_ROOT / "logs" / f"a2a_semantic_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 詳細レポートを保存しました: {report_file}")
    
    # インタラクティブ検索モード
    print("\n🔍 セマンティック検索モード（'quit'で終了）")
    while True:
        query = input("\n検索クエリを入力 > ")
        if query.lower() == 'quit':
            break
        
        results = analyzer.semantic_search_errors(query)
        if results:
            print(f"\n見つかった類似パターン: {len(results)}件")
            for i, result in enumerate(results[:5], 1):
                print(f"{i}. {result['flow']} - {result['error_type']} (類似度: {result['similarity']:.2f})")
        else:
            print("類似パターンが見つかりませんでした。")

if __name__ == "__main__":
    main()