"""
Elders Guild Unified API Specification - 統合API仕様システム
Created: 2025-07-11
Author: Claude Elder
"""

from typing import Dict, List, Optional, Any, Union, Type, get_type_hints
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from abc import ABC, abstractmethod

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import uvicorn

from .elders_guild_data_models import (
    BaseDataModel,
    KnowledgeEntity,
    TaskEntity,
    IncidentEntity,
    DocumentEntity,
    RAGContext,
    SageType,
    DataStatus,
    DataPriority,
)
from .elders_guild_event_bus import ElderGuildEventBus, EventType

# ============================================================================
# API Base Models
# ============================================================================


class APIResponse(BaseModel):
    """API統一レスポンス"""

    success: bool = Field(..., description="処理成功フラグ")
    message: str = Field(..., description="メッセージ")
    data: Optional[Any] = Field(None, description="データ")
    errors: Optional[List[str]] = Field(None, description="エラーリスト")
    metadata: Optional[Dict[str, Any]] = Field(None, description="メタデータ")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="タイムスタンプ"
    )

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class PaginatedResponse(BaseModel):
    """ページネーション付きレスポンス"""

    items: List[Any] = Field(..., description="アイテムリスト")
    total: int = Field(..., description="総件数")
    page: int = Field(..., description="ページ番号")
    per_page: int = Field(..., description="1ページあたりの件数")
    has_next: bool = Field(..., description="次ページの有無")
    has_previous: bool = Field(..., description="前ページの有無")


class APIError(BaseModel):
    """API エラー"""

    error_code: str = Field(..., description="エラーコード")
    error_message: str = Field(..., description="エラーメッセージ")
    error_details: Optional[Dict[str, Any]] = Field(None, description="エラー詳細")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="タイムスタンプ"
    )


# ============================================================================
# API Request Models
# ============================================================================


class SearchRequest(BaseModel):
    """検索リクエスト"""

    query: str = Field(..., description="検索クエリ")
    search_type: str = Field(default="semantic", description="検索タイプ")
    filters: Optional[Dict[str, Any]] = Field(None, description="フィルター")
    limit: int = Field(default=10, ge=1, le=100, description="取得件数")
    offset: int = Field(default=0, ge=0, description="オフセット")
    include_metadata: bool = Field(default=True, description="メタデータ含有フラグ")


class BulkOperationRequest(BaseModel):
    """バルク操作リクエスト"""

    operation: str = Field(..., description="操作タイプ")
    items: List[Dict[str, Any]] = Field(..., description="操作対象アイテム")
    options: Optional[Dict[str, Any]] = Field(None, description="オプション")


class EventPublishRequest(BaseModel):
    """イベント発行リクエスト"""

    event_type: str = Field(..., description="イベントタイプ")
    source: str = Field(..., description="発行元")
    data: Dict[str, Any] = Field(..., description="イベントデータ")
    metadata: Optional[Dict[str, Any]] = Field(None, description="メタデータ")
    priority: int = Field(default=2, ge=1, le=4, description="優先度")


# ============================================================================
# API Version Management
# ============================================================================


class APIVersion(Enum):
    """API バージョン"""

    V1 = "v1"
    V2 = "v2"
    LATEST = "latest"


@dataclass
class APIVersionInfo:
    """API バージョン情報"""

    version: APIVersion
    description: str
    supported_until: Optional[datetime] = None
    deprecated: bool = False
    changes: List[str] = field(default_factory=list)


class APIVersionManager:
    """API バージョン管理"""

    def __init__(self):
        """初期化メソッド"""
        self.versions = {
            APIVersion.V1: APIVersionInfo(
                version=APIVersion.V1,
                description="Initial API version with basic CRUD operations",
                supported_until=datetime(2026, 1, 1),
                changes=["Initial release"],
            ),
            APIVersion.V2: APIVersionInfo(
                version=APIVersion.V2,
                description="Enhanced API with event system and advanced search",
                changes=[
                    "Added event system",
                    "Enhanced search capabilities",
                    "Improved error handling",
                ],
            ),
        }

    def get_version_info(self, version: APIVersion) -> APIVersionInfo:
        """バージョン情報取得"""
        return self.versions.get(version)

    def get_current_version(self) -> APIVersion:
        """現在のバージョン取得"""
        return APIVersion.V2

    def is_version_supported(self, version: APIVersion) -> bool:
        """バージョンサポート確認"""
        version_info = self.get_version_info(version)
        if not version_info:
            return False

        if version_info.deprecated:
            return False

        if (
            version_info.supported_until
            and datetime.now() > version_info.supported_until
        ):
            return False

        return True


