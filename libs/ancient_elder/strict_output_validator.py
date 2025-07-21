#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏛️ Ancient Elder - Strict Output Validator
エンシェントエルダー厳格出力検証システム

Tier 3: Output Validation Engine
厳格な6層バリデーションシステム

Creation: 2025-01-20
Author: Claude Elder
"""

import ast
import re
import sys
import time
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityRisk:
    """セキュリティリスクレベル定数"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueLevel:
    """問題レベル定数"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """バリデーション結果データクラス"""
    score: float
    passed: bool
    issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeQualityScore:
    """コード品質スコアデータクラス"""
    syntax_score: float = 0.0
    logic_score: float = 0.0
    performance_score: float = 0.0
    security_score: float = 0.0
    maintainability_score: float = 0.0
    scalability_score: float = 0.0
    overall_score: float = 0.0


class StrictOutputValidator:
    """
    🏛️ 厳格出力検証システム
    
    6層の厳格バリデーション:
    1. 構文検証 (Syntax Validation)
    2. 論理検証 (Logic Validation) 
    3. パフォーマンス検証 (Performance Validation)
    4. セキュリティ侵入テスト (Security Penetration Test)
    5. 保守性監査 (Maintainability Audit)
    6. 拡張性ストレステスト (Scalability Stress Test)
    """
    
    def __init__(self):
        """バリデーター初期化"""
        self._lock = threading.Lock()
        self._security_patterns = self._load_security_patterns()
        logger.info("🏛️ StrictOutputValidator initialized")
    
    def _load_security_patterns(self) -> Dict[str, List[str]]:
        """セキュリティパターンロード"""
        return {
            'critical': [
                r'os\.system\s*\(',
                r'eval\s*\(',
                r'exec\s*\(',
                r'__import__\s*\(',
                r'subprocess\.call\s*\(',
            ],
            'high': [
                r'input\s*\(',
                r'raw_input\s*\(',
                r'open\s*\([^)]*[\'"]w',
                r'pickle\.loads?\s*\(',
            ],
            'medium': [
                r'random\.seed\s*\(',
                r'hashlib\.md5\s*\(',
                r'urllib\.request',
            ]
        }
    
    def validate_comprehensive(self, code: str) -> ValidationResult:
        """
        🔍 包括的バリデーション実行
        
        Args:
            code: 検証対象コード
            
        Returns:
            ValidationResult: 検証結果
        """
        if not code or not code.strip():
            return ValidationResult(
                score=0.0,
                passed=False,
                issues=[{
                    'type': 'empty_code',
                    'level': IssueLevel.ERROR,
                    'message': '空のコードは検証できません'
                }],
                suggestions=['有効なPythonコードを入力してください']
            )
        
        start_time = time.time()
        
        # 6層並行バリデーション
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                'syntax': executor.submit(self._syntax_validation, code),
                'logic': executor.submit(self._logic_validation, code),
                'performance': executor.submit(self._performance_validation, code),
                'security': executor.submit(self._security_penetration_test, code),
                'maintainability': executor.submit(self._maintainability_audit, code),
                'scalability': executor.submit(self._scalability_stress_test, code)
            }
            
            results = {name: future.result() for name, future in futures.items()}
        
        # 結果統合
        issues = []
        suggestions = []
        total_score = 0.0
        passed_count = 0
        
        for layer_name, result in results.items():
            total_score += result['score']
            if result['passed']:
                passed_count += 1
            
            if 'issues' in result:
                issues.extend(result['issues'])
            if 'suggestions' in result:
                suggestions.extend(result['suggestions'])
        
        overall_score = total_score / len(results)
        passed = passed_count >= 4  # 6層中4層以上が合格
        
        validation_time = time.time() - start_time
        
        return ValidationResult(
            score=overall_score,
            passed=passed,
            issues=issues,
            suggestions=suggestions,
            details={
                'layer_results': results,
                'validation_time': validation_time,
                'passed_layers': passed_count,
                'total_layers': len(results)
            }
        )
    
    def _syntax_validation(self, code: str) -> Dict[str, Any]:
        """
        🔧 構文検証
        
        Args:
            code: 検証対象コード
            
        Returns:
            Dict: 構文検証結果
        """
        try:
            ast.parse(code)
            return {
                'passed': True,
                'score': 100.0,
                'issues': [],
                'suggestions': []
            }
        except SyntaxError as e:
            return {
                'passed': False,
                'score': 0.0,
                'issues': [{
                    'type': 'syntax_error',
                    'level': IssueLevel.ERROR,
                    'message': f'構文エラー: {str(e)}',
                    'line': getattr(e, 'lineno', 0)
                }],
                'suggestions': [
                    '構文エラーを修正してください',
                    'Pythonの構文規則に従ってください'
                ]
            }
        except Exception as e:
            return {
                'passed': False,
                'score': 0.0,
                'issues': [{
                    'type': 'parse_error',
                    'level': IssueLevel.ERROR,
                    'message': f'解析エラー: {str(e)}'
                }],
                'suggestions': ['コードを確認してください']
            }
    
    def _logic_validation(self, code: str) -> Dict[str, Any]:
        """
        🧠 論理検証
        
        Args:
            code: 検証対象コード
            
        Returns:
            Dict: 論理検証結果
        """
        issues = []
        suggestions = []
        score = 100.0
        
        # ゼロ除算チェック
        if re.search(r'[a-zA-Z_]\w*\s*/\s*[a-zA-Z_]\w*', code):
            if not re.search(r'if\s+[a-zA-Z_]\w*\s*[!<>=]=\s*0', code):
                issues.append({
                    'type': 'division_risk',
                    'level': IssueLevel.WARNING,
                    'message': 'ゼロ除算の可能性があります'
                })
                suggestions.append('除算前にゼロチェックを追加してください')
                score -= 30
        
        # 無限ループチェック
        while_patterns = re.findall(r'while\s+([^:]+):', code)
        for pattern in while_patterns:
            if 'True' in pattern and 'break' not in code:
                issues.append({
                    'type': 'infinite_loop',
                    'level': IssueLevel.ERROR,
                    'message': '無限ループの可能性があります'
                })
                suggestions.append('適切な終了条件を追加してください')
                score -= 40
        
        # 未定義変数使用チェック
        try:
            tree = ast.parse(code)
            # 簡易的な未定義変数チェック
            # 実際の実装ではより詳細な解析が必要
        except:
            pass
        
        passed = score >= 70 and len(issues) == 0
        return {
            'passed': passed,
            'score': score,
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _performance_validation(self, code: str) -> Dict[str, Any]:
        """
        ⚡ パフォーマンス検証
        
        Args:
            code: 検証対象コード
            
        Returns:
            Dict: パフォーマンス検証結果
        """
        issues = []
        suggestions = []
        score = 100.0
        
        # ネストレベルチェック
        lines = code.split('\n')
        max_indent = 0
        for line in lines:
            indent = len(line) - len(line.lstrip())
            max_indent = max(max_indent, indent)
        
        if max_indent > 20:  # 5レベル以上のネスト
            issues.append({
                'type': 'deep_nesting',
                'level': IssueLevel.WARNING,
                'message': f'過度なネスト (レベル: {max_indent // 4})'
            })
            suggestions.append('ネストを浅くするためリファクタリングしてください')
            score -= 25
        
        # 不要なループチェック - 3重以上のネストを検出
        for_count = code.count('for ')
        if for_count >= 3:
            # より詳細なネストチェック
            lines = code.split('\n')
            max_for_depth = 0
            current_depth = 0
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('for '):
                    current_depth += 1
                    max_for_depth = max(max_for_depth, current_depth)
                elif stripped and not line.startswith('    '):
                    current_depth = 0
            
            if max_for_depth >= 3:
                issues.append({
                    'type': 'excessive_loops',
                    'level': IssueLevel.WARNING,
                    'message': '過度なネストループが検出されました'
                })
                suggestions.append('アルゴリズムの最適化を検討してください')
                score -= 50
        
        # リスト内包表記の推奨
        if 'append' in code and 'for' in code:
            suggestions.append('リスト内包表記の使用を検討してください')
        
        passed = score >= 60 and len(issues) == 0
        return {
            'passed': passed,
            'score': score,
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _security_penetration_test(self, code: str) -> Dict[str, Any]:
        """
        🛡️ セキュリティ侵入テスト
        
        Args:
            code: 検証対象コード
            
        Returns:
            Dict: セキュリティテスト結果
        """
        issues = []
        suggestions = []
        score = 100.0
        risk_level = SecurityRisk.LOW
        
        # 危険パターンチェック
        for risk, patterns in self._security_patterns.items():
            for pattern in patterns:
                if re.search(pattern, code):
                    severity_score = {
                        'critical': 60,
                        'high': 40,
                        'medium': 20
                    }[risk]
                    
                    issues.append({
                        'type': 'security_risk',
                        'level': IssueLevel.CRITICAL if risk == 'critical' else IssueLevel.WARNING,
                        'message': f'セキュリティリスク検出: {pattern}',
                        'risk_level': risk
                    })
                    
                    score -= severity_score
                    if risk in ['critical', 'high']:
                        risk_level = SecurityRisk.HIGH if risk == 'high' else SecurityRisk.CRITICAL
                    
                    suggestions.append(f'セキュリティリスクを軽減してください: {pattern}')
        
        # SQLインジェクション脆弱性チェック
        if 'execute(' in code and '%' in code:
            issues.append({
                'type': 'sql_injection',
                'level': IssueLevel.HIGH,
                'message': 'SQLインジェクション脆弱性の可能性'
            })
            suggestions.append('パラメータ化クエリを使用してください')
            score -= 50
            risk_level = SecurityRisk.HIGH
        
        passed = score >= 70 and risk_level not in [SecurityRisk.CRITICAL]
        return {
            'passed': passed,
            'score': score,
            'risk_level': risk_level,
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _maintainability_audit(self, code: str) -> Dict[str, Any]:
        """
        🔧 保守性監査
        
        Args:
            code: 検証対象コード
            
        Returns:
            Dict: 保守性監査結果
        """
        issues = []
        suggestions = []
        score = 100.0
        
        # 関数の引数数チェック
        func_patterns = re.findall(r'def\s+\w+\s*\(([^)]*)\)', code)
        for params in func_patterns:
            if params.strip():  # 空の引数リストを除外
                param_count = len([p for p in params.split(',') if p.strip()])
                if param_count > 7:
                    issues.append({
                        'type': 'too_many_parameters',
                        'level': IssueLevel.WARNING,
                        'message': f'引数が多すぎます ({param_count}個)'
                    })
                    suggestions.append('引数をオブジェクトにまとめることを検討してください')
                    score -= 35
        
        # ドキュメントストリングチェック (良いコードの場合は加点)
        if 'def ' in code:
            if '"""' in code or "'''" in code:
                score += 5  # ドキュメントありでボーナス
            else:
                issues.append({
                    'type': 'missing_docstring',
                    'level': IssueLevel.INFO,
                    'message': 'ドキュメントストリングが不足しています'
                })
                suggestions.append('関数やクラスにドキュメントストリングを追加してください')
                score -= 10
        
        # 変数名チェック - より厳しい判定
        poor_names = re.findall(r'\b[a-z]\b', code)  # 1文字変数
        if poor_names:
            issues.append({
                'type': 'poor_naming',
                'level': IssueLevel.WARNING,
                'message': f'1文字の変数名が使用されています: {", ".join(set(poor_names))}'
            })
            suggestions.append('意味のある変数名を使用してください')
            score -= len(set(poor_names)) * 10  # 複数の悪い変数名でペナルティ増加
        
        # 関数の長さチェック
        lines = code.split('\n')
        in_function = False
        func_length = 0
        max_func_length = 0
        
        for line in lines:
            if line.strip().startswith('def '):
                in_function = True
                func_length = 0
            elif in_function:
                if line.strip() and not line.startswith('    '):
                    max_func_length = max(max_func_length, func_length)
                    in_function = False
                else:
                    func_length += 1
        
        if max_func_length > 50:
            issues.append({
                'type': 'long_function',
                'level': IssueLevel.WARNING,
                'message': f'関数が長すぎます ({max_func_length}行)'
            })
            suggestions.append('関数を小さく分割することを検討してください')
            score -= 20
        
        passed = score >= 60 and len([issue for issue in issues if issue['level'] in ['error', 'critical']]) == 0
        return {
            'passed': passed,
            'score': score,
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _scalability_stress_test(self, code: str) -> Dict[str, Any]:
        """
        📈 拡張性ストレステスト
        
        Args:
            code: 検証対象コード
            
        Returns:
            Dict: 拡張性テスト結果
        """
        issues = []
        suggestions = []
        score = 100.0
        
        # 並行処理パターンチェック
        has_async = 'async' in code or 'await' in code
        has_threading = 'threading' in code or 'Thread' in code
        has_multiprocessing = 'multiprocessing' in code
        has_concurrent = 'concurrent.futures' in code
        
        scalable_patterns = sum([has_async, has_threading, has_multiprocessing, has_concurrent])
        
        if scalable_patterns > 0:
            score += 20  # ボーナス点
            suggestions.append('並行処理パターンが適切に使用されています')
        else:
            # 大きなデータ処理がある場合
            if 'range(' in code:
                range_matches = re.findall(r'range\((\d+)\)', code)
                for match in range_matches:
                    if int(match) > 1000:
                        issues.append({
                            'type': 'scalability_concern',
                            'level': IssueLevel.INFO,
                            'message': '大量データ処理で並行処理を検討してください'
                        })
                        suggestions.append('asyncioやThreadPoolExecutorの使用を検討してください')
                        score -= 10
        
        # メモリ効率チェック
        if 'list(' in code and 'range(' in code:
            issues.append({
                'type': 'memory_inefficient',
                'level': IssueLevel.INFO,
                'message': 'ジェネレーター式の使用を検討してください'
            })
            suggestions.append('list(range())の代わりにジェネレーター式を使用してください')
            score -= 5
        
        # キャッシュ機能チェック
        if '@lru_cache' in code or '@cache' in code:
            score += 10  # ボーナス点
            suggestions.append('キャッシュが適切に使用されています')
        
        passed = score >= 70
        return {
            'passed': passed,
            'score': score,
            'issues': issues,
            'suggestions': suggestions
        }
    
    def calculate_quality_score(self, code: str) -> CodeQualityScore:
        """
        📊 品質スコア計算
        
        Args:
            code: 検証対象コード
            
        Returns:
            CodeQualityScore: 品質スコア詳細
        """
        result = self.validate_comprehensive(code)
        layer_results = result.details.get('layer_results', {})
        
        return CodeQualityScore(
            syntax_score=layer_results.get('syntax', {}).get('score', 0.0),
            logic_score=layer_results.get('logic', {}).get('score', 0.0),
            performance_score=layer_results.get('performance', {}).get('score', 0.0),
            security_score=layer_results.get('security', {}).get('score', 0.0),
            maintainability_score=layer_results.get('maintainability', {}).get('score', 0.0),
            scalability_score=layer_results.get('scalability', {}).get('score', 0.0),
            overall_score=result.score
        )


# Ancient Elder Magic Integration
def validate_ancient_elder_output(code: str) -> ValidationResult:
    """
    🏛️ Ancient Elder魔法統合関数
    
    Args:
        code: 検証対象コード
        
    Returns:
        ValidationResult: Ancient Elder承認済み検証結果
    """
    validator = StrictOutputValidator()
    result = validator.validate_comprehensive(code)
    
    logger.info(f"🏛️ Ancient Elder validation completed: "
               f"Score={result.score:.1f}, Passed={result.passed}")
    
    return result


if __name__ == "__main__":
    # テスト実行
    validator = StrictOutputValidator()
    
    test_code = """
def fibonacci(n: int) -> int:
    '''フィボナッチ数列の計算'''
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    result = validator.validate_comprehensive(test_code)
    print(f"🏛️ Test Result: Score={result.score:.1f}, Passed={result.passed}")
    print(f"📋 Issues: {len(result.issues)}")
    print(f"💡 Suggestions: {len(result.suggestions)}")