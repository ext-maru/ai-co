#!/usr/bin/env python3
"""
New Elder Servants Batch Test Script

Tests all newly implemented servants:
- DocForge (D03) - ドワーフ工房ドキュメント生成専門
- DataMiner (W02) - RAGウィザーズデータ分析専門  
- SecurityGuard (E02) - エルフの森セキュリティ監視専門
- APIForge (D04) - ドワーフ工房API生成専門

Validates Iron Will quality standards and parallel execution capabilities.
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List

# パスの追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from libs.elder_servants.base.elder_servant_base import ServantRequest
from libs.elder_servants.dwarf_workshop.doc_forge import DocForge
from libs.elder_servants.rag_wizards.data_miner import DataMiner
from libs.elder_servants.elf_forest.security_guard import SecurityGuard
from libs.elder_servants.dwarf_workshop.api_forge import APIForge


async def test_doc_forge() -> Dict[str, Any]:
    """DocForge comprehensive test"""
    print("🔨 Testing DocForge (D03)...")
    
    try:
        doc_forge = DocForge("D03", "DocForge", "documentation_generation")
        
        test_request = ServantRequest(
            task_id="doc_comprehensive_001",
            task_type="documentation_generation",
            priority="high",
            data={
                "source_code": """
class UserManager:
    '''Manages user operations and authentication.'''
    
    def __init__(self, database_url: str):
        '''Initialize with database connection.'''
        self.db_url = database_url
    
    def create_user(self, username: str, email: str, password: str) -> dict:
        '''Create a new user account.
        
        Args:
            username: Unique username
            email: User email address
            password: User password (will be hashed)
            
        Returns:
            dict: Created user information
            
        Raises:
            ValueError: If username already exists
        '''
        return {"id": 123, "username": username, "email": email}
    
    def authenticate(self, username: str, password: str) -> bool:
        '''Authenticate user credentials.'''
        return True

def calculate_metrics(data: List[float]) -> dict:
    '''Calculate statistical metrics for data.'''
    if not data:
        return {}
    return {
        "mean": sum(data) / len(data),
        "min": min(data),
        "max": max(data)
    }
""",
                "doc_type": "api_documentation",
                "format": "markdown",
                "language": "python",
                "include_examples": True
            },
            context={"project_name": "User Management API"}
        )
        
        response = await doc_forge.execute_with_quality_gate(test_request)
        
        # Comprehensive validation
        results = {
            "servant": "DocForge",
            "status": response.status,
            "success": response.status == "success",
            "validation": {
                "request_valid": doc_forge.validate_request(test_request),
                "documentation_generated": "documentation" in response.data,
                "contains_classes": "UserManager" in response.data.get("documentation", ""),
                "contains_methods": "create_user" in response.data.get("documentation", ""),
                "contains_functions": "calculate_metrics" in response.data.get("documentation", ""),
                "quality_sufficient": response.metrics.get("quality_score", 0) >= 50
            },
            "metrics": {
                "quality_score": response.metrics.get("quality_score", 0),
                "doc_length": len(response.data.get("documentation", "")),
                "processing_time": response.metrics.get("processing_time", 0)
            },
            "errors": response.errors,
            "warnings": response.warnings
        }
        
        print(f"  ✅ DocForge test: {'PASS' if results['success'] else 'FAIL'}")
        print(f"  📊 Quality Score: {results['metrics']['quality_score']}")
        
        return results
        
    except Exception as e:
        print(f"  ❌ DocForge error: {str(e)}")
        return {"servant": "DocForge", "success": False, "error": str(e)}


async def test_data_miner() -> Dict[str, Any]:
    """DataMiner comprehensive test"""
    print("\n📊 Testing DataMiner (W02)...")
    
    try:
        data_miner = DataMiner("W02", "DataMiner", "data_analysis")
        
        # Complex dataset
        complex_data = {
            "csv_content": """product,category,price,sales,rating,region
