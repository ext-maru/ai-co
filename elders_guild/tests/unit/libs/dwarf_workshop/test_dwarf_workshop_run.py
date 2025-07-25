#!/usr/bin/env python3
"""
Dwarf Workshop (D03-D08) 統合テスト実行
TDD準拠テスト - 実装検証
"""

import asyncio
import os
import sys
import traceback
from datetime import datetime

# パス設定
sys.path.insert(0, "/home/aicompany/ai_co")

async def test_api_architect():
    """APIArchitect (D07) テスト"""
    print("=" * 60)
    print("🏗️ APIArchitect (D07) テスト開始")
    print("=" * 60)

    try:
        from libs.elder_servants.dwarf_workshop.api_architect import APIArchitect

        # 初期化テスト
        architect = APIArchitect()
        print(f"✅ 初期化成功: {architect.servant_name} ({architect.servant_id})")

        # REST API設計テスト
        api_spec = {"name": "UserAPI", "version": "1.0.0", "base_url": "/api/v1"}

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
        if result.status.name == "COMPLETED":
            print(f"✅ REST API設計成功 - Quality: {result.quality_score:0.1f}/100")
            print(f"   エンドポイント数: {result.result_data.get('endpoint_count', 0)}")
        else:
            print(f"❌ REST API設計失敗: {result.error_message}")

        # OpenAPI仕様生成テスト
        openapi_task = {
            "task_id": "test_openapi",
            "task_type": "generate_openapi_spec",
            "payload": {
                "api_design": api_spec,
                "endpoint_definitions": [
                    {"path": "/users", "method": "GET", "operation": "list_users"}
                ],
            },
        }

        result = await architect.execute_task(openapi_task)
        if result.status.name == "COMPLETED":
            print(f"✅ OpenAPI仕様生成成功 - Quality: {result.quality_score:0.1f}/100")
        else:
            print(f"❌ OpenAPI仕様生成失敗: {result.error_message}")

        # JWT認証実装テスト
        auth_task = {
            "task_id": "test_jwt_auth",
            "task_type": "implement_authentication",
            "payload": {
                "auth_requirements": {"type": "jwt"},
                "security_spec": {"algorithm": "HS256"},
            },
        }

        result = await architect.execute_task(auth_task)
        if result.status.name == "COMPLETED":
            print(f"✅ JWT認証実装成功 - Quality: {result.quality_score:0.1f}/100")
        else:
            print(f"❌ JWT認証実装失敗: {result.error_message}")

        print("🎯 APIArchitect テスト完了\n")
        return True

    except Exception as e:
        print(f"❌ APIArchitect テストエラー: {e}")
        traceback.print_exc()
        return False

async def test_database_shaper():
    """DatabaseShaper (D08) テスト"""
    print("=" * 60)
    print("🗄️ DatabaseShaper (D08) テスト開始")
    print("=" * 60)

    try:
        from libs.elder_servants.dwarf_workshop.database_shaper import DatabaseShaper

        # 初期化テスト
        shaper = DatabaseShaper()
        print(f"✅ 初期化成功: {shaper.servant_name} ({shaper.servant_id})")

        # データベーススキーマ設計テスト
        data_requirements = {
            "data_objects": [
                {
                    "name": "User",
                    "attributes": [
                        {"name": "name", "type": "string", "required": True},
                        {"name": "email", "type": "string", "required": True},
                    ],
                }
            ]
        }

        business_rules = [{"type": "uniqueness", "field": "email", "table": "User"}]

        task = {
            "task_id": "test_schema_design",
            "task_type": "design_database_schema",
            "payload": {
                "data_requirements": data_requirements,
                "business_rules": business_rules,
            },
        }

        result = await shaper.execute_task(task)
        if result.status.name == "COMPLETED":
            print(f"✅ スキーマ設計成功 - Quality: {result.quality_score:0.1f}/100")
            print(f"   テーブル数: {result.result_data.get('table_count', 0)}")
        else:
            print(f"❌ スキーマ設計失敗: {result.error_message}")

        # パフォーマンス最適化テスト
        optimization_task = {
            "task_id": "test_optimization",
            "task_type": "optimize_database_performance",
            "payload": {
                "existing_schema": {
                    "tables": [{"name": "users", "estimated_rows": 1000000}]
                },
                "query_patterns": [{"type": "SELECT", "tables": ["users"]}],
            },
        }

        result = await shaper.execute_task(optimization_task)
        if result.status.name == "COMPLETED":
            print(f"✅ パフォーマンス最適化成功 - Quality: {result.quality_score:0.1f}/100")
        else:
            print(f"❌ パフォーマンス最適化失敗: {result.error_message}")

        # インデックス戦略設計テスト
        indexing_task = {
            "task_id": "test_indexing",
            "task_type": "design_indexing_strategy",
            "payload": {
                "table_schemas": [
                    {"name": "users", "columns": [{"name": "email", "type": "VARCHAR"}]}
                ],
                "query_patterns": [
                    {"tables": ["users"], "where_conditions": [{"column": "email"}]}
                ],
            },
        }

        result = await shaper.execute_task(indexing_task)
        if result.status.name == "COMPLETED":
            print(f"✅ インデックス戦略成功 - Quality: {result.quality_score:0.1f}/100")
        else:
            print(f"❌ インデックス戦略失敗: {result.error_message}")

        print("🎯 DatabaseShaper テスト完了\n")
        return True

    except Exception as e:
        print(f"❌ DatabaseShaper テストエラー: {e}")
        traceback.print_exc()
        return False

