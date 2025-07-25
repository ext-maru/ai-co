"""
エルダーサーバントシステム総合テスト
EldersLegacy統合後の動作確認
"""

import asyncio
import sys
sys.path.append('/home/aicompany/ai_co')

from elders_guild.elder_tree.elder_servants.base.elder_servant import (
    ServantRegistry, ServantCategory, TaskStatus, TaskPriority,
    ServantRequest, ServantResponse, servant_registry
)
from elders_guild.elder_tree.elder_servants.dwarf_workshop.code_crafter import CodeCrafter
from elders_guild.elder_tree.elder_servants.dwarf_workshop.test_forge import TestForge


async def test_elders_legacy_integration()print("=== EldersLegacy統合テスト ===")
"""EldersLegacy統合テスト"""
    
    # CodeCrafterインスタンス作成
    code_crafter = CodeCrafter()
    print(f"✓ CodeCrafter作成: {code_crafter}")
    
    # EldersServiceLegacy継承確認
    print(f"✓ EldersServiceLegacy継承: {hasattr(code_crafter, 'process_request')}")
    print(f"✓ Iron Will準拠: {hasattr(code_crafter, 'quality_threshold')}")
    print(f"✓ 品質基準: {code_crafter.quality_threshold}%")
    
    # 統一リクエスト形式でのテスト
    request = ServantRequest(
        task_id="legacy_test_001",
        task_type="generate_function",
        priority=TaskPriority.HIGH,
        payload={
            "spec": {
                "name": "greet_user",
                "parameters": [{"name": "name", "type": "str"}],
                "return_type": "str",
                "docstring": "Greet a user by name",
                "body": "return f'Hello, {name}!'"
            }
        }
    )
    
    response = await code_crafter.process_request(request)
    print(f"✓ 統一リクエスト処理: {response.status.value}")
    print(f"✓ 品質スコア: {response.quality_score}")
    print(f"✓ 実行時間: {response.execution_time_ms:0.2f}ms")
    
    assert response.status == TaskStatus.COMPLETED
    assert response.quality_score >= 95.0
    
    print("\nEldersLegacy統合テスト: 成功")


async def test_servant_registry_updated()print("\n=== 更新サーバントレジストリテスト ===")
"""更新されたサーバントレジストリのテスト"""
    
    # 新しいレジストリ作成
    registry = ServantRegistry()
    
    # 両方のサーバント登録
    code_crafter = CodeCrafter()
    test_forge = TestForge()
    
    registry.register_servant(code_crafter)
    registry.register_servant(test_forge)
    
    print(f"✓ 登録サーバント数: {len(registry.servants)}")
    print(f"✓ ドワーフカテゴリ: {len(registry.get_servants_by_category(ServantCategory.DWARF))}体")
    
    # 統一リクエスト形式でのタスク実行
    func_request = ServantRequest(
        task_id="registry_test_001",
        task_type="generate_function",
        priority=TaskPriority.MEDIUM,
        payload={
            "spec": {
                "name": "calculate_sum",
                "parameters": [{"name": "numbers", "type": "List[int]"}],
                "return_type": "int",
                "body": "return sum(numbers)"
            }
        }
    )
    
    # CodeCrafterで実行
    best_servant = registry.find_best_servant_for_task({
        "type": "code_generation",
        "required_capability": "Python実装"
    })
    
    assert best_servant is not None
    assert best_servant.servant_id == "D01"
    
    response = await best_servant.process_request(func_request)
    print(f"✓ 関数生成テスト: {response.status.value}, quality={response.quality_score}")
    
    # TestForgeでテスト生成
    test_request = ServantRequest(
        task_id="registry_test_002", 
        task_type="generate_unit_tests",
        priority=TaskPriority.HIGH,
        payload={
            "spec": {
                "source_code": response.result_data.get("code", ""),
                "framework": "pytest"
            }
        }
    )
    
    test_response = await test_forge.process_request(test_request)
    print(f"✓ テスト生成: {test_response.status.value}, quality={test_response.quality_score}")
    
    print("\n更新サーバントレジストリテスト: 成功")


