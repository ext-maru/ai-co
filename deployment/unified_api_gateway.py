#!/usr/bin/env python3
"""
Elders Guild 統合APIゲートウェイ v1.0
統一APIインターフェースによる4賢者システム統合
"""

import asyncio
import json
import logging
import traceback
from dataclasses import asdict
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from flask import Blueprint, Flask, jsonify, request
from flask_cors import CORS

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent

try:
    from integration.unified_entity_manager import (
        BaseEntity,
        EntityRelationship,
        IncidentEntity,
        KnowledgeEntity,
        TaskEntity,
        UnifiedEntityManager,
        create_incident_entity,
        create_knowledge_entity,
        create_task_entity,
    )
    from integration.unified_rag_manager import SearchQuery, UnifiedRAGManager
except ImportError:
    # フォールバック
    from .unified_entity_manager import (
        BaseEntity,
        EntityRelationship,
        IncidentEntity,
        KnowledgeEntity,
        TaskEntity,
        UnifiedEntityManager,
        create_incident_entity,
        create_knowledge_entity,
        create_task_entity,
    )
    from .unified_rag_manager import SearchQuery, UnifiedRAGManager

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flaskアプリケーション設定
app = Flask(__name__)
CORS(app)  # CORS対応

# Blueprint設定
api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")

# グローバルマネージャーインスタンス
entity_manager = UnifiedEntityManager()
rag_manager = UnifiedRAGManager(entity_manager)


class APIError(Exception):
    """API専用例外クラス"""

    def __init__(self, message: str, status_code: int = 400, details: Dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class UnifiedAPIAuth:
    """統合API認証・認可システム"""

    def __init__(self):
        # 4賢者システムの権限定義
        self.sage_permissions = {
            "knowledge_sage": {
                "entities": ["create", "read", "update", "delete"],
                "knowledge": ["create", "read", "update", "delete"],
                "search": ["read"],
                "relationships": ["create", "read", "update", "delete"],
            },
            "task_oracle": {
                "entities": ["read"],
                "tasks": ["create", "read", "update", "delete"],
                "search": ["read"],
                "relationships": ["read"],
            },
            "crisis_sage": {
                "entities": ["create", "read", "update"],
                "incidents": ["create", "read", "update", "delete"],
                "search": ["read"],
                "relationships": ["create", "read", "update"],
            },
            "search_mystic": {
                "entities": ["read"],
                "search": ["create", "read", "update", "delete"],
                "relationships": ["read"],
                "analytics": ["read"],
            },
            "system": {
                "entities": ["create", "read", "update", "delete"],
                "knowledge": ["create", "read", "update", "delete"],
                "incidents": ["create", "read", "update", "delete"],
                "tasks": ["create", "read", "update", "delete"],
                "search": ["create", "read", "update", "delete"],
                "relationships": ["create", "read", "update", "delete"],
                "analytics": ["read"],
            },
        }

    def authorize_sage(self, sage_type: str, resource: str, action: str) -> bool:
        """賢者システムの認可チェック"""
        permissions = self.sage_permissions.get(sage_type, {})
        resource_perms = permissions.get(resource, [])
        return action in resource_perms

    def get_sage_from_request(self, request) -> Optional[str]:
        """リクエストから賢者タイプを取得"""
        # ヘッダーから賢者情報を取得
        sage_type = request.headers.get("X-Sage-Type")
        if sage_type in self.sage_permissions:
            return sage_type

        # APIキーベースの認証（簡易版）
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # 実際の実装では安全なAPIキー検証を行う
            sage_mapping = {
                "knowledge-sage-key": "knowledge_sage",
                "task-oracle-key": "task_oracle",
                "crisis-sage-key": "crisis_sage",
                "search-mystic-key": "search_mystic",
                "system-key": "system",
            }
            return sage_mapping.get(api_key)

        # デフォルトはシステム権限
        return "system"


# 認証インスタンス
auth = UnifiedAPIAuth()


def require_permission(resource: str, action: str):
    """権限チェックデコレータ"""

        def decorated_function(*args, **kwargs):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not sage_type:
                raise APIError("Authentication required", 401)

            if not auth.authorize_sage(sage_type, resource, action):
                raise APIError(f"Permission denied for {resource}:{action}", 403)

            # 賢者情報をリクエストコンテキストに追加
            request.sage_type = sage_type
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def handle_async(f):
    """非同期関数をFlaskで扱うためのデコレータ"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        """wrapperメソッド"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
def entity_to_dict(entity: BaseEntity) -> Dict[str, Any]:
    """エンティティを辞書に変換"""

    return wrapper

def entity_to_dict(entity: BaseEntity) -> Dict[str, Any]:
    """エンティティを辞書に変換"""
        "title": entity.title,
        "content": entity.content,
        "metadata": entity.metadata,
        "relationships": entity.relationships,
        "search_metadata": entity.search_metadata,
        "created_at": entity.created_at.isoformat() if entity.created_at else None,
        "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
    }

    # エンティティ固有データ追加
    if isinstance(entity, KnowledgeEntity):
        result["knowledge_data"] = entity.knowledge_data
    elif isinstance(entity, IncidentEntity):
        result["incident_data"] = entity.incident_data
    elif isinstance(entity, TaskEntity):
        result["task_data"] = entity.task_data

    return result


