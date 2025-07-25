#!/usr/bin/env python3
"""
Elder Flow Orchestrator新メソッドの簡易動作確認
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from elders_guild.elder_tree.elder_flow_orchestrator import ElderFlowOrchestrator


async def test_new_methods():
    """新しいメソッドの動作確認"""
    print("🏛️ Elder Flow Orchestrator新メソッドテスト開始\n")
    
    orchestrator = ElderFlowOrchestrator()
    flow_id = None
    
    try:
        # 1.0 execute_sage_council
        print("📋 Phase 1: execute_sage_council テスト")
        sage_result = await orchestrator.execute_sage_council({
            "task_name": "テスト: OAuth2.0認証システム実装",
            "priority": "high"
        })
        
        if sage_result.get("status") == "success":
            flow_id = sage_result["flow_id"]
            print(f"✅ 成功: flow_id={flow_id}")
            print(f"   - recommendations: {sage_result.get('recommendations', [])}")
        else:
            print(f"❌ 失敗: {sage_result.get('error')}")
            return
        
        # 2.0 execute_elder_servants
        print("\n📋 Phase 2: execute_elder_servants テスト")
        servant_result = await orchestrator.execute_elder_servants({
            "task_name": "テスト: OAuth2.0認証システム実装",
            "flow_id": flow_id,
            "sage_recommendations": sage_result.get("recommendations", [])
        })
        
        if servant_result.get("status") == "success":
            print(f"✅ 成功")
            print(f"   - execution_plan: {len(servant_result.get('execution_plan', []))} steps")
            print(f"   - execution_results: {len(servant_result.get('execution_results', []))} results")
        else:
            print(f"❌ 失敗: {servant_result.get('error')}")
            return
        
        # 3.0 execute_quality_gate
        print("\n📋 Phase 3: execute_quality_gate テスト")
        quality_result = await orchestrator.execute_quality_gate({
            "flow_id": flow_id,
            "implementation_results": servant_result.get("execution_results", [])
        })
        
        if quality_result.get("status") == "success":
            print(f"✅ 成功")
            print(f"   - overall_score: {quality_result.get('overall_score', 0)}")
            print(f"   - quality_results: {quality_result.get('quality_results', {})}")
        else:
            print(f"❌ 失敗: {quality_result.get('error')}")
            return
        
        # 4.0 execute_council_report
        print("\n📋 Phase 4: execute_council_report テスト")
        report_result = await orchestrator.execute_council_report({
            "flow_id": flow_id,
            "all_results": {
                "sage_council": sage_result,
                "servant_execution": servant_result,
                "quality_gate": quality_result
            }
        })
        
        if report_result.get("status") == "success":
            print(f"✅ 成功")
            council_report = report_result.get("council_report", {})
            print(f"   - summary: {council_report.get('summary', '')}")
            print(f"   - quality_score: {council_report.get('quality_score', 0)}")
        else:
            print(f"❌ 失敗: {report_result.get('error')}")
            return
        
        # 5.0 execute_git_automation
        print("\n📋 Phase 5: execute_git_automation テスト")
        git_result = await orchestrator.execute_git_automation({
            "flow_id": flow_id,
            "implementation_results": servant_result.get("execution_results", [])
        })
        
        if git_result.get("status") == "success":
            print(f"✅ 成功")
            print(f"   - git_status: {git_result.get('git_status', 'unknown')}")
            print(f"   - git_commit_id: {git_result.get('git_commit_id', 'none')}")
        else:
            print(f"❌ 失敗: {git_result.get('error')}")
            return
        
        print("\n🎉 すべてのメソッドのテストが成功しました！")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_new_methods())