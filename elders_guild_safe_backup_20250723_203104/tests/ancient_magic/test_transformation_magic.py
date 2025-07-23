#!/usr/bin/env python3
"""
🔄 Transformation Magic テストスイート
====================================

Transformation Magic（変換魔法）の包括的なテストスイート。
データ変換、フォーマット変換、構造適応、統合ブリッジングをテスト。

Author: Claude Elder
Created: 2025-07-23
"""

import pytest
import asyncio
import json
import csv
import xml.etree.ElementTree as ET
import tempfile
import os
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
from io import StringIO
import time

# テスト対象をインポート
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ancient_magic.transformation_magic.transformation_magic import TransformationMagic


class TestTransformationMagic:


"""Transformation Magic テストクラス"""
        """Transformation Magic インスタンスを作成"""
        return TransformationMagic()
        
    @pytest.fixture
    def sample_tabular_data(self):

        """テスト用表形式データ""" ["id", "name", "age", "department", "salary"],
            "rows": [
                [1, "Alice Johnson", 28, "Engineering", 75000],
                [2, "Bob Smith", 34, "Marketing", 65000],
                [3, "Carol Davis", 29, "Engineering", 80000],
                [4, "David Wilson", 42, "Sales", 70000],
                [5, "Eve Brown", 31, "Engineering", 85000]
            ],
            "metadata": {
                "total_rows": 5,
                "created_at": "2025-07-23T10:00:00",
                "data_types": {
                    "id": "int",
                    "name": "str", 
                    "age": "int",
                    "department": "str",
                    "salary": "int"
                }
            }
        }
    
    @pytest.fixture
    def sample_nested_data(self):

                """テスト用ネストデータ""" {
                "name": "Elders Guild Corporation",
                "founded": 2025,
                "headquarters": {
                    "address": "123 Ancient Street",
                    "city": "Elder City",
                    "country": "Japan"
                },
                "departments": [
                    {
                        "name": "Four Sages Division",
                        "head": "Grand Elder Maru",
                        "members": [
                            {"name": "Knowledge Sage", "expertise": "wisdom"},
                            {"name": "Task Sage", "expertise": "execution"},
                            {"name": "Incident Sage", "expertise": "crisis"},
                            {"name": "RAG Sage", "expertise": "search"}
                        ]
                    },
                    {
                        "name": "Ancient Magic Division", 
                        "head": "Claude Elder",
                        "members": [
                            {"name": "Learning Magic", "type": "evolution"},
                            {"name": "Healing Magic", "type": "recovery"},
                            {"name": "Search Magic", "type": "exploration"},
                            {"name": "Storage Magic", "type": "persistence"}
                        ]
                    }
                ]
            }
        }
    
    @pytest.fixture
    def sample_time_series_data(self):

                        """テスト用時系列データ""" [
                "2025-07-23T08:00:00",
                "2025-07-23T09:00:00", 
                "2025-07-23T10:00:00",
                "2025-07-23T11:00:00",
                "2025-07-23T12:00:00"
            ],
            "metrics": {
                "cpu_usage": [0.45, 0.67, 0.89, 0.72, 0.56],
                "memory_usage": [0.62, 0.75, 0.88, 0.91, 0.68],
                "disk_io": [120, 340, 890, 650, 280],
                "network_io": [45, 89, 156, 203, 78]
            },
            "metadata": {
                "server": "elders-guild-01",
                "monitoring_interval": "1h",
                "data_points": 5
            }
        }
    
    # Phase 1: データ変換（Data Transformation） 
    async def test_tabular_data_transformation(self, transformation_magic, sample_tabular_data):

    """表形式データ変換テスト""" sample_tabular_data,
            "source_format": "dict",
            "target_format": "dataframe",
            "transformations": [
                {"type": "filter", "column": "department", "value": "Engineering"},
                {"type": "sort", "column": "salary", "order": "desc"},
                {"type": "compute", "column": "salary_category", "expression": "lambda x: 'high' if x['salary'] > 75000 else 'normal'"}
            ]
        }
        
        result = await transformation_magic.transform_data(transformation_params)
        
        assert result["success"] is True
        transformation_result = result["transformation_result"]
        
        # 変換結果の確認
        assert "transformed_data" in transformation_result
        assert "transformation_stats" in transformation_result
        
        # フィルタ結果確認（Engineeringのみ）
        stats = transformation_result["transformation_stats"]
        assert stats["filtered_rows"] == 3  # Alice, Carol, Eve
        assert stats["transformations_applied"] == 3
        
    async def test_nested_data_flattening(self, transformation_magic, sample_nested_data):

            """ネストデータ平坦化テスト""" sample_nested_data,
            "flatten_strategy": "dot_notation",
            "max_depth": 3,
            "preserve_arrays": True
        }
        
        result = await transformation_magic.flatten_data(flattening_params)
        
        assert result["success"] is True
        flattened_data = result["flattened_data"]
        
        # 平坦化の確認
        assert "organization.name" in flattened_data
        assert "organization.headquarters.city" in flattened_data
        assert flattened_data["organization.name"] == "Elders Guild Corporation"
        assert flattened_data["organization.headquarters.city"] == "Elder City"
        
        # 配列の保持確認
        assert "organization.departments" in flattened_data
        assert isinstance(flattened_data["organization.departments"], list)
        
    async def test_time_series_aggregation(self, transformation_magic, sample_time_series_data):

        """時系列データ集約テスト""" sample_time_series_data,
            "time_column": "timestamps",
            "value_columns": ["cpu_usage", "memory_usage"],
            "aggregation_functions": ["mean", "max", "min", "std"],
            "window_size": "2h"
        }
        
        result = await transformation_magic.aggregate_time_series(aggregation_params)
        
        assert result["success"] is True
        aggregation_result = result["aggregation_result"]
        
        # 集約結果の確認
        assert "aggregated_data" in aggregation_result
        assert "statistics" in aggregation_result
        
        stats = aggregation_result["statistics"]
        assert "cpu_usage_mean" in stats
        assert "memory_usage_max" in stats
        assert 0 <= stats["cpu_usage_mean"] <= 1
        
    async def test_data_pivoting(self, transformation_magic, sample_tabular_data):

        """データピボットテスト""" sample_tabular_data,
            "index_column": "department",
            "value_column": "salary",
            "aggfunc": "mean",
            "pivot_type": "simple"
        }
        
        result = await transformation_magic.pivot_data(pivot_params)
        
        assert result["success"] is True
        pivot_result = result["pivot_result"]
        
        # ピボット結果の確認  
        assert "pivoted_data" in pivot_result
        pivoted = pivot_result["pivoted_data"]
        
        # 部署別平均給与が計算されていることを確認
        assert "Engineering" in pivoted
        assert "Marketing" in pivoted
        assert "Sales" in pivoted
        
    # Phase 2: フォーマット変換（Format Conversion）
    async def test_json_to_xml_conversion(self, transformation_magic, sample_nested_data):

    """JSON → XML変換テスト""" sample_nested_data,
            "source_format": "json",
            "target_format": "xml",
            "xml_root": "organization_data",
            "pretty_format": True
        }
        
        result = await transformation_magic.convert_format(conversion_params)
        
        assert result["success"] is True
        conversion_result = result["conversion_result"]
        
        # XML変換の確認
        assert "converted_data" in conversion_result
        xml_data = conversion_result["converted_data"]
        
        # XML構造の基本確認
        assert xml_data.startswith("<?xml")
        assert "<organization_data>" in xml_data
        assert "<name>Elders Guild Corporation</name>" in xml_data
        
    async def test_csv_format_conversion(self, transformation_magic, sample_tabular_data):

        """CSV フォーマット変換テスト""" sample_tabular_data,
            "source_format": "dict",
            "target_format": "csv",
            "csv_options": {
                "delimiter": ",",
                "quoting": "minimal",
                "include_headers": True
            }
        }
        
        result = await transformation_magic.convert_format(conversion_params)
        
        assert result["success"] is True
        conversion_result = result["conversion_result"]
        
        # CSV変換の確認
        csv_data = conversion_result["converted_data"]
        lines = csv_data.strip().split('\n')
        
        # ヘッダー確認
        assert lines[0] == "id,name,age,department,salary"
        
        # データ行確認
        assert len(lines) == 6  # ヘッダー + 5データ行
        assert "Alice Johnson" in lines[1]
        
    async def test_yaml_format_conversion(self, transformation_magic):

            """YAML フォーマット変換テスト""" {
                "version": "2.0",
                "components": ["4_sages", "ancient_elder", "elder_servants"],
                "config": {
                    "debug": True,
                    "log_level": "INFO",
                    "max_workers": 8
                }
            }
        }
        
        conversion_params = {
            "data": yaml_test_data,
            "source_format": "dict",
            "target_format": "yaml",
            "yaml_options": {
                "default_flow_style": False,
                "indent": 2
            }
        }
        
        result = await transformation_magic.convert_format(conversion_params)
        
        assert result["success"] is True
        yaml_data = result["conversion_result"]["converted_data"]
        
        # YAML形式確認
        assert "elders_guild:" in yaml_data
        assert "version: '2.0'" in yaml_data or "version: 2.0" in yaml_data
        assert "components:" in yaml_data
        
    async def test_multi_format_round_trip(self, transformation_magic):

        
    """複数フォーマット往復変換テスト""" True,
            "data": {"number": 42, "text": "test"},
            "array": [1, 2, 3]
        }
        
        # JSON → YAML → JSON 往復変換
        formats = ["json", "yaml", "json"]
        current_data = original_data
        
        for i in range(len(formats) - 1):
            source_format = "dict" if i == 0 else formats[i]
            target_format = formats[i + 1]
            
            conversion_params = {
                "data": current_data,
                "source_format": source_format,
                "target_format": target_format
            }
            
            result = await transformation_magic.convert_format(conversion_params)
            assert result["success"] is True
            
            if target_format == "json":
                current_data = json.loads(result["conversion_result"]["converted_data"])
            else:
                current_data = result["conversion_result"]["converted_data"]
        
        # 往復変換後のデータ整合性確認
        assert current_data["test_round_trip"] is True
        assert current_data["data"]["number"] == 42
        assert current_data["array"] == [1, 2, 3]
        
    # Phase 3: 構造適応（Structure Adaptation）
    async def test_schema_validation(self, transformation_magic):

    """スキーマ検証テスト""" 12345,
            "username": "claude_elder",
            "email": "claude@elders-guild.ai",
            "age": 1,  # AI age in years
            "is_active": True,
            "roles": ["elder", "developer"],
            "profile": {
                "display_name": "Claude Elder",
                "bio": "Ancient Elder responsible for development execution"
            }
        }
        
        schema_definition = {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "minimum": 1},
                "username": {"type": "string", "pattern": "^[a-z_]+$"},
                "email": {"type": "string", "format": "email"},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
                "is_active": {"type": "boolean"},
                "roles": {"type": "array", "items": {"type": "string"}},
                "profile": {
                    "type": "object",
                    "properties": {
                        "display_name": {"type": "string"},
                        "bio": {"type": "string"}
                    },
                    "required": ["display_name"]
                }
            },
            "required": ["user_id", "username", "email"]
        }
        
        validation_params = {
            "data": test_data,
            "schema": schema_definition,
            "validation_strategy": "strict",
            "return_errors": True
        }
        
        result = await transformation_magic.validate_schema(validation_params)
        
        assert result["success"] is True
        validation_result = result["validation_result"]
        
        # 検証結果の確認
        assert validation_result["is_valid"] is True
        assert validation_result["error_count"] == 0
        assert "validated_data" in validation_result
        
    async def test_schema_migration(self, transformation_magic):

        """スキーママイグレーションテスト""" 1,
            "name": "Ancient Magic System",
            "version": "1.0",
            "components": ["learning", "healing"]
        }
        
        # 新バージョンへのマイグレーション定義
        migration_rules = {
            "version": "1.0_to_2.0",
            "transformations": [
                {"action": "rename", "from": "id", "to": "system_id"},
                {"action": "add", "field": "created_at", "value": "2025-07-23T10:00:00"},
                {"action": "transform", "field": "components", "function": "extend", "new_items": ["search", "storage"]},
                {"action": "update", "field": "version", "value": "2.0"}
            ]
        }
        
        migration_params = {
            "data": old_data,
            "migration_rules": migration_rules,
            "validate_result": True
        }
        
        result = await transformation_magic.migrate_schema(migration_params)
        
        assert result["success"] is True
        migration_result = result["migration_result"]
        
        # マイグレーション結果の確認
        migrated_data = migration_result["migrated_data"]
        assert "system_id" in migrated_data
        assert "id" not in migrated_data  # 旧フィールドは削除
        assert migrated_data["version"] == "2.0"
        assert "created_at" in migrated_data
        assert len(migrated_data["components"]) == 4
        
    async def test_data_normalization(self, transformation_magic):

        """データ正規化テスト""" [
                {
                    "order_id": 1,
                    "customer_name": "Alice Johnson",
                    "customer_email": "alice@example.com",
                    "product_name": "Ancient Magic License",
                    "product_price": 999.99,
                    "quantity": 1
                },
                {
                    "order_id": 2,
                    "customer_name": "Alice Johnson", 
                    "customer_email": "alice@example.com",
                    "product_name": "Elder Consultation",
                    "product_price": 499.99,
                    "quantity": 2
                }
            ]
        }
        
        normalization_params = {
            "data": denormalized_data,
            "normalization_level": "3nf",  # Third Normal Form
            "extract_entities": ["customers", "products", "orders"],
            "primary_keys": {
                "customers": "customer_id",
                "products": "product_id",
                "orders": "order_id"
            }
        }
        
        result = await transformation_magic.normalize_data(normalization_params)
        
        assert result["success"] is True
        normalized_result = result["normalization_result"]
        
        # 正規化結果の確認
        assert "normalized_data" in normalized_result
        normalized = normalized_result["normalized_data"]
        
        # 分離されたテーブルの確認
        assert "customers" in normalized
        assert "products" in normalized
        assert "orders" in normalized
        
        # 顧客の重複排除確認
        assert len(normalized["customers"]) == 1  # Alice Johnsonは1つ
        assert len(normalized["products"]) == 2   # 2つの異なる商品
        
    async def test_data_denormalization(self, transformation_magic):

            """データ非正規化テスト""" [
                {"customer_id": 1, "name": "Alice Johnson", "email": "alice@example.com"}
            ],
            "products": [
                {"product_id": 1, "name": "Ancient Magic License", "price": 999.99},
                {"product_id": 2, "name": "Elder Consultation", "price": 499.99}
            ],
            "orders": [
                {"order_id": 1, "customer_id": 1, "product_id": 1, "quantity": 1},
                {"order_id": 2, "customer_id": 1, "product_id": 2, "quantity": 2}
            ]
        }
        
        denormalization_params = {
            "data": normalized_data,
            "join_strategy": "left_join",
            "primary_table": "orders",
            "join_mappings": [
                {"table": "customers", "on": "customer_id"},
                {"table": "products", "on": "product_id"}
            ]
        }
        
        result = await transformation_magic.denormalize_data(denormalization_params)
        
        assert result["success"] is True  
        denormalized_result = result["denormalization_result"]
        
        # 非正規化結果の確認
        denormalized = denormalized_result["denormalized_data"]
        assert len(denormalized) == 2  # 2つの注文
        
        # 結合データの確認
        first_order = denormalized[0]
        assert "customer_name" in first_order
        assert "product_name" in first_order
        assert first_order["customer_name"] == "Alice Johnson"
        
    # Phase 4: 統合ブリッジング（Integration Bridging）
    async def test_rest_api_bridge(self, transformation_magic):

    """REST API ブリッジテスト""" "https://api.elders-guild.ai/v1",
            "endpoints": {
                "sages": "/sages",
                "magic": "/ancient-magic"
            },
            "authentication": {
                "type": "bearer",
                "token": "mock_token_12345"
            }
        }
        
        bridge_params = {
            "bridge_type": "rest_api",
            "config": api_config,
            "request": {
                "method": "GET",
                "endpoint": "sages",
                "params": {"status": "active"}
            },
            "response_transformation": {
                "extract_fields": ["id", "name", "status"],
                "rename_fields": {"id": "sage_id"}
            }
        }
        
        result = await transformation_magic.create_bridge(bridge_params)
        
        assert result["success"] is True
        bridge_result = result["bridge_result"]
        
        # ブリッジ設定の確認
        assert "bridge_id" in bridge_result
        assert bridge_result["bridge_type"] == "rest_api"
        assert "connection_status" in bridge_result
        
    async def test_graphql_bridge(self, transformation_magic):

            """GraphQL ブリッジテスト""" "https://api.elders-guild.ai/graphql",
            "schema_introspection": True,
            "query_fragments": {
                "sage_info": """
                fragment SageInfo on Sage {
                    id
                    name
                    expertise
                    status
                }
                """
            }
        }
        
        bridge_params = {
            "bridge_type": "graphql",
            "config": graphql_config,
            "query": """
            query GetActiveSages {
                sages(status: ACTIVE) {
                    ...SageInfo
                }
            }
            """,
            "variables": {},
            "response_transformation": {
                "extract_path": "data.sages",
                "map_fields": {
                    "expertise": "specialization"
                }
            }
        }
        
        result = await transformation_magic.create_bridge(bridge_params)
        
        assert result["success"] is True
        bridge_result = result["bridge_result"]
        
        # GraphQLブリッジの確認
        assert bridge_result["bridge_type"] == "graphql"
        assert "query_hash" in bridge_result
        
    async def test_database_bridge(self, transformation_magic):

                """データベースブリッジテスト""" "sqlite:///elders_guild.db",
            "tables": {
                "sages": {
                    "columns": ["id", "name", "expertise", "created_at"],
                    "primary_key": "id"
                },
                "ancient_magic": {
                    "columns": ["id", "name", "type", "sage_id"],
                    "foreign_keys": [{"column": "sage_id", "references": "sages.id"}]
                }
            }
        }
        
        bridge_params = {
            "bridge_type": "database",
            "config": db_config,
            "operations": [
                {
                    "type": "query",
                    "sql": "SELECT s.name as sage_name, am.name as magic_name FROM sages s JOIN ancient_magic am ON s.id = am.sage_id",
                    "result_format": "dict"
                }
            ]
        }
        
        result = await transformation_magic.create_bridge(bridge_params)
        
        assert result["success"] is True
        bridge_result = result["bridge_result"]
        
        # DBブリッジの確認
        assert bridge_result["bridge_type"] == "database"
        assert "connection_pool" in bridge_result
        
    async def test_webhook_bridge(self, transformation_magic):

                """Webhook ブリッジテスト""" "https://hooks.elders-guild.ai/incidents",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "X-Elder-Guild-Secret": "webhook_secret_key"
            },
            "payload_template": {
                "event_type": "incident_detected",
                "timestamp": "{{timestamp}}",
                "severity": "{{severity}}",
                "description": "{{description}}"
            }
        }
        
        bridge_params = {
            "bridge_type": "webhook",
            "config": webhook_config,
            "trigger_conditions": [
                {"field": "severity", "operator": ">=", "value": "high"}
            ],
            "transformation_rules": [
                {"field": "timestamp", "format": "iso8601"},
                {"field": "description", "max_length": 500}
            ]
        }
        
        result = await transformation_magic.create_bridge(bridge_params)
        
        assert result["success"] is True
        bridge_result = result["bridge_result"]
        
        # Webhookブリッジの確認
        assert bridge_result["bridge_type"] == "webhook"
        assert "webhook_url" in bridge_result
        
    # Phase 5: パフォーマンス・エラーハンドリング
    async def test_large_data_transformation(self, transformation_magic):

    """大規模データ変換テスト""" ["id", "timestamp", "value", "category"],
            "rows": []
        }
        
        for i in range(10000):
            large_data["rows"].append([
                i,
                f"2025-07-23T{i % 24:02d}:{(i * 3) % 60:02d}:00",
                (i * 7) % 1000,
                f"category_{i % 10}"
            ])
        
        transformation_params = {
            "data": large_data,
            "source_format": "dict",
            "target_format": "dataframe",
            "transformations": [
                {"type": "filter", "column": "value", "operator": ">", "value": 500},
                {"type": "group_by", "column": "category", "agg": {"value": "mean"}},
                {"type": "sort", "column": "value_mean", "order": "desc"}
            ],
            "performance_mode": "high_memory"
        }
        
        start_time = time.time()
        result = await transformation_magic.transform_data(transformation_params)
        execution_time = time.time() - start_time
        
        assert result["success"] is True
        transformation_result = result["transformation_result"]
        
        # パフォーマンス確認
        assert execution_time < 5.0  # 5秒以内
        assert transformation_result["execution_time"] < 5.0
        assert transformation_result["memory_usage_mb"] > 0
        
    async def test_transformation_magic_invalid_intent(self, transformation_magic):

        """無効な意図での魔法発動テスト"""
        """無効なフォーマット変換テスト"""
        conversion_params = {
            "data": {"test": "data"},
            "source_format": "json",
            "target_format": "invalid_format"
        }
        
        result = await transformation_magic.convert_format(conversion_params)
        
        assert result["success"] is False
        assert "unsupported" in result["error"].lower() or "invalid" in result["error"].lower()
        
    async def test_schema_validation_failure(self, transformation_magic):

        """スキーマ検証失敗テスト""" "not_a_number",  # 型エラー
            "email": "invalid-email",    # フォーマットエラー
            "age": -5                    # 範囲エラー
        }
        
        schema_definition = {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "minimum": 1},
                "email": {"type": "string", "format": "email"},
                "age": {"type": "integer", "minimum": 0, "maximum": 150}
            },
            "required": ["user_id", "email", "age"]
        }
        
        validation_params = {
            "data": invalid_data,
            "schema": schema_definition,
            "validation_strategy": "strict"
        }
        
        result = await transformation_magic.validate_schema(validation_params)
        
        assert result["success"] is True  # 検証処理自体は成功
        validation_result = result["validation_result"]
        
        # 検証エラーの確認
        assert validation_result["is_valid"] is False
        assert validation_result["error_count"] > 0
        assert len(validation_result["errors"]) >= 3
        
    async def test_concurrent_transformations(self, transformation_magic):

        """並行変換処理テスト"""
            dataset = {
                "headers": ["id", "value"],
                "rows": [[j, j * (i + 1)] for j in range(100)]
            }
            test_datasets.append(dataset)
        
        # 並行変換タスク作成
        tasks = []
        for i, dataset in enumerate(test_datasets):
            transformation_params = {
                "data": dataset,
                "source_format": "dict",
                "target_format": "dataframe",
                "transformations": [
                    {"type": "compute", "column": "doubled", "expression": "lambda x: x['value'] * 2"}
                ]
            }
            task = transformation_magic.transform_data(transformation_params)
            tasks.append(task)
        
        # 並行実行
        results = await asyncio.gather(*tasks)
        
        # すべての変換が成功することを確認
        assert len(results) == 5
        for result in results:
            assert result["success"] is True
            assert "transformation_result" in result


