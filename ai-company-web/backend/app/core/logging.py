import os
import sys
import json
import time
import logging
import structlog
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .config import settings

class AICompanyLogger:
    """Advanced logging system for AI Company Web"""
    
    def __init__(self):
        self.setup_logging()
        self.setup_sentry()
        self.setup_structured_logging()
    
    def setup_logging(self):
        """Setup basic Python logging"""
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure logging level
        log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        
        # Basic logging configuration
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_dir / 'app.log'),
                logging.FileHandler(log_dir / 'error.log', level=logging.ERROR)
            ]
        )
        
        # Configure specific loggers
        logging.getLogger("uvicorn").setLevel(log_level)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("redis").setLevel(logging.WARNING)
    
    def setup_sentry(self):
        """Setup Sentry for error tracking"""
        if settings.SENTRY_DSN and settings.is_production:
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.ENVIRONMENT,
                release=f"ai-company-web@{settings.VERSION}",
                integrations=[
                    FastApiIntegration(auto_enabling_integrations=False),
                    SqlalchemyIntegration(),
                    RedisIntegration(),
                ],
                traces_sample_rate=0.1,
                send_default_pii=False,
                attach_stacktrace=True,
                max_breadcrumbs=50,
            )
            print("✅ Sentry monitoring initialized")
    
    def setup_structured_logging(self):
        """Setup structured logging with structlog"""
        def add_timestamp(_, __, event_dict):
            event_dict["timestamp"] = datetime.utcnow().isoformat()
            return event_dict
        
        def add_level(_, method_name, event_dict):
            event_dict["level"] = method_name
            return event_dict
        
        def add_service_info(_, __, event_dict):
            event_dict["service"] = "ai-company-web"
            event_dict["version"] = settings.VERSION
            event_dict["environment"] = settings.ENVIRONMENT
            return event_dict
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                add_timestamp,
                add_level,
                add_service_info,
                structlog.dev.ConsoleRenderer() if not settings.is_production else structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

# Initialize logger
logger_manager = AICompanyLogger()

# Get structured logger
logger = structlog.get_logger()

class RequestLogger:
    """Request logging middleware"""
    
    def __init__(self):
        self.logger = structlog.get_logger("requests")
    
    async def log_request(self, request, response, process_time: float):
        """Log HTTP request"""
        self.logger.info(
            "HTTP request processed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
            user_agent=request.headers.get("user-agent", ""),
            client_ip=request.client.host,
            content_length=response.headers.get("content-length", 0)
        )
    
    async def log_error(self, request, error: Exception):
        """Log HTTP error"""
        self.logger.error(
            "HTTP request error",
            method=request.method,
            url=str(request.url),
            error=str(error),
            error_type=type(error).__name__,
            user_agent=request.headers.get("user-agent", ""),
            client_ip=request.client.host
        )

class SecurityLogger:
    """Security event logging"""
    
    def __init__(self):
        self.logger = structlog.get_logger("security")
    
    async def log_authentication_attempt(self, username: str, success: bool, ip: str):
        """Log authentication attempt"""
        self.logger.info(
            "Authentication attempt",
            username=username,
            success=success,
            client_ip=ip,
            event_type="auth_attempt"
        )
    
    async def log_authorization_failure(self, user_id: int, endpoint: str, required_role: str):
        """Log authorization failure"""
        self.logger.warning(
            "Authorization failure",
            user_id=user_id,
            endpoint=endpoint,
            required_role=required_role,
            event_type="auth_failure"
        )
    
    async def log_security_violation(self, violation_type: str, details: dict, ip: str):
        """Log security violation"""
        self.logger.error(
            "Security violation detected",
            violation_type=violation_type,
            details=details,
            client_ip=ip,
            event_type="security_violation"
        )
    
    async def log_rate_limit_exceeded(self, ip: str, endpoint: str, limit: int):
        """Log rate limit exceeded"""
        self.logger.warning(
            "Rate limit exceeded",
            client_ip=ip,
            endpoint=endpoint,
            limit=limit,
            event_type="rate_limit"
        )

class SageLogger:
    """Sage system logging"""
    
    def __init__(self):
        self.logger = structlog.get_logger("sages")
    
    async def log_sage_activity(self, sage_type: str, action: str, details: dict):
        """Log sage activity"""
        self.logger.info(
            "Sage activity",
            sage_type=sage_type,
            action=action,
            details=details,
            event_type="sage_activity"
        )
    
    async def log_sage_error(self, sage_type: str, error: str, context: dict):
        """Log sage error"""
        self.logger.error(
            "Sage error",
            sage_type=sage_type,
            error=error,
            context=context,
            event_type="sage_error"
        )
    
    async def log_coverage_update(self, current_coverage: float, target: float):
        """Log coverage update"""
        self.logger.info(
            "Coverage update",
            current_coverage=current_coverage,
            target_coverage=target,
            coverage_achieved=current_coverage >= target,
            event_type="coverage_update"
        )

class ElderCouncilLogger:
    """Elder Council logging"""
    
    def __init__(self):
        self.logger = structlog.get_logger("elder_council")
    
    async def log_council_session(self, session_type: str, participants: list, duration: float):
        """Log Elder Council session"""
        self.logger.info(
            "Elder Council session",
            session_type=session_type,
            participants=participants,
            duration=duration,
            event_type="council_session"
        )
    
    async def log_council_decision(self, decision: str, voting_results: dict):
        """Log Elder Council decision"""
        self.logger.info(
            "Elder Council decision",
            decision=decision,
            voting_results=voting_results,
            event_type="council_decision"
        )

