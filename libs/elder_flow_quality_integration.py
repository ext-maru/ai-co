#!/usr/bin/env python3
"""
Elder Flow品質エンジン統合システム
エルダーループ Phase 3: 実装

3つの品質エンジンをElder Flow Phase 3 (品質ゲート)に統合

統合対象:
- StaticAnalysisEngine: 静的解析・コード品質チェック
- TestAutomationEngine: テスト自動実行・TDD支援
- ComprehensiveQualityEngine: 包括的品質評価・レポート生成

Created: 2025-07-24
Author: Claude Elder
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from libs.quality.static_analysis_engine import StaticAnalysisEngine
from libs.quality.test_automation_engine import TestAutomationEngine
from libs.quality.comprehensive_quality_engine import ComprehensiveQualityEngine


logger = logging.getLogger(__name__)


class ElderFlowQualityIntegration:
    """Elder Flow品質エンジン統合システム"""

    def __init__(self):
        """初期化"""
        self.static_engine = StaticAnalysisEngine()
        self.test_engine = TestAutomationEngine()
        self.comprehensive_engine = ComprehensiveQualityEngine()

    async def execute_integrated_quality_check(
        self, 
        task_context: Dict[str, Any],
        implementation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        統合品質チェック実行
        
        Args:
            task_context: タスクコンテキスト（task_name, priority, flow_id等）
            implementation_results: 実装結果（修正ファイル等）
            
        Returns:
            Dict[str, Any]: 統合された品質チェック結果
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🔍 Elder Flow統合品質チェック開始: {task_context.get('task_name', 'Unknown')}")
            
            # プロジェクトパスの取得
            project_path = self._get_project_path(task_context, implementation_results)
            modified_files = implementation_results.get("files_modified", [])
            
            # Phase 3.1: 静的解析実行
            logger.info("📊 Phase 3.1: 静的解析エンジン実行")
            static_results = await self._execute_static_analysis(
                project_path, modified_files, task_context
            )
            
            # Phase 3.2: テスト自動化実行
            logger.info("🧪 Phase 3.2: テスト自動化エンジン実行")
            test_results = await self._execute_test_automation(
                project_path, modified_files, task_context
            )
            
            # Phase 3.3: 包括的品質評価実行
            logger.info("🏆 Phase 3.3: 包括的品質エンジン実行")
            comprehensive_results = await self._execute_comprehensive_quality(
                project_path, static_results, test_results, task_context
            )
            
            # 結果統合
            integrated_results = self._integrate_results(
                static_results, test_results, comprehensive_results, 
                start_time, task_context
            )
            
            logger.info(f"✅ Elder Flow統合品質チェック完了: スコア {integrated_results['overall_quality_score']}")
            
            return integrated_results
            
        except Exception as e:
            logger.error(f"❌ Elder Flow統合品質チェックエラー: {e}")
            return self._create_error_result(str(e), start_time, task_context)

    async def _execute_static_analysis(
        self, project_path: str, modified_files: List[str], task_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """静的解析エンジン実行"""
        try:
            # 静的解析実行
            analysis_result = await self.static_engine.execute_full_pipeline(project_path)
            
            # Elder Flow統合用の結果構造に変換
            # StaticAnalysisResultオブジェクトをdictに変換
            if hasattr(analysis_result, '__dict__'):
                result_dict = analysis_result.__dict__
            else:
                result_dict = analysis_result
                
            return {
                "engine": "StaticAnalysisEngine",
                "status": "success",
                "analysis_result": result_dict,
                "modified_files_analyzed": len(modified_files),
                "iron_will_compliance": result_dict.get("summary", {}).get("iron_will_compliance", {}),
                "quality_score": result_dict.get("pylint_score", 0)
            }
            
        except Exception as e:
            logger.warning(f"静的解析エンジンエラー: {e}")
            return {
                "engine": "StaticAnalysisEngine",
                "status": "error",
                "error": str(e),
                "quality_score": 0
            }

    async def _execute_test_automation(
        self, project_path: str, modified_files: List[str], task_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """テスト自動化エンジン実行"""
        try:
            # テスト自動実行
            test_result = await self.test_engine.execute_full_pipeline(project_path)
            
            # Elder Flow統合用の結果構造に変換
            # TestExecutionResultオブジェクトをdictに変換
            if hasattr(test_result, '__dict__'):
                result_dict = test_result.__dict__
            else:
                result_dict = test_result
                
            return {
                "engine": "TestAutomationEngine", 
                "status": "success",
                "test_result": result_dict,
                "tests_executed": result_dict.get("tests_executed", 0),
                "coverage_percentage": result_dict.get("coverage_percentage", 0),
                "tdd_compliance": result_dict.get("summary", {}).get("tdd_compliance", {}),
                "quality_score": result_dict.get("coverage_percentage", 0)  # テストカバレッジをスコアとして使用
            }
            
        except Exception as e:
            logger.warning(f"テスト自動化エンジンエラー: {e}")
            return {
                "engine": "TestAutomationEngine",
                "status": "error", 
                "error": str(e),
                "quality_score": 0
            }

    async def _execute_comprehensive_quality(
        self, 
        project_path: str, 
        static_results: Dict[str, Any], 
        test_results: Dict[str, Any],
        task_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """包括的品質エンジン実行"""
        try:
            # 包括的品質評価実行
            quality_result = await self.comprehensive_engine.execute_full_pipeline(project_path)
            
            # Elder Flow統合用の結果構造に変換
            # ComprehensiveQualityResultオブジェクトをdictに変換
            if hasattr(quality_result, '__dict__'):
                result_dict = quality_result.__dict__
            else:
                result_dict = quality_result
                
            return {
                "engine": "ComprehensiveQualityEngine",
                "status": "success",
                "quality_result": result_dict,
                "graduation_eligible": result_dict.get("graduation_eligible", False),
                "overall_score": result_dict.get("overall_score", 0),
                "elder_council_report": result_dict.get("elder_council_report", {}),
                "quality_score": result_dict.get("overall_score", 0)
            }
            
        except Exception as e:
            logger.warning(f"包括的品質エンジンエラー: {e}")
            return {
                "engine": "ComprehensiveQualityEngine",
                "status": "error",
                "error": str(e), 
                "quality_score": 0
            }

    def _integrate_results(
        self,
        static_results: Dict[str, Any],
        test_results: Dict[str, Any], 
        comprehensive_results: Dict[str, Any],
        start_time: datetime,
        task_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """結果統合"""
        
        # 全体品質スコア計算（加重平均）
        scores = []
        weights = []
        
        if static_results.get("status") == "success":
            scores.append(static_results.get("quality_score", 0))
            weights.append(0.3)  # 静的解析: 30%
            
        if test_results.get("status") == "success":
            scores.append(test_results.get("quality_score", 0))
            weights.append(0.4)  # テスト: 40%
            
        if comprehensive_results.get("status") == "success":
            scores.append(comprehensive_results.get("quality_score", 0))
            weights.append(0.3)  # 包括評価: 30%
        
        # 加重平均計算
        if scores and weights:
            overall_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        else:
            overall_score = 0
            
        # Iron Will準拠チェック
        iron_will_compliance = self._check_iron_will_compliance(
            static_results, test_results, comprehensive_results
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "integration_status": "success",
            "execution_time_seconds": execution_time,
            "task_context": task_context,
            
            # 各エンジンの結果
            "static_analysis_report": static_results,
            "test_automation_report": test_results,
            "comprehensive_quality_report": comprehensive_results,
            
            # 統合結果
            "overall_quality_score": round(overall_score, 2),
            "iron_will_compliance": iron_will_compliance,
            "engines_executed": 3,
            "engines_successful": sum(1 for r in [static_results, test_results, comprehensive_results] 
                                     if r.get("status") == "success"),
            
            # Elder Flow統合情報
            "elder_flow_integration": {
                "phase": "Phase 3: Quality Gate",
                "integrated_engines": ["StaticAnalysisEngine", "TestAutomationEngine", "ComprehensiveQualityEngine"],
                "integration_version": "1.0.0"
            },
            
            # 品質判定
            "quality_assessment": self._assess_quality(overall_score, iron_will_compliance),
            
            # 次段階推奨
            "recommendations": self._generate_recommendations(
                static_results, test_results, comprehensive_results, overall_score
            )
        }

    def _check_iron_will_compliance(
        self, static_results: Dict[str, Any], test_results: Dict[str, Any], 
        comprehensive_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Iron Will準拠チェック"""
        
        compliance_checks = {
            "static_analysis_passed": static_results.get("iron_will_compliance", {}).get("passed", False),
            "test_coverage_adequate": test_results.get("coverage_percentage", 0) >= 90,
            "tdd_compliance": test_results.get("tdd_compliance", {}).get("passed", False),
            "overall_quality_threshold": comprehensive_results.get("overall_score", 0) >= 95
        }
        
        overall_compliance = all(compliance_checks.values())
        
        return {
            "overall_compliance": overall_compliance,
            "individual_checks": compliance_checks,
            "compliance_score": sum(compliance_checks.values()) / len(compliance_checks) * 100
        }

    def _assess_quality(self, overall_score: float, iron_will_compliance: Dict[str, Any]) -> Dict[str, Any]:
        """品質判定"""
        
        if overall_score >= 95 and iron_will_compliance.get("overall_compliance", False):
            level = "EXCELLENT"
            action = "Phase 4 (評議会報告) 進行可能"
        elif overall_score >= 85:
            level = "GOOD"
            action = "軽微な改善後Phase 4進行"
        elif overall_score >= 70:
            level = "ACCEPTABLE"
            action = "改善が必要、Phase 4進行は注意"
        else:
            level = "INSUFFICIENT"
            action = "重大な改善が必要、Phase 4進行停止"
            
        return {
            "quality_level": level,
            "score": overall_score,
            "next_action": action,
            "elder_council_approval": level in ["EXCELLENT", "GOOD"]
        }

    def _generate_recommendations(
        self, static_results: Dict[str, Any], test_results: Dict[str, Any],
        comprehensive_results: Dict[str, Any], overall_score: float
    ) -> List[str]:
        """改善推奨事項生成"""
        
        recommendations = []
        
        # 静的解析の推奨
        if static_results.get("status") == "success":
            if static_results.get("quality_score", 0) < 85:
                recommendations.append("🔧 静的解析の品質改善: コード複雑度削減、PEP8準拠")
        else:
            recommendations.append("❌ 静的解析エラー修復が必要")
            
        # テストの推奨  
        if test_results.get("status") == "success":
            coverage = test_results.get("coverage_percentage", 0)
            if coverage < 90:
                recommendations.append(f"🧪 テストカバレッジ向上: {coverage}% → 90%以上")
        else:
            recommendations.append("❌ テスト実行エラー修復が必要")
            
        # 包括評価の推奨
        if comprehensive_results.get("status") == "success":
            if not comprehensive_results.get("graduation_eligible", False):
                recommendations.append("🎓 品質卒業基準未達成: 包括的改善が必要")
        else:
            recommendations.append("❌ 包括品質評価エラー修復が必要")
            
        # 全体スコアの推奨
        if overall_score < 95:
            recommendations.append(f"📈 全体品質向上: {overall_score:.1f} → 95以上 (Iron Will基準)")
            
        return recommendations

    def _get_project_path(self, task_context: Dict[str, Any], implementation_results: Dict[str, Any]) -> str:
        """プロジェクトパス取得"""
        # task_contextから取得を試行
        if "project_path" in task_context:
            return task_context["project_path"]
            
        # 実装結果から推測
        modified_files = implementation_results.get("files_modified", [])
        if modified_files:
            # 最初のファイルの親ディレクトリを取得
            first_file = Path(modified_files[0])
            return str(first_file.parent.parent)  # libs/quality → ai_co
            
        # デフォルト: 現在のワーキングディレクトリ
        return str(Path.cwd())

    def _create_error_result(self, error_message: str, start_time: datetime, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """エラー結果作成"""
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "integration_status": "error",
            "error": error_message,
            "execution_time_seconds": execution_time,
            "task_context": task_context,
            "overall_quality_score": 0,
            "iron_will_compliance": {
                "overall_compliance": False,
                "compliance_score": 0
            },
            "quality_assessment": {
                "quality_level": "ERROR",
                "score": 0,
                "next_action": "エラー修復が必要",
                "elder_council_approval": False
            },
            "recommendations": ["❌ 統合品質チェックのエラー修復が必要"]
        }

    # 各エンジンにElder Flow統合インターフェースを追加する補助メソッド
    
    def add_elder_flow_interface_to_engines(self):
        """
        既存エンジンにElder Flow統合インターフェースを動的に追加
        
        これにより、テストで期待される elder_flow_execute メソッドが利用可能になる
        """
        
        # StaticAnalysisEngine用インターフェース追加
        def static_elder_flow_execute(project_path: str, task_context: Dict[str, Any]) -> Dict[str, Any]:
            try:
                # 非同期メソッドを同期で実行（Elder Flow統合のため）
                import asyncio
                result = asyncio.run(self.static_engine.execute_full_pipeline(project_path))
                # StaticAnalysisResultオブジェクトをdictに変換
                if hasattr(result, '__dict__'):
                    return result.__dict__
                return result
            except Exception as e:
                return {"error": str(e), "status": "ERROR"}
        
        # TestAutomationEngine用インターフェース追加
        def test_elder_flow_execute(project_path: str, task_context: Dict[str, Any]) -> Dict[str, Any]:
            try:
                # 非同期メソッドを同期で実行（Elder Flow統合のため）
                import asyncio
                return asyncio.run(self.test_engine.execute_full_pipeline(project_path))
            except Exception as e:
                return {"error": str(e), "status": "ERROR"}
        
        # ComprehensiveQualityEngine用インターフェース追加  
        def comprehensive_elder_flow_execute(
            project_path: str, task_context: Dict[str, Any], 
            static_results: Dict[str, Any] = None, test_results: Dict[str, Any] = None
        ) -> Dict[str, Any]:
            try:
                # 非同期メソッドを同期で実行（Elder Flow統合のため）
                import asyncio
                return asyncio.run(self.comprehensive_engine.execute_full_pipeline(project_path))
            except Exception as e:
                return {"error": str(e), "status": "ERROR"}
        
        # 動的にメソッドを追加
        self.static_engine.elder_flow_execute = static_elder_flow_execute
        self.test_engine.elder_flow_execute = test_elder_flow_execute  
        self.comprehensive_engine.elder_flow_execute = comprehensive_elder_flow_execute
        
        logger.info("✅ Elder Flow統合インターフェースを3つの品質エンジンに追加しました")

    def get_integration_info(self) -> Dict[str, Any]:
        """統合情報取得"""
        return {
            "integration_name": "Elder Flow Quality Engines Integration",
            "version": "1.0.0",
            "engines": [
                {
                    "name": "StaticAnalysisEngine",
                    "version": "1.0.0",
                    "capabilities": ["静的解析", "コード品質", "Iron Will準拠チェック"]
                },
                {
                    "name": "TestAutomationEngine", 
                    "version": "1.0.0",
                    "capabilities": ["自動テスト", "カバレッジ分析", "TDD支援"]
                },
                {
                    "name": "ComprehensiveQualityEngine",
                    "version": "1.0.0", 
                    "capabilities": ["包括品質評価", "卒業判定", "Elder Council レポート"]
                }
            ],
            "integration_phase": "Elder Flow Phase 3: Quality Gate",
            "created": "2025-07-24",
            "author": "Claude Elder"
        }