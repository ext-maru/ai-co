"""
RAG Sage - RAG賢者システム

既存のRAG Managerから実装をインポートして使用
"""

# 既存のRAG Managerから実装をインポート
from libs.rag_manager import RagManager

# RAGSageはRagManagerのエイリアス
RAGSage = RagManager


# 互換性のための関数
def setup(*args, **kwargs):
    """セットアップ関数"""
    return RagManager()


def main(*args, **kwargs):
    """メイン関数"""
    return RagManager()


# Export
__all__ = ["RAGSage", "setup", "main"]