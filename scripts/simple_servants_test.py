#!/usr/bin/env python3
"""
Simple Elder Servants Test Script

Tests the newly implemented DocForge and DataMiner servants
"""

import asyncio
import os
import sys
from datetime import datetime

# パスの追加
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from libs.elder_servants.base.elder_servant import (
    ServantRequest,
    TaskPriority,
    TaskStatus,
)
from libs.elder_servants.dwarf_workshop.doc_forge import DocForge
from libs.elder_servants.rag_wizards.data_miner import DataMiner


async def test_doc_forge():
    """DocForge のテスト"""
    print("🔨 Testing DocForge...")

    try:
        doc_forge = DocForge()

        # テストリクエスト
        test_request = ServantRequest(
            task_id="doc_test_001",
            task_type="documentation_generation",
            priority=TaskPriority.HIGH,
            payload={
                "source_code": """
def hello_world():
    '''Print hello world message.'''
    print("Hello, World!")

class Calculator:
    '''A simple calculator class.'''

    def add(self, a: int, b: int) -> int:
        '''Add two numbers.'''
        return a + b
""",
                "doc_type": "api_documentation",
                "format": "markdown",
                "language": "python",
            },
            context={"project_name": "Test API"},
        )

        # リクエスト検証
        is_valid = doc_forge.validate_request(test_request)
        print(f"  Request validation: {'✅' if is_valid else '❌'}")

        if is_valid:
            # 処理実行
            response = await doc_forge.process_request(test_request)
            success = response.status == TaskStatus.COMPLETED
            print(f"  Processing: {'✅' if success else '❌'}")

            if success:
                doc_content = response.result_data.get("documentation", "")
                has_content = len(doc_content) > 100
                print(f"  Documentation generated: {'✅' if has_content else '❌'}")
                print(f"  Quality score: {response.quality_score}")

                # サンプル出力
                print("  Sample output:")
                print("  " + doc_content[:200] + "...")
            else:
                print(f"  Error: {response.error_message}")

        return is_valid and (
            response.status == TaskStatus.COMPLETED if is_valid else False
        )

    except Exception as e:
        print(f"  Error: {str(e)}")
        return False


async def test_data_miner():
    """DataMiner のテスト"""
    print("\n📊 Testing DataMiner...")

    try:
        data_miner = DataMiner("W02", "DataMiner", "data_analysis")

        # テストデータ
        sample_data = {
            "csv_content": """name,age,score
Alice,25,85
Bob,30,92
Charlie,28,78
Diana,32,88""",
            "filename": "test_data.csv",
        }

        # テストリクエスト
        test_request = ServantRequest(
            task_id="data_test_001",
            task_type="data_analysis",
            priority=TaskPriority.MEDIUM,
            payload={
                "analysis_type": "statistical_summary",
                "data_source": sample_data,
                "output_format": "json",
                "metrics": ["mean", "median", "std"],
            },
            context={"project_name": "Test Analysis"},
        )

        # リクエスト検証
        is_valid = data_miner.validate_request(test_request)
        print(f"  Request validation: {'✅' if is_valid else '❌'}")

        if is_valid:
            # 処理実行
            response = await data_miner.process_request(test_request)
            success = response.status == TaskStatus.COMPLETED
            print(f"  Processing: {'✅' if success else '❌'}")

            if success:
                analysis_results = response.result_data.get("analysis_results", {})
                has_stats = "summary_statistics" in analysis_results
                print(f"  Analysis completed: {'✅' if has_stats else '❌'}")
                print(f"  Quality score: {response.quality_score}")

                # 統計結果の表示
                if has_stats:
                    stats = analysis_results["summary_statistics"]
                    print(f"  Statistics generated for {len(stats)} columns")
                    for col, col_stats in stats.items():
                        print(f"    {col}: mean={col_stats.get('mean', 'N/A'):.2f}")
            else:
                print(f"  Error: {response.error_message}")

        return is_valid and (
            response.status == TaskStatus.COMPLETED if is_valid else False
        )

    except Exception as e:
        print(f"  Error: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """メイン実行"""
    print("🏛️ Elder Servants Simple Test")
    print("=" * 40)

    # テスト実行
    doc_forge_success = await test_doc_forge()
    data_miner_success = await test_data_miner()

    print("\n" + "=" * 40)
    print("📊 Test Results:")
    print(f"  DocForge (D03): {'✅ PASS' if doc_forge_success else '❌ FAIL'}")
    print(f"  DataMiner (W02): {'✅ PASS' if data_miner_success else '❌ FAIL'}")

    overall_success = doc_forge_success and data_miner_success
    print(
        f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}"
    )

    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
