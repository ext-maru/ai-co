#!/usr/bin/env python3
"""
Tests for Codebase Analysis Engine
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from libs.codebase_analysis_engine import (
    ASTAnalyzer,
    PatternExtractor,
    CodebaseAnalysisEngine,
    ImportPattern,
    ClassPattern,
    MethodPattern,
    CodebaseIntelligence
)


class TestASTAnalyzer:
    """AST解析エンジンのテスト"""
    
    def setup_method(self):
        self.analyzer = ASTAnalyzer()
    
    def test_analyze_simple_file(self):
        """簡単なPythonファイルの解析"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
import os
import boto3
from typing import Dict

class TestClass:
    """Test class"""
    
    def __init__(self):
        self.initialized = True
    
    async def test_method(self, param: str) -> Dict:
        """Test method"""
        try:
            return {"status": "success"}
        except Exception as e:
            return {"error": str(e)}

def test_function():
    """Test function"""
    return "test"

TEST_CONSTANT = "test_value"
            ''')
            f.flush()
            
            analysis = self.analyzer.analyze_file(f.name)
            
            # インポートチェック
            imports = analysis['imports']
            assert len(imports) >= 3
            assert any(imp['module'] == 'os' for imp in imports)
            assert any(imp['module'] == 'boto3' for imp in imports)
            assert any(imp['module'] == 'Dict' and imp['from_module'] == 'typing' for imp in imports)
            
            # クラスチェック
            classes = analysis['classes']
            assert len(classes) == 1
            assert classes[0]['name'] == 'TestClass'
            assert len(classes[0]['methods']) == 2  # __init__ and test_method
            
            # 関数チェック
            functions = analysis['functions']
            assert len(functions) == 1
            assert functions[0]['name'] == 'test_function'
            
            # 定数チェック
            constants = analysis['constants']
            assert len(constants) == 1
            assert constants[0]['name'] == 'TEST_CONSTANT'
            
            # 技術指標チェック
            tech_indicators = analysis['tech_indicators']
            assert 'aws' in tech_indicators
            assert tech_indicators['aws'] > 0  # boto3があるため
            
            # エラーパターンチェック
            error_patterns = analysis['error_patterns']
            assert 'Exception' in error_patterns
            
        os.unlink(f.name)
    
    def test_analyze_aws_file(self):
        """AWS関連ファイルの解析"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
import boto3
from botocore.exceptions import ClientError

class S3Manager:
    def __init__(self):
        self.s3_client = boto3.client('s3')
    
    def create_bucket(self, bucket_name: str):
        try:
            response = self.s3_client.create_bucket(Bucket=bucket_name)
            return response
        except ClientError as e:
            raise e
            ''')
            f.flush()
            
            analysis = self.analyzer.analyze_file(f.name)
            
            # AWS技術指標が高いことを確認
            tech_indicators = analysis['tech_indicators']
            assert tech_indicators['aws'] > 0.3
            
            # エラーパターンにClientErrorが含まれることを確認
            error_patterns = analysis['error_patterns']
            assert 'ClientError' in error_patterns
            
        os.unlink(f.name)
    
    def test_analyze_web_file(self):
        """Web関連ファイルの解析"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    data = request.get_json()
    return jsonify({"message": "success"})
            ''')
            f.flush()
            
            analysis = self.analyzer.analyze_file(f.name)
            
            # Web技術指標が高いことを確認
            tech_indicators = analysis['tech_indicators']
            assert tech_indicators['web'] > 0.3
            
        os.unlink(f.name)
    
    def test_analyze_invalid_file(self):
        """無効なファイルの解析（フォールバック）"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('invalid python syntax {{{')
            f.flush()
            
            analysis = self.analyzer.analyze_file(f.name)
            
            # フォールバック解析結果を確認
            assert analysis['analysis_failed'] == True
            assert analysis['imports'] == []
            assert analysis['classes'] == []
            
        os.unlink(f.name)


