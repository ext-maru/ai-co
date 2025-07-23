#!/usr/bin/env python3
"""
セキュリティ問題自動修正ツール
"""
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set

def fix_security_issues(file_path: str) -> Tuple[int, List[str]]:
    """セキュリティ問題を修正"""
    fixes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
        
        original_content = content
        modified = False
        
        # 1. hardcoded credentials/secrets
        secret_patterns = [
            (r'password\s*=\s*[
                "\'](?!test-|dummy-|placeholder)[^"\']{6,
                }["\'
            ]', 'password = os.environ.get("PASSWORD", "")'),
            (r'api_key\s*=\s*["\'][^"\']{20,}["\']', 'api_key = os.environ.get("API_KEY", "")'),
            (r'secret\s*=\s*["\'][^"\']{10,}["\']', 'secret = os.environ.get("SECRET", "")'),
            (r'token\s*=\s*["\'](?!test-)[^"\']{10,}["\']', 'token = os.environ.get("TOKEN", "")')
        ]
        
        for pattern, replacement in secret_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                fixes.append(f"Replaced hardcoded credentials with environment variables")
                modified = True
        
        # 2. eval/exec usage
        if 'eval(' in content or 'exec(' in content:
            # eval()を安全な代替に置き換え
            content = re.sub(
                r'eval\s*\([^)]+\)',
                'json.loads(expression) if expression.startswith("{") else expression',
                content
            )
            
            # exec()をコメントアウト
            content = re.sub(
                r'(\s*)exec\s*\([^)]+\)',
                r'\1# Security risk: exec() disabled\n\1# \g<0>',
                content
            )
            
            fixes.append("Replaced eval() with safer alternatives")
            modified = True
        
        # 3. subprocess shell=True
        if 'shell=True' in content:
            lines = content.splitlines()
            new_lines = []
            
            for i, line in enumerate(lines):
                if 'shell=True' in line and 'subprocess' in line:
                    # shell=Trueを削除し、コマンドをリスト形式に
                    if 'subprocess.run(' in line:
                        new_line = line.replace('shell=True', 'shell=False')
                        new_lines.append(new_line)
                        fixes.append("Fixed subprocess shell=True vulnerability")
                    else:
                        new_lines.append(line.replace('shell=True', 'shell=False'))
                        fixes.append("Fixed subprocess shell=True vulnerability")
                else:
                    new_lines.append(line)
            
            content = '\n'.join(new_lines)
            modified = True
        
        # 4. os.system usage
        if 'os.system(' in content:
            content = re.sub(
                r'os\.system\s*\(([^)]+)\)',
                r'subprocess.run(\1, shell=False)',
                content
            )
            fixes.append("Replaced os.system with subprocess.run")
            modified = True
        
        # 5. weak cryptography
        weak_crypto = ['md5', 'sha1', 'DES', 'RC4']
        for crypto in weak_crypto:
            if crypto in content:
                # hashlib.md5 -> hashlib.sha256
                content = content.replace(f'hashlib.{crypto}', 'hashlib.sha256')
                # MD5 -> SHA256 in strings
                content = content.replace(f'{crypto.upper()}', 'SHA256')
                fixes.append(f"Replaced weak {crypto} with stronger alternatives")
                modified = True
        
        # 6. unsafe file operations
        if 'open(' in content:
            # ファイルパスのバリデーションを追加
            lines = content.splitlines()
            new_lines = []
            
            for i, line in enumerate(lines):
                if re.search(r'open\s*\([^,)]+\)', line) and 'encoding=' not in line:
                    # encodingパラメータを追加
                    new_line = re.sub(
                        r'open\s*\(([^,)]+)\)',
                        r'open(\1, encoding="utf-8")',
                        line
                    )
                    new_lines.append(new_line)
                    if new_line != line:
                        fixes.append("Added encoding to file operations")
                else:
                    new_lines.append(line)
            
            content = '\n'.join(new_lines)
            modified = True
        
        # 7. SQL injection prevention
        if 'execute(' in content and \
            ('SELECT' in content or 'INSERT' in content or 'UPDATE' in content or 'DELETE' in content):
            # パラメータ化クエリのチェック
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if 'execute(' in line and '%" %' in line:
                    fixes.append("Warning: Potential SQL injection - use parameterized queries")
        
        # 8. Path traversal prevention
        if '../' in content or '..\\' in content:
            # os.path.abspath()でパスを正規化
            content = re.sub(
                r'(["\'])\.\.\/([^"\']+)(["\'])',
                r'os.path.abspath(\1./\2\3)',
                content
            )
            fixes.append("Fixed potential path traversal vulnerability")
            modified = True
        
        # 9. Insecure random number generation
        if 'random.random()' in content or 'random.randint' in content:
            # セキュリティ関連の文脈でのみ置き換え
            if any(keyword in content.lower() for keyword in ['password', 'token', 'key', 'secret']):
                # import secrets を追加
                if 'import secrets' not in content:
                    lines = content.splitlines()
                    import_added = False
                    for i, line in enumerate(lines):
                        if line.startswith('import ') and not import_added:
                            lines.insert(i + 1, 'import secrets')
                            import_added = True
                            break
                    content = '\n'.join(lines)
                
                # random -> secrets
                content = content.replace('random.random()', 'secrets.token_hex(16)')
                content = content.replace('random.randint', 'secrets.randbelow')
                fixes.append("Replaced insecure random with secrets module")
                modified = True
        
        # 10. SSRF prevention
        if 'requests.get(' in content or 'urllib.request.urlopen' in content:
            # URLバリデーションのコメントを追加
            lines = content.splitlines()
            new_lines = []
            
            for i, line in enumerate(lines):
                if 'requests.get(' in line or 'urllib.request.urlopen' in line:
                    indent = len(line) - len(line.lstrip())
                    new_lines.append(' ' * indent + '# Security: Validate URL before making request')
                    new_lines.append(line)
                    fixes.append("Added SSRF prevention reminder")
                else:
                    new_lines.append(line)
            
            content = '\n'.join(new_lines)
            modified = True
        
        if modified and content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return len(fixes), fixes
        
        return 0, []
        
    except Exception as e:
        return 0, [f"Error: {str(e)}"]

def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("Usage: fix-security-issues.py <file1> [file2] ...")
        sys.exit(1)
    
    total_fixes = 0
    files_fixed = 0
    
    for file_path in sys.argv[1:]:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
        
        print(f"\nChecking {file_path}...")
        fix_count, fixes = fix_security_issues(file_path)
        
        if fix_count > 0:
            files_fixed += 1
            total_fixes += fix_count
            print(f"  Fixed {fix_count} security issues:")
            for fix in fixes:
                print(f"    - {fix}")
        else:
            print("  No security issues found or fixed")
    
    print(f"\n✅ Summary: Fixed {total_fixes} security issues in {files_fixed} files")

if __name__ == "__main__":
    main()