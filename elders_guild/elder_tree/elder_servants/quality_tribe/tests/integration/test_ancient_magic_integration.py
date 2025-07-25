"""
🏛️ Ancient Magic Integration Tests
6つの古代魔法の統合テスト
"""

import pytest
import asyncio
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from elders_guild.elder_tree.ancient_elder.audit_engine import AncientElderAuditEngine
from elders_guild.elder_tree.ancient_elder.integrity_auditor_wrapper import AncientElderIntegrityAuditor
from elders_guild.elder_tree.ancient_elder.tdd_guardian_wrapper import TDDGuardian
from elders_guild.elder_tree.ancient_elder.flow_compliance_wrapper import FlowComplianceAuditor
from elders_guild.elder_tree.ancient_elder.four_sages_wrapper import FourSagesOverseer
from elders_guild.elder_tree.ancient_elder.git_chronicle_wrapper import GitChronicle
from elders_guild.elder_tree.ancient_elder.servant_inspector_wrapper import ServantInspector


class TestAncientMagicIntegration:
    """古代魔法統合テスト"""
    
    @pytest.fixture
    def audit_engine(self):
        """監査エンジンのフィクスチャ"""
        engine = AncientElderAuditEngine()
        
        # 全ての監査者を登録
        auditors = {
            "integrity": AncientElderIntegrityAuditor(),
            "tdd_guardian": TDDGuardian(),
            "flow_compliance": FlowComplianceAuditor(),
            "four_sages": FourSagesOverseer(),
            "git_chronicle": GitChronicle(),
            "servant_inspector": ServantInspector()
        }
        
        for key, auditor in auditors.items():
            engine.register_auditor(key, auditor)
            
        return engine
        
    @pytest.mark.asyncio
    async def test_comprehensive_audit_execution(self, audit_engine):
        """包括的監査の実行テスト"""
        # テスト用ターゲット
        target = {
            "type": "project",
            "path": str(project_root),
            "comprehensive": True
        }
        
        # 監査を実行
        result = await audit_engine.run_comprehensive_audit(target)
        
        # 基本的な結果検証
        assert "guild_health_score" in result
        assert "execution_time" in result
        assert "all_violations" in result
        assert "individual_results" in result
        assert "statistics" in result
        
        # スコアの範囲チェック
        assert 0 <= result["guild_health_score"] <= 100
        
        # 実行時間が記録されているか
        assert result["execution_time"] > 0
        
    @pytest.mark.asyncio
    async def test_individual_auditor_registration(self, audit_engine):
        """個別監査者の登録テスト"""
        # 監査者が正しく登録されているか確認
        assert len(audit_engine.auditors) == 6
        assert "integrity" in audit_engine.auditors
        assert "tdd_guardian" in audit_engine.auditors
        assert "flow_compliance" in audit_engine.auditors
        assert "four_sages" in audit_engine.auditors
        assert "git_chronicle" in audit_engine.auditors
        assert "servant_inspector" in audit_engine.auditors
        
    @pytest.mark.asyncio
    async def test_violation_aggregation(self, audit_engine):
        """違反の集約テスト"""
        # 小さなターゲットで監査実行
        target = {
            "type": "file",
            "path": __file__  # このテストファイル自体を監査
        }
        
        result = await audit_engine.run_comprehensive_audit(target)
        
        # 違反が適切に集約されているか
        all_violations = result.get("all_violations", [])
        assert isinstance(all_violations, list)
        
        # 各違反に必要な情報が含まれているか
        for violation in all_violations:
            assert "severity" in violation
            assert "title" in violation
            assert "description" in violation
            
    @pytest.mark.asyncio
    async def test_health_score_calculation(self, audit_engine):
        """健康スコア計算のテスト"""
        # モックターゲット
        target = {
            "type": "project",
            "path": str(project_root / "tests"),
            "time_window_days": 1  # 短い期間で高速化
        }
        
        result = await audit_engine.run_comprehensive_audit(target)
        
        # スコア計算の妥当性
        health_score = result.get("guild_health_score", 0)
        assert 0 <= health_score <= 100
        
        # 違反数とスコアの相関
        violation_count = len(result.get("all_violations", []))
        if violation_count == 0:
            assert health_score == 100
        else:
            assert health_score < 100
            
    @pytest.mark.asyncio
    async def test_error_handling(self, audit_engine):
        """エラーハンドリングのテスト"""
        # 存在しないパスを指定
        target = {
            "type": "project",
            "path": "/nonexistent/path"
        }
        
        # エラーが適切に処理されるか
        result = await audit_engine.run_comprehensive_audit(target)
        
        # 結果が返されることを確認
        assert result is not None
        assert "failed_audits" in result
        
    @pytest.mark.asyncio
    async def test_recommendation_generation(self, audit_engine):
        """推奨事項生成のテスト"""
        target = {
            "type": "project",
            "path": str(project_root),
            "comprehensive": True
        }
        
        result = await audit_engine.run_comprehensive_audit(target)
        
        # 推奨事項が生成されているか
        recommendations = result.get("recommendations", [])
        assert isinstance(recommendations, list)
        
        # 推奨事項の内容確認
        for rec in recommendations:
            assert isinstance(rec, str)
            assert len(rec) > 0
            
    def test_auditor_capabilities(self, audit_engine):
        """各監査者の能力確認テスト"""
        for key, auditor in audit_engine.auditors.items():
            # get_audit_scopeメソッドが実装されているか
            scope = auditor.get_audit_scope()
            assert scope is not None
            
            # 基本的な能力を持っているか
            capabilities = auditor.get_capabilities()
            assert "name" in capabilities
            assert "specialty" in capabilities
            assert "type" in capabilities
            
    @pytest.mark.asyncio 
    async def test_parallel_execution(self, audit_engine):
        """並列実行のテスト"""
        import time
        
        target = {
            "type": "project",
            "path": str(project_root / "libs"),
            "time_window_days": 1
        }
        
        # 実行時間を計測
        start_time = time.time()
        result = await audit_engine.run_comprehensive_audit(target)
        execution_time = time.time() - start_time
        
        # 並列実行により高速化されているか
        # 6つの監査者が直列実行された場合より短いはず
        assert execution_time < 30  # 30秒以内に完了
        assert result["execution_time"] > 0
        
    @pytest.mark.asyncio
    async def test_metric_collection(self, audit_engine):
        """メトリクス収集のテスト"""
        target = {
            "type": "project", 
            "path": str(project_root)
        }
        
        result = await audit_engine.run_comprehensive_audit(target)
        
        # 統計情報が収集されているか
        stats = result.get("statistics", {})
        assert "total_auditors" in stats
        assert "successful_audits" in stats
        assert "failed_audits" in stats
        assert "total_violations" in stats
        
        # 統計の妥当性
        assert stats["total_auditors"] == 6
        assert stats["successful_audits"] + stats["failed_audits"] == stats["total_auditors"]