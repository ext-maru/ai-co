#!/usr/bin/env python3
"""
Mega Comma Eliminator - 超強力カンマエラー撲滅システム
🎯 78件のcomma errorを完全撲滅する最終兵器
"""
import os
import re
import ast
from pathlib import Path
from typing import List, Dict, Tuple

def get_comma_error_files_detailed() -> List[Dict]:


"""カンマエラーファイルの詳細情報を取得"""
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    ast.parse(content)
                except SyntaxError as e:
                    if 'comma' in e.msg.lower():
                        # エラー周辺のコンテキストを取得
                        lines = content.split('\n')
                        context_start = max(0, e.lineno - 3)
                        context_end = min(len(lines), e.lineno + 2)
                        context = lines[context_start:context_end]
                        
                        comma_files.append({
                            'file_path': file_path,
                            'line_no': e.lineno,
                            'error_msg': e.msg,
                            'error_text': e.text.strip() if e.text else '',
                            'context': context,
                            'priority': get_file_priority(file_path)
                        })
                except Exception:
                    pass
    
    # 優先度順にソート
    comma_files.sort(key=lambda x: x['priority'])
    return comma_files

def get_file_priority(file_path: str) -> int:
    """ファイル優先度を算出"""
    filename = os.path.basename(file_path).lower()
    
    # 高優先度キーワード
    high_priority = ['elder_flow', 'task_sage', 'knowledge_sage', 'incident_sage', 'rag_sage']
    medium_priority = ['elder', 'sage', 'ancient', 'council']
    
    for i, keyword in enumerate(high_priority):
        if keyword in filename:
            return i
            
    for i, keyword in enumerate(medium_priority):
        if keyword in filename:
            return len(high_priority) + i
            
    return 1000  # 低優先度

def mega_fix_comma_error(file_info: Dict) -> bool:
    """メガ級カンマエラー修正"""
    file_path = file_info['file_path']
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 超強力パターンマッチング集
        patterns = [
            # パターン1: Basic function with docstring separation
            {
                'pattern': r'(\s*)(def|async def)\s+([a-zA-Z_]\w*)\s*\(\s*([^)]*?):\s*\n(\s*)"""([^"]*?)"""\s*\n\s*([^)]+?)\):',
                'replacement': r'\1\2 \3(\4: \7):\n\5"""\6"""',
                'flags': re.MULTILINE | re.DOTALL
            },
            
            # パターン2: __init__ method specific
            {
                'pattern': r'(\s*)def\s+__init__\s*\(\s*(self[^)]*?):\s*\n(\s*)"""([^"]*?)"""\s*\n\s*([^)]+?)\):',
                'replacement': r'\1def __init__(\2: \5):\n\3"""\4"""',
                'flags': re.MULTILINE | re.DOTALL
            },
            
            # パターン3: Multiple parameters
            {
                'pattern': r'(\s*)(def|async def)\s+([a-zA-Z_]\w*)\s*\(\s*([^:,]*?),\s*([^)]*?):\s*\n(\s*)"""([^"]*?)"""\s*\n\s*([^)]+?)\):',
                'replacement': r'\1\2 \3(\4, \5: \8):\n\6"""\7"""',
                'flags': re.MULTILINE | re.DOTALL
            },
            
            # パターン4: Class method with self
            {
                'pattern': r'(\s*)def\s+([a-zA-Z_]\w*)\s*\(\s*(self,\s*[^)]*?):\s*\n(\s*)"""([^"]*?)"""\s*\n\s*([^)]+?)\):',
                'replacement': r'\1def \2(\3: \6):\n\4"""\5"""',
                'flags': re.MULTILINE | re.DOTALL
            },
            
            # パターン5: Static/class methods
            {
                'pattern': r'(\s*)@(staticmethod|classmethod)\s*\n(\s*)def\s+([a-zA-Z_]\w*)\s*\(\s*([^)]*?):\s*\n(\s*)"""([^"]*?)"""\s*\n\s*([^)]+?)\):',
                'replacement': r'\1@\2\n\3def \4(\5: \8):\n\6"""\7"""',
                'flags': re.MULTILINE | re.DOTALL
            },
            
            # パターン6: Property methods
            {
                'pattern': r'(\s*)@property\s*\n(\s*)def\s+([a-zA-Z_]\w*)\s*\(\s*(self[^)]*?):\s*\n(\s*)"""([^"]*?)"""\s*\n\s*([^)]+?)\):',
                'replacement': r'\1@property\n\2def \3(\4: \7):\n\5"""\6"""',
                'flags': re.MULTILINE | re.DOTALL
            },
        ]
        
        # 各パターンを順次適用
        for pattern_info in patterns:
            pattern = re.compile(pattern_info['pattern'], pattern_info['flags'])
            if pattern.search(content):
                content = pattern.sub(pattern_info['replacement'], content)
        
        # 特殊ケース: 複雑な型アノテーション
        content = fix_complex_type_annotations(content)
        
        if content != original_content:
            try:
                # 構文チェック
                ast.parse(content)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except SyntaxError as new_error:
                print(f"❌ 修正後構文エラー {os.path.basename(file_path)}: {new_error.msg}")
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ 修正エラー {os.path.basename(file_path)}: {e}")
        return False

