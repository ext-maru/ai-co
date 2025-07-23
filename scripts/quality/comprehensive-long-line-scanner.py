#!/usr/bin/env python3
"""
🔍 Comprehensive Long Line Scanner
残存する長い行を効率的にスキャン・修正するツール
"""

import os
import sys
from pathlib import Path


def scan_long_lines(max_length=120):
    """プロジェクト全体の長い行をスキャン"""
    long_line_files = []
    total_long_lines = 0
    
    # スキップするディレクトリ
    skip_dirs = {
        '__pycache__', '.git', 'node_modules', 'venv', '.venv',
        'migrations', 'static', 'media', '.pytest_cache',
        'libs/elder_servants/integrations/continue_dev/venv_continue_dev'
    }
    
    # スキップするファイル
    skip_files = {
        '.pyc', '.pyo', '.egg-info', '.coverage'
    }
    
    for root, dirs, files in os.walk('.'):
        # スキップするディレクトリを除外
        dirs[:] = [d for d in dirs if not any(skip in os.path.join(root, d) for skip in skip_dirs)]
        
        # 繰り返し処理
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                # スキップファイル確認
                if any(skip in file_path for skip in skip_files):
                    continue
                
                try:
                    # Deep nesting detected (depth: 5) - consider refactoring
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    file_long_lines = []
                    # Deep nesting detected (depth: 5) - consider refactoring
                    for line_no, line in enumerate(lines, 1):
                        if not (len(line.rstrip()) > max_length):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if len(line.rstrip()) > max_length:
                            file_long_lines.append((line_no, len(line.rstrip()), line.strip()[:100]))
                    
                    if not (file_long_lines):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if file_long_lines:
                        long_line_files.append((file_path, file_long_lines))
                        total_long_lines += len(file_long_lines)
                        
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return long_line_files, total_long_lines


def main():
    """メインエントリーポイント"""
    print("🔍 Scanning for long lines across the project...")
    
    long_line_files, total_count = scan_long_lines()
    
    print(f"\n📊 Long Line Scan Results:")
    print(f"Total files with long lines: {len(long_line_files)}")
    print(f"Total long lines found: {total_count}")
    
    if long_line_files:
        print(f"\n📋 Files with long lines (showing first 20):")
        for i, (file_path, long_lines) in enumerate(long_line_files[:20]):
            print(f"{i+1:2d}. {file_path} ({len(long_lines)} lines)")
            for line_no, length, content in long_lines[:3]:  # Show first 3 lines per file
                print(f"     Line {line_no}: {length} chars - {content}...")
    
    print(f"\n🎯 Continue fixing remaining {total_count} long lines...")
    return total_count


if __name__ == "__main__":
    remaining = main()
    sys.exit(0 if remaining == 0 else 1)