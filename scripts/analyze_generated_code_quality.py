#!/usr/bin/env python3
"""
生成されたコードの品質を詳細に分析
"""

import ast
import json
from pathlib import Path
from typing import Dict, Any, List
import re

class CodeQualityAnalyzer:
    """コード品質分析器"""
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """単一ファイルの品質分析"""
        code = file_path.read_text()
        tree = ast.parse(code)
        
        analysis = {
            'file': str(file_path),
            'metrics': self._calculate_metrics(code, tree),
            'patterns': self._analyze_patterns(code, tree),
            'elder_flow_compatibility': self._check_elder_flow_compatibility(code, tree),
            'best_practices': self._check_best_practices(code, tree),
            'score': 0
        }
        
        # スコア計算
        analysis['score'] = self._calculate_score(analysis)
        
        return analysis
    
    def _calculate_metrics(self, code: str, tree: ast.AST) -> Dict[str, Any]:
        """基本メトリクスの計算"""
        lines = code.split('\n')
        
        # ASTウォーカーでクラスと関数を収集
        classes = []
        functions = []
        docstrings = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node)
            elif isinstance(node, ast.FunctionDef):
                functions.append(node)
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
                docstrings.append(node)
        
        # 型ヒントのある関数をカウント
        typed_functions = sum(1 for f in functions if f.returns or any(arg.annotation for arg in f.args.args))
        
        return {
            'total_lines': len(lines),
            'code_lines': len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
            'comment_lines': len([l for l in lines if l.strip().startswith('#')]),
            'blank_lines': len([l for l in lines if not l.strip()]),
            'classes': len(classes),
            'functions': len(functions),
            'docstrings': len(docstrings),
            'type_hints': typed_functions,
            'type_hint_ratio': typed_functions / max(len(functions), 1),
            'complexity': self._calculate_complexity(tree),
        }
    
    def _calculate_complexity(self, tree: ast.AST) -> Dict[str, Any]:
        """循環的複雑度の計算"""
        complexity = {
            'if_statements': 0,
            'for_loops': 0,
            'while_loops': 0,
            'try_blocks': 0,
            'total': 0
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                complexity['if_statements'] += 1
            elif isinstance(node, ast.For):
                complexity['for_loops'] += 1
            elif isinstance(node, ast.While):
                complexity['while_loops'] += 1
            elif isinstance(node, ast.Try):
                complexity['try_blocks'] += 1
        
        complexity['total'] = sum(complexity.values()) - complexity['total']
        return complexity
    
    def _analyze_patterns(self, code: str, tree: ast.AST) -> Dict[str, Any]:
        """コードパターンの分析"""
        patterns = {
            'error_handling': {
                'try_except': len(re.findall(r'\btry\s*:', code)),
                'custom_exceptions': len(re.findall(r'class\s+\w+\(.*Exception.*\)', code)),
                'logging_errors': len(re.findall(r'logger\.(error|exception)', code)),
            },
            'logging': {
                'logger_usage': len(re.findall(r'logger\.', code)),
                'log_levels': {
                    'debug': len(re.findall(r'logger\.debug', code)),
                    'info': len(re.findall(r'logger\.info', code)),
                    'warning': len(re.findall(r'logger\.warning', code)),
                    'error': len(re.findall(r'logger\.error', code)),
                }
            },
            'async_usage': {
                'async_functions': len(re.findall(r'async\s+def', code)),
                'await_calls': len(re.findall(r'\bawait\s+', code)),
            },
            'imports': {
                'standard_lib': len(re.findall(r'^import\s+(?:os|sys|re|json|time|datetime)', code, re.MULTILINE)),
                'third_party': len(
                    re.findall(r'^(?:import|from)\s+(?:pandas|numpy|requests|aiohttp)',
                    code,
                    re.MULTILINE)
                ),
                'project_imports': len(re.findall(r'^from\s+(?:libs|workers|commands)', code, re.MULTILINE)),
            }
        }
        
        return patterns
    
    def _check_elder_flow_compatibility(self, code: str, tree: ast.AST) -> Dict[str, bool]:
        """Elder Flow互換性チェック"""
        return {
            'has_execute_method': bool(re.search(r'def\s+execute\s*\(', code)),
            'returns_dict': bool(re.search(r'->\s*Dict\[str,\s*Any\]', code)),
            'has_logging': 'logger' in code,
            'has_error_handling': 'try:' in code,
            'has_docstrings': '"""' in code,
            'follows_naming_convention': bool(re.search(r'class\s+Issue\d+Implementation', code)),
        }
    
    def _check_best_practices(self, code: str, tree: ast.AST) -> Dict[str, bool]:
        """ベストプラクティスチェック"""
        return {
            'no_bare_except': not bool(re.search(r'except\s*:', code)),
            'no_print_statements': 'print(' not in code,
            'has_main_guard': 'if __name__ == "__main__":' in code,
            'uses_pathlib': 'Path(' in code,
            'uses_context_managers': 'with ' in code,
            'no_global_variables': not bool(re.findall(r'^[a-zA-Z_]\w*\s*=', code, re.MULTILINE)),
        }
    
    def _calculate_score(self, analysis: Dict[str, Any]) -> float:
        """総合スコアの計算（100点満点）"""
        score = 0
        
        # メトリクススコア（40点）
        metrics = analysis['metrics']
        score += min(20, metrics['type_hint_ratio'] * 20)  # 型ヒント
        score += min(10, (metrics['docstrings'] / max(metrics['classes'] + metrics['functions'], 1)) * 10)  # Docstring
        score += min(10, 10 if metrics['complexity']['total'] < 20 else 5)  # 複雑度
        
        # パターンスコア（30点）
        patterns = analysis['patterns']
        score += min(10, patterns['error_handling']['try_except'] * 2)  # エラーハンドリング
        score += min(10, min(patterns['logging']['logger_usage'], 5) * 2)  # ロギング
        score += min(10, 10 if patterns['imports']['project_imports'] == 0 else 5)  # 独立性
        
        # Elder Flow互換性（20点）
        elder_flow = analysis['elder_flow_compatibility']
        score += sum(3.33 for v in elder_flow.values() if v)
        
        # ベストプラクティス（10点）
        best_practices = analysis['best_practices']
        score += sum(1.67 for v in best_practices.values() if v)
        
        return min(100, round(score, 1))

def main():
    """メイン処理"""
    print("="*80)
    print("📊 生成コード品質分析")
    print("="*80)
    
    analyzer = CodeQualityAnalyzer()
    output_dir = Path("generated_code_samples")
    
    if not output_dir.exists():
        print("❌ generated_code_samplesディレクトリが見つかりません")
        return
    
    # 生成されたPythonファイルをすべて分析
    python_files = list(output_dir.glob("*.py"))
    
    if not python_files:
        print("❌ 分析対象のPythonファイルが見つかりません")
        return
    
    results = []
    
    # 繰り返し処理
    for file_path in python_files:
        print(f"\n📄 分析中: {file_path.name}")
        
        try:
            analysis = analyzer.analyze_file(file_path)
            results.append(analysis)
            
            # 結果表示
            print(f"\n  📈 メトリクス:")
            print(f"    - 総行数: {analysis['metrics']['total_lines']}行")
            print(f"    - コード行数: {analysis['metrics']['code_lines']}行")
            print(f"    - クラス数: {analysis['metrics']['classes']}")
            print(f"    - 関数数: {analysis['metrics']['functions']}")
            print(f"    - 型ヒント率: {analysis['metrics']['type_hint_ratio']*100:.1f}%")
            print(f"    - 循環的複雑度: {analysis['metrics']['complexity']['total']}")
            
            print(f"\n  🎯 Elder Flow互換性:")
            for key, value in analysis['elder_flow_compatibility'].items():
                print(f"    - {key}: {'✅' if value else '❌'}")
            
            print(f"\n  🏆 総合スコア: {analysis['score']}/100点")
            
        except Exception as e:
            print(f"  ❌ エラー: {e}")
    
    # サマリー
    if results:
        print("\n" + "="*80)
        print("📊 分析サマリー")
        print("="*80)
        
        avg_score = sum(r['score'] for r in results) / len(results)
        print(f"\n  - 分析ファイル数: {len(results)}")
        print(f"  - 平均品質スコア: {avg_score:.1f}/100点")
        
        # グレード判定
        if avg_score >= 90:
            grade = "A (Production Ready)"
        elif avg_score >= 80:
            grade = "B (High Quality)"
        elif avg_score >= 70:
            grade = "C (Acceptable)"
        else:
            grade = "D (Needs Improvement)"
        
        print(f"  - 品質グレード: {grade}")
        
        # 詳細レポート保存
        report = {
            'timestamp': Path("processing_summary.json").read_text() \
                if Path("processing_summary.json").exists() \
                else "N/A",
            'files_analyzed': len(results),
            'average_score': avg_score,
            'grade': grade,
            'detailed_results': results
        }
        
        report_path = output_dir / "quality_analysis_report.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"\n  📄 詳細レポート保存: {report_path}")

if __name__ == "__main__":
    main()