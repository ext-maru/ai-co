"""
Test suite for APIArchitect (D07) - API設計・実装専門家サーバント
TDD準拠テスト - DwarfServant EldersLegacy統合検証
"""

import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from libs.elder_servants.base.elder_servant import (
    ServantCapability,
    TaskResult,
    TaskStatus,
)
from libs.elder_servants.dwarf_workshop.api_architect import APIArchitect


class TestAPIArchitectInitialization:
    """APIArchitect初期化テスト"""

    def test_api_architect_initialization(self):
        """APIArchitect正常初期化テスト"""
        architect = APIArchitect()

        assert architect.servant_id == "D07"
        assert architect.servant_name == "APIArchitect"
        assert architect.specialization == "API設計・実装"
        assert len(architect.capabilities) == 6
        assert hasattr(architect, "rest_designer")
        assert hasattr(architect, "graphql_designer")
        assert hasattr(architect, "openapi_generator")
        assert hasattr(architect, "auth_architect")

    def test_api_architect_capabilities(self):
        """APIArchitect能力定義テスト"""
        architect = APIArchitect()

        capability_names = [cap.name for cap in architect.capabilities]
        expected_capabilities = [
            "design_rest_api",
            "generate_openapi_spec",
            "implement_api_endpoints",
            "design_graphql_schema",
            "implement_authentication",
            "generate_api_documentation",
        ]

        for expected in expected_capabilities:
            assert expected in capability_names

    def test_specialized_capabilities(self):
        """専門能力テスト"""
        architect = APIArchitect()
        specialized = architect.get_specialized_capabilities()

        assert len(specialized) == 4
        specialized_names = [cap.name for cap in specialized]
        assert "design_websocket_api" in specialized_names
        assert "implement_api_versioning" in specialized_names
        assert "generate_sdk" in specialized_names
        assert "api_performance_optimization" in specialized_names


class TestRESTAPIDesign:
    """REST API設計テスト"""

    @pytest.mark.asyncio
    async def test_design_rest_api_basic(self):
        """基本REST API設計テスト"""
        architect = APIArchitect()

        api_spec = {
            "name": "UserAPI",
            "version": "1.0.0",
            "base_url": "/api/v1",
            "description": "User management API",
        }

        resource_definitions = [
            {
                "name": "User",
                "fields": ["id", "name", "email"],
                "operations": ["create", "read", "update", "delete"],
            }
        ]

        task = {
            "task_id": "test_rest_design",
            "task_type": "design_rest_api",
            "payload": {
                "api_spec": api_spec,
                "resource_definitions": resource_definitions,
            },
        }

        result = await architect.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert "api_design" in result.result_data
        assert result.result_data["endpoint_count"] > 0
        assert result.result_data["resource_count"] == 1
        assert "RESTful" in result.result_data["design_patterns"]
        assert result.quality_score > 80

    @pytest.mark.asyncio
    async def test_design_rest_api_multiple_resources(self):
        """複数リソースREST API設計テスト"""
        architect = APIArchitect()

        api_spec = {"name": "E-commerceAPI", "version": "2.0.0"}
        resource_definitions = [
            {"name": "Product", "fields": ["id", "name", "price"]},
            {"name": "Order", "fields": ["id", "customer_id", "total"]},
            {"name": "Customer", "fields": ["id", "name", "email"]},
        ]

        task = {
            "task_id": "test_multi_resource",
            "task_type": "design_rest_api",
            "payload": {
                "api_spec": api_spec,
                "resource_definitions": resource_definitions,
            },
        }

        result = await architect.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert result.result_data["resource_count"] == 3
        assert (
            result.result_data["endpoint_count"] >= 15
        )  # 5 endpoints per resource minimum

    @pytest.mark.asyncio
    async def test_rest_api_error_handling(self):
        """REST API設計エラーハンドリングテスト"""
        architect = APIArchitect()

        task = {
            "task_id": "test_error",
            "task_type": "design_rest_api",
            "payload": {},  # 空のペイロード
        }

        result = await architect.execute_task(task)

        # エラーでも基本的な設計は提供される
        assert result.status == TaskStatus.COMPLETED
        assert "api_design" in result.result_data


