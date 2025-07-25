"""
🏛️ Ancient Magic Fast Unit Tests
モックを使用した高速ユニットテスト
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from elders_guild.elder_tree.ancient_elder.base import AncientElderBase, AuditResult, ViolationSeverity
from elders_guild.elder_tree.ancient_elder.audit_engine import AncientElderAuditEngine


class TestAncientMagicFast:
    """古代魔法の高速テスト"""
    
    @pytest.fixture
    def mock_auditor(self)auditor = Mock(spec=AncientElderBase)
    """モック監査者を作成"""
        auditor.name = "MockAuditor"
        auditor.specialty = "mock_audit"
        
        # get_audit_scopeのモック
        auditor.get_audit_scope.return_value = {
            "scope": "mock_audit",
            "targets": ["test_target"],
            "description": "Mock auditor for testing"
        }
        
        # get_capabilitiesのモック
        auditor.get_capabilities.return_value = {
            "name": "MockAuditor",
            "specialty": "mock_audit",
            "type": "ancient_elder",
            "capabilities": ["audit", "test"]
        }
        
        # auditメソッドのモック（非同期）
        async def mock_audit(target):
            result = AuditResult()
            result.auditor_name = "MockAuditor"
            """mock_auditメソッド"""
            result.add_violation(
                severity=ViolationSeverity.LOW,
                title="Test violation",
                description="This is a test violation",
                location="test.py",
                suggested_fix="Fix it"
            )
            result.add_metric("test_score", 85.0)
            return result
            
        auditor.audit = AsyncMock(side_effect=mock_audit)
        
        # process_requestのモック（非同期）
        async def mock_process_request(request):
            if request.get("type") == "audit":
            """mock_process_requestを処理"""
                audit_result = await mock_audit(request.get("target", {}))
                return {
                    "status": "success",
                    "result": audit_result.get_summary(),
                    "violations": audit_result.violations
                }
            return {"status": "error", "message": "Unknown request"}
            
        auditor.process_request = AsyncMock(side_effect=mock_process_request)
        
        return auditor
    
    @pytest.fixture
    def audit_engine(self, mock_auditor)engine = AncientElderAuditEngine()
    """テスト用の監査エンジン"""
        engine.register_auditor("mock", mock_auditor)
        return engine
    
    def test_auditor_registration(self, audit_engine, mock_auditor):
        """監査者の登録テスト"""
        assert "mock" in audit_engine.auditors
        assert audit_engine.auditors["mock"] == mock_auditor
    
    @pytest.mark.asyncio
    async def test_single_audit_execution(self, mock_auditor):
        """単一監査の実行テスト"""
        target = {"type": "test", "path": "/test/path"}
        result = await mock_auditor.audit(target)
        
        assert isinstance(result, AuditResult)
        assert result.auditor_name == "MockAuditor"
        assert len(result.violations) == 1
        assert result.metrics["test_score"] == 85.0
    
    @pytest.mark.asyncio
    async def test_comprehensive_audit_fast(self, audit_engine):
        """包括的監査の高速テスト"""
        target = {"type": "project", "path": "/test/project"}
        
        # タイムアウトなしで実行
        result = await audit_engine.run_comprehensive_audit(target)
        
        assert "guild_health_score" in result
        assert "individual_results" in result
        assert "all_violations" in result
        assert result["statistics"]["total_auditors"] == 1
        assert result["statistics"]["successful_audits"] == 1
    
    @pytest.mark.asyncio
    async def test_multiple_auditors(self)engine = AncientElderAuditEngine()
    """複数監査者の並列実行テスト"""
        
        # 3つのモック監査者を作成
        for i in range(3):
            auditor = Mock(spec=AncientElderBase)
            auditor.name = f"MockAuditor{i}"
            
            async def process_request(request)await asyncio.sleep(0.1)  # 短い遅延
    """process_requestを処理"""
                return {
                    "status": "success",
                    "result": {"auditor": f"MockAuditor{i}"},
                    "violations": []
                }
            
            auditor.process_request = AsyncMock(side_effect=process_request)
            engine.register_auditor(f"mock{i}", auditor)
        
        # 並列実行
        import time
        start_time = time.time()
        result = await engine.run_comprehensive_audit({"type": "test"})
        execution_time = time.time() - start_time
        
        # 並列実行なので0.3秒以下で完了するはず
        assert execution_time < 0.3
        assert result["statistics"]["successful_audits"] == 3
    
    def test_violation_severity_handling(self)result = AuditResult()
    """違反重要度の処理テスト"""
        result.auditor_name = "TestAuditor"
        
        # 各重要度の違反を追加
        for severity in ViolationSeverity:
            result.add_violation(
                severity=severity,
                title=f"{severity.value} violation",
                description=f"Test {severity.value} violation"
            )
        
        summary = result.get_summary()
        assert summary["total_violations"] == len(ViolationSeverity)
        assert summary["severity_breakdown"]["CRITICAL"] == 1
        assert summary["severity_breakdown"]["HIGH"] == 1
        assert summary["severity_breakdown"]["MEDIUM"] == 1
        assert summary["severity_breakdown"]["LOW"] == 1
    
    @pytest.mark.asyncio
    async def test_error_handling(self, audit_engine):
        """エラーハンドリングのテスト"""
        # エラーを発生させるモック監査者
        error_auditor = Mock(spec=AncientElderBase)
        error_auditor.name = "ErrorAuditor"
        
        async def error_process_request(request):
            raise Exception("Test error")
        
        error_auditor.process_request = AsyncMock(side_effect=error_process_request)
        audit_engine.register_auditor("error", error_auditor)
        
        # エラーが適切に処理されることを確認
        result = await audit_engine.run_comprehensive_audit({"type": "test"})
        
        assert len(result.get("failed_audits", [])) == 1
        assert result["failed_audits"][0]["auditor"] == "error"
    
    def test_health_score_calculation(self, audit_engine):
        """健康スコア計算のテスト"""
        # _calculate_guild_health_scoreのテスト
        violations = [
            {"severity": "CRITICAL"},  # -50
            {"severity": "HIGH"},      # -20
            {"severity": "MEDIUM"},    # -5
            {"severity": "LOW"}        # -1
        ]
        
        score = audit_engine._calculate_guild_health_score(violations)
        # スコアは辞書形式で返される
        assert isinstance(score, dict)
        assert "total_score" in score
        # 品質カテゴリーのスコアが24になるはず
        assert score["category_scores"]["quality"] == 24
    
    @pytest.mark.asyncio
    async def test_quick_mode_performance(self):
        """クイックモードのパフォーマンステスト"""
        from elders_guild.elder_tree.ancient_elder.tdd_guardian_wrapper import TDDGuardian
        
        guardian = TDDGuardian()
        
        # クイックモードで実行（タイムアウトなし）
        target = {
            "type": "test_file",
            "path": __file__,
            "quick_mode": True,
            "timeout": 5
        }
        
        import time
        start_time = time.time()
        result = await guardian.audit(target)
        execution_time = time.time() - start_time
        
        # 5秒以内に完了
        assert execution_time < 5
        assert isinstance(result, AuditResult)