# ============================================================================
# Authentication & Authorization
# ============================================================================


class UserRole(Enum):
    """ユーザーロール"""

    ADMIN = "admin"
    ELDER = "elder"
    SAGE = "sage"
    USER = "user"
    GUEST = "guest"


class APIPermission(Enum):
    """API権限"""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    SAGE_KNOWLEDGE = "sage.knowledge"
    SAGE_TASK = "sage.task"
    SAGE_INCIDENT = "sage.incident"
    SAGE_RAG = "sage.rag"


@dataclass
class APIUser:
    """API ユーザー"""

    user_id: str
    username: str
    role: UserRole
    permissions: List[APIPermission]
    sage_type: Optional[SageType] = None

    def has_permission(self, permission: APIPermission) -> bool:
        """権限チェック"""
        return permission in self.permissions or APIPermission.ADMIN in self.permissions


class AuthenticationService:
    """認証サービス"""

    def __init__(self):
        """初期化メソッド"""
        self.security = HTTPBearer()

    async def authenticate(
        self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> APIUser:
        """認証処理"""
        token = credentials.credentials

        # トークン検証（実装例）
        user = await self._verify_token(token)
        if not user:
            raise HTTPException(
                status_code=401, detail="Invalid authentication credentials"
            )

        return user

    async def _verify_token(self, token: str) -> Optional[APIUser]:
        """トークン検証"""
        # 実際のトークン検証ロジック
        # 現在は簡易実装
        if token == "elder-admin-token":
            return APIUser(
                user_id="elder-admin",
                username="Elder Admin",
                role=UserRole.ADMIN,
                permissions=[APIPermission.ADMIN],
            )

        return None


def require_permission(permission: APIPermission):
    """権限チェックデコレータ"""

    def decorator(func):
        """decoratorメソッド"""
        async def wrapper(*args, **kwargs):
            """wrapperメソッド"""
            # 認証情報の取得
            user = kwargs.get("current_user")
            if not user or not user.has_permission(permission):
                raise HTTPException(status_code=403, detail="Insufficient permissions")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# API Middleware
# ============================================================================


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """リクエストログ記録ミドルウェア"""

    async def dispatch(self, request: Request, call_next):
        """dispatchメソッド"""
        start_time = datetime.now()

        # リクエスト情報の記録
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "timestamp": start_time.isoformat(),
        }

        response = await call_next(request)

        # レスポンス情報の記録
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()

        response_info = {
            "status_code": response.status_code,
            "response_time": response_time,
            "timestamp": end_time.isoformat(),
        }

        # ログ出力（実装例）
        print(f"API Request: {request_info}")
        print(f"API Response: {response_info}")

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """レート制限ミドルウェア"""

    def __init__(self, app, calls_per_minute: int = 60):
        """初期化メソッド"""
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.requests = {}

    async def dispatch(self, request: Request, call_next):
        """dispatchメソッド"""
        client_ip = request.client.host
        current_time = datetime.now()

        # レート制限チェック
        if client_ip in self.requests:
            request_times = self.requests[client_ip]
            # 1分以内のリクエストをフィルタ
            recent_requests = [
                t for t in request_times if (current_time - t).total_seconds() < 60
            ]

            if len(recent_requests) >= self.calls_per_minute:
                return JSONResponse(
                    status_code=429, content={"error": "Rate limit exceeded"}
                )

            self.requests[client_ip] = recent_requests + [current_time]
        else:
            self.requests[client_ip] = [current_time]

        response = await call_next(request)
        return response


# ============================================================================
# API Endpoints Factory
# ============================================================================


