"""Mock pika module for testing"""
from unittest.mock import MagicMock, Mock


# Create mock pika module structure
class exceptions:
    """Mock pika.exceptions"""

    AMQPConnectionError = Exception
    AMQPChannelError = Exception
    ConnectionClosed = Exception
    ChannelClosed = Exception
    StreamLostError = Exception


class BlockingConnection:
    """Mock BlockingConnection"""

    def __init__(self, *args, **kwargs):
        self.channel_obj = MockChannel()
        self.is_open = True

    def channel(self):
        return self.channel_obj

    def close(self):
        self.is_open = False


class MockChannel:
    """Mock Channel"""

    def __init__(self):
        self.is_open = True
        self.queues = {}

    def queue_declare(
        """queue_declareメソッド"""
        self, queue="", durable=False, exclusive=False, auto_delete=False
    ):
        self.queues[queue] = {"durable": durable}
        return Mock(method=Mock(queue=queue))

    def basic_consume(self, queue, on_message_callback, auto_ack=False):
        return "consumer_tag"

    def basic_ack(self, delivery_tag):
        pass

    def basic_nack(self, delivery_tag, requeue=False):
        pass

    def basic_publish(self, exchange, routing_key, body, properties=None):
        pass

    def start_consuming(self):
        pass

    def stop_consuming(self):
        pass

    def close(self):
        self.is_open = False


class ConnectionParameters:
    """Mock ConnectionParameters"""

    def __init__(self, host="localhost", port=5672, virtual_host="/", credentials=None):
        self.host = host
        self.port = port
        self.virtual_host = virtual_host
        self.credentials = credentials


class PlainCredentials:
    """Mock PlainCredentials"""

    def __init__(self, username, password):
        self.username = username
        self.password = password


class BasicProperties:
    """Mock BasicProperties"""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
