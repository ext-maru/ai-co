#!/usr/bin/env python3
"""
Elder Servants Parallel Testing Script

Batch 1 Priority Core Servants の並列テストを実行:
- DocForge (D03) - ドワーフ工房ドキュメント生成専門
- DataMiner (W02) - RAGウィザーズデータ分析専門
- TechScout (W01) - RAGウィザーズ技術調査専門 (既存)
- QualityWatcher (E01) - エルフの森品質監視専門 (既存)

Iron Will 品質基準でテスト実行
"""

import asyncio
import sys
import os
import logging
import json
from typing import Dict, List, Any
from datetime import datetime

# パスの追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from libs.elder_servants.registry.servant_registry import ServantRegistry, get_registry
from libs.elder_servants.base.elder_servant_base import ServantRequest, ServantDomain
from libs.elder_servants.dwarf_workshop.doc_forge import DocForge
from libs.elder_servants.rag_wizards.data_miner import DataMiner
from libs.elder_servants.rag_wizards.tech_scout import TechScout
from libs.elder_servants.elf_forest.quality_watcher import QualityWatcher

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("elder_servants_test")

async def register_all_servants() -> ServantRegistry:
    """すべてのエルダーサーバントをレジストリに登録"""
    registry = get_registry()
    
    servants_to_register = [
        (DocForge, "DocForge", ServantDomain.DWARF_WORKSHOP),
        (DataMiner, "DataMiner", ServantDomain.RAG_WIZARDS),
        (TechScout, "TechScout", ServantDomain.RAG_WIZARDS),
        (QualityWatcher, "QualityWatcher", ServantDomain.ELF_FOREST)
    ]
    
    for servant_class, name, domain in servants_to_register:
        try:
            success = registry.register(servant_class, name, domain)
            if success:
                logger.info(f"✅ Successfully registered {name}")
            else:
                logger.warning(f"⚠️ Failed to register {name}")
        except Exception as e:
            logger.error(f"❌ Error registering {name}: {str(e)}")
    
    return registry

async def test_doc_forge() -> Dict[str, Any]:
    """DocForge のテスト実行"""
    logger.info("🔨 Testing DocForge (D03)...")
    
    try:
        doc_forge = DocForge("D03", "DocForge", "documentation_generation")
        
        # テストリクエスト
        test_request = ServantRequest(
            task_id="doc_test_parallel_001",
            task_type="documentation_generation",
            priority="high",
            data={
                "source_code": """
def calculate_fibonacci(n: int) -> int:
    '''Calculate the nth Fibonacci number.
    
    Args:
        n: Position in Fibonacci sequence
        
    Returns:
        The nth Fibonacci number
    '''
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

class MathUtils:
    '''Utility class for mathematical operations.'''
    
    @staticmethod
    def factorial(n: int) -> int:
        '''Calculate factorial of n.'''
        if n <= 1:
            return 1
        return n * MathUtils.factorial(n-1)
""",
                "doc_type": "api_documentation",
                "format": "markdown",
                "language": "python"
            },
            context={"project_name": "Math Utilities API"}
        )
        
        # 処理実行
        response = await doc_forge.execute_with_quality_gate(test_request)
        
        # 結果の検証
        test_results = {
            "servant": "DocForge",
            "status": response.status,
            "success": response.status == "success",
            "documentation_generated": "documentation" in response.data,
            "contains_functions": "calculate_fibonacci" in response.data.get("documentation", ""),
            "contains_classes": "MathUtils" in response.data.get("documentation", ""),
            "quality_score": response.metrics.get("quality_score", 0),
            "errors": response.errors,
            "warnings": response.warnings
        }
        
        logger.info(f"DocForge test result: {test_results['success']}")
        return test_results
        
    except Exception as e:
        logger.error(f"DocForge test failed: {str(e)}")
        return {
            "servant": "DocForge",
            "status": "failed",
            "success": False,
            "error": str(e)
        }

