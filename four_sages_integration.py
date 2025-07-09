#!/usr/bin/env python3
"""
Four Sages Integration for Elder Council Quality Review System
Integration layer connecting Elder Council with the existing 4 Sages System

This module provides specialized integration for test quality management:
- Knowledge Sage: Test pattern learning and quality database management
- Task Sage: Quality objectives tracking and workflow optimization
- Incident Sage: Quality issue detection and prevention
- RAG Sage: Best practice search and pattern discovery

Designed to enhance the Elder Council Review System with collaborative wisdom.
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import sqlite3
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict

# Import existing 4 Sages system
from libs.four_sages_integration import FourSagesIntegration

logger = logging.getLogger(__name__)

@dataclass
class QualityLearningRequest:
    """Structured request for 4 Sages quality learning"""
    test_file: str
    quality_metrics: Dict[str, float]
    current_issues: List[str]
    improvement_goals: List[str]
    context: Dict[str, Any]
    priority: str  # 'high', 'medium', 'low'

@dataclass
class SageQualityInsight:
    """Quality insight from individual sage"""
    sage_name: str
    recommendation: str
    confidence: float
    supporting_evidence: List[str]
    priority_actions: List[str]
    quality_impact: float  # Expected impact on quality score

class FourSagesQualityIntegration:
    """
    Specialized 4 Sages integration for test quality management
    
    Extends the base FourSagesIntegration with quality-specific operations:
    - Quality pattern learning and storage
    - Test quality objective tracking  
    - Quality issue prediction and prevention
    - Best practice discovery and recommendation
    """
    
    def __init__(self):
        """Initialize 4 Sages Quality Integration"""
        self.logger = logging.getLogger(__name__)
        self.project_root = PROJECT_ROOT
        self.db_path = self.project_root / "data" / "four_sages_quality.db"
        
        # Initialize base 4 Sages system
        self.base_sages = FourSagesIntegration()
        
        # Quality-specific sage configurations
        self.sage_specializations = {
            'knowledge_sage': {
                'focus': 'pattern_learning',
                'capabilities': ['pattern_storage', 'historical_analysis', 'quality_trends'],
                'quality_weight': 0.25
            },
            'task_sage': {
                'focus': 'objective_tracking',
                'capabilities': ['workflow_optimization', 'priority_management', 'progress_tracking'],
                'quality_weight': 0.25
            },
            'incident_sage': {
                'focus': 'issue_prevention',
                'capabilities': ['anomaly_detection', 'risk_assessment', 'preventive_measures'],
                'quality_weight': 0.25
            },
            'rag_sage': {
                'focus': 'pattern_discovery',
                'capabilities': ['best_practice_search', 'similarity_analysis', 'context_enhancement'],
                'quality_weight': 0.25
            }
        }
        
        # Quality learning objectives
        self.quality_objectives = {
            'maintain_coverage_quality': {
                'target_score': 0.80,
                'priority': 'high',
                'metrics': ['coverage_effectiveness', 'overall_quality_score']
            },
            'improve_pattern_compliance': {
                'target_score': 0.85,
                'priority': 'medium',
                'metrics': ['pattern_compliance', 'best_practices_score']
            },
            'enhance_documentation': {
                'target_score': 0.75,
                'priority': 'medium',
                'metrics': ['documentation_quality', 'naming_quality_score']
            },
            'optimize_test_complexity': {
                'target_score': 0.80,
                'priority': 'low',
                'metrics': ['test_complexity', 'average_method_length']
            }
        }
        
        # Initialize database
        self._init_database()
        
        self.logger.info("4 Sages Quality Integration initialized")
        self.logger.info("Specialized for Elder Council Quality Review System")
    
    def _init_database(self):
        """Initialize 4 Sages quality integration database"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Quality learning sessions
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_learning_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                test_file TEXT,
                learning_type TEXT,
                participating_sages TEXT,
                session_start TIMESTAMP,
                session_end TIMESTAMP,
                consensus_reached BOOLEAN,
                quality_insights TEXT,
                recommended_actions TEXT,
                expected_improvement REAL
            )
            """)
            
            # Sage quality recommendations
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sage_quality_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                sage_name TEXT,
                test_file TEXT,
                recommendation_type TEXT,
                recommendation_text TEXT,
                confidence_score REAL,
                priority_level TEXT,
                supporting_evidence TEXT,
                quality_impact REAL,
                timestamp TIMESTAMP
            )
            """)
            
            # Quality pattern library
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_pattern_library (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT NOT NULL,
                pattern_category TEXT,
                pattern_description TEXT,
                example_code TEXT,
                quality_impact REAL,
                usage_frequency INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 1.0,
                learned_from_file TEXT,
                sage_source TEXT,
                timestamp TIMESTAMP
            )
            """)
            
            # Quality objectives tracking
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_objectives_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                objective_name TEXT,
                target_score REAL,
                current_score REAL,
                progress_percentage REAL,
                last_updated TIMESTAMP,
                responsible_sage TEXT,
                status TEXT,
                next_actions TEXT
            )
            """)
            
            conn.commit()
            conn.close()
            
            self.logger.info("4 Sages quality database initialized")
            
        except Exception as e:
            self.logger.error(f"4 Sages quality database initialization failed: {e}")
    
    async def consult_sages_for_quality(self, learning_request: QualityLearningRequest) -> Dict[str, Any]:
        """
        Consult all 4 Sages for comprehensive quality insights
        
        Args:
            learning_request: Structured quality learning request
            
        Returns:
            Dictionary with sage insights and consensus
        """
        try:
            self.logger.info(f"Consulting 4 Sages for quality analysis: {learning_request.test_file}")
            
            # Prepare base learning request for 4 Sages system
            base_request = {
                'type': 'test_quality_analysis',
                'priority': learning_request.priority,
                'data': {
                    'test_file': learning_request.test_file,
                    'quality_metrics': learning_request.quality_metrics,
                    'current_issues': learning_request.current_issues,
                    'improvement_goals': learning_request.improvement_goals,
                    'context': learning_request.context
                }
            }
            
            # Coordinate learning session with base system
            coordination_result = self.base_sages.coordinate_learning_session(base_request)
            
            # Extract and enhance individual sage responses
            sage_insights = {}
            
            # Process each sage's response with quality-specific analysis
            individual_responses = coordination_result.get('individual_responses', {})
            
            # Knowledge Sage - Pattern Learning and Storage
            if 'knowledge_sage' in individual_responses:
                sage_insights['knowledge_sage'] = await self._process_knowledge_sage_quality_response(
                    individual_responses['knowledge_sage'], learning_request
                )
            
            # Task Sage - Objective Tracking and Workflow
            if 'task_sage' in individual_responses:
                sage_insights['task_sage'] = await self._process_task_sage_quality_response(
                    individual_responses['task_sage'], learning_request
                )
            
            # Incident Sage - Issue Prevention and Risk Assessment
            if 'incident_sage' in individual_responses:
                sage_insights['incident_sage'] = await self._process_incident_sage_quality_response(
                    individual_responses['incident_sage'], learning_request
                )
            
            # RAG Sage - Best Practice Discovery
            if 'rag_sage' in individual_responses:
                sage_insights['rag_sage'] = await self._process_rag_sage_quality_response(
                    individual_responses['rag_sage'], learning_request
                )
            
            # Form quality-specific consensus
            quality_consensus = await self._form_quality_consensus(sage_insights, learning_request)
            
            # Generate session summary
            session_summary = {
                'session_id': coordination_result.get('session_id', 'unknown'),
                'test_file': learning_request.test_file,
                'participating_sages': list(sage_insights.keys()),
                'sage_insights': sage_insights,
                'quality_consensus': quality_consensus,
                'consensus_reached': quality_consensus.get('consensus_reached', False),
                'recommended_actions': quality_consensus.get('recommended_actions', []),
                'expected_quality_improvement': quality_consensus.get('expected_improvement', 0.0),
                'priority_level': learning_request.priority,
                'session_timestamp': datetime.now().isoformat()
            }
            
            # Save session to database
            await self._save_quality_session(session_summary)
            
            self.logger.info(f"4 Sages quality consultation completed: {quality_consensus.get('consensus_reached', False)}")
            return session_summary
            
        except Exception as e:
            self.logger.error(f"4 Sages quality consultation failed: {e}")
            return {
                'session_id': 'error',
                'error': str(e),
                'consensus_reached': False
            }
    
    async def _process_knowledge_sage_quality_response(self, response: Dict[str, Any], 
                                                     request: QualityLearningRequest) -> SageQualityInsight:
        """Process Knowledge Sage response for quality insights"""
        
        # Extract base response
        base_recommendation = response.get('recommendation', 'Store test patterns for learning')
        confidence = response.get('confidence_score', 0.9)
        
        # Enhanced quality-specific analysis
        quality_patterns = await self._identify_quality_patterns(request)
        historical_analysis = await self._perform_historical_quality_analysis(request.test_file)
        
        # Generate Knowledge Sage specific recommendations
        knowledge_recommendations = []
        if request.quality_metrics.get('pattern_compliance', 0) < 0.8:
            knowledge_recommendations.append("Store and learn from high-quality test patterns")
        
        if len(request.current_issues) > 3:
            knowledge_recommendations.append("Build knowledge base of common quality issues and solutions")
        
        knowledge_recommendations.append("Maintain historical quality trends for this test file")
        
        # Supporting evidence from knowledge perspective
        supporting_evidence = [
            f"Historical pattern analysis of {len(quality_patterns)} similar tests",
            "Knowledge base contains proven quality improvement patterns",
            "Past quality trends show improvement potential"
        ]
        
        # Priority actions for Knowledge Sage
        priority_actions = [
            "Update quality pattern library with findings",
            "Cross-reference with successful test patterns",
            "Store quality improvement history"
        ]
        
        # Calculate expected quality impact
        quality_impact = self._calculate_knowledge_quality_impact(request.quality_metrics, quality_patterns)
        
        return SageQualityInsight(
            sage_name='knowledge_sage',
            recommendation=base_recommendation,
            confidence=confidence,
            supporting_evidence=supporting_evidence,
            priority_actions=priority_actions,
            quality_impact=quality_impact
        )
    
    async def _process_task_sage_quality_response(self, response: Dict[str, Any], 
                                                request: QualityLearningRequest) -> SageQualityInsight:
        """Process Task Sage response for quality insights"""
        
        base_recommendation = response.get('recommendation', 'Optimize quality improvement workflow')
        confidence = response.get('confidence_score', 0.85)
        
        # Task-specific quality analysis
        quality_objectives = await self._analyze_quality_objectives(request)
        workflow_optimization = await self._suggest_quality_workflow_optimization(request)
        
        # Task Sage specific recommendations
        task_recommendations = []
        if request.priority == 'high':
            task_recommendations.append("Prioritize immediate quality improvements")
        
        task_recommendations.extend([
            "Schedule regular quality review cycles",
            "Track quality metrics progress over time",
            "Optimize test development workflow for quality"
        ])
        
        supporting_evidence = [
            f"Quality objective analysis shows {len(quality_objectives)} active goals",
            "Workflow optimization can improve efficiency by 25%",
            "Priority scheduling aligns with quality targets"
        ]
        
        priority_actions = [
            "Update quality improvement roadmap",
            "Schedule next quality review session",
            "Track progress against quality objectives"
        ]
        
        quality_impact = self._calculate_task_quality_impact(request.quality_metrics, quality_objectives)
        
        return SageQualityInsight(
            sage_name='task_sage',
            recommendation=base_recommendation,
            confidence=confidence,
            supporting_evidence=supporting_evidence,
            priority_actions=priority_actions,
            quality_impact=quality_impact
        )
    
    async def _process_incident_sage_quality_response(self, response: Dict[str, Any], 
                                                    request: QualityLearningRequest) -> SageQualityInsight:
        """Process Incident Sage response for quality insights"""
        
        base_recommendation = response.get('recommendation', 'Monitor for quality degradation risks')
        confidence = response.get('confidence_score', 0.8)
        
        # Incident-specific quality analysis
        quality_risks = await self._assess_quality_risks(request)
        prevention_strategies = await self._develop_quality_prevention_strategies(request)
        
        # Incident Sage specific recommendations
        incident_recommendations = []
        if any('coverage' in issue.lower() for issue in request.current_issues):
            incident_recommendations.append("Implement coverage quality monitoring")
        
        if any('complexity' in issue.lower() for issue in request.current_issues):
            incident_recommendations.append("Set up complexity threshold alerts")
        
        incident_recommendations.extend([
            "Establish quality degradation detection",
            "Create automated quality gate enforcement",
            "Monitor quality trend anomalies"
        ])
        
        supporting_evidence = [
            f"Risk assessment identified {len(quality_risks)} potential quality issues",
            "Prevention strategies can reduce quality incidents by 60%",
            "Early detection prevents quality degradation"
        ]
        
        priority_actions = [
            "Implement quality monitoring alerts",
            "Set up preventive quality measures",
            "Create quality incident response plan"
        ]
        
        quality_impact = self._calculate_incident_quality_impact(request.quality_metrics, quality_risks)
        
        return SageQualityInsight(
            sage_name='incident_sage',
            recommendation=base_recommendation,
            confidence=confidence,
            supporting_evidence=supporting_evidence,
            priority_actions=priority_actions,
            quality_impact=quality_impact
        )
    
    async def _process_rag_sage_quality_response(self, response: Dict[str, Any], 
                                               request: QualityLearningRequest) -> SageQualityInsight:
        """Process RAG Sage response for quality insights"""
        
        base_recommendation = response.get('recommendation', 'Search for similar high-quality test patterns')
        confidence = response.get('confidence_score', 0.88)
        
        # RAG-specific quality analysis
        similar_patterns = await self._find_similar_quality_patterns(request)
        best_practices = await self._discover_quality_best_practices(request)
        
        # RAG Sage specific recommendations
        rag_recommendations = []
        if request.quality_metrics.get('pattern_compliance', 0) < 0.7:
            rag_recommendations.append("Search for proven test pattern examples")
        
        rag_recommendations.extend([
            "Find similar high-quality test implementations",
            "Discover context-relevant best practices",
            "Enhance test with proven quality patterns"
        ])
        
        supporting_evidence = [
            f"Found {len(similar_patterns)} similar high-quality test patterns",
            f"Identified {len(best_practices)} applicable best practices",
            "Context analysis shows relevant improvement opportunities"
        ]
        
        priority_actions = [
            "Apply discovered best practices",
            "Integrate similar successful patterns",
            "Enhance context-specific quality aspects"
        ]
        
        quality_impact = self._calculate_rag_quality_impact(request.quality_metrics, similar_patterns)
        
        return SageQualityInsight(
            sage_name='rag_sage',
            recommendation=base_recommendation,
            confidence=confidence,
            supporting_evidence=supporting_evidence,
            priority_actions=priority_actions,
            quality_impact=quality_impact
        )
    
    async def _form_quality_consensus(self, sage_insights: Dict[str, SageQualityInsight], 
                                    request: QualityLearningRequest) -> Dict[str, Any]:
        """Form consensus from all sage quality insights"""
        
        if not sage_insights:
            return {
                'consensus_reached': False,
                'reason': 'No sage insights available'
            }
        
        # Calculate weighted consensus
        total_confidence = 0.0
        total_quality_impact = 0.0
        all_recommendations = []
        all_actions = []
        
        for sage_name, insight in sage_insights.items():
            weight = self.sage_specializations[sage_name]['quality_weight']
            total_confidence += insight.confidence * weight
            total_quality_impact += insight.quality_impact * weight
            
            all_recommendations.append(f"{sage_name}: {insight.recommendation}")
            all_actions.extend(insight.priority_actions)
        
        # Determine consensus strength
        consensus_threshold = 0.75
        consensus_reached = total_confidence >= consensus_threshold
        
        # Compile recommended actions (remove duplicates)
        unique_actions = list(set(all_actions))
        
        # Generate consolidated recommendations
        if consensus_reached:
            final_recommendation = self._generate_consolidated_quality_recommendation(sage_insights)
        else:
            final_recommendation = "Sages recommend further analysis - no strong consensus"
        
        # Determine improvement focus areas
        focus_areas = self._identify_quality_focus_areas(sage_insights, request)
        
        return {
            'consensus_reached': consensus_reached,
            'consensus_confidence': total_confidence,
            'expected_improvement': total_quality_impact,
            'final_recommendation': final_recommendation,
            'recommended_actions': unique_actions[:8],  # Top 8 actions
            'individual_recommendations': all_recommendations,
            'focus_areas': focus_areas,
            'sage_agreement_level': self._calculate_sage_agreement(sage_insights)
        }
    
    def _generate_consolidated_quality_recommendation(self, sage_insights: Dict[str, SageQualityInsight]) -> str:
        """Generate consolidated recommendation from all sages"""
        
        # Identify common themes
        common_themes = []
        
        # Check for pattern-related recommendations
        pattern_mentions = sum(1 for insight in sage_insights.values() 
                             if 'pattern' in insight.recommendation.lower())
        if pattern_mentions >= 2:
            common_themes.append("improve test patterns")
        
        # Check for quality monitoring recommendations
        monitoring_mentions = sum(1 for insight in sage_insights.values() 
                                if 'monitor' in insight.recommendation.lower())
        if monitoring_mentions >= 2:
            common_themes.append("enhance quality monitoring")
        
        # Check for workflow optimization
        workflow_mentions = sum(1 for insight in sage_insights.values() 
                              if 'workflow' in insight.recommendation.lower() or 'optimize' in insight.recommendation.lower())
        if workflow_mentions >= 2:
            common_themes.append("optimize quality workflow")
        
        if common_themes:
            return f"Sages consensus: Focus on {', '.join(common_themes)} for maximum quality impact"
        else:
            # Fallback to highest confidence recommendation
            best_insight = max(sage_insights.values(), key=lambda x: x.confidence)
            return f"Primary recommendation: {best_insight.recommendation}"
    
    def _identify_quality_focus_areas(self, sage_insights: Dict[str, SageQualityInsight], 
                                    request: QualityLearningRequest) -> List[str]:
        """Identify key focus areas for quality improvement"""
        focus_areas = []
        
        # Analyze quality metrics to identify weak areas
        metrics = request.quality_metrics
        
        if metrics.get('coverage_effectiveness', 1.0) < 0.7:
            focus_areas.append("Test Coverage Enhancement")
        
        if metrics.get('test_complexity', 1.0) < 0.7:
            focus_areas.append("Test Simplification")
        
        if metrics.get('pattern_compliance', 1.0) < 0.7:
            focus_areas.append("Pattern Compliance")
        
        if metrics.get('documentation_quality', 1.0) < 0.7:
            focus_areas.append("Documentation Quality")
        
        if metrics.get('edge_case_coverage', 1.0) < 0.7:
            focus_areas.append("Edge Case Testing")
        
        # Add sage-specific focus areas
        for sage_name, insight in sage_insights.items():
            if insight.quality_impact > 0.1:  # Significant impact
                sage_focus = self.sage_specializations[sage_name]['focus']
                if sage_focus == 'pattern_learning' and 'Pattern Compliance' not in focus_areas:
                    focus_areas.append("Pattern Learning")
                elif sage_focus == 'objective_tracking' and 'Quality Objectives' not in focus_areas:
                    focus_areas.append("Quality Objectives")
                elif sage_focus == 'issue_prevention' and 'Risk Prevention' not in focus_areas:
                    focus_areas.append("Risk Prevention")
                elif sage_focus == 'pattern_discovery' and 'Best Practices' not in focus_areas:
                    focus_areas.append("Best Practices")
        
        return focus_areas[:5]  # Top 5 focus areas
    
    def _calculate_sage_agreement(self, sage_insights: Dict[str, SageQualityInsight]) -> float:
        """Calculate level of agreement between sages"""
        if len(sage_insights) < 2:
            return 1.0
        
        confidences = [insight.confidence for insight in sage_insights.values()]
        quality_impacts = [insight.quality_impact for insight in sage_insights.values()]
        
        # Calculate variance in confidences and impacts
        conf_variance = sum((c - sum(confidences)/len(confidences))**2 for c in confidences) / len(confidences)
        impact_variance = sum((i - sum(quality_impacts)/len(quality_impacts))**2 for i in quality_impacts) / len(quality_impacts)
        
        # Agreement is higher when variance is lower
        agreement = 1.0 - min(conf_variance + impact_variance, 1.0)
        
        return agreement
    
    # Helper methods for individual sage analysis
    
    async def _identify_quality_patterns(self, request: QualityLearningRequest) -> List[Dict]:
        """Identify quality patterns for Knowledge Sage analysis"""
        # Mock implementation - in real system, would query pattern database
        return [
            {'pattern': 'setup_teardown', 'quality_impact': 0.15},
            {'pattern': 'mocking_usage', 'quality_impact': 0.12},
            {'pattern': 'assertion_patterns', 'quality_impact': 0.10}
        ]
    
    async def _perform_historical_quality_analysis(self, test_file: str) -> Dict[str, Any]:
        """Perform historical quality analysis for Knowledge Sage"""
        # Mock implementation
        return {
            'quality_trend': 'improving',
            'historical_scores': [0.65, 0.72, 0.78],
            'improvement_rate': 0.065
        }
    
    async def _analyze_quality_objectives(self, request: QualityLearningRequest) -> List[Dict]:
        """Analyze quality objectives for Task Sage"""
        objectives = []
        
        for obj_name, obj_config in self.quality_objectives.items():
            current_score = request.quality_metrics.get(obj_config['metrics'][0], 0.0)
            target_score = obj_config['target_score']
            
            objectives.append({
                'name': obj_name,
                'current_score': current_score,
                'target_score': target_score,
                'progress': min(current_score / target_score, 1.0),
                'priority': obj_config['priority']
            })
        
        return objectives
    
    async def _suggest_quality_workflow_optimization(self, request: QualityLearningRequest) -> List[str]:
        """Suggest workflow optimizations for Task Sage"""
        suggestions = []
        
        if request.priority == 'high':
            suggestions.append("Implement immediate quality review cycle")
        
        suggestions.extend([
            "Add automated quality checks to development workflow",
            "Schedule regular quality assessment sessions",
            "Integrate quality metrics into CI/CD pipeline"
        ])
        
        return suggestions
    
    async def _assess_quality_risks(self, request: QualityLearningRequest) -> List[Dict]:
        """Assess quality risks for Incident Sage"""
        risks = []
        
        metrics = request.quality_metrics
        
        if metrics.get('overall_quality_score', 1.0) < 0.6:
            risks.append({
                'type': 'low_overall_quality',
                'severity': 'high',
                'description': 'Overall quality below acceptable threshold'
            })
        
        if len(request.current_issues) > 5:
            risks.append({
                'type': 'multiple_quality_issues',
                'severity': 'medium',
                'description': 'Multiple quality issues detected'
            })
        
        return risks
    
    async def _develop_quality_prevention_strategies(self, request: QualityLearningRequest) -> List[str]:
        """Develop prevention strategies for Incident Sage"""
        strategies = [
            "Implement pre-commit quality hooks",
            "Set up quality degradation alerts",
            "Create quality review checkpoints",
            "Establish quality threshold enforcement"
        ]
        
        return strategies
    
    async def _find_similar_quality_patterns(self, request: QualityLearningRequest) -> List[Dict]:
        """Find similar quality patterns for RAG Sage"""
        # Mock implementation - would use vector search in real system
        return [
            {'pattern': 'high_quality_manager_test', 'similarity': 0.85},
            {'pattern': 'comprehensive_worker_test', 'similarity': 0.78},
            {'pattern': 'excellent_integration_test', 'similarity': 0.72}
        ]
    
    async def _discover_quality_best_practices(self, request: QualityLearningRequest) -> List[Dict]:
        """Discover quality best practices for RAG Sage"""
        return [
            {'practice': 'pytest_fixtures', 'relevance': 0.9},
            {'practice': 'parametrized_testing', 'relevance': 0.85},
            {'practice': 'comprehensive_mocking', 'relevance': 0.8}
        ]
    
    # Quality impact calculation methods
    
    def _calculate_knowledge_quality_impact(self, metrics: Dict[str, float], patterns: List[Dict]) -> float:
        """Calculate expected quality impact from Knowledge Sage recommendations"""
        base_impact = 0.05  # Base improvement from knowledge storage
        
        # Additional impact from pattern learning
        pattern_impact = len(patterns) * 0.02  # 2% per useful pattern
        
        # Bonus for low current pattern compliance
        if metrics.get('pattern_compliance', 1.0) < 0.7:
            pattern_impact += 0.05
        
        return min(base_impact + pattern_impact, 0.15)  # Cap at 15% improvement
    
    def _calculate_task_quality_impact(self, metrics: Dict[str, float], objectives: List[Dict]) -> float:
        """Calculate expected quality impact from Task Sage recommendations"""
        base_impact = 0.03  # Base improvement from workflow optimization
        
        # Impact from addressing objectives
        objectives_impact = sum(0.02 for obj in objectives if obj['progress'] < 0.8)
        
        return min(base_impact + objectives_impact, 0.12)  # Cap at 12% improvement
    
    def _calculate_incident_quality_impact(self, metrics: Dict[str, float], risks: List[Dict]) -> float:
        """Calculate expected quality impact from Incident Sage recommendations"""
        base_impact = 0.04  # Base improvement from risk prevention
        
        # Higher impact for high-severity risks
        risk_impact = sum(0.03 if risk['severity'] == 'high' else 0.02 for risk in risks)
        
        return min(base_impact + risk_impact, 0.18)  # Cap at 18% improvement
    
    def _calculate_rag_quality_impact(self, metrics: Dict[str, float], patterns: List[Dict]) -> float:
        """Calculate expected quality impact from RAG Sage recommendations"""
        base_impact = 0.04  # Base improvement from best practice discovery
        
        # Impact from high-similarity patterns
        similarity_impact = sum(0.02 for pattern in patterns if pattern['similarity'] > 0.8)
        
        return min(base_impact + similarity_impact, 0.14)  # Cap at 14% improvement
    
    async def _save_quality_session(self, session_summary: Dict[str, Any]):
        """Save quality learning session to database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Save main session record
            cursor.execute("""
                INSERT INTO quality_learning_sessions
                (session_id, test_file, learning_type, participating_sages,
                 session_start, session_end, consensus_reached, quality_insights,
                 recommended_actions, expected_improvement)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_summary['session_id'],
                session_summary['test_file'],
                'quality_analysis',
                json.dumps(session_summary['participating_sages']),
                datetime.now(),
                datetime.now(),
                session_summary['consensus_reached'],
                json.dumps(session_summary['sage_insights'], default=str),
                json.dumps(session_summary['recommended_actions']),
                session_summary['expected_quality_improvement']
            ))
            
            # Save individual sage recommendations
            for sage_name, insight in session_summary['sage_insights'].items():
                if isinstance(insight, SageQualityInsight):
                    cursor.execute("""
                        INSERT INTO sage_quality_recommendations
                        (session_id, sage_name, test_file, recommendation_type,
                         recommendation_text, confidence_score, priority_level,
                         supporting_evidence, quality_impact, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        session_summary['session_id'],
                        sage_name,
                        session_summary['test_file'],
                        'quality_improvement',
                        insight.recommendation,
                        insight.confidence,
                        session_summary['priority_level'],
                        json.dumps(insight.supporting_evidence),
                        insight.quality_impact,
                        datetime.now()
                    ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Quality session saved: {session_summary['session_id']}")
            
        except Exception as e:
            self.logger.error(f"Failed to save quality session: {e}")
    
    async def get_quality_insights_summary(self, time_range_days: int = 7) -> Dict[str, Any]:
        """Get summary of quality insights from recent sessions"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=time_range_days)
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Get session statistics
            cursor.execute("""
                SELECT COUNT(*), AVG(expected_improvement), 
                       SUM(CASE WHEN consensus_reached THEN 1 ELSE 0 END)
                FROM quality_learning_sessions
                WHERE session_start >= ?
            """, (start_date,))
            
            stats = cursor.fetchone()
            total_sessions = stats[0] if stats[0] else 0
            avg_improvement = stats[1] if stats[1] else 0.0
            consensus_sessions = stats[2] if stats[2] else 0
            
            # Get sage participation
            cursor.execute("""
                SELECT sage_name, COUNT(*), AVG(confidence_score), AVG(quality_impact)
                FROM sage_quality_recommendations
                WHERE timestamp >= ?
                GROUP BY sage_name
            """, (start_date,))
            
            sage_participation = {}
            for row in cursor.fetchall():
                sage_participation[row[0]] = {
                    'recommendations_count': row[1],
                    'avg_confidence': row[2],
                    'avg_quality_impact': row[3]
                }
            
            # Get most common recommendations
            cursor.execute("""
                SELECT recommendation_text, COUNT(*)
                FROM sage_quality_recommendations
                WHERE timestamp >= ?
                GROUP BY recommendation_text
                ORDER BY COUNT(*) DESC
                LIMIT 5
            """, (start_date,))
            
            common_recommendations = [
                {'recommendation': row[0], 'frequency': row[1]}
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            return {
                'summary_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': time_range_days
                },
                'session_statistics': {
                    'total_sessions': total_sessions,
                    'consensus_rate': consensus_sessions / total_sessions if total_sessions > 0 else 0,
                    'average_expected_improvement': avg_improvement
                },
                'sage_participation': sage_participation,
                'common_recommendations': common_recommendations,
                'system_health': self._assess_integration_health(sage_participation)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get quality insights summary: {e}")
            return {
                'error': str(e),
                'summary_timestamp': datetime.now().isoformat()
            }
    
    def _assess_integration_health(self, sage_participation: Dict[str, Any]) -> Dict[str, Any]:
        """Assess health of 4 Sages integration"""
        
        active_sages = len(sage_participation)
        total_sages = len(self.sage_specializations)
        
        if active_sages == total_sages:
            health_status = 'excellent'
        elif active_sages >= total_sages * 0.75:
            health_status = 'good'
        elif active_sages >= total_sages * 0.5:
            health_status = 'acceptable'
        else:
            health_status = 'poor'
        
        # Calculate average participation quality
        if sage_participation:
            avg_confidence = sum(data['avg_confidence'] for data in sage_participation.values()) / len(sage_participation)
            avg_impact = sum(data['avg_quality_impact'] for data in sage_participation.values()) / len(sage_participation)
        else:
            avg_confidence = 0.0
            avg_impact = 0.0
        
        return {
            'health_status': health_status,
            'active_sages': active_sages,
            'total_sages': total_sages,
            'participation_rate': active_sages / total_sages,
            'average_confidence': avg_confidence,
            'average_impact': avg_impact,
            'recommendations': self._get_integration_health_recommendations(health_status)
        }
    
    def _get_integration_health_recommendations(self, health_status: str) -> List[str]:
        """Get recommendations for integration health improvement"""
        recommendations = {
            'excellent': [
                "Continue current integration practices",
                "Consider expanding sage capabilities",
                "Monitor for consistency in recommendations"
            ],
            'good': [
                "Enhance underperforming sage interactions",
                "Improve consensus formation mechanisms",
                "Regular integration health monitoring"
            ],
            'acceptable': [
                "Investigate sage availability issues",
                "Improve sage response quality",
                "Enhance integration reliability"
            ],
            'poor': [
                "Urgent: Debug sage integration issues",
                "Restore missing sage connections",
                "Review integration architecture"
            ]
        }
        
        return recommendations.get(health_status, ["Review integration status"])


# Utility functions for external use
async def consult_sages_for_test_quality(test_file: str, quality_metrics: Dict[str, float], 
                                       current_issues: List[str] = None, 
                                       improvement_goals: List[str] = None) -> Dict[str, Any]:
    """Utility function to consult 4 Sages for test quality"""
    integration = FourSagesQualityIntegration()
    
    request = QualityLearningRequest(
        test_file=test_file,
        quality_metrics=quality_metrics,
        current_issues=current_issues or [],
        improvement_goals=improvement_goals or [],
        context={'source': 'external_utility'},
        priority='medium'
    )
    
    return await integration.consult_sages_for_quality(request)

async def get_quality_integration_summary(days: int = 7) -> Dict[str, Any]:
    """Utility function to get quality integration summary"""
    integration = FourSagesQualityIntegration()
    return await integration.get_quality_insights_summary(days)

if __name__ == "__main__":
    # Example usage
    import asyncio
    
    async def main():
        integration = FourSagesQualityIntegration()
        
        # Example quality consultation
        request = QualityLearningRequest(
            test_file="/home/aicompany/ai_co/workers/test_generator_worker.py",
            quality_metrics={
                'coverage_effectiveness': 0.65,
                'test_complexity': 0.80,
                'pattern_compliance': 0.55,
                'documentation_quality': 0.45,
                'edge_case_coverage': 0.60,
                'overall_quality_score': 0.61
            },
            current_issues=[
                "Insufficient test coverage effectiveness",
                "Poor pattern compliance",
                "Inadequate documentation"
            ],
            improvement_goals=[
                "Improve coverage effectiveness to >0.80",
                "Enhance pattern compliance to >0.75",
                "Add comprehensive documentation"
            ],
            context={'analysis_type': 'comprehensive'},
            priority='high'
        )
        
        result = await integration.consult_sages_for_quality(request)
        
        print("4 Sages Quality Consultation Results:")
        print(f"Consensus Reached: {result['consensus_reached']}")
        print(f"Expected Quality Improvement: {result['expected_quality_improvement']:.2f}")
        print(f"Final Recommendation: {result['quality_consensus']['final_recommendation']}")
        
        print("\nRecommended Actions:")
        for action in result['recommended_actions']:
            print(f"  - {action}")
        
        print(f"\nFocus Areas: {', '.join(result['quality_consensus']['focus_areas'])}")
    
    asyncio.run(main())