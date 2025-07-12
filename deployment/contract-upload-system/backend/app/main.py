"""
契約書アップロードシステム - Elder Flow準拠本番環境対応
"""

import os
import logging
from datetime import datetime
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException

# アプリケーションモジュール
from app.api.endpoints import contract
from app.api.v1 import monitoring
from app.middleware.security import configure_security_middleware, file_upload_security
from app.core.auth_production import get_current_user, login, refresh_access_token

# ログ設定
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if os.getenv('LOG_FORMAT') != 'json' else None
)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション作成
app = FastAPI(
    title="契約書アップロードシステム - Elder Flow準拠",
    description="エルダーズギルド品質基準準拠 本番環境対応システム",
    version="2.1.0",
    docs_url="/docs" if os.getenv('ENVIRONMENT') != 'production' else None,
    redoc_url="/redoc" if os.getenv('ENVIRONMENT') != 'production' else None
)

# セキュリティミドルウェア設定
configure_security_middleware(app)

# ルーター登録
app.include_router(contract.router, prefix="/api/v1/contract", tags=["contract"])
app.include_router(monitoring.router, tags=["monitoring"])

# エラーハンドリング
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP例外ハンドラー"""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """一般例外ハンドラー"""
    logger.error(f"Unhandled exception: {str(exc)} - {request.url}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# 基本エンドポイント
@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "契約書アップロードシステム API - Elder Flow準拠",
        "version": "2.1.0",
        "elder_guild": "品質基準準拠",
        "environment": os.getenv('ENVIRONMENT', 'development'),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """基本ヘルスチェック (後方互換性)"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.1.0"
    }

# 認証エンドポイント
@app.post("/api/v1/auth/login")
async def login_endpoint(username: str, password: str):
    """ログイン"""
    return await login(username, password)

@app.post("/api/v1/auth/refresh")
async def refresh_token_endpoint(refresh_token: str):
    """トークン更新"""
    return await refresh_access_token(refresh_token)

@app.get("/api/v1/auth/me")
async def get_current_user_endpoint(current_user: dict = Depends(get_current_user)):
    """現在のユーザー情報取得"""
    return current_user

# 起動時処理
@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時処理"""
    logger.info("契約書アップロードシステム起動中...")
    logger.info(f"環境: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"バージョン: 2.1.0")
    logger.info("Elder Flow準拠セキュリティ機能有効")

@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時処理"""
    logger.info("契約書アップロードシステム終了")
