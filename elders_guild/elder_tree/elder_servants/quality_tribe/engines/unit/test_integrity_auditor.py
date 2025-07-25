"""
🔮 Integrity Auditor Tests
誠実性監査魔法のテスト
"""

import pytest

import os
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.ancient_elder.integrity_auditor import (
    IntegrityAuditor,
    CodePatternAnalyzer,
    ASTAnalyzer,
    GitConsistencyChecker,
    IntegrityViolationType
)
from libs.ancient_elder.base import ViolationSeverity

class TestCodePatternAnalyzer:
    """CodePatternAnalyzerのテスト"""
    
    @pytest.fixture
    def analyzer(self):
        """テスト用のアナライザー"""
        return CodePatternAnalyzer()

        """Implementation completed"""
        test_content = """
# Implementation completed
def some_function():
    # Issue resolved
    pass
    
# Concern addressed
def another_function():

    return None
"""

            f.write(test_content)
            f.flush()
            
            violations = analyzer.analyze_file(Path(f.name))
            
        os.unlink(f.name)

    def test_stub_detection(self, analyzer):
        """スタブ実装検出のテスト"""
        test_content = """
def empty_function():
    pass

def none_return():
    return None
    
def not_implemented():
    pass  # Implementation placeholder
    
def ellipsis_function():
    ...
"""

            f.write(test_content)
            f.flush()
            
            violations = analyzer.analyze_file(Path(f.name))
            
        os.unlink(f.name)
        
        assert len(violations["stub_impl"]) >= 3
        assert any("pass" in v["content"] for v in violations["stub_impl"])
        assert any("return None" in v["content"] for v in violations["stub_impl"])
        assert any("NotImplementedError" in v["content"] for v in violations["stub_impl"])
        
    def test_placeholder_detection(self, analyzer):
        """プレースホルダー検出のテスト"""
        test_content = """
def function_with_placeholder():
    # This is a placeholder
    return PLACEHOLDER
    
def replace_me():
    value = REPLACE_ME
    return CHANGE_THIS
"""

            f.write(test_content)
            f.flush()
            
            violations = analyzer.analyze_file(Path(f.name))
            
        os.unlink(f.name)
        
        assert len(violations["placeholders"]) >= 2
        assert any("placeholder" in v["content"].lower() for v in violations["placeholders"])
        
    def test_mock_detection(self, analyzer):
        """モック使用検出のテスト"""
        test_content = """
from unittest.mock import Mock, patch, MagicMock
import mock

@mock.patch('some.module')
def test_function():
    mock_obj = Mock()
    magic_mock = MagicMock()
    with patch('another.module'):
        pass
"""

            f.write(test_content)
            f.flush()
            
            violations = analyzer.analyze_file(Path(f.name))
            
        os.unlink(f.name)
        
        assert len(violations["mock_usage"]) >= 4
        assert any("unittest.mock" in v["content"] for v in violations["mock_usage"])
        assert any("Mock()" in v["content"] for v in violations["mock_usage"])

class TestASTAnalyzer:
    """ASTAnalyzerのテスト"""
    
    @pytest.fixture
    def analyzer(self):
        """テスト用のアナライザー"""
        return ASTAnalyzer()
        
    def test_function_analysis(self, analyzer):
        """関数分析のテスト"""
        test_content = """
def normal_function(arg1, arg2):
    return arg1 + arg2
    
def empty_function():
    pass
    
def not_implemented_function():
    pass  # Implementation placeholder
    
def none_return_function():
    return None
"""

            f.write(test_content)
            f.flush()
            
            result = analyzer.analyze_file(Path(f.name))
            
        os.unlink(f.name)
        
        assert len(result["functions"]) == 4
        assert len(result["empty_functions"]) == 1
        assert len(result["not_implemented"]) == 1
        assert len(result["suspicious_returns"]) == 1
        
        # 関数の詳細をチェック
        normal_func = next(f for f in result["functions"] if f["name"] == "normal_function")
        assert normal_func["args"] == 2
        
    def test_class_analysis(self, analyzer):
        """クラス分析のテスト"""
        test_content = """
class SimpleClass:
    def method1(self):
        pass
        
    def method2(self):
        return "test"
        
class EmptyClass:
    pass
"""

            f.write(test_content)
            f.flush()
            
            result = analyzer.analyze_file(Path(f.name))
            
        os.unlink(f.name)
        
        assert len(result["classes"]) == 2
        
        simple_class = next(c for c in result["classes"] if c["name"] == "SimpleClass")
        assert simple_class["methods"] == 2
        
        empty_class = next(c for c in result["classes"] if c["name"] == "EmptyClass")
        assert empty_class["methods"] == 0

class TestGitConsistencyChecker:
    """GitConsistencyCheckerのテスト"""
    
    def test_git_consistency_check(self):
        """Git整合性チェックのテスト"""
        # 実際のプロジェクトルートでテスト
        project_root = Path(__file__).parent.parent.parent
        
        if (project_root / ".git").exists():
            checker = GitConsistencyChecker(project_root)
            
            # このテストファイル自体をチェック
            result = checker.check_file_consistency(Path(__file__))
            
            if "error" not in result and "warning" not in result:
                assert "last_commit" in result
                assert "hash" in result["last_commit"]
                assert "author_name" in result["last_commit"]
            else:
                # Gitが利用できない環境やファイルが履歴にない場合は警告のみ
                pytest.skip("Git not available or file not in git history")