# ============================================
# エンティティ管理API
# ============================================


@api_v1.route("/entities", methods=["POST"])
@require_permission("entities", "create")
def create_entity():
    """エンティティ作成"""
    try:
        data = request.get_json()

        if not data:
            raise APIError("Request body is required")

        entity_type = data.get("type")
        if not entity_type:
            raise APIError("Entity type is required")

        # エンティティタイプに応じたオブジェクト作成
        if entity_type == "knowledge":
            entity = create_knowledge_entity(
                title=data.get("title", ""),
                content=data.get("content", ""),
                confidence_score=data.get("confidence_score", 0.8),
                domain=data.get("domain", "general"),
            )
            if "knowledge_data" in data:
                entity.knowledge_data.update(data["knowledge_data"])

        elif entity_type == "incident":
            entity = create_incident_entity(
                title=data.get("title", ""),
                content=data.get("content", ""),
                severity=data.get("severity", "medium"),
                affected_systems=data.get("affected_systems", []),
            )
            if "incident_data" in data:
                entity.incident_data.update(data["incident_data"])

        elif entity_type == "task":
            entity = create_task_entity(
                title=data.get("title", ""),
                content=data.get("content", ""),
                task_type=data.get("task_type", "general"),
                assigned_worker=data.get("assigned_worker"),
            )
            if "task_data" in data:
                entity.task_data.update(data["task_data"])

        else:
            # 基本エンティティ
            entity = BaseEntity(
                id=data.get("id", ""),
                type=entity_type,
                title=data.get("title", ""),
                content=data.get("content", ""),
            )

        # メタデータ設定
        if "metadata" in data:
            entity.metadata.update(data["metadata"])

        # エンティティ作成
        entity_id = entity_manager.create_entity(entity)

        return (
            jsonify(
                {
                    "success": True,
                    "entity_id": entity_id,
                    "message": "Entity created successfully",
                }
            ),
            201,
        )

    except APIError:
        raise
    except Exception as e:
        logger.error(f"Create entity error: {e}")
        raise APIError("Internal server error", 500)


@api_v1.route("/entities/<entity_id>", methods=["GET"])
@require_permission("entities", "read")
def get_entity(entity_id: str):
    """エンティティ取得"""
    try:
        entity = entity_manager.get_entity(entity_id)

        if not entity:
            raise APIError("Entity not found", 404)

        return jsonify({"success": True, "entity": entity_to_dict(entity)})

    except APIError:
        raise
    except Exception as e:
        logger.error(f"Get entity error: {e}")
        raise APIError("Internal server error", 500)


@api_v1.route("/entities/<entity_id>", methods=["PUT"])
@require_permission("entities", "update")
def update_entity(entity_id: str):
    """エンティティ更新"""
    try:
        data = request.get_json()

        if not data:
            raise APIError("Request body is required")

        # 既存エンティティ取得
        entity = entity_manager.get_entity(entity_id)
        if not entity:
            raise APIError("Entity not found", 404)

        # 更新可能フィールドの設定
        if "title" in data:
            entity.title = data["title"]
        if "content" in data:
            entity.content = data["content"]
        if "metadata" in data:
            entity.metadata.update(data["metadata"])

        # エンティティ固有データの更新
        if isinstance(entity, KnowledgeEntity) and "knowledge_data" in data:
            entity.knowledge_data.update(data["knowledge_data"])
        elif isinstance(entity, IncidentEntity) and "incident_data" in data:
            entity.incident_data.update(data["incident_data"])
        elif isinstance(entity, TaskEntity) and "task_data" in data:
            entity.task_data.update(data["task_data"])

        # 更新実行
        success = entity_manager.update_entity(entity)

        if not success:
            raise APIError("Failed to update entity", 500)

        return jsonify({"success": True, "message": "Entity updated successfully"})

    except APIError:
        raise
    except Exception as e:
        logger.error(f"Update entity error: {e}")
        raise APIError("Internal server error", 500)


