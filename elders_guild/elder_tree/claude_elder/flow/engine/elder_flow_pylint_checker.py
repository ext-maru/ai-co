#!/usr/bin/env python3
"""
🏛️ Elder Flow Pylint Checker
エルダーフロー専用Pylintチェッカー

Features:
- Pylint統合チェック
- カスタムルール適用
- エルダーズギルド標準準拠
- 詳細レポート生成
"""

import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PylintIssue:
    """Pylint問題詳細"""
    type: str  # error, warning, convention, refactor, info
    module: str
    obj: str
    line: int
    column: int
    message_id: str
    symbol: str
    message: str
    confidence: Optional[str] = None
    
    @property
    def severity(self) -> str:
        """エルダーズギルド重要度マッピング"""
        severity_map = {
            'error': 'critical',
            'fatal': 'critical', 
            'warning': 'high',
            'convention': 'medium',
            'refactor': 'low',
            'info': 'low'
        }
        return severity_map.get(self.type.lower(), 'medium')
        
    @property
    def elder_guild_category(self) -> str:
        """エルダーズギルドカテゴリ分類"""
        # メッセージIDによる分類
        if self.message_id.startswith('E'):  # Error
            return 'syntax_error'
        elif self.message_id.startswith('W'):  # Warning
            if 'unused' in self.symbol:
                return 'unused_code'
            elif 'import' in self.symbol:
                return 'import_issue'

        elif self.message_id.startswith('C'):  # Convention
            return 'style_issue'
        elif self.message_id.startswith('R'):  # Refactor
            return 'complexity_issue'
        return 'quality_issue'

@dataclass
class PylintResult:
    """Pylint実行結果"""
    issues: List[PylintIssue] = field(default_factory=list)
    score: float = 0.0
    previous_score: Optional[float] = None
    total_statements: int = 0
    analyzed_files: int = 0
    
    @property
    def total_issues(self) -> int:
        return len(self.issues)
        
    @property
    def issues_by_severity(self) -> Dict[str, int]:
        """重要度別問題数"""
        severity_count = {}
        for issue in self.issues:
            severity = issue.severity
            severity_count[severity] = severity_count.get(severity, 0) + 1
        return severity_count
        
    @property
    def issues_by_category(self) -> Dict[str, int]:
        """カテゴリ別問題数"""
        category_count = {}
        for issue in self.issues:
            category = issue.elder_guild_category
            category_count[category] = category_count.get(category, 0) + 1
        return category_count

