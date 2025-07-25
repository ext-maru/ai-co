#!/usr/bin/env python3
"""
Pylintを使用した構文エラー修正スクリプト
Elder Flow品質基準準拠
"""

import os
import re
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class PylintSyntaxFixer:
    """Pylintベースの構文エラー修正ツール"""
    
    def __init__(self):
        self.fixed_count = 0
        self.error_patterns = {
            'missing_colon': {
                'pattern': r'def\s+__init__\s*\(self\)([^:\n]+)\n(\s*)"""',
                'replacement': r'def __init__(self):\n\2"""',
                'description': 'メソッド定義のコロン欠落'
            },
            'continue_outside_loop': {
                'pattern': r'(\s*)if\s+not\s*\(([^)]+)\):\s*\n\s*continue\s*(?:#.*)?(?:\n\s*#.*)?',
                'replacement': r'\1# Removed invalid continue statement',
                'description': 'ループ外のcontinue文'
            },
            'malformed_method': {
                'pattern': r'def\s+(\w+)\s*\(self\)(\w+)',
                'replacement': r'def \1(self):\n    """\2メソッド"""',
                'description': '不正なメソッド定義'
            },
            'duplicate_condition': {
                'pattern': r'(\s*)if\s+([^:]+):\s*\n(\s*)if\s+\2:',
                'replacement': r'\1if \2:',
                'description': '重複条件文'
            }
        }
        
    def run_pylint(self, filepath: str) -> Optional[Dict]:
        """Pylintを実行して構文エラーを検出"""
        try:
            # 構文エラーのみを検出
            cmd = [
                'pylint',
                '--errors-only',
                '--disable=all',
                '--enable=E0001',  # syntax-error
                '--output-format=json',
                filepath
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.stdout:
                messages = json.loads(result.stdout)
                return messages[0] if messages else None
                
        except Exception as e:
            print(f"Pylint実行エラー: {e}")
            
        return None
    
    def analyze_file(self, filepath: str) -> List[Dict]:
        """ファイルの構文エラーを分析"""
        errors = []
        
        # Pylintでエラー検出
        pylint_error = self.run_pylint(filepath)
        if pylint_error:
            errors.append({
                'file': filepath,
                'line': pylint_error.get('line', 0),
                'message': pylint_error.get('message', ''),
                'type': 'syntax-error'
            })
            
        # 追加の静的解析
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 各パターンをチェック
            for error_type, config in self.error_patterns.items():
                matches = list(re.finditer(config['pattern'], content))
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    errors.append({
                        'file': filepath,
                        'line': line_num,
                        'message': config['description'],
                        'type': error_type,
                        'match': match
                    })
                    
        except Exception as e:
            print(f"ファイル分析エラー {filepath}: {e}")
            
        return errors
    
    def fix_file(self, filepath: str, errors: List[Dict]) -> bool:
        """ファイルの構文エラーを修正"""
        if not errors:
            return False
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            
            # エラータイプごとに修正
            for error in errors:
                error_type = error.get('type')
                
                if error_type in self.error_patterns:
                    config = self.error_patterns[error_type]
                    content = re.sub(
                        config['pattern'],
                        config['replacement'],
                        content
                    )
                    
            # 特殊なケースの処理
            # 連続したコロンの修正
            content = re.sub(r':\s*:', ':', content)
            
            # 空の括弧の後の不正な文字
            content = re.sub(r'\(\)([a-zA-Z])', r'():\n    """\1', content)
            
            if content != original_content:
                # バックアップ作成
                backup_path = f"{filepath}.bak"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                    
                # 修正内容を書き込み
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                # 修正後の検証
                if self.verify_fix(filepath):
                    self.fixed_count += 1
                    os.remove(backup_path)  # 成功したらバックアップ削除
                    return True
                else:
                    # 修正が失敗したら復元
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    os.remove(backup_path)
                    
        except Exception as e:
            print(f"修正エラー {filepath}: {e}")
            
        return False
    
    def verify_fix(self, filepath: str) -> bool:
        """修正後のファイルを検証"""
        try:
            # Pythonコンパイルで検証
            compile(open(filepath).read(), filepath, 'exec')
            
            # Pylintで再検証
            pylint_error = self.run_pylint(filepath)
            return pylint_error is None
            
        except:
            return False
    
    def process_directory(self, directory: str, max_files: int = None):
        """ディレクトリ内のファイルを処理"""
        print(f"🔍 {directory} 内の構文エラーを検索中...")
        
        all_errors = []
        processed = 0
        
        for root, dirs, files in os.walk(directory):
            # 除外ディレクトリ
            if any(skip in root for skip in ['venv', 'site-packages', '.git', '__pycache__']):
                continue
                
            for file in files:
                if not file.endswith('.py'):
                    continue
                    
                if max_files and processed >= max_files:
                    break
                    
                filepath = os.path.join(root, file)
                errors = self.analyze_file(filepath)
                
                if errors:
                    all_errors.append((filepath, errors))
                    
                processed += 1
                
        print(f"\n📊 分析結果:")
        print(f"  - 検査ファイル数: {processed}")
        print(f"  - エラーのあるファイル: {len(all_errors)}")
        
        if not all_errors:
            print("✅ 構文エラーは見つかりませんでした！")
            return
            
        # エラー種別の集計
        error_types = {}
        for _, errors in all_errors:
            for error in errors:
                error_type = error.get('type', 'unknown')
                error_types[error_type] = error_types.get(error_type, 0) + 1
                
        print("\n📋 エラー種別:")
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {error_type}: {count}件")
            
        # 修正実行
        print("\n🔧 修正を開始します...")
        fixed_files = []
        
        for filepath, errors in all_errors:
            if self.fix_file(filepath, errors):
                fixed_files.append(filepath)
                print(f"  ✅ 修正完了: {filepath}")
            else:
                print(f"  ❌ 修正失敗: {filepath}")
                
        print(f"\n✨ 修正結果:")
        print(f"  - 修正成功: {len(fixed_files)}ファイル")
        print(f"  - 修正失敗: {len(all_errors) - len(fixed_files)}ファイル")
        
    def generate_report(self, output_file: str = "syntax_fix_report.md"):
        """修正レポートを生成"""
        report = f"""# 構文エラー修正レポート

## 実行結果
- 修正ファイル数: {self.fixed_count}

## 使用ツール
- Pylint {subprocess.check_output(['pylint', '--version']).decode().split()[1]}
- Python {sys.version.split()[0]}

## 修正パターン
"""
        
        for error_type, config in self.error_patterns.items():
            report += f"\n### {config['description']}\n"
            report += f"- タイプ: `{error_type}`\n"
            report += f"- パターン: `{config['pattern'][:50]}...`\n"
            
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
            
        print(f"\n📄 レポートを生成しました: {output_file}")

def main():
    """メイン処理"""
    fixer = PylintSyntaxFixer()
    
    # libsディレクトリを優先的に処理
    print("🚀 Pylintベース構文エラー修正ツール")
    print("="*50)
    
    # 段階的に処理
    directories = [
        ('libs/elder_servants', 50),
        ('libs/integrations', 50),
        ('libs/ancient_elder', 30),
        ('libs', 100),
    ]
    
    for directory, max_files in directories:
        if os.path.exists(directory):
            print(f"\n🗂️ 処理中: {directory}")
            fixer.process_directory(directory, max_files)
            
    # レポート生成
    fixer.generate_report("docs/reports/pylint_syntax_fix_report.md")

if __name__ == '__main__':
    main()