async def test_iron_will_compliance()print("\n=== Iron Will品質基準準拠テスト ===")
"""Iron Will品質基準準拠テスト"""
    
    test_forge = TestForge()
    
    # 高品質タスク実行
    high_quality_request = ServantRequest(
        task_id="iron_will_001",
        task_type="generate_unit_tests",
        priority=TaskPriority.CRITICAL,
        payload={
            "spec": {
                "source_code": '''
def fibonacci(n):
    """Calculate fibonacci number"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class Calculator:
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b
''',
                "framework": "pytest",
                "coverage_target": 95.0
            }
        }
    )
    
    response = await test_forge.process_request(high_quality_request)
    
    print(f"✓ Iron Will基準チェック: {response.quality_score >}")
    print(f"✓ 品質スコア: {response.quality_score}")
    print(f"✓ タスクステータス: {response.status.value}")
    
    # Iron Will基準を満たしているか確認
    assert response.quality_score >= 95.0, f"Iron Will基準未達: {response.quality_score}%"
    
    # 生成されたテストコードの品質確認
    if response.status == TaskStatus.COMPLETED:
        test_code = response.result_data.get("test_code", "")
        assert "import pytest" in test_code
        assert "def test_" in test_code
        assert response.result_data.get("test_count", 0) > 0
        
        print(f"✓ テストコード行数: {len(test_code.splitlines())}")
        print(f"✓ 生成テスト数: {response.result_data.get('test_count', 0)}")
        print(f"✓ 推定カバレッジ: {response.result_data.get('estimated_coverage', 0)}%")
    
    print("\nIron Will品質基準準拠テスト: 成功")


async def test_error_handling_robustness()print("\n=== エラーハンドリング堅牢性テスト ===")
"""エラーハンドリング堅牢性テスト"""
    
    code_crafter = CodeCrafter()
    
    # 不正なリクエスト
    invalid_request = ServantRequest(
        task_id="error_test_001",
        task_type="invalid_task_type",
        priority=TaskPriority.LOW,
        payload={}
    )
    
    response = await code_crafter.process_request(invalid_request)
    
    print(f"✓ 不正タスク処理: {response.status.value}")
    print(f"✓ エラーメッセージ: {response.error_message}")
    
    assert response.status == TaskStatus.FAILED
    assert response.error_message is not None
    assert response.quality_score == 0.0
    
    # 空のペイロード
    empty_request = ServantRequest(
        task_id="error_test_002",
        task_type="generate_function",
        priority=TaskPriority.MEDIUM,
        payload={"spec": {}}  # 空の仕様
    )
    
    response = await code_crafter.process_request(empty_request)
    print(f"✓ 空ペイロード処理: {response.status.value}")
    
    # サーバントは適切にエラーを処理できているか
    assert response.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
    
    print("\nエラーハンドリング堅牢性テスト: 成功")


async def test_performance_metrics()print("\n=== パフォーマンスメトリクステスト ===")
"""パフォーマンスメトリクステスト"""
    
    test_forge = TestForge()
    
    # 複数の同時実行
    tasks = []
    for i in range(5):
        request = ServantRequest(
            task_id=f"perf_test_{i:03d}",
            task_type="generate_test_data",
            priority=TaskPriority.MEDIUM,
            payload={
                "spec": {
                    "schema": {
                        "id": {"type": "uuid"},
                        "name": {"type": "string"}, 
                        "value": {"type": "integer"}
                    },
                    "count": 10
                }
            }
        )
        tasks.append(test_forge.process_request(request))
    
    # 並列実行
    import time
    start_time = time.time()
    responses = await asyncio.gather(*tasks)
    end_time = time.time()
    
    total_time = (end_time - start_time) * 1000
    successful_tasks = sum(1 for r in responses if r.status == TaskStatus.COMPLETED)
    average_quality = sum(r.quality_score for r in responses) / len(responses)
    
    print(f"✓ 並列実行タスク数: {len(tasks)}")
    print(f"✓ 成功タスク数: {successful_tasks}")
    print(f"✓ 総実行時間: {total_time:0.2f}ms")
    print(f"✓ 平均品質スコア: {average_quality:0.1f}")
    print(f"✓ タスクあたり平均時間: {total_time/len(tasks):0.2f}ms")
    
    assert successful_tasks == len(tasks)
    assert average_quality >= 95.0
    assert total_time < 5000  # 5秒以内
    
    print("\nパフォーマンスメトリクステスト: 成功")