class ElderFlowPylintChecker:
    """Elder Flow専用Pylintチェッカー"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初期化
        
        Args:
            config_path: カスタムpylintrc設定ファイルパス
        """
        self.logger = logging.getLogger(__name__)
        self.project_root = Path('/home/aicompany/ai_co')
        self.config_path = config_path or self._get_default_config_path()
        
        # エルダーズギルド品質基準
        self.quality_thresholds = {
            'minimum_score': 7.0,  # 最低スコア
            'max_critical_issues': 0,  # クリティカル問題許容数
            'max_high_issues': 5,  # 高優先度問題許容数
            'max_complexity': 20,  # 最大複雑度
        }
        
    def _get_default_config_path(self) -> str:
        """デフォルト設定ファイルパス取得"""
        default_path = self.project_root / '.pylintrc'
        if default_path.exists():
            return str(default_path)
        return None
        
    async def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """単一ファイル分析"""
        self.logger.info(f"🔍 Analyzing file with Pylint: {file_path}")
        
        try:
            result = await self._run_pylint([file_path])
            
            # 分析結果生成
            analysis = {
                'file': file_path,
                'score': result.score,
                'previous_score': result.previous_score,
                'total_issues': result.total_issues,
                'issues_by_severity': result.issues_by_severity,
                'issues_by_category': result.issues_by_category,
                'critical_issues': [
                    self._format_issue(issue) 
                    for issue in result.issues 
                    if issue.severity == 'critical'
                ],
                'high_priority_issues': [
                    self._format_issue(issue)
                    for issue in result.issues
                    if issue.severity == 'high'
                ][:10],  # 最初の10件
                'quality_passed': self._check_quality_thresholds(result),
                'recommendations': self._generate_recommendations(result)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ Pylint analysis failed: {e}")
            return {
                'file': file_path,
                'error': str(e),
                'score': 0.0,
                'quality_passed': False
            }
            
    async def analyze_directory(self, directory: str) -> Dict[str, Any]:
        """ディレクトリ全体分析"""
        self.logger.info(f"📁 Analyzing directory with Pylint: {directory}")
        
        try:
            # Pythonファイル収集
            py_files = list(Path(directory).rglob('*.py'))
            py_files = [
                f for f in py_files 
                if '__pycache__' not in str(f) and '.pyc' not in str(f)
            ]
            
            if not py_files:
                return {
                    'directory': directory,
                    'error': 'No Python files found',
                    'total_files': 0
                }
                
            # バッチ分析
            result = await self._run_pylint([str(f) for f in py_files[:50]])  # 最大50ファイル
            
            # 統計情報生成
            analysis = {
                'directory': directory,
                'total_files': len(py_files),
                'analyzed_files': result.analyzed_files,
                'overall_score': result.score,
                'total_issues': result.total_issues,
                'issues_by_severity': result.issues_by_severity,
                'issues_by_category': result.issues_by_category,
                'quality_passed': self._check_quality_thresholds(result),
                'top_issues': self._get_top_issues(result),
                'worst_files': self._get_worst_files(result),
                'recommendations': self._generate_recommendations(result)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ Directory analysis failed: {e}")
            return {
                'directory': directory,
                'error': str(e),
                'total_files': 0
            }
            
    async def _run_pylint(self, targets: List[str]) -> PylintResult:
        """Pylint実行"""
        cmd = ['python3', '-m', 'pylint']
        
        # 設定ファイル指定
        if self.config_path:
            cmd.extend(['--rcfile', self.config_path])
            
        # 出力フォーマット
        cmd.extend([
            '--output-format=text',
            '--reports=yes',
            '--exit-zero'  # エラーでも終了コード0
        ])
        
        # ターゲット追加
        cmd.extend(targets)
        
        # 実行
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.project_root)
        )
        
        stdout, stderr = await process.communicate()
        
        # 結果パース
        return self._parse_pylint_output(stdout.decode())
        
    def _parse_pylint_output(self, output: str) -> PylintResult:
        """Pylint出力パース"""
        result = PylintResult()
        
        if not output.strip():
            return result
            
        try:
            # テキスト出力をパース
            lines = output.strip().split('\n')
            import re
            
            # 各行を処理
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # スコア情報を探す
                if 'Your code has been rated at' in line:
                    # スコア抽出
                    score_match = re.search(r'rated at ([\d.-]+)/10', line)
                    if score_match:
                        result.score = float(score_match.group(1))
                        
                    # 前回スコア
                    prev_match = re.search(r'previous run: ([\d.-]+)/10', line)
                    if prev_match:
                        result.previous_score = float(prev_match.group(1))
                
                # 問題行を検出（簡易パース）
                if ':' in line and ('error' in line.lower() or 'warning' in line.lower() or 'convention' in line.lower() or 'refactor' in line.lower()):
                    # パターン例: "libs/knowledge_consolidator.py:123:4: C0103: Invalid name 'x' (invalid-name)"
                    match = re.match(r'^([^:]+):(\d+):(\d+):\s*([CRWE]\d+):\s*(.+)', line)
                    if match:
                        file_path, line_no, col_no, msg_id, message = match.groups()
                        
                        # タイプを判定
                        type_map = {'C': 'convention', 'R': 'refactor', 'W': 'warning', 'E': 'error'}
                        issue_type = type_map.get(msg_id[0], 'unknown')
                        
                        issue = PylintIssue(
                            type=issue_type,
                            module=file_path.replace('/', '.').replace('.py', ''),
                            obj='',
                            line=int(line_no),
                            column=int(col_no),
                            message_id=msg_id,
                            symbol='',
                            message=message,
                            confidence=None
                        )
                        result.issues.append(issue)
                
            # ファイル数カウント
            modules = set(issue.module for issue in result.issues)
            result.analyzed_files = len(modules)
            
        except Exception as e:
            self.logger.error(f"Failed to parse Pylint output: {e}")
            
        return result
        
    def _check_quality_thresholds(self, result: PylintResult) -> bool:
        """品質基準チェック"""
        # スコアチェック
        if result.score < self.quality_thresholds['minimum_score']:
            return False
            
        # クリティカル問題チェック
        severity_count = result.issues_by_severity
        if severity_count.get('critical', 0) > self.quality_thresholds['max_critical_issues']:
            return False
            
        # 高優先度問題チェック
        if severity_count.get('high', 0) > self.quality_thresholds['max_high_issues']:
            return False
            
        return True
        
    def _format_issue(self, issue: PylintIssue) -> Dict[str, Any]:
        """問題情報フォーマット"""
        return {
            'file': issue.module,
            'line': issue.line,
            'column': issue.column,
            'severity': issue.severity,
            'category': issue.elder_guild_category,
            'message_id': issue.message_id,
            'symbol': issue.symbol,
            'message': issue.message,
            'confidence': issue.confidence
        }
        
    def _get_top_issues(self, result: PylintResult, limit: int = 10) -> List[Dict]:
        """最も重要な問題取得"""
        # 重要度でソート
        sorted_issues = sorted(
            result.issues,
            key=lambda i: (
                {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(i.severity, 4),
                i.line
            )
        )
        
        return [self._format_issue(issue) for issue in sorted_issues[:limit]]
        
    def _get_worst_files(self, result: PylintResult, limit: int = 5) -> List[Dict]:
        """最も問題の多いファイル取得"""
        file_issues = {}
        
        for issue in result.issues:
            module = issue.module
            if module not in file_issues:
                file_issues[module] = {
                    'total': 0,
                    'critical': 0,
                    'high': 0
                }
                
            file_issues[module]['total'] += 1
            if issue.severity == 'critical':
                file_issues[module]['critical'] += 1
            elif issue.severity == 'high':
                file_issues[module]['high'] += 1
                
        # 問題数でソート
        worst_files = sorted(
            file_issues.items(),
            key=lambda x: (x[1]['critical'], x[1]['high'], x[1]['total']),
            reverse=True
        )
        
        return [
            {
                'file': file,
                'total_issues': stats['total'],
                'critical_issues': stats['critical'],
                'high_issues': stats['high']
            }
            for file, stats in worst_files[:limit]
        ]
        
    def _generate_recommendations(self, result: PylintResult) -> List[str]:
        """改善推奨事項生成"""
        recommendations = []
        
        # スコアベース推奨
        if result.score < 5.0:
            recommendations.append("🚨 Critical: Major refactoring needed. Score is below 5.0")
        elif result.score < 7.0:
            recommendations.append("⚠️ Warning: Code quality needs improvement")
        elif result.score < 9.0:
            recommendations.append("📈 Good: Minor improvements will reach excellence")
            
        # 問題タイプ別推奨
        category_count = result.issues_by_category
        
        if category_count.get('syntax_error', 0) > 0:
            recommendations.append("🔧 Fix syntax errors immediately")
            
        if category_count.get('unused_code', 0) > 5:
            recommendations.append("🧹 Clean up unused imports and variables")
            
        if category_count.get('complexity_issue', 0) > 3:
            recommendations.append("♻️ Refactor complex functions for better maintainability")
            
        if category_count.get('import_issue', 0) > 0:
            recommendations.append("📦 Resolve import issues and circular dependencies")
            
        if category_count.get('style_issue', 0) > 20:
            recommendations.append("🎨 Apply consistent coding style (PEP 8)")
            
        # エルダーズギルド特有推奨
        if 'eval(' in str(result.issues):
            recommendations.append("🛡️ Security: Remove eval() usage - Iron Will violation")

        return recommendations[:5]  # 最大5つの推奨事項

# 便利関数
async def pylint_check_file(file_path: str) -> Dict[str, Any]:
    """ファイルのPylintチェック"""
    checker = ElderFlowPylintChecker()
    return await checker.analyze_file(file_path)
    
async def pylint_check_directory(directory: str) -> Dict[str, Any]:
    """ディレクトリのPylintチェック"""
    checker = ElderFlowPylintChecker()
    return await checker.analyze_directory(directory)

if __name__ == "__main__":
    async def test_pylint_checker():
        """Pylintチェッカーテスト"""
        checker = ElderFlowPylintChecker()
        
        # テストファイル作成
        test_file = "/tmp/test_pylint.py"
        with open(test_file, 'w') as f:
            f.write('''
"""Test module for Pylint"""
import os
import sys
import unused_module  # This will trigger unused-import

def bad_function(x, y):
    """Function with issues"""

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
        
        # ファイル分析
        print("🔍 Analyzing test file...")
        result = await checker.analyze_file(test_file)
        
        print(f"\n📊 Analysis Results:")
        print(f"Score: {result['score']}/10")
        print(f"Total Issues: {result['total_issues']}")
        print(f"Quality Passed: {result['quality_passed']}")
        
        print(f"\n🔥 Issues by Severity:")
        for severity, count in result['issues_by_severity'].items():
            print(f"  {severity}: {count}")
            
        print(f"\n📂 Issues by Category:")
        for category, count in result['issues_by_category'].items():
            print(f"  {category}: {count}")
            
        print(f"\n💡 Recommendations:")
        for rec in result['recommendations']:
            print(f"  {rec}")
            
    asyncio.run(test_pylint_checker())