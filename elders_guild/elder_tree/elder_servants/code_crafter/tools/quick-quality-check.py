#!/usr/bin/env python3
"""
簡易品質チェックスクリプト
"""

import os
import re
from pathlib import Path
from datetime import datetime
import json

def check_quality():
    """簡易品質チェック"""
    base_path = Path("/home/aicompany/ai_co")
    
    # 問題集計
    issues = {
        "security": [],
        "quality": [],
        "performance": [],
        "iron_will": []
    }
    
    # スキャン対象ファイル
    py_files = list(base_path.rglob("*.py"))
    py_files = [f for f in py_files if not any(
        p in str(f) for p in ["venv", ".git", "__pycache__", "migrations"]
    )]
    
    print(f"🔍 {len(py_files)}個のPythonファイルをスキャン中...")
    
    # 各ファイルチェック
    for i, file_path in enumerate(py_files):
        if i % 100 == 0:
            print(f"進捗: {i}/{len(py_files)}")
            
        try:
            content = file_path.read_text(encoding='utf-8')
            relative_path = str(file_path.relative_to(base_path))
            
            # セキュリティチェック（文字列内の誤検知を避ける）
            # コメントと文字列を除外してチェック
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                # コメントを除外
                if '#' in line:
                    line = line[:line.index('#')]
                # 文字列内のパターンを除外（簡易的）
                if '"eval(' in line or "'eval(" in line or 'r"eval' in line or "r'eval" in line:
                    continue
                if re.search(r'\beval\s*\(', line):
                    issues["security"].append({
                        "file": relative_path,
                        "issue": f"eval() usage detected at line {line_num}",
                        "severity": "critical"
                    })
                    
                # 複雑な条件判定
                if '"exec(' in line or "'exec(" in line or 'r"exec' in line or "r'exec" in line:
                    continue
                if re.search(r'\bexec\s*\(', line):
                    issues["security"].append({
                        "file": relative_path,
                        "issue": f"exec() usage detected at line {line_num}",
                        "severity": "critical"
                    })
                
            if re.search(r"password\s*=\s*[\"'][^\"']+[\"']", content):
                issues["security"].append({
                    "file": relative_path,
                    "issue": "Hardcoded password detected",
                    "severity": "high"
                })
            
            # Iron Will違反

                if pattern in content:
                    issues["iron_will"].append({
                        "file": relative_path,
                        "pattern": pattern,
                        "count": content.count(pattern)
                    })
                    break
            
            # 品質チェック（ファイル長）
            lines = content.split('\n')
            if len(lines) > 1000:
                issues["quality"].append({
                    "file": relative_path,
                    "issue": f"File too long ({len(lines)} lines)",
                    "severity": "medium"
                })
            
            # 複雑度の簡易チェック（深いネスト）
            max_indent = 0
            for line in lines:
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    max_indent = max(max_indent, indent // 4)
            
            if max_indent > 5:
                issues["quality"].append({
                    "file": relative_path,
                    "issue": f"Deep nesting detected (level {max_indent})",
                    "severity": "medium"
                })
                
        except Exception as e:
            pass
    
    # レポート生成
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_files": len(py_files),
        "issues": issues,
        "summary": {
            "security_issues": len(issues["security"]),
            "quality_issues": len(issues["quality"]),
            "iron_will_violations": len(issues["iron_will"]),
            "critical_count": sum(1 for i in issues["security"] if i.get("severity") == "critical")
        }
    }
    
    # 結果表示
    print(f"\n📊 品質チェック完了")
    print(f"総ファイル数: {report['total_files']}")
    print(f"セキュリティ問題: {report['summary']['security_issues']}件")
    print(f"品質問題: {report['summary']['quality_issues']}件")
    print(f"Iron Will違反: {report['summary']['iron_will_violations']}件")
    print(f"重大な問題: {report['summary']['critical_count']}件")
    
    # 重大な問題の詳細
    if report['summary']['critical_count'] > 0:
        print("\n🚨 重大なセキュリティ問題:")
        for issue in issues["security"][:10]:
            if issue.get("severity") == "critical":
                print(f"  - {issue['file']}: {issue['issue']}")
    
    # レポート保存
    output_path = Path("/tmp/quick_quality_report.json")
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 詳細レポート: {output_path}")
    
    return report['summary']['critical_count'] == 0

if __name__ == "__main__":
    success = check_quality()
    exit(0 if success else 1)