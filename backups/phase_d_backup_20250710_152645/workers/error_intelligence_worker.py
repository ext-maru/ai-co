#!/usr/bin/env python3
"""
Error Intelligence Worker - Elders Guild Error Analysis Specialist
エラー知能ワーカー - エルダー評議会のエラー分析専門家

This worker serves as the error analysis specialist within the Elder Tree hierarchy,
reporting to the Incident Sage and leveraging the wisdom of all Four Sages.
"""

import logging
from datetime import datetime
import signal
import json
import sys
from pathlib import Path
from unittest.mock import Mock
from typing import Dict, List, Optional, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Elder Tree imports
try:
    from libs.four_sages_integration import FourSagesIntegration
    from libs.elder_council_summoner import ElderCouncilSummoner
    from libs.elder_tree_hierarchy import (
        get_elder_tree, ElderMessage, ElderRank, SageType
    )
    ELDER_SYSTEM_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Elder system not available: {e}")
    ELDER_SYSTEM_AVAILABLE = False
    FourSagesIntegration = None
    ElderCouncilSummoner = None

logger = logging.getLogger(__name__)

class ErrorIntelligenceWorker:
    """Error Intelligence Worker - AI-powered error analysis specialist of the Elder Tree hierarchy"""
    
    def __init__(self):
        self.worker_type = 'error_intelligence'
        self.logger = logger
        self.connection = Mock()  # Mock connection for testing
        self.created_at = datetime.now()
        self.processed_count = 0
        self.error_patterns = {}
        self.critical_error_threshold = 5  # Threshold for escalation
        
        # Initialize Elder systems
        self.elder_systems_initialized = False
        self._initialize_elder_systems()
        
        logger.info(f"ErrorIntelligenceWorker initialized as Elder Tree error specialist")
        
    def _initialize_elder_systems(self):
        """Initialize Elder Tree hierarchy systems with error handling"""
        if not ELDER_SYSTEM_AVAILABLE:
            self.logger.warning("Elder systems not available, running in standalone mode")
            self.four_sages = None
            self.council_summoner = None
            self.elder_tree = None
            return
            
        try:
            # Initialize Four Sages Integration
            self.four_sages = FourSagesIntegration()
            self.logger.info("Four Sages Integration initialized successfully")
            
            # Initialize Elder Council Summoner
            self.council_summoner = ElderCouncilSummoner()
            self.logger.info("Elder Council Summoner initialized successfully")
            
            # Get Elder Tree reference
            self.elder_tree = get_elder_tree()
            self.logger.info("Elder Tree hierarchy connected")
            
            self.elder_systems_initialized = True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Elder systems: {e}")
            self.four_sages = None
            self.council_summoner = None
            self.elder_tree = None
            self.elder_systems_initialized = False
    
    def process_message(self, ch, method, properties, body):
        """Process incoming message with Elder Tree integration"""
        try:
            # Parse JSON message
            task = json.loads(body.decode('utf-8'))
            self.processed_count += 1
            
            # Analyze error with Elder guidance
            analysis_result = self._analyze_error_with_elders(task)
            
            # Store patterns in Knowledge Sage
            if analysis_result.get('pattern_detected'):
                self._store_error_pattern(analysis_result)
            
            # Check for critical errors requiring escalation
            if analysis_result.get('severity') == 'critical':
                self._escalate_to_claude_elder(analysis_result)
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except json.JSONDecodeError:
            self.handle_error(Exception("Invalid JSON"), "process_message")
            
    def _analyze_error_with_elders(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze error using Elder Tree hierarchy guidance"""
        result = {
            'task_id': task.get('id'),
            'error_type': task.get('error_type', 'unknown'),
            'timestamp': datetime.now().isoformat(),
            'pattern_detected': False,
            'severity': 'normal'
        }
        
        if not self.elder_systems_initialized:
            # Basic analysis without Elder systems
            return self._basic_error_analysis(task)
        
        try:
            # Report to Incident Sage for analysis
            incident_response = self._report_to_incident_sage(task)
            result.update(incident_response)
            
            # Use RAG Sage for pattern matching
            pattern_match = self._check_error_patterns_with_rag(task)
            if pattern_match:
                result['pattern_detected'] = True
                result['similar_errors'] = pattern_match
            
            # Determine severity and resolution strategy
            result['severity'] = self._determine_error_severity(task, pattern_match)
            result['resolution_strategy'] = self._get_resolution_strategy(task, result)
            
        except Exception as e:
            self.logger.error(f"Elder analysis failed: {e}")
            return self._basic_error_analysis(task)
        
        return result
    
    def _report_to_incident_sage(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Report error to Incident Sage for analysis"""
        if not self.four_sages:
            return {}
            
        try:
            incident_data = {
                'type': 'error_report',
                'error_type': task.get('error_type'),
                'message': task.get('error_message'),
                'stack_trace': task.get('stack_trace'),
                'context': task.get('context', {}),
                'timestamp': datetime.now().isoformat()
            }
            
            # Send to Incident Sage
            response = self.four_sages.consult_incident_sage(incident_data)
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to report to Incident Sage: {e}")
            return {}
    
    def _store_error_pattern(self, analysis: Dict[str, Any]) -> None:
        """Store error pattern in Knowledge Sage"""
        if not self.four_sages:
            return
            
        try:
            pattern_data = {
                'error_type': analysis.get('error_type'),
                'pattern': analysis.get('pattern'),
                'resolution': analysis.get('resolution_strategy'),
                'frequency': analysis.get('frequency', 1),
                'first_seen': analysis.get('timestamp'),
                'last_seen': analysis.get('timestamp')
            }
            
            # Store in Knowledge Sage
            self.four_sages.store_knowledge('error_patterns', pattern_data)
            
        except Exception as e:
            self.logger.error(f"Failed to store error pattern: {e}")
    
    def _check_error_patterns_with_rag(self, task: Dict[str, Any]) -> Optional[List[Dict]]:
        """Use RAG Sage to find similar error patterns"""
        if not self.four_sages:
            return None
            
        try:
            query = {
                'error_type': task.get('error_type'),
                'error_message': task.get('error_message'),
                'context': task.get('context', {})
            }
            
            # Search for similar patterns
            similar_errors = self.four_sages.search_similar_patterns('errors', query)
            return similar_errors
            
        except Exception as e:
            self.logger.error(f"RAG pattern search failed: {e}")
            return None
    
    def _escalate_to_claude_elder(self, analysis: Dict[str, Any]) -> None:
        """Escalate critical errors to Claude Elder"""
        if not self.elder_tree:
            self.logger.warning("Cannot escalate - Elder Tree not available")
            return
            
        try:
            # Create escalation message
            message = ElderMessage(
                sender_rank=ElderRank.SAGE,
                sender_type=SageType.INCIDENT,
                content={
                    'type': 'critical_error_escalation',
                    'analysis': analysis,
                    'recommendation': 'Immediate attention required',
                    'timestamp': datetime.now().isoformat()
                },
                urgency='critical'
            )
            
            # Send to Claude Elder
            self.elder_tree.send_to_claude_elder(message)
            self.logger.info("Critical error escalated to Claude Elder")
            
        except Exception as e:
            self.logger.error(f"Failed to escalate to Claude Elder: {e}")
    
    def _determine_error_severity(self, task: Dict[str, Any], pattern_match: Optional[List]) -> str:
        """Determine error severity based on various factors"""
        # Critical indicators
        critical_keywords = ['crash', 'fatal', 'critical', 'emergency', 'panic']
        high_keywords = ['error', 'failed', 'exception', 'timeout']
        
        error_message = str(task.get('error_message', '')).lower()
        error_type = str(task.get('error_type', '')).lower()
        
        # Check for critical keywords
        if any(keyword in error_message or keyword in error_type for keyword in critical_keywords):
            return 'critical'
        
        # Check pattern history
        if pattern_match and len(pattern_match) > self.critical_error_threshold:
            return 'critical'
        
        # Check for high severity
        if any(keyword in error_message or keyword in error_type for keyword in high_keywords):
            return 'high'
        
        return 'normal'
    
    def _get_resolution_strategy(self, task: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get resolution strategy based on error analysis"""
        strategy = {
            'auto_recoverable': False,
            'recommended_actions': [],
            'elder_guidance': None
        }
        
        # Check if similar errors have known resolutions
        if analysis.get('similar_errors'):
            for similar in analysis['similar_errors']:
                if similar.get('resolution') and similar.get('success_rate', 0) > 0.8:
                    strategy['auto_recoverable'] = True
                    strategy['recommended_actions'].append(similar['resolution'])
        
        # Add severity-based recommendations
        severity = analysis.get('severity', 'normal')
        if severity == 'critical':
            strategy['recommended_actions'].append('Immediate manual intervention required')
            strategy['elder_guidance'] = 'Claude Elder notified'
        elif severity == 'high':
            strategy['recommended_actions'].append('Monitor closely and prepare intervention')
        
        return strategy
    
    def _basic_error_analysis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Basic error analysis without Elder systems"""
        return {
            'task_id': task.get('id'),
            'error_type': task.get('error_type', 'unknown'),
            'timestamp': datetime.now().isoformat(),
            'pattern_detected': False,
            'severity': 'normal',
            'resolution_strategy': {
                'auto_recoverable': False,
                'recommended_actions': ['Manual review required']
            }
        }
    
    def handle_error(self, error, operation):
        """Handle errors gracefully with Elder reporting"""
        self.logger.error(f"Error in {operation}: {error}")
        
        # Report internal errors to Incident Sage if available
        if self.elder_systems_initialized and self.four_sages:
            try:
                self.four_sages.report_incident({
                    'type': 'worker_error',
                    'worker': 'error_intelligence',
                    'operation': operation,
                    'error': str(error),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Failed to report internal error: {e}")
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.stop()
        
    def stop(self):
        """Stop the worker"""
        self.logger.info("Stopping ErrorIntelligenceWorker")
        
    def get_elder_error_intelligence_status(self) -> Dict[str, Any]:
        """Get comprehensive Elder error intelligence status"""
        status = {
            'worker_type': self.worker_type,
            'elder_role': 'Error Analysis Specialist',
            'reporting_to': 'Incident Sage',
            'elder_systems': {
                'initialized': self.elder_systems_initialized,
                'four_sages_active': self.four_sages is not None,
                'council_summoner_active': self.council_summoner is not None,
                'elder_tree_connected': self.elder_tree is not None
            },
            'error_intelligence': {
                'patterns_tracked': len(self.error_patterns),
                'errors_processed': self.processed_count,
                'critical_threshold': self.critical_error_threshold
            },
            'uptime': (datetime.now() - self.created_at).total_seconds(),
            'status': 'healthy' if self.elder_systems_initialized else 'degraded'
        }
        
        # Add Four Sages status if available
        if self.four_sages:
            try:
                status['four_sages_status'] = self.four_sages.get_sages_status()
            except Exception as e:
                status['four_sages_status'] = f"Error retrieving status: {e}"
        
        return status
    
    def health_check(self):
        """Return health status with Elder integration info"""
        base_health = {
            'status': 'healthy' if self.elder_systems_initialized else 'degraded',
            'worker_type': self.worker_type,
            'uptime': (datetime.now() - self.created_at).total_seconds(),
            'processed_count': self.processed_count
        }
        
        # Add Elder-specific health info
        base_health['elder_integration'] = {
            'role': 'Error Analysis Specialist',
            'systems_initialized': self.elder_systems_initialized,
            'reporting_chain': 'Incident Sage -> Claude Elder -> Grand Elder Maru'
        }
        
        return base_health
        
    def send_result(self, result):
        """Send result to output queue with Elder Tree metadata"""
        # Enhance result with Elder metadata
        elder_result = {
            'original_result': result,
            'elder_metadata': {
                'processed_by': 'Error Intelligence Worker',
                'elder_role': 'Error Analysis Specialist',
                'timestamp': datetime.now().isoformat(),
                'elder_systems_active': self.elder_systems_initialized
            }
        }
        
        # If Elder systems are active, add their insights
        if self.elder_systems_initialized and isinstance(result, dict):
            if result.get('error_analysis'):
                elder_result['elder_insights'] = {
                    'incident_sage_analysis': result.get('incident_response'),
                    'pattern_matches': result.get('similar_errors'),
                    'resolution_strategy': result.get('resolution_strategy')
                }
        
        self.logger.info(f"Sending Elder-enhanced result: {elder_result}")
    
    def report_to_elders(self, report_type: str, data: Dict[str, Any]) -> None:
        """General method to report various data to Elder Tree hierarchy"""
        if not self.elder_systems_initialized:
            self.logger.warning("Elder systems not initialized, cannot report")
            return
        
        try:
            if report_type == 'daily_summary':
                self._send_daily_summary_to_elders(data)
            elif report_type == 'critical_incident':
                self._escalate_to_claude_elder(data)
            elif report_type == 'pattern_discovery':
                self._report_pattern_to_knowledge_sage(data)
            else:
                self.logger.warning(f"Unknown report type: {report_type}")
        except Exception as e:
            self.logger.error(f"Failed to report to Elders: {e}")
    
    def _send_daily_summary_to_elders(self, data: Dict[str, Any]) -> None:
        """Send daily error intelligence summary to Task Sage"""
        if not self.four_sages:
            return
        
        summary = {
            'type': 'daily_error_summary',
            'date': datetime.now().date().isoformat(),
            'errors_processed': self.processed_count,
            'patterns_discovered': len(self.error_patterns),
            'critical_incidents': data.get('critical_count', 0),
            'top_error_types': data.get('top_errors', []),
            'recommendations': data.get('recommendations', [])
        }
        
        self.four_sages.report_to_task_sage(summary)
    
    def _report_pattern_to_knowledge_sage(self, pattern: Dict[str, Any]) -> None:
        """Report newly discovered error pattern to Knowledge Sage"""
        if not self.four_sages:
            return
        
        knowledge_entry = {
            'type': 'error_pattern',
            'pattern': pattern,
            'discovered_at': datetime.now().isoformat(),
            'discovered_by': 'Error Intelligence Worker',
            'confidence': pattern.get('confidence', 0.0),
            'impact': pattern.get('impact', 'unknown')
        }
        
        self.four_sages.store_knowledge('error_patterns', knowledge_entry)

# Default instance
default_instance = ErrorIntelligenceWorker()

# Common exports
__all__ = ['ErrorIntelligenceWorker', 'default_instance']


# Worker function for RabbitMQ integration with Elder support
def error_intelligence_worker(channel, method, properties, body):
    """Worker function wrapper for ErrorIntelligenceWorker with Elder Tree integration"""
    try:
        worker = ErrorIntelligenceWorker()
        
        # Process message through Elder-enhanced pipeline
        worker.process_message(channel, method, properties, body)
        
        # Note: Acknowledgment is handled within process_message
    except Exception as e:
        logger.error(f"Error in error_intelligence_worker: {e}")
        
        # Report critical failures to Elder Tree if possible
        try:
            if worker.elder_systems_initialized:
                worker.handle_error(e, "error_intelligence_worker")
        except:
            pass
        
        if channel:
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
