#!/usr/bin/env python3
"""
PROJECT ELDERZAN - Session Management Module
プロジェクトエルダーザン セッション管理モジュール

Elders Guild 80-95%コストカット実現の核心システム
エルダー評議会 + 4賢者システム監修による次世代セッション管理

主要コンポーネント:
- SessionContextManager: セッション間知識継続システム
- SessionContext: セッションデータモデル
- HybridStorage: SQLite + JSON + Vector統合ストレージ
- SecurityLayer: AES-256暗号化・RBAC・監査ログ
- FourSagesIntegration: 4賢者システム統合

4賢者との連携:
📚 ナレッジ賢者: 知識永続化・統合戦略
📋 タスク賢者: タスク管理・優先順位
🚨 インシデント賢者: セキュリティ・障害対策
🔍 RAG賢者: ベクトル検索・コンテキスト圧縮
"""

__version__ = "1.0.0"
__project__ = "PROJECT ELDERZAN"
__module__ = "Session Management"
__authority__ = "エルダー評議会 + 4賢者システム"

from .models import SageInteraction, SessionContext, SessionMetadata

__all__ = [
    "SessionContext",
    "SessionMetadata",
    "SageInteraction",
]
