"""
🏛️ Ancient Elder Base Tests
AncientElderBaseクラスのテスト
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.ancient_elder.base import (
    AncientElderBase, 
    AuditResult, 
    ViolationSeverity
)
from libs.base_soul import ElderType


class TestAncientElderImpl(AncientElderBase):
    """テスト用の具体的な実装"""
    
    async def audit(self, target):
        """テスト用の監査実装"""
        result = AuditResult()
        result.auditor_name = self.name
        
        # テスト用の違反を追加
        if target.get("has_violations"):
            result.add_violation(
                severity=ViolationSeverity.HIGH,
                title="Test Violation",
                description="This is a test violation",
                location="test.py",
                suggested_fix="Fix the test"
            )
            
        result.add_metric("test_metric", 100)
        return result
        
    def get_audit_scope(self):
        """テスト用の監査範囲"""
        return {
            "scope": "test",
            "targets": ["test_files"],
            "description": "Test audit scope"
        }


class TestAncientElderBase:
    """AncientElderBaseのテスト"""
    
    @pytest.fixture
    def ancient_elder(self):
        """テスト用のAncient Elderインスタンス"""
        return TestAncientElderImpl("TestAuditor")
        
    def test_initialization(self, ancient_elder):
        """初期化のテスト"""
        assert ancient_elder.name == "AncientElder_TestAuditor"
        assert ancient_elder.elder_type == ElderType.ANCIENT_ELDER
        assert ancient_elder.specialty == "TestAuditor"
        assert len(ancient_elder.violation_threshold) == 4
        assert ancient_elder.audit_history == []
        
    def test_violation_thresholds(self, ancient_elder):
        """違反閾値の設定テスト"""
        assert ancient_elder.violation_threshold[ViolationSeverity.CRITICAL] == 0
        assert ancient_elder.violation_threshold[ViolationSeverity.HIGH] == 3
        assert ancient_elder.violation_threshold[ViolationSeverity.MEDIUM] == 10
        assert ancient_elder.violation_threshold[ViolationSeverity.LOW] == 50
        
    @pytest.mark.asyncio
    async def test_audit_request_success(self, ancient_elder):
        """監査リクエスト成功のテスト"""
        request = {
            "type": "audit",
            "target": {"has_violations": True}
        }
        
        result = await ancient_elder.process_request(request)
        
        assert result["status"] == "success"
        assert "result" in result
        assert "violations" in result
        assert len(result["violations"]) == 1
        assert result["violations"][0]["severity"] == "HIGH"
        
    @pytest.mark.asyncio
    async def test_audit_request_no_violations(self, ancient_elder):
        """違反なしの監査テスト"""
        request = {
            "type": "audit",
            "target": {"has_violations": False}
        }
        
        result = await ancient_elder.process_request(request)
        
        assert result["status"] == "success"
        assert len(result["violations"]) == 0
        assert result["result"]["total_violations"] == 0
        
    @pytest.mark.asyncio
    async def test_get_scope_request(self, ancient_elder):
        """監査範囲取得リクエストのテスト"""
        request = {"type": "get_scope"}
        
        result = await ancient_elder.process_request(request)
        
        assert result["status"] == "success"
        assert "scope" in result
        assert result["scope"]["scope"] == "test"
        
    @pytest.mark.asyncio
    async def test_get_history_request(self, ancient_elder):
        """履歴取得リクエストのテスト"""
        # まず監査を実行して履歴を作成
        await ancient_elder.process_request({
            "type": "audit",
            "target": {"has_violations": True}
        })
        
        # 履歴を取得
        request = {"type": "get_history", "limit": 5}
        result = await ancient_elder.process_request(request)
        
        assert result["status"] == "success"
        assert "history" in result
        assert len(result["history"]) == 1
        
    @pytest.mark.asyncio
    async def test_threshold_alerts(self, ancient_elder):
        """閾値アラートのテスト"""
        # 閾値を低く設定
        ancient_elder.violation_threshold[ViolationSeverity.HIGH] = 0
        
        request = {
            "type": "audit",
            "target": {"has_violations": True}
        }
        
        result = await ancient_elder.process_request(request)
        
        assert "alerts" in result
        assert len(result["alerts"]) > 0
        assert result["alerts"][0]["type"] == "threshold_exceeded"
        
    def test_get_capabilities(self, ancient_elder):
        """能力取得のテスト"""
        capabilities = ancient_elder.get_capabilities()
        
        assert capabilities["name"] == "AncientElder_TestAuditor"
        assert capabilities["specialty"] == "TestAuditor"
        assert capabilities["type"] == "ancient_elder"
        assert "audit_scope" in capabilities
        assert "violation_thresholds" in capabilities
        assert "capabilities" in capabilities
        
    def test_validate_request(self, ancient_elder):
        """リクエスト検証のテスト"""
        # 有効なリクエスト
        assert ancient_elder.validate_request({"type": "audit", "target": {}})
        assert ancient_elder.validate_request({"type": "get_scope"})
        assert ancient_elder.validate_request({"type": "get_history"})
        
        # 無効なリクエスト
        assert not ancient_elder.validate_request({"type": "invalid"})
        assert not ancient_elder.validate_request({"type": "audit"})  # targetがない
        
    @pytest.mark.asyncio
    async def test_error_handling(self, ancient_elder):
        """エラーハンドリングのテスト"""
        request = {"type": "unknown_type"}
        
        result = await ancient_elder.process_request(request)
        
        assert result["status"] == "error"
        assert "message" in result


class TestAuditResult:
    """AuditResultクラスのテスト"""
    
    def test_audit_result_initialization(self):
        """AuditResult初期化のテスト"""
        result = AuditResult()
        
        assert result.violations == []
        assert result.metrics == {}
        assert isinstance(result.timestamp, datetime)
        
    def test_add_violation(self):
        """違反追加のテスト"""
        result = AuditResult()
        
        result.add_violation(
            severity=ViolationSeverity.CRITICAL,
            title="Critical Issue",
            description="This is critical",
            location="critical.py:10",
            suggested_fix="Fix immediately",
            metadata={"category": "security"}
        )
        
        assert len(result.violations) == 1
        violation = result.violations[0]
        assert violation["severity"] == "CRITICAL"
        assert violation["title"] == "Critical Issue"
        assert violation["metadata"]["category"] == "security"
        
    def test_add_metric(self):
        """メトリクス追加のテスト"""
        result = AuditResult()
        
        result.add_metric("coverage", 85.5)
        result.add_metric("violations_fixed", 10)
        
        assert result.metrics["coverage"] == 85.5
        assert result.metrics["violations_fixed"] == 10
        
    def test_get_summary(self):
        """サマリー取得のテスト"""
        result = AuditResult()
        result.auditor_name = "TestAuditor"
        
        # 各種違反を追加
        result.add_violation(ViolationSeverity.CRITICAL, "Critical", "desc")
        result.add_violation(ViolationSeverity.HIGH, "High", "desc")
        result.add_violation(ViolationSeverity.HIGH, "High2", "desc")
        result.add_violation(ViolationSeverity.MEDIUM, "Medium", "desc")
        
        summary = result.get_summary()
        
        assert summary["auditor"] == "TestAuditor"
        assert summary["total_violations"] == 4
        assert summary["severity_breakdown"]["CRITICAL"] == 1
        assert summary["severity_breakdown"]["HIGH"] == 2
        assert summary["severity_breakdown"]["MEDIUM"] == 1
        assert summary["severity_breakdown"]["LOW"] == 0