class APIEndpointFactory:
    """API エンドポイントファクトリー"""

    def __init__(
        self, event_bus: ElderGuildEventBus, auth_service: AuthenticationService
    ):
        self.event_bus = event_bus
        self.auth_service = auth_service
        self.version_manager = APIVersionManager()

    def create_knowledge_endpoints(self, app: FastAPI):
        """Knowledge Sage API エンドポイント作成"""

        @app.get("/api/v2/knowledge/entities", response_model=APIResponse)
        async def list_knowledge_entities(
            page: int = Query(1, ge=1),
            per_page: int = Query(10, ge=1, le=100),
            category: Optional[str] = Query(None),
            tags: Optional[str] = Query(None),
            current_user: APIUser = Depends(self.auth_service.authenticate),
        ):
            """知識エンティティ一覧取得"""
            try:
                # 実際の実装ではデータベースから取得
                entities = []  # データベースから取得

                # イベント発行
                await self.event_bus.publish_event(
                    EventType.SAGE_KNOWLEDGE_SEARCHED,
                    source="api",
                    data={
                        "query_params": {
                            "page": page,
                            "per_page": per_page,
                            "category": category,
                        }
                    },
                    user_id=current_user.user_id,
                )

                return APIResponse(
                    success=True,
                    message="Knowledge entities retrieved successfully",
                    data=PaginatedResponse(
                        items=entities,
                        total=len(entities),
                        page=page,
                        per_page=per_page,
                        has_next=False,
                        has_previous=page > 1,
                    ),
                )
            except Exception as e:
                return APIResponse(
                    success=False,
                    message="Failed to retrieve knowledge entities",
                    errors=[str(e)],
                )

        @app.post("/api/v2/knowledge/entities", response_model=APIResponse)
        async def create_knowledge_entity(
            entity_data: Dict[str, Any] = Body(...),
            current_user: APIUser = Depends(self.auth_service.authenticate),
        ):
            """知識エンティティ作成"""
            try:
                # 権限チェック
                if not current_user.has_permission(APIPermission.SAGE_KNOWLEDGE):
                    raise HTTPException(
                        status_code=403, detail="Insufficient permissions"
                    )

                # エンティティ作成
                entity = KnowledgeEntity(**entity_data)

                # 実際の実装ではデータベースに保存

                # イベント発行
                await self.event_bus.publish_event(
                    EventType.SAGE_KNOWLEDGE_CREATED,
                    source="api",
                    data={"entity_id": entity.id, "title": entity.title},
                    user_id=current_user.user_id,
                )

                return APIResponse(
                    success=True,
                    message="Knowledge entity created successfully",
                    data=entity.to_dict(),
                )
            except Exception as e:
                return APIResponse(
                    success=False,
                    message="Failed to create knowledge entity",
                    errors=[str(e)],
                )

        @app.get("/api/v2/knowledge/entities/{entity_id}", response_model=APIResponse)
        async def get_knowledge_entity(
            entity_id: str = Path(...),
            current_user: APIUser = Depends(self.auth_service.authenticate),
        ):
            """知識エンティティ取得"""
            try:
                # 実際の実装ではデータベースから取得
                entity = None  # データベースから取得

                if not entity:
                    raise HTTPException(
                        status_code=404, detail="Knowledge entity not found"
                    )

                return APIResponse(
                    success=True,
                    message="Knowledge entity retrieved successfully",
                    data=entity,
                )
            except HTTPException:
                raise
            except Exception as e:
                return APIResponse(
                    success=False,
                    message="Failed to retrieve knowledge entity",
                    errors=[str(e)],
                )

        @app.post("/api/v2/knowledge/search", response_model=APIResponse)
        async def search_knowledge(
            search_request: SearchRequest,
            current_user: APIUser = Depends(self.auth_service.authenticate),
        ):
            """知識検索"""
            try:
                # 実際の実装では検索エンジンを使用
                results = []  # 検索結果

                # イベント発行
                await self.event_bus.publish_event(
                    EventType.SAGE_KNOWLEDGE_SEARCHED,
                    source="api",
                    data={
                        "query": search_request.query,
                        "search_type": search_request.search_type,
                    },
                    user_id=current_user.user_id,
                )

                return APIResponse(
                    success=True,
                    message="Knowledge search completed successfully",
                    data=results,
                )
            except Exception as e:
                return APIResponse(
                    success=False, message="Knowledge search failed", errors=[str(e)]
                )

    def create_task_endpoints(self, app: FastAPI):
        """Task Sage API エンドポイント作成"""

        @app.get("/api/v2/tasks/entities", response_model=APIResponse)
        async def list_task_entities(
            page: int = Query(1, ge=1),
            per_page: int = Query(10, ge=1, le=100),
            status: Optional[str] = Query(None),
            assigned_to: Optional[str] = Query(None),
            current_user: APIUser = Depends(self.auth_service.authenticate),
        ):
            """タスクエンティティ一覧取得"""
            try:
                # 実際の実装ではデータベースから取得
                entities = []

                return APIResponse(
                    success=True,
                    message="Task entities retrieved successfully",
                    data=PaginatedResponse(
                        items=entities,
                        total=len(entities),
                        page=page,
                        per_page=per_page,
                        has_next=False,
                        has_previous=page > 1,
                    ),
                )
            except Exception as e:
                return APIResponse(
                    success=False,
                    message="Failed to retrieve task entities",
                    errors=[str(e)],
                )

        @app.post("/api/v2/tasks/entities", response_model=APIResponse)
        async def create_task_entity(
            entity_data: Dict[str, Any] = Body(...),
            current_user: APIUser = Depends(self.auth_service.authenticate),
        ):
            """タスクエンティティ作成"""
            try:
                # 権限チェック
                if not current_user.has_permission(APIPermission.SAGE_TASK):
                    raise HTTPException(
                        status_code=403, detail="Insufficient permissions"
                    )

                # エンティティ作成
                entity = TaskEntity(**entity_data)

                # イベント発行
                await self.event_bus.publish_event(
                    EventType.SAGE_TASK_CREATED,
                    source="api",
                    data={"entity_id": entity.id, "name": entity.name},
                    user_id=current_user.user_id,
                )

                return APIResponse(
                    success=True,
                    message="Task entity created successfully",
                    data=entity.to_dict(),
                )
            except Exception as e:
                return APIResponse(
                    success=False,
                    message="Failed to create task entity",
                    errors=[str(e)],
                )

    def create_incident_endpoints(self, app: FastAPI):
        """Incident Sage API エンドポイント作成"""

        @app.get("/api/v2/incidents/entities", response_model=APIResponse)
        async def list_incident_entities(
            page: int = Query(1, ge=1),
            per_page: int = Query(10, ge=1, le=100),
            severity: Optional[str] = Query(None),
            status: Optional[str] = Query(None),
            current_user: APIUser = Depends(self.auth_service.authenticate),
        ):
            """インシデントエンティティ一覧取得"""
            try:
                # 実際の実装ではデータベースから取得
                entities = []

                return APIResponse(
                    success=True,
                    message="Incident entities retrieved successfully",
                    data=PaginatedResponse(
                        items=entities,
                        total=len(entities),
                        page=page,
                        per_page=per_page,
                        has_next=False,
                        has_previous=page > 1,
                    ),
                )
            except Exception as e:
                return APIResponse(
                    success=False,
                    message="Failed to retrieve incident entities",
                    errors=[str(e)],
                )

        @app.post("/api/v2/incidents/entities", response_model=APIResponse)
        async def create_incident_entity(
            entity_data: Dict[str, Any] = Body(...),
            current_user: APIUser = Depends(self.auth_service.authenticate),
        ):
            """インシデントエンティティ作成"""
            try:
                # 権限チェック
                if not current_user.has_permission(APIPermission.SAGE_INCIDENT):
                    raise HTTPException(
                        status_code=403, detail="Insufficient permissions"
                    )

                # エンティティ作成
                entity = IncidentEntity(**entity_data)

                # イベント発行
                await self.event_bus.publish_event(
                    EventType.SAGE_INCIDENT_CREATED,
                    source="api",
                    data={
                        "entity_id": entity.id,
                        "title": entity.title,
                        "severity": entity.severity,
                    },
                    user_id=current_user.user_id,
                )

                return APIResponse(
                    success=True,
                    message="Incident entity created successfully",
                    data=entity.to_dict(),
                )
            except Exception as e:
                return APIResponse(
                    success=False,
                    message="Failed to create incident entity",
                    errors=[str(e)],
                )

    def create_rag_endpoints(self, app: FastAPI):
        """RAG Sage API エンドポイント作成"""

        @app.post("/api/v2/rag/query", response_model=APIResponse)
        async def process_rag_query(
            query_data: Dict[str, Any] = Body(...),
            current_user: APIUser = Depends(self.auth_service.authenticate),
        ):
            """RAG クエリ処理"""
            try:
                # 権限チェック
                if not current_user.has_permission(APIPermission.SAGE_RAG):
                    raise HTTPException(
                        status_code=403, detail="Insufficient permissions"
                    )

                # クエリ処理
                context = RAGContext(**query_data)

                # 実際の実装では RAG エンジンを使用
                response = "Sample response"

                # イベント発行
                await self.event_bus.publish_event(
                    EventType.SAGE_RAG_QUERY_PROCESSED,
                    source="api",
                    data={"query": context.query, "session_id": context.session_id},
                    user_id=current_user.user_id,
                )

                return APIResponse(
                    success=True,
                    message="RAG query processed successfully",
                    data={"response": response, "context": context.to_dict()},
                )
            except Exception as e:
                return APIResponse(
                    success=False,
                    message="Failed to process RAG query",
                    errors=[str(e)],
                )

    def create_system_endpoints(self, app: FastAPI):
        """システム API エンドポイント作成"""

        @app.get("/api/v2/system/health", response_model=APIResponse)
        async def system_health():
            """システムヘルスチェック"""
            try:
                # 各コンポーネントのヘルスチェック
                health_status = {
                    "database": "healthy",
                    "event_bus": "healthy",
                    "cache": "healthy",
                    "timestamp": datetime.now().isoformat(),
                }

                return APIResponse(
                    success=True,
                    message="System health check completed",
                    data=health_status,
                )
            except Exception as e:
                return APIResponse(
                    success=False, message="System health check failed", errors=[str(e)]
                )

        @app.get("/api/v2/system/version", response_model=APIResponse)
        async def get_api_version():
            """API バージョン情報取得"""
            try:
                current_version = self.version_manager.get_current_version()
                version_info = self.version_manager.get_version_info(current_version)

                return APIResponse(
                    success=True,
                    message="API version information retrieved",
                    data={
                        "current_version": current_version.value,
                        "description": version_info.description,
                        "supported_versions": [v.value for v in APIVersion],
                        "changes": version_info.changes,
                    },
                )
            except Exception as e:
                return APIResponse(
                    success=False,
                    message="Failed to retrieve API version information",
                    errors=[str(e)],
                )

        @app.post("/api/v2/system/events", response_model=APIResponse)
        async def publish_system_event(
            event_request: EventPublishRequest,
            current_user: APIUser = Depends(self.auth_service.authenticate),
        ):
            """システムイベント発行"""
            try:
                # 権限チェック
                if not current_user.has_permission(APIPermission.ADMIN):
                    raise HTTPException(
                        status_code=403, detail="Insufficient permissions"
                    )

                # イベント発行
                await self.event_bus.publish_event(
                    EventType(event_request.event_type),
                    source=event_request.source,
                    data=event_request.data,
                    metadata=event_request.metadata,
                    user_id=current_user.user_id,
                )

                return APIResponse(
                    success=True,
                    message="System event published successfully",
                    data={"event_type": event_request.event_type},
                )
            except Exception as e:
                return APIResponse(
                    success=False,
                    message="Failed to publish system event",
                    errors=[str(e)],
                )