class PerformanceLogger:
    """Performance monitoring logger"""
    
    def __init__(self):
        self.logger = structlog.get_logger("performance")
    
    async def log_slow_query(self, query: str, duration: float, params: dict = None):
        """Log slow database query"""
        self.logger.warning(
            "Slow query detected",
            query=query[:200],  # Truncate long queries
            duration=duration,
            params=params,
            event_type="slow_query"
        )
    
    async def log_high_memory_usage(self, usage_mb: float, threshold: float):
        """Log high memory usage"""
        self.logger.warning(
            "High memory usage",
            usage_mb=usage_mb,
            threshold_mb=threshold,
            event_type="high_memory"
        )
    
    async def log_api_performance(self, endpoint: str, response_time: float, status_code: int):
        """Log API performance metrics"""
        self.logger.info(
            "API performance",
            endpoint=endpoint,
            response_time=response_time,
            status_code=status_code,
            event_type="api_performance"
        )

class BusinessLogger:
    """Business logic logging"""
    
    def __init__(self):
        self.logger = structlog.get_logger("business")
    
    async def log_user_registration(self, user_id: int, role: str):
        """Log user registration"""
        self.logger.info(
            "User registered",
            user_id=user_id,
            role=role,
            event_type="user_registration"
        )
    
    async def log_feature_usage(self, feature: str, user_id: int, details: dict):
        """Log feature usage"""
        self.logger.info(
            "Feature used",
            feature=feature,
            user_id=user_id,
            details=details,
            event_type="feature_usage"
        )
    
    async def log_migration_event(self, event_type: str, endpoint: str, details: dict):
        """Log migration events"""
        self.logger.info(
            "Migration event",
            event_type=event_type,
            endpoint=endpoint,
            details=details,
            event_type="migration"
        )

# Global logger instances
request_logger = RequestLogger()
security_logger = SecurityLogger()
sage_logger = SageLogger()
elder_council_logger = ElderCouncilLogger()
performance_logger = PerformanceLogger()
business_logger = BusinessLogger()

class LogAnalyzer:
    """Log analysis and alerting"""
    
    def __init__(self):
        self.logger = structlog.get_logger("analyzer")
        self.error_threshold = 10  # errors per minute
        self.response_time_threshold = 2.0  # seconds
    
    async def analyze_error_rate(self, logs: list) -> dict:
        """Analyze error rate from logs"""
        recent_logs = [log for log in logs if self._is_recent(log, 60)]  # Last minute
        error_logs = [log for log in recent_logs if log.get("level") == "error"]
        
        error_rate = len(error_logs) / max(len(recent_logs), 1) * 100
        
        if len(error_logs) > self.error_threshold:
            await self._send_alert("High error rate detected", {
                "error_count": len(error_logs),
                "total_requests": len(recent_logs),
                "error_rate": error_rate
            })
        
        return {
            "error_count": len(error_logs),
            "total_requests": len(recent_logs),
            "error_rate": error_rate
        }
    
    async def analyze_response_times(self, logs: list) -> dict:
        """Analyze response times"""
        api_logs = [log for log in logs if log.get("event_type") == "api_performance"]
        
        if not api_logs:
            return {"average_response_time": 0, "slow_requests": 0}
        
        response_times = [log.get("response_time", 0) for log in api_logs]
        average = sum(response_times) / len(response_times)
        slow_requests = len([rt for rt in response_times if rt > self.response_time_threshold])
        
        if average > self.response_time_threshold:
            await self._send_alert("High response times detected", {
                "average_response_time": average,
                "slow_requests": slow_requests,
                "total_requests": len(api_logs)
            })
        
        return {
            "average_response_time": average,
            "slow_requests": slow_requests,
            "total_requests": len(api_logs)
        }
    
    def _is_recent(self, log: dict, seconds: int) -> bool:
        """Check if log entry is recent"""
        try:
            log_time = datetime.fromisoformat(log.get("timestamp", ""))
            return (datetime.utcnow() - log_time).total_seconds() <= seconds
        except:
            return False
    
    async def _send_alert(self, message: str, data: dict):
        """Send alert (could integrate with Slack, email, etc.)"""
        self.logger.critical(
            "ALERT: " + message,
            alert_data=data,
            event_type="alert"
        )
        
        # Here you could integrate with:
        # - Slack notifications
        # - Email alerts
        # - PagerDuty
        # - Discord webhooks
        # etc.

# Global log analyzer
log_analyzer = LogAnalyzer()

# Utility functions
def get_logger(name: str = None):
    """Get a logger instance"""
    return structlog.get_logger(name) if name else logger

def log_exception(exc: Exception, context: dict = None):
    """Log an exception with context"""
    logger.error(
        "Exception occurred",
        exception=str(exc),
        exception_type=type(exc).__name__,
        context=context or {},
        event_type="exception"
    )

def log_startup():
    """Log application startup"""
    logger.info(
        "AI Company Web starting up",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        log_level=settings.LOG_LEVEL,
        event_type="startup"
    )

def log_shutdown():
    """Log application shutdown"""
    logger.info(
        "AI Company Web shutting down",
        event_type="shutdown"
    )