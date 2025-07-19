"""
Task Sage A2Aプロキシ
エルダー評議会令第30号に基づく実装
"""
from typing import Any, Dict, List, Optional

from .base_sage_proxy import BaseSageProxy


class TaskSageProxy(BaseSageProxy):
    """Task Sage へのA2Aプロキシ"""

    def _get_sage_type(self) -> str:
        """賢者タイプを返す"""
        return "task_sage"

    async def create_task(
        self, title: str, description: str, priority: str = "medium"
    ) -> Dict[str, Any]:
        """タスクを作成"""
        return await self.call_sage(
            "create_task", title=title, description=description, priority=priority
        )

    async def update_task_status(self, task_id: str, status: str) -> Dict[str, Any]:
        """タスクステータスを更新"""
        return await self.call_sage(
            "update_task_status", task_id=task_id, status=status
        )

    async def get_task_list(
        self, status: Optional[str] = None, priority: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """タスクリストを取得"""
        return await self.call_sage("get_task_list", status=status, priority=priority)

    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """タスクを取得"""
        return await self.call_sage("get_task", task_id=task_id)

    async def analyze_task_progress(self) -> Dict[str, Any]:
        """タスク進捗を分析"""
        return await self.call_sage("analyze_task_progress")

    async def assign_task(self, task_id: str, assignee: str) -> Dict[str, Any]:
        """タスクを割り当て"""
        return await self.call_sage("assign_task", task_id=task_id, assignee=assignee)

    async def prioritize_tasks(self, task_ids: List[str]) -> List[Dict[str, Any]]:
        """タスクの優先順位を設定"""
        return await self.call_sage("prioritize_tasks", task_ids=task_ids)

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """汎用リクエスト処理（後方互換性のため）"""
        return await self.call_sage("process_request", request=request)


# シングルトンインスタンス（オプション）
_task_sage_proxy = None


def get_task_sage_proxy() -> TaskSageProxy:
    """Task Sage プロキシのシングルトンインスタンスを取得"""
    global _task_sage_proxy
    if _task_sage_proxy is None:
        _task_sage_proxy = TaskSageProxy()
    return _task_sage_proxy
