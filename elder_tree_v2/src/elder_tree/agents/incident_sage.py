"""
Incident Sage - 危機管理・障害対応専門AI
TDD Green Phase: 実装フェーズ
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from elder_tree.agents.base_agent import ElderTreeAgent
from sqlmodel import SQLModel, Field, Session, create_engine, select
from prometheus_client import Counter, Gauge, Histogram
import structlog
import redis.asyncio as redis
from anthropic import AsyncAnthropic


class IncidentSeverity(str, Enum):
    """インシデント深刻度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """インシデントステータス"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MONITORING = "monitoring"
    RESOLVED = "resolved"


# SQLModel Incident定義
class Incident(SQLModel, table=True):
    """インシデントモデル"""
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: str = Field(index=True, unique=True)
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus = Field(default=IncidentStatus.OPEN)
    affected_services: str = Field(default="[]")  # JSON array
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    detected_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    response_time_minutes: Optional[float] = None
    

class IncidentSage(ElderTreeAgent):
    """
    Incident Sage - 危機管理・障害対応の専門家
    
    責務:
    - インシデント検知・エスカレーション
    - 根本原因分析
    - 緊急対応指示
    - 復旧手順管理
    - ポストモーテム実施
    """
    
    def __init__(self, 
                 db_url: str = "sqlite:///incidents.db",
                 redis_url: str = "redis://localhost:6379"):
        super().__init__(
            name="incident_sage",
            domain="incident",
            port=50053
        )
        
        # データベース初期化
        self.engine = create_engine(db_url)
        SQLModel.metadata.create_all(self.engine)
        
        # Redis接続（アラート管理用）
        self.redis_url = redis_url
        self.redis_client = None
        
        # Claude API（高度な分析用）
        self.anthropic = AsyncAnthropic()
        
        # 追加メトリクス
        self.incident_count = Gauge(
            'incident_sage_active_incidents',
            'Number of active incidents',
            ['severity', 'status']
        )
        
        self.response_time = Histogram(
            'incident_sage_response_time_seconds',
            'Incident response time',
            ['severity']
        )
        
        self.escalation_counter = Counter(
            'incident_sage_escalations_total',
            'Total escalations',
            ['severity', 'target']
        )
        
        # ドメイン固有ハンドラー登録
        self._register_domain_handlers()
        
        self.logger.info("IncidentSage initialized")
    
    async def start(self):
        """起動時処理"""
        await super().start()
        # Redis接続
        self.redis_client = await redis.from_url(self.redis_url)
        self.logger.info("Connected to Redis for alert management")
    
    async def stop(self):
        """停止時処理"""
        if self.redis_client:
            await self.redis_client.close()
        await super().stop()
    
    def _register_domain_handlers(self):
        """Incident Sage専用ハンドラー登録"""
        
        @self.on_message("detect_incident")
        async def handle_detect_incident(message) -> Dict[str, Any]:
            """
            インシデント検知・記録
            
            Input:
                - title: インシデントタイトル
                - description: 詳細説明
                - severity: 深刻度
                - affected_services: 影響サービスリスト
                - source: 検知元（monitoring, user_report, etc）
            """
            data = message.data
            
            # インシデントID生成
            incident_id = f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 深刻度判定（必要に応じてAI分析）
            severity = data.get("severity", IncidentSeverity.MEDIUM)
            if severity == IncidentSeverity.CRITICAL:
                # 緊急エスカレーション
                await self._escalate_critical_incident(incident_id, data)
            
            with Session(self.engine) as session:
                incident = Incident(
                    incident_id=incident_id,
                    title=data.get("title", "Unknown Incident"),
                    description=data.get("description", ""),
                    severity=severity,
                    status=IncidentStatus.OPEN,
                    affected_services=json.dumps(data.get("affected_services", [])),
                    detected_at=datetime.now()
                )
                
                session.add(incident)
                session.commit()
                session.refresh(incident)
                
                # メトリクス更新
                self.incident_count.labels(
                    severity=incident.severity,
                    status=incident.status
                ).inc()
                
                # Redisにアラート登録
                if self.redis_client:
                    await self.redis_client.setex(
                        f"alert:{incident_id}",
                        3600,  # 1時間TTL
                        json.dumps({
                            "incident_id": incident_id,
                            "severity": severity,
                            "timestamp": datetime.now().isoformat()
                        })
                    )
                
                # 他の賢者に通知
                await self._notify_sages_about_incident(incident)
                
                return {
                    "status": "success",
                    "incident_id": incident_id,
                    "severity": severity,
                    "message": f"Incident {incident_id} detected and logged"
                }
        
        @self.on_message("analyze_root_cause")
        async def handle_analyze_root_cause(message) -> Dict[str, Any]:
            """
            根本原因分析（AI支援）
            """
            incident_id = message.data.get("incident_id")
            additional_info = message.data.get("additional_info", {})
            
            with Session(self.engine) as session:
                statement = select(Incident).where(Incident.incident_id == incident_id)
                incident = session.exec(statement).first()
                
                if not incident:
                    return {"status": "error", "message": "Incident not found"}
                
                # Claude APIで高度な分析
                analysis_prompt = f"""
                インシデント分析:
                - タイトル: {incident.title}
                - 説明: {incident.description}
                - 影響サービス: {incident.affected_services}
                - 追加情報: {json.dumps(additional_info)}
                
                根本原因を分析し、以下を提供してください：
                1. 最も可能性の高い根本原因
                2. 確認すべき項目
                3. 推奨される対応手順
                """
                
                try:
                    response = await self.anthropic.messages.create(
                        model="claude-3-opus-20240229",
                        max_tokens=1000,
                        messages=[{
                            "role": "user",
                            "content": analysis_prompt
                        }]
                    )
                    
                    analysis_result = response.content[0].text
                    
                    # 分析結果を保存
                    incident.root_cause = analysis_result
                    incident.status = IncidentStatus.IDENTIFIED
                    session.add(incident)
                    session.commit()
                    
                    # RAG Sageに関連情報検索依頼
                    rag_results = await self.collaborate_with_sage(
                        "rag_sage",
                        {
                            "action": "search_similar_incidents",
                            "keywords": [incident.title, incident.severity],
                            "limit": 5
                        }
                    )
                    
                    return {
                        "status": "success",
                        "incident_id": incident_id,
                        "root_cause_analysis": analysis_result,
                        "similar_incidents": rag_results.data if rag_results else []
                    }
                    
                except Exception as e:
                    self.logger.error("Root cause analysis failed", error=str(e))
                    return {
                        "status": "error",
                        "message": f"Analysis failed: {str(e)}"
                    }
        
        @self.on_message("update_incident_status")
        async def handle_update_status(message) -> Dict[str, Any]:
            """
            インシデントステータス更新
            """
            incident_id = message.data.get("incident_id")
            new_status = message.data.get("status")
            resolution = message.data.get("resolution")
            
            with Session(self.engine) as session:
                statement = select(Incident).where(Incident.incident_id == incident_id)
                incident = session.exec(statement).first()
                
                if not incident:
                    return {"status": "error", "message": "Incident not found"}
                
                old_status = incident.status
                incident.status = new_status
                
                if new_status == IncidentStatus.RESOLVED:
                    incident.resolved_at = datetime.now()
                    incident.resolution = resolution
                    # 対応時間計算
                    response_time = (incident.resolved_at - incident.detected_at).total_seconds() / 60
                    incident.response_time_minutes = response_time
                    
                    # メトリクス記録
                    self.response_time.labels(
                        severity=incident.severity
                    ).observe(response_time * 60)  # 秒単位で記録
                
                session.add(incident)
                session.commit()
                
                # メトリクス更新
                self.incident_count.labels(
                    severity=incident.severity,
                    status=old_status
                ).dec()
                self.incident_count.labels(
                    severity=incident.severity,
                    status=new_status
                ).inc()
                
                return {
                    "status": "success",
                    "incident_id": incident_id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "resolved": new_status == IncidentStatus.RESOLVED
                }
        
        @self.on_message("get_active_incidents")
        async def handle_get_active_incidents(message) -> Dict[str, Any]:
            """
            アクティブなインシデント一覧取得
            """
            with Session(self.engine) as session:
                statement = select(Incident).where(
                    Incident.status != IncidentStatus.RESOLVED
                ).order_by(Incident.severity.desc(), Incident.detected_at.desc())
                
                active_incidents = session.exec(statement).all()
                
                incidents_list = []
                for incident in active_incidents:
                    incidents_list.append({
                        "incident_id": incident.incident_id,
                        "title": incident.title,
                        "severity": incident.severity,
                        "status": incident.status,
                        "affected_services": json.loads(incident.affected_services),
                        "detected_at": incident.detected_at.isoformat(),
                        "duration_minutes": round(
                            (datetime.now() - incident.detected_at).total_seconds() / 60, 1
                        )
                    })
                
                return {
                    "status": "success",
                    "active_incidents": incidents_list,
                    "count": len(incidents_list),
                    "critical_count": sum(
                        1 for inc in incidents_list 
                        if inc["severity"] == IncidentSeverity.CRITICAL
                    )
                }
        
        @self.on_message("generate_postmortem")
        async def handle_generate_postmortem(message) -> Dict[str, Any]:
            """
            ポストモーテム生成
            """
            incident_id = message.data.get("incident_id")
            
            with Session(self.engine) as session:
                statement = select(Incident).where(Incident.incident_id == incident_id)
                incident = session.exec(statement).first()
                
                if not incident:
                    return {"status": "error", "message": "Incident not found"}
                
                if incident.status != IncidentStatus.RESOLVED:
                    return {
                        "status": "error", 
                        "message": "Incident must be resolved before generating postmortem"
                    }
                
                postmortem = {
                    "incident_id": incident.incident_id,
                    "title": incident.title,
                    "severity": incident.severity,
                    "timeline": {
                        "detected_at": incident.detected_at.isoformat(),
                        "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
                        "total_duration_minutes": incident.response_time_minutes
                    },
                    "impact": {
                        "affected_services": json.loads(incident.affected_services),
                        "severity": incident.severity
                    },
                    "root_cause": incident.root_cause or "Not analyzed",
                    "resolution": incident.resolution or "Not documented",
                    "lessons_learned": [
                        "Incident detection was successful",
                        f"Response time: {incident.response_time_minutes:.1f} minutes",
                        "Consider implementing preventive measures"
                    ],
                    "action_items": [
                        "Review monitoring thresholds",
                        "Update runbooks",
                        "Conduct team training if needed"
                    ]
                }
                
                # Knowledge Sageに学習データとして送信
                await self.collaborate_with_sage(
                    "knowledge_sage",
                    {
                        "action": "store_postmortem",
                        "postmortem": postmortem
                    }
                )
                
                return {
                    "status": "success",
                    "postmortem": postmortem
                }
    
    async def _escalate_critical_incident(self, incident_id: str, data: Dict[str, Any]):
        """クリティカルインシデントのエスカレーション"""
        self.escalation_counter.labels(
            severity=IncidentSeverity.CRITICAL,
            target="all_sages"
        ).inc()
        
        # 全賢者に緊急通知
        escalation_message = {
            "action": "critical_incident_alert",
            "incident_id": incident_id,
            "title": data.get("title"),
            "severity": IncidentSeverity.CRITICAL,
            "affected_services": data.get("affected_services", [])
        }
        
        # 並列で全賢者に通知
        tasks = [
            self.collaborate_with_sage("knowledge_sage", escalation_message),
            self.collaborate_with_sage("task_sage", escalation_message),
            self.collaborate_with_sage("rag_sage", escalation_message)
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        self.logger.warning(
            "Critical incident escalated to all sages",
            incident_id=incident_id
        )
    
    async def _notify_sages_about_incident(self, incident: Incident):
        """インシデントについて関連賢者に通知"""
        notification = {
            "action": "incident_notification",
            "incident_id": incident.incident_id,
            "severity": incident.severity,
            "affected_services": json.loads(incident.affected_services)
        }
        
        # Task Sageに通知（タスク優先度調整のため）
        if incident.severity in [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]:
            await self.collaborate_with_sage("task_sage", notification)


# 単体実行用
async def main():
    sage = IncidentSage()
    await sage.start()
    print(f"Incident Sage running on port {sage.port}")
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await sage.stop()


if __name__ == "__main__":
    asyncio.run(main())