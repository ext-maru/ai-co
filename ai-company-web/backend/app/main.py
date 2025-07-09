"""
AI Company Web - FastAPI Backend Main Application
Phase 4: Production-Ready Elder's Guild Four Sages System
"""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Import API routers
from app.api.v1.api import api_router
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.migration import router as migration_router
from app.api.endpoints.monitoring import router as monitoring_router
from app.api.endpoints.elder_council import router as elder_council_router
from app.api.endpoints.sages_incidents import router as sages_incidents_router
from app.api.endpoints.sages_knowledge import router as sages_knowledge_router
from app.api.endpoints.sages_search import router as sages_search_router
from app.api.endpoints.sages_tasks import router as sages_tasks_router
from app.api.endpoints.websocket_routes import router as websocket_router

# Import core modules
from app.core.config import settings
from app.core.logging import (
    logger_manager, 
    log_startup, 
    log_shutdown, 
    request_logger, 
    security_logger,
    performance_logger
)
from app.core.database import db_manager, check_database_health, check_redis_health
from app.core.security import SecurityHeaders

# Import middleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import SecurityMiddleware

# Import WebSocket manager
from app.websocket.secure_manager import websocket_manager

# Configure structured logging
log_startup()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager for startup and shutdown events.
    Enhanced with Elder's Guild production features.
    """
    # Startup
    logger.info("🏰 Starting AI Company Web - Elder's Guild Phase 4")
    
    try:
        # Initialize database
        if settings.DATABASE_URL:
            db_manager.create_tables()
            db_health = await check_database_health()
            logger.info("Database status", status=db_health["status"])
        
        # Check Redis
        redis_health = await check_redis_health()
        logger.info("Redis status", status=redis_health["status"])
        
        # Initialize WebSocket manager
        logger.info("Initializing secure WebSocket manager")
        
        # Announce startup completion
        logger.info(
            "🚀 AI Company Web Elder's Guild System ONLINE",
            environment=settings.ENVIRONMENT,
            elder_council_enabled=settings.ELDER_COUNCIL_ENABLED,
            max_sages=settings.MAX_SAGES,
            coverage_target=settings.COVERAGE_TARGET
        )
        
    except Exception as e:
        logger.error("Startup failed", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("🏰 Shutting down AI Company Web - Elder's Guild")
    
    try:
        # Cleanup WebSocket connections
        logger.info("Closing WebSocket connections")
        
        # Log shutdown
        log_shutdown()
        
    except Exception as e:
        logger.error("Shutdown error", error=str(e))


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    Enhanced for Elder's Guild production deployment.
    """
    app = FastAPI(
        title="AI Company Web - Elder's Guild API",
        description="Production-ready Four Sages System with Elder Council governance",
        version="1.0.0",
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
        openapi_url="/api/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # Add Security Middleware (first in chain)
    app.add_middleware(SecurityMiddleware)
    
    # Add Rate Limiting Middleware
    app.add_middleware(RateLimitMiddleware)

    # Security Middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if not settings.is_production else [
            "ai-company.com",
            "www.ai-company.com",
            "ai-company-web.vercel.app",
            "ai-company-api.railway.app"
        ],
    )

    # CORS Middleware for Next.js integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    )

    # Request/Response logging middleware
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            "HTTP request started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host,
            user_agent=request.headers.get("user-agent", "")
        )
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add performance headers
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log successful request
            await request_logger.log_request(request, response, process_time)
            
            # Log performance if slow
            if process_time > 1.0:  # Slow request threshold
                await performance_logger.log_api_performance(
                    str(request.url.path),
                    process_time,
                    response.status_code
                )
            
            return response
            
        except Exception as e:
            # Log error
            await request_logger.log_error(request, e)
            raise

    # Exception handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        headers = SecurityHeaders.get_security_headers()
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "timestamp": time.time()
            },
            headers=headers
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        headers = SecurityHeaders.get_security_headers()
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "details": exc.errors(),
                "timestamp": time.time()
            },
            headers=headers
        )

    # Include API routes
    app.include_router(api_router, prefix="/api")
    
    # Include specific endpoint routers
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(migration_router, prefix="/api/v1/migration", tags=["Migration"])
    app.include_router(monitoring_router, prefix="/api/v1/monitoring", tags=["Monitoring"])
    app.include_router(elder_council_router, prefix="/api/v1/elder-council", tags=["Elder Council"])
    app.include_router(sages_incidents_router, prefix="/api/v1/sages/incidents", tags=["Incident Sage"])
    app.include_router(sages_knowledge_router, prefix="/api/v1/sages/knowledge", tags=["Knowledge Sage"])
    app.include_router(sages_search_router, prefix="/api/v1/sages/search", tags=["Search Sage"])
    app.include_router(sages_tasks_router, prefix="/api/v1/sages/tasks", tags=["Task Sage"])
    app.include_router(websocket_router, prefix="/api/v1/ws", tags=["WebSocket"])

    return app


