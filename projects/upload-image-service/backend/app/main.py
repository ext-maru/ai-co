from app.api.endpoints import admin
from app.api.endpoints import auth
from app.api.endpoints import upload
from app.core.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Upload Image Manager", description="画像アップロード管理システム", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(upload.router, prefix="/api/v1/upload", tags=["upload"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])


@app.get("/")
async def root():
    return {"message": "Upload Image Manager API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