@api_v1.route("/entities/<entity_id>", methods=["DELETE"])
@require_permission("entities", "delete")
def delete_entity(entity_id: str):
    """エンティティ削除"""
    try:
        success = entity_manager.delete_entity(entity_id)

        if not success:
            raise APIError("Entity not found or deletion failed", 404)

        return jsonify({"success": True, "message": "Entity deleted successfully"})

    except APIError:
        raise
    except Exception as e:
        logger.error(f"Delete entity error: {e}")
        raise APIError("Internal server error", 500)


@api_v1.route("/entities", methods=["GET"])
@require_permission("entities", "read")
def list_entities():
    """エンティティ一覧取得"""
    try:
        # クエリパラメータ取得
        entity_type = request.args.get("type")
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))

        # フィルタ作成
        filters = {}
        if request.args.get("status"):
            filters["status"] = request.args.get("status")
        if request.args.get("priority"):
            filters["priority"] = request.args.get("priority")
        if request.args.get("category"):
            filters["category"] = request.args.get("category")

        entities = entity_manager.list_entities(
            entity_type=entity_type, limit=limit, offset=offset, filters=filters
        )

        return jsonify(
            {
                "success": True,
                "entities": [entity_to_dict(entity) for entity in entities],
                "count": len(entities),
                "limit": limit,
                "offset": offset,
            }
        )

    except APIError:
        raise
    except Exception as e:
        logger.error(f"List entities error: {e}")
        raise APIError("Internal server error", 500)


# ============================================
# 統合検索API
# ============================================


@api_v1.route("/search/unified", methods=["POST"])
@require_permission("search", "read")
@handle_async
async def unified_search():
    """統合検索"""
    try:
        data = request.get_json()

        if not data or "query" not in data:
            raise APIError("Query is required")

        # 検索クエリ構築
        search_query = SearchQuery(
            text=data["query"],
            entity_types=data.get("entity_types"),
            filters=data.get("filters"),
            limit=data.get("limit", 20),
            include_relationships=data.get("include_relationships", True),
            max_relationship_depth=data.get("max_relationship_depth", 2),
            semantic_threshold=data.get("semantic_threshold", 0.7),
            intent=data.get("intent"),
        )

        # 検索実行
        result = await rag_manager.search(search_query)

        return jsonify(
            {
                "success": True,
                "query": {
                    "text": result.query.text,
                    "intent": result.query.intent,
                    "entity_types": result.query.entity_types,
                },
                "primary_results": [
                    entity_to_dict(entity) for entity in result.primary_results
                ],
                "related_entities": [
                    entity_to_dict(entity) for entity in result.related_entities
                ],
                "relationships": result.relationships,
                "confidence_scores": result.confidence_scores,
                "assembled_context": result.assembled_context,
                "total_found": result.total_found,
                "search_time_ms": result.search_time_ms,
                "suggestions": result.suggestions,
            }
        )

    except APIError:
        raise
    except Exception as e:
        logger.error(f"Unified search error: {e}")
        raise APIError("Internal server error", 500)


@api_v1.route("/search/knowledge", methods=["POST"])
@require_permission("search", "read")
@handle_async
async def search_knowledge():
    """知識検索"""
    try:
        data = request.get_json()

        if not data or "query" not in data:
            raise APIError("Query is required")

        result = await rag_manager.search_knowledge(
            query=data["query"], domain=data.get("domain")
        )

        return jsonify(
            {
                "success": True,
                "results": [
                    entity_to_dict(entity) for entity in result.primary_results
                ],
                "context": result.assembled_context,
                "total_found": result.total_found,
                "search_time_ms": result.search_time_ms,
            }
        )

    except APIError:
        raise
    except Exception as e:
        logger.error(f"Knowledge search error: {e}")
        raise APIError("Internal server error", 500)


@api_v1.route("/search/incidents", methods=["POST"])
@require_permission("search", "read")
@handle_async
async def search_incidents():
    """インシデント検索"""
    try:
        data = request.get_json()

        if not data or "query" not in data:
            raise APIError("Query is required")

        result = await rag_manager.search_incidents(
            query=data["query"], severity=data.get("severity")
        )

        return jsonify(
            {
                "success": True,
                "results": [
                    entity_to_dict(entity) for entity in result.primary_results
                ],
                "context": result.assembled_context,
                "total_found": result.total_found,
                "search_time_ms": result.search_time_ms,
            }
        )

    except APIError:
        raise
    except Exception as e:
        logger.error(f"Incident search error: {e}")
        raise APIError("Internal server error", 500)


# ============================================
# 関係性管理API
# ============================================


