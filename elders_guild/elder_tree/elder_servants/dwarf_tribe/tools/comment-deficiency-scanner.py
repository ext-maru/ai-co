#!/usr/bin/env python3
"""
💬 Comment Deficiency Scanner
コメント不足を検出・修正するツール
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set


class CommentDeficiencyScanner:
    """コメント不足スキャナー"""
    
    def __init__(self):
        self.deficiencies = []
        self.scanned_files = 0
        self.total_functions = 0
        self.commented_functions = 0
        
    def scan_project(self) -> Dict:
        """プロジェクト全体をスキャン"""
        print("💬 Starting comment deficiency scan...")
        
        skip_patterns = [
            '__pycache__', '.git', 'venv', '.venv', 'node_modules',
            'libs/elder_servants/integrations/continue_dev/venv_continue_dev'
        ]
        
        results = {
            'files_with_deficiencies': [],
            'total_deficiencies': 0,
            'total_files_scanned': 0,
            'function_comment_ratio': 0.0,
            'class_comment_ratio': 0.0
        }
        
        for root, dirs, files in os.walk('.'):
            # スキップディレクトリ除外
            dirs[:] = [d for d in dirs if not any(skip in os.path.join(root, d) for skip in skip_patterns)]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    
                    if any(skip in file_path for skip in skip_patterns):
                        continue
                    
                    deficiencies = self._scan_file(file_path)
                    if deficiencies:
                        results['files_with_deficiencies'].append({
                            'file': file_path,
                            'deficiencies': deficiencies,
                            'count': len(deficiencies)
                        })
                        results['total_deficiencies'] += len(deficiencies)
                    
                    results['total_files_scanned'] += 1
        
        # 統計計算
        if self.total_functions > 0:
            results['function_comment_ratio'] = (self.commented_functions / self.total_functions) * 100
        
        return results
    
    def _scan_file(self, file_path: str) -> List[Dict]:
        """ファイルの内容をスキャンしてコメント不足を検出"""
        deficiencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # AST解析
            try:
                tree = ast.parse(content)
                deficiencies.extend(self._analyze_ast(tree, content, file_path))
            except SyntaxError:
                # 構文エラーがある場合はスキップ
                return []
        
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
            
        return deficiencies
    
    def _analyze_ast(self, tree: ast.AST, content: str, file_path: str) -> List[Dict]:
        """ASTを分析してコメント不足を検出"""
        deficiencies = []
        lines = content.split('\n')
        
        # 関数とクラスを分析
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.total_functions += 1
                deficiency = self._check_function_comments(node, lines, file_path)
                if deficiency:
                    deficiencies.append(deficiency)
                else:
                    self.commented_functions += 1
            
            elif isinstance(node, ast.ClassDef):
                deficiency = self._check_class_comments(node, lines, file_path)
                if deficiency:
                    deficiencies.append(deficiency)
        
        # 複雑な処理の分析
        deficiencies.extend(self._check_complex_logic_comments(tree, lines, file_path))
        
        return deficiencies
    
    def _check_function_comments(self, node: ast.FunctionDef, lines: List[str], file_path: str) -> Optional[Dict]:
        """関数のコメント不足をチェック"""
        func_name = node.name
        line_no = node.lineno
        
        # docstringチェック
        has_docstring = (
            node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)
        )
        
        # インラインコメントチェック
        has_inline_comments = False
        func_end_line = self._get_function_end_line(node, lines)
        
        for i in range(line_no - 1, min(func_end_line, len(lines))):
            if '#' in lines[i] and not lines[i].strip().startswith('#'):
                has_inline_comments = True
                break
        
        # コメント不足の判定
        if not has_docstring and not has_inline_comments:
            # 特殊関数は除外
            if func_name.startswith('__') and func_name.endswith('__'):
                return None
            
            # 短い関数（3行以下）は除外
            if func_end_line - line_no <= 3:
                return None
            
            return {
                'type': 'missing_function_comment',
                'line': line_no,
                'name': func_name,
                'severity': 'medium',
                'message': f'Function "{func_name}" lacks documentation or inline comments',
                'suggestion': 'Add docstring or inline comments explaining the function purpose'
            }
        
        return None
    
    def _check_class_comments(self, node: ast.ClassDef, lines: List[str], file_path: str) -> Optional[Dict]:
        """クラスのコメント不足をチェック"""
        class_name = node.name
        line_no = node.lineno
        
        # docstringチェック
        has_docstring = (
            node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)
        )
        
        if not has_docstring:
            return {
                'type': 'missing_class_comment',
                'line': line_no,
                'name': class_name,
                'severity': 'medium',
                'message': f'Class "{class_name}" lacks docstring',
                'suggestion': 'Add class docstring explaining purpose and usage'
            }
        
        return None
    
    def _check_complex_logic_comments(self, tree: ast.AST, lines: List[str], file_path: str) -> List[Dict]:
        """複雑なロジックのコメント不足をチェック"""
        deficiencies = []
        
        for node in ast.walk(tree):
            # 複雑な条件文
            if isinstance(node, ast.If) and self._is_complex_condition(node.test):
                line_no = node.lineno
                if not self._has_nearby_comment(lines, line_no):
                    deficiencies.append({
                        'type': 'missing_complex_logic_comment',
                        'line': line_no,
                        'name': 'complex_condition',
                        'severity': 'low',
                        'message': 'Complex conditional logic lacks explanatory comment',
                        'suggestion': 'Add comment explaining the condition logic'
                    })
            
            # 複雑なループ
            elif isinstance(node, (ast.For, ast.While)) and self._is_complex_loop(node):
                line_no = node.lineno
                if not self._has_nearby_comment(lines, line_no):
                    deficiencies.append({
                        'type': 'missing_loop_comment',
                        'line': line_no,
                        'name': 'complex_loop',
                        'severity': 'low',
                        'message': 'Complex loop logic lacks explanatory comment',
                        'suggestion': 'Add comment explaining the loop purpose'
                    })
        
        return deficiencies
    
    def _get_function_end_line(self, node: ast.FunctionDef, lines: List[str]) -> int:
        """関数の終了行を取得"""
        if hasattr(node, 'end_lineno') and node.end_lineno:
            return node.end_lineno
        
        # fallback: 次の関数の開始行を探す
        start_line = node.lineno
        for i in range(start_line, len(lines)):
            line = lines[i].strip()
            if line.startswith('def ') or line.startswith('class ') or (
                line and not line.startswith(' ') and not line.startswith('\t') and not line.startswith('#')
            ):
                if i != start_line - 1:
                    return i
        
        return len(lines)
    
    def _is_complex_condition(self, node: ast.expr) -> bool:
        """条件が複雑かどうか判定"""
        if isinstance(node, ast.BoolOp):
            return len(node.values) >= 3  # 3つ以上の条件
        elif isinstance(node, ast.Compare):
            return len(node.comparators) >= 2  # 2つ以上の比較
        return False
    
    def _is_complex_loop(self, node) -> bool:
        """ループが複雑かどうか判定"""
        # ネストしたループや複雑な条件を持つループ
        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While)) and child != node:
                return True  # ネストループ
        return False
    
    def _has_nearby_comment(self, lines: List[str], line_no: int) -> bool:
        """近くにコメントがあるかチェック"""
        # 前後2行以内にコメントがあるかチェック
        start = max(0, line_no - 3)
        end = min(len(lines), line_no + 2)
        
        for i in range(start, end):
            if '#' in lines[i]:
                return True
        
        return False
    
    def generate_report(self, results: Dict) -> str:
        """レポート生成"""
        report = [
            "# 💬 Comment Deficiency Scan Report",
            "",
            f"**Scan Date**: {self._get_timestamp()}",
            f"**Files Scanned**: {results['total_files_scanned']}",
            f"**Total Deficiencies**: {results['total_deficiencies']}",
            "",
            "## 📊 Summary",
            "",
            f"- **Function Comment Ratio**: {results['function_comment_ratio']:0.1f}%",
            f"- **Files with Issues**: {len(results['files_with_deficiencies'])}",
            "",
            "## 📋 Deficiency Types",
            "",
            "| Type | Count | Severity |",
            "|------|--------|----------|"
        ]
        
        # 種類別集計
        type_counts = {}
        for file_data in results['files_with_deficiencies']:
            for deficiency in file_data['deficiencies']:
                def_type = deficiency['type']
                severity = deficiency['severity']
                if def_type not in type_counts:
                    type_counts[def_type] = {'count': 0, 'severity': severity}
                type_counts[def_type]['count'] += 1
        
        for def_type, data in type_counts.items():
            report.append(f"| {def_type} | {data['count']} | {data['severity']} |")
        
        report.extend([
            "",
            "## 📂 Files with Deficiencies",
            ""
        ])
        
        # ファイル別詳細
        for file_data in sorted(results['files_with_deficiencies'][:20], key=lambda x: x['count'], reverse=True):
            report.extend([
                f"### {file_data['file']} ({file_data['count']} issues)",
                ""
            ])
            
            for deficiency in file_data['deficiencies'][:5]:  # 上位5件
                report.append(f"- **Line {deficiency['line']}**: {deficiency['message']}")
            
            if len(file_data['deficiencies']) > 5:
                report.append(f"- ... and {len(file_data['deficiencies']) - 5} more")
            
            report.append("")
        
        if len(results['files_with_deficiencies']) > 20:
            report.append(f"*... and {len(results['files_with_deficiencies']) - 20} more files*")
        
        return "\n".join(report)
    
    def _get_timestamp(self) -> str:
        """タイムスタンプ取得"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    """メインエントリーポイント"""
    scanner = CommentDeficiencyScanner()
    
    print("💬 Comment Deficiency Scanner Starting...")
    results = scanner.scan_project()
    
    print(f"\n📊 Scan Complete!")
    print(f"Files scanned: {results['total_files_scanned']}")
    print(f"Total deficiencies: {results['total_deficiencies']}")
    print(f"Function comment ratio: {results['function_comment_ratio']:0.1f}%")
    
    # レポート生成
    report = scanner.generate_report(results)
    
    # レポート保存
    report_dir = Path("docs/reports/quality")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = scanner._get_timestamp().replace(' ', '-').replace(':', '')
    report_path = report_dir / f"comment-deficiency-report-{timestamp}.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Report saved: {report_path}")
    
    return results


if __name__ == "__main__":
    main()