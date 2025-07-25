"""
🏛️ Ancient Elder Audit Engine Tests
AncientElderAuditEngineクラスのテスト
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from elders_guild.elder_tree.ancient_elder.audit_engine import AncientElderAuditEngine
from elders_guild.elder_tree.ancient_elder.base import AncientElderBase, AuditResult, ViolationSeverity


class MockAuditor(AncientElderBase):
    """テスト用のモック監査者"""
    
    def __init__(self, specialty: str, violations_to_add=None):
        super().__init__(specialty)
        self.violations_to_add = violations_to_add or []
        
    async def audit(self, target):
        """モック監査実装"""
        result = AuditResult()
        result.auditor_name = self.name
        
        for violation in self.violations_to_add:
            result.add_violation(**violation)
            
        result.add_metric("test_metric", 100)
        return result
        
    def get_audit_scope(self):
        """モック監査範囲"""
        return {
            "scope": f"{self.specialty}_scope",
            "description": f"Mock {self.specialty} auditor"
        }


class TestAncientElderAuditEngine:
    """AncientElderAuditEngineのテスト"""
    
    @pytest.fixture
    def audit_engine(self):
        """テスト用のAudit Engineインスタンス"""
        return AncientElderAuditEngine()
        
    def test_initialization(self, audit_engine):
        """初期化のテスト"""
        assert audit_engine.auditors == {}
        assert audit_engine.audit_history == []
        assert "integrity" in audit_engine.score_weights
        assert ViolationSeverity.CRITICAL in audit_engine.violation_weights
        
    def test_register_auditor(self, audit_engine):
        """監査者登録のテスト"""
        auditor = MockAuditor("test")
        audit_engine.register_auditor("test", auditor)
        
        assert "test" in audit_engine.auditors
        assert audit_engine.auditors["test"] == auditor
        
    @pytest.mark.asyncio
    async def test_comprehensive_audit_success(self, audit_engine):
        """包括的監査成功のテスト"""
        # 監査者を登録
        auditor1 = MockAuditor("integrity", [
            {
                "severity": ViolationSeverity.HIGH,
                "title": "Integrity violation",
                "description": "Mock detected",
                "metadata": {"category": "integrity"}
            }
        ])
        auditor2 = MockAuditor("tdd", [
            {
                "severity": ViolationSeverity.MEDIUM,
                "title": "TDD violation",
                "description": "Test missing",
                "metadata": {"category": "quality"}
            }
        ])
        
        audit_engine.register_auditor("integrity", auditor1)
        audit_engine.register_auditor("tdd", auditor2)
        
        # 監査を実行
        target = {"test": "data"}
        result = await audit_engine.run_comprehensive_audit(target)
        
        assert result["auditors_run"] == 2
        assert result["auditors_failed"] == 0
        assert result["total_violations"] == 2
        assert result["violation_breakdown"]["HIGH"] == 1
        assert result["violation_breakdown"]["MEDIUM"] == 1
        assert "guild_health_score" in result
        assert "evaluation" in result
        assert "recommendations" in result
        
    @pytest.mark.asyncio
    async def test_comprehensive_audit_with_failure(self, audit_engine):
        """一部の監査が失敗する場合のテスト"""
        # 正常な監査者
        good_auditor = MockAuditor("good")
        
        # 失敗する監査者
        bad_auditor = MockAuditor("bad")
        bad_auditor.process_request = AsyncMock(side_effect=Exception("Audit failed"))
        
        audit_engine.register_auditor("good", good_auditor)
        audit_engine.register_auditor("bad", bad_auditor)
        
        # 監査を実行
        result = await audit_engine.run_comprehensive_audit({})
        
        assert result["auditors_run"] == 2
        assert result["auditors_failed"] == 1
        assert len(result["failed_audits"]) == 1
        assert result["failed_audits"][0]["auditor"] == "bad"
        
    def test_calculate_guild_health_score(self, audit_engine):
        """健全性スコア計算のテスト"""
        violations = [
            {"severity": "CRITICAL", "metadata": {"category": "integrity"}},
            {"severity": "HIGH", "metadata": {"category": "process"}},
            {"severity": "MEDIUM", "metadata": {"category": "quality"}},
            {"severity": "LOW", "metadata": {"category": "collaboration"}}
        ]
        
        score = audit_engine._calculate_guild_health_score(violations)
        
        assert "total_score" in score
        assert "category_scores" in score
        assert score["total_score"] < 100  # 違反があるので100未満
        assert all(cat in score["category_scores"] for cat in ["integrity", "process", "quality", "collaboration"])
        
    def test_get_violation_breakdown(self, audit_engine):
        """違反内訳取得のテスト"""
        violations = [
            {"severity": "CRITICAL"},
            {"severity": "HIGH"},
            {"severity": "HIGH"},
            {"severity": "MEDIUM"},
            {"severity": "MEDIUM"},
            {"severity": "MEDIUM"},
            {"severity": "LOW"}
        ]
        
        breakdown = audit_engine._get_violation_breakdown(violations)
        
        assert breakdown["CRITICAL"] == 1
        assert breakdown["HIGH"] == 2
        assert breakdown["MEDIUM"] == 3
        assert breakdown["LOW"] == 1
        
    def test_evaluate_health_score(self, audit_engine):
        """健全性スコア評価のテスト"""
        assert "EXCELLENT" in audit_engine._evaluate_health_score({"total_score": 95})
        assert "GOOD" in audit_engine._evaluate_health_score({"total_score": 80})
        assert "FAIR" in audit_engine._evaluate_health_score({"total_score": 65})
        assert "POOR" in audit_engine._evaluate_health_score({"total_score": 45})
        assert "CRITICAL" in audit_engine._evaluate_health_score({"total_score": 30})
        
    def test_generate_recommendations(self, audit_engine):
        """改善提案生成のテスト"""
        violations = [{"severity": "CRITICAL", "metadata": {}}]
        health_score = {
            "total_score": 50,
            "category_scores": {
                "integrity": 40,
                "process": 60,
                "quality": 50,
                "collaboration": 80
            }
        }
        
        recommendations = audit_engine._generate_recommendations(violations, health_score)
        
        assert len(recommendations) > 0
        assert any("緊急" in rec for rec in recommendations)  # CRITICAL違反への対応
        assert any("誠実性" in rec for rec in recommendations)  # 低スコアカテゴリー
        
    @pytest.mark.asyncio
    async def test_get_audit_history(self, audit_engine):
        """監査履歴取得のテスト"""
        # 履歴を作成
        auditor = MockAuditor("test")
        audit_engine.register_auditor("test", auditor)
        
        # 複数回監査を実行
        for i in range(3):
            await audit_engine.run_comprehensive_audit({"run": i})
            
        # 履歴を取得
        history = await audit_engine.get_audit_history(limit=2)
        
        assert len(history) == 2
        assert all("timestamp" in h for h in history)
        
    def test_get_capabilities(self, audit_engine):
        """能力取得のテスト"""
        auditor = MockAuditor("test")
        audit_engine.register_auditor("test", auditor)
        
        capabilities = audit_engine.get_capabilities()
        
        assert capabilities["engine"] == "AncientElderAuditEngine"
        assert "version" in capabilities
        assert "test" in capabilities["registered_auditors"]
        assert "score_weights" in capabilities
        assert "violation_weights" in capabilities
        assert "capabilities" in capabilities
        
    @pytest.mark.asyncio
    async def test_no_violations_perfect_score(self, audit_engine):
        """違反なしの場合の完璧なスコアテスト"""
        # 違反なしの監査者
        auditor = MockAuditor("perfect", [])
        audit_engine.register_auditor("perfect", auditor)
        
        result = await audit_engine.run_comprehensive_audit({})
        
        assert result["total_violations"] == 0
        assert result["guild_health_score"]["total_score"] == 100.0
        assert "EXCELLENT" in result["evaluation"]
        
    @pytest.mark.asyncio
    async def test_critical_violations_impact(self, audit_engine):
        """CRITICAL違反の影響テスト"""
        # CRITICAL違反を持つ監査者
        auditor = MockAuditor("critical", [
            {
                "severity": ViolationSeverity.CRITICAL,
                "title": "Critical issue",
                "description": "Very serious",
                "metadata": {"category": "integrity"}
            }
        ])
        audit_engine.register_auditor("critical", auditor)
        
        result = await audit_engine.run_comprehensive_audit({})
        
        # CRITICALは-50点なので大幅に減点される
        assert result["guild_health_score"]["total_score"] < 100  # 100未満になることを確認
        assert result["guild_health_score"]["category_scores"]["integrity"] < 100  # integrityカテゴリが減点される
        assert result["violation_breakdown"]["CRITICAL"] == 1
        # 緊急対応の推奨が含まれる
        assert any("緊急" in rec for rec in result["recommendations"])