@api_v1.route("/relationships", methods=["POST"])
@require_permission("relationships", "create")
def create_relationship():
    """関係性作成"""
    try:
        data = request.get_json()

        if not data:
            raise APIError("Request body is required")

        required_fields = ["source_id", "target_id", "relationship_type"]
        for field in required_fields:
            if field not in data:
                raise APIError(f"Field '{field}' is required")

        relationship = EntityRelationship(
            source_id=data["source_id"],
            target_id=data["target_id"],
            relationship_type=data["relationship_type"],
            weight=data.get("weight", 1.0),
            metadata=data.get("metadata", {}),
            created_by=getattr(request, "sage_type", "system"),
        )

        success = entity_manager.create_relationship(relationship)

        if not success:
            raise APIError("Failed to create relationship", 500)

        return (
            jsonify({"success": True, "message": "Relationship created successfully"}),
            201,
        )

    except APIError:
        raise
    except Exception as e:
        logger.error(f"Create relationship error: {e}")
        raise APIError("Internal server error", 500)


@api_v1.route("/relationships/<entity_id>", methods=["GET"])
@require_permission("relationships", "read")
def get_relationships(entity_id: str):
    """エンティティの関係性取得"""
    try:
        direction = request.args.get("direction", "both")

        relationships = entity_manager.get_relationships(entity_id, direction)

        relationship_data = []
        for rel in relationships:
            relationship_data.append(
                {
                    "source_id": rel.source_id,
                    "target_id": rel.target_id,
                    "relationship_type": rel.relationship_type,
                    "weight": rel.weight,
                    "metadata": rel.metadata,
                    "created_by": rel.created_by,
                }
            )

        return jsonify(
            {
                "success": True,
                "entity_id": entity_id,
                "direction": direction,
                "relationships": relationship_data,
                "count": len(relationship_data),
            }
        )

    except APIError:
        raise
    except Exception as e:
        logger.error(f"Get relationships error: {e}")
        raise APIError("Internal server error", 500)


# ============================================
# システム情報・分析API
# ============================================


@api_v1.route("/system/statistics", methods=["GET"])
@require_permission("analytics", "read")
def get_system_statistics():
    """システム統計取得"""
    try:
        entity_stats = entity_manager.get_statistics()
        search_analytics = rag_manager.get_search_analytics()

        return jsonify(
            {
                "success": True,
                "entity_statistics": entity_stats,
                "search_analytics": search_analytics,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except APIError:
        raise
    except Exception as e:
        logger.error(f"Get statistics error: {e}")
        raise APIError("Internal server error", 500)


@api_v1.route("/system/health", methods=["GET"])
def health_check():
    """ヘルスチェック"""
    try:
        # 基本的なヘルスチェック
        entity_count = len(entity_manager.list_entities(limit=1))

        return jsonify(
            {
                "success": True,
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "entity_manager": "ok",
                    "rag_manager": "ok",
                    "database": "ok",
                },
            }
        )

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            503,
        )


# ============================================
# エラーハンドリング
# ============================================


@api_v1.errorhandler(APIError)
def handle_api_error(error):
    """API例外ハンドラー"""
    return (
        jsonify(
            {
                "success": False,
                "error": {"message": error.message, "details": error.details},
                "timestamp": datetime.now().isoformat(),
            }
        ),
        error.status_code,
    )


@api_v1.errorhandler(404)
def handle_not_found(error):
    """404ハンドラー"""
    return (
        jsonify(
            {
                "success": False,
                "error": {"message": "Endpoint not found"},
                "timestamp": datetime.now().isoformat(),
            }
        ),
        404,
    )


@api_v1.errorhandler(500)
def handle_internal_error(error):
def handle_internal_error(error):
    """500ハンドラー"""
    logger.error(f"Internal server error: {error}")
            {
                "success": False,
                "error": {"message": "Internal server error"},
                "timestamp": datetime.now().isoformat(),
            }
        ),
        500,
    )

# ============================================
# アプリケーション設定
# ============================================
    return (
        jsonify(
app.register_blueprint(api_v1)


@app.route("/")
def index():
    """API情報"""
    return jsonify(
        {
            "name": "Elders Guild Unified API Gateway",
            "version": "1.0",
            "description": "統合エンティティ管理・検索API",
            "endpoints": {
                "entities": "/api/v1/entities",
                "search": "/api/v1/search/unified",
                "relationships": "/api/v1/relationships",
                "health": "/api/v1/system/health",
                "statistics": "/api/v1/system/statistics",
            },
            "documentation": "https://github.com/ai-company/unified-api-docs",
        }
    )


# ============================================
# 起動設定
# ============================================


def create_app(config=None):
    """アプリケーションファクトリー"""
    if config:
        app.config.update(config)

    return app


if __name__ == "__main__":
    # 開発サーバー起動
    logger.info("Starting Elders Guild Unified API Gateway...")
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
