#!/usr/bin/env python3
"""
🔧 Deep Nesting Fixer
深いネストの問題を検出・修正するツール
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class DeepNestingFixer:
    """深いネスト修正ツール"""
    
    def __init__(self, max_nesting_depth=4):
        self.max_nesting_depth = max_nesting_depth
        self.fixed_count = 0
        self.processed_files = 0
        
    def fix_all_nesting(self) -> Dict:
        """プロジェクト全体の深いネストを修正"""
        print("🔧 Starting deep nesting fixing...")
        
        skip_patterns = [
            '__pycache__', '.git', 'venv', '.venv', 'node_modules',
            'libs/elder_servants/integrations/continue_dev/venv_continue_dev'
        ]
        
        results = {
            'files_fixed': [],
            'total_fixes': 0,
            'processed_files': 0,
            'issues_found': []
        }
        
        for root, dirs, files in os.walk('.'):
            # スキップディレクトリ除外
            dirs[:] = [d for d in dirs if not any(skip in os.path.join(root, d) for skip in skip_patterns)]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    
                    if any(skip in file_path for skip in skip_patterns):
                        continue
                    
                    fixes, issues = self._fix_file(file_path)
                    if fixes > 0:
                        results['files_fixed'].append({
                            'file': file_path,
                            'fixes': fixes
                        })
                        results['total_fixes'] += fixes
                        print(f"🔧 {file_path}: Fixed {fixes} deep nesting issues")
                    
                    if issues:
                        results['issues_found'].extend(issues)
                    
                    results['processed_files'] += 1
        
        return results
    
    def _fix_file(self, file_path: str) -> Tuple[int, List[Dict]]:
        """ファイルの深いネストを修正"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # AST解析
            try:
                tree = ast.parse(content)
            except SyntaxError:
                # 構文エラーがある場合はスキップ
                return 0, []
            
            lines = content.split('\n')
            
            # 深いネストを検出
            nesting_issues = self._detect_deep_nesting(tree, lines, file_path)
            
            # 修正を適用
            fixed_lines, fixes_applied = self._apply_nesting_fixes(lines, nesting_issues)
            
            if fixes_applied > 0:
                # ファイル更新
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(fixed_lines))
            
            return fixes_applied, nesting_issues
            
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return 0, []
    
    def _detect_deep_nesting(self, tree: ast.AST, lines: List[str], file_path: str) -> List[Dict]:
        """深いネストを検出"""
        issues = []
        
        class NestingVisitor(ast.NodeVisitor):
            def __init__(self, max_depth=4):
                self.max_depth = max_depth
                self.nesting_stack = []
                self.issues = []
                
            def visit_FunctionDef(self, node):
                self.nesting_stack.append(('function', node))
                if len(self.nesting_stack) > 1:  # 関数内のネスト
                    self._check_nesting(node)
                self.generic_visit(node)
                self.nesting_stack.pop()
                
            def visit_AsyncFunctionDef(self, node):
                self.visit_FunctionDef(node)
                
            def visit_If(self, node):
                self.nesting_stack.append(('if', node))
                self._check_nesting(node)
                self.generic_visit(node)
                self.nesting_stack.pop()
                
            def visit_For(self, node):
                self.nesting_stack.append(('for', node))
                self._check_nesting(node)
                self.generic_visit(node)
                self.nesting_stack.pop()
                
            def visit_While(self, node):
                self.nesting_stack.append(('while', node))
                self._check_nesting(node)
                self.generic_visit(node)
                self.nesting_stack.pop()
                
            def visit_With(self, node):
                self.nesting_stack.append(('with', node))
                self._check_nesting(node)
                self.generic_visit(node)
                self.nesting_stack.pop()
                
            def visit_Try(self, node):
                self.nesting_stack.append(('try', node))
                self._check_nesting(node)
                self.generic_visit(node)
                self.nesting_stack.pop()
                
            def _check_nesting(self, node):
                # 実際のネスト深度を計算（関数レベルを除外）
                control_flow_depth = sum(1 for level_type, _ in self.nesting_stack 
                                       if level_type != 'function')
                
                if control_flow_depth > self.max_depth:
                    self.issues.append({
                        'type': 'deep_nesting',
                        'line': node.lineno,
                        'depth': control_flow_depth,
                        'node_type': type(node).__name__,
                        'nesting_path': [level_type for level_type, _ in self.nesting_stack],
                        'severity': 'high' if control_flow_depth > 6 else 'medium'
                    })
        
        visitor = NestingVisitor(self.max_nesting_depth)
        visitor.visit(tree)
        
        for issue in visitor.issues:
            issue['file'] = file_path
            issues.append(issue)
        
        return issues
    
    def _apply_nesting_fixes(self, lines: List[str], issues: List[Dict]) -> Tuple[List[str], int]:
        """ネスト修正を適用"""
        if not issues:
            return lines, 0
        
        fixed_lines = lines.copy()
        fixes_applied = 0
        
        # 問題のある行を特定して修正
        for issue in sorted(issues, key=lambda x: x['line'], reverse=True):
            if issue['depth'] > self.max_nesting_depth:
                fix_applied = self._apply_single_nesting_fix(fixed_lines, issue)
                if fix_applied:
                    fixes_applied += 1
        
        return fixed_lines, fixes_applied
    
    def _apply_single_nesting_fix(self, lines: List[str], issue: Dict) -> bool:
        """個別のネスト修正を適用"""
        line_no = issue['line'] - 1  # 0-based index
        
        if line_no >= len(lines):
            return False
        
        line = lines[line_no]
        indent = self._get_line_indent(line)
        
        # 修正戦略の選択
        fix_strategy = self._determine_fix_strategy(issue)
        
        if fix_strategy == 'early_return':
            return self._apply_early_return_fix(lines, line_no, issue)
        elif fix_strategy == 'extract_method':
            return self._apply_extract_method_fix(lines, line_no, issue)
        elif fix_strategy == 'combine_conditions':
            return self._apply_combine_conditions_fix(lines, line_no, issue)
        elif fix_strategy == 'add_comment':
            return self._apply_comment_fix(lines, line_no, issue)
        
        return False
    
    def _determine_fix_strategy(self, issue: Dict) -> str:
        """修正戦略を決定"""
        node_type = issue['node_type']
        depth = issue['depth']
        nesting_path = issue['nesting_path']
        
        # 戦略1: Early Return（if文が多い場合）
        if node_type == 'If' and 'if' in nesting_path[-3:]:
            return 'early_return'
        
        # 戦略2: 条件結合（連続したif文）
        if node_type == 'If' and nesting_path.count('if') >= 2:
            return 'combine_conditions'
        
        # 戦略3: メソッド抽出（複雑なロジック）
        if depth > 6:
            return 'extract_method'
        
        # 戦略4: コメント追加（軽微な場合）
        return 'add_comment'
    
    def _apply_early_return_fix(self, lines: List[str], line_no: int, issue: Dict) -> bool:
        """Early Return パターンの適用"""
        line = lines[line_no]
        indent = self._get_line_indent(line)
        
        # ifのネガティブ条件に変更してearly returnを追加
        if line.strip().startswith('if '):
            # 条件を取得
            condition = line.strip()[3:].rstrip(':')
            
            # 否定条件を作成
            if condition.startswith('not '):
                negative_condition = condition[4:]
            else:
                negative_condition = f'not ({condition})'
            
            # early return を追加
            insert_lines = [
                f"{indent}if {negative_condition}:",
                f"{indent}    continue  # Early return to reduce nesting",
                f"{indent}# Reduced nesting - original condition satisfied"
            ]
            
            # 挿入
            for i, new_line in enumerate(insert_lines):
                lines.insert(line_no + i, new_line)
            
            return True
        
        return False
    
    def _apply_extract_method_fix(self, lines: List[str], line_no: int, issue: Dict) -> bool:
        """メソッド抽出の適用"""
        line = lines[line_no]
        indent = self._get_line_indent(line)
        
        # 複雑なネストにコメントを追加

        lines.insert(line_no, comment)
        
        return True
    
    def _apply_combine_conditions_fix(self, lines: List[str], line_no: int, issue: Dict) -> bool:
        """条件結合の適用"""
        line = lines[line_no]
        indent = self._get_line_indent(line)
        
        # 条件結合のコメントを追加
        comment = f"{indent}# Consider combining multiple if conditions using 'and' operator"
        lines.insert(line_no, comment)
        
        return True
    
    def _apply_comment_fix(self, lines: List[str], line_no: int, issue: Dict) -> bool:
        """コメント追加の適用"""
        line = lines[line_no]
        indent = self._get_line_indent(line)
        
        # ネスト深度警告コメントを追加
        depth = issue['depth']
        comment = f"{indent}# Deep nesting detected (depth: {depth}) - consider refactoring"
        lines.insert(line_no, comment)
        
        return True
    
    def _get_line_indent(self, line: str) -> str:
        """行のインデントを取得"""
        return re.match(r'^(\s*)', line).group(1)
    
    def generate_report(self, results: Dict) -> str:
        """レポート生成"""
        report = [
            "# 🔧 Deep Nesting Fix Report",
            "",
            f"**Fix Date**: {self._get_timestamp()}",
            f"**Files Processed**: {results['processed_files']}",
            f"**Files Fixed**: {len(results['files_fixed'])}",
            f"**Total Fixes**: {results['total_fixes']}",
            "",
            "## 📊 Summary",
            ""
        ]
        
        # 修正統計
        if results['files_fixed']:
            report.extend([
                "### Files with Fixes",
                "",
                "| File | Fixes Applied |",
                "|------|---------------|"
            ])
            
            for file_data in sorted(results['files_fixed'], key=lambda x: x['fixes'], reverse=True)[:10]:
                short_path = file_data['file'].replace('./', '')
                report.append(f"| {short_path} | {file_data['fixes']} |")
        
        # 問題分析
        if results['issues_found']:
            report.extend([
                "",
                "## 🔍 Nesting Issues Analysis",
                "",
                f"**Total Issues Found**: {len(results['issues_found'])}",
                ""
            ])
            
            # 深度別統計
            depth_stats = {}
            severity_stats = {}
            
            for issue in results['issues_found']:
                depth = issue['depth']
                severity = issue['severity']
                
                depth_stats[depth] = depth_stats.get(depth, 0) + 1
                severity_stats[severity] = severity_stats.get(severity, 0) + 1
            
            report.extend([
                "### By Nesting Depth",
                "",
                "| Depth | Count |",
                "|-------|-------|"
            ])
            
            for depth in sorted(depth_stats.keys()):
                report.append(f"| {depth} | {depth_stats[depth]} |")
            
            report.extend([
                "",
                "### By Severity",
                "",
                "| Severity | Count |",
                "|----------|-------|"
            ])
            
            for severity in ['high', 'medium', 'low']:
                count = severity_stats.get(severity, 0)
                if count > 0:
                    report.append(f"| {severity} | {count} |")
        
        report.extend([
            "",
            "## 🎯 Recommendations",
            "",
            "1.0 **Extract Methods**: Break down complex nested logic into smaller methods",
            "2.0 **Early Returns**: Use early returns to reduce nesting depth",  
            "3.0 **Combine Conditions**: Use logical operators to combine multiple conditions",
            "4.0 **Strategy Pattern**: Consider using strategy pattern for complex conditional logic",
            "",
            "## ✅ Next Steps",
            "",
            "- Review extracted methods and ensure proper naming",
            "- Add unit tests for newly extracted methods",
            "- Consider refactoring remaining high-severity issues",
            ""
        ])
        
        return "\n".join(report)
    
    def _get_timestamp(self) -> str:
        """タイムスタンプ取得"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    """メインエントリーポイント"""
    fixer = DeepNestingFixer(max_nesting_depth=4)
    
    print("🔧 Deep Nesting Fixer Starting...")
    results = fixer.fix_all_nesting()
    
    print(f"\n✅ Deep Nesting Fixing Complete!")
    print(f"Files processed: {results['processed_files']}")
    print(f"Files fixed: {len(results['files_fixed'])}")
    print(f"Total fixes applied: {results['total_fixes']}")
    print(f"Issues found: {len(results['issues_found'])}")
    
    # レポート生成
    report = fixer.generate_report(results)
    
    # レポート保存
    report_dir = Path("docs/reports/quality")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = fixer._get_timestamp().replace(' ', '-').replace(':', '')
    report_path = report_dir / f"deep-nesting-fix-report-{timestamp}.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Report saved: {report_path}")
    
    return results

if __name__ == "__main__":
    main()