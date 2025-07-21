#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏛️ Ancient Elder - StrictOutputValidator TDD Tests
エンシェントエルダー厳格出力検証システムテスト

Test coverage: Comprehensive validation tests
Creation date: 2025-01-20
Test approach: Red-Green-Refactor TDD cycle
"""

import pytest
import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch
from dataclasses import dataclass
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from libs.ancient_elder.strict_output_validator import (
        StrictOutputValidator,
        ValidationResult,
        CodeQualityScore,
        SecurityRisk,
        IssueLevel
    )
except ImportError:
    # Create mock classes for TDD Red phase
    @dataclass
    class ValidationResult:
        score: float
        passed: bool
        issues: List[Dict[str, Any]]
        suggestions: List[str]
        details: Dict[str, Any]
        
    @dataclass  
    class CodeQualityScore:
        syntax_score: float
        logic_score: float
        performance_score: float
        security_score: float
        maintainability_score: float
        scalability_score: float
        overall_score: float
        
    class SecurityRisk:
        LOW = "low"
        MEDIUM = "medium" 
        HIGH = "high"
        CRITICAL = "critical"
        
    class IssueLevel:
        INFO = "info"
        WARNING = "warning"
        ERROR = "error"
        CRITICAL = "critical"
        
    class StrictOutputValidator:
        def __init__(self):
            pass
            
        def validate_comprehensive(self, code: str) -> ValidationResult:
            return ValidationResult(0.0, False, [], [], {})
            
        def _syntax_validation(self, code: str) -> Dict[str, Any]:
            return {'passed': False, 'score': 0.0}
            
        def _logic_validation(self, code: str) -> Dict[str, Any]:
            return {'passed': False, 'score': 0.0}
            
        def _performance_validation(self, code: str) -> Dict[str, Any]:
            return {'passed': False, 'score': 0.0}
            
        def _security_penetration_test(self, code: str) -> Dict[str, Any]:
            return {'passed': False, 'score': 0.0}
            
        def _maintainability_audit(self, code: str) -> Dict[str, Any]:
            return {'passed': False, 'score': 0.0}
            
        def _scalability_stress_test(self, code: str) -> Dict[str, Any]:
            return {'passed': False, 'score': 0.0}
            
        def calculate_quality_score(self, code: str) -> CodeQualityScore:
            return CodeQualityScore(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


class TestStrictOutputValidator:
    """🔴 Red Phase: 厳格出力検証システムTDDテスト"""
    
    def setup_method(self):
        """🔧 テスト環境セットアップ"""
        self.validator = StrictOutputValidator()
        
    def test_validator_initialization(self):
        """🔴 Red: バリデーター初期化テスト"""
        validator = StrictOutputValidator()
        assert validator is not None
        
    def test_syntax_validation_valid_code(self):
        """🔴 Red: 構文検証 - 有効なコード"""
        valid_code = """
def hello_world():
    print("Hello, World!")
    return True
"""
        result = self.validator._syntax_validation(valid_code)
        assert result['passed'] is True
        assert result['score'] >= 0.8  # 高得点期待
        
    def test_syntax_validation_invalid_code(self):
        """🔴 Red: 構文検証 - 無効なコード"""
        invalid_code = """
