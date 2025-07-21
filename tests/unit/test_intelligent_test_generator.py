#!/usr/bin/env python3
"""
Tests for Intelligent Test Generator
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch

from libs.intelligent_test_generator import (
    CodeAnalyzer,
    UnitTestGenerator,
    PropertyTestGenerator,
    IntegrationTestGenerator,
    IntelligentTestGenerator,
    TestCase,
    TestSuite
)


class TestCodeAnalyzer:
    """コード分析器のテスト"""
    
    def setup_method(self):
        self.analyzer = CodeAnalyzer()
    
    def test_analyze_simple_class(self):
        """簡単なクラスの分析"""
        code = '''
import boto3
from typing import Dict

class S3Manager:
    def __init__(self, region='us-east-1'):
        self.s3_client = boto3.client('s3', region_name=region)
    
    def create_bucket(self, bucket_name: str) -> Dict:
        try:
            response = self.s3_client.create_bucket(Bucket=bucket_name)
            return {"status": "success", "response": response}
        except Exception as e:
            raise ValueError(f"Failed to create bucket: {e}")
'''
        
        analysis = self.analyzer.analyze_implementation(code)
        
        # クラス分析
        assert len(analysis['classes']) == 1
        s3_class = analysis['classes'][0]
        assert s3_class['name'] == 'S3Manager'
        assert s3_class['has_init'] == True
        assert len(s3_class['methods']) == 2  # __init__ + create_bucket
        
        # メソッド分析
        create_method = next(m for m in s3_class['methods'] if m['name'] == 'create_bucket')
        assert create_method['has_return'] == True
        assert create_method['calls_external'] == True
        assert 'ValueError' in create_method['raises_exceptions']
        
        # 外部依存関係
        assert 'aws_service' in analysis['external_dependencies']
        
        # インポート
        assert len(analysis['imports']) >= 2
        boto3_import = next((imp for imp in analysis['imports'] if imp['module'] == 'boto3'), None)
        assert boto3_import is not None
    
    def test_analyze_async_function(self):
        """非同期関数の分析"""
        code = '''
import asyncio
import aiohttp

async def fetch_data(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
'''
        
        analysis = self.analyzer.analyze_implementation(code)
        
        # 関数分析
        assert len(analysis['functions']) == 1
        fetch_func = analysis['functions'][0]
        assert fetch_func['name'] == 'fetch_data'
        assert fetch_func['is_async'] == True
        assert fetch_func['has_return'] == True
        
        # 外部依存
        assert 'http_api' in analysis['external_dependencies']
    
    def test_analyze_complex_code(self):
        """複雑なコードの分析"""
        code = '''
import boto3
import logging
from typing import Dict, List, Optional

class ComplexService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
    
    async def process_data(self, data: List[Dict]) -> Optional[Dict]:
        try:
            if not data:
                return None
            
            for item in data:
                if item.get('type') == 'file':
                    await self._upload_to_s3(item)
                elif item.get('type') == 'record':
                    self._save_to_dynamo(item)
                else:
                    self.logger.warning(f"Unknown type: {item.get('type')}")
            
            return {"processed": len(data), "status": "complete"}
            
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            raise
    
    async def _upload_to_s3(self, item: Dict):
        # Private method implementation
        pass
    
    def _save_to_dynamo(self, item: Dict):
        # Private method implementation  
        pass
'''
        
        analysis = self.analyzer.analyze_implementation(code)
        
        # 複雑度分析
        complexity = analysis['complexity_indicators']
        assert complexity['cyclomatic'] > 2  # if/elif/else + for
        assert complexity['nesting_depth'] >= 2  # nested if in for
        assert complexity['external_calls'] > 3
        assert complexity['exception_handling'] >= 1
        
        # テスト可能メソッド（パブリックのみ）
        testable = analysis['testable_methods']
        public_methods = [m for m in testable if not m['name'].startswith('_')]
        assert len(public_methods) >= 1  # process_data
        
        process_method = next((m for m in testable if m['name'] == 'process_data'), None)
        assert process_method is not None
        assert 'integration' in process_method['test_types']
        assert 'mock' in process_method['test_types']


class TestUnitTestGenerator:
    """ユニットテスト生成器のテスト"""
    
    def setup_method(self):
        self.generator = UnitTestGenerator()
    
    def test_generate_class_init_test(self):
        """クラス初期化テスト生成"""
        intelligence = {'primary_domain': 'aws'}
        test_case = self.generator._generate_init_test('S3Manager', intelligence)
        
        assert test_case.name == 'test_s3manager_initialization'
        assert test_case.test_type == 'unit'
        assert 'region_name=' in test_case.code
        assert 'assert instance is not None' in test_case.code
    
    def test_generate_method_test_aws(self):
        """AWSメソッドテスト生成"""
        method_info = {
            'name': 'create_bucket',
            'args': ['self', 'bucket_name'],
            'has_return': True,
            'calls_external': True,
            'is_async': False
        }
        intelligence = {'primary_domain': 'aws'}
        
        test_case = self.generator._generate_method_test('S3Manager', method_info, intelligence)
        
        assert test_case.name == 'test_s3manager_create_bucket'
        assert 'bucket_name = "test-bucket-name"' in test_case.code
        assert 'result =' in test_case.code
        assert 'assert' in test_case.code
    
    def test_generate_async_method_test(self):
        """非同期メソッドテスト生成"""
        method_info = {
            'name': 'fetch_data',
            'args': ['url'],
            'has_return': True,
            'calls_external': True,
            'is_async': True
        }
        intelligence = {'primary_domain': 'web'}
        
        test_case = self.generator._generate_method_test('APIClient', method_info, intelligence)
        
        assert 'await ' in test_case.code
        assert 'test_apiclient_fetch_data' in test_case.name
    
    def test_generate_function_test(self):
        """関数テスト生成"""
        func_info = {
            'name': 'calculate_total',
            'args': ['items', 'tax_rate'],
            'has_return': True,
            'calls_external': False,
            'is_async': False
        }
        
        tests = self.generator._generate_function_tests(func_info, None)
        
        assert len(tests) == 1
        test = tests[0]
        assert test.name == 'test_calculate_total'
        assert 'items = "test_value"' in test.code
        assert 'tax_rate = "test_value"' in test.code


class TestPropertyTestGenerator:
    """プロパティテスト生成器のテスト"""
    
    def setup_method(self):
        self.generator = PropertyTestGenerator()
    
    def test_generate_property_test_aws(self):
        """AWSプロパティテスト生成"""
        method_info = {
            'name': 'validate_bucket_name',
            'test_types': ['unit', 'property']
        }
        intelligence = {'primary_domain': 'aws'}
        
        test_case = self.generator._generate_property_test(method_info, intelligence)
        
        assert test_case.name == 'test_validate_bucket_name_property'
        assert test_case.test_type == 'property'
        assert '@given(' in test_case.code
        assert 'assume(' in test_case.code
        assert 'min_size=3, max_size=63' in test_case.code  # AWS bucket name constraints
    
    def test_generate_strategies_web(self):
        """Web用ストラテジー生成"""
        method_info = {'name': 'process_json'}
        intelligence = {'primary_domain': 'web'}
        
        strategies = self.generator._generate_strategies(method_info, intelligence)
        
        assert 'st.dictionaries' in strategies
        assert 'st.text()' in strategies
    
    def test_skip_without_hypothesis(self):
        """Hypothesis なしの場合のスキップ"""
        with patch('libs.intelligent_test_generator.HYPOTHESIS_AVAILABLE', False):
            generator = PropertyTestGenerator()
            tests = generator.generate_property_tests({}, None)
            assert tests == []


class TestIntegrationTestGenerator:
    """統合テスト生成器のテスト"""
    
    def setup_method(self):
        self.generator = IntegrationTestGenerator()
    
    def test_generate_aws_integration_test(self):
        """AWS統合テスト生成"""
        intelligence = {'primary_domain': 'aws'}
        test_case = self.generator._generate_aws_integration_test(intelligence)
        
        assert test_case.name == 'test_aws_service_integration'
        assert test_case.test_type == 'integration'
        assert '@pytest.mark.integration' in test_case.code
        assert '@pytest.mark.aws' in test_case.code
        assert 'mock_aws()' in test_case.code
        assert 'moto' in test_case.dependencies
    
    def test_generate_api_integration_test(self):
        """API統合テスト生成"""
        intelligence = {'primary_domain': 'web'}
        test_case = self.generator._generate_api_integration_test(intelligence)
        
        assert test_case.name == 'test_api_integration'
        assert 'TestClient' in test_case.code
        assert 'response.status_code == 200' in test_case.code
        assert 'fastapi.testclient' in test_case.dependencies
    
    def test_generate_multiple_integration_tests(self):
        """複数統合テスト生成"""
        analysis = {
            'external_dependencies': ['aws_service', 'http_api', 'database']
        }
        
        tests = self.generator.generate_integration_tests(analysis, None)
        
        assert len(tests) == 3
        test_names = [t.name for t in tests]
        assert 'test_aws_service_integration' in test_names
        assert 'test_api_integration' in test_names
        assert 'test_database_integration' in test_names


class TestIntelligentTestGenerator:
    """インテリジェントテスト生成器のテスト"""
    
    def setup_method(self):
        self.generator = IntelligentTestGenerator()
    
    def test_generate_comprehensive_tests_aws(self):
        """AWS実装の包括的テスト生成"""
        implementation_code = '''
import boto3
from botocore.exceptions import ClientError

class S3Service:
    def __init__(self, region='us-east-1'):
        self.s3_client = boto3.client('s3', region_name=region)
    
    def create_bucket(self, bucket_name: str):
        try:
            response = self.s3_client.create_bucket(Bucket=bucket_name)
            return {"status": "success", "response": response}
        except ClientError as e:
            raise e
'''
        
        intelligence = {
            'primary_domain': 'aws',
            'tech_requirements': [{'name': 'aws_s3', 'category': 'aws'}],
            'implementation_hints': ['boto3.client("s3")']
        }
        
        test_suite = self.generator.generate_comprehensive_tests(
            implementation_code, intelligence
        )
        
        # テストスイート構成確認
        assert isinstance(test_suite, TestSuite)
        assert len(test_suite.unit_tests) > 0
        assert len(test_suite.integration_tests) > 0
        
        # ユニットテスト確認
        unit_test_names = [t.name for t in test_suite.unit_tests]
        assert any('s3service' in name for name in unit_test_names)
        assert any('create_bucket' in name for name in unit_test_names)
        
        # 統合テスト確認
        integration_test = test_suite.integration_tests[0]
        assert integration_test.test_type == 'integration'
        assert 'aws' in integration_test.code.lower()
        
        # モック設定確認
        assert 'aws' in test_suite.mock_configurations
        assert test_suite.mock_configurations['aws']['mock_type'] == 'moto'
        
        # フィクスチャ確認
        assert len(test_suite.fixtures) > 0
        fixture_code = '\n'.join(test_suite.fixtures)
        assert 'sample_data' in fixture_code
        assert 'aws_credentials' in fixture_code
    
    def test_generate_comprehensive_tests_web(self):
        """Web API実装の包括的テスト生成"""
        implementation_code = '''
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/api/data', methods=['POST'])
def process_data():
    data = request.get_json()
    
    # External API call
    response = requests.post('https://external-api.com/process', json=data)
    
    if response.status_code == 200:
        return jsonify({"status": "success", "result": response.json()})
    else:
        return jsonify({"status": "error"}), 500
'''
        
        intelligence = {
            'primary_domain': 'web',
            'tech_requirements': [{'name': 'web_flask', 'category': 'web'}]
        }
        
        test_suite = self.generator.generate_comprehensive_tests(
            implementation_code, intelligence
        )
        
        # Web特有のテスト確認
        assert len(test_suite.unit_tests) > 0
        assert len(test_suite.integration_tests) > 0
        
        # HTTP関連のモック設定
        assert 'http' in test_suite.mock_configurations
        assert test_suite.mock_configurations['http']['mock_type'] == 'requests_mock'
    
    def test_generate_tests_with_codebase_learning(self):
        """コードベース学習結果を活用したテスト生成"""
        implementation_code = '''
class DataProcessor:
    def __init__(self):
        self.initialized = True
    
    def process(self, data):
        return {"processed": len(data)}
'''
        
        # モックのコードベース学習結果
        codebase_intelligence = Mock()
        codebase_intelligence.class_patterns = [
            Mock(name='BaseService', tech_domain='general'),
            Mock(name='DataProcessor', tech_domain='data')
        ]
        
        test_suite = self.generator.generate_comprehensive_tests(
            implementation_code, None, codebase_intelligence
        )
        
        # コードベース学習ベースのフィクスチャが生成される
        assert len(test_suite.fixtures) > 0
        fixture_code = '\n'.join(test_suite.fixtures)
        assert 'mock_' in fixture_code.lower()
    
    def test_mock_configuration_generation(self):
        """モック設定生成のテスト"""
        analysis = {
            'external_dependencies': ['aws_service', 'http_api']
        }
        intelligence = {'primary_domain': 'aws'}
        
        mock_configs = self.generator._generate_mock_configurations(analysis, intelligence)
        
        # AWS モック設定
        assert 'aws' in mock_configs
        assert mock_configs['aws']['mock_type'] == 'moto'
        assert 's3' in mock_configs['aws']['services']
        
        # HTTP モック設定
        assert 'http' in mock_configs
        assert mock_configs['http']['mock_type'] == 'requests_mock'
    
    def test_fixtures_generation(self):
        """フィクスチャ生成のテスト"""
        analysis = {'classes': [{'name': 'TestClass'}]}
        intelligence = {'primary_domain': 'aws'}
        
        fixtures = self.generator._generate_fixtures(analysis, intelligence, None)
        
        # 基本フィクスチャ
        assert len(fixtures) >= 2
        fixture_code = '\n'.join(fixtures)
        assert '@pytest.fixture' in fixture_code
        assert 'sample_data' in fixture_code
        assert 'aws_credentials' in fixture_code


if __name__ == "__main__":
    pytest.main([__file__])