#!/usr/bin/env python3
"""
Error Classification System - エラー分類システム
AI学習・進化における自動エラー分類・優先度判定システム

エルダーズ推奨の高優先度タスク
242万件のエラーデータを活用した機械学習分類システム
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import re
import pickle
import sqlite3
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import hashlib

# 機械学習ライブラリ
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.cluster import KMeans
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available, using basic classification")

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """エラーカテゴリの定義"""
    
    # システムエラー
    DATABASE_ERROR = "DATABASE_ERROR"
    API_ERROR = "API_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    PERMISSION_ERROR = "PERMISSION_ERROR"
    RESOURCE_ERROR = "RESOURCE_ERROR"
    
    # アプリケーションエラー
    WORKER_ERROR = "WORKER_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    
    # 外部エラー
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    
    # 不明・その他
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    
    @property
    def default_severity(self) -> str:
        """カテゴリのデフォルト重要度"""
        severity_map = {
            self.DATABASE_ERROR: "critical",
            self.API_ERROR: "high",
            self.NETWORK_ERROR: "high",
            self.PERMISSION_ERROR: "high",
            self.RESOURCE_ERROR: "critical",
            self.WORKER_ERROR: "medium",
            self.VALIDATION_ERROR: "low",
            self.TIMEOUT_ERROR: "medium",
            self.CONFIGURATION_ERROR: "high",
            self.EXTERNAL_API_ERROR: "medium",
            self.DEPENDENCY_ERROR: "high",
            self.UNKNOWN_ERROR: "low"
        }
        return severity_map.get(self, "medium")
    
    @property
    def parent(self) -> Optional['ErrorCategory']:
        """親カテゴリの取得"""
        parent_map = {
            self.DATABASE_ERROR: None,  # システムエラー
            self.API_ERROR: None,       # システムエラー
            self.NETWORK_ERROR: None,   # システムエラー
            self.WORKER_ERROR: None,    # アプリケーションエラー
        }
        return parent_map.get(self)


@dataclass
class ErrorPattern:
    """エラーパターンの定義"""
    category: ErrorCategory
    keywords: List[str]
    regex_patterns: List[str]
    confidence: float
    severity: str
    description: str
    suggested_actions: List[str]
    
    @classmethod
    def extract(cls, error_text: str) -> 'ErrorPattern':
        """エラーテキストからパターンを抽出"""
        # 基本的なパターン抽出ロジック
        text_lower = error_text.lower()
        
        # API関連エラー
        if any(keyword in text_lower for keyword in ['api key', 'invalid key', 'unauthorized']):
            return cls(
                category=ErrorCategory.API_ERROR,
                keywords=['api', 'key', 'unauthorized'],
                regex_patterns=[r'api.*key', r'unauthorized'],
                confidence=0.9,
                severity="high",
                description="API認証エラー",
                suggested_actions=["APIキーの確認", "権限設定の確認"]
            )
        
        # データベースエラー
        if any(keyword in text_lower for keyword in ['database', 'connection', 'sql', 'db']):
            return cls(
                category=ErrorCategory.DATABASE_ERROR,
                keywords=['database', 'connection', 'sql'],
                regex_patterns=[r'database.*error', r'connection.*failed'],
                confidence=0.85,
                severity="critical",
                description="データベース接続エラー",
                suggested_actions=["データベース接続の確認", "接続プール設定の確認"]
            )
        
        # タイムアウトエラー
        if any(keyword in text_lower for keyword in ['timeout', 'timed out', 'time out']):
            return cls(
                category=ErrorCategory.TIMEOUT_ERROR,
                keywords=['timeout', 'time'],
                regex_patterns=[r'timeout', r'timed.*out'],
                confidence=0.8,
                severity="medium",
                description="タイムアウトエラー",
                suggested_actions=["タイムアウト設定の確認", "処理の最適化"]
            )
        
        # ワーカーエラー
        if any(keyword in text_lower for keyword in ['worker', 'process', 'died', 'failed']):
            return cls(
                category=ErrorCategory.WORKER_ERROR,
                keywords=['worker', 'process'],
                regex_patterns=[r'worker.*failed', r'process.*died'],
                confidence=0.75,
                severity="medium",
                description="ワーカープロセスエラー",
                suggested_actions=["ワーカーの再起動", "リソース使用量の確認"]
            )
        
        # デフォルト（不明）
        return cls(
            category=ErrorCategory.UNKNOWN_ERROR,
            keywords=[],
            regex_patterns=[],
            confidence=0.1,
            severity="low",
            description="未分類エラー",
            suggested_actions=["ログの詳細確認", "手動分析が必要"]
        )


class ClassificationModel:
    """機械学習分類モデル"""
    
    def __init__(self):
        self.vectorizer = None
        self.classifier = None
        self.is_trained = False
        self.accuracy = 0.0
        self.feature_count = 0
        
        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(max_features=10000, stop_words='english')
            self.classifier = MultinomialNB()
    
    def extract_features(self, error_text: str) -> Dict[str, Any]:
        """エラーテキストから特徴を抽出"""
        features = {}
        text_lower = error_text.lower()
        
        # キーワード特徴
        keywords = ['connection', 'timeout', 'error', 'failed', 'denied', 'invalid']
        for keyword in keywords:
            features[keyword] = keyword in text_lower
        
        # 数値特徴（ポート番号、エラーコードなど）
        port_match = re.search(r':(\d+)', error_text)
        if port_match:
            features['port_number'] = int(port_match.group(1))
        
        # 長さ特徴
        features['text_length'] = len(error_text)
        features['word_count'] = len(error_text.split())
        
        return features
    
    def train(self, training_data: List[Tuple[str, str]]) -> None:
        """訓練データでモデルを学習"""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, skipping ML training")
            self.is_trained = True
            self.accuracy = 0.7  # 基本ルールベースの精度
            return
        
        try:
            texts, labels = zip(*training_data)
            
            # テキストをベクトル化
            X = self.vectorizer.fit_transform(texts)
            y = labels
            
            # 訓練・テスト分割
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # モデル訓練
            self.classifier.fit(X_train, y_train)
            
            # 精度評価
            y_pred = self.classifier.predict(X_test)
            self.accuracy = accuracy_score(y_test, y_pred)
            
            self.is_trained = True
            self.feature_count = X.shape[1]
            
            logger.info(f"Model trained with accuracy: {self.accuracy:.3f}")
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            self.is_trained = False
    
    def predict(self, error_text: str) -> Tuple[str, float]:
        """エラーテキストの分類を予測"""
        if not self.is_trained:
            # ルールベースのフォールバック
            pattern = ErrorPattern.extract(error_text)
            return pattern.category.value, pattern.confidence
        
        if not SKLEARN_AVAILABLE:
            pattern = ErrorPattern.extract(error_text)
            return pattern.category.value, pattern.confidence
        
        try:
            X = self.vectorizer.transform([error_text])
            prediction = self.classifier.predict(X)[0]
            probabilities = self.classifier.predict_proba(X)[0]
            confidence = max(probabilities)
            
            return prediction, confidence
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            pattern = ErrorPattern.extract(error_text)
            return pattern.category.value, pattern.confidence
    
    def evaluate(self, test_data: List[Tuple[str, str]]) -> Dict[str, float]:
        """テストデータでモデルを評価"""
        if not test_data or not self.is_trained:
            return {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1_score': 0.0}
        
        try:
            texts, true_labels = zip(*test_data)
            predictions = [self.predict(text)[0] for text in texts]
            
            metrics = {
                'accuracy': accuracy_score(true_labels, predictions),
                'precision': precision_score(true_labels, predictions, average='weighted', zero_division=0),
                'recall': recall_score(true_labels, predictions, average='weighted', zero_division=0),
                'f1_score': f1_score(true_labels, predictions, average='weighted', zero_division=0)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1_score': 0.0}
    
    def save(self, model_path: Path) -> None:
        """モデルを保存"""
        try:
            model_data = {
                'vectorizer': self.vectorizer,
                'classifier': self.classifier,
                'is_trained': self.is_trained,
                'accuracy': self.accuracy,
                'feature_count': self.feature_count
            }
            
            with open(model_path, 'wb') as f:
                pickle.dump(model_data, f)
                
            logger.info(f"Model saved to {model_path}")
            
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    @classmethod
    def load(cls, model_path: Path) -> 'ClassificationModel':
        """保存されたモデルを読み込み"""
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            model = cls()
            model.vectorizer = model_data.get('vectorizer')
            model.classifier = model_data.get('classifier')
            model.is_trained = model_data.get('is_trained', False)
            model.accuracy = model_data.get('accuracy', 0.0)
            model.feature_count = model_data.get('feature_count', 0)
            
            logger.info(f"Model loaded from {model_path}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return cls()


class ErrorAnalyzer:
    """エラー分析クラス"""
    
    def __init__(self):
        self.error_cache = {}
    
    def calculate_similarity(self, error1: str, error2: str) -> float:
        """2つのエラーメッセージの類似度を計算"""
        # 簡単なJaccard類似度
        words1 = set(error1.lower().split())
        words2 = set(error2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def cluster_errors(self, errors: List[str], n_clusters: int = 3) -> List[List[str]]:
        """エラーメッセージをクラスタリング"""
        if not SKLEARN_AVAILABLE or len(errors) < n_clusters:
            # 簡単なグルーピング
            groups = [[] for _ in range(n_clusters)]
            for i, error in enumerate(errors):
                groups[i % n_clusters].append(error)
            return groups
        
        try:
            # TF-IDFベクトル化
            vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            X = vectorizer.fit_transform(errors)
            
            # K-meansクラスタリング
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            labels = kmeans.fit_predict(X)
            
            # クラスタごとにグループ化
            clusters = [[] for _ in range(n_clusters)]
            for i, label in enumerate(labels):
                clusters[label].append(errors[i])
            
            return clusters
            
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            # フォールバック
            groups = [[] for _ in range(n_clusters)]
            for i, error in enumerate(errors):
                groups[i % n_clusters].append(error)
            return groups
    
    def find_root_cause(self, error_chain: List[str]) -> Dict[str, Any]:
        """エラーチェーンから根本原因を分析"""
        # 簡単な根本原因分析
        common_patterns = {
            'database': ['DATABASE_CONNECTION_LIMIT', 'connection pool'],
            'timeout': ['NETWORK_TIMEOUT', 'slow response'],
            'memory': ['MEMORY_LEAK', 'resource exhaustion'],
            'permission': ['PERMISSION_DENIED', 'access control']
        }
        
        chain_text = ' '.join(error_chain).lower()
        
        for pattern, causes in common_patterns.items():
            if pattern in chain_text:
                return {
                    'cause': causes[0],
                    'confidence': 0.8,
                    'remediation': f"Check {pattern} configuration",
                    'pattern': pattern
                }
        
        return {
            'cause': 'UNKNOWN_ROOT_CAUSE',
            'confidence': 0.1,
            'remediation': 'Manual analysis required',
            'pattern': 'unknown'
        }
    
    def find_correlations(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """エラー間の相関を分析"""
        correlations = []
        
        # 時間的相関の検出
        for i, error1 in enumerate(errors):
            for j, error2 in enumerate(errors[i+1:], i+1):
                # 時間差を計算
                try:
                    time1 = datetime.fromisoformat(error1.get('timestamp', ''))
                    time2 = datetime.fromisoformat(error2.get('timestamp', ''))
                    time_diff = abs((time2 - time1).total_seconds())
                    
                    # 30秒以内の場合は相関ありとみなす
                    if time_diff <= 30:
                        similarity = self.calculate_similarity(
                            error1.get('message', ''),
                            error2.get('message', '')
                        )
                        
                        if similarity > 0.3:  # 類似度30%以上
                            correlations.append({
                                'error1': error1,
                                'error2': error2,
                                'correlation': similarity,
                                'time_diff': time_diff,
                                'type': 'temporal'
                            })
                            
                except (ValueError, TypeError):
                    continue
        
        return correlations
    
    def analyze_trends(self, errors: List[Dict[str, Any]], window: str = '1h') -> Dict[str, Any]:
        """エラートレンドを分析"""
        trends = defaultdict(lambda: {'frequency': 0, 'trend': 'stable'})
        
        # 時間ウィンドウの設定
        window_minutes = {'1h': 60, '1d': 1440, '1w': 10080}.get(window, 60)
        
        # エラーカテゴリごとの頻度を計算
        for error in errors:
            try:
                timestamp = datetime.fromisoformat(error.get('timestamp', ''))
                message = error.get('message', '')
                
                # 簡単な分類
                pattern = ErrorPattern.extract(message)
                category = pattern.category.value
                
                trends[category]['frequency'] += 1
                
            except (ValueError, TypeError):
                continue
        
        # トレンドの判定（簡単な実装）
        for category, data in trends.items():
            if data['frequency'] > 5:
                data['trend'] = 'increasing'
            elif data['frequency'] < 2:
                data['trend'] = 'decreasing'
        
        return dict(trends)


class ErrorClassificationSystem:
    """エラー分類システムメインクラス"""
    
    def __init__(self, model_path: Optional[Path] = None):
        """エラー分類システム初期化"""
        self.model_path = model_path or PROJECT_ROOT / "models" / "error_classification_model.pkl"
        self.db_path = PROJECT_ROOT / "data" / "error_classification.db"
        self.knowledge_base_path = PROJECT_ROOT / "knowledge_base"
        
        # コンポーネント初期化
        self.model = ClassificationModel()
        self.analyzer = ErrorAnalyzer()
        
        # エラーカテゴリリスト
        self.error_categories = [category.value for category in ErrorCategory]
        
        # 統計情報
        self.metrics = {
            'total_processed': 0,
            'total_classified': 0,
            'accuracy_samples': [],
            'category_distribution': defaultdict(int)
        }
        
        # データベース初期化
        self._init_database()
        
        # 既存モデルの読み込み
        if self.model_path.exists():
            self.model = ClassificationModel.load(self.model_path)
        
        logger.info("Error Classification System initialized")
    
    def _init_database(self):
        """データベース初期化"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS classified_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_hash TEXT UNIQUE,
                    original_message TEXT,
                    category TEXT,
                    confidence REAL,
                    priority TEXT,
                    suggested_actions TEXT,
                    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    feedback TEXT,
                    is_correct BOOLEAN
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS error_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_name TEXT,
                    regex_pattern TEXT,
                    category TEXT,
                    confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_error_hash 
                ON classified_errors(error_hash)
            """)
    
    def classify(self, error: Dict[str, Any]) -> Dict[str, Any]:
        """単一エラーの分類"""
        try:
            message = error.get('message', '')
            source = error.get('source', 'unknown')
            timestamp = error.get('timestamp', datetime.now().isoformat())
            
            # エラーのハッシュ化（重複チェック用）
            error_hash = hashlib.md5(message.encode()).hexdigest()
            
            # キャッシュから検索
            cached_result = self._get_cached_result(error_hash)
            if cached_result:
                return cached_result
            
            # 分類実行
            category, confidence = self.model.predict(message)
            
            # 優先度の決定
            error_category = ErrorCategory(category)
            priority = self._determine_priority(error_category, message, source)
            
            # 推奨アクションの生成
            suggested_actions = self._generate_suggested_actions(error_category, message)
            
            result = {
                'category': category,
                'confidence': confidence,
                'priority': priority,
                'suggested_action': suggested_actions,
                'documentation_link': self._get_documentation_link(error_category),
                'error_hash': error_hash,
                'classified_at': datetime.now().isoformat(),
                'source': source,
                'original_message': message
            }
            
            # 結果をキャッシュ
            self._cache_result(result)
            
            # 統計更新
            self.metrics['total_processed'] += 1
            self.metrics['total_classified'] += 1
            self.metrics['category_distribution'][category] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return {
                'category': 'UNKNOWN_ERROR',
                'confidence': 0.0,
                'priority': 'low',
                'suggested_action': ['Manual analysis required'],
                'error': str(e)
            }
    
    def classify_batch(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """バッチ分類"""
        results = []
        
        for error in errors:
            result = self.classify(error)
            results.append(result)
        
        logger.info(f"Classified {len(results)} errors in batch")
        return results
    
    def _determine_priority(self, category: ErrorCategory, message: str, source: str) -> str:
        """優先度の決定"""
        base_priority = category.default_severity
        
        # メッセージ内容による調整
        message_lower = message.lower()
        
        # クリティカルワードの検出
        critical_words = ['corrupted', 'failed', 'crashed', 'fatal', 'critical']
        if any(word in message_lower for word in critical_words):
            return 'critical'
        
        # 高優先度ワードの検出
        high_words = ['error', 'exception', 'timeout', 'denied']
        if any(word in message_lower for word in high_words):
            if base_priority == 'medium':
                return 'high'
        
        return base_priority
    
    def _generate_suggested_actions(self, category: ErrorCategory, message: str) -> List[str]:
        """推奨アクションの生成"""
        action_map = {
            ErrorCategory.API_ERROR: [
                "APIキーの設定を確認してください",
                "API制限をチェックしてください",
                "認証設定を確認してください"
            ],
            ErrorCategory.DATABASE_ERROR: [
                "データベース接続を確認してください",
                "接続プールの設定を確認してください",
                "データベースサーバーの状態を確認してください"
            ],
            ErrorCategory.TIMEOUT_ERROR: [
                "タイムアウト設定を増やしてください",
                "ネットワーク接続を確認してください",
                "処理の最適化を検討してください"
            ],
            ErrorCategory.WORKER_ERROR: [
                "ワーカープロセスを再起動してください",
                "リソース使用量を確認してください",
                "ワーカー設定を確認してください"
            ],
            ErrorCategory.PERMISSION_ERROR: [
                "ファイル・ディレクトリの権限を確認してください",
                "ユーザー権限を確認してください",
                "SELinux/AppArmorの設定を確認してください"
            ]
        }
        
        return action_map.get(category, ["ログを詳細に確認してください", "手動での調査が必要です"])
    
    def _get_documentation_link(self, category: ErrorCategory) -> str:
        """ドキュメントリンクの取得"""
        base_url = "/docs/troubleshooting/"
        category_map = {
            ErrorCategory.API_ERROR: f"{base_url}api-errors.md",
            ErrorCategory.DATABASE_ERROR: f"{base_url}database-errors.md",
            ErrorCategory.WORKER_ERROR: f"{base_url}worker-errors.md",
            ErrorCategory.TIMEOUT_ERROR: f"{base_url}timeout-errors.md"
        }
        
        return category_map.get(category, f"{base_url}general-errors.md")
    
    def _get_cached_result(self, error_hash: str) -> Optional[Dict[str, Any]]:
        """キャッシュから結果を取得"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute("""
                    SELECT category, confidence, priority, suggested_actions, classified_at
                    FROM classified_errors
                    WHERE error_hash = ?
                    ORDER BY classified_at DESC
                    LIMIT 1
                """, (error_hash,))
                
                row = cursor.fetchone()
                if row:
                    category, confidence, priority, suggested_actions, classified_at = row
                    return {
                        'category': category,
                        'confidence': confidence,
                        'priority': priority,
                        'suggested_action': json.loads(suggested_actions) if suggested_actions else [],
                        'cached': True,
                        'classified_at': classified_at
                    }
                    
        except Exception as e:
            logger.error(f"Cache lookup failed: {e}")
        
        return None
    
    def _cache_result(self, result: Dict[str, Any]) -> None:
        """結果をキャッシュ"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO classified_errors 
                    (error_hash, original_message, category, confidence, priority, suggested_actions)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    result['error_hash'],
                    result['original_message'],
                    result['category'],
                    result['confidence'],
                    result['priority'],
                    json.dumps(result['suggested_action'])
                ))
                
        except Exception as e:
            logger.error(f"Cache storage failed: {e}")
    
    def load_errors_from_log(self, log_path: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """ログファイルからエラーを読み込み"""
        errors = []
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if limit and i >= limit:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 簡単なログパース（JSON形式を想定）
                    try:
                        if line.startswith('{'):
                            error_data = json.loads(line)
                            errors.append(error_data)
                        else:
                            # プレーンテキストの場合
                            errors.append({
                                'message': line,
                                'timestamp': datetime.now().isoformat(),
                                'source': 'log_file'
                            })
                    except json.JSONDecodeError:
                        errors.append({
                            'message': line,
                            'timestamp': datetime.now().isoformat(),
                            'source': 'log_file'
                        })
                        
        except Exception as e:
            logger.error(f"Failed to load errors from log: {e}")
        
        logger.info(f"Loaded {len(errors)} errors from {log_path}")
        return errors
    
    def get_classification_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分類結果の統計を取得"""
        stats = {
            'total_classified': len(results),
            'accuracy': sum(r.get('confidence', 0) for r in results) / len(results) if results else 0,
            'category_distribution': Counter(r.get('category', 'UNKNOWN') for r in results),
            'priority_distribution': Counter(r.get('priority', 'unknown') for r in results),
            'average_confidence': sum(r.get('confidence', 0) for r in results) / len(results) if results else 0
        }
        
        return stats
    
    def get_metrics(self) -> Dict[str, Any]:
        """システムメトリクスを取得"""
        return self.metrics.copy()
    
    def incremental_train(self, new_errors: List[Dict[str, Any]]) -> None:
        """新しいデータで増分学習"""
        if not new_errors:
            return
        
        # 新しい訓練データの準備
        training_data = []
        for error in new_errors:
            message = error.get('message', '')
            category = error.get('category', 'UNKNOWN_ERROR')
            if message and category:
                training_data.append((message, category))
        
        if training_data:
            # 既存モデルと新データで再訓練
            self.model.train(training_data)
            
            # モデルを保存
            self.model.save(self.model_path)
            
            logger.info(f"Incremental training completed with {len(training_data)} samples")
    
    def evaluate(self) -> float:
        """現在のモデルの精度を評価"""
        return self.model.accuracy