"""
エルダーズギルド A2Aプロキシ
エルダー評議会令第30号に基づく実装
"""

from .base_sage_proxy import BaseSageProxy
from .incident_sage_proxy import IncidentSageProxy, get_incident_sage_proxy
from .knowledge_sage_proxy import KnowledgeSageProxy, get_knowledge_sage_proxy
from .rag_sage_proxy import RAGSageProxy, get_rag_sage_proxy
from .task_sage_proxy import TaskSageProxy, get_task_sage_proxy

__all__ = [
    "BaseSageProxy",
    "KnowledgeSageProxy",
    "TaskSageProxy",
    "IncidentSageProxy",
    "RAGSageProxy",
    "get_knowledge_sage_proxy",
    "get_task_sage_proxy",
    "get_incident_sage_proxy",
    "get_rag_sage_proxy",
]