Laptop,Electronics,1200,450,4.5,North
Phone,Electronics,800,620,4.2,South
Tablet,Electronics,600,380,4.0,East
Keyboard,Accessories,120,890,4.3,North
Mouse,Accessories,80,1200,4.1,West
Monitor,Electronics,400,320,4.4,North
Headset,Accessories,150,560,4.2,South
Cable,Accessories,25,2300,3.9,East
Speakers,Electronics,200,440,4.0,West
Webcam,Electronics,180,290,3.8,South""",
            "filename": "sales_data.csv"
        }
        
        test_request = ServantRequest(
            task_id="data_comprehensive_001",
            task_type="data_analysis",
            priority="high",
            data={
                "analysis_type": "statistical_summary",
                "data_source": complex_data,
                "output_format": "json",
                "metrics": ["mean", "median", "std", "correlation"],
                "include_outliers": True
            },
            context={"project_name": "Sales Analytics"}
        )
        
        response = await data_miner.execute_with_quality_gate(test_request)
        
        # Comprehensive validation
        analysis_results = response.data.get("analysis_results", {})
        results = {
            "servant": "DataMiner",
            "status": response.status,
            "success": response.status == "success",
            "validation": {
                "request_valid": data_miner.validate_request(test_request),
                "analysis_completed": "summary_statistics" in analysis_results,
                "statistics_generated": len(analysis_results.get("summary_statistics", {})) > 0,
                "data_quality_assessed": "data_quality" in analysis_results,
                "insights_provided": len(response.data.get("insights", [])) > 0
            },
            "metrics": {
                "quality_score": response.metrics.get("quality_score", 0),
                "data_points": response.metrics.get("data_points_analyzed", 0),
                "columns_analyzed": len(analysis_results.get("summary_statistics", {}))
            },
            "analysis_details": {
                "price_mean": analysis_results.get("summary_statistics", {}).get("price", {}).get("mean", 0),
                "sales_mean": analysis_results.get("summary_statistics", {}).get("sales", {}).get("mean", 0),
                "data_rows": analysis_results.get("data_info", {}).get("row_count", 0)
            },
            "errors": response.errors,
            "warnings": response.warnings
        }
        
        print(f"  ✅ DataMiner test: {'PASS' if results['success'] else 'FAIL'}")
        print(f"  📊 Quality Score: {results['metrics']['quality_score']}")
        print(f"  📈 Data Points: {results['metrics']['data_points']}")
        
        return results
        
    except Exception as e:
        print(f"  ❌ DataMiner error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"servant": "DataMiner", "success": False, "error": str(e)}


async def test_security_guard() -> Dict[str, Any]:
    """SecurityGuard comprehensive test"""
    print("\n🛡️ Testing SecurityGuard (E02)...")
    
    try:
        security_guard = SecurityGuard("E02", "SecurityGuard", "security_monitoring")
        
        # Vulnerable code sample
        vulnerable_code = """
import os
import mysql.connector

def login(username, password):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    
    # Hardcoded credentials
    admin_password = "admin123"
    
    # Command injection vulnerability
    os.system(f"echo {username} logged in")
    
    # Insecure crypto
    import hashlib
    hashed = hashlib.md5(password.encode()).hexdigest()
    
    return True

def debug_info():
    # Information disclosure
    print(f"Database password: {os.environ.get('DB_PASS', 'secret123')}")
    
    # Eval vulnerability
    user_input = input("Enter code: ")
    eval(user_input)
