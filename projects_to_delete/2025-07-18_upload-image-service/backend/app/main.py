from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router


# データベース初期化
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時
    Base.metadata.create_all(bind=engine)
    yield
    # 終了時


# FastAPIアプリケーション作成
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーター登録
app.include_router(api_router, prefix="/api/v1")

# ヘルスチェック
@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.version}

# ルートエンドポイント
@app.get("/")
async def root():
    return {
        "message": "Upload Image Service API",
        "version": settings.version,
        "docs": "/docs"
    }
