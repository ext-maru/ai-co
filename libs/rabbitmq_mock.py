#!/usr/bin/env python3
"""
RabbitMQ Complete Mock Implementation
Phase 3: 完全なRabbitMQモック実装
"""
import json
import logging
import threading
import time
import uuid
from collections import defaultdict, deque
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class MockMessage:
    """Mock RabbitMQ message"""
    body: bytes
    headers: Dict[str, Any] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)
    delivery_tag: int = field(default_factory=lambda: uuid.uuid4().int & (1<<32)-1)
    exchange: str = ""
    routing_key: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    rejected: bool = False
    redelivered: bool = False

class MockChannel:
    """Mock RabbitMQ channel"""
    
    def __init__(self, connection, channel_number=1):
        self.connection = connection
        self.channel_number = channel_number
        self.is_open = True
        self.exchanges = {}
        self.queues = {}
        self.bindings = defaultdict(list)
        self.consumers = {}
        self.consumer_tags = {}
        self.message_id_counter = 0
        self.prefetch_count = 1
        self.transactional = False
        self.callbacks = defaultdict(list)
        self._delivery_tag_counter = 0
        
    def exchange_declare(self, exchange, exchange_type='direct', durable=False, 
                        auto_delete=False, arguments=None):
        """Declare an exchange"""
        if not self.is_open:
            raise Exception("Channel is closed")
            
        self.exchanges[exchange] = {
            'type': exchange_type,
            'durable': durable,
            'auto_delete': auto_delete,
            'arguments': arguments or {}
        }
        logger.info(f"Exchange declared: {exchange} (type: {exchange_type})")
        
    def queue_declare(self, queue='', durable=False, exclusive=False, 
                     auto_delete=False, arguments=None):
        """Declare a queue"""
        if not self.is_open:
            raise Exception("Channel is closed")
            
        if not queue:
            queue = f"amq.gen-{uuid.uuid4()}"
            
        self.queues[queue] = {
            'messages': deque(),
            'durable': durable,
            'exclusive': exclusive,
            'auto_delete': auto_delete,
            'arguments': arguments or {},
            'message_count': 0,
            'consumer_count': 0
        }
        
        logger.info(f"Queue declared: {queue}")
        
        # Return mock method frame
        class MethodFrame:
            def __init__(self, queue_name, message_count=0, consumer_count=0):
                self.method = type('method', (), {
                    'queue': queue_name,
                    'message_count': message_count,
                    'consumer_count': consumer_count
                })()
                
        return MethodFrame(queue, 0, 0)
        
    def queue_bind(self, queue, exchange, routing_key=''):
        """Bind a queue to an exchange"""
        if not self.is_open:
            raise Exception("Channel is closed")
            
        if exchange not in self.exchanges:
            raise Exception(f"Exchange '{exchange}' does not exist")
            
        if queue not in self.queues:
            raise Exception(f"Queue '{queue}' does not exist")
            
        binding = {
            'queue': queue,
            'exchange': exchange,
            'routing_key': routing_key
        }
        
        key = f"{exchange}:{routing_key}"
        if binding not in self.bindings[key]:
            self.bindings[key].append(binding)
            
        logger.info(f"Queue bound: {queue} -> {exchange} (routing_key: {routing_key})")
        
    def basic_publish(self, exchange, routing_key, body, properties=None, mandatory=False):
        """Publish a message"""
        if not self.is_open:
            raise Exception("Channel is closed")
            
        if isinstance(body, str):
            body = body.encode('utf-8')
            
        message = MockMessage(
            body=body,
            properties=properties or {},
            exchange=exchange,
            routing_key=routing_key
        )
        
        # Route message to appropriate queues
        routed = False
        
        if exchange == '':
            # Direct to queue routing
            if routing_key in self.queues:
                self.queues[routing_key]['messages'].append(message)
                self.queues[routing_key]['message_count'] += 1
                routed = True
                logger.debug(f"Message published directly to queue: {routing_key}")
        else:
            # Exchange routing
            if exchange in self.exchanges:
                exchange_type = self.exchanges[exchange]['type']
                
                for binding_key, bindings in self.bindings.items():
                    for binding in bindings:
                        if binding['exchange'] != exchange:
                            continue
                            
                        match = False
                        if exchange_type == 'direct':
                            match = binding['routing_key'] == routing_key
                        elif exchange_type == 'topic':
                            match = self._match_topic(binding['routing_key'], routing_key)
                        elif exchange_type == 'fanout':
                            match = True
                            
                        if match:
                            queue_name = binding['queue']
                            if queue_name in self.queues:
                                self.queues[queue_name]['messages'].append(message)
                                self.queues[queue_name]['message_count'] += 1
                                routed = True
                                
        if mandatory and not routed:
            raise Exception(f"Message could not be routed: exchange={exchange}, routing_key={routing_key}")
            
    def basic_consume(self, queue, on_message_callback, auto_ack=False, 
                     exclusive=False, consumer_tag=None, arguments=None):
        """Start consuming messages from a queue"""
        if not self.is_open:
            raise Exception("Channel is closed")
            
        if queue not in self.queues:
            raise Exception(f"Queue '{queue}' does not exist")
            
        if not consumer_tag:
            consumer_tag = f"ctag-{uuid.uuid4()}"
            
        self.consumers[consumer_tag] = {
            'queue': queue,
            'callback': on_message_callback,
            'auto_ack': auto_ack,
            'exclusive': exclusive,
            'arguments': arguments or {}
        }
        
        self.queues[queue]['consumer_count'] += 1
        self.consumer_tags[queue] = consumer_tag
        
        logger.info(f"Consumer started: {consumer_tag} on queue {queue}")
        
        # Start delivering messages if any are queued
        self._deliver_messages(queue)
        
        return consumer_tag
        
    def basic_ack(self, delivery_tag, multiple=False):
        """Acknowledge one or more messages"""
        if not self.is_open:
            raise Exception("Channel is closed")
        logger.debug(f"Message acknowledged: {delivery_tag} (multiple: {multiple})")
        
    def basic_nack(self, delivery_tag, multiple=False, requeue=True):
        """Negative acknowledge one or more messages"""
        if not self.is_open:
            raise Exception("Channel is closed")
        logger.debug(f"Message nacked: {delivery_tag} (multiple: {multiple}, requeue: {requeue})")
        
    def basic_reject(self, delivery_tag, requeue=True):
        """Reject a message"""
        if not self.is_open:
            raise Exception("Channel is closed")
        logger.debug(f"Message rejected: {delivery_tag} (requeue: {requeue})")
        
    def basic_qos(self, prefetch_size=0, prefetch_count=0, global_qos=False):
        """Set quality of service parameters"""
        if not self.is_open:
            raise Exception("Channel is closed")
        self.prefetch_count = prefetch_count
        logger.info(f"QoS set: prefetch_count={prefetch_count}")
        
    def queue_delete(self, queue, if_unused=False, if_empty=False):
        """Delete a queue"""
        if not self.is_open:
            raise Exception("Channel is closed")
            
        if queue in self.queues:
            queue_info = self.queues[queue]
            
            if if_unused and queue_info['consumer_count'] > 0:
                raise Exception(f"Queue '{queue}' has consumers")
                
            if if_empty and queue_info['message_count'] > 0:
                raise Exception(f"Queue '{queue}' is not empty")
                
            del self.queues[queue]
            logger.info(f"Queue deleted: {queue}")
            
    def exchange_delete(self, exchange, if_unused=False):
        """Delete an exchange"""
        if not self.is_open:
            raise Exception("Channel is closed")
            
        if exchange in self.exchanges:
            del self.exchanges[exchange]
            # Remove related bindings
            self.bindings = {k: v for k, v in self.bindings.items() 
                           if not any(b['exchange'] == exchange for b in v)}
            logger.info(f"Exchange deleted: {exchange}")
            
    def close(self):
        """Close the channel"""
        self.is_open = False
        logger.info(f"Channel {self.channel_number} closed")
        
    def _deliver_messages(self, queue):
        """Deliver queued messages to consumers"""
        if queue not in self.queues or queue not in self.consumer_tags:
            return
            
        consumer_tag = self.consumer_tags[queue]
        if consumer_tag not in self.consumers:
            return
            
        consumer = self.consumers[consumer_tag]
        queue_info = self.queues[queue]
        
        while queue_info['messages']:
            message = queue_info['messages'].popleft()
            queue_info['message_count'] -= 1
            
            # Create delivery info
            self._delivery_tag_counter += 1
            
            class Method:
                def __init__(self, delivery_tag, redelivered=False):
                    self.delivery_tag = delivery_tag
                    self.redelivered = redelivered
                    self.exchange = message.exchange
                    self.routing_key = message.routing_key
                    
            class Properties:
                def __init__(self, message_properties):
                    for key, value in message_properties.items():
                        setattr(self, key, value)
                        
            method = Method(self._delivery_tag_counter, message.redelivered)
            properties = Properties(message.properties)
            
            # Call the callback
            try:
                consumer['callback'](self, method, properties, message.body)
                if consumer['auto_ack']:
                    self.basic_ack(method.delivery_tag)
            except Exception as e:
                logger.error(f"Error in consumer callback: {e}")
                if not consumer['auto_ack']:
                    self.basic_nack(method.delivery_tag, requeue=True)
                    
    def _match_topic(self, pattern, topic):
        """Match topic routing patterns"""
        pattern_parts = pattern.split('.')
        topic_parts = topic.split('.')
        
        if len(pattern_parts) != len(topic_parts):
            return False
            
        for p, t in zip(pattern_parts, topic_parts):
            if p == '#':
                return True
            elif p == '*':
                continue
            elif p != t:
                return False
                
        return True

