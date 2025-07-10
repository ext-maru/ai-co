#!/usr/bin/env python3
"""
Execute Grimoire Migration
魔法書移行実行スクリプト（簡略版）

依存関係とエラーを回避して、基本的なファイル収集と移行を実行
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# プロジェクトルート追加
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def discover_md_files(root_path: str = ".") -> list:
    """MDファイル発見"""
    print(f"🔍 Discovering MD files in {root_path}...")
    
    md_files = []
    root_path_obj = Path(root_path)
    
    # 除外パターン
    exclude_patterns = [
        'venv', 'node_modules', '__pycache__', 
        'temp', 'tmp', '.git', '.pytest_cache'
    ]
    
    for md_file in root_path_obj.rglob("*.md"):
        # 除外パターンチェック
        should_exclude = False
        for pattern in exclude_patterns:
            if pattern in str(md_file):
                should_exclude = True
                break
        
        if not should_exclude:
            md_files.append(str(md_file.absolute()))
    
    print(f"✅ Found {len(md_files)} MD files")
    return md_files

def analyze_file(file_path: str) -> dict:
    """ファイル簡易分析"""
    try:
        path_obj = Path(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 基本情報
        size = len(content.encode())
        
        # 簡単な分類
        path_lower = str(path_obj).lower()
        content_lower = content.lower()
        
        # 魔法学派判定
        if 'task' in path_lower or 'workflow' in content_lower:
            magic_school = 'task_oracle'
        elif 'incident' in path_lower or 'error' in content_lower:
            magic_school = 'crisis_sage'
        elif 'search' in path_lower or 'rag' in content_lower:
            magic_school = 'search_mystic'
        else:
            magic_school = 'knowledge_sage'
        
        # 重要度判定
        if 'readme' in path_lower or 'claude' in path_lower:
            importance = 'HIGH'
        elif 'knowledge_base' in path_lower:
            importance = 'MEDIUM'
        else:
            importance = 'LOW'
        
        return {
            'file_path': file_path,
            'relative_path': str(path_obj.relative_to(Path.cwd())),
            'file_name': path_obj.name,
            'size': size,
            'magic_school': magic_school,
            'importance': importance,
            'content_preview': content[:200] + "..." if len(content) > 200 else content
        }
        
    except Exception as e:
        print(f"❌ Analysis failed for {file_path}: {e}")
        return None

def create_migration_report(analyses: list) -> dict:
    """移行レポート作成"""
    # 統計計算
    total_files = len(analyses)
    
    by_school = {}
    by_importance = {}
    total_size = 0
    
    for analysis in analyses:
        if analysis:
            school = analysis['magic_school']
            importance = analysis['importance']
            
            by_school[school] = by_school.get(school, 0) + 1
            by_importance[importance] = by_importance.get(importance, 0) + 1
            total_size += analysis['size']
    
    return {
        'migration_summary': {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'by_magic_school': by_school,
            'by_importance': by_importance
        },
        'migration_plan': {
            'high_priority_files': [a for a in analyses if a and a['importance'] == 'HIGH'],
            'medium_priority_files': [a for a in analyses if a and a['importance'] == 'MEDIUM'],
            'low_priority_files': [a for a in analyses if a and a['importance'] == 'LOW']
        },
        'timestamp': datetime.now().isoformat(),
        'database_ready': False,  # PostgreSQL未接続
        'next_steps': [
            "PostgreSQL + pgvector環境構築",
            "魔法書データベーススキーマ作成",
            "実際のベクトル化実装",
            "4賢者統合システム完成"
        ]
    }

def main():
    """メイン実行"""
    print("=" * 80)
    print("🏛️ Elders Guild Grimoire Migration Analysis")
    print("=" * 80)
    
    # 1. ファイル発見
    md_files = discover_md_files()
    
    if not md_files:
        print("❌ No MD files found")
        return
    
    print(f"\n📊 Analyzing {len(md_files)} files...")
    
    # 2. ファイル分析
    analyses = []
    for i, file_path in enumerate(md_files):
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i + 1}/{len(md_files)}")
        
        analysis = analyze_file(file_path)
        if analysis:
            analyses.append(analysis)
    
    # 3. レポート生成
    report = create_migration_report(analyses)
    
    # 4. レポート保存
    report_dir = Path("migration_reports")
    report_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"grimoire_analysis_{timestamp}.json"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 5. 結果表示
    summary = report['migration_summary']
    
    print("\n" + "=" * 80)
    print("📊 Migration Analysis Complete!")
    print("=" * 80)
    print(f"📁 Total files: {summary['total_files']}")
    print(f"💾 Total size: {summary['total_size_mb']} MB")
    print()
    print("🏫 By Magic School:")
    for school, count in summary['by_magic_school'].items():
        print(f"  • {school}: {count} files")
    print()
    print("⚡ By Importance:")
    for importance, count in summary['by_importance'].items():
        print(f"  • {importance}: {count} files")
    print()
    print(f"📄 Report saved: {report_path}")
    print()
    
    # 重要ファイルの表示
    high_priority = report['migration_plan']['high_priority_files']
    if high_priority:
        print("🔥 High Priority Files:")
        for file_info in high_priority[:10]:  # 最初の10個
            print(f"  • {file_info['relative_path']}")
        if len(high_priority) > 10:
            print(f"  ... and {len(high_priority) - 10} more")
        print()
    
    print("🚀 Next Steps:")
    for step in report['next_steps']:
        print(f"  1. {step}")
    
    print("=" * 80)
    print("🎯 Ready for actual PostgreSQL + pgvector migration!")
    print("=" * 80)

if __name__ == "__main__":
    main()