class TestPatternExtractor:
    """パターン抽出エンジンのテスト"""
    
    def setup_method(self):
        self.extractor = PatternExtractor()
    
    def test_extract_import_patterns(self):
        """インポートパターン抽出のテスト"""
        analyses = [
            {
                'imports': [
                    {'module': 'boto3', 'alias': None, 'from_module': None},
                    {'module': 'os', 'alias': None, 'from_module': None},
                    {'module': 'Dict', 'alias': None, 'from_module': 'typing'}
                ],
                'tech_indicators': {'aws': 0.8, 'web': 0.1}
            },
            {
                'imports': [
                    {'module': 'boto3', 'alias': None, 'from_module': None},
                    {'module': 'json', 'alias': None, 'from_module': None},
                    {'module': 'ClientError', 'alias': None, 'from_module': 'botocore.exceptions'}
                ],
                'tech_indicators': {'aws': 0.9, 'web': 0.0}
            }
        ]
        
        patterns = self.extractor.extract_import_patterns(analyses)
        
        # boto3が2回使用されているため抽出される
        boto3_pattern = next((p for p in patterns if p.module == 'boto3'), None)
        assert boto3_pattern is not None
        assert boto3_pattern.frequency == 2
        assert 'aws' in boto3_pattern.context
    
    def test_extract_class_patterns(self):
        """クラスパターン抽出のテスト"""
        analyses = [
            {
                'classes': [
                    {
                        'name': 'TestClass',
                        'base_classes': [],
                        'methods': [
                            {
                                'name': '__init__',
                                'args': ['self'],
                                'is_async': False,
                                'decorators': [],
                                'docstring': None,
                                'returns': None
                            },
                            {
                                'name': 'test_method',
                                'args': ['self',
                                'param'],
                                'is_async': True,
                                'decorators': [],
                                'docstring': 'Test method',
                                'returns': 'Dict'
                            }
                        ],
                        'attributes': ['initialized'],
                        'docstring': 'Test class',
                        'decorators': []
                    }
                ],
                'file_path': '/test/file.py',
                'tech_indicators': {'aws': 0.8, 'web': 0.1}
            }
        ]
        
        patterns = self.extractor.extract_class_patterns(analyses)
        
        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.name == 'TestClass'
        assert pattern.tech_domain == 'aws'
        assert 'test_method' in pattern.methods
        assert 'initialized' in pattern.attributes
    
    def test_extract_method_patterns(self):
        """メソッドパターン抽出のテスト"""
        analyses = [
            {
                'classes': [
                    {
                        'methods': [
                            {
                                'name': 'async_method',
                                'args': ['self'],
                                'is_async': True,
                                'decorators': ['property'],
                                'docstring': None,
                                'returns': None
                            }
                        ]
                    }
                ],
                'functions': [
                    {
                        'name': 'sync_function',
                        'args': ['param'],
                        'is_async': False,
                        'decorators': [],
                        'docstring': 'Test function',
                        'returns': 'str',
                        'error_handling': ['ValueError']
                    }
                ]
            }
        ]
        
        patterns = self.extractor.extract_method_patterns(analyses)
        
        assert len(patterns) == 2
        
        async_pattern = next((p for p in patterns if p.name == 'async_method'), None)
        assert async_pattern is not None
        assert async_pattern.is_async == True
        assert 'property' in async_pattern.decorators
        
        sync_pattern = next((p for p in patterns if p.name == 'sync_function'), None)
        assert sync_pattern is not None
        assert sync_pattern.is_async == False
        assert 'ValueError' in sync_pattern.error_handling
    
    def test_extract_error_handling_patterns(self):
        """エラーハンドリングパターン抽出のテスト"""
        analyses = [
            {'error_patterns': ['Exception', 'ValueError', 'ClientError']},
            {'error_patterns': ['Exception', 'TypeError', 'ClientError']},
            {'error_patterns': ['KeyError']}
        ]
        
        patterns = self.extractor.extract_error_handling_patterns(analyses)
        
        # 2回以上使用されているパターンのみ
        assert 'Exception' in patterns
        assert 'ClientError' in patterns
        assert 'KeyError' not in patterns  # 1回のみ
    
    def test_analyze_naming_conventions(self):
        """命名規則分析のテスト"""
        analyses = [
            {
                'classes': [
                    {'name': 'TestClass'},
                    {'name': 'AnotherClass'}
                ],
                'functions': [
                    {'name': 'test_function'},
                    {'name': 'another_function'}
                ]
            }
        ]
        
        conventions = self.extractor.analyze_naming_conventions(analyses)
        
        assert conventions['class_naming'] == 'PascalCase'
        assert conventions['function_naming'] == 'snake_case'


