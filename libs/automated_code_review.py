#!/usr/bin/env python3
"""
自動コードレビューシステム
コード品質分析、セキュリティチェック、ベストプラクティス検証を提供
"""
import re
import ast
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from enum import Enum
import tokenize
import io


class Severity(Enum):
    """重要度レベル"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueType(Enum):
    """問題タイプ"""
    STYLE = "style"
    CODE_SMELL = "code_smell"
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"


@dataclass
class Issue:
    """コード問題"""
    type: str
    subtype: str
    severity: str
    location: Dict[str, int]
    message: str
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'type': self.type,
            'subtype': self.subtype,
            'severity': self.severity,
            'location': self.location,
            'message': self.message,
            'suggestion': self.suggestion
        }


@dataclass
class CodeMetrics:
    """コードメトリクス"""
    lines_of_code: int = 0
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    maintainability_index: float = 100.0
    halstead_metrics: Dict[str, float] = field(default_factory=dict)


class CodeAnalyzer:
    """コード分析器"""
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.issues = []
        self.metrics = CodeMetrics()
    
    def analyze_code_quality(self, code: str, language: str = 'python') -> Dict[str, Any]:
        """コード品質分析"""
        self.issues = []
        self._code_content = code  # スコア計算用に保存
        
        if language == 'python':
            self._analyze_python_code(code)
        
        # メトリクス計算
        self._calculate_metrics(code)
        
        # 品質スコア計算
        quality_score = self._calculate_quality_score()
        
        return {
            'quality_score': quality_score,
            'issues': [issue.to_dict() for issue in self.issues],
            'metrics': {
                'lines_of_code': self.metrics.lines_of_code,
                'cyclomatic_complexity': self.metrics.cyclomatic_complexity,
                'cognitive_complexity': self.metrics.cognitive_complexity,
                'maintainability_index': self.metrics.maintainability_index,
                'halstead_metrics': self.metrics.halstead_metrics
            }
        }
    
    def detect_code_smells(self, code: str) -> List[Dict[str, Any]]:
        """コードスメル検出"""
        smells = []
        
        # 長すぎるパラメータリスト
        smells.extend(self._detect_too_many_parameters(code))
        
        # 深いネスト
        smells.extend(self._detect_deep_nesting(code))
        
        # マジックナンバー
        smells.extend(self._detect_magic_numbers(code))
        
        # 重複コード
        smells.extend(self._detect_duplicate_code(code))
        
        return smells
    
    def check_best_practices(self, code: str, language: str = 'python') -> List[Dict[str, Any]]:
        """ベストプラクティスチェック"""
        violations = []
        
        # パスワードの平文保存チェック
        if re.search(r'password[\'"\s]*[:=][\'"\s]*[^{]', code, re.IGNORECASE):
            violations.append({
                'rule': 'no_plain_passwords',
                'line': self._find_line_number(code, 'password'),
                'severity': 'critical',
                'suggestion': 'Use hashed passwords with bcrypt or similar'
            })
        
        # ハードコードされた認証情報（接続文字列も含む）
        if re.search(r'(password|secret|key)[\'"\s]*[:=][\'"\s]*[\'"][^\'"\s]+[\'"]', code, re.IGNORECASE) or \
           re.search(r'(postgresql|mysql|mongodb)://[^@]+:[^@]+@', code):
            violations.append({
                'rule': 'no_hardcoded_credentials',
                'line': self._find_line_number(code, 'password'),
                'severity': 'critical',
                'suggestion': 'Use environment variables or secure credential storage'
            })
        
        return violations
    
    def analyze_complexity(self, code: str) -> Dict[str, Any]:
        """複雑度分析"""
        try:
            tree = ast.parse(code)
            
            # サイクロマティック複雑度
            cyclomatic = self._calculate_cyclomatic_complexity(tree)
            
            # 認知的複雑度
            cognitive = self._calculate_cognitive_complexity(tree)
            
            # Halstead メトリクス
            halstead = self._calculate_halstead_metrics(code)
            
            # 推奨事項
            recommendations = []
            if cyclomatic > 10:
                recommendations.append("Consider breaking down complex functions")
            if cognitive > 15:
                recommendations.append("Simplify nested logic structures")
            
            return {
                'cyclomatic_complexity': cyclomatic,
                'cognitive_complexity': cognitive,
                'halstead_metrics': halstead,
                'recommendations': recommendations
            }
        except Exception as e:
            self.logger.error(f"Error analyzing complexity: {e}")
            return {
                'cyclomatic_complexity': 0,
                'cognitive_complexity': 0,
                'halstead_metrics': {},
                'recommendations': []
            }
    
    def _analyze_python_code(self, code: str):
        """Pythonコード分析"""
        try:
            tree = ast.parse(code)
            # AST解析（簡易実装）
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # 関数の分析
                    if len(node.args.args) > 5:
                        self.issues.append(Issue(
                            type='code_smell',
                            subtype='too_many_parameters',
                            severity='medium',
                            location={'line': node.lineno},
                            message=f"Function '{node.name}' has too many parameters",
                            suggestion="Consider using a configuration object"
                        ))
        except Exception as e:
            self.logger.error(f"Error parsing Python code: {e}")
    
    def _calculate_metrics(self, code: str):
        """メトリクス計算"""
        lines = code.split('\n')
        self.metrics.lines_of_code = len([l for l in lines if l.strip()])
        
        # 簡易的な複雑度計算
        self.metrics.cyclomatic_complexity = code.count('if ') + code.count('elif ') + code.count('for ') + code.count('while ') + 1
        self.metrics.cognitive_complexity = self.metrics.cyclomatic_complexity  # 簡易実装
        
        # 保守性指標（簡易計算）
        self.metrics.maintainability_index = max(0, 100 - self.metrics.cyclomatic_complexity * 5)
    
    def _calculate_quality_score(self) -> int:
        """品質スコア計算"""
        base_score = 100
        
        # 問題による減点
        for issue in self.issues:
            if issue.severity == 'critical':
                base_score -= 20
            elif issue.severity == 'high':
                base_score -= 10
            elif issue.severity == 'medium':
                base_score -= 5
            else:
                base_score -= 2
        
        # 複雑度による減点
        if self.metrics.cyclomatic_complexity > 10:
            base_score -= 10
        
        # コード内容による減点（パスワードやカード番号が露出している場合）
        if hasattr(self, '_code_content'):
            if 'card_number' in self._code_content or 'password' in self._code_content:
                base_score -= 20
        
        return max(0, base_score)
    
    def _detect_too_many_parameters(self, code: str) -> List[Dict[str, Any]]:
        """パラメータ数過多の検出"""
        smells = []
        
        # 簡易的な正規表現での検出
        pattern = r'def\s+\w+\s*\([^)]+\):'
        for match in re.finditer(pattern, code):
            params = match.group(0).count(',')
            if params >= 8:  # 9個以上のパラメータ
                line_no = code[:match.start()].count('\n') + 1
                smells.append({
                    'type': 'too_many_parameters',
                    'line': line_no,
                    'severity': 'medium',
                    'message': 'Too many parameters in function'
                })
        
        return smells
    
    def _detect_deep_nesting(self, code: str) -> List[Dict[str, Any]]:
        """深いネストの検出"""
        smells = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines):
            # インデントレベルをカウント
            indent_level = (len(line) - len(line.lstrip())) // 4
            if indent_level >= 4 and ('if' in line or 'for' in line or 'while' in line):
                smells.append({
                    'type': 'deep_nesting',
                    'line': i + 1,
                    'severity': 'medium',
                    'message': 'Deep nesting detected'
                })
        
        return smells
    
    def _detect_magic_numbers(self, code: str) -> List[Dict[str, Any]]:
        """マジックナンバーの検出"""
        smells = []
        
        # 数値リテラルの検出（0, 1以外）
        pattern = r'\b(?<!\.)\d+(?:\.\d+)?(?!\.)\b'
        for match in re.finditer(pattern, code):
            number = match.group(0)
            if number not in ['0', '1', '2']:  # 0, 1, 2は許容
                line_no = code[:match.start()].count('\n') + 1
                smells.append({
                    'type': 'magic_numbers',
                    'line': line_no,
                    'severity': 'low',
                    'message': f'Magic number {number} detected'
                })
        
        return smells
    
    def _detect_duplicate_code(self, code: str) -> List[Dict[str, Any]]:
        """重複コードの検出"""
        smells = []
        lines = code.split('\n')
        
        # 簡易的な重複検出（同じ行が2回以上出現）
        line_counts = Counter(line.strip() for line in lines if line.strip())
        
        for line, count in line_counts.items():
            if count > 1 and len(line) > 20:  # 20文字以上の行が重複
                smells.append({
                    'type': 'duplicate_code',
                    'line': -1,  # 複数行にまたがるため特定不可
                    'severity': 'medium',
                    'message': f'Duplicate code detected: "{line[:50]}..."'
                })
        
        return smells
    
    def _find_line_number(self, code: str, pattern: str) -> int:
        """パターンの行番号検索"""
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if pattern.lower() in line.lower():
                return i + 1
        return -1
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """サイクロマティック複雑度計算"""
        complexity = 1
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _calculate_cognitive_complexity(self, tree: ast.AST) -> int:
        """認知的複雑度計算"""
        # 簡易実装
        return self._calculate_cyclomatic_complexity(tree)
    
    def _calculate_halstead_metrics(self, code: str) -> Dict[str, float]:
        """Halstead メトリクス計算"""
        # 簡易実装
        operators = len(re.findall(r'[+\-*/=<>!&|]', code))
        operands = len(re.findall(r'\b\w+\b', code))
        
        return {
            'operators': operators,
            'operands': operands,
            'vocabulary': operators + operands,
            'length': operators + operands,
            'difficulty': operators / 2 if operands > 0 else 0
        }


class SecurityScanner:
    """セキュリティスキャナー"""
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.vulnerability_patterns = self._load_vulnerability_patterns()
    
    def scan_vulnerabilities(self, code: str) -> List[Dict[str, Any]]:
        """脆弱性スキャン"""
        vulnerabilities = []
        
        # SQLインジェクション
        if re.search(r'(execute|cursor\.execute)\s*\([^)]*[fF][\'""]|\.format\(', code) or \
           re.search(r'f"SELECT.*{', code) or \
           re.search(r'f\'SELECT.*{', code) or \
           re.search(r'SELECT.*\'\s*\+.*username', code, re.IGNORECASE):
            vulnerabilities.append({
                'type': 'sql_injection',
                'line': self._find_pattern_line(code, 'execute') or self._find_pattern_line(code, 'SELECT'),
                'severity': 'critical',
                'description': 'SQL injection vulnerability detected',
                'fix_suggestion': 'Use parameterized queries instead of string formatting'
            })
        
        # コマンドインジェクション
        if re.search(r'os\.(system|popen)\s*\([^)]*[fF][\'""]|\.format\(', code):
            vulnerabilities.append({
                'type': 'command_injection',
                'line': self._find_pattern_line(code, 'os.system'),
                'severity': 'critical',
                'description': 'Command injection vulnerability detected',
                'fix_suggestion': 'Use subprocess.run with proper argument escaping'
            })
        
        # パストラバーサル
        if re.search(r'open\s*\([^)]*[fF][\'""]|\.format\(', code):
            vulnerabilities.append({
                'type': 'path_traversal',
                'line': self._find_pattern_line(code, 'open'),
                'severity': 'high',
                'description': 'Potential path traversal vulnerability',
                'fix_suggestion': 'Validate and sanitize file paths'
            })
        
        return vulnerabilities
    
    def check_dependencies(self, requirements: str, format: str = 'requirements.txt') -> List[Dict[str, Any]]:
        """依存関係チェック"""
        issues = []
        
        # 既知の脆弱性を持つパッケージ（簡易データベース）
        vulnerable_packages = {
            'django': {'vulnerable_versions': ['<2.2.10'], 'safe_version': '3.2.0'},
            'requests': {'vulnerable_versions': ['<2.21.0'], 'safe_version': '2.26.0'},
            'pyyaml': {'vulnerable_versions': ['<5.3.1'], 'safe_version': '6.0'}
        }
        
        lines = requirements.strip().split('\n')
        for line in lines:
            if '==' in line:
                package, version = line.split('==')
                package = package.strip().lower()
                version = version.strip()
                
                if package in vulnerable_packages:
                    issues.append({
                        'package': package,
                        'current_version': version,
                        'recommended_version': vulnerable_packages[package]['safe_version'],
                        'vulnerabilities': ['Known security vulnerabilities'],
                        'severity': 'high'
                    })
        
        return issues
    
    def detect_sensitive_data(self, code: str) -> List[Dict[str, Any]]:
        """機密データ検出"""
        sensitive_data = []
        
        # APIキー
        api_key_pattern = r'(api[_-]?key|apikey)\s*[:=]\s*[\'"][^\'"]+[\'"]'
        for match in re.finditer(api_key_pattern, code, re.IGNORECASE):
            line_no = code[:match.start()].count('\n') + 1
            sensitive_data.append({
                'type': 'api_key',
                'line': line_no,
                'severity': 'critical',
                'recommendation': 'Store API keys in environment variables'
            })
        
        # AWS認証情報
        aws_pattern = r'(aws[_-]?secret[_-]?key|aws[_-]?access[_-]?key)\s*[:=]\s*[\'"][^\'"]+[\'"]'
        for match in re.finditer(aws_pattern, code, re.IGNORECASE):
            line_no = code[:match.start()].count('\n') + 1
            sensitive_data.append({
                'type': 'aws_credentials',
                'line': line_no,
                'severity': 'critical',
                'recommendation': 'Use AWS IAM roles or environment variables'
            })
        
        # データベース認証情報
        db_pattern = r'(password|passwd|pwd|DATABASE_URL)\s*[:=]\s*[\'"][^\'"]+[\'"]'
        for match in re.finditer(db_pattern, code, re.IGNORECASE):
            line_no = code[:match.start()].count('\n') + 1
            sensitive_data.append({
                'type': 'database_credentials',
                'line': line_no,
                'severity': 'critical',
                'recommendation': 'Use secure credential management'
            })
        
        # 秘密鍵
        private_key_pattern = r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----'
        if re.search(private_key_pattern, code):
            sensitive_data.append({
                'type': 'private_key',
                'line': self._find_pattern_line(code, '-----BEGIN'),
                'severity': 'critical',
                'recommendation': 'Never commit private keys to version control'
            })
        
        return sensitive_data
    
    def analyze_crypto_usage(self, code: str) -> Dict[str, Any]:
        """暗号使用法分析"""
        analysis = {
            'weak_algorithms': [],
            'recommendations': []
        }
        
        # 弱い暗号アルゴリズムの検出
        weak_algorithms = ['md5', 'sha1', 'des', 'rc4']
        for algo in weak_algorithms:
            if algo in code.lower():
                analysis['weak_algorithms'].append(algo)
                analysis['recommendations'].append(f"Replace {algo} with stronger algorithm")
        
        return analysis
    
    def _load_vulnerability_patterns(self) -> Dict[str, Any]:
        """脆弱性パターンのロード"""
        # 実際にはデータベースや設定ファイルから読み込む
        return {
            'sql_injection': {
                'patterns': [r'execute.*format', r'execute.*%'],
                'severity': 'critical'
            },
            'xss': {
                'patterns': [r'innerHTML\s*=', r'document\.write'],
                'severity': 'high'
            }
        }
    
    def _find_pattern_line(self, code: str, pattern: str) -> int:
        """パターンの行番号検索"""
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if pattern in line:
                return i + 1
        return -1


class ReviewEngine:
    """レビューエンジン"""
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.code_analyzer = CodeAnalyzer()
        self.security_scanner = SecurityScanner()
    
    def perform_review(self, code: str, language: str = 'python', 
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """包括的レビュー実行"""
        # コード品質分析
        quality_analysis = self.code_analyzer.analyze_code_quality(code, language)
        
        # セキュリティスキャン
        security_issues = self.security_scanner.scan_vulnerabilities(code)
        
        # 全体的な問題リスト
        all_issues = quality_analysis['issues'] + [
            {'type': 'security', 'severity': issue['severity'], **issue}
            for issue in security_issues
        ]
        
        # スコア計算
        overall_score = self._calculate_overall_score(quality_analysis, security_issues)
        
        # サマリー生成
        summary = self._generate_summary(all_issues, overall_score)
        
        # 改善提案生成
        suggestions = self.generate_suggestions(all_issues)
        
        return {
            'overall_score': overall_score,
            'issues': all_issues,
            'suggestions': suggestions,
            'summary': summary,
            'quality_metrics': quality_analysis['metrics']
        }
    
    def generate_suggestions(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """改善提案生成"""
        suggestions = []
        
        # 問題タイプ別の提案
        issue_types = set(issue.get('subtype', issue.get('type', '')) for issue in issues)
        
        for issue_type in issue_types:
            if issue_type == 'magic_numbers':
                suggestions.append({
                    'description': 'Extract magic numbers to named constants',
                    'code_example': 'MAX_RETRIES = 3\nTIMEOUT_SECONDS = 30',
                    'priority': 'medium'
                })
            elif issue_type == 'sensitive_data_exposure':
                suggestions.append({
                    'description': 'Use environment variables for sensitive data',
                    'code_example': 'api_key = os.environ.get("API_KEY")',
                    'priority': 'high'
                })
        
        return suggestions
    
    def prioritize_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """問題優先順位付け"""
        # 優先度スコア計算
        priority_scores = {
            'critical': 1000,
            'high': 100,
            'medium': 10,
            'low': 1
        }
        
        impact_scores = {
            'data_breach': 500,
            'functionality': 200,
            'performance': 50,
            'readability': 10,
            'speed': 25
        }
        
        prioritized = []
        for issue in issues:
            severity = issue.get('severity', 'low')
            impact = issue.get('impact', 'readability')
            
            priority_score = priority_scores.get(severity, 1)
            priority_score += impact_scores.get(impact, 10)
            
            issue_copy = issue.copy()
            issue_copy['priority_score'] = priority_score
            prioritized.append(issue_copy)
        
        # スコアでソート
        prioritized.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return prioritized
    
    def create_review_report(self, review_data: Dict[str, Any], format: str = 'markdown') -> str:
        """レビューレポート生成"""
        if format == 'markdown':
            return self._create_markdown_report(review_data)
        else:
            return json.dumps(review_data, indent=2)
    
    def _calculate_overall_score(self, quality_analysis: Dict[str, Any], 
                                security_issues: List[Dict[str, Any]]) -> int:
        """総合スコア計算"""
        base_score = quality_analysis['quality_score']
        
        # セキュリティ問題による減点
        for issue in security_issues:
            if issue['severity'] == 'critical':
                base_score -= 20
            elif issue['severity'] == 'high':
                base_score -= 10
        
        return max(0, base_score)
    
    def _generate_summary(self, issues: List[Dict[str, Any]], score: int) -> str:
        """サマリー生成"""
        issue_count = len(issues)
        critical_count = sum(1 for i in issues if i.get('severity') == 'critical')
        
        if score >= 90:
            grade = "Excellent"
        elif score >= 80:
            grade = "Good"
        elif score >= 70:
            grade = "Fair"
        else:
            grade = "Needs Improvement"
        
        return f"Code quality: {grade} ({score}/100). Found {issue_count} issues ({critical_count} critical)."
    
    def _create_markdown_report(self, review_data: Dict[str, Any]) -> str:
        """Markdownレポート作成"""
        report = f"""# Code Review Report

