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

from souls.base_soul import BaseSoul, ElderType


class ViolationSeverity(Enum):
    """違反の重要度"""
    CRITICAL = "CRITICAL"  # 即座に対応が必要
    HIGH = "HIGH"          # 重大な違反
    MEDIUM = "MEDIUM"      # 中程度の違反
    LOW = "LOW"            # 軽微な違反


class AuditResult:
    """監査結果を表すクラス"""
    def __init__(self):
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
        super().__init__(
            name=f"AncientElder_{specialty}",
            elder_type=ElderType.ANCIENT_ELDER,
            specialty=specialty
        )
        
        self.logger = logging.getLogger(f"AncientElder.{specialty}")
        
        # 違反閾値の設定
        self.violation_threshold = {
            ViolationSeverity.CRITICAL: 0,    # 即座に対応
            ViolationSeverity.HIGH: 3,        # 3件で警告
            ViolationSeverity.MEDIUM: 10,     # 10件で注意
            ViolationSeverity.LOW: 50         # 50件で改善提案
        }
        
        # 監査履歴
        self.audit_history: List[AuditResult] = []
        
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