"""
Test suite for DatabaseShaper (D08) - データベース設計・最適化専門家サーバント
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
from libs.elder_servants.dwarf_workshop.database_shaper import DatabaseShaper


class TestDatabaseShaperInitialization:
    """DatabaseShaper初期化テスト"""

    def test_database_shaper_initialization(self):
        """DatabaseShaper正常初期化テスト"""
        shaper = DatabaseShaper()

        assert shaper.servant_id == "D08"
        assert shaper.servant_name == "DatabaseShaper"
        assert shaper.specialization == "データベース設計・最適化"
        assert len(shaper.capabilities) == 6
        assert hasattr(shaper, "schema_designer")
        assert hasattr(shaper, "performance_optimizer")
        assert hasattr(shaper, "migration_generator")
        assert hasattr(shaper, "index_architect")

    def test_database_shaper_capabilities(self):
        """DatabaseShaper能力定義テスト"""
        shaper = DatabaseShaper()

        capability_names = [cap.name for cap in shaper.capabilities]
        expected_capabilities = [
            "design_database_schema",
            "optimize_database_performance",
            "generate_migrations",
            "design_indexing_strategy",
            "implement_data_partitioning",
            "generate_orm_models",
        ]

        for expected in expected_capabilities:
            assert expected in capability_names

    def test_specialized_capabilities(self):
        """専門能力テスト"""
        shaper = DatabaseShaper()
        specialized = shaper.get_specialized_capabilities()

        assert len(specialized) == 4
        specialized_names = [cap.name for cap in specialized]
        assert "design_data_warehouse" in specialized_names
        assert "implement_database_sharding" in specialized_names
        assert "generate_backup_strategy" in specialized_names
        assert "analyze_query_performance" in specialized_names

    def test_supported_databases(self):
        """サポートデータベーステスト"""
        shaper = DatabaseShaper()

        expected_databases = ["postgresql", "mysql", "sqlite", "mongodb", "redis"]
        for db in expected_databases:
            assert db in shaper.supported_databases

    def test_supported_orms(self):
        """サポートORMテスト"""
        shaper = DatabaseShaper()

        expected_orms = ["sqlalchemy", "django", "peewee", "tortoise", "mongoengine"]
        for orm in expected_orms:
            assert orm in shaper.supported_orms


class TestDatabaseSchemaDesign:
    """データベーススキーマ設計テスト"""

    @pytest.mark.asyncio
    async def test_design_database_schema_basic(self):
        """基本データベーススキーマ設計テスト"""
        shaper = DatabaseShaper()

        data_requirements = {
            "data_objects": [
                {
                    "name": "User",
                    "attributes": [
                        {"name": "name", "type": "string", "required": True},
                        {"name": "email", "type": "string", "required": True},
                        {"name": "age", "type": "integer", "required": False},
                    ],
                }
            ]
        }

        business_rules = [
            {"type": "uniqueness", "field": "email", "table": "User"},
            {"type": "validation", "field": "age", "rule": "age >= 0"},
        ]

        task = {
            "task_id": "test_schema_design",
            "task_type": "design_database_schema",
            "payload": {
                "data_requirements": data_requirements,
                "business_rules": business_rules,
            },
        }

        result = await shaper.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert "database_schema" in result.result_data
        assert result.result_data["table_count"] >= 1
        assert result.result_data["relationship_count"] >= 0

        schema = result.result_data["database_schema"]
        assert "entities" in schema
        assert "tables" in schema
        assert "constraints" in schema
        assert "recommended_indexes" in schema
        assert result.quality_score > 70

    @pytest.mark.asyncio
    async def test_design_complex_schema(self):
        """複雑スキーマ設計テスト"""
        shaper = DatabaseShaper()

        data_requirements = {
            "data_objects": [
                {"name": "User", "attributes": [{"name": "id", "type": "integer"}]},
                {
                    "name": "Order",
                    "attributes": [
                        {"name": "id", "type": "integer"},
                        {"name": "user_id", "type": "integer"},
                    ],
                },
                {
                    "name": "Product",
                    "attributes": [
                        {"name": "id", "type": "integer"},
                        {"name": "name", "type": "string"},
                    ],
                },
            ]
        }

        business_rules = [
            {"type": "foreign_key", "from": "Order.user_id", "to": "User.id"},
            {"type": "many_to_many", "table1": "Order", "table2": "Product"},
        ]

        task = {
            "task_id": "test_complex_schema",
            "task_type": "design_database_schema",
            "payload": {
                "data_requirements": data_requirements,
                "business_rules": business_rules,
            },
        }

        result = await shaper.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert result.result_data["table_count"] >= 3
        assert len(result.result_data["ddl_statements"]) > 0

    @pytest.mark.asyncio
    async def test_schema_design_empty_requirements(self):
        """空要件でのスキーマ設計テスト"""
        shaper = DatabaseShaper()

        task = {
            "task_id": "test_empty_schema",
            "task_type": "design_database_schema",
            "payload": {"data_requirements": {}, "business_rules": []},
        }

        result = await shaper.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert result.result_data["table_count"] == 0


class TestPerformanceOptimization:
    """パフォーマンス最適化テスト"""

    @pytest.mark.asyncio
    async def test_optimize_database_performance(self):
        """データベースパフォーマンス最適化テスト"""
        shaper = DatabaseShaper()

        existing_schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER"},
                        {"name": "email", "type": "VARCHAR(255)"},
                        {"name": "created_at", "type": "TIMESTAMP"},
                    ],
                    "estimated_rows": 1500000,  # 大きなテーブル
                }
            ]
        }

        query_patterns = [
            {
                "type": "SELECT",
                "tables": ["users"],
                "where_conditions": [{"column": "email", "operator": "="}],
                "frequency": "high",
            },
            {
                "type": "SELECT",
                "tables": ["users"],
                "where_conditions": [{"column": "created_at", "operator": "BETWEEN"}],
                "frequency": "medium",
            },
        ]

        task = {
            "task_id": "test_performance_opt",
            "task_type": "optimize_database_performance",
            "payload": {
                "existing_schema": existing_schema,
                "query_patterns": query_patterns,
            },
        }

        result = await shaper.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert "optimization_plan" in result.result_data
        assert result.result_data["strategies_count"] > 0

        plan = result.result_data["optimization_plan"]
        assert "analysis" in plan
        assert "bottlenecks" in plan
        assert "strategies" in plan
        assert "implementation_plan" in plan

    @pytest.mark.asyncio
    async def test_performance_bottleneck_detection(self):
        """パフォーマンスボトルネック検出テスト"""
        shaper = DatabaseShaper()

        existing_schema = {
            "tables": [
                {"name": "large_table", "estimated_rows": 5000000},  # 大きなテーブル
                {"name": "small_table", "estimated_rows": 1000},
            ]
        }

        query_patterns = [{"type": "SELECT", "execution_time_ms": 5000}]  # 遅いクエリ

        task = {
            "task_id": "test_bottleneck",
            "task_type": "optimize_database_performance",
            "payload": {
                "existing_schema": existing_schema,
                "query_patterns": query_patterns,
            },
        }

        result = await shaper.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        bottlenecks = result.result_data["optimization_plan"]["bottlenecks"]
        assert "large_tables" in bottlenecks
        assert "large_table" in bottlenecks["large_tables"]


class TestMigrationGeneration:
    """マイグレーション生成テスト"""

    @pytest.mark.asyncio
    async def test_generate_migrations_basic(self):
        """基本マイグレーション生成テスト"""
        shaper = DatabaseShaper()

        current_schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER"},
                        {"name": "name", "type": "VARCHAR(100)"},
                    ],
                }
            ]
        }

        target_schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER"},
                        {"name": "name", "type": "VARCHAR(100)"},
                        {"name": "email", "type": "VARCHAR(255)"},  # 新しいカラム
                    ],
                },
                {
                    "name": "orders",  # 新しいテーブル
                    "columns": [
                        {"name": "id", "type": "INTEGER"},
                        {"name": "user_id", "type": "INTEGER"},
                    ],
                },
            ]
        }

        task = {
            "task_id": "test_migration",
            "task_type": "generate_migrations",
            "payload": {
                "current_schema": current_schema,
                "target_schema": target_schema,
            },
        }

        result = await shaper.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert "migration_scripts" in result.result_data

        scripts = result.result_data["migration_scripts"]
        assert "forward_migrations" in scripts
        assert "rollback_migrations" in scripts
        assert "operations" in scripts
        assert len(scripts["operations"]) > 0

    @pytest.mark.asyncio
    async def test_complex_migration(self):
        """複雑マイグレーションテスト"""
        shaper = DatabaseShaper()

        current_schema = {
            "tables": [
                {"name": "old_table", "columns": [{"name": "id", "type": "INTEGER"}]}
            ]
        }

        target_schema = {
            "tables": [
                {"name": "new_table", "columns": [{"name": "id", "type": "INTEGER"}]}
            ]
        }

        task = {
            "task_id": "test_complex_migration",
            "task_type": "generate_migrations",
            "payload": {
                "current_schema": current_schema,
                "target_schema": target_schema,
            },
        }

        result = await shaper.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert "risk_assessment" in result.result_data
        assert "estimated_duration" in result.result_data


class TestIndexingStrategy:
    """インデックス戦略テスト"""

    @pytest.mark.asyncio
    async def test_design_indexing_strategy(self):
        """インデックス戦略設計テスト"""
        shaper = DatabaseShaper()

        table_schemas = [
            {
                "name": "users",
                "columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "email", "type": "VARCHAR(255)"},
                    {"name": "name", "type": "VARCHAR(100)"},
                    {"name": "created_at", "type": "TIMESTAMP"},
                ],
            }
        ]

        query_patterns = [
            {
                "tables": ["users"],
                "where_conditions": [{"column": "email"}],
                "frequency": "high",
            },
            {
                "tables": ["users"],
                "where_conditions": [{"column": "name"}, {"column": "created_at"}],
                "frequency": "medium",
            },
        ]

        task = {
            "task_id": "test_indexing",
            "task_type": "design_indexing_strategy",
            "payload": {
                "table_schemas": table_schemas,
                "query_patterns": query_patterns,
            },
        }

        result = await shaper.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert "indexing_plan" in result.result_data
        assert result.result_data["index_count"] > 0

        plan = result.result_data["indexing_plan"]
        assert "recommended_indexes" in plan
        assert "performance_impact" in plan
        assert "implementation_sql" in result.result_data

    @pytest.mark.asyncio
    async def test_index_optimization(self):
        """インデックス最適化テスト"""
        shaper = DatabaseShaper()

        table_schemas = [
            {
                "name": "large_table",
                "columns": [
                    {"name": "col1", "type": "INTEGER"},
                    {"name": "col2", "type": "VARCHAR(255)"},
                    {"name": "col3", "type": "TIMESTAMP"},
                ],
            }
        ]

        # 重複するクエリパターン
        query_patterns = [
            {"tables": ["large_table"], "where_conditions": [{"column": "col1"}]},
            {"tables": ["large_table"], "where_conditions": [{"column": "col1"}]},  # 重複
            {"tables": ["large_table"], "where_conditions": [{"column": "col2"}]},
        ]

        task = {
            "task_id": "test_index_optimization",
            "task_type": "design_indexing_strategy",
            "payload": {
                "table_schemas": table_schemas,
                "query_patterns": query_patterns,
            },
        }

        result = await shaper.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        # 重複が除去されているかチェック
        indexes = result.result_data["indexing_plan"]["recommended_indexes"]
        index_combinations = [(idx["table"], tuple(idx["columns"])) for idx in indexes]
        assert len(index_combinations) == len(set(index_combinations))


class TestDataPartitioning:
    """データパーティショニングテスト"""

    @pytest.mark.asyncio
    async def test_implement_data_partitioning(self):
        """データパーティショニング実装テスト"""
        shaper = DatabaseShaper()

        large_tables = [
            {
                "name": "transactions",
                "size_estimate": 10000000,  # 1000万件
                "columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "date", "type": "DATE"},
                    {"name": "amount", "type": "DECIMAL"},
                ],
            }
        ]

        partitioning_strategy = {
            "method": "range",
            "partition_key": "date",
            "partition_size": "monthly",
        }

        task = {
            "task_id": "test_partitioning",
            "task_type": "implement_data_partitioning",
            "payload": {
                "large_tables": large_tables,
                "partitioning_strategy": partitioning_strategy,
            },
        }

        result = await shaper.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert "partitioning_implementation" in result.result_data
        assert result.result_data["tables_partitioned"] == 1

        implementation = result.result_data["partitioning_implementation"]
        assert "table_implementations" in implementation
        assert "overall_plan" in implementation
        assert len(implementation["table_implementations"]) == 1


class TestORMModelGeneration:
    """ORMモデル生成テスト"""

    @pytest.mark.asyncio
    async def test_generate_sqlalchemy_models(self):
        """SQLAlchemyモデル生成テスト"""
        shaper = DatabaseShaper()

        database_schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {
                            "name": "id",
                            "type": "INTEGER",
                            "constraints": ["PRIMARY KEY"],
                        },
                        {
                            "name": "name",
                            "type": "VARCHAR(100)",
                            "constraints": ["NOT NULL"],
                        },
                        {
                            "name": "email",
                            "type": "VARCHAR(255)",
                            "constraints": ["UNIQUE"],
                        },
                    ],
                }
            ],
            "relationships": [{"type": "one_to_many", "from": "users", "to": "orders"}],
        }

        task = {
            "task_id": "test_orm_generation",
            "task_type": "generate_orm_models",
            "payload": {
                "database_schema": database_schema,
                "orm_framework": "sqlalchemy",
            },
        }

        result = await shaper.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert "orm_models" in result.result_data
        assert result.result_data["orm_framework"] == "sqlalchemy"
        assert result.result_data["model_count"] == 1

        models = result.result_data["orm_models"]
        assert "individual_models" in models
        assert "integrated_models" in models
        assert "relationships" in models
        assert len(models["individual_models"]) == 1

    @pytest.mark.asyncio
    async def test_generate_django_models(self):
        """Djangoモデル生成テスト"""
        shaper = DatabaseShaper()

        database_schema = {
            "tables": [
                {"name": "products", "columns": [{"name": "id", "type": "INTEGER"}]}
            ]
        }

        task = {
            "task_id": "test_django_orm",
            "task_type": "generate_orm_models",
            "payload": {"database_schema": database_schema, "orm_framework": "django"},
        }

        result = await shaper.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert result.result_data["orm_framework"] == "django"

    @pytest.mark.asyncio
    async def test_unsupported_orm_framework(self):
        """サポート外ORMフレームワークテスト"""
        shaper = DatabaseShaper()

        task = {
            "task_id": "test_unsupported_orm",
            "task_type": "generate_orm_models",
            "payload": {"database_schema": {}, "orm_framework": "unsupported_orm"},
        }

        result = await shaper.execute_task(task)

        assert result.status == TaskStatus.FAILED
        assert "Unsupported ORM framework" in result.error_message


class TestSpecializedCapabilities:
    """専門能力テスト"""

    @pytest.mark.asyncio
    async def test_design_data_warehouse(self):
        """データウェアハウス設計テスト"""
        shaper = DatabaseShaper()

        task = {
            "task_id": "test_warehouse",
            "task_type": "design_data_warehouse",
            "payload": {
                "business_requirements": {"type": "analytics"},
                "data_sources": ["sales_db", "inventory_db"],
            },
        }

        result = await shaper.execute_task(task)
        assert result.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_implement_database_sharding(self):
        """データベースシャーディング実装テスト"""
        shaper = DatabaseShaper()

        task = {
            "task_id": "test_sharding",
            "task_type": "implement_database_sharding",
            "payload": {
                "database_schema": {"tables": []},
                "sharding_strategy": {"method": "hash", "key": "user_id"},
            },
        }

        result = await shaper.execute_task(task)
        assert result.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_generate_backup_strategy(self):
        """バックアップ戦略生成テスト"""
        shaper = DatabaseShaper()

        task = {
            "task_id": "test_backup",
            "task_type": "generate_backup_strategy",
            "payload": {
                "database_config": {"engine": "postgresql"},
                "recovery_requirements": {"rto": "1hour", "rpo": "15min"},
            },
        }

        result = await shaper.execute_task(task)
        assert result.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_analyze_query_performance(self):
        """クエリパフォーマンス分析テスト"""
        shaper = DatabaseShaper()

        task = {
            "task_id": "test_query_analysis",
            "task_type": "analyze_query_performance",
            "payload": {
                "sql_queries": ["SELECT * FROM users WHERE email = ?"],
                "execution_plans": [{"cost": 100, "rows": 1000}],
            },
        }

        result = await shaper.execute_task(task)
        assert result.status == TaskStatus.COMPLETED


class TestCraftArtifact:
    """製作品作成テスト"""

    @pytest.mark.asyncio
    async def test_craft_schema_design(self):
        """スキーマ設計製作テスト"""
        shaper = DatabaseShaper()

        specification = {
            "type": "schema_design",
            "requirements": {"data_objects": []},
            "rules": [],
        }

        result = await shaper.craft_artifact(specification)

        assert "database_schema" in result

    @pytest.mark.asyncio
    async def test_craft_performance_optimization(self):
        """パフォーマンス最適化製作テスト"""
        shaper = DatabaseShaper()

        specification = {
            "type": "performance_optimization",
            "schema": {"tables": []},
            "queries": [],
        }

        result = await shaper.craft_artifact(specification)

        assert "optimization_plan" in result

    @pytest.mark.asyncio
    async def test_craft_indexing_strategy(self):
        """インデックス戦略製作テスト"""
        shaper = DatabaseShaper()

        specification = {"type": "indexing", "tables": [], "patterns": []}

        result = await shaper.craft_artifact(specification)

        assert "indexing_plan" in result


class TestQualityValidation:
    """品質検証テスト"""

    @pytest.mark.asyncio
    async def test_database_design_quality_validation(self):
        """データベース設計品質検証テスト"""
        shaper = DatabaseShaper()

        # 高品質な結果データ
        high_quality_result = {
            "database_schema": {"tables": []},
            "table_count": 5,
            "design_quality": {
                "normalization": 90,
                "consistency": 85,
                "performance": 88,
            },
            "strategies_count": 8,
            "index_count": 10,
            "implementation_complexity": "low",
        }

        quality_score = await shaper._validate_database_design_quality(
            high_quality_result
        )
        assert quality_score >= 85

        # 低品質な結果データ
        low_quality_result = {
            "error": "Failed to design database",
            "table_count": 0,
            "implementation_complexity": "very_high",
        }

        quality_score = await shaper._validate_database_design_quality(
            low_quality_result
        )
        assert quality_score < 50


class TestErrorHandling:
    """エラーハンドリングテスト"""

    @pytest.mark.asyncio
    async def test_unknown_task_type(self):
        """未知のタスクタイプテスト"""
        shaper = DatabaseShaper()

        task = {
            "task_id": "test_unknown",
            "task_type": "unknown_task_type",
            "payload": {},
        }

        result = await shaper.execute_task(task)

        assert result.status == TaskStatus.FAILED
        assert "Unknown task type" in result.error_message

    @pytest.mark.asyncio
    async def test_exception_handling(self):
        """例外処理テスト"""
        shaper = DatabaseShaper()

        # DatabaseShaperの内部メソッドにパッチを当てて例外を発生させる
        with patch.object(
            shaper, "_design_database_schema", side_effect=Exception("Test exception")
        ):
            task = {
                "task_id": "test_exception",
                "task_type": "design_database_schema",
                "payload": {"data_requirements": {}, "business_rules": []},
            }

            result = await shaper.execute_task(task)

            assert result.status == TaskStatus.FAILED
            assert "Test exception" in result.error_message
            assert result.quality_score == 0.0


class TestDwarfServantIntegration:
    """DwarfServant統合テスト"""

    def test_inherits_from_dwarf_servant(self):
        """DwarfServant継承テスト"""
        shaper = DatabaseShaper()

        from libs.elder_servants.base.specialized_servants import DwarfServant

        assert isinstance(shaper, DwarfServant)
        assert hasattr(shaper, "craft_artifact")
        assert hasattr(shaper, "validate_crafting_quality")

    @pytest.mark.asyncio
    async def test_elders_legacy_integration(self):
        """EldersLegacy統合テスト"""
        shaper = DatabaseShaper()

        # EldersLegacy基底クラスの機能をテスト
        assert hasattr(shaper, "process_request")
        assert hasattr(shaper, "validate_request")
        assert hasattr(shaper, "get_capabilities")

        # ヘルスチェック
        health_result = await shaper.health_check()
        assert health_result["status"] == "healthy"
        assert health_result["servant_id"] == "D08"


class TestHelperClasses:
    """ヘルパークラステスト"""

    def test_schema_designer(self):
        """スキーマ設計器テスト"""
        from libs.elder_servants.dwarf_workshop.database_shaper import SchemaDesigner

        designer = SchemaDesigner()

        # エンティティ分析
        requirements = {
            "data_objects": [
                {"name": "User", "attributes": [{"name": "id", "type": "integer"}]}
            ]
        }
        entities = designer.analyze_entities(requirements)
        assert len(entities) == 1
        assert entities[0]["name"] == "User"

        # テーブル設計
        entity = {"name": "User", "attributes": [{"name": "name", "type": "string"}]}
        table = designer.design_table(entity, [])
        assert table["name"] == "user"
        assert len(table["columns"]) >= 3  # id, name, timestamps

    def test_performance_optimizer(self):
        """パフォーマンス最適化器テスト"""
        from libs.elder_servants.dwarf_workshop.database_shaper import (
            PerformanceOptimizer,
        )

        optimizer = PerformanceOptimizer()

        # クエリ分析
        query_patterns = [{"type": "SELECT"}, {"type": "INSERT"}, {"type": "SELECT"}]
        analysis = optimizer.analyze_queries(query_patterns)
        assert analysis["total_queries"] == 3
        assert analysis["query_types"]["SELECT"] == 2
        assert analysis["query_types"]["INSERT"] == 1

    def test_migration_generator(self):
        """マイグレーション生成器テスト"""
        from libs.elder_servants.dwarf_workshop.database_shaper import (
            MigrationGenerator,
        )

        generator = MigrationGenerator()

        # スキーマ差分分析
        current = {"tables": [{"name": "users"}]}
        target = {"tables": [{"name": "users"}, {"name": "orders"}]}

        differences = generator.analyze_schema_differences(current, target)
        assert "table_changes" in differences
        assert len(differences["table_changes"]) >= 1

    def test_index_architect(self):
        """インデックスアーキテクトテスト"""
        from libs.elder_servants.dwarf_workshop.database_shaper import IndexArchitect

        architect = IndexArchitect()

        # クエリパターン分析
        query_patterns = [
            {"where_conditions": [{"column": "email"}]},
            {"where_conditions": [{"column": "name"}]},
        ]
        analysis = architect.analyze_query_patterns(query_patterns)
        assert "where_clauses" in analysis
        assert len(analysis["where_clauses"]) == 2

        # 単一カラムインデックス推奨
        table = {"name": "users"}
        queries = [{"where_conditions": [{"column": "email"}]}]
        indexes = architect.recommend_single_column_indexes(table, queries)
        assert len(indexes) == 1
        assert indexes[0]["columns"] == ["email"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
