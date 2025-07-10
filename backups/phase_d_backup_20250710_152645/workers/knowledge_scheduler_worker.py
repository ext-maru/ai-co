#!/usr/bin/env python3
"""
Knowledge Scheduler Worker - Elders Guild Knowledge Coordination Specialist
ナレッジスケジューラーワーカー - エルダー評議会の知識調整専門家

This worker serves as the knowledge coordination specialist within the Elder Tree hierarchy,
reporting to the Knowledge Sage and managing knowledge base updates and learning schedules.
"""

import logging
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys
from typing import Dict, Any, List, Optional
import schedule
import time
import threading

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

# RAG Grimoire Integration
try:
    from libs.rag_grimoire_integration import RagGrimoireIntegration, RagGrimoireConfig
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    RagGrimoireIntegration = None
    RagGrimoireConfig = None

from core.base_worker import BaseWorker

logger = logging.getLogger(__name__)

class KnowledgeSchedulerWorker(BaseWorker):
    """Knowledge Scheduler Worker - Knowledge coordination specialist of the Elder Tree hierarchy"""
    
    def __init__(self):
        super().__init__(
            input_queue='knowledge_scheduler_tasks',
            output_queue='ai_notifications',
            worker_type='knowledge_scheduler'
        )
        
        self.logger = logger
        self.created_at = datetime.now()
        self.scheduled_tasks = 0
        self.completed_tasks = 0
        self.knowledge_updates = 0
        
        # Schedule storage
        self.schedules = {}
        self.scheduler_thread = None
        self.running = True
        
        # RAG Grimoire Integration setup
        self.rag_integration = None
        if RAG_AVAILABLE:
            self.rag_config = RagGrimoireConfig(
                database_url="postgresql://localhost/grimoire",
                search_threshold=0.7,
                max_search_results=10
            )
            self._initialize_rag_integration()
        
        # Initialize Elder systems
        self.elder_systems_initialized = False
        self._initialize_elder_systems()
        
        # Start scheduler thread
        self._start_scheduler_thread()
        
        logger.info(f"KnowledgeSchedulerWorker initialized as Elder Tree knowledge coordination specialist")
        
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
    
    def _initialize_rag_integration(self):
        """Initialize RAG Grimoire integration"""
        try:
            self.rag_integration = RagGrimoireIntegration(self.rag_config)
            self.logger.info("RAG Grimoire integration initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG integration: {e}")
            self.rag_integration = None
    
    def _start_scheduler_thread(self):
        """Start the scheduler thread"""
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        self.logger.info("Scheduler thread started")
    
    def process_message(self, ch, method, properties, body):
        """Process incoming message with Elder Tree integration"""
        try:
            # Parse JSON message
            task = json.loads(body.decode('utf-8'))
            task_type = task.get('type', 'general')
            
            self.logger.info(f"Processing knowledge scheduler task: {task_type}")
            
            # Report task start to Knowledge Sage
            if self.elder_systems_initialized:
                self._report_task_start_to_knowledge_sage(task)
            
            # Process based on task type
            if task_type == 'schedule_update':
                result = self._schedule_knowledge_update(task)
            elif task_type == 'immediate_update':
                result = self._perform_immediate_update(task)
            elif task_type == 'query_schedule':
                result = self._query_schedule(task)
            elif task_type == 'cancel_schedule':
                result = self._cancel_schedule(task)
            else:
                result = {'status': 'error', 'message': f'Unknown task type: {task_type}'}
            
            # Report result
            if result.get('status') == 'success':
                self.completed_tasks += 1
                if self.elder_systems_initialized:
                    self._report_success_to_knowledge_sage(task, result)
            else:
                if self.elder_systems_initialized:
                    self._report_failure_to_incident_sage(task, result)
            
            # Send result
            self.send_result(result)
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            self.handle_error(e, "process_message")
            
    def _schedule_knowledge_update(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a knowledge base update"""
        try:
            schedule_id = task.get('schedule_id', f"schedule_{datetime.now().timestamp()}")
            schedule_type = task.get('schedule_type', 'daily')
            schedule_time = task.get('schedule_time', '03:00')
            knowledge_source = task.get('knowledge_source')
            
            self.scheduled_tasks += 1
            
            # Create schedule based on type
            if schedule_type == 'daily':
                schedule.every().day.at(schedule_time).do(
                    self._execute_knowledge_update, 
                    schedule_id, 
                    knowledge_source
                )
            elif schedule_type == 'hourly':
                schedule.every().hour.do(
                    self._execute_knowledge_update,
                    schedule_id,
                    knowledge_source
                )
            elif schedule_type == 'weekly':
                day = task.get('day_of_week', 'monday')
                getattr(schedule.every(), day).at(schedule_time).do(
                    self._execute_knowledge_update,
                    schedule_id,
                    knowledge_source
                )
            
            # Store schedule info
            self.schedules[schedule_id] = {
                'type': schedule_type,
                'time': schedule_time,
                'source': knowledge_source,
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            return {
                'status': 'success',
                'schedule_id': schedule_id,
                'message': f'Knowledge update scheduled: {schedule_type} at {schedule_time}'
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _perform_immediate_update(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform immediate knowledge update"""
        try:
            knowledge_source = task.get('knowledge_source')
            update_type = task.get('update_type', 'full')
            
            # Execute update
            result = self._execute_knowledge_update(
                f"immediate_{datetime.now().timestamp()}",
                knowledge_source
            )
            
            return {
                'status': 'success',
                'update_result': result,
                'message': 'Immediate knowledge update completed'
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _execute_knowledge_update(self, schedule_id: str, knowledge_source: Dict[str, Any]):
        """Execute the actual knowledge update"""
        try:
            self.knowledge_updates += 1
            
            # Report update start to Knowledge Sage
            if self.elder_systems_initialized:
                self._report_update_start_to_knowledge_sage(schedule_id, knowledge_source)
            
            update_result = {
                'schedule_id': schedule_id,
                'source': knowledge_source,
                'timestamp': datetime.now().isoformat(),
                'items_processed': 0,
                'items_added': 0,
                'items_updated': 0
            }
            
            # If RAG integration available, perform update
            if self.rag_integration and knowledge_source:
                source_type = knowledge_source.get('type', 'file')
                
                if source_type == 'file':
                    file_path = knowledge_source.get('path')
                    if file_path and Path(file_path).exists():
                        # Process file and update knowledge base
                        update_result['items_processed'] = 1
                        update_result['items_added'] = 1
                        
                        # Store in Knowledge Sage
                        if self.four_sages:
                            self.four_sages.store_knowledge('scheduled_updates', {
                                'file': file_path,
                                'timestamp': datetime.now().isoformat(),
                                'schedule_id': schedule_id
                            })
                
                elif source_type == 'directory':
                    dir_path = knowledge_source.get('path')
                    if dir_path and Path(dir_path).exists():
                        files = list(Path(dir_path).glob('**/*.md'))
                        update_result['items_processed'] = len(files)
                        update_result['items_added'] = len(files)
            
            # Report update completion
            if self.elder_systems_initialized:
                self._report_update_completion_to_knowledge_sage(schedule_id, update_result)
            
            return update_result
            
        except Exception as e:
            self.logger.error(f"Knowledge update failed: {e}")
            if self.elder_systems_initialized:
                self._report_update_failure_to_incident_sage(schedule_id, e)
            return {'error': str(e)}
    
    def _query_schedule(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Query existing schedules"""
        try:
            schedule_id = task.get('schedule_id')
            
            if schedule_id:
                # Query specific schedule
                schedule_info = self.schedules.get(schedule_id)
                if schedule_info:
                    return {
                        'status': 'success',
                        'schedule': schedule_info
                    }
                else:
                    return {
                        'status': 'error',
                        'message': f'Schedule not found: {schedule_id}'
                    }
            else:
                # Return all schedules
                return {
                    'status': 'success',
                    'schedules': self.schedules,
                    'total': len(self.schedules)
                }
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _cancel_schedule(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel a scheduled update"""
        try:
            schedule_id = task.get('schedule_id')
            
            if schedule_id in self.schedules:
                # Mark as cancelled
                self.schedules[schedule_id]['status'] = 'cancelled'
                self.schedules[schedule_id]['cancelled_at'] = datetime.now().isoformat()
                
                # Clear from schedule
                schedule.clear(schedule_id)
                
                return {
                    'status': 'success',
                    'message': f'Schedule cancelled: {schedule_id}'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Schedule not found: {schedule_id}'
                }
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _report_task_start_to_knowledge_sage(self, task: Dict[str, Any]):
        """Report task start to Knowledge Sage"""
        if not self.four_sages:
            return
            
        try:
            report = {
                'type': 'knowledge_scheduler_task_start',
                'worker': 'knowledge_scheduler',
                'task_type': task.get('type'),
                'timestamp': datetime.now().isoformat()
            }
            
            self.four_sages.report_to_knowledge_sage(report)
            
        except Exception as e:
            self.logger.error(f"Failed to report task start to Knowledge Sage: {e}")
    
    def _report_success_to_knowledge_sage(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Report success to Knowledge Sage"""
        if not self.four_sages:
            return
            
        try:
            report = {
                'type': 'knowledge_scheduler_success',
                'worker': 'knowledge_scheduler',
                'task_type': task.get('type'),
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            self.four_sages.report_to_knowledge_sage(report)
            
        except Exception as e:
            self.logger.error(f"Failed to report success to Knowledge Sage: {e}")
    
    def _report_failure_to_incident_sage(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Report failure to Incident Sage"""
        if not self.four_sages:
            return
            
        try:
            incident_data = {
                'type': 'knowledge_scheduler_failure',
                'worker': 'knowledge_scheduler',
                'task_type': task.get('type'),
                'error': result.get('message'),
                'timestamp': datetime.now().isoformat()
            }
            
            self.four_sages.consult_incident_sage(incident_data)
            
        except Exception as e:
            self.logger.error(f"Failed to report failure to Incident Sage: {e}")
    
    def _report_update_start_to_knowledge_sage(self, schedule_id: str, knowledge_source: Dict[str, Any]):
        """Report knowledge update start to Knowledge Sage"""
        if not self.four_sages:
            return
            
        try:
            report = {
                'type': 'knowledge_update_start',
                'schedule_id': schedule_id,
                'source': knowledge_source,
                'timestamp': datetime.now().isoformat()
            }
            
            self.four_sages.report_to_knowledge_sage(report)
            
        except Exception as e:
            self.logger.error(f"Failed to report update start: {e}")
    
    def _report_update_completion_to_knowledge_sage(self, schedule_id: str, result: Dict[str, Any]):
        """Report knowledge update completion to Knowledge Sage"""
        if not self.four_sages:
            return
            
        try:
            report = {
                'type': 'knowledge_update_complete',
                'schedule_id': schedule_id,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            self.four_sages.report_to_knowledge_sage(report)
            
        except Exception as e:
            self.logger.error(f"Failed to report update completion: {e}")
    
    def _report_update_failure_to_incident_sage(self, schedule_id: str, error: Exception):
        """Report knowledge update failure to Incident Sage"""
        if not self.four_sages:
            return
            
        try:
            incident_data = {
                'type': 'knowledge_update_failure',
                'schedule_id': schedule_id,
                'error': str(error),
                'error_type': type(error).__name__,
                'timestamp': datetime.now().isoformat()
            }
            
            self.four_sages.consult_incident_sage(incident_data)
            
        except Exception as e:
            self.logger.error(f"Failed to report update failure: {e}")
    
    def handle_error(self, error, operation):
        """Handle errors gracefully with Elder reporting"""
        self.logger.error(f"Error in {operation}: {error}")
        
        # Report internal errors to Incident Sage if available
        if self.elder_systems_initialized and self.four_sages:
            try:
                self.four_sages.report_incident({
                    'type': 'worker_error',
                    'worker': 'knowledge_scheduler',
                    'operation': operation,
                    'error': str(error),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Failed to report internal error: {e}")
    
    def get_elder_scheduler_status(self) -> Dict[str, Any]:
        """Get comprehensive Elder knowledge scheduler status"""
        status = {
            'worker_type': self.worker_type,
            'elder_role': 'Knowledge Coordination Specialist',
            'reporting_to': 'Knowledge Sage',
            'elder_systems': {
                'initialized': self.elder_systems_initialized,
                'four_sages_active': self.four_sages is not None,
                'council_summoner_active': self.council_summoner is not None,
                'elder_tree_connected': self.elder_tree is not None
            },
            'scheduler_stats': {
                'scheduled_tasks': self.scheduled_tasks,
                'completed_tasks': self.completed_tasks,
                'knowledge_updates': self.knowledge_updates,
                'active_schedules': len([s for s in self.schedules.values() if s.get('status') == 'active']),
                'rag_available': RAG_AVAILABLE,
                'rag_initialized': self.rag_integration is not None
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
            'scheduled_tasks': self.scheduled_tasks,
            'completed_tasks': self.completed_tasks
        }
        
        # Add Elder-specific health info
        base_health['elder_integration'] = {
            'role': 'Knowledge Coordination Specialist',
            'systems_initialized': self.elder_systems_initialized,
            'reporting_chain': 'Knowledge Sage -> Claude Elder -> Grand Elder Maru'
        }
        
        return base_health
    
    def stop(self):
        """Stop the worker and scheduler thread"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        super().stop()

# Default instance
default_instance = KnowledgeSchedulerWorker()

# Common exports
__all__ = ['KnowledgeSchedulerWorker', 'default_instance']

if __name__ == "__main__":
    worker = KnowledgeSchedulerWorker()
    print("Knowledge Scheduler Worker started")
    try:
        worker.start()
    except KeyboardInterrupt:
        print("\nStopping Knowledge Scheduler Worker...")
        worker.stop()