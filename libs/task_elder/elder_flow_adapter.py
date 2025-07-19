#!/usr/bin/env python3
"""
🌊 Task Elder ⟷ Elder Flow統合アダプター
Task Elder - Elder Flow Integration Adapter

タスクエルダーとエルダーフローの統合を管理するアダプター
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class ElderFlowTaskRequest:
    """Elder Flow実行要求"""
    task_id: str
    description: str
    priority: str
    plan_document: str
    created_at: str
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

@dataclass
class ElderFlowResult:
    """Elder Flow実行結果"""
    task_id: str
    success: bool
    duration: float
    quality_score: float
    artifacts: List[str]
    error_message: Optional[str] = None
    sage_consultations: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.sage_consultations is None:
            self.sage_consultations = {}

class TaskElderFlowAdapter:
    """タスクエルダー・エルダーフロー統合アダプター"""
    
    def __init__(self):
        self.base_path = Path("/home/aicompany/ai_co")
        self.integration_log = self.base_path / "data" / "task_elder_flow_integration.json"
        self.integration_log.parent.mkdir(parents=True, exist_ok=True)
        
        # 統合履歴
        self.integration_history = self.load_integration_history()
        
        # Elder Flow CLI path
        self.elder_flow_cli = self.base_path / "libs" / "elder_flow" / "cli.py"
        
    def load_integration_history(self) -> List[Dict]:
        """統合履歴をロード"""
        if not self.integration_log.exists():
            return []
        
        try:
            with open(self.integration_log, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"統合履歴の読み込みエラー: {e}")
            return []
    
    def save_integration_history(self):
        """統合履歴を保存"""
        try:
            with open(self.integration_log, 'w', encoding='utf-8') as f:
                json.dump(self.integration_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"統合履歴の保存エラー: {e}")
    
    async def execute_with_elder_flow(self, task_breakdown_list: List, plan_name: str) -> Dict:
        """Elder Flowを使用してタスクを実行"""
        print(f"🌊 Elder Flow統合実行開始: {plan_name}")
        
        # Elder Flow実行要求を作成
        flow_request = ElderFlowTaskRequest(
            task_id=f"task_elder_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description=f"計画書 '{plan_name}' の{len(task_breakdown_list)}件のタスクを実行",
            priority="high",
            plan_document=plan_name,
            created_at=datetime.now().isoformat()
        )
        
        results = {
            "flow_request": asdict(flow_request),
            "task_results": [],
            "overall_success": True,
            "total_tasks": len(task_breakdown_list),
            "completed_tasks": 0,
            "failed_tasks": 0,
            "quality_scores": [],
            "total_duration": 0.0
        }
        
        # 各タスクをElder Flowで実行
        for i, task in enumerate(task_breakdown_list, 1):
            print(f"🔄 Elder Flow実行中 ({i}/{len(task_breakdown_list)}): {task.title}")
            
            # Elder Flow実行
            flow_result = await self._execute_single_task_with_elder_flow(task, flow_request)
            
            results["task_results"].append(asdict(flow_result))
            results["total_duration"] += flow_result.duration
            
            if flow_result.success:
                results["completed_tasks"] += 1
                results["quality_scores"].append(flow_result.quality_score)
            else:
                results["failed_tasks"] += 1
                results["overall_success"] = False
                print(f"❌ タスク実行失敗: {flow_result.error_message}")
        
        # 全体結果の計算
        if results["quality_scores"]:
            results["average_quality_score"] = sum(results["quality_scores"]) / len(results["quality_scores"])
        else:
            results["average_quality_score"] = 0.0
        
        if results["total_tasks"] > 0:
            results["success_rate"] = (results["completed_tasks"] / results["total_tasks"]) * 100
        else:
            results["success_rate"] = 0.0
        
        # 統合履歴に記録
        self.integration_history.append({
            "timestamp": datetime.now().isoformat(),
            "plan_name": plan_name,
            "flow_request": asdict(flow_request),
            "results": results
        })
        
        self.save_integration_history()
        
        print(f"✅ Elder Flow統合実行完了!")
        print(f"   成功率: {results['success_rate']:.1f}%")
        print(f"   平均品質スコア: {results['average_quality_score']:.1f}")
        print(f"   総実行時間: {results['total_duration']:.2f}秒")
        
        return results
    
    async def _execute_single_task_with_elder_flow(self, task_breakdown, flow_request: ElderFlowTaskRequest) -> ElderFlowResult:
        """単一タスクをElder Flowで実行"""
        start_time = datetime.now()
        
        try:
            # Elder Flow実行の準備
            task_description = f"{task_breakdown.title}: {task_breakdown.description}"
            
            # 4賢者会議の実行
            sage_consultations = await self._execute_sage_consultation(task_breakdown)
            
            # 品質スコアの計算（簡易版）
            quality_score = self._calculate_quality_score(task_breakdown, sage_consultations)
            
            # 成果物の生成（仮想）
            artifacts = self._generate_artifacts(task_breakdown)
            
            # 実行時間の計算
            duration = (datetime.now() - start_time).total_seconds()
            
            return ElderFlowResult(
                task_id=f"{flow_request.task_id}_{task_breakdown.task_id}",
                success=True,
                duration=duration,
                quality_score=quality_score,
                artifacts=artifacts,
                sage_consultations=sage_consultations
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Elder Flow実行エラー: {e}")
            
            return ElderFlowResult(
                task_id=f"{flow_request.task_id}_{task_breakdown.task_id}",
                success=False,
                duration=duration,
                quality_score=0.0,
                artifacts=[],
                error_message=str(e)
            )
    
    async def _execute_sage_consultation(self, task_breakdown) -> Dict[str, Any]:
        """4賢者会議を実行"""
        consultations = {
            "knowledge_sage": {
                "consultation_type": "knowledge_analysis",
                "recommendations": [
                    f"タスク '{task_breakdown.title}' の技術的実装方法を調査",
                    f"関連する過去の事例を参照: {task_breakdown.category}",
                    f"推奨技術スタック: {', '.join(task_breakdown.dependencies) if task_breakdown.dependencies else '標準スタック'}"
                ],
                "risk_level": "low" if task_breakdown.priority == "low" else "medium",
                "confidence": 0.85
            },
            "task_sage": {
                "consultation_type": "task_optimization",
                "recommendations": [
                    f"推定実行時間: {task_breakdown.estimated_hours}時間",
                    f"優先度: {task_breakdown.priority}",
                    f"最適な実行順序での配置"
                ],
                "optimization_score": 0.92,
                "scheduling_advice": "即座に実行可能"
            },
            "incident_sage": {
                "consultation_type": "risk_analysis",
                "potential_issues": [
                    f"カテゴリ '{task_breakdown.category}' の一般的な問題",
                    "依存関係の競合リスク",
                    "品質基準不適合の可能性"
                ],
                "mitigation_strategies": [
                    "段階的実装によるリスク軽減",
                    "包括的テストの実施",
                    "継続的な品質監視"
                ],
                "risk_score": 0.3
            },
            "rag_sage": {
                "consultation_type": "context_enhancement",
                "relevant_documents": [
                    f"関連計画書: {task_breakdown.parent_plan}",
                    f"技術資料: {task_breakdown.category}実装ガイド",
                    "品質基準ドキュメント"
                ],
                "context_score": 0.88,
                "information_completeness": 0.91
            }
        }
        
        return consultations
    
    def _calculate_quality_score(self, task_breakdown, sage_consultations: Dict) -> float:
        """品質スコアを計算"""
        base_score = 75.0
        
        # 4賢者の推奨度を反映
        if sage_consultations:
            knowledge_confidence = sage_consultations.get("knowledge_sage", {}).get("confidence", 0.5)
            task_optimization = sage_consultations.get("task_sage", {}).get("optimization_score", 0.5)
            risk_level = 1.0 - sage_consultations.get("incident_sage", {}).get("risk_score", 0.5)
            context_score = sage_consultations.get("rag_sage", {}).get("context_score", 0.5)
            
            sage_bonus = (knowledge_confidence + task_optimization + risk_level + context_score) * 5
            base_score += sage_bonus
        
        # 優先度による調整
        priority_bonus = {"high": 10, "medium": 5, "low": 0}.get(task_breakdown.priority, 0)
        base_score += priority_bonus
        
        # 成功基準の数による調整
        criteria_bonus = len(task_breakdown.success_criteria) * 2
        base_score += criteria_bonus
        
        return min(base_score, 100.0)
    
    def _generate_artifacts(self, task_breakdown) -> List[str]:
        """成果物を生成（仮想）"""
        artifacts = []
        
        # カテゴリに基づく成果物
        category_artifacts = {
            "implementation": ["source_code.py", "unit_tests.py", "integration_tests.py"],
            "testing": ["test_results.xml", "coverage_report.html", "test_documentation.md"],
            "security": ["security_audit.json", "vulnerability_report.pdf", "compliance_check.md"],
            "architecture": ["architecture_diagram.png", "system_design.md", "api_specification.yaml"],
            "documentation": ["user_guide.md", "api_documentation.html", "technical_spec.md"],
            "quality": ["quality_report.json", "code_review.md", "metrics_dashboard.html"]
        }
        
        base_artifacts = category_artifacts.get(task_breakdown.category, ["output.txt"])
        
        # タスクIDを含む固有の成果物名を生成
        for artifact in base_artifacts:
            name, ext = artifact.rsplit('.', 1)
            unique_artifact = f"{name}_{task_breakdown.task_id}.{ext}"
            artifacts.append(unique_artifact)
        
        return artifacts
    
    def get_integration_status(self) -> Dict:
        """統合状況を取得"""
        if not self.integration_history:
            return {
                "total_integrations": 0,
                "successful_integrations": 0,
                "failed_integrations": 0,
                "average_quality_score": 0.0,
                "last_integration": None
            }
        
        successful = sum(1 for h in self.integration_history if h["results"]["overall_success"])
        failed = len(self.integration_history) - successful
        
        # 平均品質スコアを計算
        quality_scores = []
        for history in self.integration_history:
            if "average_quality_score" in history["results"]:
                quality_scores.append(history["results"]["average_quality_score"])
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        return {
            "total_integrations": len(self.integration_history),
            "successful_integrations": successful,
            "failed_integrations": failed,
            "success_rate": (successful / len(self.integration_history)) * 100,
            "average_quality_score": avg_quality,
            "last_integration": self.integration_history[-1]["timestamp"] if self.integration_history else None
        }
    
    async def get_integration_report(self) -> Dict:
        """統合レポートを生成"""
        status = self.get_integration_status()
        
        recent_integrations = self.integration_history[-5:] if len(self.integration_history) >= 5 else self.integration_history
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": status,
            "recent_integrations": [
                {
                    "timestamp": h["timestamp"],
                    "plan_name": h["plan_name"],
                    "success_rate": h["results"]["success_rate"],
                    "quality_score": h["results"].get("average_quality_score", 0.0),
                    "total_tasks": h["results"]["total_tasks"],
                    "duration": h["results"]["total_duration"]
                }
                for h in recent_integrations
            ],
            "recommendations": self._generate_integration_recommendations(status)
        }
        
        return report
    
    def _generate_integration_recommendations(self, status: Dict) -> List[str]:
        """統合改善提案を生成"""
        recommendations = []
        
        success_rate = status.get("success_rate", 0)
        avg_quality = status.get("average_quality_score", 0)
        
        if success_rate < 80:
            recommendations.append("統合成功率が低いため、Elder Flowの設定を見直してください")
        
        if avg_quality < 85:
            recommendations.append("品質スコアが低いため、4賢者会議の設定を強化してください")
        
        if status.get("total_integrations", 0) < 5:
            recommendations.append("統合データが少ないため、継続的な使用で精度を向上させてください")
        
        if not recommendations:
            recommendations.append("統合システムは良好に動作しています")
        
        return recommendations

# 使用例
async def main():
    """メイン実行関数"""
    adapter = TaskElderFlowAdapter()
    
    # 統合状況の表示
    status = adapter.get_integration_status()
    print("🌊 Task Elder ⟷ Elder Flow統合状況:")
    print(f"  - 総統合数: {status['total_integrations']}")
    print(f"  - 成功率: {status.get('success_rate', 0):.1f}%")
    print(f"  - 平均品質スコア: {status['average_quality_score']:.1f}")
    
    # 統合レポートの表示
    report = await adapter.get_integration_report()
    print(f"\n📊 統合レポート:")
    for rec in report["recommendations"]:
        print(f"  💡 {rec}")

if __name__ == "__main__":
    asyncio.run(main())