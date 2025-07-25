#\!/usr/bin/env python3
"""
FINAL CLEANUP - 最終クリーンアップ
"""

import ast
import re
from pathlib import Path

def main()print("🔧 FINAL CLEANUP - 最終クリーンアップ")
"""メイン処理"""
    
    # 全体のシンタックスチェック
    print("\n🔍 最終チェック...")
    project_root = Path('/home/aicompany/ai_co')
    error_count = 0
    error_files = []
    
    for py_file in project_root.rglob('*.py'):
        if any(skip in str(py_file) for skip in ['.venv', '__pycache__', 'node_modules', '.git', 'site-packages']):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
        except SyntaxError as e:
            error_count += 1
            error_files.append(f"{py_file.relative_to(project_root)}:{e.lineno} - {e.msg}")
            if error_count <= 20:
                print(f"❌ {py_file.relative_to(project_root)}:{e.lineno} - {e.msg}")
    
    print(f"\n📊 最終結果:")
    print(f"  初期エラー: 1651")
    print(f"  残存エラー: {error_count}")
    print(f"  修正済み: {1651 - error_count}")
    print(f"  削減率: {((1651-error_count)/1651*100):.1f}%")
    
    if error_count == 0:
        print("\n🎉 完全勝利！すべてのシンタックスエラーが殲滅されました！")
    elif error_count <= 20:
        print(f"\n⚔️  残り {error_count} エラー - ほぼ完了！")
    else:
        print(f"\n📈 大幅改善達成！")

if __name__ == "__main__":
    main()
EOF < /dev/null