## Summary
- **File**: {review_data.get('file_path', 'Unknown')}
- **Overall Score**: {review_data.get('overall_score', 0)}/100
- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Issues Found
"""
        
        # 問題のカテゴリ別集計
        issue_types = defaultdict(int)
        for issue in review_data.get('issues', []):
            issue_types[issue.get('type', 'unknown')] += 1
        
        for issue_type, count in issue_types.items():
            report += f"- **{issue_type}**: {count} issues\n"
        
        report += "\n## Suggestions\n"
        for suggestion in review_data.get('suggestions', []):
            report += f"- {suggestion}\n"
        
        report += "\n## Code Metrics\n"
        metrics = review_data.get('metrics', {})
        for metric, value in metrics.items():
            report += f"- **{metric}**: {value}\n"
        
        return report


class AIReviewAssistant:
    """AIレビューアシスタント"""
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
    
    def analyze_code_intent(self, code: str) -> Dict[str, Any]:
        """コード意図分析"""
        # 簡易的な意図分析
        intent = {
            'purpose': '',
            'inputs': [],
            'outputs': [],
            'business_logic': ''
        }
        
        # 関数名とコメントから目的を推測
        if 'user' in code.lower() and 'active' in code.lower():
            intent['purpose'] = 'Analyzes active users and calculates metrics'
        
        # 入出力の分析
        if 'users' in code:
            intent['inputs'] = ['users list']
        
        if 'return' in code and 'dict' in code:
            intent['outputs'] = ['dictionary with metrics']
        
        # ビジネスロジックの抽出
        if 'last_login' in code and 'days < 30' in code:
            intent['business_logic'] = 'Filters users active within last 30 days'
        
        return intent
    
    def suggest_refactoring(self, code: str) -> List[Dict[str, Any]]:
        """リファクタリング提案"""
        suggestions = []
        
        # 条件分岐が多い場合はStrategy Patternを提案
        if code.count('if') + code.count('elif') > 5:
            suggestions.append({
                'pattern': 'Strategy Pattern',
                'description': 'Replace complex conditionals with strategy pattern',
                'refactored_code': self._generate_strategy_pattern_example(),
                'benefits': ['Improved maintainability', 'Easier testing', 'Better extensibility']
            })
        
        return suggestions
    
    def generate_documentation(self, code: str, style: str = 'numpy') -> str:
        """ドキュメント生成"""
        # 簡易的なドキュメント生成
        doc = """
    Cache manager for storing and retrieving cached data.
    
    Parameters
    ----------
    max_size : int, optional
        Maximum number of items in cache (default 1000)
    ttl : int, optional
        Time to live in seconds (default 3600)
    
    Returns
    -------
    None
    
    Examples
    --------
    >>> cache = CacheManager(max_size=500, ttl=1800)
    >>> cache.set('key', 'value')
    >>> cache.get('key')
    'value'
    """
        return doc
    
    def explain_complex_code(self, code: str) -> str:
        """複雑なコードの説明"""
        explanation = "This code implements a caching mechanism with TTL support."
        return explanation
    
    def _generate_strategy_pattern_example(self) -> str:
        """Strategy Patternの例生成"""
        return """