@pytest.mark.asyncio  
class TestTransformationMagicIntegration:

            """Transformation Magic統合テスト"""
        """包括的変換ワークフローテスト"""
        transformation_magic = TransformationMagic()
        
        # Step 1: 生データ（JSON形式）
        raw_data = {
            "sales_data": [
                {"date": "2025-07-01", "product": "Ancient Magic License", "amount": 999.99, "region": "Asia"},
                {"date": "2025-07-02", "product": "Elder Consultation", "amount": 499.99, "region": "Europe"},
                {"date": "2025-07-03", "product": "Ancient Magic License", "amount": 999.99, "region": "Americas"},
                {"date": "2025-07-04", "product": "Four Sages Training", "amount": 1999.99, "region": "Asia"}
            ]
        }
        
        # Step 2: データ変換（集約）
        transformation_params = {
            "data": raw_data["sales_data"],
            "source_format": "list",
            "target_format": "dataframe",
            "transformations": [
                {"type": "group_by", "column": "region", "agg": {"amount": "sum"}},
                {"type": "sort", "column": "amount_sum", "order": "desc"}
            ]
        }
        
        transform_result = await transformation_magic.transform_data(transformation_params)
        assert transform_result["success"] is True
        
        # Step 3: フォーマット変換（DataFrame → CSV）
        aggregated_data = transform_result["transformation_result"]["transformed_data"]
        
        csv_conversion_params = {
            "data": aggregated_data,
            "source_format": "dataframe", 
            "target_format": "csv",
            "csv_options": {"include_headers": True}
        }
        
        csv_result = await transformation_magic.convert_format(csv_conversion_params)
        assert csv_result["success"] is True
        
        # Step 4: スキーマ検証
        validation_schema = {
            "type": "object",
            "properties": {
                "region": {"type": "string"},
                "amount_sum": {"type": "number", "minimum": 0}
            }
        }
        
        # CSVをJSONに戻して検証
        csv_data = csv_result["conversion_result"]["converted_data"]
        assert "region,amount_sum" in csv_data
        assert len(csv_data.split('\n')) >= 4  # ヘッダー + 3地域
    
    async def test_multi_format_data_pipeline(self):

            """複数フォーマット データパイプラインテスト""" JSON → XML → YAML → JSON
        original_data = {
            "elders_guild": {
                "version": "2.0",
                "active_sages": 4,
                "ancient_magics": ["learning", "healing", "search", "storage"]
            }
        }
        
        pipeline_steps = [
            {"source": "dict", "target": "xml"},
            {"source": "xml", "target": "yaml"},
            {"source": "yaml", "target": "json"}
        ]
        
        current_data = original_data
        
        for step in pipeline_steps:
            conversion_params = {
                "data": current_data,
                "source_format": step["source"],
                "target_format": step["target"]
            }
            
            result = await transformation_magic.convert_format(conversion_params)
            assert result["success"] is True
            
            # 次のステップ用にデータ更新
            current_data = result["conversion_result"]["converted_data"]
        
        # 最終結果をJSONとしてパース
        final_data = json.loads(current_data)
        
        # データ整合性確認
        assert final_data["elders_guild"]["version"] == "2.0"
        assert final_data["elders_guild"]["active_sages"] == 4
        assert len(final_data["elders_guild"]["ancient_magics"]) == 4


if __name__ == "__main__":
    pytest.main(["-v", __file__])