#!/usr/bin/env python3
"""
🧠 Autonomous Learning System - 自律的学習システム
4賢者協調による完全自律学習の実現

グランドエルダーmaru → クロードエルダー → 4賢者 → 評議会 → サーバント
全階層での知識共有と相互学習を実現

Author: Claude Elder
Date: 2025-07-10
Phase: 2 (自律的学習システム実装)
"""

import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import sqlite3
import threading
import queue
from collections import defaultdict, deque
import hashlib
import pickle
from abc import ABC, abstractmethod

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent

# 既存システムのインポート（モック）
try:
    from .elder_tree_vector_network import ElderTreeVectorNetwork, ElderNode
    from .multidimensional_vector_system import MultiDimensionalVectorSystem, KnowledgeType
    from .predictive_pattern_learning import PredictivePatternLearningSystem, TaskExecutionRecord
    from .realtime_monitoring_enhancement import RealtimeMonitoringEnhancement, AnomalyEvent
except ImportError:
    # モック実装
    ElderTreeVectorNetwork = None
    MultiDimensionalVectorSystem = None
    PredictivePatternLearningSystem = None
    RealtimeMonitoringEnhancement = None

class LearningDomain(Enum):
    """学習ドメイン"""
    KNOWLEDGE = "knowledge"      # 知識領域
    TASK = "task"               # タスク実行
    INCIDENT = "incident"       # インシデント対応
    SEARCH = "search"           # 検索・RAG
    CROSS_DOMAIN = "cross"      # クロスドメイン

class LearningStrategy(Enum):
    """学習戦略"""
    SUPERVISED = "supervised"          # 教師あり学習
    UNSUPERVISED = "unsupervised"    # 教師なし学習
    REINFORCEMENT = "reinforcement"   # 強化学習
    TRANSFER = "transfer"             # 転移学習
    META = "meta"                     # メタ学習
    FEDERATED = "federated"           # 連合学習

class SageType(Enum):
    """賢者タイプ"""
    KNOWLEDGE = "knowledge"    # ナレッジ賢者
    TASK = "task"             # タスク賢者
    INCIDENT = "incident"     # インシデント賢者
    RAG = "rag"               # RAG賢者

@dataclass
class LearningExperience:
    """学習経験"""
    experience_id: str
    timestamp: datetime
    domain: LearningDomain
    sage_type: SageType
    input_data: Dict[str, Any]
    output_result: Dict[str, Any]
    success: bool
    confidence: float
    lessons_learned: List[str]
    knowledge_vector: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class CrossDomainInsight:
    """クロスドメイン洞察"""
    insight_id: str
    created_at: datetime
    source_domains: List[LearningDomain]
    insight_type: str
    discovery: str
    applicable_domains: List[LearningDomain]
    confidence: float
    evidence: List[Dict[str, Any]]
    potential_impact: Dict[str, float]

@dataclass
class MetaLearningPattern:
    """メタ学習パターン"""
    pattern_id: str
    discovered_at: datetime
    pattern_type: str
    effectiveness: float
    applicable_strategies: List[LearningStrategy]
    success_conditions: Dict[str, Any]
    failure_conditions: Dict[str, Any]
    optimization_hints: List[str]

@dataclass
class ElderKnowledgePacket:
    """エルダー知識パケット"""
    packet_id: str
    created_at: datetime
    source_elder: str
    target_elder: Optional[str]
    knowledge_type: str
    content: Dict[str, Any]
    vector_representation: Optional[np.ndarray]
    propagation_path: List[str]
    absorption_rate: float

class SageAgent(ABC):
    """賢者エージェント基底クラス"""
    
    def __init__(self, sage_type: SageType, learning_system):
        self.sage_type = sage_type
        self.learning_system = learning_system
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{sage_type.value}")
        self.knowledge_base = {}
        self.learning_history = deque(maxlen=1000)
        self.performance_metrics = defaultdict(float)
        
    @abstractmethod
    async def process_experience(self, experience: LearningExperience) -> Dict[str, Any]:
        """経験を処理して学習"""
        pass
    
    @abstractmethod
    async def share_knowledge(self) -> ElderKnowledgePacket:
        """知識を共有"""
        pass
    
    @abstractmethod
    async def receive_knowledge(self, packet: ElderKnowledgePacket):
        """知識を受信して統合"""
        pass
    
    async def evaluate_performance(self) -> Dict[str, float]:
        """パフォーマンス評価"""
        return dict(self.performance_metrics)

