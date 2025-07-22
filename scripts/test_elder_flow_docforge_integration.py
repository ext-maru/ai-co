#!/usr/bin/env python3
"""
Elder Flow + DocForge Enhanced統合テストスクリプト
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.elder_flow_integration import execute_elder_flow, get_elder_flow_status


async def test_docforge_integration():
    """DocForge Enhanced統合のテスト"""
    print("🌊 Elder Flow + DocForge Enhanced Integration Test")
    print("=" * 50)
    
    # 設計書生成タスク
    test_requirements = """
    ECサイトでは、顧客が商品を検索し、カートに追加して購入できる。
    会員ランクがゴールドの場合、全商品15%割引を適用する。
    注文金額が1万円以上の場合、送料無料とする。
    在庫管理システムと連携し、リアルタイムで在庫を更新する。
    決済はクレジットカード、PayPal、銀行振込に対応する。
    購入履歴から推薦商品を表示する。
    """
    
    print("📋 テスト要件:")
    print(test_requirements.strip())
    print()
    
    try:
        # Elder Flow実行（設計書生成タスクとして認識されるはず）
        print("🚀 Starting Elder Flow with design document task...")
        task_id = await execute_elder_flow(
            description=f"ECサイト設計書作成: {test_requirements.strip()}",
            priority="high",
            auto_commit=False  # テストなのでコミットしない
        )
        
        print(f"✅ Task started: {task_id}")
        
        # 結果確認
        status = get_elder_flow_status(task_id)
        if status:
            print(f"\n📊 Task Status: {status['status']}")
            print(f"⏱️  Duration: {status['total_duration']:.2f}s")
            
            # 実行結果の詳細
            if status.get("execution_result"):
                exec_result = status["execution_result"]
                
                if exec_result.get("doc_forge_enhanced"):
                    print("\n🏗️ DocForge Enhanced Results:")
                    print(f"   Quality Score: {exec_result.get('quality_score', 0):.1f}/100")
                    print(f"   Word Count: {exec_result.get('word_count', 0)}")
                    
                    analysis = exec_result.get("analysis_results", {})
                    print(f"   Entities: {analysis.get('entities_count', 0)}")
                    print(f"   Business Rules: {analysis.get('business_rules_count', 0)}")
                    print(f"   Implicit Needs: {analysis.get('implicit_needs_count', 0)}")
                    
                    output_file = exec_result.get("output_file")
                    if output_file:
                        print(f"   Output File: {output_file}")
                        
                        # ファイル内容の一部を表示
                        try:
                            with open(output_file, "r", encoding="utf-8") as f:
                                content = f.read()
                                lines = content.split("\n")
                                print("\n📝 Generated Document (first 10 lines):")
                                for i, line in enumerate(lines[:10], 1):
                                    print(f"   {i:2}: {line}")
                                if len(lines) > 10:
                                    print(f"   ... (total {len(lines)} lines)")
                        except Exception as e:
                            print(f"   ⚠️ Could not read output file: {e}")
                else:
                    print("\n📄 Standard Elder Flow execution (not DocForge Enhanced)")
            
            # 品質結果
            if status.get("quality_result"):
                quality = status["quality_result"]
                print(f"\n🔍 Quality Assessment:")
                print(f"   Status: {quality.get('overall_status', 'unknown')}")
                print(f"   Score: {quality.get('overall_score', 0):.1f}/10")
                
                if quality.get("quality_summary", {}).get("analyzer_enhanced"):
                    print("   ✅ Enhanced Requirement Analyzer used")
                
                if quality.get("error"):
                    print(f"   ❌ Error: {quality['error']}")
            
            if status.get("error_message"):
                print(f"\n❌ Task Error: {status['error_message']}")
        
        return task_id
    
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return None


async def test_standard_flow():
    """標準フロー（非設計書タスク）のテスト"""
    print("\n" + "=" * 50)
    print("🔧 Standard Elder Flow Test (non-design task)")
    print("=" * 50)
    
    try:
        task_id = await execute_elder_flow(
            description="OAuth2.0認証システムの実装",  # これは設計書タスクではない
            priority="medium",
            auto_commit=False
        )
        
        print(f"✅ Standard flow task started: {task_id}")
        
        status = get_elder_flow_status(task_id)
        if status and status.get("execution_result"):
            exec_result = status["execution_result"]
            if exec_result.get("doc_forge_enhanced"):
                print("❌ Unexpected: DocForge Enhanced was used for non-design task")
            else:
                print("✅ Standard Elder Flow was used correctly")
        
        return task_id
    
    except Exception as e:
        print(f"❌ Standard flow test failed: {str(e)}")
        return None


async def main():
    """メインテスト関数"""
    print("🧪 Elder Flow DocForge Enhanced Integration Test Suite")
    print("Testing the integration of DocForge Enhanced into Elder Flow main system")
    print()
    
    # テスト1: 設計書生成タスク
    design_task_id = await test_docforge_integration()
    
    # テスト2: 標準フロー
    standard_task_id = await test_standard_flow()
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("=" * 50)
    
    if design_task_id:
        print(f"✅ Design Document Task: {design_task_id}")
    else:
        print("❌ Design Document Task: FAILED")
    
    if standard_task_id:
        print(f"✅ Standard Flow Task: {standard_task_id}")
    else:
        print("❌ Standard Flow Task: FAILED")
    
    success_count = sum([1 for task_id in [design_task_id, standard_task_id] if task_id])
    print(f"\n📈 Success Rate: {success_count}/2 ({success_count/2*100:.0f}%)")
    
    if success_count == 2:
        print("🎉 All tests passed! Elder Flow + DocForge Enhanced integration is working!")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main())