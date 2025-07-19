"""
Incident Sage A2Aプロキシ
エルダー評議会令第30号に基づく実装
"""
from typing import Dict, List, Optional, Any
from .base_sage_proxy import BaseSageProxy


class IncidentSageProxy(BaseSageProxy):
    """Incident Sage へのA2Aプロキシ"""
    
    def _get_sage_type(self) -> str:
        """賢者タイプを返す"""
        return "incident_sage"
    
    async def report_incident(self, severity: str, title: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """インシデントを報告"""
        return await self.call_sage(
            "report_incident",
            severity=severity,
            title=title,
            details=details
        )
    
    async def analyze_incident(self, incident_id: str) -> Dict[str, Any]:
        """インシデントを分析"""
        return await self.call_sage(
            "analyze_incident",
            incident_id=incident_id
        )
    
    async def get_incident_status(self, incident_id: str) -> Dict[str, Any]:
        """インシデントステータスを取得"""
        return await self.call_sage(
            "get_incident_status",
            incident_id=incident_id
        )
    
    async def resolve_incident(self, incident_id: str, resolution: str) -> Dict[str, Any]:
        """インシデントを解決"""
        return await self.call_sage(
            "resolve_incident",
            incident_id=incident_id,
            resolution=resolution
        )
    
    async def get_incident_list(self, status: Optional[str] = None, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """インシデントリストを取得"""
        return await self.call_sage(
            "get_incident_list",
            status=status,
            severity=severity
        )
    
    async def emergency_response(self, incident_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """緊急対応"""
        return await self.call_sage(
            "emergency_response",
            incident_type=incident_type,
            context=context
        )
    
    async def get_incident_stats(self, period: Optional[str] = None) -> Dict[str, Any]:
        """インシデント統計を取得"""
        return await self.call_sage(
            "get_incident_stats",
            period=period
        )
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """汎用リクエスト処理（後方互換性のため）"""
        return await self.call_sage(
            "process_request",
            request=request
        )


# シングルトンインスタンス（オプション）
_incident_sage_proxy = None

def get_incident_sage_proxy() -> IncidentSageProxy:
    """Incident Sage プロキシのシングルトンインスタンスを取得"""
    global _incident_sage_proxy
    if _incident_sage_proxy is None:
        _incident_sage_proxy = IncidentSageProxy()
    return _incident_sage_proxy