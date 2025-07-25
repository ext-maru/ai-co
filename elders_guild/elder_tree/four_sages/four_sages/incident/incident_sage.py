"""
インシデント賢者 (Incident Sage)
システム監視、障害対応、セキュリティ管理を提供
"""

import hashlib
import json
import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import sys
from pathlib import Path

# Add elders_guild to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from shared_libs.config import config

from ..base_sage import BaseSage


class IncidentSeverity(Enum):
    """インシデント重要度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(Enum):
    """インシデント状態"""

    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentCategory(Enum):
    """インシデントカテゴリ"""

    SECURITY = "security"
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    DATA_INTEGRITY = "data_integrity"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    HARDWARE = "hardware"
    SOFTWARE = "software"


class IncidentSage(BaseSage):
    """インシデント賢者 - 障害対応とセキュリティ管理"""

    def __init__(self, data_path: Optional[str] = None):
        """初期化メソッド"""
        super().__init__("Incident")

        self.data_path = data_path or str(config.get_db_path("incidents"))
        self.db_path = os.path.join(self.data_path, "incidents.db")

        # データベース初期化
        self._init_database()

        # アラートルール
        self.alert_rules = {
            "error_rate_threshold": 5.0,  # 5%
            "response_time_threshold": 5000,  # 5秒
            "cpu_usage_threshold": 80.0,  # 80%
            "memory_usage_threshold": 85.0,  # 85%
            "disk_usage_threshold": 90.0,  # 90%
        }

        # セキュリティパターン
        self.security_patterns = [
            "sql injection",
            "xss attack",
            "brute force",
            "unauthorized access",
            "privilege escalation",
            "data breach",
            "malware",
            "ddos",
        ]

        self.logger.info("Incident Sage ready for crisis management")

    def _init_database(self):
        """インシデントデータベースの初期化"""
        os.makedirs(self.data_path, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # インシデントテーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    severity TEXT NOT NULL DEFAULT 'medium',
                    status TEXT NOT NULL DEFAULT 'open',
                    category TEXT NOT NULL DEFAULT 'software',
                    affected_systems TEXT,
                    impact_description TEXT,
                    root_cause TEXT,
                    resolution TEXT,
                    assignee TEXT,
                    reporter TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    estimated_resolution_time INTEGER,
                    actual_resolution_time INTEGER,
                    tags TEXT,
                    metadata TEXT
                )
            """
            )

            # インシデントログテーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS incident_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    user_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (incident_id) REFERENCES incidents(id)
                )
            """
            )

            # メトリクステーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    unit TEXT,
                    source_system TEXT NOT NULL,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tags TEXT
                )
            """
            )

            # アラートテーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT,
                    source_system TEXT,
                    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    acknowledged_at TIMESTAMP,
                    resolved_at TIMESTAMP,
                    acknowledged_by TEXT,
                    resolved_by TEXT,
                    incident_id TEXT,
                    metadata TEXT,
                    FOREIGN KEY (incident_id) REFERENCES incidents(id)
                )
            """
            )

            # セキュリティイベントテーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS security_events (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    source_ip TEXT,
                    target_ip TEXT,
                    user_agent TEXT,
                    event_details TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    investigated BOOLEAN DEFAULT FALSE,
                    incident_id TEXT,
                    metadata TEXT,
                    FOREIGN KEY (incident_id) REFERENCES incidents(id)
                )
            """
            )

            # インデックス作成
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_incident_severity ON incidents(severity)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_incident_status ON incidents(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_incident_category ON incidents(category)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_incident_created ON incidents(created_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_name ON system_metrics(metric_name)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_collected ON system_metrics(collected_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type)"
            )

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """インシデント賢者のリクエスト処理"""
        start_time = datetime.now()
        try:
            request_type = request.get("type", "unknown")

            if request_type == "create_incident":
                result = await self._create_incident(request)
            elif request_type == "update_incident":
                result = await self._update_incident(request)
            elif request_type == "get_incident":
                result = await self._get_incident(request)
            elif request_type == "list_incidents":
                result = await self._list_incidents(request)
            elif request_type == "resolve_incident":
                result = await self._resolve_incident(request)
            elif request_type == "create_alert":
                result = await self._create_alert(request)
            elif request_type == "acknowledge_alert":
                result = await self._acknowledge_alert(request)
            elif request_type == "record_metric":
                result = await self._record_metric(request)
            elif request_type == "analyze_metrics":
                result = await self._analyze_metrics(request)
            elif request_type == "security_scan":
                result = await self._security_scan(request)
            elif request_type == "get_dashboard":
                result = await self._get_dashboard(request)
            elif request_type == "escalate_incident":
                result = await self._escalate_incident(request)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown request type: {request_type}",
                    "supported_types": [
                        "create_incident",
                        "update_incident",
                        "get_incident",
                        "list_incidents",
                        "resolve_incident",
                        "create_alert",
                        "acknowledge_alert",
                        "record_metric",
                        "analyze_metrics",
                        "security_scan",
                        "get_dashboard",
                        "escalate_incident",
                    ],
                }

            # 処理時間を計算
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            result["processing_time_ms"] = processing_time

            await self.log_request(request, result)
            return result

        except Exception as e:
            await self.log_error(e, {"request": request})
            return {"success": False, "error": str(e), "sage": self.sage_name}

    async def _create_incident(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """新規インシデント作成"""
        title = request.get("title", "")
        description = request.get("description", "")
        severity = request.get("severity", IncidentSeverity.MEDIUM.value)
        category = request.get("category", IncidentCategory.SOFTWARE.value)
        affected_systems = request.get("affected_systems", [])
        impact_description = request.get("impact_description", "")
        reporter = request.get("reporter", "system")
        assignee = request.get("assignee")
        tags = request.get("tags", [])
        metadata = request.get("metadata", {})
        
        if not title:
            return {"success": False, "error": "Incident title is required"}

        incident_id = str(uuid.uuid4())

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # インシデント作成
            cursor.execute(
                """
                INSERT INTO incidents
                (id, title, description, severity, category, affected_systems,
                 impact_description, reporter, assignee, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    incident_id,
                    title,
                    description,
                    severity,
                    category,
                    json.dumps(affected_systems),
                    impact_description,
                    reporter,
                    assignee,
                    json.dumps(tags),
                    json.dumps(metadata),
                ),
            )

            # ログ記録
            cursor.execute(
                """
                INSERT INTO incident_logs (incident_id, action, details, user_id)
                VALUES (?, 'created', ?, ?)
            """,
                (
                    incident_id,
                    json.dumps({"title": title, "severity": severity}),
                    reporter,
                ),
            )

        # 重要度がHIGH以上の場合は自動エスカレーション
        if severity in [IncidentSeverity.HIGH.value, IncidentSeverity.CRITICAL.value]:
            await self._auto_escalate(incident_id, severity)

        return {
            "success": True,
            "incident_id": incident_id,
            "message": "Incident created successfully",
            "auto_escalated": severity
            in [IncidentSeverity.HIGH.value, IncidentSeverity.CRITICAL.value],
        }

    async def _update_incident(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ンシデント更新"""
        incident_id = request.get("incident_id")
        updates = request.get("updates", {})
        user_id = request.get("user_id", "system")
        if not incident_id:
            return {"success": False, "error": "Incident ID is required"}

        allowed_fields = [
            "title",
            "description",
            "severity",
            "status",
            "category",
            "affected_systems",
            "impact_description",
            "root_cause",
            "resolution",
            "assignee",
            "tags",
            "metadata",
        ]

        update_fields = []
        params = []
        logs = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 既存データ取得
            cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
            existing_incident = cursor.fetchone()

            if not existing_incident:
                return {"success": False, "error": "Incident not found"}

            # 更新フィールド処理
            for field, value in updates.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")

                    if field in ["affected_systems", "tags", "metadata"] and isinstance(
                        value, (list, dict)
                    ):
                        params.append(json.dumps(value))
                    else:
                        params.append(value)

                    # ログ用の古い値を記録
                    logs.append((field, value))

            if not update_fields:
                return {"success": False, "error": "No valid fields to update"}

            params.append(datetime.now().isoformat())  # updated_at
            params.append(incident_id)

            # インシデント更新
            cursor.execute(
                f"""
                UPDATE incidents
                SET {', '.join(update_fields)}, updated_at = ?
                WHERE id = ?
            """,
                params,
            )

            # ログ記録
            for field, new_value in logs:
                cursor.execute(
                    """
                    INSERT INTO incident_logs (incident_id, action, details, user_id)
                    VALUES (?, ?, ?, ?)
                """,
                    (incident_id, f"updated_{field}", str(new_value), user_id),
                )

        return {
            "success": True,
            "message": "Incident updated successfully",
            "updated_fields": list(updates.keys()),
        }

    async def _get_incident(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ンシデント詳細取得"""
        incident_id = request.get("incident_id")
        if not incident_id:
            return {"success": False, "error": "Incident ID is required"}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # インシデント詳細取得
            cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
            incident_row = cursor.fetchone()

            if not incident_row:
                return {"success": False, "error": "Incident not found"}

            # カラム名取得
            columns = [description[0] for description in cursor.description]
            incident = dict(zip(columns, incident_row))

            # JSONフィールドをパース
            if incident.get("affected_systems"):
                incident["affected_systems"] = json.loads(incident["affected_systems"])
            if incident.get("tags"):
                incident["tags"] = json.loads(incident["tags"])
            if incident.get("metadata"):
                incident["metadata"] = json.loads(incident["metadata"])

            # ログ取得
            cursor.execute(
                """
                SELECT action, details, user_id, created_at
                FROM incident_logs
                WHERE incident_id = ?
                ORDER BY created_at DESC
            """,
                (incident_id,),
            )

            logs = [
                {
                    "action": row[0],
                    "details": row[1],
                    "user_id": row[2],
                    "created_at": row[3],
                }
                for row in cursor.fetchall()
            ]

            # 関連アラート取得
            cursor.execute(
                """
                SELECT id, alert_type, severity, title, triggered_at
                FROM alerts
                WHERE incident_id = ?
                ORDER BY triggered_at DESC
            """,
                (incident_id,),
            )

            alerts = [
                {
                    "id": row[0],
                    "alert_type": row[1],
                    "severity": row[2],
                    "title": row[3],
                    "triggered_at": row[4],
                }
                for row in cursor.fetchall()
            ]

            incident["logs"] = logs
            incident["related_alerts"] = alerts

        return {"success": True, "incident": incident}

    async def _list_incidents(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ンシデント一覧取得"""
        filters = request.get("filters", {})
        sort_by = request.get("sort_by", "created_at")
        sort_order = request.get("sort_order", "DESC")
        limit = request.get("limit", 50)
        offset = request.get("offset", 0)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # WHERE句構築
            where_conditions = []
            params = []

            for field, value in filters.items():
                if field in ["severity", "status", "category", "assignee", "reporter"]:
                    where_conditions.append(f"{field} = ?")
                    params.append(value)
                elif field == "date_range":
                    if "start" in value:
                        where_conditions.append("created_at >= ?")
                        params.append(value["start"])
                    if "end" in value:
                        where_conditions.append("created_at <= ?")
                        params.append(value["end"])

            where_clause = (
                " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            )

            # クエリ実行
            query = f"""
                SELECT * FROM incidents
                {where_clause}
                ORDER BY {sort_by} {sort_order}
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            cursor.execute(query, params)
            incident_rows = cursor.fetchall()

            # カラム名取得
            columns = [description[0] for description in cursor.description]

            incidents = []
            for row in incident_rows:
                incident = dict(zip(columns, row))

                # JSONフィールドをパース
                if incident.get("affected_systems"):
                    incident["affected_systems"] = json.loads(
                        incident["affected_systems"]
                    )
                if incident.get("tags"):
                    incident["tags"] = json.loads(incident["tags"])
                if incident.get("metadata"):
                    incident["metadata"] = json.loads(incident["metadata"])

                incidents.append(incident)

            # 総数取得
            count_query = f"SELECT COUNT(*) FROM incidents{where_clause}"
            cursor.execute(count_query, params[:-2])  # limit, offsetを除く
            total_count = cursor.fetchone()[0]

        return {
            "success": True,
            "incidents": incidents,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }

    async def _resolve_incident(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ンシデント解決"""
        incident_id = request.get("incident_id")
        resolution = request.get("resolution", "")
        root_cause = request.get("root_cause", "")
        user_id = request.get("user_id", "system")
        if not incident_id:
            return {"success": False, "error": "Incident ID is required"}

        resolved_at = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # インシデント存在確認
            cursor.execute(
                "SELECT created_at FROM incidents WHERE id = ?", (incident_id,)
            )
            incident = cursor.fetchone()

            if not incident:
                return {"success": False, "error": "Incident not found"}

            # 解決時間計算
            created_at = datetime.fromisoformat(incident[0].replace("Z", "+00:00"))
            resolution_time = int(
                (datetime.now() - created_at).total_seconds() / 60
            )  # 分単位

            # インシデント解決
            cursor.execute(
                """
                UPDATE incidents
                SET status = 'resolved', resolution = ?, root_cause = ?,
                    resolved_at = ?, actual_resolution_time = ?, updated_at = ?
                WHERE id = ?
            """,
                (
                    resolution,
                    root_cause,
                    resolved_at,
                    resolution_time,
                    resolved_at,
                    incident_id,
                ),
            )

            # ログ記録
            cursor.execute(
                """
                INSERT INTO incident_logs (incident_id, action, details, user_id)
                VALUES (?, 'resolved', ?, ?)
            """,
                (
                    incident_id,
                    json.dumps(
                        {
                            "resolution": resolution,
                            "root_cause": root_cause,
                            "resolution_time_minutes": resolution_time,
                        }
                    ),
                    user_id,
                ),
            )

            # 関連アラートも解決
            cursor.execute(
                """
                UPDATE alerts
                SET resolved_at = ?, resolved_by = ?
                WHERE incident_id = ? AND resolved_at IS NULL
            """,
                (resolved_at, user_id, incident_id),
            )

        return {
            "success": True,
            "message": "Incident resolved successfully",
            "resolution_time_minutes": resolution_time,
        }

    async def _create_alert(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ラート作成"""
        alert_type = request.get("alert_type", "")
        severity = request.get("severity", IncidentSeverity.MEDIUM.value)
        title = request.get("title", "")
        message = request.get("message", "")
        source_system = request.get("source_system", "unknown")
        metadata = request.get("metadata", {})
        if not alert_type or not title:
            return {"success": False, "error": "Alert type and title are required"}

        alert_id = str(uuid.uuid4())

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO alerts
                (id, alert_type, severity, title, message, source_system, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    alert_id,
                    alert_type,
                    severity,
                    title,
                    message,
                    source_system,
                    json.dumps(metadata),
                ),
            )

        # 重要度がHIGH以上の場合は自動でインシデント作成
        auto_incident_created = False
        incident_id = None

        if severity in [IncidentSeverity.HIGH.value, IncidentSeverity.CRITICAL.value]:
            incident_result = await self._create_incident(
                {
                    "title": f"Auto-created from alert: {title}",
                    "description": f"Alert: {message}",
                    "severity": severity,
                    "category": "software",
                    "reporter": "system",
                    "tags": ["auto-created", "alert-generated"],
                }
            )

            if incident_result.get("success"):
                incident_id = incident_result["incident_id"]
                auto_incident_created = True

                # アラートとインシデントを関連付け
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE alerts SET incident_id = ? WHERE id = ?",
                        (incident_id, alert_id),
                    )

        return {
            "success": True,
            "alert_id": alert_id,
            "message": "Alert created successfully",
            "auto_incident_created": auto_incident_created,
            "incident_id": incident_id,
        }

    async def _acknowledge_alert(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ラート確認"""
        alert_id = request.get("alert_id")
        user_id = request.get("user_id", "system")
        if not alert_id:
            return {"success": False, "error": "Alert ID is required"}

        acknowledged_at = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE alerts
                SET acknowledged_at = ?, acknowledged_by = ?
                WHERE id = ? AND acknowledged_at IS NULL
            """,
                (acknowledged_at, user_id, alert_id),
            )

            if cursor.rowcount == 0:
                return {
                    "success": False,
                    "error": "Alert not found or already acknowledged",
                }

        return {"success": True, "message": "Alert acknowledged successfully"}

    async def _record_metric(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ステムメトリクス記録"""
        metric_name = request.get("metric_name", "")
        metric_value = request.get("metric_value")
        unit = request.get("unit", "")
        source_system = request.get("source_system", "unknown")
        tags = request.get("tags", [])
        if not metric_name or metric_value is None:
            return {"success": False, "error": "Metric name and value are required"}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO system_metrics
                (metric_name, metric_value, unit, source_system, tags)
                VALUES (?, ?, ?, ?, ?)
            """,
                (metric_name, metric_value, unit, source_system, json.dumps(tags)),
            )

        # アラートルールチェック
        alert_triggered = await self._check_alert_rules(
            metric_name, metric_value, source_system
        )

        return {
            "success": True,
            "message": "Metric recorded successfully",
            "alert_triggered": alert_triggered is not None,
            "alert_id": alert_triggered,
        }

    async def _check_alert_rules(
        self, metric_name: str, metric_value: float, source_system: str
    ) -> Optional[str]:
        """アラートルールチェック"""
        alert_id = None

        # CPU使用率チェック
        if (
            metric_name == "cpu_usage"
            and metric_value > self.alert_rules["cpu_usage_threshold"]
        ):
            alert_result = await self._create_alert(
                {
                    "alert_type": "performance",
                    "severity": (
                        IncidentSeverity.HIGH.value
                        if metric_value > 95
                        else IncidentSeverity.MEDIUM.value
                    ),
                    "title": f"High CPU Usage on {source_system}",
                    "message": f"CPU usage is {metric_value}%, exceeding threshold of {self.alert_rules['cpu_usage_threshold']}%",
                    "source_system": source_system,
                    "metadata": {
                        "metric_value": metric_value,
                        "threshold": self.alert_rules["cpu_usage_threshold"],
                    },
                }
            )
            alert_id = alert_result.get("alert_id")

        # メモリ使用率チェック
        elif (
            metric_name == "memory_usage"
            and metric_value > self.alert_rules["memory_usage_threshold"]
        ):
            alert_result = await self._create_alert(
                {
                    "alert_type": "performance",
                    "severity": (
                        IncidentSeverity.HIGH.value
                        if metric_value > 95
                        else IncidentSeverity.MEDIUM.value
                    ),
                    "title": f"High Memory Usage on {source_system}",
                    "message": f"Memory usage is {metric_value}%, exceeding threshold of {self.alert_rules['memory_usage_threshold']}%",
                    "source_system": source_system,
                    "metadata": {
                        "metric_value": metric_value,
                        "threshold": self.alert_rules["memory_usage_threshold"],
                    },
                }
            )
            alert_id = alert_result.get("alert_id")

        # ディスク使用率チェック
        elif (
            metric_name == "disk_usage"
            and metric_value > self.alert_rules["disk_usage_threshold"]
        ):
            alert_result = await self._create_alert(
                {
                    "alert_type": "availability",
                    "severity": (
                        IncidentSeverity.CRITICAL.value
                        if metric_value > 98
                        else IncidentSeverity.HIGH.value
                    ),
                    "title": f"High Disk Usage on {source_system}",
                    "message": f"Disk usage is {metric_value}%, exceeding threshold of {self.alert_rules['disk_usage_threshold']}%",
                    "source_system": source_system,
                    "metadata": {
                        "metric_value": metric_value,
                        "threshold": self.alert_rules["disk_usage_threshold"],
                    },
                }
            )
            alert_id = alert_result.get("alert_id")

        return alert_id

    async def _analyze_metrics(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """トリクス分析"""
        metric_name = request.get("metric_name")
        period_hours = request.get("period_hours", 24)
        source_system = request.get("source_system")

        start_time = (datetime.now() - timedelta(hours=period_hours)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            where_conditions = ["collected_at >= ?"]
            params = [start_time]

            if metric_name:
                where_conditions.append("metric_name = ?")
                params.append(metric_name)

            if source_system:
                where_conditions.append("source_system = ?")
                params.append(source_system)

            where_clause = " AND ".join(where_conditions)

            # 統計情報取得
            cursor.execute(
                f"""
                SELECT
                    COUNT(*) as count,
                    AVG(metric_value) as avg_value,
                    MIN(metric_value) as min_value,
                    MAX(metric_value) as max_value
                FROM system_metrics
                WHERE {where_clause}
            """,
                params,
            )

            stats = cursor.fetchone()

            # 時系列データ取得
            cursor.execute(
                f"""
                SELECT
                    strftime('%Y-%m-%d %H:00:00', collected_at) as hour,
                    AVG(metric_value) as avg_value
                FROM system_metrics
                WHERE {where_clause}
                GROUP BY strftime('%Y-%m-%d %H:00:00', collected_at)
                ORDER BY hour
            """,
                params,
            )

            timeseries = [
                {"timestamp": row[0], "value": round(row[1], 2)}
                for row in cursor.fetchall()
            ]

        analysis = {
            "period_hours": period_hours,
            "metric_name": metric_name,
            "source_system": source_system,
            "statistics": {
                "count": stats[0] or 0,
                "average": round(stats[1] or 0, 2),
                "minimum": round(stats[2] or 0, 2),
                "maximum": round(stats[3] or 0, 2),
            },
            "timeseries": timeseries,
        }

        return {"success": True, "analysis": analysis}

    async def _security_scan(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """キュリティスキャン"""
        scan_type = request.get("scan_type", "basic")
        target = request.get("target", "system")

        # 簡易セキュリティスキャンのシミュレーション
        findings = []

        # ログファイルチェック（シミュレーション）
        if scan_type in ["basic", "full"]:
            # セキュリティパターンマッチング
            for pattern in self.security_patterns[:3]:  # 簡易チェック
                finding = {
                    "type": "log_analysis",
                    "severity": "medium",
                    "description": f"Potential {pattern} detected in system logs",
                    "recommendation": f"Review and investigate {pattern} incidents",
                }
                findings.append(finding)

        # ネットワークチェック（シミュレーション）
        if scan_type == "full":
            findings.append(
                {
                    "type": "network_security",
                    "severity": "low",
                    "description": "Open ports detected",
                    "recommendation": "Review and close unnecessary ports",
                }
            )

        # セキュリティイベント記録
        event_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO security_events
                (id, event_type, severity, event_details, metadata)
                VALUES (?, 'security_scan', 'low', ?, ?)
            """,
                (
                    event_id,
                    f"Security scan completed for {target}",
                    json.dumps(
                        {"scan_type": scan_type, "findings_count": len(findings)}
                    ),
                ),
            )

        return {
            "success": True,
            "scan_id": event_id,
            "scan_type": scan_type,
            "target": target,
            "findings_count": len(findings),
            "findings": findings,
        }

    async def _get_dashboard(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ッシュボードデータ取得"""
        period_hours = request.get("period_hours", 24)

        start_time = (datetime.now() - timedelta(hours=period_hours)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # インシデント統計
            cursor.execute(
                """
                SELECT
                    status,
                    severity,
                    COUNT(*) as count
                FROM incidents
                WHERE created_at >= ?
                GROUP BY status, severity
            """,
                (start_time,),
            )

            incident_stats = {}
            for status, severity, count in cursor.fetchall():
                if status not in incident_stats:
                    incident_stats[status] = {}
                incident_stats[status][severity] = count

            # アラート統計
            cursor.execute(
                """
                SELECT
                    alert_type,
                    severity,
                    COUNT(*) as count
                FROM alerts
                WHERE triggered_at >= ?
                GROUP BY alert_type, severity
            """,
                (start_time,),
            )

            alert_stats = {}
            for alert_type, severity, count in cursor.fetchall():
                if alert_type not in alert_stats:
                    alert_stats[alert_type] = {}
                alert_stats[alert_type][severity] = count

            # 平均解決時間
            cursor.execute(
                """
                SELECT AVG(actual_resolution_time) as avg_resolution
                FROM incidents
                WHERE resolved_at >= ? AND actual_resolution_time IS NOT NULL
            """,
                (start_time,),
            )

            avg_resolution = cursor.fetchone()[0] or 0

            # アクティブアラート数
            cursor.execute(
                """
                SELECT COUNT(*) FROM alerts
                WHERE resolved_at IS NULL
            """
            )

            active_alerts = cursor.fetchone()[0]

        dashboard = {
            "period_hours": period_hours,
            "incident_statistics": incident_stats,
            "alert_statistics": alert_stats,
            "average_resolution_time_minutes": round(avg_resolution, 2),
            "active_alerts_count": active_alerts,
            "health_status": (
                "healthy"
                if active_alerts < 5
                else "degraded" if active_alerts < 20 else "critical"
            ),
        }

        return {"success": True, "dashboard": dashboard}

    async def _escalate_incident(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ンシデントエスカレーション"""
        incident_id = request.get("incident_id")
        escalation_reason = request.get("reason", "manual_escalation")
        user_id = request.get("user_id", "system")
        if not incident_id:
            return {"success": False, "error": "Incident ID is required"}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 現在の重要度取得
            cursor.execute(
                "SELECT severity FROM incidents WHERE id = ?", (incident_id,)
            )
            current_severity = cursor.fetchone()

            if not current_severity:
                return {"success": False, "error": "Incident not found"}

            # 重要度をエスカレーション
            severity_escalation = {
                IncidentSeverity.LOW.value: IncidentSeverity.MEDIUM.value,
                IncidentSeverity.MEDIUM.value: IncidentSeverity.HIGH.value,
                IncidentSeverity.HIGH.value: IncidentSeverity.CRITICAL.value,
                IncidentSeverity.CRITICAL.value: IncidentSeverity.CRITICAL.value,  # 既に最高レベル
            }

            new_severity = severity_escalation.get(
                current_severity[0], IncidentSeverity.CRITICAL.value
            )

            # インシデント更新
            cursor.execute(
                """
                UPDATE incidents
                SET severity = ?, updated_at = ?
                WHERE id = ?
            """,
                (new_severity, datetime.now().isoformat(), incident_id),
            )

            # エスカレーションログ記録
            cursor.execute(
                """
                INSERT INTO incident_logs (incident_id, action, details, user_id)
                VALUES (?, 'escalated', ?, ?)
            """,
                (
                    incident_id,
                    json.dumps(
                        {
                            "old_severity": current_severity[0],
                            "new_severity": new_severity,
                            "reason": escalation_reason,
                        }
                    ),
                    user_id,
                ),
            )

        return {
            "success": True,
            "message": "Incident escalated successfully",
            "old_severity": current_severity[0],
            "new_severity": new_severity,
        }

    async def _auto_escalate(self, incident_id: str, severity: str):
        """自動エスカレーション"""
        # CRITICAL インシデントの場合は即座に通知
        if severity == IncidentSeverity.CRITICAL.value:
            self.logger.critical(f"CRITICAL incident created: {incident_id}")
            # ここで実際の通知システムと連携（Slack、メール等）

        # HIGH インシデントの場合は担当者にアサイン
        elif severity == IncidentSeverity.HIGH.value:
            self.logger.warning(f"HIGH severity incident created: {incident_id}")
            # ここで担当者自動アサインロジックを実装

    def get_capabilities(self) -> List[str]:
        """インシデント賢者の能力一覧"""
        return [
            "create_incident",
            "update_incident",
            "get_incident",
            "list_incidents",
            "resolve_incident",
            "create_alert",
            "acknowledge_alert",
            "record_metric",
            "analyze_metrics",
            "security_scan",
            "get_dashboard",
            "escalate_incident",
            "incident_management",
            "alert_monitoring",
            "security_management",
            "system_monitoring",
        ]
