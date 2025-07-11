from fastapi import APIRouter
from app.api.v1.endpoints import sessions, admin, uploads, google_drive

api_router = APIRouter()

# エンドポイント登録
api_router.include_router(sessions.router, tags=["sessions"])
api_router.include_router(admin.router, tags=["admin"])
api_router.include_router(uploads.router, tags=["uploads"])
api_router.include_router(google_drive.router, tags=["google-drive"])
