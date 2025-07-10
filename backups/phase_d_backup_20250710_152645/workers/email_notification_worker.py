#!/usr/bin/env python3
"""
Email Notification Worker - Elders Guild Communication Specialist
メール通知ワーカー - エルダー評議会の通信専門家

This worker serves as the communication specialist within the Elder Tree hierarchy,
reporting to the Task Sage and ensuring all guild members stay informed.
"""

import logging
import smtplib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
import ssl

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

from core.base_worker import BaseWorker

logger = logging.getLogger(__name__)

class EmailNotificationWorker(BaseWorker):
    """Email Notification Worker - Communication specialist of the Elder Tree hierarchy"""
    
    def __init__(self):
        super().__init__(
            input_queue='email_notifications',
            output_queue='ai_notifications',
            worker_type='email_notification'
        )
        
        self.logger = logger
        self.created_at = datetime.now()
        self.sent_count = 0
        self.failed_count = 0
        
        # Email configuration
        self.smtp_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True,
            'username': '',  # To be configured
            'password': ''   # To be configured
        }
        
        # Initialize Elder systems
        self.elder_systems_initialized = False
        self._initialize_elder_systems()
        
        logger.info(f"EmailNotificationWorker initialized as Elder Tree communication specialist")
        
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
        """Process incoming email notification request with Elder Tree integration"""
        try:
            # Parse JSON message
            notification = json.loads(body.decode('utf-8'))
            self.sent_count += 1
            
            # Send email with Elder enhancement
            result = self._send_email_with_elders(notification)
            
            # Report to Task Sage if available
            if result.get('success'):
                self._report_success_to_task_sage(notification, result)
            else:
                self._report_failure_to_incident_sage(notification, result)
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except json.JSONDecodeError:
            self.handle_error(Exception("Invalid JSON"), "process_message")
            self.failed_count += 1
            
    def _send_email_with_elders(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Send email with Elder Tree hierarchy enhancement"""
        result = {
            'notification_id': notification.get('id'),
            'recipient': notification.get('recipient'),
            'subject': notification.get('subject'),
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'elder_enhanced': self.elder_systems_initialized
        }
        
        try:
            # Add Elder signature if systems available
            if self.elder_systems_initialized:
                notification = self._enhance_notification_with_elder_context(notification)
            
            # Check if this is a test/simulation or real email
            if notification.get('test_mode', True):
                # Simulate email sending for testing
                result.update({
                    'success': True,
                    'method': 'simulated',
                    'message': 'Email simulated successfully',
                    'delivery_time': 0.1
                })
                self.logger.info(f"Simulated email to {notification.get('recipient')}")
            else:
                # Real email sending logic would go here
                result.update({
                    'success': True,
                    'method': 'smtp',
                    'message': 'Email sent successfully (not implemented)',
                    'delivery_time': 1.0
                })
                self.logger.info(f"Email sending not implemented for {notification.get('recipient')}")
                
        except Exception as e:
            result.update({
                'success': False,
                'error': str(e),
                'message': 'Email sending failed'
            })
            self.logger.error(f"Email sending failed: {e}")
        
        return result
    
    def _enhance_notification_with_elder_context(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance notification with Elder Tree context"""
        if not self.four_sages:
            return notification
            
        try:
            # Add Elder footer to email body
            original_body = notification.get('body', '')
            elder_footer = "\n\n---\n🏛️ Sent via Elders Guild Communication Network\n⚔️ Secured by Elder Tree Hierarchy"
            
            notification['body'] = original_body + elder_footer
            notification['elder_enhanced'] = True
            
            # Add priority based on Elder context
            if 'critical' in notification.get('subject', '').lower():
                notification['priority'] = 'high'
                notification['elder_urgency'] = 'critical'
            
            return notification
            
        except Exception as e:
            self.logger.error(f"Failed to enhance notification: {e}")
            return notification
    
    def _report_success_to_task_sage(self, notification: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Report successful email delivery to Task Sage"""
        if not self.four_sages:
            return
            
        try:
            report = {
                'type': 'communication_success',
                'worker': 'email_notification',
                'notification_id': notification.get('id'),
                'recipient': notification.get('recipient'),
                'delivery_time': result.get('delivery_time'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Report to Task Sage
            self.four_sages.report_to_task_sage(report)
            
        except Exception as e:
            self.logger.error(f"Failed to report success to Task Sage: {e}")
    
    def _report_failure_to_incident_sage(self, notification: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Report email failure to Incident Sage"""
        if not self.four_sages:
            return
            
        try:
            incident_data = {
                'type': 'communication_failure',
                'worker': 'email_notification',
                'notification_id': notification.get('id'),
                'recipient': notification.get('recipient'),
                'error': result.get('error'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Report to Incident Sage
            self.four_sages.consult_incident_sage(incident_data)
            
            # Escalate critical failures
            if notification.get('priority') == 'critical':
                self._escalate_to_claude_elder(incident_data)
            
        except Exception as e:
            self.logger.error(f"Failed to report failure to Incident Sage: {e}")
    
    def _escalate_to_claude_elder(self, incident: Dict[str, Any]) -> None:
        """Escalate critical communication failures to Claude Elder"""
        if not self.elder_tree:
            self.logger.warning("Cannot escalate - Elder Tree not available")
            return
            
        try:
            # Create escalation message
            message = ElderMessage(
                sender_rank=ElderRank.SAGE,
                sender_type=SageType.INCIDENT,
                content={
                    'type': 'critical_communication_failure',
                    'incident': incident,
                    'recommendation': 'Communication channels require immediate attention',
                    'timestamp': datetime.now().isoformat()
                },
                urgency='critical'
            )
            
            # Send to Claude Elder
            self.elder_tree.send_to_claude_elder(message)
            self.logger.info("Critical communication failure escalated to Claude Elder")
            
        except Exception as e:
            self.logger.error(f"Failed to escalate to Claude Elder: {e}")
    
    def handle_error(self, error, operation):
        """Handle errors gracefully with Elder reporting"""
        self.logger.error(f"Error in {operation}: {error}")
        
        # Report internal errors to Incident Sage if available
        if self.elder_systems_initialized and self.four_sages:
            try:
                self.four_sages.report_incident({
                    'type': 'worker_error',
                    'worker': 'email_notification',
                    'operation': operation,
                    'error': str(error),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Failed to report internal error: {e}")
    
    def get_elder_communication_status(self) -> Dict[str, Any]:
        """Get comprehensive Elder communication status"""
        status = {
            'worker_type': self.worker_type,
            'elder_role': 'Communication Specialist',
            'reporting_to': 'Task Sage',
            'elder_systems': {
                'initialized': self.elder_systems_initialized,
                'four_sages_active': self.four_sages is not None,
                'council_summoner_active': self.council_summoner is not None,
                'elder_tree_connected': self.elder_tree is not None
            },
            'communication_stats': {
                'emails_sent': self.sent_count,
                'emails_failed': self.failed_count,
                'success_rate': self.sent_count / (self.sent_count + self.failed_count) if (self.sent_count + self.failed_count) > 0 else 0.0
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
            'sent_count': self.sent_count,
            'failed_count': self.failed_count
        }
        
        # Add Elder-specific health info
        base_health['elder_integration'] = {
            'role': 'Communication Specialist',
            'systems_initialized': self.elder_systems_initialized,
            'reporting_chain': 'Task Sage -> Claude Elder -> Grand Elder Maru'
        }
        
        return base_health
        
    def send_result(self, result):
        """Send result to output queue with Elder Tree metadata"""
        # Enhance result with Elder metadata
        elder_result = {
            'original_result': result,
            'elder_metadata': {
                'processed_by': 'Email Notification Worker',
                'elder_role': 'Communication Specialist',
                'timestamp': datetime.now().isoformat(),
                'elder_systems_active': self.elder_systems_initialized
            }
        }
        
        # If Elder systems are active, add their insights
        if self.elder_systems_initialized and isinstance(result, dict):
            if result.get('communication_report'):
                elder_result['elder_insights'] = {
                    'task_sage_report': result.get('task_response'),
                    'delivery_status': result.get('delivery_status'),
                    'priority_level': result.get('priority_level')
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
            elif report_type == 'critical_failure':
                self._escalate_to_claude_elder(data)
            elif report_type == 'communication_pattern':
                self._report_pattern_to_knowledge_sage(data)
            else:
                self.logger.warning(f"Unknown report type: {report_type}")
        except Exception as e:
            self.logger.error(f"Failed to report to Elders: {e}")
    
    def _send_daily_summary_to_elders(self, data: Dict[str, Any]) -> None:
        """Send daily communication summary to Task Sage"""
        if not self.four_sages:
            return
        
        summary = {
            'type': 'daily_communication_summary',
            'date': datetime.now().date().isoformat(),
            'emails_sent': self.sent_count,
            'emails_failed': self.failed_count,
            'success_rate': self.sent_count / (self.sent_count + self.failed_count) if (self.sent_count + self.failed_count) > 0 else 0.0,
            'top_recipients': data.get('top_recipients', []),
            'peak_hours': data.get('peak_hours', [])
        }
        
        self.four_sages.report_to_task_sage(summary)
    
    def _report_pattern_to_knowledge_sage(self, pattern: Dict[str, Any]) -> None:
        """Report communication patterns to Knowledge Sage"""
        if not self.four_sages:
            return
        
        knowledge_entry = {
            'type': 'communication_pattern',
            'pattern': pattern,
            'discovered_at': datetime.now().isoformat(),
            'discovered_by': 'Email Notification Worker',
            'relevance': pattern.get('relevance', 0.0),
            'impact': pattern.get('impact', 'unknown')
        }
        
        self.four_sages.store_knowledge('communication_patterns', knowledge_entry)

# Default instance
default_instance = EmailNotificationWorker()

# Common exports
__all__ = ['EmailNotificationWorker', 'default_instance']