"""
        
        test_request = ServantRequest(
            task_id="security_comprehensive_001",
            task_type="security_monitoring",
            priority="high",
            data={
                "scan_type": "vulnerability_scan",
                "target_code": vulnerable_code,
                "severity_threshold": "low",
                "include_dependencies": True,
                "compliance_standards": ["OWASP", "CWE"]
            },
            context={"project_name": "Security Test"}
        )
        
        response = await security_guard.execute_with_quality_gate(test_request)
        
        # Comprehensive validation
        scan_results = response.data.get("security_scan", {})
        threat_analysis = response.data.get("threat_analysis", {})
        
        results = {
            "servant": "SecurityGuard",
            "status": response.status,
            "success": response.status == "success",
            "validation": {
                "request_valid": security_guard.validate_request(test_request),
                "scan_completed": "security_issues" in scan_results,
                "vulnerabilities_detected": len(scan_results.get("security_issues", [])) > 0,
                "threat_analysis_done": "overall_threat" in threat_analysis,
                "compliance_checked": "compliance_results" in response.data
            },
            "security_metrics": {
                "total_issues": scan_results.get("scan_summary", {}).get("total_issues", 0),
                "critical_issues": scan_results.get("scan_summary", {}).get("critical_issues", 0),
                "high_issues": scan_results.get("scan_summary", {}).get("high_issues", 0),
                "threat_level": threat_analysis.get("overall_threat", "UNKNOWN"),
                "security_score": response.metrics.get("security_score", 0)
            },
            "detected_categories": list(set([
                issue.get("category", "unknown") 
                for issue in scan_results.get("security_issues", [])
            ])),
            "errors": response.errors,
            "warnings": response.warnings
        }
        
        print(f"  ✅ SecurityGuard test: {'PASS' if results['success'] else 'FAIL'}")
        print(f"  🔍 Issues found: {results['security_metrics']['total_issues']}")
        print(f"  ⚠️ Threat level: {results['security_metrics']['threat_level']}")
        
        return results
        
    except Exception as e:
        print(f"  ❌ SecurityGuard error: {str(e)}")
        return {"servant": "SecurityGuard", "success": False, "error": str(e)}


async def test_api_forge() -> Dict[str, Any]:
    """APIForge comprehensive test"""
    print("\n🔧 Testing APIForge (D04)...")
    
    try:
        api_forge = APIForge("D04", "APIForge", "api_generation")
        
        test_request = ServantRequest(
            task_id="api_comprehensive_001",
            task_type="api_generation",
            priority="high",
            data={
                "api_type": "rest",
                "framework": "fastapi",
                "language": "python",
                "api_description": "User management API with CRUD operations",
                "include_authentication": True,
                "include_validation": True,
                "include_tests": True,
                "include_documentation": True,
                "database_integration": False
            },
            context={"project_name": "User API"}
        )
        
        response = await api_forge.execute_with_quality_gate(test_request)
        
        # Comprehensive validation
        api_impl = response.data.get("api_implementation", {})
        api_tests = response.data.get("api_tests", {})
        api_docs = response.data.get("api_documentation", {})
        
        results = {
            "servant": "APIForge",
            "status": response.status,
            "success": response.status == "success",
            "validation": {
                "request_valid": api_forge.validate_request(test_request),
                "api_generated": "main.py" in api_impl,
                "tests_generated": api_tests is not None and len(api_tests) > 0,
                "docs_generated": api_docs is not None and len(api_docs) > 0,
                "requirements_included": "requirements.txt" in api_impl,
                "dockerfile_included": "Dockerfile" in api_impl
            },
            "api_metrics": {
                "quality_score": response.metrics.get("quality_score", 0),
                "endpoints_generated": response.metrics.get("endpoints_generated", 0),
                "files_generated": len(api_impl),
                "test_files": len(api_tests) if api_tests else 0,
                "doc_files": len(api_docs) if api_docs else 0
            },
            "generated_files": {
                "implementation": list(api_impl.keys()),
                "tests": list(api_tests.keys()) if api_tests else [],
                "documentation": list(api_docs.keys()) if api_docs else []
            },
            "errors": response.errors,
            "warnings": response.warnings
        }
        
        print(f"  ✅ APIForge test: {'PASS' if results['success'] else 'FAIL'}")
        print(f"  📊 Quality Score: {results['api_metrics']['quality_score']}")
        print(f"  🔗 Endpoints: {results['api_metrics']['endpoints_generated']}")
        
        return results
        
    except Exception as e:
        print(f"  ❌ APIForge error: {str(e)}")
        return {"servant": "APIForge", "success": False, "error": str(e)}


async def run_parallel_comprehensive_tests() -> Dict[str, Any]:
    """Run all servant tests in parallel"""
    print("🚀 Starting Comprehensive Elder Servants Testing...")
    print("Testing new batch: DocForge, DataMiner, SecurityGuard, APIForge")
    print("=" * 70)
    
    start_time = datetime.now()
    
    # Run all tests in parallel
    test_tasks = [
        test_doc_forge(),
        test_data_miner(),
        test_security_guard(),
        test_api_forge()
    ]
    
    test_results = await asyncio.gather(*test_tasks, return_exceptions=True)
    
    # Process results
    processed_results = []
    for i, result in enumerate(test_results):
        if isinstance(result, Exception):
            servant_names = ["DocForge", "DataMiner", "SecurityGuard", "APIForge"]
            processed_results.append({
                "servant": servant_names[i] if i < len(servant_names) else f"Unknown_{i}",
                "success": False,
                "error": str(result)
            })
        else:
            processed_results.append(result)
    
    execution_time = (datetime.now() - start_time).total_seconds()
    
    # Calculate overall metrics
    total_tests = len(processed_results)
    successful_tests = sum(1 for r in processed_results if r.get("success", False))
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    # Quality score aggregation
    quality_scores = []
    for result in processed_results:
        if result.get("success") and "metrics" in result:
            quality_scores.append(result["metrics"].get("quality_score", 0))
        elif result.get("success") and "api_metrics" in result:
            quality_scores.append(result["api_metrics"].get("quality_score", 0))
        elif result.get("success") and "security_metrics" in result:
            quality_scores.append(result["security_metrics"].get("security_score", 0))
    
    avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    
    summary = {
        "execution_summary": {
            "start_time": start_time.isoformat(),
            "execution_time_seconds": execution_time,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": success_rate,
            "average_quality_score": avg_quality_score
        },
        "individual_results": processed_results,
        "iron_will_compliance": success_rate >= 95 and avg_quality_score >= 80,
        "parallel_execution": True,
        "test_categories": {
            "documentation": [r for r in processed_results if r.get("servant") == "DocForge"],
            "data_analysis": [r for r in processed_results if r.get("servant") == "DataMiner"],
            "security": [r for r in processed_results if r.get("servant") == "SecurityGuard"],
            "api_generation": [r for r in processed_results if r.get("servant") == "APIForge"]
        }
    }
    
    return summary


def generate_comprehensive_report(summary: Dict[str, Any]) -> str:
    """Generate detailed test report"""
    report_lines = []
    
    # Header
    report_lines.extend([
        "# Elder Servants Comprehensive Test Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "Testing New Batch: DocForge, DataMiner, SecurityGuard, APIForge",
        ""
    ])
    
    # Executive Summary
    exec_summary = summary["execution_summary"]
    report_lines.extend([
        "## Executive Summary",
        f"- **Execution Time**: {exec_summary['execution_time_seconds']:0.2f} seconds",
        f"- **Success Rate**: {exec_summary['success_rate']:0.1f}%",
        f"- **Average Quality Score**: {exec_summary['average_quality_score']:0.1f}/100",
        f"- **Iron Will Compliance**: {'✅ PASS' if summary['iron_will_compliance'] else '❌ FAIL'}",
        f"- **Parallel Execution**: {'✅ Enabled' if summary['parallel_execution'] else '❌ Disabled'}",
        ""
    ])
    
    # Individual Results
    report_lines.append("## Individual Servant Results")
    
    for result in summary["individual_results"]:
        servant_name = result.get("servant", "Unknown")
        success = result.get("success", False)
        
        report_lines.extend([
            f"### {servant_name}",
            f"**Status**: {'✅ PASS' if success else '❌ FAIL'}"
        ])
        
        if success:
            # Servant-specific metrics
            if "metrics" in result:
                metrics = result["metrics"]
                report_lines.extend([
                    f"- **Quality Score**: {metrics.get('quality_score', 'N/A')}",
                    f"- **Processing Details**: {metrics}"
                ])
            
            if "validation" in result:
                validation = result["validation"]
                passed_validations = sum(1 for v in validation.values() if v)
                total_validations = len(validation)
                report_lines.append(f"- **Validation**: {passed_validations}/{total_validations} checks passed")
            
            # Specific metrics per servant type
            if servant_name == "SecurityGuard" and "security_metrics" in result:
                sec_metrics = result["security_metrics"]
                report_lines.extend([
                    f"- **Security Issues**: {sec_metrics.get('total_issues', 0)}",
                    f"- **Threat Level**: {sec_metrics.get('threat_level', 'Unknown')}"
                ])
            
            elif servant_name == "APIForge" and "api_metrics" in result:
                api_metrics = result["api_metrics"]
                report_lines.extend([
                    f"- **Endpoints Generated**: {api_metrics.get('endpoints_generated', 0)}",
                    f"- **Files Created**: {api_metrics.get('files_generated', 0)}"
                ])
        
        else:
            error = result.get("error", "Unknown error")
            report_lines.append(f"- **Error**: {error}")
        
        report_lines.append("")
    
    # Conclusion
    report_lines.extend([
        "## Conclusion",
        ""
    ])
    
    if summary["iron_will_compliance"]:
        report_lines.extend([
            "🎉 **SUCCESS**: All Elder Servants meet Iron Will quality standards!",
            "",
            "### Next Steps:",
            "- Deploy servants to production environment",
            "- Enable parallel processing for maximum efficiency",
            "- Monitor performance in live environment",
            "- Continue with Phase 3 implementation"
        ])
    else:
        report_lines.extend([
            "⚠️ **IMPROVEMENT NEEDED**: Some servants require optimization.",
            "",
            "### Action Items:",
            "- Review failed tests and implement fixes",
            "- Improve quality scores where needed",
            "- Re-run tests after improvements",
            "- Consider additional training or optimization"
        ])
    
    return "\n".join(report_lines)


async def main():
    """Main execution function"""
    try:
        # Run comprehensive tests
        summary = await run_parallel_comprehensive_tests()
        
        # Generate and display report
        report = generate_comprehensive_report(summary)
        
        print("\n" + "=" * 70)
        print(report)
        print("=" * 70)
        
        # Save detailed results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"/tmp/elder_servants_comprehensive_test_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        # Exit with appropriate code
        success = summary["iron_will_compliance"]
        exit_code = 0 if success else 1
        
        print(f"\n🎯 Final Result: {'SUCCESS' if success else 'NEEDS_IMPROVEMENT'}")
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())