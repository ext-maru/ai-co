#!/usr/bin/env python3
"""
🏛️ Elder Flow Pylintコマンド
Elder FlowシステムでPylintチェックを実行するCLIツール

使用例:
    # ファイルチェック
    elder-flow-pylint check file.py
    
    # ディレクトリチェック
    elder-flow-pylint check-dir /path/to/project
    
    # プロジェクト全体チェック
    elder-flow-pylint check-all
    
    # 品質ゲート実行
    elder-flow-pylint quality-gate
"""

import sys
import asyncio
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.elder_flow_pylint_checker import (
    ElderFlowPylintChecker,
    pylint_check_file,
    pylint_check_directory
)
from libs.elder_flow_quality_gate_real import QualityGateManagerReal


class ElderFlowPylintCLI:
    """Elder Flow Pylint CLIツール"""
    
    def __init__(self):
        self.checker = ElderFlowPylintChecker()
        self.quality_gate = QualityGateManagerReal()
        
    async def check_file(self, file_path: str) -> int:
        """単一ファイルチェック"""
        print(f"🔍 Checking file: {file_path}")
        print("=" * 80)
        
        result = await self.checker.analyze_file(file_path)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return 1
            
        # 結果表示
        self._display_file_result(result)
        
        # 品質合格判定
        if result['quality_passed']:
            print("\n✅ Quality check PASSED")
            return 0
        else:
            print("\n❌ Quality check FAILED")
            return 1
            
    async def check_directory(self, directory: str) -> int:
        """ディレクトリチェック"""
        print(f"📁 Checking directory: {directory}")
        print("=" * 80)
        
        result = await self.checker.analyze_directory(directory)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return 1
            
        # 結果表示
        self._display_directory_result(result)
        
        # 品質合格判定
        if result['quality_passed']:
            print("\n✅ Quality check PASSED")
            return 0
        else:
            print("\n❌ Quality check FAILED")
            return 1
            
    async def check_all(self) -> int:
        """プロジェクト全体チェック"""
        print("🏛️ Checking entire project")
        print("=" * 80)
        
        # 主要ディレクトリをチェック
        directories = ['libs', 'scripts', 'commands', 'workers']
        total_score = 0
        total_files = 0
        all_passed = True
        
        for dir_name in directories:
            dir_path = PROJECT_ROOT / dir_name
            if dir_path.exists():
                print(f"\n📂 Checking {dir_name}/...")
                result = await self.checker.analyze_directory(str(dir_path))
                
                if 'error' not in result:
                    score = result['overall_score']
                    files = result['analyzed_files']
                    passed = result['quality_passed']
                    
                    total_score += score * files
                    total_files += files
                    all_passed = all_passed and passed
                    
                    print(f"  Score: {score:.1f}/10 ({files} files)")
                    print(f"  Issues: {result['total_issues']}")
                    print(f"  Status: {'✅ PASSED' if passed else '❌ FAILED'}")
                    
        # 総合結果
        if total_files > 0:
            overall_score = total_score / total_files
            print(f"\n{'=' * 80}")
            print(f"📊 Overall Project Score: {overall_score:.1f}/10")
            print(f"📁 Total Files Analyzed: {total_files}")
            print(f"🎯 Overall Status: {'✅ PASSED' if all_passed else '❌ FAILED'}")
            
            return 0 if all_passed else 1
        else:
            print("❌ No Python files found to analyze")
            return 1
            
    async def run_quality_gate(self) -> int:
        """品質ゲート実行"""
        print("🛡️ Running Elder Flow Quality Gate with Pylint")
        print("=" * 80)
        
        # 品質ゲート実行
        context = {
            'task_description': 'Elder Flow Pylint Quality Check',
            'timestamp': datetime.now().isoformat()
        }
        
        result = await self.quality_gate.run_quality_checks(context)
        
        # 結果表示
        self._display_quality_gate_result(result)
        
        # ステータス判定
        overall_status = result['overall_status'].value
        if overall_status == 'passed':
            print("\n✅ Quality Gate PASSED")
            return 0
        elif overall_status == 'warning':
            print("\n⚠️ Quality Gate PASSED with WARNINGS")
            return 0
        else:
            print("\n❌ Quality Gate FAILED")
            return 1
            
    def _display_file_result(self, result: Dict[str, Any]):
        """ファイル結果表示"""
        print(f"\n📊 Pylint Score: {result['score']:.1f}/10")
        print(f"📋 Total Issues: {result['total_issues']}")
        
        # 重要度別問題数
        if result['issues_by_severity']:
            print("\n🔥 Issues by Severity:")
            for severity, count in result['issues_by_severity'].items():
                icon = {'critical': '🚨', 'high': '⚠️', 'medium': '📌', 'low': '💡'}.get(severity, '•')
                print(f"  {icon} {severity.capitalize()}: {count}")
                
        # カテゴリ別問題数
        if result['issues_by_category']:
            print("\n📂 Issues by Category:")
            for category, count in result['issues_by_category'].items():
                print(f"  • {category.replace('_', ' ').title()}: {count}")
                
        # クリティカル問題
        if result.get('critical_issues'):
            print("\n🚨 Critical Issues:")
            for issue in result['critical_issues'][:5]:
                print(f"  Line {issue['line']}: {issue['message']}")
                
        # 推奨事項
        if result.get('recommendations'):
            print("\n💡 Recommendations:")
            for rec in result['recommendations']:
                print(f"  • {rec}")
                
    def _display_directory_result(self, result: Dict[str, Any]):
        """ディレクトリ結果表示"""
        print(f"\n📊 Overall Score: {result['overall_score']:.1f}/10")
        print(f"📁 Files Analyzed: {result['analyzed_files']}/{result['total_files']}")
        print(f"📋 Total Issues: {result['total_issues']}")
        
        # 重要度別問題数
        if result['issues_by_severity']:
            print("\n🔥 Issues by Severity:")
            for severity, count in result['issues_by_severity'].items():
                icon = {'critical': '🚨', 'high': '⚠️', 'medium': '📌', 'low': '💡'}.get(severity, '•')
                print(f"  {icon} {severity.capitalize()}: {count}")
                
        # 最も問題の多いファイル
        if result.get('worst_files'):
            print("\n📁 Files with Most Issues:")
            for file_info in result['worst_files']:
                print(f"  • {Path(file_info['file']).name}: {file_info['total_issues']} issues")
                
        # 推奨事項
        if result.get('recommendations'):
            print("\n💡 Recommendations:")
            for rec in result['recommendations']:
                print(f"  • {rec}")
                
    def _display_quality_gate_result(self, result: Dict[str, Any]):
        """品質ゲート結果表示"""
        overall_status = result['overall_status'].value
        summary = result['summary']
        
        print(f"\n🎯 Overall Status: {overall_status.upper()}")
        print(f"✅ Passed Checks: {summary['passed']}/{summary['total_checks']}")
        print(f"❌ Failed Checks: {summary['failed']}/{summary['total_checks']}")
        print(f"⚠️ Warning Checks: {summary['warnings']}/{summary['total_checks']}")
        
        # チェック結果詳細
        print("\n📋 Check Results:")
        for check_type, check_result in result['check_results'].items():
            status_icon = {
                'passed': '✅',
                'warning': '⚠️',
                'failed': '❌'
            }.get(check_result.status.value, '•')
            
            print(f"\n{status_icon} {check_type.value}:")
            
            # 主要メトリクス表示
            for metric in check_result.metrics[:3]:
                passed_icon = '✓' if metric.passed else '✗'
                print(f"  {passed_icon} {metric.name}: {metric.value:.1f}{metric.unit} (threshold: {metric.threshold}{metric.unit})")
                
        # 総合推奨事項
        if summary['recommendations']:
            print("\n💡 Top Recommendations:")
            for rec in summary['recommendations']:
                print(f"  • {rec}")


async def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='Elder Flow Pylint Quality Checker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # check コマンド
    check_parser = subparsers.add_parser('check', help='Check a single file')
    check_parser.add_argument('file', help='Python file to check')
    
    # check-dir コマンド
    checkdir_parser = subparsers.add_parser('check-dir', help='Check a directory')
    checkdir_parser.add_argument('directory', help='Directory to check')
    
    # check-all コマンド
    subparsers.add_parser('check-all', help='Check entire project')
    
    # quality-gate コマンド
    subparsers.add_parser('quality-gate', help='Run full quality gate')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
        
    cli = ElderFlowPylintCLI()
    
    # コマンド実行
    if args.command == 'check':
        return await cli.check_file(args.file)
    elif args.command == 'check-dir':
        return await cli.check_directory(args.directory)
    elif args.command == 'check-all':
        return await cli.check_all()
    elif args.command == 'quality-gate':
        return await cli.run_quality_gate()
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)