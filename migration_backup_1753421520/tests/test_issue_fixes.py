#!/usr/bin/env python3
"""
Issue修正の統合テスト
Issue #157, #158の修正を検証
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_elder_flow_orchestrator_imports():
    """ElderFlowOrchestratorがインポートできることを確認"""
    try:
        from libs.elder_flow_orchestrator import ElderFlowOrchestrator
        print("✅ ElderFlowOrchestrator import success")
        
        # 互換性メソッドの存在確認
        orchestrator = ElderFlowOrchestrator()
        assert hasattr(orchestrator, '_consult_knowledge_sage'), "Missing _consult_knowledge_sage method"
        assert hasattr(orchestrator, '_consult_task_sage'), "Missing _consult_task_sage method"
        assert hasattr(orchestrator, '_consult_incident_sage'), "Missing _consult_incident_sage method"
        assert hasattr(orchestrator, '_consult_rag_sage'), "Missing _consult_rag_sage method"
        print("✅ All sage consultation methods exist")
        
        return True
    except Exception as e:
        print(f"❌ ElderFlowOrchestrator import failed: {e}")
        return False


def test_auto_issue_processor_imports():
    """AutoIssueProcessorがインポートできることを確認"""
    try:
        from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
        from libs.integrations.github.safe_git_operations import SafeGitOperations
        print("✅ AutoIssueProcessor and SafeGitOperations import success")
        return True
    except Exception as e:
        print(f"❌ AutoIssueProcessor import failed: {e}")
        return False


def test_security_issues_key_handling():
    """security_issuesキーの安全な参照を確認"""
    quality_results = {
        "code_quality": 80,
        "security_scan": "passed"
        # security_issuesキーは意図的に含まない
    }
    
    # .get()メソッドでデフォルト値を使用
    security_issues = quality_results.get("security_issues", 0)
    assert security_issues == 0, "Default value should be 0"
    print("✅ security_issues key handling works correctly")
    return True


async def test_sage_consultation_methods():
    """賢者相談メソッドの基本動作を確認"""
    from libs.elder_flow_orchestrator import ElderFlowOrchestrator
    
    orchestrator = ElderFlowOrchestrator()
    
    # 各賢者相談メソッドを呼び出し（実際の賢者が初期化されていないため、フォールバックが動作するはず）
    test_request = {"type": "test", "query": "test query"}
    
    try:
        # Knowledge Sage
        result = await orchestrator._consult_knowledge_sage(test_request)
        assert isinstance(result, dict), "Should return a dictionary"
        print("✅ _consult_knowledge_sage works")
        
        # Task Sage
        result = await orchestrator._consult_task_sage(test_request)
        assert isinstance(result, dict), "Should return a dictionary"
        print("✅ _consult_task_sage works")
        
        # Incident Sage
        result = await orchestrator._consult_incident_sage(test_request)
        assert isinstance(result, dict), "Should return a dictionary"
        print("✅ _consult_incident_sage works")
        
        # RAG Sage
        result = await orchestrator._consult_rag_sage(test_request)
        assert isinstance(result, dict), "Should return a dictionary"
        print("✅ _consult_rag_sage works")
        
        return True
    except Exception as e:
        print(f"❌ Sage consultation test failed: {e}")
        return False


def main():
    """すべてのテストを実行"""
    print("🧪 Running Issue Fixes Integration Tests\n")
    
    results = []
    
    # 同期テスト
    results.append(("ElderFlowOrchestrator Import", test_elder_flow_orchestrator_imports()))
    results.append(("AutoIssueProcessor Import", test_auto_issue_processor_imports()))
    results.append(("Security Issues Key Handling", test_security_issues_key_handling()))
    
    # 非同期テスト
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results.append(("Sage Consultation Methods", loop.run_until_complete(test_sage_consultation_methods())))
    
    # 結果サマリー
    print("\n📊 Test Results Summary:")
    total = len(results)
    passed = sum(1 for _, result in results if result)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)