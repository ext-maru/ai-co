"""
🏛️ Ancient Elder System
エンシェントエルダーによる6つの古代魔法を統合した監査システム
"""

from .base import AncientElderBase
from .audit_engine import AncientElderAuditEngine
from .integrity_auditor import AncientElderIntegrityAuditor

__all__ = [
    "AncientElderBase",
    "AncientElderAuditEngine", 
    "AncientElderIntegrityAuditor",
]

# System version
__version__ = "1.0.0"