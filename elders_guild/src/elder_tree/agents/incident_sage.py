"""
Incident Sage Implementation
インシデント管理・緊急対応エージェント
"""

from elder_tree.agents.base_agent import ElderTreeAgent
from typing import Dict, Any, List
import os
from datetime import datetime


class IncidentSage(ElderTreeAgent):
    """Incident Sage - インシデント管理専門エージェント"""
    
    def __init__(self, port: int = 50053):
        super().__init__(
            name="incident_sage",
            domain="incident",
            port=port
        )
        
        self.incidents = {}
        self.incident_counter = 0
        
        self.logger.info("Incident Sage initialized")
    
    def handle_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """メッセージハンドラー"""
        message_type = data.get('type', 'unknown')
        
        # 基本メッセージタイプの処理
        if message_type in ["health_check", "get_metrics"]:
            return super().handle_message(data)
        
        # Incident Sage固有のメッセージタイプ処理
        if message_type == "detect_incident":
            return self._handle_detect_incident(data)
        elif message_type == "update_incident":
            return self._handle_update_incident(data)
        elif message_type == "get_incidents":
            return self._handle_get_incidents(data)
        elif message_type == "elder_flow_consultation":
            return self._handle_elder_flow_consultation(data)
        else:
            return {"status": "error", "message": f"Unknown message type: {message_type}"}
    
    def _handle_detect_incident(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """インシデント検知"""
        self.incident_counter += 1
        incident_id = f"INC-{self.incident_counter:04d}"
        
        incident = {
            "id": incident_id,
            "title": data.get("title", "Unknown Incident"),
            "description": data.get("description", ""),
            "severity": data.get("severity", "medium"),
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "affected_services": data.get("affected_services", []),
            "source": data.get("source", "unknown")
        }
        
        self.incidents[incident_id] = incident
        
        return {
            "status": "success",
            "incident": incident
        }
    
    def _handle_update_incident(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """インシデント更新"""
        incident_id = data.get("incident_id")
        if incident_id not in self.incidents:
            return {"status": "error", "message": "Incident not found"}
        
        # 更新可能なフィールドを更新
        updatable_fields = ["status", "severity", "description"]
        for field in updatable_fields:
            if field in data:
                self.incidents[incident_id][field] = data[field]
        
        self.incidents[incident_id]["updated_at"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "incident": self.incidents[incident_id]
        }
    
    def _handle_get_incidents(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """インシデント一覧取得"""
        status_filter = data.get("status")
        severity_filter = data.get("severity")
        
        filtered_incidents = []
        for incident in self.incidents.values():
            if status_filter and incident["status"] != status_filter:
                continue
            if severity_filter and incident["severity"] != severity_filter:
                continue
            filtered_incidents.append(incident)
        
        return {
            "status": "success",
            "incidents": filtered_incidents,
            "count": len(filtered_incidents)
        }
    
    def _handle_elder_flow_consultation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Elder Flow協議処理"""
        task_type = data.get("task_type", "unknown")
        requirements = data.get("requirements", [])
        
        # インシデント管理の観点からの推奨事項
        recommendations = [
            "Monitor for potential incidents",
            "Setup alerting and notifications",
            "Prepare rollback procedures"
        ]
        
        # リスク評価（簡易版）
        risk_level = "high" if "critical" in task_type.lower() else "medium"
        
        return {
            "status": "success",
            "recommendations": recommendations,
            "risk_level": risk_level,
            "monitoring_required": True
        }


# 単体実行用
def main():
    """mainメソッド"""
    # Create Incident Sage
    port = int(os.getenv("INCIDENT_SAGE_PORT", 50053))
    sage = IncidentSage(port=port)
    
    # Create Flask app
    app = sage.create_app()
    
    # Consul registration (optional)
    if os.getenv("CONSUL_HOST"):
        try:
            import consul
            c = consul.Consul(
                host=os.getenv("CONSUL_HOST"),
                port=int(os.getenv("CONSUL_PORT", 8500))
            )
            c.agent.service.register(
                name="incident-sage",
                service_id=f"incident-sage-{port}",
                address="incident_sage",
                port=port,
                tags=["elder-tree", "sage", "incident"],
                check=consul.Check.http(f"http://incident_sage:{port}/health", interval="10s")
            )
            print(f"Registered with Consul as incident-sage")
        except ImportError:
            print("Consul client not available, skipping registration")
        except Exception as e:
            print(f"Failed to register with Consul: {e}")
    
    # Start Flask app
    print(f"Incident Sage running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()