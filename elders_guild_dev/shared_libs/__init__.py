"""
Elder Tree Shared Libraries
共有ライブラリのエクスポート
"""

from .soul_base import BaseSoul, SoulContext
from .a2a_protocol import (
    A2AMessage,
    A2ACommunicator,
    LocalA2ACommunicator,
    MessageType,
    MessagePriority
)

__all__ = [
    # Base Classes
    "BaseSoul",
    "SoulContext",
    
    # A2A Protocol
    "A2AMessage",
    "A2ACommunicator", 
    "LocalA2ACommunicator",
    "MessageType",
    "MessagePriority",
]

__version__ = "1.0.0"