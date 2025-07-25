#!/usr/bin/env python3
"""
🧪 Elder Flow Pylintチェッカー テスト
エルダーフロー専用Pylintチェッカーのユニットテスト
"""

import pytest
import asyncio
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from elders_guild.elder_tree.elder_flow_pylint_checker import (
    PylintIssue,
    PylintResult,
    ElderFlowPylintChecker,
    pylint_check_file,
    pylint_check_directory
)


class TestPylintIssue:
    """PylintIssueクラスのテスト"""
    
    def test_pylint_issue_creation(self):
        """PylintIssue生成テスト"""
        issue = PylintIssue(
            type="error",
            module="test_module",
            obj="test_function",
            line=10,
            column=5,
            message_id="E0001",
            symbol="syntax-error",
            message="Syntax error in test_function"
        )
        
        assert issue.type == "error"
        assert issue.module == "test_module"
        assert issue.line == 10
        assert issue.severity == "critical"
        assert issue.elder_guild_category == "syntax_error"
        
    def test_severity_mapping(self):
        """重要度マッピングテスト"""
        # エラー → クリティカル
        error_issue = PylintIssue(
            type="error", module="", obj="", line=1, column=1,
            message_id="E0001", symbol="", message=""
        )
        assert error_issue.severity == "critical"
        
        # 警告 → 高
        warning_issue = PylintIssue(
            type="warning", module="", obj="", line=1, column=1,
            message_id="W0001", symbol="", message=""
        )
        assert warning_issue.severity == "high"
        
        # 規約 → 中
        convention_issue = PylintIssue(
            type="convention", module="", obj="", line=1, column=1,
            message_id="C0001", symbol="", message=""
        )
        assert convention_issue.severity == "medium"
        
    def test_category_classification(self):
        """カテゴリ分類テスト"""
        # Error → syntax_error
        error_issue = PylintIssue(
            type="error", module="", obj="", line=1, column=1,
            message_id="E0001", symbol="syntax-error", message=""
        )
        assert error_issue.elder_guild_category == "syntax_error"
        
        # Warning (unused) → unused_code
        unused_issue = PylintIssue(
            type="warning", module="", obj="", line=1, column=1,
            message_id="W0611", symbol="unused-import", message=""
        )
        assert unused_issue.elder_guild_category == "unused_code"
        
        # Warning (import) → import_issue
        import_issue = PylintIssue(
            type="warning", module="", obj="", line=1, column=1,
            message_id="W0401", symbol="wildcard-import", message=""
        )
        assert import_issue.elder_guild_category == "import_issue"
        
        # Refactor → complexity_issue
        refactor_issue = PylintIssue(
            type="refactor", module="", obj="", line=1, column=1,
            message_id="R0912", symbol="too-many-branches", message=""
        )
        assert refactor_issue.elder_guild_category == "complexity_issue"


class TestPylintResult:
    """PylintResultクラスのテスト"""
    
    def test_pylint_result_creation(self):
        """PylintResult生成テスト"""
        issues = [
            PylintIssue(
                type="error", module="test", obj="", line=1, column=1,
                message_id="E0001", symbol="", message=""
            ),
            PylintIssue(
                type="warning", module="test", obj="", line=2, column=1,
                message_id="W0001", symbol="", message=""
            )
        ]
        
        result = PylintResult(
            issues=issues,
            score=7.5,
            total_statements=100,
            analyzed_files=5
        )
        
        assert result.total_issues == 2
        assert result.score == 7.5
        assert result.analyzed_files == 5
        
    def test_issues_by_severity(self):
        """重要度別問題数テスト"""
        issues = [
            PylintIssue(
                type="error", module="", obj="", line=1, column=1,
                message_id="E0001", symbol="", message=""
            ),
            PylintIssue(
                type="error", module="", obj="", line=2, column=1,
                message_id="E0002", symbol="", message=""
            ),
            PylintIssue(
                type="warning", module="", obj="", line=3, column=1,
                message_id="W0001", symbol="", message=""
            ),
            PylintIssue(
                type="convention", module="", obj="", line=4, column=1,
                message_id="C0001", symbol="", message=""
            )
        ]
        
        result = PylintResult(issues=issues)
        severity_count = result.issues_by_severity
        
        assert severity_count['critical'] == 2  # 2 errors
        assert severity_count['high'] == 1      # 1 warning
        assert severity_count['medium'] == 1    # 1 convention
        
    def test_issues_by_category(self):
        """カテゴリ別問題数テスト"""
        issues = [
            PylintIssue(
                type="error", module="", obj="", line=1, column=1,
                message_id="E0001", symbol="syntax-error", message=""
            ),
            PylintIssue(
                type="warning", module="", obj="", line=2, column=1,
                message_id="W0611", symbol="unused-import", message=""
            ),
            PylintIssue(
                type="warning", module="", obj="", line=3, column=1,
                message_id="W0612", symbol="unused-variable", message=""
            )
        ]
        
        result = PylintResult(issues=issues)
        category_count = result.issues_by_category
        
        assert category_count['syntax_error'] == 1
        assert category_count['unused_code'] == 2


