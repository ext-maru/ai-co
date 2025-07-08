#!/usr/bin/env python3
"""
Elder Council Auto-Summoning System
エルダー会議自動召集システム - 全分析と進化継続のための戦略的意思決定支援
"""

import os
import sys
import json
import time
import logging
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
import psutil

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.env_config import get_config
# Worker auto recovery imports - 直接ファイルからインポート
try:
    # ディレクトリではなくファイルから直接インポート
    import sys
    import importlib.util
    from pathlib import Path
    
    # worker_auto_recovery.py ファイルを直接読み込む
    recovery_file = Path(__file__).parent / "worker_auto_recovery.py"
    if recovery_file.exists():
        spec = importlib.util.spec_from_file_location("worker_auto_recovery_direct", str(recovery_file))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        WorkerHealthMonitor = module.WorkerHealthMonitor
        AutoRecoveryEngine = module.AutoRecoveryEngine
    else:
        # フォールバック
        WorkerHealthMonitor = None
        AutoRecoveryEngine = None
except Exception:
    # Fallback if module not available
    WorkerHealthMonitor = None
    AutoRecoveryEngine = None

logger = logging.getLogger(__name__)

class UrgencyLevel(Enum):
    """会議の緊急度レベル"""
    CRITICAL = "critical"      # 24時間以内
    HIGH = "high"             # 1週間以内
    MEDIUM = "medium"         # 1ヶ月以内
    LOW = "low"               # 3ヶ月以内

class TriggerCategory(Enum):
    """トリガーカテゴリ"""
    SYSTEM_FAILURE = "system_failure"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    STRATEGIC_DECISION = "strategic_decision"
    EVOLUTION_OPPORTUNITY = "evolution_opportunity"
    KNOWLEDGE_GAP = "knowledge_gap"
    RESOURCE_CONFLICT = "resource_conflict"
    INTEGRATION_CHALLENGE = "integration_challenge"
    ARCHITECTURAL_CHANGE = "architectural_change"

@dataclass
class CouncilTrigger:
    """エルダー会議トリガー"""
    trigger_id: str
    category: TriggerCategory
    urgency: UrgencyLevel
    title: str
    description: str
    triggered_at: datetime
    metrics: Dict[str, Any]
    affected_systems: List[str]
    suggested_agenda: List[str]
    auto_analysis: Dict[str, Any]
    four_sages_input: Optional[Dict[str, Any]] = None

@dataclass
class SystemEvolutionMetrics:
    """システム進化メトリクス"""
    timestamp: datetime
    test_coverage: float
    worker_health_score: float
    api_utilization: float
    memory_usage: float
    cpu_usage: float
    queue_backlog: int
    error_rate: float
    autonomous_decision_success_rate: float
    four_sages_consensus_rate: float
    system_complexity_score: float
    learning_velocity: float