class TestOpenAPISpecGeneration:
    """OpenAPI仕様書生成テスト"""

    @pytest.mark.asyncio
    async def test_generate_openapi_spec_basic(self):
        """基本OpenAPI仕様書生成テスト"""
        architect = APIArchitect()

        api_design = {
            "name": "TestAPI",
            "version": "1.0.0",
            "base_url": "http://localhost:8000/api/v1",
            "models": [{"name": "User", "fields": [{"name": "id", "type": "integer"}]}],
        }

        endpoint_definitions = [
            {
                "path": "/users",
                "method": "GET",
                "operation": "list_users",
                "description": "List all users",
            }
        ]

        task = {
            "task_id": "test_openapi",
            "task_type": "generate_openapi_spec",
            "payload": {
                "api_design": api_design,
                "endpoint_definitions": endpoint_definitions,
            },
        }

        result = await architect.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert "openapi_specification" in result.result_data

        spec = result.result_data["openapi_specification"]
        assert spec["openapi"] == "3.0.3"
        assert spec["info"]["title"] == "TestAPI"
        assert "/users" in spec["paths"]
        assert result.result_data["paths_count"] == 1
        assert result.result_data["validation_status"] == "valid"

    @pytest.mark.asyncio
    async def test_openapi_with_security_schemes(self):
        """セキュリティスキーム付きOpenAPI生成テスト"""
        architect = APIArchitect()

        api_design = {
            "name": "SecureAPI",
            "version": "1.0.0",
            "security_requirements": ["jwt", "api_key"],
        }

        task = {
            "task_id": "test_secure_openapi",
            "task_type": "generate_openapi_spec",
            "payload": {"api_design": api_design, "endpoint_definitions": []},
        }

        result = await architect.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        spec = result.result_data["openapi_specification"]
        assert "securitySchemes" in spec["components"]


class TestAPIEndpointImplementation:
    """APIエンドポイント実装テスト"""

    @pytest.mark.asyncio
    async def test_implement_fastapi_endpoints(self):
        """FastAPIエンドポイント実装テスト"""
        architect = APIArchitect()

        api_spec = {
            "name": "UserAPI",
            "endpoints": [
                {"path": "/users", "method": "GET", "operation": "list_users"}
            ],
            "models": [{"name": "User", "fields": [{"name": "id", "type": "int"}]}],
        }

        task = {
            "task_id": "test_fastapi_impl",
            "task_type": "implement_api_endpoints",
            "payload": {"api_spec": api_spec, "framework_choice": "fastapi"},
        }

        result = await architect.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert "api_implementation" in result.result_data
        assert result.result_data["framework"] == "fastapi"
        assert result.result_data["endpoints_implemented"] == 1

        implementation = result.result_data["api_implementation"]
        assert "main_app" in implementation
        assert "models" in implementation
        assert "routes" in implementation

    @pytest.mark.asyncio
    async def test_unsupported_framework(self):
        """サポート外フレームワークテスト"""
        architect = APIArchitect()

        task = {
            "task_id": "test_unsupported",
            "task_type": "implement_api_endpoints",
            "payload": {"api_spec": {}, "framework_choice": "unsupported_framework"},
        }

        result = await architect.execute_task(task)

        assert result.status == TaskStatus.FAILED
        assert "Unsupported framework" in result.error_message


class TestGraphQLDesign:
    """GraphQL設計テスト"""

    @pytest.mark.asyncio
    async def test_design_graphql_schema(self):
        """GraphQLスキーマ設計テスト"""
        architect = APIArchitect()

        data_models = [
            {
                "name": "User",
                "fields": [
                    {"name": "id", "type": "ID", "required": True},
                    {"name": "name", "type": "String", "required": True},
                    {"name": "email", "type": "String", "required": False},
                ],
            }
        ]

        query_requirements = [
            {"name": "getUser", "return_type": "User"},
            {"name": "getUsers", "return_type": "[User]"},
        ]

        task = {
            "task_id": "test_graphql",
            "task_type": "design_graphql_schema",
            "payload": {
                "data_models": data_models,
                "query_requirements": query_requirements,
            },
        }

        result = await architect.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert "graphql_schema" in result.result_data

        schema = result.result_data["graphql_schema"]
        assert "schema_definition" in schema
        assert "resolvers" in schema
        assert schema["type_count"] == 1
        assert schema["query_count"] == 2
        assert result.result_data["implementation_framework"] == "graphene-python"


