#\!/usr/bin/env python3
"""
Auto-repaired file by Incident Knights
"""

import logging
from datetime import datetime
import json
from unittest.mock import Mock
import asyncio
from typing import Dict, Any

# Add RAG Grimoire Integration
try:
    from libs.rag_grimoire_integration import RagGrimoireIntegration, RagGrimoireConfig
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

logger = logging.getLogger(__name__)

class KnowledgeManagementScheduler:
    """Knowledge Management Scheduler - Manages knowledge base updates and learning"""
    
    def __init__(self):
        self.worker_type = 'knowledge_scheduler'
        self.logger = logger
        self.connection = Mock()  # Mock connection for testing
        self.created_at = datetime.now()
        self.processed_count = 0
        
        # RAG Grimoire Integration setup
        self.rag_integration = None
        if RAG_AVAILABLE:
            self.rag_config = RagGrimoireConfig(
                database_url="postgresql://localhost/grimoire",
                search_threshold=0.7,
                max_search_results=10
            )
            self._initialize_rag_integration()
        
        logger.info(f"KnowledgeManagementScheduler initialized with RAG: {RAG_AVAILABLE}")
        
    def process_message(self, ch, method, properties, body):
        """Process incoming message with RAG integration"""
        try:
            # Parse JSON message
            task = json.loads(body.decode('utf-8'))
            task_type = task.get('type', 'general')
            
            # Process different types of knowledge management tasks
            if task_type == 'knowledge_update':
                self._process_knowledge_update(task)
            elif task_type == 'knowledge_search':
                result = self._process_knowledge_search(task)
                if result:
                    self.send_result(result)
            elif task_type == 'knowledge_migration':
                self._process_knowledge_migration(task)
            else:
                self.logger.warning(f"Unknown task type: {task_type}")
            
            self.processed_count += 1
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except json.JSONDecodeError:
            self.handle_error(Exception("Invalid JSON"), "process_message")
        except Exception as e:
            self.handle_error(e, "process_message")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
    def handle_error(self, error, operation):
        """Handle errors gracefully"""
        self.logger.error(f"Error in {operation}: {error}")
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.stop()
        
    def stop(self):
        """Stop the worker"""
        self.cleanup_rag_integration()
        self.logger.info("Stopping KnowledgeManagementScheduler")
        
    def health_check(self):
        """Return health status"""
        return {
            'status': 'healthy',
            'worker_type': self.worker_type,
            'uptime': (datetime.now() - self.created_at).total_seconds(),
            'processed_count': self.processed_count
        }
        
    def send_result(self, result):
        """Send result to output queue"""
        self.logger.info(f"Sending result: {result}")
    
    def _initialize_rag_integration(self):
        """Initialize RAG Grimoire Integration"""
        if not RAG_AVAILABLE:
            return
        
        try:
            self.rag_integration = RagGrimoireIntegration(self.rag_config)
            # Initialize in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.rag_integration.initialize())
            loop.close()
            self.logger.info("📚 RAG Grimoire Integration initialized for knowledge scheduler")
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG Grimoire Integration: {e}")
            self.rag_integration = None
    
    def _process_knowledge_update(self, task: Dict[str, Any]):
        """Process knowledge update request"""
        if not self.rag_integration:
            self.logger.warning("RAG integration not available for knowledge update")
            return
        
        try:
            knowledge_data = task.get('knowledge', {})
            spell_name = knowledge_data.get('name', f"scheduled_knowledge_{datetime.now().timestamp()}")
            content = knowledge_data.get('content', '')
            metadata = knowledge_data.get('metadata', {})
            
            # Add scheduling metadata
            metadata.update({
                'scheduled_at': datetime.now().isoformat(),
                'scheduler_worker': self.worker_type,
                'task_id': task.get('task_id', 'unknown')
            })
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            spell_id = loop.run_until_complete(
                self.rag_integration.add_knowledge_unified(
                    spell_name=spell_name,
                    content=content,
                    metadata=metadata,
                    category='scheduled_update',
                    tags=['scheduled', 'knowledge_update']
                )
            )
            loop.close()
            
            self.logger.info(f"📚 Knowledge updated: {spell_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to process knowledge update: {e}")
    
    def _process_knowledge_search(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process knowledge search request"""
        if not self.rag_integration:
            self.logger.warning("RAG integration not available for knowledge search")
            return {'error': 'RAG integration not available'}
        
        try:
            query = task.get('query', '')
            limit = task.get('limit', 5)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            results = loop.run_until_complete(
                self.rag_integration.search_unified(
                    query=query,
                    limit=limit,
                    threshold=self.rag_config.search_threshold
                )
            )
            loop.close()
            
            self.logger.info(f"📚 Knowledge search completed: {len(results)} results")
            
            return {
                'task_id': task.get('task_id'),
                'query': query,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process knowledge search: {e}")
            return {'error': str(e)}
    
    def _process_knowledge_migration(self, task: Dict[str, Any]):
        """Process knowledge migration request"""
        if not self.rag_integration:
            self.logger.warning("RAG integration not available for knowledge migration")
            return
        
        try:
            migration_type = task.get('migration_type', 'full')
            dry_run = task.get('dry_run', True)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            migration_result = loop.run_until_complete(
                self.rag_integration.migrate_legacy_knowledge(
                    force=migration_type == 'force',
                    dry_run=dry_run
                )
            )
            loop.close()
            
            self.logger.info(f"📚 Knowledge migration completed: {migration_result}")
            
        except Exception as e:
            self.logger.error(f"Failed to process knowledge migration: {e}")
    
    def cleanup_rag_integration(self):
        """Cleanup RAG integration resources"""
        if self.rag_integration:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.rag_integration.cleanup())
                loop.close()
                self.logger.info("📚 RAG Grimoire Integration cleaned up")
            except Exception as e:
                self.logger.error(f"Error during RAG cleanup: {e}")

# Default instance
default_instance = KnowledgeManagementScheduler()

# Common exports
__all__ = ['KnowledgeManagementScheduler', 'default_instance']


# Alias function for backward compatibility
def knowledge_management_scheduler(channel, method, properties, body):
    """Alias for KnowledgeSchedulerWorker - backward compatibility"""
    try:
        worker = KnowledgeSchedulerWorker()
        worker.process_message(body)
        if channel:
            channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error in knowledge_management_scheduler: {e}")
        if channel:
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