class TestElderFlowPylintChecker:
    """ElderFlowPylintCheckerクラスのテスト"""
    
    @pytest.fixture
    def checker(self)return ElderFlowPylintChecker()
    """チェッカーインスタンス作成"""
        
    @pytest.fixture
    def temp_python_file(self)with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    """テスト用Pythonファイル作成"""
            f.write('''
"""Test module"""
import os
import sys
import unused_module  # This will trigger unused-import

def bad_function(x, y):
    """Function with issues"""
    # TODO: Fix this later
    z = eval("x + y")  # Security issue
    
    if x > 10:
        if y > 20:
            if z > 30:
                if x + y + z > 60:
                    return True  # Too deeply nested
    
    magic_number = 42  # Magic number
    return magic_number

class BadClass:
    def __init__(self):
        pass
        
    def unused_method(self):
        pass
''')
            return f.name
            
    @pytest.mark.asyncio
    async def test_analyze_file(self, checker, temp_python_file):
        """ファイル分析テスト"""
        # モックPylint結果
        mock_result = PylintResult(
            issues=[
                PylintIssue(
                    type="error", module=temp_python_file, obj="bad_function",
                    line=9, column=8, message_id="W0123", symbol="eval-used",
                    message="Use of eval"
                ),
                PylintIssue(
                    type="warning", module=temp_python_file, obj="",
                    line=5, column=0, message_id="W0611", symbol="unused-import",
                    message="Unused import unused_module"
                )
            ],
            score=6.5,
            analyzed_files=1
        )
        
        with patch.object(checker, '_run_pylint', return_value=mock_result):
            result = await checker.analyze_file(temp_python_file)
            
            assert result['file'] == temp_python_file
            assert result['score'] == 6.5
            assert result['total_issues'] == 2
            assert 'critical_issues' in result
            assert 'high_priority_issues' in result
            assert result['quality_passed'] is False  # スコアが7.0未満
            assert len(result['recommendations']) > 0
            
    @pytest.mark.asyncio
    async def test_analyze_directory(self, checker, tmp_path):
        """ディレクトリ分析テスト"""
        # テストファイル作成
        (tmp_path / "test1.py").write_text("print('test1')")
        (tmp_path / "test2.py").write_text("print('test2')")
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "test.pyc").write_text("compiled")
        
        # モック結果
        mock_result = PylintResult(
            issues=[],
            score=9.5,
            analyzed_files=2
        )
        
        with patch.object(checker, '_run_pylint', return_value=mock_result):
            result = await checker.analyze_directory(str(tmp_path))
            
            assert result['directory'] == str(tmp_path)
            assert result['total_files'] >= 2
            assert result['analyzed_files'] == 2
            assert result['overall_score'] == 9.5
            assert result['quality_passed'] is True
            
    def test_check_quality_thresholds(self, checker):
        """品質基準チェックテスト"""
        # 合格ケース
        good_result = PylintResult(
            issues=[
                PylintIssue(
                    type="warning", module="", obj="", line=1, column=1,
                    message_id="W0001", symbol="", message=""
                )
            ],
            score=8.5
        )
        assert checker._check_quality_thresholds(good_result) is True
        
        # 不合格ケース（スコア不足）
        low_score_result = PylintResult(issues=[], score=6.0)
        assert checker._check_quality_thresholds(low_score_result) is False
        
        # 不合格ケース（クリティカル問題）
        critical_result = PylintResult(
            issues=[
                PylintIssue(
                    type="error", module="", obj="", line=1, column=1,
                    message_id="E0001", symbol="", message=""
                )
            ],
            score=8.0
        )
        assert checker._check_quality_thresholds(critical_result) is False
        
    def test_generate_recommendations(self, checker):
        """推奨事項生成テスト"""
        # 低スコアケース
        low_score_result = PylintResult(issues=[], score=4.5)
        recommendations = checker._generate_recommendations(low_score_result)
        assert any("Critical: Major refactoring needed" in r for r in recommendations)
        
        # 未使用コード多数ケース
        unused_issues = [
            PylintIssue(
                type="warning", module="", obj="", line=i, column=1,
                message_id="W0611", symbol="unused-import", message=""
            )
            for i in range(10):
        ]
        unused_result = PylintResult(issues=unused_issues, score=7.5)
        recommendations = checker._generate_recommendations(unused_result)
        assert any("Clean up unused imports" in r for r in recommendations)
        
        # 複雑度問題ケース
        complexity_issues = [
            PylintIssue(
                type="refactor", module="", obj="", line=i, column=1,
                message_id="R0912", symbol="too-many-branches", message=""
            )
            for i in range(5):
        ]
        complexity_result = PylintResult(issues=complexity_issues, score=7.5)
        recommendations = checker._generate_recommendations(complexity_result)
        assert any("Refactor complex functions" in r for r in recommendations)
        
        # Iron Will違反ケース
        todo_issue = PylintIssue(
            type="warning", module="", obj="", line=1, column=1,
            message_id="W0511", symbol="fixme", message="TODO found"
        )
        iron_will_result = PylintResult(issues=[todo_issue], score=8.0)
        
        # TODOが含まれているかチェック
        with patch.object(iron_will_result, '__str__', return_value="TODO"):
            recommendations = checker._generate_recommendations(iron_will_result)
            assert any("Iron Will: Remove TODO/FIXME" in r for r in recommendations)
            
    @pytest.mark.asyncio
    async def test_parse_pylint_output(self, checker):
        """Pylint出力パーステスト"""
        # JSON形式の出力
        json_output = '''[
{"type": "error", "module": "test", "obj": "func", "line": 1, "column": 0, 
 "message-id": "E0001", "symbol": "syntax-error", "message": "Syntax error"}
]
Your code has been rated at 7.50/10 (previous run: 8.00/10, -0.50)
'''
        
        result = checker._parse_pylint_output(json_output)
        
        assert len(result.issues) == 1
        assert result.issues[0].type == "error"
        assert result.score == 7.5
        assert result.previous_score == 8.0
        
    @pytest.mark.asyncio
    async def test_error_handling(self, checker):
        """エラーハンドリングテスト"""
        # 存在しないファイル
        result = await checker.analyze_file("/nonexistent/file.py")
        assert 'error' in result
        assert result['score'] == 0.0
        assert result['quality_passed'] is False
        
        # 空のディレクトリ
        with tempfile.TemporaryDirectory() as tmpdir:
            result = await checker.analyze_directory(tmpdir)
            assert result['total_files'] == 0


@pytest.mark.asyncio
async def test_convenience_functions()with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as ff.write("print('test')")
"""便利関数のテスト"""
        f.flush()
        
        # ファイルチェック
        with patch('libs.elder_flow_pylint_checker.ElderFlowPylintChecker.analyze_file',:
                   return_value={'score': 10.0}):
            result = await pylint_check_file(f.name)
            assert result['score'] == 10.0
            
    # ディレクトリチェック
    with patch('libs.elder_flow_pylint_checker.ElderFlowPylintChecker.analyze_directory',:
               return_value={'overall_score': 9.0}):
        result = await pylint_check_directory("/tmp")
        assert result['overall_score'] == 9.0