def fix_complex_type_annotations(content: str) -> str:
    """複雑な型アノテーションの修正"""
    
    # Optional[Type] = None パターン
    pattern1 = re.compile(
        r'(\s*)(def|async def)\s+([a-zA-Z_]\w*)\s*\(\s*([^:]*?):\s*\n(\s*)"""([^"]*?)"""\s*\n\s*(Optional\[[^\]]+\])\s*=\s*([^)]+)\):',
        re.MULTILINE | re.DOTALL
    )
    content = pattern1.sub(r'\1\2 \3(\4: \7 = \8):\n\5"""\6"""', content)
    
    # Union[Type1, Type2] パターン  
    pattern2 = re.compile(
        r'(\s*)(def|async def)\s+([a-zA-Z_]\w*)\s*\(\s*([^:]*?):\s*\n(\s*)"""([^"]*?)"""\s*\n\s*(Union\[[^\]]+\])\):',
        re.MULTILINE | re.DOTALL
    )
    content = pattern2.sub(r'\1\2 \3(\4: \7):\n\5"""\6"""', content)
    
    # List[Type], Dict[Key, Value] パターン
    pattern3 = re.compile(
        r'(\s*)(def|async def)\s+([a-zA-Z_]\w*)\s*\(\s*([^:]*?):\s*\n(\s*)"""([^"]*?)"""\s*\n\s*((?:List|Dict|Set|Tuple)\[[^\]]+\])\):',
        re.MULTILINE | re.DOTALL
    )
    content = pattern3.sub(r'\1\2 \3(\4: \7):\n\5"""\6"""', content)
    
    return content

def main():

    
    """メイン実行""" {len(comma_files)}件")
    
    if not comma_files:
        print("✅ カンマエラーなし！すでに撲滅完了")
        return
    
    # 優先度別表示
    print(f"\n📋 上位10ファイル（優先度順）:")
    for i, file_info in enumerate(comma_files[:10]):
        filename = os.path.basename(file_info['file_path'])
        print(f"   {i+1:2d}. {filename} (line {file_info['line_no']}) - Priority: {file_info['priority']}")
    
    # メガ修正実行
    print(f"\n🚀 メガ級修正開始 - {len(comma_files)}件処理")
    fixed_count = 0
    failed_files = []
    
    for i, file_info in enumerate(comma_files):
        filename = os.path.basename(file_info['file_path'])
        print(f"[{i+1:3d}/{len(comma_files)}] Processing: {filename}")
        
        if mega_fix_comma_error(file_info):
            print(f"✅ Fixed: {filename}")
            fixed_count += 1
        else:
            print(f"❌ Failed: {filename}")
            failed_files.append(file_info)
    
    # 結果確認
    remaining_comma_files = get_comma_error_files_detailed()
    
    print("=" * 80)
    print(f"🎯 メガ撲滅結果:")
    print(f"   処理前: {len(comma_files)}件")
    print(f"   修正成功: {fixed_count}件")
    print(f"   処理後: {len(remaining_comma_files)}件")
    reduction_rate = (len(comma_files) - len(remaining_comma_files)) / max(1, len(comma_files)) * 100
    print(f"   削減率: {reduction_rate:.1f}%")
    
    if len(remaining_comma_files) == 0:
        print("\n🎉 カンマエラー完全撲滅達成！")
    else:
        print(f"\n🎯 残存{len(remaining_comma_files)}件への対策継続中...")
        
        # 失敗ファイルの詳細分析
        if failed_files:
            print(f"\n🔍 修正失敗ファイル分析:")
            for file_info in failed_files[:5]:
                print(f"   - {os.path.basename(file_info['file_path'])}: {file_info['error_msg']}")

if __name__ == "__main__":
    main()