class KnowledgeSageAgent(SageAgent):
    """ナレッジ賢者エージェント"""
    
    async def process_experience(self, experience: LearningExperience) -> Dict[str, Any]:
        """知識領域の経験を処理"""
        try:
            # 知識パターン抽出
            patterns = await self._extract_knowledge_patterns(experience)
            
            # 知識ベース更新
            await self._update_knowledge_base(patterns)
            
            # 新しい洞察生成
            insights = await self._generate_insights(patterns)
            
            # パフォーマンス更新
            self.performance_metrics['processed_experiences'] += 1
            self.performance_metrics['knowledge_patterns'] += len(patterns)
            
            return {
                'patterns': patterns,
                'insights': insights,
                'knowledge_growth': len(self.knowledge_base)
            }
            
        except Exception as e:
            self.logger.error(f"Experience processing failed: {e}")
            return {'error': str(e)}
    
    async def share_knowledge(self) -> ElderKnowledgePacket:
        """最も価値のある知識を共有"""
        # 最重要知識を選択
        top_knowledge = await self._select_top_knowledge()
        
        packet = ElderKnowledgePacket(
            packet_id=f"knowledge_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            created_at=datetime.now(),
            source_elder=f"sage_{self.sage_type.value}",
            target_elder=None,  # ブロードキャスト
            knowledge_type="knowledge_pattern",
            content=top_knowledge,
            vector_representation=None,  # 簡略化
            propagation_path=[f"sage_{self.sage_type.value}"],
            absorption_rate=0.0
        )
        
        return packet
    
    async def receive_knowledge(self, packet: ElderKnowledgePacket):
        """他の賢者からの知識を統合"""
        # 知識の関連性評価
        relevance = await self._evaluate_relevance(packet)
        
        if relevance > 0.5:
            # 知識統合
            await self._integrate_knowledge(packet)
            packet.absorption_rate = relevance
            self.logger.info(f"Knowledge integrated: {packet.packet_id} (relevance: {relevance:.2f})")
    
    async def _extract_knowledge_patterns(self, experience: LearningExperience) -> List[Dict[str, Any]]:
        """知識パターン抽出"""
        patterns = []
        
        # 成功パターン
        if experience.success and experience.confidence > 0.7:
            patterns.append({
                'type': 'success_pattern',
                'domain': experience.domain.value,
                'confidence': experience.confidence,
                'conditions': experience.input_data,
                'outcomes': experience.output_result
            })
        
        # 失敗パターン
        elif not experience.success:
            patterns.append({
                'type': 'failure_pattern',
                'domain': experience.domain.value,
                'lessons': experience.lessons_learned,
                'avoid_conditions': experience.input_data
            })
        
        return patterns
    
    async def _update_knowledge_base(self, patterns: List[Dict[str, Any]]):
        """知識ベース更新"""
        for pattern in patterns:
            pattern_key = f"{pattern['type']}_{pattern['domain']}"
            if pattern_key not in self.knowledge_base:
                self.knowledge_base[pattern_key] = []
            self.knowledge_base[pattern_key].append(pattern)
    
    async def _generate_insights(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """洞察生成"""
        insights = []
        
        # パターン分析
        for pattern in patterns:
            if pattern['type'] == 'success_pattern' and pattern['confidence'] > 0.8:
                insights.append(f"High confidence pattern discovered in {pattern['domain']}")
            elif pattern['type'] == 'failure_pattern':
                insights.append(f"Failure pattern identified: {', '.join(pattern['lessons'])}")
        
        return insights
    
    async def _select_top_knowledge(self) -> Dict[str, Any]:
        """最重要知識選択"""
        # 簡略化実装
        return {
            'knowledge_count': len(self.knowledge_base),
            'top_patterns': list(self.knowledge_base.keys())[:5],
            'sage_type': self.sage_type.value
        }
    
    async def _evaluate_relevance(self, packet: ElderKnowledgePacket) -> float:
        """知識関連性評価"""
        # ドメインマッチング
        if packet.knowledge_type == "knowledge_pattern":
            return 0.8
        elif packet.source_elder.startswith("sage_"):
            return 0.6
        else:
            return 0.3
    
    async def _integrate_knowledge(self, packet: ElderKnowledgePacket):
        """知識統合"""
        integrated_key = f"integrated_{packet.source_elder}_{packet.knowledge_type}"
        self.knowledge_base[integrated_key] = packet.content

class TaskSageAgent(SageAgent):
    """タスク賢者エージェント"""
    
    async def process_experience(self, experience: LearningExperience) -> Dict[str, Any]:
        """タスク実行経験を処理"""
        # タスクパターン学習
        task_patterns = await self._learn_task_patterns(experience)
        
        # 最適化戦略生成
        optimization_strategies = await self._generate_optimization_strategies(task_patterns)
        
        self.performance_metrics['task_experiences'] += 1
        self.performance_metrics['optimization_strategies'] += len(optimization_strategies)
        
        return {
            'task_patterns': task_patterns,
            'optimization_strategies': optimization_strategies
        }
    
    async def share_knowledge(self) -> ElderKnowledgePacket:
        """タスク最適化知識を共有"""
        best_strategies = await self._get_best_strategies()
        
        return ElderKnowledgePacket(
            packet_id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            created_at=datetime.now(),
            source_elder=f"sage_{self.sage_type.value}",
            target_elder=None,
            knowledge_type="task_optimization",
            content=best_strategies,
            vector_representation=None,
            propagation_path=[f"sage_{self.sage_type.value}"],
            absorption_rate=0.0
        )
    
    async def receive_knowledge(self, packet: ElderKnowledgePacket):
        """タスク関連知識を受信"""
        if packet.knowledge_type in ["task_optimization", "execution_pattern"]:
            await self._apply_optimization_knowledge(packet)
            packet.absorption_rate = 0.9
    
    async def _learn_task_patterns(self, experience: LearningExperience) -> List[Dict[str, Any]]:
        """タスクパターン学習"""
        return [{
            'pattern_type': 'execution',
            'success_rate': 0.8 if experience.success else 0.2,
            'conditions': experience.input_data
        }]
    
    async def _generate_optimization_strategies(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """最適化戦略生成"""
        strategies = []
        for pattern in patterns:
            if pattern['success_rate'] > 0.7:
                strategies.append({
                    'strategy': 'replicate_success',
                    'pattern': pattern
                })
            else:
                strategies.append({
                    'strategy': 'avoid_failure',
                    'pattern': pattern
                })
        return strategies
    
    async def _get_best_strategies(self) -> Dict[str, Any]:
        """最良戦略取得"""
        return {
            'top_strategies': list(self.knowledge_base.keys())[:3],
            'performance_metrics': dict(self.performance_metrics)
        }
    
    async def _apply_optimization_knowledge(self, packet: ElderKnowledgePacket):
        """最適化知識適用"""
        self.knowledge_base[f"external_{packet.packet_id}"] = packet.content

class IncidentSageAgent(SageAgent):
    """インシデント賢者エージェント"""
    
    async def process_experience(self, experience: LearningExperience) -> Dict[str, Any]:
        """インシデント経験を処理"""
        # 異常パターン学習
        anomaly_patterns = await self._learn_anomaly_patterns(experience)
        
        # 予防策生成
        prevention_strategies = await self._generate_prevention_strategies(anomaly_patterns)
        
        self.performance_metrics['incidents_processed'] += 1
        self.performance_metrics['prevention_strategies'] += len(prevention_strategies)
        
        return {
            'anomaly_patterns': anomaly_patterns,
            'prevention_strategies': prevention_strategies
        }
    
    async def share_knowledge(self) -> ElderKnowledgePacket:
        """インシデント予防知識を共有"""
        critical_patterns = await self._get_critical_patterns()
        
        return ElderKnowledgePacket(
            packet_id=f"incident_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            created_at=datetime.now(),
            source_elder=f"sage_{self.sage_type.value}",
            target_elder=None,
            knowledge_type="incident_prevention",
            content=critical_patterns,
            vector_representation=None,
            propagation_path=[f"sage_{self.sage_type.value}"],
            absorption_rate=0.0
        )
    
    async def receive_knowledge(self, packet: ElderKnowledgePacket):
        """インシデント関連知識を受信"""
        if packet.knowledge_type in ["incident_prevention", "anomaly_pattern"]:
            await self._integrate_prevention_knowledge(packet)
            packet.absorption_rate = 0.95
    
    async def _learn_anomaly_patterns(self, experience: LearningExperience) -> List[Dict[str, Any]]:
        """異常パターン学習"""
        return [{
            'anomaly_type': 'system_anomaly',
            'severity': 'high' if not experience.success else 'low',
            'indicators': experience.input_data
        }]
    
    async def _generate_prevention_strategies(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """予防策生成"""
        strategies = []
        for pattern in patterns:
            if pattern['severity'] == 'high':
                strategies.append({
                    'action': 'immediate_prevention',
                    'target': pattern['anomaly_type'],
                    'priority': 'critical'
                })
        return strategies
    
    async def _get_critical_patterns(self) -> Dict[str, Any]:
        """重要パターン取得"""
        return {
            'critical_anomalies': list(self.knowledge_base.keys())[:5],
            'prevention_count': len(self.knowledge_base)
        }
    
    async def _integrate_prevention_knowledge(self, packet: ElderKnowledgePacket):
        """予防知識統合"""
        self.knowledge_base[f"prevention_{packet.packet_id}"] = packet.content

class RAGSageAgent(SageAgent):
    """RAG賢者エージェント"""
    
    async def process_experience(self, experience: LearningExperience) -> Dict[str, Any]:
        """検索・RAG経験を処理"""
        # 検索パターン学習
        search_patterns = await self._learn_search_patterns(experience)
        
        # 検索最適化生成
        search_optimizations = await self._generate_search_optimizations(search_patterns)
        
        self.performance_metrics['searches_processed'] += 1
        self.performance_metrics['search_optimizations'] += len(search_optimizations)
        
        return {
            'search_patterns': search_patterns,
            'search_optimizations': search_optimizations
        }
    
    async def share_knowledge(self) -> ElderKnowledgePacket:
        """検索最適化知識を共有"""
        best_search_strategies = await self._get_best_search_strategies()
        
        return ElderKnowledgePacket(
            packet_id=f"rag_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            created_at=datetime.now(),
            source_elder=f"sage_{self.sage_type.value}",
            target_elder=None,
            knowledge_type="search_optimization",
            content=best_search_strategies,
            vector_representation=None,
            propagation_path=[f"sage_{self.sage_type.value}"],
            absorption_rate=0.0
        )
    
    async def receive_knowledge(self, packet: ElderKnowledgePacket):
        """検索関連知識を受信"""
        if packet.knowledge_type in ["search_optimization", "retrieval_pattern"]:
            await self._apply_search_knowledge(packet)
            packet.absorption_rate = 0.85
    
    async def _learn_search_patterns(self, experience: LearningExperience) -> List[Dict[str, Any]]:
        """検索パターン学習"""
        return [{
            'search_type': 'semantic_search',
            'effectiveness': experience.confidence,
            'query_patterns': experience.input_data
        }]
    
    async def _generate_search_optimizations(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """検索最適化生成"""
        optimizations = []
        for pattern in patterns:
            if pattern['effectiveness'] > 0.7:
                optimizations.append({
                    'optimization': 'enhance_query',
                    'method': pattern['search_type'],
                    'expected_improvement': 0.2
                })
        return optimizations
    
    async def _get_best_search_strategies(self) -> Dict[str, Any]:
        """最良検索戦略取得"""
        return {
            'top_search_methods': list(self.knowledge_base.keys())[:3],
            'search_performance': dict(self.performance_metrics)
        }
    
    async def _apply_search_knowledge(self, packet: ElderKnowledgePacket):
        """検索知識適用"""
        self.knowledge_base[f"search_{packet.packet_id}"] = packet.content

class AutonomousLearningSystem:
    """自律的学習システム - 4賢者協調による完全自律学習"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or self._default_config()
        
        # 4賢者エージェント初期化
        self.sages = {
            SageType.KNOWLEDGE: KnowledgeSageAgent(SageType.KNOWLEDGE, self),
            SageType.TASK: TaskSageAgent(SageType.TASK, self),
            SageType.INCIDENT: IncidentSageAgent(SageType.INCIDENT, self),
            SageType.RAG: RAGSageAgent(SageType.RAG, self)
        }
        
        # 学習経験キュー
        self.experience_queue = queue.Queue()
        self.knowledge_exchange_queue = queue.Queue()
        
        # クロスドメイン洞察
        self.cross_domain_insights = []
        self.meta_learning_patterns = []
        
        # メトリクス
        self.system_metrics = {
            'total_experiences': 0,
            'cross_domain_insights': 0,
            'meta_patterns_discovered': 0,
            'knowledge_packets_exchanged': 0,
            'learning_efficiency': 0.0
        }
        
        # 学習履歴
        self.learning_history = deque(maxlen=10000)
        
        # エルダー階層統合
        self.elder_hierarchy = {
            'grand_elder': {'knowledge_packets': [], 'decisions': []},
            'claude_elder': {'instructions': [], 'feedback': []},
            'council': {'proposals': [], 'votes': []},
            'servants': {'tasks': [], 'reports': []}
        }
        
        # 学習スレッド
        self.learning_active = False
        self.learning_threads = []
        
        # データベース初期化
        self._init_database()
        
        self.logger.info("🧠 Autonomous Learning System initialized with 4 Sages")
    
    def _default_config(self) -> Dict[str, Any]:
        """デフォルト設定"""
        return {
            'learning_rate': 0.001,
            'batch_size': 32,
            'exchange_interval': 60,  # 知識交換間隔（秒）
            'meta_learning_threshold': 100,  # メタ学習開始閾値
            'cross_domain_threshold': 0.7,  # クロスドメイン相関閾値
            'database_path': str(PROJECT_ROOT / "data" / "autonomous_learning.db")
        }
    
    def _init_database(self):
        """データベース初期化"""
        try:
            db_path = self.config['database_path']
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 学習経験テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_experiences (
                    experience_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    domain TEXT,
                    sage_type TEXT,
                    input_data TEXT,
                    output_result TEXT,
                    success BOOLEAN,
                    confidence REAL,
                    lessons_learned TEXT,
                    metadata TEXT
                );
            """)
            
            # クロスドメイン洞察テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cross_domain_insights (
                    insight_id TEXT PRIMARY KEY,
                    created_at TEXT,
                    source_domains TEXT,
                    insight_type TEXT,
                    discovery TEXT,
                    applicable_domains TEXT,
                    confidence REAL,
                    evidence TEXT,
                    potential_impact TEXT
                );
            """)
            
            # メタ学習パターンテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meta_learning_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    discovered_at TEXT,
                    pattern_type TEXT,
                    effectiveness REAL,
                    applicable_strategies TEXT,
                    success_conditions TEXT,
                    failure_conditions TEXT,
                    optimization_hints TEXT
                );
            """)
            
            # 知識パケットテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_packets (
                    packet_id TEXT PRIMARY KEY,
                    created_at TEXT,
                    source_elder TEXT,
                    target_elder TEXT,
                    knowledge_type TEXT,
                    content TEXT,
                    propagation_path TEXT,
                    absorption_rate REAL
                );
            """)
            
            conn.commit()
            conn.close()
            
            self.logger.info("📊 Learning database initialized")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
    
    async def start_learning(self):
        """学習開始"""
        if self.learning_active:
            self.logger.warning("Learning already active")
            return
        
        self.learning_active = True
        
        # 学習タスク開始
        tasks = [
            asyncio.create_task(self._experience_processing_loop()),
            asyncio.create_task(self._knowledge_exchange_loop()),
            asyncio.create_task(self._cross_domain_analysis_loop()),
            asyncio.create_task(self._meta_learning_loop()),
            asyncio.create_task(self._elder_integration_loop())
        ]
        
        self.logger.info("🚀 Autonomous learning started with 4 Sages")
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Learning error: {e}")
            self.learning_active = False
    
    async def stop_learning(self):
        """学習停止"""
        self.learning_active = False
        self.logger.info("🛑 Autonomous learning stopped")
    
    async def submit_experience(self, 
                              domain: LearningDomain,
                              sage_type: SageType,
                              input_data: Dict[str, Any],
                              output_result: Dict[str, Any],
                              success: bool,
                              confidence: float,
                              lessons_learned: List[str] = None) -> str:
        """学習経験を投稿"""
        experience = LearningExperience(
            experience_id=f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{sage_type.value}",
            timestamp=datetime.now(),
            domain=domain,
            sage_type=sage_type,
            input_data=input_data,
            output_result=output_result,
            success=success,
            confidence=confidence,
            lessons_learned=lessons_learned or []
        )
        
        # キューに追加
        self.experience_queue.put(experience)
        self.system_metrics['total_experiences'] += 1
        
        # データベース保存
        await self._persist_experience(experience)
        
        self.logger.info(f"📝 Experience submitted: {experience.experience_id}")
        return experience.experience_id
    
    async def _experience_processing_loop(self):
        """経験処理ループ"""
        while self.learning_active:
            try:
                # バッチ処理
                batch = []
                for _ in range(self.config['batch_size']):
                    try:
                        experience = self.experience_queue.get(timeout=1)
                        batch.append(experience)
                    except:
                        break
                
                if batch:
                    # 各賢者で処理
                    for experience in batch:
                        sage = self.sages[experience.sage_type]
                        result = await sage.process_experience(experience)
                        
                        # 履歴記録
                        self.learning_history.append({
                            'experience': experience,
                            'result': result,
                            'timestamp': datetime.now()
                        })
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Experience processing error: {e}")
                await asyncio.sleep(5)
    
    async def _knowledge_exchange_loop(self):
        """知識交換ループ"""
        while self.learning_active:
            try:
                # 各賢者から知識を収集
                for sage_type, sage in self.sages.items():
                    packet = await sage.share_knowledge()
                    
                    # 他の賢者に配布
                    for other_sage_type, other_sage in self.sages.items():
                        if other_sage_type != sage_type:
                            await other_sage.receive_knowledge(packet)
                    
                    # 統計更新
                    self.system_metrics['knowledge_packets_exchanged'] += 1
                    
                    # 保存
                    await self._persist_knowledge_packet(packet)
                
                await asyncio.sleep(self.config['exchange_interval'])
                
            except Exception as e:
                self.logger.error(f"Knowledge exchange error: {e}")
                await asyncio.sleep(60)
    
    async def _cross_domain_analysis_loop(self):
        """クロスドメイン分析ループ"""
        while self.learning_active:
            try:
                # 十分な履歴がある場合
                if len(self.learning_history) >= 50:
                    insights = await self._analyze_cross_domain_patterns()
                    
                    for insight in insights:
                        self.cross_domain_insights.append(insight)
                        self.system_metrics['cross_domain_insights'] += 1
                        
                        # 保存
                        await self._persist_cross_domain_insight(insight)
                        
                        self.logger.info(f"💡 Cross-domain insight discovered: {insight.insight_type}")
                
                await asyncio.sleep(300)  # 5分毎
                
            except Exception as e:
                self.logger.error(f"Cross-domain analysis error: {e}")
                await asyncio.sleep(300)
    
    async def _meta_learning_loop(self):
        """メタ学習ループ"""
        while self.learning_active:
            try:
                # メタ学習閾値チェック
                if len(self.learning_history) >= self.config['meta_learning_threshold']:
                    patterns = await self._discover_meta_patterns()
                    
                    for pattern in patterns:
                        self.meta_learning_patterns.append(pattern)
                        self.system_metrics['meta_patterns_discovered'] += 1
                        
                        # 保存
                        await self._persist_meta_pattern(pattern)
                        
                        self.logger.info(f"🧩 Meta-learning pattern discovered: {pattern.pattern_type}")
                
                await asyncio.sleep(600)  # 10分毎
                
            except Exception as e:
                self.logger.error(f"Meta-learning error: {e}")
                await asyncio.sleep(600)
    
    async def _elder_integration_loop(self):
        """エルダー階層統合ループ"""
        while self.learning_active:
            try:
                # グランドエルダーへの報告
                grand_elder_report = await self._generate_grand_elder_report()
                self.elder_hierarchy['grand_elder']['knowledge_packets'].append(grand_elder_report)
                
                # クロードエルダーからの指示処理
                await self._process_claude_elder_instructions()
                
                # 評議会への提案
                council_proposals = await self._generate_council_proposals()
                self.elder_hierarchy['council']['proposals'].extend(council_proposals)
                
                # サーバントへのタスク配布
                servant_tasks = await self._distribute_servant_tasks()
                self.elder_hierarchy['servants']['tasks'].extend(servant_tasks)
                
                await asyncio.sleep(3600)  # 1時間毎
                
            except Exception as e:
                self.logger.error(f"Elder integration error: {e}")
                await asyncio.sleep(3600)
    
    async def _analyze_cross_domain_patterns(self) -> List[CrossDomainInsight]:
        """クロスドメインパターン分析"""
        insights = []
        
        # ドメイン別経験を収集
        domain_experiences = defaultdict(list)
        for entry in list(self.learning_history)[-100:]:  # 最新100件
            experience = entry['experience']
            domain_experiences[experience.domain].append(experience)
        
        # ドメイン間相関分析
        domains = list(domain_experiences.keys())
        for i, domain1 in enumerate(domains):
            for domain2 in domains[i+1:]:
                correlation = await self._calculate_domain_correlation(
                    domain_experiences[domain1],
                    domain_experiences[domain2]
                )
                
                if correlation > self.config['cross_domain_threshold']:
                    insight = CrossDomainInsight(
                        insight_id=f"insight_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        created_at=datetime.now(),
                        source_domains=[domain1, domain2],
                        insight_type="domain_correlation",
                        discovery=f"Strong correlation between {domain1.value} and {domain2.value}",
                        applicable_domains=[domain1, domain2],
                        confidence=correlation,
                        evidence=[],
                        potential_impact={'efficiency': 0.3, 'accuracy': 0.2}
                    )
                    insights.append(insight)
        
        return insights
    
    async def _calculate_domain_correlation(self, 
                                          experiences1: List[LearningExperience],
                                          experiences2: List[LearningExperience]) -> float:
        """ドメイン相関計算"""
        if not experiences1 or not experiences2:
            return 0.0
        
        # 成功率の相関
        success_rates1 = [exp.confidence if exp.success else 0 for exp in experiences1]
        success_rates2 = [exp.confidence if exp.success else 0 for exp in experiences2]
        
        # 簡易相関計算
        if len(success_rates1) == len(success_rates2):
            correlation = np.corrcoef(success_rates1, success_rates2)[0, 1]
            return abs(correlation) if not np.isnan(correlation) else 0.0
        
        return 0.0
    
    async def _discover_meta_patterns(self) -> List[MetaLearningPattern]:
        """メタパターン発見"""
        patterns = []
        
        # 学習戦略の効果分析
        strategy_effectiveness = defaultdict(list)
        
        for entry in list(self.learning_history)[-200:]:  # 最新200件
            experience = entry['experience']
            result = entry['result']
            
            # 戦略判定（簡略化）
            if experience.success:
                strategy = LearningStrategy.SUPERVISED
            else:
                strategy = LearningStrategy.REINFORCEMENT
            
            effectiveness = experience.confidence if experience.success else 0.0
            strategy_effectiveness[strategy].append(effectiveness)
        
        # 効果的な戦略パターン抽出
        for strategy, effectiveness_list in strategy_effectiveness.items():
            if effectiveness_list:
                avg_effectiveness = np.mean(effectiveness_list)
                
                if avg_effectiveness > 0.7:
                    pattern = MetaLearningPattern(
                        pattern_id=f"meta_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        discovered_at=datetime.now(),
                        pattern_type=f"high_effectiveness_{strategy.value}",
                        effectiveness=avg_effectiveness,
                        applicable_strategies=[strategy],
                        success_conditions={'confidence_threshold': 0.7},
                        failure_conditions={'error_rate': 0.3},
                        optimization_hints=['Increase batch size', 'Fine-tune learning rate']
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _generate_grand_elder_report(self) -> Dict[str, Any]:
        """グランドエルダー向けレポート生成"""
        return {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': dict(self.system_metrics),
            'sage_performance': {
                sage_type.value: await sage.evaluate_performance()
                for sage_type, sage in self.sages.items()
            },
            'key_insights': len(self.cross_domain_insights),
            'meta_patterns': len(self.meta_learning_patterns),
            'recommendations': [
                "Continue autonomous learning",
                "Increase cross-domain collaboration",
                "Optimize meta-learning strategies"
            ]
        }
    
    async def _process_claude_elder_instructions(self):
        """クロードエルダーからの指示処理"""
        # 指示があれば処理（モック実装）
        pass
    
    async def _generate_council_proposals(self) -> List[Dict[str, Any]]:
        """評議会向け提案生成"""
        proposals = []
        
        # 重要な洞察に基づく提案
        for insight in self.cross_domain_insights[-5:]:  # 最新5件
            if insight.confidence > 0.8:
                proposals.append({
                    'proposal_id': f"prop_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'type': 'system_improvement',
                    'based_on': insight.insight_id,
                    'recommendation': f"Implement {insight.discovery}",
                    'expected_impact': insight.potential_impact
                })
        
        return proposals
    
    async def _distribute_servant_tasks(self) -> List[Dict[str, Any]]:
        """サーバント向けタスク配布"""
        tasks = []
        
        # 学習タスクの生成
        for sage_type, sage in self.sages.items():
            performance = await sage.evaluate_performance()
            
            # パフォーマンスが低い場合はタスク生成
            if performance.get('efficiency', 1.0) < 0.7:
                tasks.append({
                    'task_id': f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'assigned_to': 'elder_servants',
                    'task_type': 'improve_sage_performance',
                    'target_sage': sage_type.value,
                    'priority': 'high',
                    'deadline': (datetime.now() + timedelta(days=1)).isoformat()
                })
        
        return tasks
    
    async def _persist_experience(self, experience: LearningExperience):
        """経験永続化"""
        try:
            conn = sqlite3.connect(self.config['database_path'])
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO learning_experiences 
                (experience_id, timestamp, domain, sage_type, input_data,
                 output_result, success, confidence, lessons_learned, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experience.experience_id,
                experience.timestamp.isoformat(),
                experience.domain.value,
                experience.sage_type.value,
                json.dumps(experience.input_data),
                json.dumps(experience.output_result),
                experience.success,
                experience.confidence,
                json.dumps(experience.lessons_learned),
                json.dumps(experience.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Experience persistence failed: {e}")
    
    async def _persist_knowledge_packet(self, packet: ElderKnowledgePacket):
        """知識パケット永続化"""
        try:
            conn = sqlite3.connect(self.config['database_path'])
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO knowledge_packets 
                (packet_id, created_at, source_elder, target_elder,
                 knowledge_type, content, propagation_path, absorption_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                packet.packet_id,
                packet.created_at.isoformat(),
                packet.source_elder,
                packet.target_elder,
                packet.knowledge_type,
                json.dumps(packet.content),
                json.dumps(packet.propagation_path),
                packet.absorption_rate
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Knowledge packet persistence failed: {e}")
    
    async def _persist_cross_domain_insight(self, insight: CrossDomainInsight):
        """クロスドメイン洞察永続化"""
        try:
            conn = sqlite3.connect(self.config['database_path'])
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO cross_domain_insights 
                (insight_id, created_at, source_domains, insight_type,
                 discovery, applicable_domains, confidence, evidence, potential_impact)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                insight.insight_id,
                insight.created_at.isoformat(),
                json.dumps([d.value for d in insight.source_domains]),
                insight.insight_type,
                insight.discovery,
                json.dumps([d.value for d in insight.applicable_domains]),
                insight.confidence,
                json.dumps(insight.evidence),
                json.dumps(insight.potential_impact)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Cross-domain insight persistence failed: {e}")
    
    async def _persist_meta_pattern(self, pattern: MetaLearningPattern):
        """メタパターン永続化"""
        try:
            conn = sqlite3.connect(self.config['database_path'])
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO meta_learning_patterns 
                (pattern_id, discovered_at, pattern_type, effectiveness,
                 applicable_strategies, success_conditions, failure_conditions, optimization_hints)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern.pattern_id,
                pattern.discovered_at.isoformat(),
                pattern.pattern_type,
                pattern.effectiveness,
                json.dumps([s.value for s in pattern.applicable_strategies]),
                json.dumps(pattern.success_conditions),
                json.dumps(pattern.failure_conditions),
                json.dumps(pattern.optimization_hints)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Meta pattern persistence failed: {e}")
    
    async def get_learning_status(self) -> Dict[str, Any]:
        """学習状況取得"""
        sage_status = {}
        for sage_type, sage in self.sages.items():
            sage_status[sage_type.value] = {
                'performance': await sage.evaluate_performance(),
                'knowledge_base_size': len(sage.knowledge_base),
                'learning_history_size': len(sage.learning_history)
            }
        
        return {
            'system_metrics': dict(self.system_metrics),
            'sage_status': sage_status,
            'cross_domain_insights': len(self.cross_domain_insights),
            'meta_patterns': len(self.meta_learning_patterns),
            'learning_efficiency': self._calculate_learning_efficiency(),
            'elder_hierarchy_status': {
                'grand_elder_reports': len(self.elder_hierarchy['grand_elder']['knowledge_packets']),
                'council_proposals': len(self.elder_hierarchy['council']['proposals']),
                'servant_tasks': len(self.elder_hierarchy['servants']['tasks'])
            }
        }
    
    def _calculate_learning_efficiency(self) -> float:
        """学習効率計算"""
        if self.system_metrics['total_experiences'] == 0:
            return 0.0
        
        # 成功経験の割合
        success_count = sum(1 for entry in self.learning_history 
                          if entry['experience'].success)
        
        efficiency = success_count / self.system_metrics['total_experiences']
        
        # クロスドメイン洞察とメタパターンによるボーナス
        insight_bonus = self.system_metrics['cross_domain_insights'] * 0.01
        meta_bonus = self.system_metrics['meta_patterns_discovered'] * 0.02
        
        return min(1.0, efficiency + insight_bonus + meta_bonus)


# 使用例
async def main():
    """メイン実行関数"""
    try:
        # システム初期化
        learning_system = AutonomousLearningSystem()
        
        print("🧠 Starting Autonomous Learning System with 4 Sages...")
        
        # 学習開始（バックグラウンド）
        learning_task = asyncio.create_task(learning_system.start_learning())
        
        # サンプル経験投稿
        print("\n📝 Submitting sample learning experiences...")
        
        # ナレッジ賢者の経験
        await learning_system.submit_experience(
            domain=LearningDomain.KNOWLEDGE,
            sage_type=SageType.KNOWLEDGE,
            input_data={'query': 'pgvector integration', 'context': 'elders guild'},
            output_result={'patterns': ['vector_search', 'knowledge_graph'], 'quality': 0.9},
            success=True,
            confidence=0.9,
            lessons_learned=['Vector embeddings improve search quality']
        )
        
        # タスク賢者の経験
        await learning_system.submit_experience(
            domain=LearningDomain.TASK,
            sage_type=SageType.TASK,
            input_data={'task': 'optimize_execution', 'complexity': 'high'},
            output_result={'optimization': 'parallel_processing', 'speedup': 2.5},
            success=True,
            confidence=0.85,
            lessons_learned=['Parallel processing effective for complex tasks']
        )
        
        # インシデント賢者の経験
        await learning_system.submit_experience(
            domain=LearningDomain.INCIDENT,
            sage_type=SageType.INCIDENT,
            input_data={'anomaly': 'high_cpu', 'severity': 'critical'},
            output_result={'action': 'auto_scaling', 'prevented': True},
            success=True,
            confidence=0.95,
            lessons_learned=['Proactive scaling prevents incidents']
        )
        
        # RAG賢者の経験
        await learning_system.submit_experience(
            domain=LearningDomain.SEARCH,
            sage_type=SageType.RAG,
            input_data={'search_type': 'semantic', 'query_complexity': 'high'},
            output_result={'relevance': 0.92, 'response_time': 150},
            success=True,
            confidence=0.88,
            lessons_learned=['Semantic search handles complex queries well']
        )
        
        # 少し待機
        await asyncio.sleep(5)
        
        # 学習状況確認
        print("\n📊 Checking learning status...")
        status = await learning_system.get_learning_status()
        
        print(f"\n🎯 System Metrics:")
        print(f"  Total Experiences: {status['system_metrics']['total_experiences']}")
        print(f"  Knowledge Packets Exchanged: {status['system_metrics']['knowledge_packets_exchanged']}")
        print(f"  Cross-Domain Insights: {status['cross_domain_insights']}")
        print(f"  Meta Patterns: {status['meta_patterns']}")
        print(f"  Learning Efficiency: {status['learning_efficiency']:.2f}")
        
        print(f"\n🧙‍♂️ Sage Status:")
        for sage_type, sage_status in status['sage_status'].items():
            print(f"  {sage_type}:")
            print(f"    Knowledge Base: {sage_status['knowledge_base_size']} items")
            print(f"    Performance: {sage_status['performance']}")
        
        print(f"\n🏛️ Elder Hierarchy Integration:")
        print(f"  Grand Elder Reports: {status['elder_hierarchy_status']['grand_elder_reports']}")
        print(f"  Council Proposals: {status['elder_hierarchy_status']['council_proposals']}")
        print(f"  Servant Tasks: {status['elder_hierarchy_status']['servant_tasks']}")
        
        # 停止
        await learning_system.stop_learning()
        learning_task.cancel()
        
        print("\n🎉 Autonomous Learning System Phase 2 demonstration completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())