async def test_capability_discovery()print("\n=== 能力検出テスト ===")
"""能力検出テスト"""
    
    code_crafter = CodeCrafter()
    test_forge = TestForge()
    
    # CodeCrafter能力確認
    code_capabilities = code_crafter.get_capabilities()
    print(f"✓ CodeCrafter能力数: {len(code_capabilities)}")
    print(f"✓ 主要能力: {code_capabilities[:3]}")
    
    # TestForge能力確認
    test_capabilities = test_forge.get_capabilities()
    print(f"✓ TestForge能力数: {len(test_capabilities)}")
    print(f"✓ 主要能力: {test_capabilities[:3]}")
    
    # 能力の重複確認
    common_capabilities = set(code_capabilities) & set(test_capabilities)
    print(f"✓ 共通能力: {len(common_capabilities)}個")
    
    # 専門能力の確認
    code_specialized = code_crafter.get_specialized_capabilities()
    test_specialized = test_forge.get_specialized_capabilities()
    
    print(f"✓ CodeCrafter専門能力: {len(code_specialized)}個")
    print(f"✓ TestForge専門能力: {len(test_specialized)}個")
    
    assert len(code_capabilities) > 0
    assert len(test_capabilities) > 0
    assert len(code_specialized) > 0
    assert len(test_specialized) > 0
    
    print("\n能力検出テスト: 成功")


async def test_workflow_integration()print("\n=== ワークフロー統合テスト ===")
"""ワークフロー統合テスト"""
    
    # レジストリとサーバント準備
    registry = ServantRegistry()
    code_crafter = CodeCrafter()
    test_forge = TestForge()
    
    registry.register_servant(code_crafter)
    registry.register_servant(test_forge)
    
    # Step 1: 関数生成
    func_request = ServantRequest(
        task_id="workflow_001",
        task_type="generate_function",
        priority=TaskPriority.HIGH,
        payload={
            "spec": {
                "name": "validate_email",
                "parameters": [{"name": "email", "type": "str"}],
                "return_type": "bool",
                "docstring": "Validate email format",
                "body": '''
    import re
    pattern = r'^[a-zA-Z0-9.0_%+-]+@[a-zA-Z0-9.0-]+\\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))'''
            }
        }
    )
    
    func_response = await code_crafter.process_request(func_request)
    print(f"✓ Step 1 - 関数生成: {func_response.status.value}")
    
    # Step 2: 生成された関数のテスト作成
    test_request = ServantRequest(
        task_id="workflow_002",
        task_type="generate_unit_tests",
        priority=TaskPriority.HIGH,
        payload={
            "spec": {
                "source_code": func_response.result_data.get("code", ""),
                "framework": "pytest",
                "coverage_target": 95.0
            }
        }
    )
    
    test_response = await test_forge.process_request(test_request)
    print(f"✓ Step 2 - テスト生成: {test_response.status.value}")
    
    # Step 3: テストカバレッジ分析
    coverage_request = ServantRequest(
        task_id="workflow_003",
        task_type="analyze_test_coverage",
        priority=TaskPriority.MEDIUM,
        payload={
            "source_code": func_response.result_data.get("code", ""),
            "test_code": test_response.result_data.get("test_code", "")
        }
    )
    
    coverage_response = await test_forge.process_request(coverage_request)
    print(f"✓ Step 3 - カバレッジ分析: {coverage_response.status.value}")
    
    # ワークフロー品質確認
    overall_quality = (
        func_response.quality_score + 
        test_response.quality_score + 
        coverage_response.quality_score
    ) / 3
    
    print(f"✓ ワークフロー全体品質: {overall_quality:0.1f}%")
    print(f"✓ 総実行時間: {func_response.execution_time_ms " \
        "+ test_response.execution_time_ms + coverage_response.execution_time_ms:0.2f}ms")
    
    assert overall_quality >= 95.0
    
    print("\nワークフロー統合テスト: 成功")


async def main()print("🧝‍♂️ エルダーサーバントシステム総合テスト開始")
"""メインテスト実行"""
    print("="*60)
    
    try:
        await test_elders_legacy_integration()
        await test_servant_registry_updated()
        await test_iron_will_compliance()
        await test_error_handling_robustness()
        await test_performance_metrics()
        await test_capability_discovery()
        await test_workflow_integration()
        
        print("\n" + "="*60)
        print("🎉 すべてのテストが成功しました！")
        print("🏛️ EldersLegacy統合完了")
        print("⚡ Iron Will品質基準準拠確認")
        print("🚀 システム統合性確認完了")
        print("="*60)
        
        # 最終統計
        print("\n📊 システム統計:")
        print("- 実装済みサーバント: 2体 (CodeCrafter, TestForge)")
        print("- 品質基準達成率: 100%")
        print("- EldersLegacy統合: 完了")
        print("- Iron Will準拠: 95%以上保証")
        print("- 統一リクエスト形式: 対応済み")
        print("- エラーハンドリング: 堅牢性確認")
        
    except Exception as e:
        print(f"\n❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)