async def test_data_miner() -> Dict[str, Any]:
    """DataMiner のテスト実行"""
    logger.info("📊 Testing DataMiner (W02)...")
    
    try:
        data_miner = DataMiner("W02", "DataMiner", "data_analysis")
        
        # テストデータの準備
        sample_data = {
            "csv_content": """name,age,salary,department,years_experience
John Doe,25,50000,Engineering,2
Jane Smith,30,65000,Marketing,5
Bob Wilson,35,70000,Engineering,8
Alice Brown,28,55000,Sales,3
Charlie Davis,32,60000,Marketing,6
Diana Prince,29,58000,Engineering,4
Eve Adams,26,52000,Sales,2
Frank Miller,33,68000,Engineering,9
Grace Lee,31,62000,Marketing,7
Henry Ford,27,54000,Sales,3""",
            "filename": "employee_data.csv"
        }
        
        # テストリクエスト
        test_request = ServantRequest(
            task_id="data_test_parallel_001",
            task_type="data_analysis",
            priority="high",
            data={
                "analysis_type": "statistical_summary",
                "data_source": sample_data,
                "output_format": "json",
                "metrics": ["mean", "median", "std", "correlation"]
            },
            context={"project_name": "HR Analytics"}
        )
        
        # 処理実行
        response = await data_miner.execute_with_quality_gate(test_request)
        
        # 結果の検証
        analysis_results = response.data.get("analysis_results", {})
        test_results = {
            "servant": "DataMiner",
            "status": response.status,
            "success": response.status == "success",
            "has_statistics": "summary_statistics" in analysis_results,
            "has_correlations": "correlations" in analysis_results,
            "data_processed": analysis_results.get("data_info", {}).get("row_count", 0),
            "quality_score": response.metrics.get("quality_score", 0),
            "insights_generated": len(response.data.get("insights", [])),
            "errors": response.errors,
            "warnings": response.warnings
        }
        
        logger.info(f"DataMiner test result: {test_results['success']}")
        return test_results
        
    except Exception as e:
        logger.error(f"DataMiner test failed: {str(e)}")
        return {
            "servant": "DataMiner",
            "status": "failed",
            "success": False,
            "error": str(e)
        }

async def test_tech_scout() -> Dict[str, Any]:
    """TechScout のテスト実行"""
    logger.info("🔍 Testing TechScout (W01)...")
    
    try:
        tech_scout = TechScout("W01", "TechScout", "technology_research")
        
        # テストリクエスト
        test_request = ServantRequest(
            task_id="tech_test_parallel_001",
            task_type="technology_research",
            priority="medium",
            data={
                "research_topic": "machine_learning_frameworks",
                "depth": "comprehensive",
                "focus_areas": ["python", "deep_learning", "performance"],
                "output_format": "structured_report"
            },
            context={"project_context": "AI development platform"}
        )
        
        # 処理実行
        response = await tech_scout.execute_with_quality_gate(test_request)
        
        # 結果の検証
        test_results = {
            "servant": "TechScout",
            "status": response.status,
            "success": response.status == "success",
            "research_completed": "research_results" in response.data,
            "recommendations_provided": "recommendations" in response.data,
            "quality_score": response.metrics.get("quality_score", 0),
            "errors": response.errors,
            "warnings": response.warnings
        }
        
        logger.info(f"TechScout test result: {test_results['success']}")
        return test_results
        
    except Exception as e:
        logger.error(f"TechScout test failed: {str(e)}")
        return {
            "servant": "TechScout",
            "status": "failed", 
            "success": False,
            "error": str(e)
        }

async def test_quality_watcher() -> Dict[str, Any]:
    """QualityWatcher のテスト実行"""
    logger.info("🌿 Testing QualityWatcher (E01)...")
    
    try:
        quality_watcher = QualityWatcher("E01", "QualityWatcher", "quality_monitoring")
        
        # テストリクエスト
        test_request = ServantRequest(
            task_id="quality_test_parallel_001",
            task_type="quality_monitoring",
            priority="high",
            data={
                "monitoring_type": "code_quality",
                "target_code": """
def process_data(data):

    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
""",
                "quality_standards": ["pep8", "complexity", "documentation"],
                "severity_threshold": "medium"
            },
            context={"project_name": "Quality Test"}
        )
        
        # 処理実行
        response = await quality_watcher.execute_with_quality_gate(test_request)
        
        # 結果の検証
        test_results = {
            "servant": "QualityWatcher",
            "status": response.status,
            "success": response.status == "success",
            "monitoring_completed": "monitoring_results" in response.data,
            "issues_detected": len(response.data.get("monitoring_results", {}).get("issues", [])),
            "quality_score": response.metrics.get("quality_score", 0),
            "errors": response.errors,
            "warnings": response.warnings
        }
        
        logger.info(f"QualityWatcher test result: {test_results['success']}")
        return test_results
        
    except Exception as e:
        logger.error(f"QualityWatcher test failed: {str(e)}")
        return {
            "servant": "QualityWatcher",
            "status": "failed",
            "success": False,
            "error": str(e)
        }

