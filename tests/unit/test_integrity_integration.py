"""
🔮 Integrity Auditor Integration Tests
誠実性監査魔法とAncient Elder システム統合テスト
"""

import pytest
import tempfile
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.ancient_elder.audit_engine import AncientElderAuditEngine
from libs.ancient_elder.integrity_auditor import IntegrityAuditor


class TestIntegrityAuditorIntegration:
    """IntegrityAuditorとAuditEngineの統合テスト"""
    
    @pytest.fixture
    def audit_engine(self):
        """テスト用のAudit Engine"""
        engine = AncientElderAuditEngine()
        
        # IntegrityAuditorを登録
        integrity_auditor = IntegrityAuditor()
        engine.register_auditor("integrity", integrity_auditor)
        
        return engine
        
    @pytest.mark.asyncio
    async def test_comprehensive_integrity_audit(self, audit_engine):
        """包括的誠実性監査のテスト"""
        # テストコードを作成
        test_content = """
# TODO: Implement user authentication
def login_user(username, password):
    '''User login function'''
    # FIXME: Add proper validation
    if username == "admin":
        return True
    return False

def logout_user():
    '''User logout function'''
    pass  # TODO: Implement logout logic

def get_user_profile():
    '''Get user profile'''
    raise NotImplementedError("Profile service not implemented")
    
def placeholder_function():
    '''Placeholder for future feature'''
    return PLACEHOLDER
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            f.flush()
            
            # 包括的監査を実行
            target = {
                "type": "file",
                "path": f.name
            }
            
            result = await audit_engine.run_comprehensive_audit(target)
            
        import os
        os.unlink(f.name)
        
        # 結果の検証
        assert result["auditors_run"] == 1
        assert result["auditors_failed"] == 0
        assert "integrity" in result["individual_results"]
        
        integrity_result = result["individual_results"]["integrity"]
        assert integrity_result["auditor"] == "integrity"
        assert len(integrity_result["violations"]) > 0
        
        # ギルド健全性スコアが計算されている
        assert "guild_health_score" in result
        assert result["guild_health_score"]["total_score"] < 100  # 違反があるので100未満
        
        # 違反の内訳
        assert result["total_violations"] > 0
        # NotImplementedError があればCRITICAL、なければMEDIUM以上の違反があることを確認
        total_high_severity = result["violation_breakdown"]["CRITICAL"] + result["violation_breakdown"]["HIGH"]
        assert total_high_severity >= 1 or result["violation_breakdown"]["MEDIUM"] >= 3  # 複数のTODO/FIXME
        
        # 推奨事項が生成されている
        assert len(result["recommendations"]) > 0
        
    @pytest.mark.asyncio
    async def test_clean_code_audit(self, audit_engine):
        """クリーンなコードの監査テスト"""
        clean_content = """
def calculate_sum(a, b):
    '''Calculate the sum of two numbers'''
    return a + b

def calculate_product(a, b):
    '''Calculate the product of two numbers'''
    return a * b

class Calculator:
    '''Simple calculator class'''
    
    def __init__(self):
        self.result = 0
        
    def add(self, value):
        '''Add value to result'''
        self.result += value
        return self.result
        
    def multiply(self, value):
        '''Multiply result by value'''
        self.result *= value
        return self.result
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(clean_content)
            f.flush()
            
            target = {"type": "file", "path": f.name}
            result = await audit_engine.run_comprehensive_audit(target)
            
        import os
        os.unlink(f.name)
        
        # クリーンなコードなので高いスコア
        assert result["guild_health_score"]["total_score"] >= 90
        assert result["total_violations"] == 0 or result["total_violations"] <= 2  # 軽微な違反のみ許容
        assert "EXCELLENT" in result["evaluation"]
        
    @pytest.mark.asyncio
    async def test_multiple_files_audit(self, audit_engine):
        """複数ファイルの監査テスト"""
        files = []
        
        try:
            # クリーンなファイル
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f1:
                f1.write("""
def good_function():
    '''A well-implemented function'''
    return "Hello, World!"
""")
                files.append(f1.name)
                
            # 問題のあるファイル
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f2:
                f2.write("""
# TODO: Fix this mess
def bad_function():
    pass  # FIXME: No implementation
    
def critical_function():
    raise NotImplementedError("Critical missing implementation")
""")
                files.append(f2.name)
                
            # ファイルリストで監査
            target = {"type": "files", "files": files}
            result = await audit_engine.run_comprehensive_audit(target)
            
            # 結果の検証
            assert result["total_violations"] > 0
            # CRITICAL違反があるか、または多くの違反がある
            has_critical = result["violation_breakdown"]["CRITICAL"] >= 1
            has_many_violations = result["total_violations"] >= 3
            assert has_critical or has_many_violations
            
            assert result["guild_health_score"]["total_score"] < 90  # 問題があるので低スコア
            
            # 推奨事項が生成されている
            recommendations = result["recommendations"]
            assert len(recommendations) > 0
            
        finally:
            # クリーンアップ
            for file_path in files:
                try:
                    import os
                    os.unlink(file_path)
                except:
                    pass
                    
    def test_auditor_capabilities(self, audit_engine):
        """監査者の能力テスト"""
        capabilities = audit_engine.get_capabilities()
        
        assert "registered_auditors" in capabilities
        assert "integrity" in capabilities["registered_auditors"]
        assert "score_weights" in capabilities
        assert "violation_weights" in capabilities
        
        # IntegrityAuditorの範囲を確認
        integrity_auditor = audit_engine.auditors["integrity"]
        scope = integrity_auditor.get_audit_scope()
        
        assert scope["scope"] == "code_integrity"
        assert "violation_types" in scope
        assert len(scope["violation_types"]) > 0
        
    @pytest.mark.asyncio
    async def test_audit_history_tracking(self, audit_engine):
        """監査履歴追跡のテスト"""
        test_content = "def simple(): return 'test'"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            f.flush()
            
            # 複数回監査を実行
            target = {"type": "file", "path": f.name}
            
            result1 = await audit_engine.run_comprehensive_audit(target)
            result2 = await audit_engine.run_comprehensive_audit(target)
            
        import os
        os.unlink(f.name)
        
        # 履歴が記録されている
        history = await audit_engine.get_audit_history()
        assert len(history) >= 2
        
        # 最新の監査結果
        latest = history[-1]
        assert "timestamp" in latest
        assert "guild_health_score" in latest
        assert "individual_results" in latest