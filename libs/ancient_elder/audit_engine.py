"""
🏛️ Ancient Elder Audit Engine
6つの古代魔法を統合する監査エンジン
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# プロジェクトルートをパスに追加
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.ancient_elder.base import AncientElderBase, AuditResult, ViolationSeverity


class AncientElderAuditEngine:
    """6つの古代魔法を統合する監査エンジン"""
    
    def __init__(self):
        self.logger = logging.getLogger("AncientElderAuditEngine")
        
        # 監査者の辞書（実装時に各監査者を追加）
        self.auditors: Dict[str, AncientElderBase] = {}
        
        # 監査結果の履歴
        self.audit_history: List[Dict[str, Any]] = []
        
        # 総合スコアリングの重み
        self.score_weights = {
            "integrity": 40,      # 誠実性（最重要）
            "process": 25,        # プロセス遵守
            "quality": 20,        # 品質基準
            "collaboration": 15   # 協調性
        }
        
        # 違反の重みづけ
        self.violation_weights = {
            ViolationSeverity.CRITICAL: -50,  # 即座に不合格
            ViolationSeverity.HIGH: -20,      # 大幅減点
            ViolationSeverity.MEDIUM: -5,     # 中程度減点
            ViolationSeverity.LOW: -1         # 軽微な減点
        }
        
    def register_auditor(self, key: str, auditor: AncientElderBase):
        """
        監査者を登録
        
        Args:
            key: 監査者のキー
            auditor: 監査者インスタンス
        """
        self.auditors[key] = auditor
        self.logger.info(f"Registered auditor: {key} - {auditor.name}")
        
    async def run_comprehensive_audit(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """
        包括的な監査を実行
        
        Args:
            target: 監査対象
            
        Returns:
            Dict: 統合監査結果
        """
        try:
            start_time = datetime.now()
            
            # 各監査者で並行監査を実行
            audit_tasks = []
            for key, auditor in self.auditors.items():
                task = asyncio.create_task(self._run_single_audit(key, auditor, target))
                audit_tasks.append(task)
                
            # 全監査の完了を待つ
            audit_results = await asyncio.gather(*audit_tasks, return_exceptions=True)
            
            # 結果を整理
            individual_results = {}
            all_violations = []
            failed_audits = []
            
            for i, (key, _) in enumerate(self.auditors.items()):
                result = audit_results[i]
                if isinstance(result, Exception):
                    failed_audits.append({
                        "auditor": key,
                        "error": str(result)
                    })
                    self.logger.error(f"Audit failed for {key}: {result}")
                else:
                    individual_results[key] = result
                    if result.get("violations"):
                        all_violations.extend(result["violations"])
                        
            # 総合スコアを計算
            guild_health_score = self._calculate_guild_health_score(all_violations)
            
            # 総合評価
            comprehensive_result = {
                "timestamp": start_time.isoformat(),
                "duration": (datetime.now() - start_time).total_seconds(),
                "auditors_run": len(self.auditors),
                "auditors_failed": len(failed_audits),
                "individual_results": individual_results,
                "total_violations": len(all_violations),
                "violation_breakdown": self._get_violation_breakdown(all_violations),
                "guild_health_score": guild_health_score,
                "evaluation": self._evaluate_health_score(guild_health_score),
                "failed_audits": failed_audits,
                "recommendations": self._generate_recommendations(
                    all_violations,
                    guild_health_score
                )
            }
            
            # 履歴に追加
            self.audit_history.append(comprehensive_result)
            
            # 戻り値の形式を統一
            comprehensive_result["all_violations"] = all_violations
            comprehensive_result["statistics"] = {
                "total_auditors": len(self.auditors),
                "successful_audits": len(individual_results),
                "failed_audits": len(failed_audits),
                "total_violations": len(all_violations)
            }
            comprehensive_result["execution_time"] = comprehensive_result.pop("duration", 0)
            
            return comprehensive_result
            
        except Exception as e:
            self.logger.error(f"Comprehensive audit failed: {str(e)}")
            return {
                "status": "error",
                "message": f"Audit engine error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            
    async def _run_single_audit(
        self,
        key: str,
        auditor: AncientElderBase,
        target: Dict[str,
        Any]
    ) -> Dict[str, Any]:
        """
        単一の監査を実行
        
        Args:
            key: 監査者のキー
            auditor: 監査者
            target: 監査対象
            
        Returns:
            Dict: 監査結果
        """
        try:
            # 監査を実行
            result = await auditor.process_request({
                "type": "audit",
                "target": target
            })
            
            if result.get("status") == "success":
                return {
                    "auditor": key,
                    "summary": result.get("result", {}),
                    "violations": result.get("violations", []),
                    "alerts": result.get("alerts", [])
                }
            else:
                raise Exception(result.get("message", "Unknown error"))
                
        except Exception as e:
            self.logger.error(f"Single audit failed for {key}: {str(e)}")
            raise
            
    def _calculate_guild_health_score(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        ギルドの健全性スコアを計算
        
        Args:
            violations: 全違反のリスト
            
        Returns:
            Dict: スコアの詳細
        """
        # 基本スコア（100点満点）
        base_score = 100.0
        
        # カテゴリー別のスコア
        category_scores = {
            "integrity": 100.0,
            "process": 100.0,
            "quality": 100.0,
            "collaboration": 100.0
        }
        
        # 違反による減点を計算
        for violation in violations:
            severity = ViolationSeverity[violation["severity"]]
            weight = self.violation_weights[severity]
            
            # 違反のカテゴリーを判定（メタデータから）
            category = violation.get("metadata", {}).get("category", "quality")
            if category in category_scores:
                category_scores[category] += weight
                category_scores[category] = max(0, category_scores[category])
                
        # 重み付け総合スコアを計算
        total_weight = sum(self.score_weights.values())
        weighted_score = 0
        
        for category, score in category_scores.items():
            weight = self.score_weights.get(category, 0)
            weighted_score += (score * weight) / total_weight
            
        return {
            "total_score": round(weighted_score, 2),
            "category_scores": {k: round(v, 2) for k, v in category_scores.items()},
            "score_weights": self.score_weights
        }
        
    def _get_violation_breakdown(self, violations: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        違反の内訳を取得
        
        Args:
            violations: 違反のリスト
            
        Returns:
            Dict: 重要度別の違反数
        """
        breakdown = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0
        }
        
        for violation in violations:
            severity = violation.get("severity", "LOW")
            if severity in breakdown:
                breakdown[severity] += 1
                
        return breakdown
        
    def _evaluate_health_score(self, health_score: Dict[str, Any]) -> str:
        """
        健全性スコアを評価
        
        Args:
            health_score: スコアの詳細
            
        Returns:
            str: 評価結果
        """
        total_score = health_score["total_score"]
        
        if total_score >= 90:
            return "EXCELLENT - エルダーズギルドは健全に機能しています"
        elif total_score >= 75:
            return "GOOD - 軽微な改善点があります"
        elif total_score >= 60:
            return "FAIR - 複数の改善が必要です"
        elif total_score >= 40:
            return "POOR - 重大な問題があります"
        else:
            return "CRITICAL - 即座の対応が必要です"
            
    def _generate_recommendations(
        self,
        violations: List[Dict[str,
        Any]],
        health_score: Dict[str,
        Any]
    ) -> List[str]:
        """
        改善提案を生成
        
        Args:
            violations: 違反のリスト
            health_score: 健全性スコア
            
        Returns:
            List[str]: 提案のリスト
        """
        recommendations = []
        
        # カテゴリー別スコアから提案
        category_scores = health_score["category_scores"]
        
        if category_scores["integrity"] < 70:
            recommendations.append("誠実性の向上: モック/スタブの削減、実装の完全性確保")
            
        if category_scores["process"] < 70:
            recommendations.append("プロセス遵守: Elder Flow、Git Flow、TDDサイクルの徹底")
            
        if category_scores["quality"] < 70:
            recommendations.append("品質向上: テストカバレッジ向上、コードレビュー強化")
            
        if category_scores["collaboration"] < 70:
            recommendations.append("協調性改善: 4賢者相談の活用、サーバント間連携強化")
            
        # 重大違反への対応
        breakdown = self._get_violation_breakdown(violations)
        if breakdown["CRITICAL"] > 0:
            recommendations.insert(0, f"⚠️ 緊急: {breakdown['CRITICAL']}件のCRITICAL違反に即座対応が必要")
            
        return recommendations
        
    async def get_audit_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        監査履歴を取得
        
        Args:
            limit: 取得する履歴の最大数
            
        Returns:
            List[Dict]: 監査履歴
        """
        return self.audit_history[-limit:]
        
    def get_capabilities(self) -> Dict[str, Any]:
        """
        エンジンの能力を返す
        
        Returns:
            Dict: 能力の説明
        """
        return {
            "engine": "AncientElderAuditEngine",
            "version": "1.0.0",
            "registered_auditors": list(self.auditors.keys()),
            "score_weights": self.score_weights,
            "violation_weights": {k.value: v for k, v in self.violation_weights.items()},
            "capabilities": [
                "comprehensive_audit",
                "parallel_execution",
                "health_scoring",
                "recommendation_generation",
                "historical_tracking"
            ]
        }