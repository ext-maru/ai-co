#!/usr/bin/env python3
"""
🧙‍♂️ Four Sages Quality Bridge
4賢者と品質システムの連携ブリッジ

Features:
- ナレッジ賢者: 品質パターン・ベストプラクティス管理
- インシデント賢者: 品質問題の即座対応・記録
- タスク賢者: 品質改善タスクの優先順位管理
- RAG賢者: 類似問題・解決策の高速検索
"""

import asyncio
import logging
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

# Add project root to path
sys.path.insert(0, '/home/aicompany/ai_co')

from libs.elders_code_quality_engine import (
    EldersCodeQualityEngine,
    BugLearningCase,
    QualityPattern
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QualityIncident:
    """品質インシデント構造"""
    incident_id: str
    severity: str  # critical, high, medium, low
    category: str  # iron_will_violation, quality_score_low, security_risk
    file_path: str
    description: str
    quality_score: float
    violations: List[Dict]
    suggested_actions: List[str]
    timestamp: datetime
    
@dataclass
class QualityTask:
    """品質改善タスク構造"""
    task_id: str
    title: str
    description: str
    priority: str  # critical, high, medium, low
    estimated_effort: int  # minutes
    files_affected: List[str]
    improvement_impact: float
    created_at: datetime
    assigned_sage: str
    
@dataclass
class QualityKnowledge:
    """品質知識構造"""
    knowledge_id: str
    title: str
    content: str
    category: str  # pattern, practice, guide, warning
    confidence_score: float
    usage_count: int
    effectiveness_rating: float
    tags: List[str]
    sage_source: str

class KnowledgeSageQualityBridge:
    """📚 ナレッジ賢者品質ブリッジ"""
    
    def __init__(self, quality_engine):
        self.quality_engine = quality_engine
        self.knowledge_base = []
        self.patterns_cache = {}
        
    async def store_quality_pattern(self, pattern: QualityPattern, context: Dict = None) -> str:
        """品質パターンをナレッジベースに保存"""
        try:
            # 品質エンジンに保存
            pattern_uuid = await self.quality_engine.learn_quality_pattern(pattern)
            
            # ナレッジ賢者用の知識として記録
            knowledge = QualityKnowledge(
                knowledge_id=pattern_uuid,
                title=pattern.pattern_name,
                content=f"Pattern: {pattern.description}\nBefore: {pattern.problematic_code}\nAfter: {pattern.improved_code}",
                category="pattern",
                confidence_score=pattern.improvement_score / 100.0,
                usage_count=0,
                effectiveness_rating=0.0,
                tags=pattern.tags + ["quality_pattern"],
                sage_source="knowledge_sage"
            )
            
            self.knowledge_base.append(knowledge)
            self.patterns_cache[pattern.pattern_type] = self.patterns_cache.get(pattern.pattern_type, []) + [pattern]
            
            logger.info(f"📚 Knowledge Sage stored quality pattern: {pattern.pattern_name}")
            return pattern_uuid
            
        except Exception as e:
            logger.error(f"❌ Knowledge Sage failed to store pattern: {e}")
            raise
            
    async def retrieve_best_practices(self, category: str = None) -> List[QualityKnowledge]:
        """ベストプラクティス取得"""
        if category:
            return [k for k in self.knowledge_base if k.category == category]
        return [k for k in self.knowledge_base if k.category in ["pattern", "practice"]]
        
    async def generate_quality_guidance(self, file_analysis: Dict) -> List[str]:
        """品質ガイダンス生成"""
        guidance = []
        quality_score = file_analysis.get('quality_score', 0)
        issues = file_analysis.get('issues', [])
        
        # 品質スコア別ガイダンス
        if quality_score < 50:
            guidance.append("🚨 Critical quality issues detected. Immediate refactoring required.")
            guidance.append("💡 Focus on reducing complexity and adding proper error handling.")
        elif quality_score < 70:
            guidance.append("⚠️ Quality improvements needed. Consider following Elder Guild standards.")
            guidance.append("📚 Review knowledge base for applicable patterns.")
        
        # 問題別ガイダンス
        for issue in issues:
            issue_type = issue.get('type', '')
            if issue_type == 'anti_pattern':
                pattern_name = issue.get('name', '')
                if pattern_name in self.patterns_cache:
                    guidance.append(f"🎯 Apply {pattern_name} improvement pattern from knowledge base.")
                    
        return guidance

class IncidentSageQualityBridge:
    """🚨 インシデント賢者品質ブリッジ"""
    
    def __init__(self, quality_engine):
        self.quality_engine = quality_engine
        self.incident_history = []
        self.severity_thresholds = {
            'critical': 90,  # Iron Will violations, security risks
            'high': 70,      # Quality score < 50
            'medium': 40,    # Quality score < 70
            'low': 10        # Minor issues
        }
        
    async def detect_quality_incident(self, file_analysis: Dict, file_path: str) -> Optional[QualityIncident]:
        """品質インシデント検出"""
        quality_score = file_analysis.get('quality_score', 100)
        iron_will = file_analysis.get('iron_will_compliance', True)
        bug_risks = file_analysis.get('bug_risks', [])
        issues = file_analysis.get('issues', [])
        
        # インシデントレベル判定
        incident = None
        
        # Critical: Iron Will violations
        if not iron_will:
            incident = QualityIncident(
                incident_id=f"QI_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(file_path) % 10000}",
                severity='critical',
                category='iron_will_violation',
                file_path=file_path,
                description='Iron Will compliance violation detected',
                quality_score=quality_score,
                violations=[{'type': 'iron_will', 'description': 'Workaround/TODO comments found'}],
                suggested_actions=[
                    'Remove all TODO/FIXME comments',
                    'Complete all temporary implementations',
                    'Follow Elder Guild no-workaround policy'
                ],
                timestamp=datetime.now()
            )
            
        # Critical: High security risks
        elif any(risk.get('risk_level', 0) > 8 for risk in bug_risks):
            high_risks = [risk for risk in bug_risks if risk.get('risk_level', 0) > 8]
            incident = QualityIncident(
                incident_id=f"QI_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(file_path) % 10000}",
                severity='critical',
                category='security_risk',
                file_path=file_path,
                description='Critical security vulnerabilities detected',
                quality_score=quality_score,
                violations=[{'type': 'security', 'risks': high_risks}],
                suggested_actions=[
                    'Fix security vulnerabilities immediately',
                    'Review code for injection attacks',
                    'Add input validation and sanitization'
                ],
                timestamp=datetime.now()
            )
            
        # High: Very low quality score
        elif quality_score < 50:
            incident = QualityIncident(
                incident_id=f"QI_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(file_path) % 10000}",
                severity='high',
                category='quality_score_low',
                file_path=file_path,
                description=f'Quality score critically low: {quality_score:.1f}/100',
                quality_score=quality_score,
                violations=[{'type': 'quality', 'issues': issues}],
                suggested_actions=[
                    'Refactor complex functions',
                    'Add proper documentation',
                    'Improve error handling',
                    'Follow coding standards'
                ],
                timestamp=datetime.now()
            )
            
        if incident:
            self.incident_history.append(incident)
            await self.escalate_incident(incident)
            
        return incident
        
    async def escalate_incident(self, incident: QualityIncident):
        """インシデント エスカレーション"""
        logger.warning(f"🚨 Quality incident escalated: {incident.severity} - {incident.description}")
        
        # Critical/High incidents require immediate action
        if incident.severity in ['critical', 'high']:
            await self.trigger_immediate_response(incident)
            
    async def trigger_immediate_response(self, incident: QualityIncident):
        """即座対応トリガー"""
        logger.critical(f"🔥 Immediate response required for: {incident.file_path}")
        
        # Auto-create improvement task
        if hasattr(self, 'task_sage_bridge'):
            await self.task_sage_bridge.create_quality_task_from_incident(incident)
            
    async def get_incident_statistics(self) -> Dict:
        """インシデント統計"""
        if not self.incident_history:
            return {'total': 0, 'by_severity': {}, 'by_category': {}}
            
        stats = {
            'total': len(self.incident_history),
            'by_severity': {},
            'by_category': {},
            'recent_incidents': len([i for i in self.incident_history 
                                   if (datetime.now() - i.timestamp).days < 7])
        }
        
        for incident in self.incident_history:
            # By severity
            severity = incident.severity
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
            
            # By category
            category = incident.category
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
        return stats

class TaskSageQualityBridge:
    """📋 タスク賢者品質ブリッジ"""
    
    def __init__(self, quality_engine):
        self.quality_engine = quality_engine
        self.quality_tasks = []
        self.priority_matrix = {
            'critical': {'weight': 100, 'sla_hours': 2},
            'high': {'weight': 75, 'sla_hours': 8},
            'medium': {'weight': 50, 'sla_hours': 24},
            'low': {'weight': 25, 'sla_hours': 72}
        }
        
    async def create_quality_task_from_incident(self, incident: QualityIncident) -> QualityTask:
        """インシデントから品質タスク作成"""
        task = QualityTask(
            task_id=f"QT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.quality_tasks)}",
            title=f"Fix {incident.category}: {incident.file_path}",
            description=f"Resolve quality incident: {incident.description}",
            priority=incident.severity,
            estimated_effort=self._estimate_effort(incident),
            files_affected=[incident.file_path],
            improvement_impact=self._calculate_improvement_impact(incident),
            created_at=datetime.now(),
            assigned_sage="incident_sage"
        )
        
        self.quality_tasks.append(task)
        logger.info(f"📋 Task Sage created quality task: {task.task_id}")
        return task
        
    async def prioritize_quality_tasks(self) -> List[QualityTask]:
        """品質タスク優先順位付け"""
        def priority_score(task):
            base_weight = self.priority_matrix.get(task.priority, {}).get('weight', 0)
            impact_bonus = task.improvement_impact * 10
            urgency_bonus = max(0, 100 - (datetime.now() - task.created_at).days * 5)
            return base_weight + impact_bonus + urgency_bonus
            
        return sorted(self.quality_tasks, key=priority_score, reverse=True)
        
    async def create_batch_improvement_plan(self, file_analyses: List[Dict]) -> Dict:
        """一括改善計画作成"""
        plan = {
            'total_files': len(file_analyses),
            'improvement_tasks': [],
            'estimated_total_effort': 0,
            'priority_distribution': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        }
        
        for analysis in file_analyses:
            if analysis.get('quality_score', 100) < 70:
                priority = self._determine_task_priority(analysis)
                effort = self._estimate_effort_from_analysis(analysis)
                
                task = {
                    'file': analysis.get('file_path', 'unknown'),
                    'priority': priority,
                    'effort_minutes': effort,
                    'improvements_needed': len(analysis.get('issues', [])),
                    'current_score': analysis.get('quality_score', 0)
                }
                
                plan['improvement_tasks'].append(task)
                plan['estimated_total_effort'] += effort
                plan['priority_distribution'][priority] += 1
                
        return plan
        
    def _estimate_effort(self, incident: QualityIncident) -> int:
        """作業量見積もり（分）"""
        base_effort = {
            'critical': 120,  # 2 hours
            'high': 60,       # 1 hour
            'medium': 30,     # 30 minutes
            'low': 15         # 15 minutes
        }
        
        effort = base_effort.get(incident.severity, 30)
        
        # 違反数に応じて調整
        violation_count = len(incident.violations)
        effort += violation_count * 10
        
        return effort
        
    def _calculate_improvement_impact(self, incident: QualityIncident) -> float:
        """改善インパクト計算"""
        # 品質スコアが低いほど改善インパクトが高い
        quality_impact = max(0, (100 - incident.quality_score) / 100)
        
        # 重要度による重み付け
        severity_weight = {
            'critical': 1.0,
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
        
        return quality_impact * severity_weight.get(incident.severity, 0.5)
        
    def _determine_task_priority(self, analysis: Dict) -> str:
        """タスク優先度決定"""
        quality_score = analysis.get('quality_score', 100)
        iron_will = analysis.get('iron_will_compliance', True)
        bug_risks = analysis.get('bug_risks', [])
        
        if not iron_will:
            return 'critical'
        elif any(risk.get('risk_level', 0) > 7 for risk in bug_risks):
            return 'critical'
        elif quality_score < 50:
            return 'high'
        elif quality_score < 70:
            return 'medium'
        else:
            return 'low'
            
    def _estimate_effort_from_analysis(self, analysis: Dict) -> int:
        """分析結果から作業量見積もり"""
        base = 30  # 30 minutes base
        
        issues = len(analysis.get('issues', []))
        suggestions = len(analysis.get('suggestions', []))
        complexity = analysis.get('complexity_score', 1)
        
        # 問題数と複雑度に基づく調整
        effort = base + (issues * 5) + (suggestions * 3) + (complexity * 2)
        
        return min(effort, 180)  # Maximum 3 hours per file

class RAGSageQualityBridge:
    """🔍 RAG賢者品質ブリッジ"""
    
    def __init__(self, quality_engine):
        self.quality_engine = quality_engine
        self.search_cache = {}
        self.recommendation_engine = None
        
    async def search_similar_quality_issues(self, current_analysis: Dict) -> List[Dict]:
        """類似品質問題検索"""
        try:
            # 現在の分析からテキスト生成
            file_content = current_analysis.get('original_code', '')
            issues = current_analysis.get('issues', [])
            issue_text = ' '.join([issue.get('description', '') for issue in issues])
            
            search_text = f"{file_content} {issue_text}"
            
            # キャッシュチェック
            cache_key = hash(search_text) % 10000
            if cache_key in self.search_cache:
                return self.search_cache[cache_key]
                
            # 品質エンジンでベクトル検索
            if hasattr(self.quality_engine, 'embedder'):
                embedding = await self.quality_engine.embedder.generate_embedding(search_text)
                similar_bugs = await self.quality_engine.db.search_similar_bugs(embedding, 0.7, 10)
                similar_patterns = await self.quality_engine.db.search_similar_patterns(embedding, 0.7, 10)
                
                results = {
                    'similar_bugs': similar_bugs,
                    'similar_patterns': similar_patterns,
                    'recommendations': await self._generate_recommendations(similar_bugs, similar_patterns)
                }
                
                self.search_cache[cache_key] = results
                return results
            else:
                return {'similar_bugs': [], 'similar_patterns': [], 'recommendations': []}
                
        except Exception as e:
            logger.error(f"❌ RAG Sage search failed: {e}")
            return {'similar_bugs': [], 'similar_patterns': [], 'recommendations': []}
            
    async def _generate_recommendations(self, similar_bugs: List, similar_patterns: List) -> List[str]:
        """推奨事項生成"""
        recommendations = []
        
        # 類似バグからの推奨
        for bug in similar_bugs[:3]:
            if bug.get('similarity', 0) > 0.8:
                prevention_tips = bug.get('prevention_tips', [])
                for tip in prevention_tips:
                    if tip not in recommendations:
                        recommendations.append(f"🐛 Prevention: {tip}")
                        
        # 類似パターンからの推奨
        for pattern in similar_patterns[:3]:
            if pattern.get('similarity', 0) > 0.8:
                rec = f"🎯 Apply pattern: {pattern.get('pattern_name', 'Unknown')}"
                if rec not in recommendations:
                    recommendations.append(rec)
                    
        return recommendations
        
    async def get_contextual_guidance(self, file_path: str, quality_issues: List[Dict]) -> Dict:
        """コンテキスト別ガイダンス"""
        guidance = {
            'file_specific': [],
            'project_wide': [],
            'best_practices': [],
            'learning_resources': []
        }
        
        # ファイル種別別ガイダンス
        if 'test_' in file_path:
            guidance['file_specific'].append("🧪 Test file - Focus on coverage and clear assertions")
        elif 'api' in file_path.lower():
            guidance['file_specific'].append("🌐 API file - Ensure proper validation and error handling")
        elif 'model' in file_path.lower():
            guidance['file_specific'].append("📊 Model file - Focus on data validation and type safety")
            
        # 問題別ガイダンス
        for issue in quality_issues:
            issue_type = issue.get('name', '')
            if 'complexity' in issue_type.lower():
                guidance['best_practices'].append("📐 Break down complex functions into smaller units")
            elif 'documentation' in issue_type.lower():
                guidance['best_practices'].append("📚 Add comprehensive docstrings and type hints")
                
        return guidance

class FourSagesQualityOrchestrator:
    """🏛️ 4賢者品質オーケストレーター"""
    
    def __init__(self):
        self.quality_engine = None
        self.knowledge_sage = None
        self.incident_sage = None
        self.task_sage = None
        self.rag_sage = None
        
    async def initialize(self):
        """4賢者品質システム初期化"""
        # 品質エンジン初期化
        db_params = {
            'host': 'localhost',
            'database': 'elders_guild_pgvector',
            'user': 'postgres',
            'password': ''
        }
        
        self.quality_engine = EldersCodeQualityEngine(db_params)
        await self.quality_engine.initialize()
        
        # 各賢者ブリッジ初期化
        self.knowledge_sage = KnowledgeSageQualityBridge(self.quality_engine)
        self.incident_sage = IncidentSageQualityBridge(self.quality_engine)
        self.task_sage = TaskSageQualityBridge(self.quality_engine)
        self.rag_sage = RAGSageQualityBridge(self.quality_engine)
        
        # 相互参照設定
        self.incident_sage.task_sage_bridge = self.task_sage
        
        logger.info("🏛️ Four Sages Quality System initialized")
        
    async def shutdown(self):
        """4賢者品質システム終了"""
        if self.quality_engine:
            await self.quality_engine.shutdown()
        logger.info("🔒 Four Sages Quality System shutdown")
        
    async def comprehensive_quality_analysis(self, file_path: str) -> Dict:
        """包括的品質分析（4賢者連携）"""
        try:
            # 基本品質分析
            analysis_result = await self.quality_engine.analyze_file(file_path)
            
            if 'error' in analysis_result:
                return {'error': analysis_result['error']}
                
            analysis = analysis_result.get('analysis', {})
            
            # 各賢者による分析
            four_sages_analysis = {
                'basic_analysis': analysis,
                'knowledge_sage_guidance': await self.knowledge_sage.generate_quality_guidance(analysis),
                'incident_sage_alert': await self.incident_sage.detect_quality_incident(analysis, file_path),
                'task_sage_planning': None,
                'rag_sage_insights': await self.rag_sage.search_similar_quality_issues(analysis),
                'orchestrated_recommendations': []
            }
            
            # インシデントがあればタスク作成
            if four_sages_analysis['incident_sage_alert']:
                task = await self.task_sage.create_quality_task_from_incident(
                    four_sages_analysis['incident_sage_alert']
                )
                four_sages_analysis['task_sage_planning'] = asdict(task)
                
            # 統合推奨事項生成
            four_sages_analysis['orchestrated_recommendations'] = await self._generate_orchestrated_recommendations(
                four_sages_analysis
            )
            
            return four_sages_analysis
            
        except Exception as e:
            logger.error(f"❌ Four Sages analysis failed: {e}")
            return {'error': str(e)}
            
    async def _generate_orchestrated_recommendations(self, analysis: Dict) -> List[str]:
        """4賢者統合推奨事項生成"""
        recommendations = []
        
        # Knowledge Sage からの提案
        knowledge_guidance = analysis.get('knowledge_sage_guidance', [])
        for guidance in knowledge_guidance:
            recommendations.append(f"📚 Knowledge: {guidance}")
            
        # Incident Sage からの警告
        incident = analysis.get('incident_sage_alert')
        if incident:
            for action in incident.suggested_actions:
                recommendations.append(f"🚨 Incident: {action}")
                
        # Task Sage からの計画
        task_planning = analysis.get('task_sage_planning')
        if task_planning:
            recommendations.append(f"📋 Task: {task_planning['description']} (Est: {task_planning['estimated_effort']}min)")
            
        # RAG Sage からの洞察
        rag_insights = analysis.get('rag_sage_insights', {})
        rag_recommendations = rag_insights.get('recommendations', [])
        for rec in rag_recommendations:
            recommendations.append(f"🔍 RAG: {rec}")
            
        return recommendations
        
    async def project_wide_quality_assessment(self, file_paths: List[str]) -> Dict:
        """プロジェクト全体品質評価"""
        assessment = {
            'total_files': len(file_paths),
            'analyzed_files': 0,
            'quality_distribution': {'excellent': 0, 'good': 0, 'needs_improvement': 0, 'poor': 0},
            'incident_summary': {},
            'task_summary': {},
            'knowledge_gaps': [],
            'overall_recommendations': []
        }
        
        for file_path in file_paths:
            try:
                analysis = await self.comprehensive_quality_analysis(file_path)
                if 'error' not in analysis:
                    assessment['analyzed_files'] += 1
                    
                    # 品質分布
                    quality_score = analysis['basic_analysis'].get('quality_score', 0)
                    if quality_score >= 85:
                        assessment['quality_distribution']['excellent'] += 1
                    elif quality_score >= 70:
                        assessment['quality_distribution']['good'] += 1
                    elif quality_score >= 50:
                        assessment['quality_distribution']['needs_improvement'] += 1
                    else:
                        assessment['quality_distribution']['poor'] += 1
                        
            except Exception as e:
                logger.warning(f"⚠️ Failed to analyze {file_path}: {e}")
                
        # インシデント・タスク統計
        assessment['incident_summary'] = await self.incident_sage.get_incident_statistics()
        assessment['task_summary'] = {
            'total_tasks': len(self.task_sage.quality_tasks),
            'by_priority': {}
        }
        
        for task in self.task_sage.quality_tasks:
            priority = task.priority
            assessment['task_summary']['by_priority'][priority] = \
                assessment['task_summary']['by_priority'].get(priority, 0) + 1
                
        return assessment

# グローバルインスタンス
_four_sages_orchestrator = None

async def get_four_sages_quality_orchestrator():
    """4賢者品質オーケストレーター取得"""
    global _four_sages_orchestrator
    if _four_sages_orchestrator is None:
        _four_sages_orchestrator = FourSagesQualityOrchestrator()
        await _four_sages_orchestrator.initialize()
    return _four_sages_orchestrator

# 便利関数
async def four_sages_analyze_file(file_path: str) -> Dict:
    """4賢者ファイル分析便利関数"""
    orchestrator = await get_four_sages_quality_orchestrator()
    return await orchestrator.comprehensive_quality_analysis(file_path)

async def four_sages_project_assessment(file_paths: List[str]) -> Dict:
    """4賢者プロジェクト評価便利関数"""
    orchestrator = await get_four_sages_quality_orchestrator()
    return await orchestrator.project_wide_quality_assessment(file_paths)

if __name__ == "__main__":
    async def test_four_sages():
        """4賢者テスト"""
        orchestrator = FourSagesQualityOrchestrator()
        await orchestrator.initialize()
        
        try:
            # テストファイル作成
            test_file = "/tmp/test_four_sages.py"
            with open(test_file, 'w') as f:
                f.write('''
def bad_function():
    # TODO: fix this later
    magic_number = 42
    try:
        result = eval("1 + 1")
    except:
        pass
    return magic_number
''')
            
            # 4賢者分析実行
            result = await orchestrator.comprehensive_quality_analysis(test_file)
            
            print("🏛️ Four Sages Quality Analysis:")
            print(json.dumps(result, indent=2, default=str))
            
        finally:
            await orchestrator.shutdown()
            
    asyncio.run(test_four_sages())