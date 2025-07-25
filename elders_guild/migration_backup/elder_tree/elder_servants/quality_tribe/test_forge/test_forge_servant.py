"""
🔨 TestForge Servant - テスト品質統括サーバント
python-a2a統合による Block B 実装
One Servant, One Command: verify_test_quality
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from python_a2a import A2AServer, skill, Message, TextContent, MessageRole

# 既存エンジンの活用
from elders_guild.quality.test_automation_engine import TestAutomationEngine

logger = logging.getLogger(__name__)


class TestForgeServant(A2AServer):
    """
    Block B: テスト品質統括サーバント
    
    責任範囲:
    - pytest/coverage/hypothesis/toxの統合実行
    - テスト品質・カバレッジの専門判定
    - TDD準拠の確認
    - テスト戦略の最適化提案
    """
    
    def __init__(self, host: str = "localhost", port: int = 8811):
        """A2Aサーバント初期化"""
        super().__init__()
        
        # サーバント情報
        self.agent_name = "test-forge"
        self.description = "Test Quality Guardian - Block B"
        self.host = host
        self.port = port
        self.command = "verify_test_quality"  # One Command
        
        # テスト自動化エンジン
        self.test_engine = TestAutomationEngine()
        
        # メトリクス
        self.total_verifications = 0
        self.tdd_compliant_count = 0
        self.coverage_failures = 0
        
        logger.info(f"TestForge Servant initialized on {host}:{port}")
    
    async def initialize(self) -> bool:
        """サーバント初期化"""
        try:
            # エンジン初期化
            await self.test_engine.initialize()
            logger.info("TestForge Servant ready to forge quality")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            return False
    
    def _extract_data_from_message(self, message: Message) -> Dict[str, Any]:
        """メッセージからデータ抽出"""
        if isinstance(message.content, TextContent):
            text_content = message.content.text
            try:
                return json.loads(text_content)
            except json.JSONDecodeError:
                return {"target_path": text_content}
        else:
            raise ValueError("TextContent required")
    
    def _create_response_message(self, result: Dict[str, Any]) -> Message:
        """レスポンスメッセージ作成"""
        return Message(
            content=TextContent(text=json.dumps(result)),
            role=MessageRole.AGENT
        )
    
    @skill(name="verify_test_quality")
    async def verify_test_quality(self, message: Message) -> Message:
        """
        統合テスト品質コマンド - One Servant, One Command
        
        実行フロー:
        1. エンジンによる自動実行 (pytest, coverage, hypothesis, tox)
        2. サーバントによる専門判定
        3. TDD準拠・カバレッジ評価
        """
        try:
            # データ抽出
            data = self._extract_data_from_message(message)
            target_path = data.get("target_path", ".")
            
            self.total_verifications += 1
            logger.info(f"Verifying test quality for: {target_path}")
            
            # エンジン実行（自動化）
            engine_result = await self.test_engine.execute_full_test_suite(target_path)
            
            # サーバント判定（専門性）
            verdict = self._judge_test_quality(engine_result)
            
            # メトリクス更新
            if verdict["verdict"] == "APPROVED":
                if verdict.get("tdd_compliant", False):
                    self.tdd_compliant_count += 1
            else:
                if verdict.get("coverage", 0) < 95.0:
                    self.coverage_failures += 1
            
            # レスポンス作成
            response = {
                "servant": self.agent_name,
                "command": self.command,
                "target_path": target_path,
                "timestamp": datetime.now().isoformat(),
                **verdict
            }
            
            return self._create_response_message(response)
            
        except Exception as e:
            logger.error(f"Error in verify_test_quality: {e}")
            error_response = {
                "servant": self.agent_name,
                "command": self.command,
                "success": False,
                "error": str(e),
                "verdict": "ERROR"
            }
            return self._create_response_message(error_response)
    
    def _judge_test_quality(self, result) -> Dict[str, Any]:
        """
        純粋な判定ロジック - テスト品質の専門判定
        
        判定基準:
        - カバレッジ95%以上 + TDDスコア90以上: APPROVED
        - カバレッジ85%以上 + TDDスコア80以上: CONDITIONAL
        - それ以外: NEEDS_IMPROVEMENT
        """
        coverage = result.coverage_percentage
        tdd_score = result.tdd_quality_score
        test_failures = result.test_failures
        
        # TDD準拠チェック
        tdd_compliance = self._check_tdd_compliance(result)
        
        if coverage >= 95.0 and tdd_score >= 90.0 and test_failures == 0:
            return {
                "verdict": "APPROVED",
                "coverage": coverage,
                "tdd_score": tdd_score,
                "tdd_compliant": tdd_compliance["compliant"],
                "certification": "TDD_MASTER",
                "message": "Excellent test quality! TDD excellence achieved.",
                "details": {
                    "total_tests": result.total_tests,
                    "passed_tests": result.passed_tests,
                    "test_types": {
                        "unit": result.unit_test_count,
                        "integration": result.integration_test_count,
                        "property": result.property_test_count
                    },
                    "multi_env_tested": result.tox_environments_tested
                }
            }
        elif coverage >= 85.0 and tdd_score >= 80.0:
            improvements = self._get_test_improvements(result)
            return {
                "verdict": "CONDITIONAL",
                "coverage": coverage,
                "tdd_score": tdd_score,
                "tdd_compliant": tdd_compliance["compliant"],
                "certification": "TDD_PRACTITIONER",
                "message": "Good test quality, but improvements needed.",
                "requirements": improvements,
                "missing_coverage": self._analyze_missing_coverage(result),
                "command": f"{self.command} --generate-missing-tests"
            }
        else:
            critical_gaps = self._identify_test_gaps(result)
            return {
                "verdict": "NEEDS_IMPROVEMENT",
                "coverage": coverage,
                "tdd_score": tdd_score,
                "tdd_compliant": tdd_compliance["compliant"],
                "certification": "TDD_APPRENTICE",
                "message": "Test quality below standards. Major improvements required.",
                "critical_gaps": critical_gaps,
                "mandatory_actions": [
                    "Increase test coverage to 95%+",
                    "Write tests before implementation",
                    "Add property-based tests",
                    "Ensure all tests pass"
                ],
                "command": f"{self.command} --emergency-test-generation"
            }
    
    def _check_tdd_compliance(self, result) -> Dict[str, Any]:
        """TDD準拠チェック"""
        compliance_checks = {
            "tests_exist": result.total_tests > 0,
            "tests_first": result.test_to_code_ratio >= 1.0,
            "red_green_refactor": result.tdd_cycle_detected,
            "test_naming": result.test_naming_compliance >= 90.0,
            "assertions_quality": result.assertion_quality_score >= 85.0
        }
        
        compliant = all(compliance_checks.values())
        score = sum(1 for check in compliance_checks.values() if check) / len(compliance_checks) * 100
        
        return {
            "compliant": compliant,
            "score": score,
            "checks": compliance_checks
        }
    
    def _get_test_improvements(self, result) -> List[Dict[str, Any]]:
        """テスト改善要求事項の生成"""
        improvements = []
        
        if result.coverage_percentage < 95.0:
            improvements.append({
                "area": "Test Coverage",
                "current": f"{result.coverage_percentage}%",
                "target": "95%+",
                "action": "Add tests for uncovered code paths",
                "priority": "HIGH"
            })
        
        if result.property_test_count < 5:
            improvements.append({
                "area": "Property-Based Testing",
                "current": f"{result.property_test_count} tests",
                "target": "5+ tests",
                "action": "Add Hypothesis property tests",
                "priority": "MEDIUM"
            })
        
        if not result.tox_environments_tested:
            improvements.append({
                "area": "Multi-Environment Testing",
                "current": "Not tested",
                "target": "All Python versions",
                "action": "Configure and run tox",
                "priority": "MEDIUM"
            })
        
        if result.test_duplication_percentage > 10:
            improvements.append({
                "area": "Test Duplication",
                "current": f"{result.test_duplication_percentage}%",
                "target": "<10%",
                "action": "Refactor duplicate test code",
                "priority": "LOW"
            })
        
        return improvements
    
    def _analyze_missing_coverage(self, result) -> Dict[str, Any]:
        """カバレッジ不足箇所の分析"""
        return {
            "uncovered_lines": result.uncovered_lines,
            "uncovered_branches": result.uncovered_branches,
            "critical_paths": [
                {
                    "file": path["file"],
                    "lines": path["lines"],
                    "importance": path["importance"]
                }
                for path in result.critical_uncovered_paths[:5]  # Top 5
            ],
            "suggested_tests": result.suggested_test_cases
        }
    
    def _identify_test_gaps(self, result) -> List[Dict[str, Any]]:
        """テストギャップの特定"""
        gaps = []
        
        if result.coverage_percentage < 80:
            gaps.append({
                "severity": "CRITICAL",
                "gap": "Low Overall Coverage",
                "current": f"{result.coverage_percentage}%",
                "impact": "Major code paths untested"
            })
        
        if result.unit_test_count < result.function_count * 0.8:
            gaps.append({
                "severity": "HIGH",
                "gap": "Insufficient Unit Tests",
                "current": f"{result.unit_test_count} tests for {result.function_count} functions",
                "impact": "Functions not properly tested"
            })
        
        if result.edge_case_coverage < 50:
            gaps.append({
                "severity": "MEDIUM",
                "gap": "Poor Edge Case Coverage",
                "current": f"{result.edge_case_coverage}%",
                "impact": "Edge cases may cause failures"
            })
        
        if not result.integration_test_count:
            gaps.append({
                "severity": "MEDIUM",
                "gap": "No Integration Tests",
                "current": "0 tests",
                "impact": "Component interactions untested"
            })
        
        return gaps
    
    @skill(name="generate_test_strategy")
    async def generate_test_strategy(self, message: Message) -> Message:
        """テスト戦略生成スキル"""
        try:
            data = self._extract_data_from_message(message)
            target_path = data.get("target_path", ".")
            
            # コード分析に基づくテスト戦略生成
            strategy = await self._create_optimal_test_strategy(target_path)
            
            return self._create_response_message({
                "success": True,
                "strategy": strategy
            })
            
        except Exception as e:
            logger.error(f"Error generating test strategy: {e}")
            return self._create_response_message({
                "success": False,
                "error": str(e)
            })
    
    async def _create_optimal_test_strategy(self, target_path: str) -> Dict[str, Any]:
        """最適なテスト戦略の生成"""
        # エンジンでコード分析
        analysis = await self.test_engine.analyze_code_structure(target_path)
        
        return {
            "test_pyramid": {
                "unit_tests": {
                    "target_percentage": 70,
                    "focus_areas": analysis.get("complex_functions", []),
                    "tools": ["pytest", "pytest-mock"]
                },
                "integration_tests": {
                    "target_percentage": 20,
                    "focus_areas": analysis.get("external_dependencies", []),
                    "tools": ["pytest", "pytest-asyncio"]
                },
                "e2e_tests": {
                    "target_percentage": 10,
                    "focus_areas": analysis.get("user_workflows", []),
                    "tools": ["pytest", "pytest-bdd"]
                }
            },
            "coverage_targets": {
                "line_coverage": 95,
                "branch_coverage": 90,
                "function_coverage": 100
            },
            "special_considerations": {
                "property_testing": analysis.get("data_processing_functions", []),
                "performance_testing": analysis.get("performance_critical", []),
                "security_testing": analysis.get("security_sensitive", [])
            },
            "implementation_order": [
                "Critical business logic",
                "Data validation functions",
                "API endpoints",
                "Error handling paths",
                "Edge cases"
            ]
        }
    
    @skill(name="health_check")
    async def health_check(self, message: Message) -> Message:
        """ヘルスチェックスキル"""
        health_status = {
            "status": "healthy",
            "servant": self.agent_name,
            "port": self.port,
            "uptime": "operational",
            "metrics": {
                "total_verifications": self.total_verifications,
                "tdd_compliant": self.tdd_compliant_count,
                "coverage_failures": self.coverage_failures,
                "tdd_compliance_rate": (
                    self.tdd_compliant_count / self.total_verifications * 100
                    if self.total_verifications > 0 else 0
                )
            }
        }
        return self._create_response_message(health_status)
    
    async def shutdown(self):
        """サーバント終了処理"""
        logger.info(f"TestForge Servant shutting down. Total verifications: {self.total_verifications}")


# === サーバント実行スクリプト ===

async def main():
    """TestForge サーバント起動"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    servant = TestForgeServant()
    
    try:
        if await servant.initialize():
            print(f"🔨 Starting TestForge Servant on port {servant.port}...")
            # Note: 実際のpython-a2a実装では run_server を使用
            await asyncio.Event().wait()  # Keep running
        else:
            print("❌ Failed to initialize TestForge Servant")
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested")
    finally:
        await servant.shutdown()
        print("✅ TestForge Servant stopped")


if __name__ == "__main__":
    asyncio.run(main())