#!/usr/bin/env python3
"""
🏛️ Elder Guild Docstring Batch Fixer
エルダーズギルド バッチdocstring修正スクリプト

大量のdocstring不足を効率的に修正するツール
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class DocstringFixer:
    """docstring自動修正クラス"""
    
    def __init__(self):
        self.fixed_count = 0
        self.total_count = 0
        
    def fix_file_docstrings(self, file_path: str) -> bool:
        """ファイル内のdocstring不足を修正"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                original_content = content
            
            tree = ast.parse(content)
            lines = content.split('\n')
            
            # 修正対象を収集
            fixes = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        docstring = self._generate_docstring(node, file_path)
                        if not (docstring):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if docstring:
                            fixes.append((node.lineno, node, docstring))
            
            # 修正を適用（行番号の大きい順に処理）
            fixes.sort(key=lambda x: x[0], reverse=True)
            
            for line_no, node, docstring in fixes:
                # 関数/クラス定義行を見つける
                def_line_idx = line_no - 1
                
                # インデントを取得
                def_line = lines[def_line_idx]
                indent_match = re.match(r'^(\s*)', def_line)
                base_indent = indent_match.group(1) if indent_match else ''
                doc_indent = base_indent + '    '  # 4スペース追加
                
                # docstringを挿入
                if ':' in def_line:
                    # 同じ行にコロンがある場合
                    colon_pos = def_line.find(':')
                    if def_line[colon_pos+1:].strip() == '':
                        # コロンの後が空の場合、次の行に挿入
                        lines.insert(def_line_idx + 1, f'{doc_indent}"""{docstring}"""')
                    else:
                        # コロンの後に何かある場合、その前に挿入
                        rest = def_line[colon_pos+1:]
                        lines[def_line_idx] = def_line[:colon_pos+1]
                        lines.insert(def_line_idx + 1, f'{doc_indent}"""{docstring}"""')
                        lines.insert(def_line_idx + 2, f'{base_indent}{rest.lstrip()}')
                
                self.fixed_count += 1
            
            if fixes:
                # ファイルに書き戻し
                new_content = '\n'.join(lines)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"✅ Fixed {len(fixes)} docstrings in {file_path}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
            return False
    
    def _generate_docstring(self, node: ast.AST, file_path: str) -> str:
        """適切なdocstringを生成"""
        if isinstance(node, ast.ClassDef):
            return self._generate_class_docstring(node, file_path)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return self._generate_function_docstring(node, file_path)
        return ""
    
    def _generate_class_docstring(self, node: ast.ClassDef, file_path: str) -> str:
        """クラス用docstring生成"""
        class_name = node.name
        
        # Elder関連のクラス名パターン
        if 'Elder' in class_name:
            return f"{class_name} - エルダーズギルド関連クラス"
        elif 'Sage' in class_name:
            return f"{class_name} - 4賢者システム関連クラス"
        elif 'Guardian' in class_name:
            return f"{class_name} - 守護システムクラス"
        elif 'Manager' in class_name:
            return f"{class_name} - 管理システムクラス"
        elif 'Engine' in class_name:
            return f"{class_name} - エンジンクラス"
        elif 'Handler' in class_name:
            return f"{class_name} - ハンドラークラス"
        elif 'Builder' in class_name:
            return f"{class_name} - ビルダークラス"
        elif 'Parser' in class_name:
            return f"{class_name} - パーサークラス"
        elif 'Analyzer' in class_name:
            return f"{class_name} - 分析クラス"
        elif 'Detector' in class_name:
            return f"{class_name} - 検出器クラス"
        elif 'Tracker' in class_name:
            return f"{class_name} - トラッカークラス"
        elif 'Monitor' in class_name:
            return f"{class_name} - 監視クラス"
        else:
            return f"{class_name}クラス"
    
    def _generate_function_docstring(self, node: ast.FunctionDef, file_path: str) -> str:
        """関数用docstring生成"""
        func_name = node.name
        
        # 特殊メソッド
        if func_name == '__init__':
            return "初期化メソッド"
        elif func_name == '__str__':
            return "文字列表現取得"
        elif func_name == '__repr__':
            return "オブジェクト表現取得"
        elif func_name.startswith('__') and func_name.endswith('__'):
            return f"{func_name}特殊メソッド"
        
        # プライベート/保護メソッド
        if func_name.startswith('_'):
            if 'check' in func_name.lower():
                return f"{func_name[1:]}チェック（内部メソッド）"
            elif 'get' in func_name.lower():
                return f"{func_name[1:]}取得（内部メソッド）"
            elif 'set' in func_name.lower():
                return f"{func_name[1:]}設定（内部メソッド）"
            elif 'create' in func_name.lower():
                return f"{func_name[1:]}作成（内部メソッド）"
            else:
                return f"{func_name[1:]}（内部メソッド）"
        
        # パブリックメソッド
        if 'execute' in func_name.lower():
            return f"{func_name}実行メソッド"
        elif 'process' in func_name.lower():
            return f"{func_name}処理メソッド"
        elif 'analyze' in func_name.lower():
            return f"{func_name}分析メソッド"
        elif 'generate' in func_name.lower():
            return f"{func_name}生成メソッド"
        elif 'validate' in func_name.lower():
            return f"{func_name}検証メソッド"
        elif 'check' in func_name.lower():
            return f"{func_name}チェックメソッド"
        elif func_name.lower().startswith('get_'):
            return f"{func_name[4:]}取得メソッド"
        elif func_name.lower().startswith('set_'):
            return f"{func_name[4:]}設定メソッド"
        elif func_name.lower().startswith('is_'):
            return f"{func_name[3:]}判定メソッド"
        elif func_name.lower().startswith('has_'):
            return f"{func_name[4:]}存在確認メソッド"
        elif func_name.lower().startswith('can_'):
            return f"{func_name[4:]}可能性判定メソッド"
        elif func_name.lower().startswith('should_'):
            return f"{func_name[7:]}必要性判定メソッド"
        elif func_name.lower().startswith('create_'):
            return f"{func_name[7:]}作成メソッド"
        elif func_name.lower().startswith('build_'):
            return f"{func_name[6:]}構築メソッド"
        elif func_name.lower().startswith('load_'):
            return f"{func_name[5:]}読み込みメソッド"
        elif func_name.lower().startswith('save_'):
            return f"{func_name[5:]}保存メソッド"
        elif func_name.lower().startswith('update_'):
            return f"{func_name[7:]}更新メソッド"
        elif func_name.lower().startswith('delete_'):
            return f"{func_name[7:]}削除メソッド"
        elif func_name.lower().startswith('remove_'):
            return f"{func_name[7:]}除去メソッド"
        elif func_name.lower().startswith('add_'):
            return f"{func_name[4:]}追加メソッド"
        elif func_name.lower().startswith('find_'):
            return f"{func_name[5:]}検索メソッド"
        elif func_name.lower().startswith('search_'):
            return f"{func_name[7:]}検索メソッド"
        elif 'test' in func_name.lower():
            return f"{func_name}テストメソッド"
        else:
            return f"{func_name}メソッド"


def main():
    """メインエントリーポイント"""
    if len(sys.argv) < 2:
        print("Usage: python3 batch-docstring-fix.py <directory_or_file>")
        return 1
    
    target_path = Path(sys.argv[1])
    fixer = DocstringFixer()
    
    if target_path.is_file():
        # 単一ファイル処理
        files_to_process = [target_path]
    elif target_path.is_dir():
        # ディレクトリ処理
        files_to_process = list(target_path.rglob("*.py"))
    else:
        print(f"❌ Path not found: {target_path}")
        return 1
    
    print(f"🔧 Processing {len(files_to_process)} Python files...")
    
    for file_path in files_to_process:
        # テストファイル、__pycache__、migrations等をスキップ
        if any(skip in str(file_path) for skip in ['__pycache__', '.pyc', 'migrations', 'venv']):
            continue
            
        fixer.total_count += 1
        fixer.fix_file_docstrings(str(file_path))
    
    print(f"\n✅ Batch docstring fix completed!")
    print(f"📊 Fixed: {fixer.fixed_count} docstrings in {fixer.total_count} files")
    
    return 0


if __name__ == "__main__":
    exit(main())