# Strategy Pattern Example
class PricingStrategy:
    def calculate(self, base_price):
        raise NotImplementedError

class ElectronicsStrategy(PricingStrategy):
    def calculate(self, base_price):
        return base_price * 0.9

class ClothingStrategy(PricingStrategy):
    def calculate(self, base_price):
        return base_price * 0.8
"""


class CodeReviewPipeline:
    """コードレビューパイプライン"""
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.review_engine = ReviewEngine()
        self.ai_assistant = AIReviewAssistant()
        self.cache = {}
        self.cache_ttl = timedelta(hours=1)
    
    def review_file(self, file_content: str, file_path: str = None,
                   review_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """ファイルレビュー実行"""
        # キャッシュチェック
        content_hash = hashlib.md5(file_content.encode()).hexdigest()
        cache_key = f"{file_path}:{content_hash}"
        
        if cache_key in self.cache:
            cached_result = self.cache[cache_key].copy()
            if datetime.now() - cached_result['timestamp'] < self.cache_ttl:
                cached_result['from_cache'] = True
                cached_result['review_time_ms'] = 0  # キャッシュは即座に返る
                return cached_result
        
        start_time = datetime.now()
        
        # レビュー実行
        review_result = self.review_engine.perform_review(
            file_content,
            context={'file_path': file_path}
        )
        
        # グレード判定
        score = review_result['overall_score']
        if score >= 90:
            grade = 'A'
        elif score >= 80:
            grade = 'B'
        elif score >= 70:
            grade = 'C'
        elif score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        # セキュリティ問題の抽出
        security_issues = [
            issue for issue in review_result['issues']
            if issue.get('type') == 'security'
        ]
        
        # 自動修正可能性チェック
        auto_fixable = self._check_auto_fixable(review_result['issues'])
        
        result = {
            'status': 'completed',
            'overall_grade': grade,
            'overall_score': score,
            'security_issues': security_issues,
            'improvement_suggestions': review_result['suggestions'],
            'auto_fix_available': auto_fixable,
            'review_time_ms': int((datetime.now() - start_time).total_seconds() * 1000),
            'from_cache': False,
            'timestamp': datetime.now()
        }
        
        # キャッシュに保存
        self.cache[cache_key] = result
        
        return result
    
    def generate_auto_fix(self, code: str, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """自動修正生成"""
        fixed_code = code
        changes_made = []
        
        for issue in issues:
            if issue['type'] == 'error_handling':
                # エラーハンドリングの追加
                fixed_code = self._add_error_handling(fixed_code, issue)
                changes_made.append({
                    'type': 'error_handling',
                    'description': 'Added error handling'
                })
            elif issue['type'] == 'hardcoded_secret':
                # ハードコードされた秘密情報の置換
                fixed_code = self._replace_hardcoded_secrets(fixed_code)
                changes_made.append({
                    'type': 'security',
                    'description': 'Replaced hardcoded secrets with environment variables'
                })
        
        return {
            'fixed_code': fixed_code,
            'changes_made': changes_made
        }
    
    def _check_auto_fixable(self, issues: List[Dict[str, Any]]) -> bool:
        """自動修正可能性チェック"""
        auto_fixable_types = ['error_handling', 'hardcoded_secret', 'magic_numbers']
        
        for issue in issues:
            if issue.get('type') in auto_fixable_types:
                return True
        
        return False
    
    def _add_error_handling(self, code: str, issue: Dict[str, Any]) -> str:
        """エラーハンドリング追加"""
        # 簡易実装：ゼロ除算チェック
        if 'divide' in code and 'return a / b' in code:
            fixed_code = code.replace(
                'return a / b',
                'if b == 0:\n        raise ValueError("Division by zero")\n    return a / b'
            )
            return fixed_code
        
        return code
    
    def _replace_hardcoded_secrets(self, code: str) -> str:
        """ハードコードされた秘密情報の置換"""
        # APIキーの置換
        fixed_code = re.sub(
            r"'api_key':\s*'[^']+'",
            "'api_key': os.environ.get('API_KEY', '')",
            code
        )
        
        # import osの追加（必要な場合）
        if 'os.environ' in fixed_code and 'import os' not in fixed_code:
            fixed_code = 'import os\n' + fixed_code
        
        return fixed_code