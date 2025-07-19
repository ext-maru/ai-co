#!/usr/bin/env python3
"""
PROJECT ELDERZAN SecurityLayer
プロジェクトエルダーザン セキュリティレイヤー

統合セキュリティシステム - AES-256暗号化 + RBAC + 監査ログ
80%コストカット実現のための高性能セキュリティ基盤

4賢者システム統合:
📚 ナレッジ賢者: セキュリティ知識統合・脅威パターン分析
📋 タスク賢者: 実装優先順位・品質管理
🚨 インシデント賢者: 脅威検出・緊急対応
🔍 RAG賢者: 暗号化検索・セキュアRAG
"""

from .authentication.rbac_manager import ElderZanRBACManager
from .core.encryption_engine import AES256EncryptionEngine
from .core.security_layer import ElderZanSecurityLayer
from .monitoring.audit_logger import ComplianceAuditLogger

__version__ = "1.0.0"
__author__ = "PROJECT ELDERZAN Team"
__description__ = "Unified Security Layer for 80% Cost Reduction"

__all__ = [
    "ElderZanSecurityLayer",
    "AES256EncryptionEngine",
    "ElderZanRBACManager",
    "ComplianceAuditLogger",
]
