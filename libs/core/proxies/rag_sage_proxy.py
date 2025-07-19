"""
RAG Sage A2Aプロキシ
エルダー評議会令第30号に基づく実装
"""

from typing import Any, Dict, List, Optional

from .base_sage_proxy import BaseSageProxy


class RAGSageProxy(BaseSageProxy):
    """RAG Sage へのA2Aプロキシ"""

    def _get_sage_type(self) -> str:
        """賢者タイプを返す"""
        return "rag_sage"

    async def search_documents(
        self, query: str, filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """ドキュメントを検索"""
        return await self.call_sage(
            "search_documents", query=query, filters=filters or {}
        )

    async def generate_answer(
        self, question: str, context: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """回答を生成"""
        return await self.call_sage(
            "generate_answer", question=question, context=context or []
        )

    async def index_document(
        self, document: Dict[str, Any], metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """ドキュメントをインデックス"""
        return await self.call_sage(
            "index_document", document=document, metadata=metadata or {}
        )

    async def semantic_search(
        self, query: str, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """意味検索を実行"""
        return await self.call_sage("semantic_search", query=query, top_k=top_k)

    async def update_index(
        self, document_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """インデックスを更新"""
        return await self.call_sage(
            "update_index", document_id=document_id, updates=updates
        )

    async def delete_from_index(self, document_id: str) -> Dict[str, Any]:
        """インデックスから削除"""
        return await self.call_sage("delete_from_index", document_id=document_id)

    async def get_index_stats(self) -> Dict[str, Any]:
        """インデックス統計を取得"""
        return await self.call_sage("get_index_stats")

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """汎用リクエスト処理（後方互換性のため）"""
        return await self.call_sage("process_request", request=request)


# シングルトンインスタンス（オプション）
_rag_sage_proxy = None


def get_rag_sage_proxy() -> RAGSageProxy:
    """RAG Sage プロキシのシングルトンインスタンスを取得"""
    global _rag_sage_proxy
    if _rag_sage_proxy is None:
        _rag_sage_proxy = RAGSageProxy()
    return _rag_sage_proxy
