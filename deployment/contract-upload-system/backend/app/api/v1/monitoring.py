"""
監視・ヘルスチェックエンドポイント - Elder Flow準拠
"""

import os
import time
import psutil
import platform
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import logging
import sqlite3
from sqlalchemy import create_engine, text
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

class HealthStatus(BaseModel):
    """ヘルス状態"""
    status: str
    timestamp: str
    version: str
    uptime: float

class SystemMetrics(BaseModel):
    """システムメトリクス"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_connections: int

class DatabaseHealth(BaseModel):
    """データベースヘルス"""
    status: str
    connection_time: float
    tables_count: int

class ServiceHealth(BaseModel):
    """サービスヘルス総合"""
    overall_status: str
    components: Dict[str, Any]
    metrics: SystemMetrics
    timestamp: str

# アプリケーション開始時刻
app_start_time = time.time()

@router.get("/health", response_model=HealthStatus)
async def health_check():
    """基本ヘルスチェック"""
    try:
        return HealthStatus(
            status="healthy",
            timestamp=datetime.utcnow().isoformat(),
            version=os.getenv("APP_VERSION", "1.0.0"),
            uptime=time.time() - app_start_time
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@router.get("/readiness")
async def readiness_check():
    """本番準備状況チェック"""
    checks = {}
    ready = True

    # 環境変数チェック
    required_env_vars = [
        'DATABASE_URL', 'SECRET_KEY', 'JWT_SECRET_KEY',
        'FRONTEND_URL', 'ALLOWED_ORIGINS'
    ]

    env_check = {
        "status": "pass",
        "missing_vars": []
    }

    for var in required_env_vars:
        if not os.getenv(var):
            env_check["missing_vars"].append(var)
            env_check["status"] = "fail"
            ready = False

    checks["environment"] = env_check

    # データベース接続チェック
    db_check = await _check_database_connection()
    checks["database"] = db_check
    if db_check["status"] != "pass":
        ready = False

    # ファイルアップロード設定チェック
    upload_check = _check_upload_configuration()
    checks["file_upload"] = upload_check
    if upload_check["status"] != "pass":
        ready = False

    # セキュリティ設定チェック
    security_check = _check_security_configuration()
    checks["security"] = security_check
    if security_check["status"] != "pass":
        ready = False

    status_code = 200 if ready else 503

    return {
        "status": "ready" if ready else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }

@router.get("/liveness")
async def liveness_check():
    """生存確認"""
    try:
        # 基本的な機能が動作しているかチェック
        current_time = datetime.utcnow()

        # メモリ使用量チェック (90%以上で異常とみなす)
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > 90:
            raise HTTPException(status_code=503, detail="High memory usage")

        # CPU使用率チェック (95%以上で異常とみなす)
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 95:
            raise HTTPException(status_code=503, detail="High CPU usage")

        return {
            "status": "alive",
            "timestamp": current_time.isoformat(),
            "memory_usage": memory_percent,
            "cpu_usage": cpu_percent
        }

    except Exception as e:
        logger.error(f"Liveness check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service not responsive")

@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics():
    """システムメトリクス取得"""
    try:
        # システムメトリクス収集
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # ネットワーク接続数
        connections = len(psutil.net_connections())

        # プロセス情報
        process = psutil.Process()
        process_info = {
            "pid": process.pid,
            "memory_info": process.memory_info()._asdict(),
            "cpu_percent": process.cpu_percent(),
            "create_time": process.create_time(),
            "num_threads": process.num_threads()
        }

        # アプリケーション固有メトリクス
        app_metrics = {
            "uptime": time.time() - app_start_time,
            "python_version": platform.python_version(),
            "platform": platform.platform()
        }

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_usage_percent": cpu_usage,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "network_connections": connections
            },
            "process": process_info,
            "application": app_metrics
        }

    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to collect metrics")

@router.get("/status", response_model=ServiceHealth)
async def get_service_status():
    """サービス状態総合取得"""
    try:
        components = {}
        overall_healthy = True

        # データベース状態
        db_health = await _check_database_connection()
        components["database"] = db_health
        if db_health["status"] != "pass":
            overall_healthy = False

        # ファイルアップロード状態
        upload_health = _check_upload_configuration()
        components["file_upload"] = upload_health
        if upload_health["status"] != "pass":
            overall_healthy = False

        # セキュリティ設定状態
        security_health = _check_security_configuration()
        components["security"] = security_health
        if security_health["status"] != "pass":
            overall_healthy = False

        # システムメトリクス
        cpu_usage = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        connections = len(psutil.net_connections())

        metrics = SystemMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            disk_usage=(disk.used / disk.total) * 100,
            active_connections=connections
        )

        return ServiceHealth(
            overall_status="healthy" if overall_healthy else "degraded",
            components=components,
            metrics=metrics,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Service status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get service status")

async def _check_database_connection() -> Dict[str, Any]:
    """データベース接続チェック"""
    try:
        start_time = time.time()
        database_url = os.getenv('DATABASE_URL', 'sqlite:///./contracts.db')

        engine = create_engine(database_url)

        with engine.connect() as connection:
            # 簡単なクエリでテスト
            result = connection.execute(text("SELECT 1"))
            result.fetchone()

            # テーブル数取得
            if 'sqlite' in database_url:
                tables_result = connection.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'"))
            else:
                tables_result = connection.execute(text("SELECT COUNT(*) FROM information_schema.tables"))

            tables_count = tables_result.fetchone()[0]

        connection_time = time.time() - start_time

        return {
            "status": "pass",
            "connection_time": connection_time,
            "tables_count": tables_count,
            "database_type": "sqlite" if 'sqlite' in database_url else "postgresql"
        }

    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return {
            "status": "fail",
            "error": str(e),
            "connection_time": None,
            "tables_count": 0
        }

def _check_upload_configuration() -> Dict[str, Any]:
    """ファイルアップロード設定チェック"""
    try:
        max_size = os.getenv('MAX_FILE_SIZE', '31457280')
        allowed_types = os.getenv('ALLOWED_FILE_TYPES', 'pdf,doc,docx,txt')

        # Google Drive設定チェック
        credentials_path = os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH')
        credentials_exist = credentials_path and os.path.exists(credentials_path)

        issues = []
        if not credentials_exist:
            issues.append("Google Drive credentials not found")

        try:
            max_size_int = int(max_size)
            if max_size_int <= 0:
                issues.append("Invalid max file size")
        except ValueError:
            issues.append("Max file size not numeric")

        if not allowed_types:
            issues.append("No allowed file types configured")

        return {
            "status": "pass" if not issues else "warn",
            "max_file_size": max_size,
            "allowed_types": allowed_types.split(','),
            "google_drive_configured": credentials_exist,
            "issues": issues
        }

    except Exception as e:
        return {
            "status": "fail",
            "error": str(e)
        }

def _check_security_configuration() -> Dict[str, Any]:
    """セキュリティ設定チェック"""
    try:
        issues = []

        # 必須セキュリティ設定チェック
        if not os.getenv('SECRET_KEY') or os.getenv('SECRET_KEY') == 'development-secret-key':
            issues.append("Production secret key not configured")

        if not os.getenv('JWT_SECRET_KEY'):
            issues.append("JWT secret key not configured")

        # HTTPS設定チェック (本番環境)
        if os.getenv('ENVIRONMENT') == 'production':
            frontend_url = os.getenv('FRONTEND_URL', '')
            if not frontend_url.startswith('https://'):
                issues.append("HTTPS not configured for production")

        # CORS設定チェック
        allowed_origins = os.getenv('ALLOWED_ORIGINS', '')
        if not allowed_origins:
            issues.append("CORS origins not configured")

        # セキュリティヘッダー設定チェック
        security_headers_enabled = os.getenv('ENABLE_SECURITY_HEADERS', 'true').lower() == 'true'
        if not security_headers_enabled:
            issues.append("Security headers disabled")

        return {
            "status": "pass" if not issues else "warn",
            "security_headers_enabled": security_headers_enabled,
            "cors_configured": bool(allowed_origins),
            "https_enabled": os.getenv('FRONTEND_URL', '').startswith('https://'),
            "issues": issues
        }

    except Exception as e:
        return {
            "status": "fail",
            "error": str(e)
        }