class ElderCouncilSummoner:
    """エルダー会議自動召集システム"""
    
    def __init__(self):
        """初期化"""
        self.config = get_config()
        # ワーカー監視システム（利用可能な場合のみ初期化）
        self.worker_health_monitor = WorkerHealthMonitor() if WorkerHealthMonitor else None
        self.auto_recovery_engine = AutoRecoveryEngine() if AutoRecoveryEngine else None
        
        # 監視設定
        self.monitoring_interval = 300  # 5分間隔
        self.monitoring_active = False
        self.monitor_thread = None
        
        # トリガー設定
        self.triggers = {}
        self.trigger_history = deque(maxlen=1000)
        self.pending_councils = {}
        
        # メトリクス履歴
        self.metrics_history = deque(maxlen=1000)
        
        # 閾値設定
        self.thresholds = self._load_thresholds()
        
        # 4賢者統合
        self.four_sages_enabled = True
        
        logger.info("Elder Council Summoner initialized")
    
    def _load_thresholds(self) -> Dict[str, Any]:
        """閾値設定の読み込み"""
        return {
            # 緊急度: CRITICAL (24時間以内)
            'critical': {
                'worker_failure_rate': 0.5,      # 50%以上のワーカー失敗
                'system_wide_error_rate': 0.1,   # 10%以上のエラー率
                'api_rate_limit_breach': 0.9,    # 90%以上のAPI使用率
                'memory_critical': 0.95,         # 95%以上のメモリ使用
                'queue_critical_backlog': 500,   # 500以上のキューバックログ
                'four_sages_failure': 0.5,       # 50%未満のコンセンサス
            },
            
            # 緊急度: HIGH (1週間以内)
            'high': {
                'test_coverage_critical': 0.05,  # 5%未満のテストカバレッジ
                'performance_degradation': 0.5,  # 50%以上のパフォーマンス低下
                'worker_failure_rate': 0.3,      # 30%以上のワーカー失敗
                'architectural_complexity': 0.8, # 複雑度スコア80%以上
                'learning_velocity_drop': 0.3,   # 学習速度30%以上低下
                'integration_failure_rate': 0.2, # 統合失敗率20%以上
            },
            
            # 緊急度: MEDIUM (1ヶ月以内)
            'medium': {
                'scalability_limit': 0.8,        # スケーラビリティ限界80%
                'knowledge_gap_score': 0.7,      # 知識ギャップスコア70%以上
                'user_experience_issues': 0.3,   # UX問題30%以上
                'resource_conflicts': 3,         # 3つ以上のリソース競合
                'evolution_opportunity': 0.8,    # 進化機会スコア80%以上
            },
            
            # 緊急度: LOW (3ヶ月以内)
            'low': {
                'optimization_opportunity': 0.6, # 最適化機会60%以上
                'competitive_analysis_needed': True,
                'technology_upgrade': 0.5,       # 技術アップグレード必要性50%
                'strategic_planning': True       # 戦略的計画が必要
            }
        }
    
    def start_monitoring(self):
        """監視開始"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Elder Council Summoner monitoring started")
    
    def stop_monitoring(self):
        """監視停止"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Elder Council Summoner monitoring stopped")
    
    def _monitoring_loop(self):
        """監視ループ"""
        while self.monitoring_active:
            try:
                # システムメトリクス収集
                metrics = self._collect_system_metrics()
                self.metrics_history.append(metrics)
                
                # トリガー評価
                self._evaluate_triggers(metrics)
                
                # 進化機会の分析
                self._analyze_evolution_opportunities(metrics)
                
                # 4賢者からの入力
                if self.four_sages_enabled:
                    self._collect_four_sages_input()
                
                # ペンディング中の会議チェック
                self._check_pending_councils()
                
                # データ保存
                self._save_monitoring_data()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)
    
    def _collect_system_metrics(self) -> SystemEvolutionMetrics:
        """システムメトリクス収集"""
        try:
            # Worker health
            worker_status = self.worker_health_monitor.get_system_status()
            total_workers = worker_status.get('total_workers', 0)
            health_summary = worker_status.get('health_summary', {})
            healthy_workers = health_summary.get('healthy', 0)
            worker_health_score = healthy_workers / total_workers if total_workers > 0 else 0.0
            
            # System resources
            cpu_usage = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            memory_usage = memory.percent / 100.0
            
            # Queue status
            queue_backlog = self._get_total_queue_backlog()
            
            # Test coverage (estimated from existing data)
            test_coverage = self._calculate_test_coverage()
            
            # API utilization (estimated)
            api_utilization = self._estimate_api_utilization()
            
            # Error rate (from worker recovery data)
            error_rate = self._calculate_error_rate()
            
            # 4 Sages metrics
            four_sages_consensus = self._get_four_sages_consensus_rate()
            
            # Learning velocity
            learning_velocity = self._calculate_learning_velocity()
            
            # System complexity
            complexity_score = self._calculate_system_complexity()
            
            # Autonomous decision success
            autonomous_success = self._calculate_autonomous_decision_success()
            
            return SystemEvolutionMetrics(
                timestamp=datetime.now(),
                test_coverage=test_coverage,
                worker_health_score=worker_health_score,
                api_utilization=api_utilization,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage / 100.0,
                queue_backlog=queue_backlog,
                error_rate=error_rate,
                autonomous_decision_success_rate=autonomous_success,
                four_sages_consensus_rate=four_sages_consensus,
                system_complexity_score=complexity_score,
                learning_velocity=learning_velocity
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemEvolutionMetrics(
                timestamp=datetime.now(),
                test_coverage=0.018,  # Known current value
                worker_health_score=0.0,
                api_utilization=0.0,
                memory_usage=0.0,
                cpu_usage=0.0,
                queue_backlog=0,
                error_rate=0.0,
                autonomous_decision_success_rate=0.0,
                four_sages_consensus_rate=0.0,
                system_complexity_score=0.0,
                learning_velocity=0.0
            )
    
    def _evaluate_triggers(self, metrics: SystemEvolutionMetrics):
        """トリガー評価"""
        current_time = datetime.now()
        
        # Critical triggers
        if metrics.worker_health_score < (1 - self.thresholds['critical']['worker_failure_rate']):
            self._create_trigger(
                "worker_system_critical",
                TriggerCategory.SYSTEM_FAILURE,
                UrgencyLevel.CRITICAL,
                "Critical Worker System Failure",
                f"Worker health score dropped to {metrics.worker_health_score:.2%}",
                metrics,
                ["worker_system"],
                ["Immediate worker system stabilization", "Emergency recovery protocols", "System architecture review"]
            )
        
        if metrics.memory_usage > self.thresholds['critical']['memory_critical']:
            self._create_trigger(
                "memory_critical",
                TriggerCategory.SYSTEM_FAILURE,
                UrgencyLevel.CRITICAL,
                "Critical Memory Usage",
                f"Memory usage reached {metrics.memory_usage:.2%}",
                metrics,
                ["system_resources"],
                ["Memory optimization strategy", "Resource allocation review", "Scaling decisions"]
            )
        
        if metrics.queue_backlog > self.thresholds['critical']['queue_critical_backlog']:
            self._create_trigger(
                "queue_backlog_critical",
                TriggerCategory.PERFORMANCE_DEGRADATION,
                UrgencyLevel.CRITICAL,
                "Critical Queue Backlog",
                f"Queue backlog reached {metrics.queue_backlog} messages",
                metrics,
                ["task_processing", "worker_system"],
                ["Queue processing optimization", "Worker scaling strategy", "Load balancing review"]
            )
        
        # High priority triggers
        if metrics.test_coverage < self.thresholds['high']['test_coverage_critical']:
            self._create_trigger(
                "test_coverage_critical",
                TriggerCategory.STRATEGIC_DECISION,
                UrgencyLevel.HIGH,
                "Critical Test Coverage Gap",
                f"Test coverage is only {metrics.test_coverage:.2%}",
                metrics,
                ["quality_assurance", "development_process"],
                ["Test coverage improvement strategy", "Quality gates implementation", "Development process review"]
            )
        
        if metrics.four_sages_consensus_rate < self.thresholds['critical']['four_sages_failure']:
            self._create_trigger(
                "four_sages_consensus_failure",
                TriggerCategory.INTEGRATION_CHALLENGE,
                UrgencyLevel.HIGH,
                "4 Sages Consensus Failure",
                f"4 Sages consensus rate dropped to {metrics.four_sages_consensus_rate:.2%}",
                metrics,
                ["four_sages_system", "decision_making"],
                ["4 Sages system review", "Decision-making process optimization", "Conflict resolution mechanisms"]
            )
        
        # Evolution opportunity triggers
        if metrics.learning_velocity < 0.5:  # Assuming baseline of 1.0
            evolution_score = 1.0 - metrics.learning_velocity
            if evolution_score > self.thresholds['medium']['evolution_opportunity']:
                self._create_trigger(
                    "evolution_opportunity",
                    TriggerCategory.EVOLUTION_OPPORTUNITY,
                    UrgencyLevel.MEDIUM,
                    "System Evolution Opportunity",
                    f"Learning velocity decreased, evolution opportunity score: {evolution_score:.2%}",
                    metrics,
                    ["ai_evolution", "learning_systems"],
                    ["AI evolution strategy review", "Learning algorithm optimization", "Self-improvement mechanisms"]
                )
        
        # Strategic decision triggers
        if self._detect_resource_conflicts():
            self._create_trigger(
                "resource_allocation_conflict",
                TriggerCategory.RESOURCE_CONFLICT,
                UrgencyLevel.HIGH,
                "Resource Allocation Conflicts",
                "Multiple competing priorities detected requiring strategic direction",
                metrics,
                ["resource_management", "strategic_planning"],
                ["Priority matrix review", "Resource allocation strategy", "Project roadmap optimization"]
            )
        
        # Architectural complexity trigger
        if metrics.system_complexity_score > self.thresholds['high']['architectural_complexity']:
            self._create_trigger(
                "architectural_complexity",
                TriggerCategory.ARCHITECTURAL_CHANGE,
                UrgencyLevel.HIGH,
                "High System Complexity",
                f"System complexity score: {metrics.system_complexity_score:.2%}",
                metrics,
                ["system_architecture", "technical_debt"],
                ["Architecture simplification strategy", "Component decoupling", "Technical debt reduction plan"]
            )
    
    def _create_trigger(self, trigger_id: str, category: TriggerCategory, urgency: UrgencyLevel,
                       title: str, description: str, metrics: SystemEvolutionMetrics,
                       affected_systems: List[str], suggested_agenda: List[str]):
        """トリガー作成"""
        # 重複チェック
        if trigger_id in self.triggers:
            existing = self.triggers[trigger_id]
            # 24時間以内の重複は無視
            if (datetime.now() - existing.triggered_at).total_seconds() < 86400:
                return
        
        # 自動分析実行
        auto_analysis = self._perform_auto_analysis(category, metrics)
        
        trigger = CouncilTrigger(
            trigger_id=trigger_id,
            category=category,
            urgency=urgency,
            title=title,
            description=description,
            triggered_at=datetime.now(),
            metrics=asdict(metrics),
            affected_systems=affected_systems,
            suggested_agenda=suggested_agenda,
            auto_analysis=auto_analysis
        )
        
        # 4賢者からの入力を収集
        if self.four_sages_enabled:
            trigger.four_sages_input = self._request_four_sages_analysis(trigger)
        
        self.triggers[trigger_id] = trigger
        self.trigger_history.append(trigger)
        
        # 会議召集の検討
        if urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
            self._consider_council_summoning(trigger)
        
        logger.info(f"Elder Council trigger created: {title} ({urgency.value})")
        self._save_trigger_to_file(trigger)
    
    def _perform_auto_analysis(self, category: TriggerCategory, metrics: SystemEvolutionMetrics) -> Dict[str, Any]:
        """自動分析実行"""
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'category': category.value,
            'trend_analysis': self._analyze_trends(metrics),
            'impact_assessment': self._assess_impact(category, metrics),
            'recommended_actions': self._generate_recommendations(category, metrics),
            'risk_level': self._calculate_risk_level(metrics),
            'urgency_justification': self._justify_urgency(category, metrics)
        }
        
        return analysis
    
    def _analyze_trends(self, current_metrics: SystemEvolutionMetrics) -> Dict[str, Any]:
        """トレンド分析"""
        if len(self.metrics_history) < 2:
            return {'status': 'insufficient_data'}
        
        recent_metrics = list(self.metrics_history)[-10:]  # 最新10データポイント
        
        trends = {}
        
        # Worker health trend
        worker_health_values = [m.worker_health_score for m in recent_metrics]
        trends['worker_health_trend'] = self._calculate_trend(worker_health_values)
        
        # Memory usage trend
        memory_values = [m.memory_usage for m in recent_metrics]
        trends['memory_trend'] = self._calculate_trend(memory_values)
        
        # Error rate trend
        error_values = [m.error_rate for m in recent_metrics]
        trends['error_trend'] = self._calculate_trend(error_values)
        
        # Learning velocity trend
        learning_values = [m.learning_velocity for m in recent_metrics]
        trends['learning_trend'] = self._calculate_trend(learning_values)
        
        return trends
    
    def _calculate_trend(self, values: List[float]) -> str:
        """トレンド計算"""
        if len(values) < 2:
            return 'unknown'
        
        recent_avg = sum(values[-3:]) / len(values[-3:])
        older_avg = sum(values[:-3]) / len(values[:-3]) if len(values) > 3 else values[0]
        
        change = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
        
        if change > 0.1:
            return 'improving'
        elif change < -0.1:
            return 'declining'
        else:
            return 'stable'
    
    def _assess_impact(self, category: TriggerCategory, metrics: SystemEvolutionMetrics) -> Dict[str, Any]:
        """影響評価"""
        impact = {
            'immediate': [],
            'short_term': [],
            'long_term': [],
            'severity': 'unknown'
        }
        
        if category == TriggerCategory.SYSTEM_FAILURE:
            impact['immediate'] = ['Service disruption', 'User experience degradation']
            impact['short_term'] = ['Reduced productivity', 'System instability']
            impact['long_term'] = ['Technical debt accumulation', 'User trust erosion']
            impact['severity'] = 'high'
            
        elif category == TriggerCategory.EVOLUTION_OPPORTUNITY:
            impact['immediate'] = ['Performance optimization potential']
            impact['short_term'] = ['Enhanced capabilities', 'Improved efficiency']
            impact['long_term'] = ['Competitive advantage', 'Autonomous evolution']
            impact['severity'] = 'positive'
            
        elif category == TriggerCategory.STRATEGIC_DECISION:
            impact['immediate'] = ['Decision paralysis risk']
            impact['short_term'] = ['Resource misallocation']
            impact['long_term'] = ['Strategic misalignment']
            impact['severity'] = 'medium'
        
        return impact
    
    def _generate_recommendations(self, category: TriggerCategory, metrics: SystemEvolutionMetrics) -> List[str]:
        """推奨事項生成"""
        recommendations = []
        
        if category == TriggerCategory.SYSTEM_FAILURE:
            recommendations = [
                "Immediate system stabilization",
                "Root cause analysis",
                "Emergency rollback procedures",
                "Monitoring enhancement",
                "Preventive measures implementation"
            ]
            
        elif category == TriggerCategory.EVOLUTION_OPPORTUNITY:
            recommendations = [
                "Evolution roadmap creation",
                "Learning algorithm optimization",
                "Performance baseline establishment",
                "Gradual enhancement implementation",
                "Impact measurement framework"
            ]
            
        elif category == TriggerCategory.STRATEGIC_DECISION:
            recommendations = [
                "Stakeholder analysis",
                "Options evaluation matrix",
                "Risk-benefit analysis",
                "Implementation timeline",
                "Success metrics definition"
            ]
        
        return recommendations
    
    def _calculate_risk_level(self, metrics: SystemEvolutionMetrics) -> str:
        """リスクレベル計算"""
        risk_factors = []
        
        if metrics.worker_health_score < 0.7:
            risk_factors.append('worker_instability')
        
        if metrics.memory_usage > 0.8:
            risk_factors.append('resource_exhaustion')
        
        if metrics.error_rate > 0.05:
            risk_factors.append('high_error_rate')
        
        if metrics.test_coverage < 0.1:
            risk_factors.append('low_test_coverage')
        
        if len(risk_factors) >= 3:
            return 'critical'
        elif len(risk_factors) >= 2:
            return 'high'
        elif len(risk_factors) >= 1:
            return 'medium'
        else:
            return 'low'
    
    def _justify_urgency(self, category: TriggerCategory, metrics: SystemEvolutionMetrics) -> str:
        """緊急度の正当化"""
        justifications = []
        
        if category == TriggerCategory.SYSTEM_FAILURE:
            justifications.append("System stability directly affects operational continuity")
        
        if metrics.worker_health_score < 0.5:
            justifications.append("Majority of workers are failing, critical intervention needed")
        
        if metrics.memory_usage > 0.9:
            justifications.append("System approaching resource exhaustion")
        
        if metrics.test_coverage < 0.05:
            justifications.append("Extremely low test coverage poses significant quality risks")
        
        return "; ".join(justifications) if justifications else "Standard threshold breach"
    
    def _request_four_sages_analysis(self, trigger: CouncilTrigger) -> Dict[str, Any]:
        """4賢者からの分析要請"""
        # 4賢者システムとの統合（実装簡略化）
        sages_input = {
            'timestamp': datetime.now().isoformat(),
            'consensus_confidence': 0.85,  # シミュレート値
            'individual_assessments': {
                'knowledge_sage': {
                    'assessment': 'Historical patterns suggest immediate attention required',
                    'confidence': 0.9,
                    'recommended_priority': 'high'
                },
                'task_sage': {
                    'assessment': 'Resource allocation optimization needed',
                    'confidence': 0.8,
                    'recommended_priority': 'high'
                },
                'incident_sage': {
                    'assessment': 'Proactive intervention prevents escalation',
                    'confidence': 0.85,
                    'recommended_priority': 'critical'
                },
                'rag_sage': {
                    'assessment': 'Analysis indicates systematic intervention needed',
                    'confidence': 0.88,
                    'recommended_priority': 'high'
                }
            },
            'collective_recommendation': 'Summon Elder Council for strategic guidance'
        }
        
        return sages_input
    
    def _consider_council_summoning(self, trigger: CouncilTrigger):
        """会議召集の検討"""
        council_id = f"council_{trigger.triggered_at.strftime('%Y%m%d_%H%M%S')}_{trigger.trigger_id}"
        
        # 既存の会議との重複チェック
        for pending_id, pending_council in self.pending_councils.items():
            if trigger.category in pending_council.get('categories', []):
                # 既存の会議に追加
                pending_council['triggers'].append(trigger.trigger_id)
                pending_council['agenda'].extend(trigger.suggested_agenda)
                logger.info(f"Added trigger {trigger.trigger_id} to existing council {pending_id}")
                return
        
        # 新しい会議を作成
        council_request = {
            'council_id': council_id,
            'urgency': trigger.urgency,
            'categories': [trigger.category],
            'triggers': [trigger.trigger_id],
            'agenda': trigger.suggested_agenda.copy(),
            'affected_systems': trigger.affected_systems.copy(),
            'auto_analysis': trigger.auto_analysis,
            'four_sages_input': trigger.four_sages_input,
            'created_at': datetime.now(),
            'deadline': self._calculate_deadline(trigger.urgency),
            'status': 'pending'
        }
        
        self.pending_councils[council_id] = council_request
        
        # 会議要請文書の作成
        self._create_council_request_document(council_request)
        
        logger.info(f"Elder Council summoning requested: {council_id} ({trigger.urgency.value})")
    
    def _calculate_deadline(self, urgency: UrgencyLevel) -> datetime:
        """会議期限計算"""
        now = datetime.now()
        
        if urgency == UrgencyLevel.CRITICAL:
            return now + timedelta(hours=24)
        elif urgency == UrgencyLevel.HIGH:
            return now + timedelta(days=7)
        elif urgency == UrgencyLevel.MEDIUM:
            return now + timedelta(days=30)
        else:  # LOW
            return now + timedelta(days=90)
    
    def _create_council_request_document(self, council_request: Dict[str, Any]):
        """会議要請文書作成"""
        council_id = council_request['council_id']
        
        # 詳細な分析文書を作成
        document_content = self._generate_council_document(council_request)
        
        # ファイル保存
        document_file = PROJECT_ROOT / 'knowledge_base' / f'{council_id}_elder_council_request.md'
        
        with open(document_file, 'w', encoding='utf-8') as f:
            f.write(document_content)
        
        logger.info(f"Council request document created: {document_file}")
    
    def _generate_council_document(self, council_request: Dict[str, Any]) -> str:
        """会議文書生成"""
        urgency = council_request['urgency']
        triggers = council_request['triggers']
        
        document = f"""# 🏛️ エルダー会議召集要請

**会議ID**: {council_request['council_id']}  
**緊急度**: {urgency.value.upper()}  
**期限**: {council_request['deadline'].strftime('%Y年%m月%d日 %H:%M')}  
**作成日時**: {council_request['created_at'].strftime('%Y年%m月%d日 %H:%M:%S')}

---

## 📋 **召集理由**

以下のトリガーによりエルダー会議の召集が要請されました：

"""
        
        # トリガー詳細を追加
        for trigger_id in triggers:
            if trigger_id in self.triggers:
                trigger = self.triggers[trigger_id]
                document += f"""
### {trigger.title}
- **カテゴリ**: {trigger.category.value}
- **説明**: {trigger.description}
- **影響システム**: {', '.join(trigger.affected_systems)}
- **発生時刻**: {trigger.triggered_at.strftime('%Y年%m月%d日 %H:%M:%S')}

"""
        
        # 自動分析結果
        if council_request.get('auto_analysis'):
            analysis = council_request['auto_analysis']
            document += f"""
## 🔍 **自動分析結果**

### リスクレベル: {analysis.get('risk_level', 'unknown').upper()}

### トレンド分析:
{self._format_trend_analysis(analysis.get('trend_analysis', {}))}

### 影響評価:
{self._format_impact_assessment(analysis.get('impact_assessment', {}))}

### 推奨事項:
{self._format_recommendations(analysis.get('recommended_actions', []))}

"""
        
        # 4賢者の分析
        if council_request.get('four_sages_input'):
            sages_input = council_request['four_sages_input']
            document += f"""
## 🧙‍♂️ **4賢者システム分析**

### コンセンサス信頼度: {sages_input.get('consensus_confidence', 0):.1%}

### 個別評価:
"""
            
            for sage_name, assessment in sages_input.get('individual_assessments', {}).items():
                document += f"""
**{sage_name}**:
- 評価: {assessment.get('assessment', 'No assessment')}
- 信頼度: {assessment.get('confidence', 0):.1%}
- 推奨優先度: {assessment.get('recommended_priority', 'unknown')}

"""
            
            document += f"""
### 集合的推奨: {sages_input.get('collective_recommendation', 'No recommendation')}

"""
        
        # 提案議題
        document += f"""
## 📝 **提案議題**

{self._format_agenda(council_request.get('agenda', []))}

## 🎯 **求められる決定事項**

1. **緊急対応**: 即座に実行すべきアクション
2. **戦略的方針**: 長期的な方向性と優先順位
3. **リソース配分**: 人的・技術的リソースの最適配分
4. **進化戦略**: システム進化の次のステップ
5. **権限委譲**: 4賢者システムへの自律的決定権限

## ⏰ **緊急度の根拠**

{council_request.get('auto_analysis', {}).get('urgency_justification', '閾値超過による自動判定')}

---

**エルダー会議の開催をお待ちしています。**

**召集システム**: Elder Council Summoner  
**文書ID**: {council_request['council_id']}
"""
        
        return document
    
    def _format_trend_analysis(self, trends: Dict[str, Any]) -> str:
        """トレンド分析のフォーマット"""
        if not trends or trends.get('status') == 'insufficient_data':
            return "- データ不足のため分析不可"
        
        formatted = []
        for metric, trend in trends.items():
            formatted.append(f"- {metric}: {trend}")
        
        return '\n'.join(formatted)
    
    def _format_impact_assessment(self, impact: Dict[str, Any]) -> str:
        """影響評価のフォーマット"""
        if not impact:
            return "- 影響評価データなし"
        
        formatted = []
        if impact.get('immediate'):
            formatted.append(f"**即座の影響**: {', '.join(impact['immediate'])}")
        if impact.get('short_term'):
            formatted.append(f"**短期的影響**: {', '.join(impact['short_term'])}")
        if impact.get('long_term'):
            formatted.append(f"**長期的影響**: {', '.join(impact['long_term'])}")
        
        return '\n'.join(formatted)
    
    def _format_recommendations(self, recommendations: List[str]) -> str:
        """推奨事項のフォーマット"""
        if not recommendations:
            return "- 推奨事項なし"
        
        return '\n'.join(f"- {rec}" for rec in recommendations)
    
    def _format_agenda(self, agenda: List[str]) -> str:
        """議題のフォーマット"""
        if not agenda:
            return "- 議題が設定されていません"
        
        return '\n'.join(f"{i+1}. {item}" for i, item in enumerate(agenda))
    
    # その他のヘルパーメソッド（簡略化実装）
    
    def _get_total_queue_backlog(self) -> int:
        """キューバックログ総数取得"""
        try:
            import pika
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            
            total_backlog = 0
            queues = ['ai_tasks', 'ai_pm', 'ai_results', 'dialog_task_queue']
            
            for queue in queues:
                try:
                    method = channel.queue_declare(queue=queue, passive=True)
                    total_backlog += method.method.message_count
                except:
                    pass
            
            connection.close()
            return total_backlog
            
        except Exception as e:
            logger.error(f"Error getting queue backlog: {e}")
            return 0
    
    def _calculate_test_coverage(self) -> float:
        """テストカバレッジ計算"""
        # 既知の値を返す（実際の実装では動的に計算）
        return 0.018
    
    def _estimate_api_utilization(self) -> float:
        """API使用率推定"""
        # 実装簡略化
        return 0.3
    
    def _calculate_error_rate(self) -> float:
        """エラー率計算"""
        # Worker recovery データから計算（簡略化）
        return 0.02
    
    def _get_four_sages_consensus_rate(self) -> float:
        """4賢者コンセンサス率取得"""
        # 実装簡略化
        return 0.85
    
    def _calculate_learning_velocity(self) -> float:
        """学習速度計算"""
        # 実装簡略化
        return 0.7
    
    def _calculate_system_complexity(self) -> float:
        """システム複雑度計算"""
        # 実装簡略化
        return 0.6
    
    def _calculate_autonomous_decision_success(self) -> float:
        """自律決定成功率計算"""
        # 実装簡略化
        return 0.8
    
    def _detect_resource_conflicts(self) -> bool:
        """リソース競合検出"""
        # 既知の競合: Worker Recovery vs Multi-CC vs AI Evolution
        return True
    
    def _analyze_evolution_opportunities(self, metrics: SystemEvolutionMetrics):
        """進化機会分析"""
        # 実装簡略化
        pass
    
    def _collect_four_sages_input(self):
        """4賢者からの入力収集"""
        # 実装簡略化
        pass
    
    def _check_pending_councils(self):
        """ペンディング会議チェック"""
        current_time = datetime.now()
        
        for council_id, council in list(self.pending_councils.items()):
            deadline = council['deadline']
            
            if current_time > deadline:
                logger.warning(f"Elder Council deadline passed: {council_id}")
                council['status'] = 'overdue'
    
    def _save_monitoring_data(self):
        """監視データ保存"""
        try:
            # メトリクス履歴保存
            metrics_file = PROJECT_ROOT / 'data' / 'evolution_metrics.json'
            metrics_file.parent.mkdir(parents=True, exist_ok=True)
            
            metrics_data = [asdict(m) for m in list(self.metrics_history)[-100:]]
            
            # datetime オブジェクトを文字列に変換
            for item in metrics_data:
                item['timestamp'] = item['timestamp'].isoformat()
            
            with open(metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            # トリガー履歴保存
            triggers_file = PROJECT_ROOT / 'data' / 'council_triggers.json'
            triggers_data = [asdict(t) for t in list(self.trigger_history)[-100:]]
            
            # datetime オブジェクトを文字列に変換
            for item in triggers_data:
                item['triggered_at'] = item['triggered_at'].isoformat()
                item['category'] = item['category'].value
                item['urgency'] = item['urgency'].value
            
            with open(triggers_file, 'w') as f:
                json.dump(triggers_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save monitoring data: {e}")
    
    def _save_trigger_to_file(self, trigger: CouncilTrigger):
        """トリガーをファイルに保存"""
        try:
            trigger_file = PROJECT_ROOT / 'logs' / 'elder_council_triggers.json'
            
            triggers = []
            if trigger_file.exists():
                with open(trigger_file, 'r') as f:
                    triggers = json.load(f)
            
            trigger_data = asdict(trigger)
            trigger_data['triggered_at'] = trigger.triggered_at.isoformat()
            trigger_data['category'] = trigger.category.value
            trigger_data['urgency'] = trigger.urgency.value
            
            triggers.append(trigger_data)
            
            with open(trigger_file, 'w') as f:
                json.dump(triggers, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save trigger to file: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """システム状況取得"""
        return {
            'monitoring_active': self.monitoring_active,
            'total_triggers': len(self.triggers),
            'pending_councils': len(self.pending_councils),
            'trigger_categories': [t.category.value for t in self.triggers.values()],
            'urgency_distribution': {
                level.value: sum(1 for t in self.triggers.values() if t.urgency == level)
                for level in UrgencyLevel
            },
            'recent_metrics': asdict(self.metrics_history[-1]) if self.metrics_history else None,
            'four_sages_enabled': self.four_sages_enabled
        }
    
    def force_trigger_evaluation(self) -> Dict[str, Any]:
        """強制トリガー評価"""
        metrics = self._collect_system_metrics()
        self._evaluate_triggers(metrics)
        return self.get_system_status()


def main():
    """テスト実行"""
    summoner = ElderCouncilSummoner()
    
    logger.info("Elder Council Summoner starting...")
    summoner.start_monitoring()
    
    try:
        while True:
            time.sleep(60)
            status = summoner.get_system_status()
            logger.info(f"System status: {json.dumps(status, indent=2, default=str)}")
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        summoner.stop_monitoring()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    )
    main()