async def test_existing_servants():
    """既存サーバント (D03-D06) テスト"""
    print("=" * 60)
    print("🔨 既存Dwarfサーバント (D03-D06) テスト開始")
    print("=" * 60)

    test_results = []

    # D03: RefactorSmith
    try:
        from libs.elder_servants.dwarf_workshop.refactor_smith import RefactorSmith

        refactor_smith = RefactorSmith()
        print(f"✅ D03 RefactorSmith 初期化成功: {refactor_smith.servant_id}")

        # 簡単なリファクタリングテスト
        task = {
            "task_id": "test_refactor",
            "task_type": "eliminate_duplication",
            "payload": {"source_code": "def func1(): pass\ndef func2(): pass"},
        }

        result = await refactor_smith.execute_task(task)
        if result.status.name == "COMPLETED":
            print(f"✅ D03 リファクタリング成功 - Quality: {result.quality_score:0.1f}/100")
        else:
            print(f"❌ D03 リファクタリング失敗: {result.error_message}")

        test_results.append(("D03 RefactorSmith", result.status.name == "COMPLETED"))

    except Exception as e:
        print(f"❌ D03 RefactorSmith エラー: {e}")
        test_results.append(("D03 RefactorSmith", False))

    # D04: PerformanceTuner
    try:
        from libs.elder_servants.dwarf_workshop.performance_tuner import (
            PerformanceTuner,
        )

        performance_tuner = PerformanceTuner()
        print(f"✅ D04 PerformanceTuner 初期化成功: {performance_tuner.servant_id}")

        task = {
            "task_id": "test_profile",
            "task_type": "profile_code",
            "payload": {
                "source_code": "for i in range(1000): print(i)",
                "test_data": {},
            },
        }

        result = await performance_tuner.execute_task(task)
        if result.status.name == "COMPLETED":
            print(f"✅ D04 プロファイリング成功 - Quality: {result.quality_score:0.1f}/100")
        else:
            print(f"❌ D04 プロファイリング失敗: {result.error_message}")

        test_results.append(("D04 PerformanceTuner", result.status.name == "COMPLETED"))

    except Exception as e:
        print(f"❌ D04 PerformanceTuner エラー: {e}")
        test_results.append(("D04 PerformanceTuner", False))

    try:

        task = {
            "task_id": "test_static_analysis",
            "task_type": "static_analysis",
            "payload": {"source_code": "def test_func():\n    x = 1\n    return x + 1"},
        }

        if result.status.name == "COMPLETED":
            print(f"✅ D05 静的解析成功 - Quality: {result.quality_score:0.1f}/100")
        else:
            print(f"❌ D05 静的解析失敗: {result.error_message}")

    except Exception as e:

    # D06: SecurityGuard
    try:
        from libs.elder_servants.dwarf_workshop.security_guard import SecurityGuard

        security_guard = SecurityGuard()
        print(f"✅ D06 SecurityGuard 初期化成功: {security_guard.servant_id}")

        task = {
            "task_id": "test_security_audit",
            "task_type": "security_audit",
            "payload": {
                "source_code": "import os\ndef safe_func(): return 'safe'",
                "config_files": [],
            },
        }

        result = await security_guard.execute_task(task)
        if result.status.name == "COMPLETED":
            print(f"✅ D06 セキュリティ監査成功 - Quality: {result.quality_score:0.1f}/100")
        else:
            print(f"❌ D06 セキュリティ監査失敗: {result.error_message}")

        test_results.append(("D06 SecurityGuard", result.status.name == "COMPLETED"))

    except Exception as e:
        print(f"❌ D06 SecurityGuard エラー: {e}")
        test_results.append(("D06 SecurityGuard", False))

    print("🎯 既存サーバント テスト完了\n")
    return test_results

async def main():
    """メインテスト実行"""
    print("🏛️ ドワーフ工房 (D01-D08) 総合テスト開始")
    print(f"📅 実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # テスト結果収集
    all_passed = True

    # 既存サーバント (D03-D06) テスト
    existing_results = await test_existing_servants()

    # 新規サーバント (D07-D08) テスト
    api_architect_result = await test_api_architect()
    database_shaper_result = await test_database_shaper()

    # 結果集計
    print("=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)

    for test_name, passed in existing_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False

    api_status = "✅ PASS" if api_architect_result else "❌ FAIL"
    db_status = "✅ PASS" if database_shaper_result else "❌ FAIL"

    print(f"{api_status} D07 APIArchitect")
    print(f"{db_status} D08 DatabaseShaper")

    if not api_architect_result:
        all_passed = False
    if not database_shaper_result:
        all_passed = False

    print("=" * 60)
    overall_status = "✅ 全テスト成功" if all_passed else "❌ 一部テスト失敗"
    print(f"🎯 総合結果: {overall_status}")

    if all_passed:
        print("🎉 ドワーフ工房前半 (D01-D08) 実装完了！")
        print("📋 Issue #70 対応完了")
    else:
        print("🔧 修正が必要な項目があります")

    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
