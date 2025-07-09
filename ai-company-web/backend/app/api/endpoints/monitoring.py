import time
import psutil
import asyncio
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db, check_database_health, check_redis_health
from ...core.security import get_current_user, require_elder
from ...models.auth import User
from ...core.logging import log_analyzer, performance_logger
from ...services.migration_service import migration_service

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "ai-company-web",
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check(
    current_user: User = Depends(get_current_user)
):
    """Detailed health check with component status"""
    
    # Check database
    db_health = await check_database_health()
    
    # Check Redis
    redis_health = await check_redis_health()
    
    # Check system resources
    system_health = await _check_system_health()
    
    # Overall status
    overall_status = "healthy"
    if (db_health["status"] != "healthy" or 
        redis_health["status"] != "healthy" or 
        system_health["status"] != "healthy"):
        overall_status = "degraded"
    
    return {
        "status": overall_status,
        "timestamp": time.time(),
        "components": {
            "database": db_health,
            "redis": redis_health,
            "system": system_health
        }
    }

@router.get("/metrics")
async def get_metrics(
    current_user: User = Depends(require_elder)
):
    """Get system metrics - Elder access required"""
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Network metrics (if available)
    try:
        network = psutil.net_io_counters()
        network_metrics = {
            "bytes_sent": network.bytes_sent,
            "bytes_received": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_received": network.packets_recv
        }
    except:
        network_metrics = {}
    
    # Migration metrics
    migration_status = await migration_service.get_migration_status()
    
    return {
        "timestamp": time.time(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_percent": round((disk.used / disk.total) * 100, 2)
            },
            "network": network_metrics
        },
        "application": {
            "migration_status": migration_status
        }
    }

@router.get("/logs/analysis")
async def analyze_logs(
    current_user: User = Depends(require_elder)
):
    """Analyze recent logs for patterns - Elder access required"""
    
    # This would typically read from a log aggregation system
    # For demo purposes, we'll return simulated analysis
    
    sample_logs = [
        {
            "timestamp": time.time() - 30,
            "level": "info",
            "event_type": "api_performance",
            "response_time": 0.5
        },
        {
            "timestamp": time.time() - 20,
            "level": "error",
            "event_type": "security_violation",
            "details": "Rate limit exceeded"
        }
    ]
    
    error_analysis = await log_analyzer.analyze_error_rate(sample_logs)
    performance_analysis = await log_analyzer.analyze_response_times(sample_logs)
    
    return {
        "timestamp": time.time(),
        "analysis": {
            "error_rate": error_analysis,
            "performance": performance_analysis
        },
        "recommendations": _get_recommendations(error_analysis, performance_analysis)
    }

@router.get("/performance/stats")
async def get_performance_stats(
    hours: int = 24,
    current_user: User = Depends(require_elder)
):
    """Get performance statistics - Elder access required"""
    
    # This would typically aggregate data from monitoring systems
    # For demo purposes, we'll return simulated data
    
    return {
        "timestamp": time.time(),
        "period_hours": hours,
        "stats": {
            "api_requests": {
                "total": 15420,
                "successful": 15180,
                "failed": 240,
                "success_rate": 98.4
            },
            "response_times": {
                "average_ms": 245,
                "p50_ms": 180,
                "p95_ms": 650,
                "p99_ms": 1200
            },
            "error_breakdown": {
                "4xx_errors": 180,
                "5xx_errors": 60,
                "timeout_errors": 15,
                "connection_errors": 8
            },
            "endpoints": [
                {
                    "path": "/api/v1/sages/status",
                    "requests": 3240,
                    "avg_response_time": 156,
                    "error_rate": 0.8
                },
                {
                    "path": "/api/v1/auth/login",
                    "requests": 1820,
                    "avg_response_time": 320,
                    "error_rate": 2.1
                }
            ]
        }
    }

@router.get("/alerts")
async def get_active_alerts(
    current_user: User = Depends(require_elder)
):
    """Get active system alerts - Elder access required"""
    
    # This would typically query an alerting system
    # For demo purposes, we'll return simulated alerts
    
    alerts = []
    
    # Check current system state and generate alerts
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    if cpu_percent > 80:
        alerts.append({
            "id": "cpu_high",
            "severity": "warning",
            "title": "High CPU Usage",
            "description": f"CPU usage is {cpu_percent}%",
            "timestamp": time.time(),
            "resolved": False
        })
    
    if memory.percent > 85:
        alerts.append({
            "id": "memory_high",
            "severity": "critical",
            "title": "High Memory Usage",
            "description": f"Memory usage is {memory.percent}%",
            "timestamp": time.time(),
            "resolved": False
        })
    
    return {
        "timestamp": time.time(),
        "alerts": alerts,
        "total_active": len(alerts)
    }

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(require_elder)
):
    """Resolve an alert - Elder access required"""
    
    # This would typically update an alerting system
    # For demo purposes, we'll just return success
    
    return {
        "alert_id": alert_id,
        "resolved": True,
        "resolved_by": current_user.id,
        "resolved_at": time.time()
    }