class TestCodebaseAnalysisEngine:
    """コードベース分析エンジンのテスト"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.engine = CodebaseAnalysisEngine(self.temp_dir)
    
    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_collect_python_files(self):
        """Pythonファイル収集のテスト"""
        # テストファイル作成
        test_file1 = Path(self.temp_dir) / "test1.py"
        test_file2 = Path(self.temp_dir) / "subdir" / "test2.py"
        exclude_file = Path(self.temp_dir) / "__pycache__" / "cached.py"
        
        test_file1.write_text("# test1")
        test_file2.parent.mkdir(exist_ok=True)
        test_file2.write_text("# test2")
        exclude_file.parent.mkdir(exist_ok=True)
        exclude_file.write_text("# cached")
        
        files = self.engine._collect_python_files()
        
        # 通常のPythonファイルは含まれる
        assert any(f.name == "test1.py" for f in files)
        assert any(f.name == "test2.py" for f in files)
        
        # __pycache__内のファイルは除外される
        assert not any(f.name == "cached.py" for f in files)
    
    def test_filter_relevant_files_aws(self):
        """AWS関連ファイルフィルタリングのテスト"""
        # AWSファイル作成
        aws_file = Path(self.temp_dir) / "aws_service.py"
        aws_file.write_text("import boto3\ns3_client = boto3.client('s3')")
        
        general_file = Path(self.temp_dir) / "general.py"
        general_file.write_text("import os\nprint('hello')")
        
        files = [aws_file, general_file]
        tech_stack = {'primary_stack': 'aws', 'services': ['s3']}
        
        relevant_files = self.engine._filter_relevant_files(files, tech_stack)
        
        # AWSファイルが優先される
        assert aws_file in relevant_files
        # 一般ファイルは含まれない（スコア0のため）
        assert general_file not in relevant_files
    
    def test_analyze_codebase_integration(self):
        """コードベース分析の統合テスト"""
        # テストファイル群作成
        aws_file = Path(self.temp_dir) / "aws_service.py"
        aws_file.write_text('''
import boto3
from botocore.exceptions import ClientError

class S3Service:
    def __init__(self):
        self.client = boto3.client('s3')
    
    def create_bucket(self, name: str):
        try:
            return self.client.create_bucket(Bucket=name)
        except ClientError as e:
            raise e
        ''')
        
        web_file = Path(self.temp_dir) / "web_api.py"
        web_file.write_text('''
from flask import Flask, request

app = Flask(__name__)

@app.route('/api/test')
def test_endpoint():
    return {"status": "ok"}
        ''')
        
        tech_stack = {'primary_stack': 'aws', 'services': ['s3']}
        intelligence = self.engine.analyze_codebase(tech_stack)
        
        assert isinstance(intelligence, CodebaseIntelligence)
        assert len(intelligence.import_patterns) > 0
        assert len(intelligence.class_patterns) > 0
        assert 'aws' in intelligence.tech_domains
        assert intelligence.tech_domains['aws'] > 0
    
    def test_find_similar_implementations_aws(self):
        """AWS類似実装検索のテスト"""
        # AWS関連ファイル作成
        aws_file1 = Path(self.temp_dir) / "s3_manager.py"
        aws_file1.write_text("import boto3\ns3 = boto3.client('s3')")
        
        aws_file2 = Path(self.temp_dir) / "dynamo_service.py"
        aws_file2.write_text("import boto3\ndynamodb = boto3.resource('dynamodb')")
        
        general_file = Path(self.temp_dir) / "utils.py"
        general_file.write_text("import os\nprint('utility')")
        
        tech_stack = {'primary_stack': 'aws', 'services': ['s3', 'dynamodb']}
        similar_files = self.engine.find_similar_implementations(tech_stack)
        
        # AWS関連ファイルが検索される
        assert any('s3_manager.py' in f for f in similar_files)
        assert any('dynamo_service.py' in f for f in similar_files)
        # 一般ファイルは検索されない
        assert not any('utils.py' in f for f in similar_files)
    
    @patch('libs.codebase_analysis_engine.Path.rglob')
    def test_analyze_codebase_empty_project(self, mock_rglob):
        """空プロジェクトの分析テスト"""
        mock_rglob.return_value = []
        
        tech_stack = {'primary_stack': 'general'}
        intelligence = self.engine.analyze_codebase(tech_stack)
        
        assert isinstance(intelligence, CodebaseIntelligence)
        assert len(intelligence.import_patterns) == 0
        assert len(intelligence.class_patterns) == 0
        assert len(intelligence.method_patterns) == 0


if __name__ == "__main__":
    pytest.main([__file__])