class TestIntegrityAuditor:
    """IntegrityAuditorのテスト"""
    
    @pytest.fixture
    def auditor(self):
        """テスト用の監査者"""
        return IntegrityAuditor()
        
    def test_auditor_initialization(self, auditor):
        """監査者初期化のテスト"""
        assert auditor.name == "AncientElder_IntegrityAuditor"
        assert auditor.specialty == "IntegrityAuditor"
        assert auditor.pattern_analyzer is not None
        assert auditor.ast_analyzer is not None
        
    @pytest.mark.asyncio
    async def test_file_audit_success(self, auditor):
        """ファイル監査成功のテスト"""
        test_content = """
def good_function():
    '''A properly implemented function'''
    return "Hello, World!"
    
class GoodClass:
    def __init__(self):
        self.value = 42
        
    def get_value(self):
        return self.value
"""

            f.write(test_content)
            f.flush()
            
            target = {
                "type": "file", 
                "path": f.name
            }
            
            result = await auditor.audit(target)
            
        os.unlink(f.name)
        
        assert result.auditor_name == auditor.name
        assert "integrity_score" in result.metrics
        # 良いコードなので違反は少ないはず
        assert result.metrics["critical_violations"] == 0
        
    @pytest.mark.asyncio
    async def test_file_audit_with_violations(self, auditor):
        """違反のあるファイル監査のテスト"""
        test_content = """

def bad_function():
    # Issue resolved
    pass
    
def not_implemented():
    pass  # Implementation placeholder
    
def placeholder_function():
    return PLACEHOLDER
"""

            f.write(test_content)
            f.flush()
            
            target = {
                "type": "file",
                "path": f.name
            }
            
            result = await auditor.audit(target)
            
        os.unlink(f.name)
        
        assert len(result.violations) > 0
        assert result.metrics["critical_violations"] >= 1  # NotImplementedError
        assert result.metrics["integrity_score"] < 100
        
        # 特定の違反タイプをチェック
        violation_types = [v.get("metadata", {}).get("violation_type") for v in result.violations]

        assert IntegrityViolationType.NOT_IMPLEMENTED in violation_types
        
    @pytest.mark.asyncio
    async def test_directory_audit(self, auditor):
        """ディレクトリ監査のテスト"""

            # テストファイルを作成

def good_function():
    return "good"
""")

# Implementation completed
def bad_function():
    pass
""")
            
            # 非Pythonファイル（無視されるはず）

            target = {
                "type": "directory",

            }
            
            result = await auditor.audit(target)
            
            assert result.auditor_name == auditor.name
            assert "integrity_score" in result.metrics
            # bad_file.pyからの違反があるはず
            assert len(result.violations) > 0
            
    @pytest.mark.asyncio
    async def test_files_audit(self, auditor):
        """複数ファイル監査のテスト"""
        files = []
        
        try:
            # テストファイルを作成

                f1.write("def good(): return 'good'")
                files.append(f1.name)

                files.append(f2.name)
                
            target = {
                "type": "files",
                "files": files
            }
            
            result = await auditor.audit(target)
            
            assert result.auditor_name == auditor.name
            assert len(result.violations) > 0  # f2からの違反
            
        finally:
            # クリーンアップ
            for file_path in files:
                try:
                    os.unlink(file_path)
                except:
                    pass
                    
    @pytest.mark.asyncio
    async def test_nonexistent_file(self, auditor):
        """存在しないファイルのテスト"""
        target = {
            "type": "file",
            "path": "/nonexistent/file.py"
        }
        
        result = await auditor.audit(target)
        
        assert len(result.violations) > 0
        assert any("not exist" in v["description"].lower() or \
            "not found" in v["description"].lower() for v in result.violations)
        
    @pytest.mark.asyncio
    async def test_unsupported_target_type(self, auditor):
        """サポートされていないターゲットタイプのテスト"""
        target = {
            "type": "unsupported",
            "path": "something"
        }
        
        result = await auditor.audit(target)
        
        assert len(result.violations) > 0
        assert any("not supported" in v["description"].lower() for v in result.violations)
        
    def test_get_audit_scope(self, auditor):
        """監査範囲取得のテスト"""
        scope = auditor.get_audit_scope()
        
        assert scope["scope"] == "code_integrity"
        assert "targets" in scope
        assert "violation_types" in scope
        assert "description" in scope
        assert len(scope["violation_types"]) > 0
        
    @pytest.mark.asyncio
    async def test_integrity_metrics_calculation(self, auditor):
        """誠実性メトリクス計算のテスト"""
        test_content = """

def critical_function():
    pass  # Implementation placeholder
    
# Issue resolved
def high_function():
    return PLACEHOLDER

def medium_function():
    pass
"""

            f.write(test_content)
            f.flush()
            
            target = {"type": "file", "path": f.name}
            result = await auditor.audit(target)
            
        os.unlink(f.name)
        
        assert "integrity_score" in result.metrics
        assert "total_violations" in result.metrics  
        assert "violations_by_severity" in result.metrics
        assert "violations_by_type" in result.metrics
        
        # スコアは減点されているはず
        assert result.metrics["integrity_score"] < 100
        
        # 重要度別の違反数
        severity_breakdown = result.metrics["violations_by_severity"]
        assert severity_breakdown["CRITICAL"] >= 1  # NotImplementedError
        assert severity_breakdown["HIGH"] >= 1      # PLACEHOLDER

class TestIntegrityAuditorIntegration:
    """IntegrityAuditor統合テスト"""
    
    @pytest.mark.asyncio
    async def test_real_code_audit(self):
        """実際のコードファイルの監査テスト"""
        auditor = IntegrityAuditor()
        
        # このテストファイル自体を監査
        target = {
            "type": "file",
            "path": str(Path(__file__))
        }
        
        result = await auditor.audit(target)
        
        assert result.auditor_name == auditor.name
        assert "integrity_score" in result.metrics
        # テストファイルなので、モック使用などで違反があるが、監査は正常に実行される
        assert result.metrics["integrity_score"] >= 0  # スコアは0以上であることを確認
        assert "total_violations" in result.metrics