class MockConnection:
    """Mock RabbitMQ connection"""
    
    def __init__(self, host='localhost', port=5672, virtual_host='/', 
                 credentials=None, **kwargs):
        self.host = host
        self.port = port
        self.virtual_host = virtual_host
        self.credentials = credentials
        self.is_open = True
        self.channels = {}
        self._channel_counter = 0
        self.params = kwargs
        logger.info(f"Mock connection created: {host}:{port}/{virtual_host}")
        
    def channel(self):
        """Create a new channel"""
        if not self.is_open:
            raise Exception("Connection is closed")
            
        self._channel_counter += 1
        channel = MockChannel(self, self._channel_counter)
        self.channels[self._channel_counter] = channel
        return channel
        
    def close(self):
        """Close the connection"""
        for channel in self.channels.values():
            if channel.is_open:
                channel.close()
        self.is_open = False
        logger.info("Connection closed")
        
    def is_closed(self):
        """Check if connection is closed"""
        return not self.is_open
        
    def is_closing(self):
        """Check if connection is closing"""
        return False
        
    def is_open(self):
        """Check if connection is open"""
        return self.is_open

class BlockingConnection(MockConnection):
    """Mock pika BlockingConnection"""
    pass

class ConnectionParameters:
    """Mock pika ConnectionParameters"""
    
    def __init__(self, host='localhost', port=5672, virtual_host='/', 
                 credentials=None, **kwargs):
        self.host = host
        self.port = port
        self.virtual_host = virtual_host
        self.credentials = credentials
        self.heartbeat = kwargs.get('heartbeat', 600)
        self.blocked_connection_timeout = kwargs.get('blocked_connection_timeout', 300)
        self.connection_attempts = kwargs.get('connection_attempts', 1)
        self.retry_delay = kwargs.get('retry_delay', 2.0)
        self.socket_timeout = kwargs.get('socket_timeout', 10.0)
        
class PlainCredentials:
    """Mock pika credentials"""
    
    def __init__(self, username, password):
        self.username = username
        self.password = password

# Mock pika module exports
__all__ = [
    'BlockingConnection',
    'ConnectionParameters', 
    'PlainCredentials',
    'MockConnection',
    'MockChannel',
    'MockMessage'
]