# Create the FastAPI application instance
app = create_application()


@app.get("/health")
async def health_check():
    """
    Enhanced health check endpoint with component status.
    """
    try:
        # Check database
        db_health = await check_database_health()
        
        # Check Redis
        redis_health = await check_redis_health()
        
        # Overall health
        overall_status = "healthy"
        if (db_health.get("status") != "healthy" or 
            redis_health.get("status") != "healthy"):
            overall_status = "degraded"
        
        response_data = {
            "status": overall_status,
            "service": "ai-company-web-api",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "timestamp": time.time(),
            "components": {
                "database": db_health,
                "redis": redis_health,
                "elder_council": {
                    "status": "healthy",
                    "enabled": settings.ELDER_COUNCIL_ENABLED
                },
                "sages": {
                    "status": "healthy",
                    "max_count": settings.MAX_SAGES,
                    "coverage_target": settings.COVERAGE_TARGET
                }
            }
        }
        
        status_code = 200 if overall_status == "healthy" else 503
        headers = SecurityHeaders.get_security_headers()
        
        return JSONResponse(
            content=response_data,
            status_code=status_code,
            headers=headers
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        headers = SecurityHeaders.get_security_headers()
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            },
            status_code=503,
            headers=headers
        )


@app.get("/")
async def root():
    """
    Root endpoint with Elder's Guild API information.
    """
    headers = SecurityHeaders.get_security_headers()
    
    return JSONResponse(
        content={
            "message": "🏰 AI Company Web - Elder's Guild API",
            "description": "Production-ready Four Sages System with Elder Council governance",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "features": {
                "elder_council": settings.ELDER_COUNCIL_ENABLED,
                "max_sages": settings.MAX_SAGES,
                "coverage_target": f"{settings.COVERAGE_TARGET}%",
                "security": "Enterprise-grade OWASP Top 10 compliant",
                "websocket": "Secure real-time communication",
                "migration": "Gradual Flask API integration"
            },
            "endpoints": {
                "health": "/health",
                "docs": "/api/docs" if not settings.is_production else "disabled",
                "elder_council": "/api/v1/elder-council",
                "sages": "/api/v1/sages",
                "auth": "/api/v1/auth",
                "monitoring": "/api/v1/monitoring",
                "websocket": "/api/v1/ws"
            },
            "timestamp": time.time()
        },
        headers=headers
    )


@app.get("/api/v1/system/info")
async def system_info():
    """
    System information endpoint for Elder Council.
    """
    try:
        # Get WebSocket connection stats
        ws_stats = websocket_manager.get_connection_stats()
        
        headers = SecurityHeaders.get_security_headers()
        
        return JSONResponse(
            content={
                "system": "AI Company Web - Elder's Guild",
                "phase": "Phase 4 - Production Deployment",
                "status": "operational",
                "architecture": {
                    "frontend": "Next.js 15 on Vercel",
                    "backend": "FastAPI on Railway",
                    "database": "PostgreSQL with Redis cache",
                    "cdn": "Cloudflare with edge optimization",
                    "websocket": "Secure real-time communication"
                },
                "security": {
                    "authentication": "JWT + OAuth 2.1",
                    "authorization": "Elder hierarchy (Grand Elder > Elder > Sage > Servant)",
                    "protection": "OWASP Top 10 compliant",
                    "rate_limiting": "Multi-tier with Redis backend",
                    "headers": "Comprehensive security headers"
                },
                "monitoring": {
                    "logging": "Structured with Sentry integration",
                    "performance": "Core Web Vitals tracking",
                    "analytics": "Real-time monitoring",
                    "alerts": "Automated alert system"
                },
                "websocket_stats": ws_stats,
                "timestamp": time.time()
            },
            headers=headers
        )
        
    except Exception as e:
        logger.error("System info failed", error=str(e))
        raise


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🏰 Starting AI Company Web development server")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    logger.info(f"Redis: {settings.REDIS_URL.split('@')[-1] if '@' in settings.REDIS_URL else settings.REDIS_URL}")
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=not settings.is_production,
        log_level="info",
        workers=settings.WORKERS if settings.is_production else 1,
    )