# ============================================================================
# Main API Application
# ============================================================================


class ElderGuildAPI:
    """エルダーズギルド統合API"""

    def __init__(self, event_bus:
        """初期化メソッド"""
    ElderGuildEventBus):
        self.event_bus = event_bus
        self.auth_service = AuthenticationService()
        self.endpoint_factory = APIEndpointFactory(event_bus, self.auth_service)
        self.app = self._create_app()

    def _create_app(self) -> FastAPI:
        """FastAPI アプリケーション作成"""
        app = FastAPI(
            title="Elders Guild Unified API",
            description="エルダーズギルド統合プラットフォーム API",
            version="2.0.0",
            docs_url="/api/docs",
            redoc_url="/api/redoc",
        )

        # CORS設定
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # カスタムミドルウェア
        app.add_middleware(RequestLoggingMiddleware)
        app.add_middleware(RateLimitMiddleware)

        # エンドポイント作成
        self.endpoint_factory.create_knowledge_endpoints(app)
        self.endpoint_factory.create_task_endpoints(app)
        self.endpoint_factory.create_incident_endpoints(app)
        self.endpoint_factory.create_rag_endpoints(app)
        self.endpoint_factory.create_system_endpoints(app)

        return app

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """API サーバー起動"""
        uvicorn.run(self.app, host=host, port=port)


# ============================================================================
# Usage Example
# ============================================================================


async def main():
    """使用例"""
    from .elders_guild_db_manager import EldersGuildDatabaseManager, DatabaseConfig

    # データベース設定
    db_config = DatabaseConfig()
    db_manager = EldersGuildDatabaseManager(db_config)

    # イベントバス
    event_bus = ElderGuildEventBus(db_manager)
    await event_bus.initialize()
    await event_bus.start()

    # API アプリケーション
    api = ElderGuildAPI(event_bus)

    print("Starting Elders Guild API server...")
    print("API Documentation: http://localhost:8000/api/docs")

    # API サーバー起動
    api.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