class TestAuthentication:
    """認証システムテスト"""

    @pytest.mark.asyncio
    async def test_implement_jwt_authentication(self):
        """JWT認証実装テスト"""
        architect = APIArchitect()

        auth_requirements = {
            "type": "jwt",
            "token_expiry": 3600,
            "refresh_enabled": True,
        }

        security_spec = {"secret_key_rotation": True, "algorithm": "HS256"}

        task = {
            "task_id": "test_jwt_auth",
            "task_type": "implement_authentication",
            "payload": {
                "auth_requirements": auth_requirements,
                "security_spec": security_spec,
            },
        }

        result = await architect.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert "auth_implementation" in result.result_data
        assert result.result_data["auth_type"] == "jwt"

        auth_impl = result.result_data["auth_implementation"]
        assert "authentication" in auth_impl
        assert "security_middleware" in auth_impl
        assert "user_management" in auth_impl
        assert "authorization" in auth_impl

    @pytest.mark.asyncio
    async def test_implement_oauth2_authentication(self):
        """OAuth2認証実装テスト"""
        architect = APIArchitect()

        task = {
            "task_id": "test_oauth2",
            "task_type": "implement_authentication",
            "payload": {
                "auth_requirements": {"type": "oauth2"},
                "security_spec": {"provider": "google"},
            },
        }

        result = await architect.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert result.result_data["auth_type"] == "oauth2"

    @pytest.mark.asyncio
    async def test_unsupported_auth_type(self):
        """サポート外認証タイプテスト"""
        architect = APIArchitect()

        task = {
            "task_id": "test_unsupported_auth",
            "task_type": "implement_authentication",
            "payload": {
                "auth_requirements": {"type": "unsupported_auth"},
                "security_spec": {},
            },
        }

        result = await architect.execute_task(task)

        assert result.status == TaskStatus.FAILED
        assert "Unsupported authentication type" in result.error_message


class TestAPIDocumentation:
    """APIドキュメント生成テスト"""

    @pytest.mark.asyncio
    async def test_generate_api_documentation(self):
        """APIドキュメント生成テスト"""
        architect = APIArchitect()

        api_code = """
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    return {"users": []}
"""

        specification = {
            "name": "UserAPI",
            "version": "1.0.0",
            "endpoints": [
                {"path": "/users", "method": "GET", "description": "Get all users"}
            ],
        }

        task = {
            "task_id": "test_docs",
            "task_type": "generate_api_documentation",
            "payload": {"api_code": api_code, "specification": specification},
        }

        result = await architect.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert "api_documentation" in result.result_data
        assert result.result_data["documentation_type"] == "comprehensive"

        docs = result.result_data["api_documentation"]
        assert "markdown" in docs
        assert "html" in docs
        assert "openapi" in docs
        assert len(result.result_data["formats_available"]) == 3


class TestCraftArtifact:
    """製作品作成テスト"""

    @pytest.mark.asyncio
    async def test_craft_rest_api(self):
        """REST API製作テスト"""
        architect = APIArchitect()

        specification = {
            "type": "rest_api",
            "api_spec": {"name": "TestAPI"},
            "resources": [{"name": "User"}],
        }

        result = await architect.craft_artifact(specification)

        assert "api_design" in result
        assert result["endpoint_count"] > 0

    @pytest.mark.asyncio
    async def test_craft_graphql_schema(self):
        """GraphQLスキーマ製作テスト"""
        architect = APIArchitect()

        specification = {
            "type": "graphql",
            "models": [{"name": "User"}],
            "queries": [{"name": "getUser"}],
        }

        result = await architect.craft_artifact(specification)

        assert "graphql_schema" in result

    @pytest.mark.asyncio
    async def test_craft_openapi_spec(self):
        """OpenAPI仕様製作テスト"""
        architect = APIArchitect()

        specification = {"type": "openapi", "design": {"name": "API"}, "endpoints": []}

        result = await architect.craft_artifact(specification)

        assert "openapi_specification" in result