def hello_world(:  # 構文エラー
    print("Hello, World!"
    return True
"""
        result = self.validator._syntax_validation(invalid_code)
        assert result['passed'] is False
        assert result['score'] < 0.3  # 低得点期待
        
    def test_logic_validation_correct_logic(self):
        """🔴 Red: 論理検証 - 正しい論理"""
        correct_code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""
        result = self.validator._logic_validation(correct_code)
        assert result['passed'] is True
        assert result['score'] >= 0.7
        
    def test_logic_validation_flawed_logic(self):
        """🔴 Red: 論理検証 - 欠陥のある論理"""
        flawed_code = """
def divide(a, b):
    return a / b  # ゼロ除算チェックなし
"""
        result = self.validator._logic_validation(flawed_code)
        assert result['passed'] is False
        assert 'division by zero' in str(result).lower()
        
    def test_performance_validation_efficient_code(self):
        """🔴 Red: パフォーマンス検証 - 効率的なコード"""
        efficient_code = """
def binary_search(arr, x):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == x:
            return mid
        elif arr[mid] < x:
            left = mid + 1
        else:
            right = mid - 1
    return -1
"""
        result = self.validator._performance_validation(efficient_code)
        assert result['passed'] is True
        assert result['score'] >= 0.8
        
    def test_performance_validation_inefficient_code(self):
        """🔴 Red: パフォーマンス検証 - 非効率なコード"""
        inefficient_code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            for k in range(100):  # 不要なネストループ
                if arr[j] > arr[j+1]:
                    arr[j], arr[j+1] = arr[j+1], arr[j]
"""
        result = self.validator._performance_validation(inefficient_code)
        assert result['passed'] is False
        assert result['score'] < 0.4
        
    def test_security_penetration_test(self):
        """🔴 Red: セキュリティ侵入テストテスト"""
        dangerous_code = """
import os
def execute_command(cmd):
    os.system(cmd)  # セキュリティリスク: 任意コマンド実行
"""
        result = self.validator._security_penetration_test(dangerous_code)
        assert result['passed'] is False  # セキュリティリスクで失敗するはず
        assert result['risk_level'] in [SecurityRisk.HIGH, SecurityRisk.CRITICAL]
        
    def test_security_safe_code(self):
        """🔴 Red: セキュリティ - 安全なコード"""
        safe_code = """
import hashlib
def hash_password(password: str) -> str:
    salt = "secure_salt"
    return hashlib.sha256((password + salt).encode()).hexdigest()
"""
        result = self.validator._security_penetration_test(safe_code)
        assert result['passed'] is True
        assert result['risk_level'] == SecurityRisk.LOW
        
    def test_maintainability_audit_good_code(self):
        """🔴 Red: 保守性監査 - 良いコード"""
        good_code = """
class Calculator:
    \"\"\"電卓クラス - 基本的な数学演算を提供\"\"\"
    
    def add(self, a: float, b: float) -> float:
        \"\"\"二つの数値を足す\"\"\"
        return a + b
        
    def divide(self, a: float, b: float) -> float:
        \"\"\"二つの数値を割る\"\"\"
        if b == 0:
            raise ValueError("ゼロで割ることはできません")
        return a / b
"""
        result = self.validator._maintainability_audit(good_code)
        assert result['passed'] is True
        assert result['score'] >= 0.8
        
    def test_maintainability_audit_bad_code(self):
        """🔴 Red: 保守性監査 - 悪いコード"""
        bad_code = """
def x(a,b,c,d,e,f,g,h,i,j):  # 多すぎる引数
    if a:
        if b:
            if c:
                if d:
                    if e:  # 深すぎるネスト
                        return f+g+h+i+j
"""
        result = self.validator._maintainability_audit(bad_code)
        assert result['passed'] is False
        assert result['score'] < 0.4
        
    def test_scalability_stress_test(self):
        """🔴 Red: 拡張性ストレステスト"""
        scalable_code = """
from concurrent.futures import ThreadPoolExecutor
import asyncio

class ScalableProcessor:
    def __init__(self, max_workers=10):
        self.max_workers = max_workers
        
    async def process_batch(self, items):
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            loop = asyncio.get_event_loop()
            tasks = [loop.run_in_executor(executor, self.process_item, item) 
                    for item in items]
            return await asyncio.gather(*tasks)
"""
        result = self.validator._scalability_stress_test(scalable_code)
        assert result['passed'] is True
        assert result['score'] >= 0.7
        
    def test_comprehensive_validation_integration(self):
        """🔴 Red: 包括的検証統合テスト"""
        sample_code = """
def fibonacci(n: int) -> int:
    \"\"\"フィボナッチ数列の計算\"\"\"
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        result = self.validator.validate_comprehensive(sample_code)
        assert isinstance(result, ValidationResult)
        assert isinstance(result.score, float)
        assert isinstance(result.passed, bool)
        assert isinstance(result.issues, list)
        assert isinstance(result.suggestions, list)
        
    def test_quality_score_calculation(self):
        """🔴 Red: 品質スコア計算テスト"""
        code = "def test(): pass"
        score = self.validator.calculate_quality_score(code)
        assert isinstance(score, CodeQualityScore)
        assert 0.0 <= score.overall_score <= 100.0
        
    def test_empty_code_handling(self):
        """🔴 Red: 空コードハンドリング"""
        result = self.validator.validate_comprehensive("")
        assert result.passed is False
        assert any(issue['type'] == 'empty_code' for issue in result.issues)
        
    def test_large_code_handling(self):
        """🔴 Red: 大型コードハンドリング"""
        large_code = "def test():\n    pass\n" * 10000  # 大きなコード
        result = self.validator.validate_comprehensive(large_code)
        assert isinstance(result, ValidationResult)  # エラーにならないことを確認
        
    def test_unicode_code_handling(self):
        """🔴 Red: Unicode文字含有コードハンドリング"""
        unicode_code = """
def 挨拶():
    print("こんにちは世界！")
    # 日本語コメント含有
    return "成功"
"""
        result = self.validator.validate_comprehensive(unicode_code)
        assert isinstance(result, ValidationResult)
        
    def test_validation_performance(self):
        """🔴 Red: バリデーション性能テスト"""
        import time
        code = """
def complex_function():
    data = {}
    for i in range(100):
        data[f'key_{i}'] = [j for j in range(50)]
    return data
"""
        start_time = time.time()
        result = self.validator.validate_comprehensive(code)
        end_time = time.time()
        
        # バリデーションは5秒以内に完了すること
        assert (end_time - start_time) < 5.0
        assert isinstance(result, ValidationResult)
        
    def test_concurrent_validation(self):
        """🔴 Red: 並行バリデーションテスト"""
        import threading
        
        code = "def test(): return 42"
        results = []
        
        def validate_code():
            result = self.validator.validate_comprehensive(code)
            results.append(result)
            
        # 10個の並行バリデーション
        threads = [threading.Thread(target=validate_code) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
            
        assert len(results) == 10
        assert all(isinstance(r, ValidationResult) for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])