@router.get("/sage-monitoring")
async def get_sage_monitoring(
    current_user: User = Depends(get_current_user)
):
    """Get Sage system monitoring data"""
    
    # This would typically query sage system metrics
    # For demo purposes, we'll return simulated data
    
    sage_stats = {
        "incident": {
            "status": "active",
            "last_activity": time.time() - 120,
            "incidents_processed": 45,
            "response_time_avg": 0.8,
            "coverage": 67.2
        },
        "knowledge": {
            "status": "active",
            "last_activity": time.time() - 45,
            "queries_processed": 156,
            "response_time_avg": 0.3,
            "coverage": 71.8
        },
        "search": {
            "status": "active",
            "last_activity": time.time() - 30,
            "searches_processed": 89,
            "response_time_avg": 0.5,
            "coverage": 69.4
        },
        "task": {
            "status": "active",
            "last_activity": time.time() - 180,
            "tasks_processed": 34,
            "response_time_avg": 1.2,
            "coverage": 62.1
        }
    }
    
    overall_coverage = sum(sage["coverage"] for sage in sage_stats.values()) / len(sage_stats)
    
    return {
        "timestamp": time.time(),
        "overall_coverage": round(overall_coverage, 1),
        "target_coverage": 66.7,
        "coverage_achieved": overall_coverage >= 66.7,
        "sages": sage_stats
    }

@router.get("/elder-council-monitoring")
async def get_elder_council_monitoring(
    current_user: User = Depends(require_elder)
):
    """Get Elder Council monitoring data - Elder access required"""
    
    return {
        "timestamp": time.time(),
        "council_status": "active",
        "active_members": 4,
        "last_session": time.time() - 3600,
        "decisions_made": 12,
        "consensus_rate": 87.5,
        "current_initiatives": [
            {
                "name": "66.7% Coverage Achievement",
                "status": "in_progress",
                "completion": 89.2
            },
            {
                "name": "Security Enhancement Phase 4",
                "status": "completed",
                "completion": 100.0
            }
        ]
    }

async def _check_system_health() -> Dict[str, Any]:
    """Check system health metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Determine health status
        status = "healthy"
        issues = []
        
        if cpu_percent > 90:
            status = "unhealthy"
            issues.append(f"High CPU usage: {cpu_percent}%")
        elif cpu_percent > 80:
            status = "degraded"
            issues.append(f"Elevated CPU usage: {cpu_percent}%")
        
        if memory.percent > 95:
            status = "unhealthy"
            issues.append(f"Critical memory usage: {memory.percent}%")
        elif memory.percent > 85:
            status = "degraded"
            issues.append(f"High memory usage: {memory.percent}%")
        
        disk_percent = (disk.used / disk.total) * 100
        if disk_percent > 95:
            status = "unhealthy"
            issues.append(f"Critical disk usage: {disk_percent:.1f}%")
        elif disk_percent > 85:
            if status == "healthy":
                status = "degraded"
            issues.append(f"High disk usage: {disk_percent:.1f}%")
        
        return {
            "status": status,
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": round(disk_percent, 2),
            "issues": issues,
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "status": "unknown",
            "error": str(e),
            "timestamp": time.time()
        }

def _get_recommendations(error_analysis: Dict, performance_analysis: Dict) -> List[str]:
    """Generate recommendations based on analysis"""
    recommendations = []
    
    if error_analysis.get("error_rate", 0) > 5:
        recommendations.append("High error rate detected. Consider reviewing recent deployments and error logs.")
    
    if performance_analysis.get("average_response_time", 0) > 2.0:
        recommendations.append("High response times detected. Consider optimizing database queries and caching.")
    
    if performance_analysis.get("slow_requests", 0) > 10:
        recommendations.append("Multiple slow requests detected. Consider implementing response time monitoring alerts.")
    
    if not recommendations:
        recommendations.append("System is performing within normal parameters.")
    
    return recommendations