class TestQualityValidation:
    """品質検証テスト"""

    @pytest.mark.asyncio
    async def test_api_architecture_quality_validation(self):
        """API設計品質検証テスト"""
        architect = APIArchitect()

        # 高品質な結果データ
        high_quality_result = {
            "api_design": {"endpoints": []},
            "endpoint_count": 10,
            "design_patterns": ["RESTful", "HATEOAS"],
            "api_implementation": {"main_app": "code"},
            "security_level": "high",
            "api_documentation": {"formats": ["markdown", "html"]},
            "formats_available": ["markdown", "html", "openapi"],
        }

        quality_score = await architect._validate_api_architecture_quality(
            high_quality_result
        )
        assert quality_score >= 85

        # 低品質な結果データ
        low_quality_result = {"error": "Failed to generate API", "endpoint_count": 0}

        quality_score = await architect._validate_api_architecture_quality(
            low_quality_result
        )
        assert quality_score < 50


class TestSpecializedCapabilities:
    """専門能力テスト"""

    @pytest.mark.asyncio
    async def test_websocket_api_design(self):
        """WebSocket API設計テスト"""
        architect = APIArchitect()

        task = {
            "task_id": "test_websocket",
            "task_type": "design_websocket_api",
            "payload": {
                "real_time_requirements": {"type": "chat"},
                "message_protocols": ["json"],
            },
        }

        result = await architect.execute_task(task)
        assert result.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_api_versioning(self):
        """APIバージョニングテスト"""
        architect = APIArchitect()

        task = {
            "task_id": "test_versioning",
            "task_type": "implement_api_versioning",
            "payload": {
                "existing_api": "# Existing API code",
                "version_strategy": "url",
            },
        }

        result = await architect.execute_task(task)
        assert result.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_sdk_generation(self):
        """SDK生成テスト"""
        architect = APIArchitect()

        task = {
            "task_id": "test_sdk",
            "task_type": "generate_sdk",
            "payload": {
                "api_specification": {"name": "TestAPI"},
                "target_languages": ["python", "javascript"],
            },
        }

        result = await architect.execute_task(task)
        assert result.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_api_performance_optimization(self):
        """APIパフォーマンス最適化テスト"""
        architect = APIArchitect()

        task = {
            "task_id": "test_perf_opt",
            "task_type": "api_performance_optimization",
            "payload": {
                "api_code": "# API code to optimize",
                "performance_requirements": {"response_time": "< 100ms"},
            },
        }

        result = await architect.execute_task(task)
        assert result.status == TaskStatus.COMPLETED


class TestErrorHandling:
    """エラーハンドリングテスト"""

    @pytest.mark.asyncio
    async def test_unknown_task_type(self):
        """未知のタスクタイプテスト"""
        architect = APIArchitect()

        task = {
            "task_id": "test_unknown",
            "task_type": "unknown_task_type",
            "payload": {},
        }

        result = await architect.execute_task(task)

        assert result.status == TaskStatus.FAILED
        assert "Unknown task type" in result.error_message

    @pytest.mark.asyncio
    async def test_exception_handling(self):
        """例外処理テスト"""
        architect = APIArchitect()

        # APIArchitectの内部メソッドにパッチを当てて例外を発生させる
        with patch.object(
            architect, "_design_rest_api", side_effect=Exception("Test exception")
        ):
            task = {
                "task_id": "test_exception",
                "task_type": "design_rest_api",
                "payload": {"api_spec": {}, "resource_definitions": []},
            }

            result = await architect.execute_task(task)

            assert result.status == TaskStatus.FAILED
            assert "Test exception" in result.error_message
            assert result.quality_score == 0.0


class TestDwarfServantIntegration:
    """DwarfServant統合テスト"""

    def test_inherits_from_dwarf_servant(self):
        """DwarfServant継承テスト"""
        architect = APIArchitect()

        from libs.elder_servants.base.specialized_servants import DwarfServant

        assert isinstance(architect, DwarfServant)
        assert hasattr(architect, "craft_artifact")
        assert hasattr(architect, "validate_crafting_quality")

    @pytest.mark.asyncio
    async def test_elders_legacy_integration(self):
        """EldersLegacy統合テスト"""
        architect = APIArchitect()

        # EldersLegacy基底クラスの機能をテスト
        assert hasattr(architect, "process_request")
        assert hasattr(architect, "validate_request")
        assert hasattr(architect, "get_capabilities")

        # ヘルスチェック
        health_result = await architect.health_check()
        assert health_result["status"] == "healthy"
        assert health_result["servant_id"] == "D07"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
