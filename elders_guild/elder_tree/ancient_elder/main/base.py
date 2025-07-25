"""
🏛️ Ancient Elder Base Class
すべてのエンシェントエルダーの基底クラス
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from pathlib import Path

# プロジェクトルートをパスに追加
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from elders_guild.elder_tree.base_soul import BaseSoul, ElderType, SoulIdentity, SoulCapability


class ViolationSeverity(Enum):
    """違反の重要度"""
    CRITICAL = "CRITICAL"  # 即座に対応が必要
    HIGH = "HIGH"          # 重大な違反
    MEDIUM = "MEDIUM"      # 中程度の違反
    LOW = "LOW"            # 軽微な違反


class AuditResult:
    """監査結果を表すクラス"""
    def __init__(self):
        """初期化メソッド"""
        self.violations: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {}
        self.timestamp = datetime.now()
        self.auditor_name: str = ""
        
    def add_violation(self, 
                     severity: ViolationSeverity,
                     title: str,
                     description: str,
                     location: Optional[str] = None,
                     suggested_fix: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None):
        """違反を追加"""
        violation = {
            "severity": severity.value,
            "title": title,
            "description": description,
            "location": location,
            "suggested_fix": suggested_fix,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        self.violations.append(violation)
        
    def add_metric(self, name: str, value: Any):
        """メトリクスを追加"""
        self.metrics[name] = value
        
    def get_summary(self) -> Dict[str, Any]:
        """サマリーを取得"""
        severity_counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0
        }
        
        for violation in self.violations:
            severity_counts[violation["severity"]] += 1
            
        return {
            "auditor": self.auditor_name,
            "timestamp": self.timestamp.isoformat(),
            "total_violations": len(self.violations),
            "severity_breakdown": severity_counts,
            "metrics": self.metrics
        }


class AncientElderBase(BaseSoul, ABC):
    """すべてのエンシェントエルダーの基底クラス"""
    
    def __init__(self, specialty: str):
        """初期化メソッド"""
        # SoulIdentityを作成
        identity = SoulIdentity(
            soul_id=f"ancient_elder_{specialty.lower()}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            soul_name=f"AncientElder_{specialty}",
            elder_type=ElderType.ANCIENT_ELDER,
            hierarchy_level=2,  # Ancient Elderは階層レベル2
            capabilities=[
                SoulCapability.LEARNING,
                SoulCapability.ANALYSIS,
                SoulCapability.QUALITY_ASSURANCE,
                SoulCapability.LEADERSHIP
            ],
            specializations=[specialty]
        )
        
        # BaseSoulの初期化
        super().__init__(identity)
        
        self.specialty = specialty
        self.name = identity.soul_name
        
        # 違反閾値の設定
        self.violation_threshold = {
            ViolationSeverity.CRITICAL: 0,    # 即座に対応
            ViolationSeverity.HIGH: 3,        # 3件で警告
            ViolationSeverity.MEDIUM: 10,     # 10件で注意
            ViolationSeverity.LOW: 50         # 50件で改善提案
        }
        
        # 監査履歴
        self.audit_history: List[AuditResult] = []
        
        # elder_typeプロパティ（互換性のため）
        self.elder_type = ElderType.ANCIENT_ELDER
        
    @abstractmethod
    async def audit(self, target: Dict[str, Any]) -> AuditResult:
        """
        監査を実行する（サブクラスで実装）
        
        Args:
            target: 監査対象の情報
            
        Returns:
            AuditResult: 監査結果
        """
        pass
        
    @abstractmethod
    def get_audit_scope(self) -> Dict[str, Any]:
        """
        この監査者の監査範囲を返す
        
        Returns:
            Dict: 監査範囲の説明
        """
        pass
        
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        リクエストを処理する（BaseSoulインターフェース）
        
        Args:
            request: リクエスト情報
            
        Returns:
            Dict: 処理結果
        """
        try:
            request_type = request.get("type", "audit")
            
            if request_type == "audit":
                # 監査の実行
                target = request.get("target", {})
                result = await self.audit(target)
                
                # 履歴に追加
                self.audit_history.append(result)
                
                # 閾値チェック
                alerts = self._check_thresholds(result)
                
                return {
                    "status": "success",
                    "result": result.get_summary(),
                    "violations": result.violations,
                    "alerts": alerts
                }
                
            elif request_type == "get_scope":
                # 監査範囲の取得
                return {
                    "status": "success",
                    "scope": self.get_audit_scope()
                }
                
            elif request_type == "get_history":
                # 監査履歴の取得
                limit = request.get("limit", 10)
                history = [
                    result.get_summary() 
                    for result in self.audit_history[-limit:]
                ]
                return {
                    "status": "success",
                    "history": history
                }
                
            else:
                return {
                    "status": "error",
                    "message": f"Unknown request type: {request_type}"
                }
                
        except Exception as e:
            self.logger.error(f"Error processing request: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
            
    def _check_thresholds(self, result: AuditResult) -> List[Dict[str, Any]]:
        """
        違反数が閾値を超えているかチェック
        
        Args:
            result: 監査結果
            
        Returns:
            List[Dict]: アラートのリスト
        """
        alerts = []
        severity_counts = {}
        
        # 重要度別に違反をカウント
        for violation in result.violations:
            severity = violation["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
        # 閾値チェック
        for severity, threshold in self.violation_threshold.items():
            count = severity_counts.get(severity.value, 0)
            if count > threshold:
                alerts.append({
                    "type": "threshold_exceeded",
                    "severity": severity.value,
                    "count": count,
                    "threshold": threshold,
                    "message": f"{severity.value} violations exceeded threshold: {count} > {threshold}"
                })
                
        return alerts
        
    def get_capabilities(self) -> Dict[str, Any]:
        """
        この監査者の能力を返す
        
        Returns:
            Dict: 能力の説明
        """
        return {
            "name": self.name,
            "specialty": self.specialty,
            "type": "ancient_elder",
            "audit_scope": self.get_audit_scope(),
            "violation_thresholds": {
                k.value: v for k, v in self.violation_threshold.items()
            },
            "capabilities": [
                "audit",
                "violation_detection",
                "threshold_monitoring",
                "historical_analysis"
            ]
        }
        
    def validate_request(self, request: Dict[str, Any]) -> bool:
        """
        リクエストの妥当性を検証
        
        Args:
            request: リクエスト情報
            
        Returns:
            bool: 妥当な場合True
        """
        request_type = request.get("type")
        valid_types = ["audit", "get_scope", "get_history"]
        
        if request_type not in valid_types:
            return False
            
        if request_type == "audit" and "target" not in request:
            return False
            
        return True
        
    async def on_soul_awakening(self) -> Dict[str, Any]:
        """
        魂が覚醒した時の処理（BaseSoulインターフェース）
        """
        self.logger.info(f"{self.name} awakened as Ancient Elder")
        return {
            "status": "awakened",
            "name": self.name,
            "specialty": self.specialty
        }
        
    async def on_autonomous_activity(self) -> Dict[str, Any]:
        """
        自律的な活動（BaseSoulインターフェース）
        """
        # Ancient Elderは定期的な監査を自律的に実行
        return {
            "activity": "periodic_audit",
            "status": "monitoring"
        }
        
    async def on_learning_cycle(self, experiences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        学習サイクル（BaseSoulインターフェース）
        """
        # 過去の監査結果から学習
        patterns_learned = []
        for exp in experiences:
            if exp.get("type") == "audit_result":
                patterns_learned.append(exp.get("pattern", "unknown"))
                
        return {
            "learned_patterns": patterns_learned,
            "improvement_areas": self._analyze_improvement_areas()
        }
        
    async def process_soul_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        魂リクエストの処理（BaseSoulインターフェース）
        """
        # process_requestに委譲
        return await self.process_request(request)
        
    def _analyze_improvement_areas(self) -> List[str]:
        """
        改善領域を分析する内部メソッド
        """
        areas = []
        if len(self.audit_history) > 0:
            recent_violations = sum(
                len(audit.violations) for audit in self.audit_history[-5:]
            )
            if recent_violations > 20:
                areas.append("Increase audit frequency")
            if recent_violations < 5:
                areas.append("Focus on preventive measures")
                
        return areas