async def run_parallel_tests() -> Dict[str, Any]:
    """すべてのサーバントテストを並列実行"""
    logger.info("🚀 Starting parallel Elder Servants testing...")
    
    start_time = datetime.now()
    
    # 並列テスト実行
    test_tasks = [
        test_doc_forge(),
        test_data_miner(),
        test_tech_scout(),
        test_quality_watcher()
    ]
    
    test_results = await asyncio.gather(*test_tasks, return_exceptions=True)
    
    # 例外をエラー結果に変換
    processed_results = []
    for i, result in enumerate(test_results):
        if isinstance(result, Exception):
            processed_results.append({
                "servant": f"Unknown_{i}",
                "status": "failed",
                "success": False,
                "error": str(result)
            })
        else:
            processed_results.append(result)
    
    execution_time = (datetime.now() - start_time).total_seconds()
    
    # 総合結果の集計
    total_tests = len(processed_results)
    successful_tests = sum(1 for result in processed_results if result.get("success", False))
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    summary = {
        "test_execution": {
            "start_time": start_time.isoformat(),
            "execution_time_seconds": execution_time,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": success_rate
        },
        "individual_results": processed_results,
        "iron_will_compliance": success_rate >= 95,  # Iron Will基準
        "parallel_execution": True
    }
    
    return summary

async def generate_test_report(test_summary: Dict[str, Any]) -> str:
    """テスト結果レポートを生成"""
    report_lines = []
    
    report_lines.append("# Elder Servants Parallel Test Report")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # 実行サマリー
    exec_info = test_summary["test_execution"]
    report_lines.append("## Execution Summary")
    report_lines.append(f"- **Execution Time**: {exec_info['execution_time_seconds']:0.2f} seconds")
    report_lines.append(f"- **Total Tests**: {exec_info['total_tests']}")
    report_lines.append(f"- **Successful**: {exec_info['successful_tests']}")
    report_lines.append(f"- **Failed**: {exec_info['failed_tests']}")
    report_lines.append(f"- **Success Rate**: {exec_info['success_rate']:0.1f}%")
    report_lines.append(f"- **Iron Will Compliance**: {'✅ PASS' if test_summary['iron_will_compliance'] else '❌ FAIL'}")
    report_lines.append("")
    
    # 個別結果
    report_lines.append("## Individual Results")
    for result in test_summary["individual_results"]:
        servant_name = result.get("servant", "Unknown")
        status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
        
        report_lines.append(f"### {servant_name}")
        report_lines.append(f"- **Status**: {status}")
        report_lines.append(f"- **Quality Score**: {result.get('quality_score', 'N/A')}")
        
        if result.get("errors"):
            report_lines.append(f"- **Errors**: {len(result['errors'])}")
        if result.get("warnings"):
            report_lines.append(f"- **Warnings**: {len(result['warnings'])}")
        
        report_lines.append("")
    
    # 結論
    report_lines.append("## Conclusion")
    if test_summary["iron_will_compliance"]:
        report_lines.append("🎉 All Elder Servants meet Iron Will quality standards!")
        report_lines.append("Ready for deployment in parallel execution mode.")
    else:
        report_lines.append("⚠️ Some servants require improvement to meet Iron Will standards.")
        report_lines.append("Review failed tests and implement fixes.")
    
    return "\n".join(report_lines)

async def main():
    """メイン実行関数"""
    try:
        logger.info("🏛️ Elder Servants Parallel Testing Initiative")
        
        # レジストリの準備
        registry = await register_all_servants()
        logger.info(f"Registry prepared with {len(registry._servants)} servants")
        
        # 並列テスト実行
        test_summary = await run_parallel_tests()
        
        # レポート生成
        report = await generate_test_report(test_summary)
        
        # レポート出力
        print("\n" + "="*60)
        print(report)
        print("="*60)
        
        # JSON出力（詳細データ）
        json_output = json.dumps(test_summary, indent=2, default=str)
        output_file = f"/tmp/elder_servants_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            f.write(json_output)
        
        logger.info(f"📄 Detailed results saved to: {output_file}")
        
        # 終了コード
        exit_code = 0 if test_summary["iron_will_compliance"] else 1
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())