"""
Knowledge Sage A2Aプロキシ
エルダー評議会令第30号に基づく実装
"""

from typing import Any, Dict, List, Optional

from .base_sage_proxy import BaseSageProxy


class KnowledgeSageProxy(BaseSageProxy):
    """Knowledge Sage へのA2Aプロキシ"""

    def _get_sage_type(self) -> str:
        """賢者タイプを返す"""
        return "knowledge_sage"

    async def get_knowledge(
        self, query: str, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """知識を取得"""
        return await self.call_sage("get_knowledge", query=query, context=context or {})

    async def save_knowledge(
        self, category: str, content: str, metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """知識を保存"""
        return await self.call_sage(
            "save_knowledge",
            category=category,
            content=content,
            metadata=metadata or {},
        )

    async def search_knowledge(
        self, keywords: List[str], filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """知識を検索"""
        return await self.call_sage(
            "search_knowledge", keywords=keywords, filters=filters or {}
        )

    async def analyze_knowledge_gap(self, domain: str) -> Dict[str, Any]:
        """知識ギャップを分析"""
        return await self.call_sage("analyze_knowledge_gap", domain=domain)

    async def update_knowledge(
        self, knowledge_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """知識を更新"""
        return await self.call_sage(
            "update_knowledge", knowledge_id=knowledge_id, updates=updates
        )

    async def delete_knowledge(self, knowledge_id: str) -> Dict[str, Any]:
        """知識を削除"""
        return await self.call_sage("delete_knowledge", knowledge_id=knowledge_id)

    async def get_knowledge_stats(
        self, category: Optional[str] = None
    ) -> Dict[str, Any]:
        """知識統計を取得"""
        return await self.call_sage("get_knowledge_stats", category=category)

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """汎用リクエスト処理（後方互換性のため）"""
        return await self.call_sage("process_request", request=request)


# シングルトンインスタンス（オプション）
_knowledge_sage_proxy = None


def get_knowledge_sage_proxy() -> KnowledgeSageProxy:
    """Knowledge Sage プロキシのシングルトンインスタンスを取得"""
    global _knowledge_sage_proxy
    if _knowledge_sage_proxy is None:
        _knowledge_sage_proxy = KnowledgeSageProxy()
    return _knowledge_sage_proxy
