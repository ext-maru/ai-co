#!/usr/bin/env python3
"""品質違反の分析"""
import json
from collections import Counter

# JSONファイルを読み込み
with open('docs/reports/quality/quality-audit-20250723-023357.json', 'r') as f:
    data = json.load(f)

# 違反タイプを集計
violations = data.get('violations', [])
counts = Counter(v['violation_type'] for v in violations)

print("品質違反タイプ別統計:")
for vtype, count in counts.most_common():
    print(f"  {vtype}: {count}")

print(f"\n総違反数: {len(violations)}")
print(f"Iron Will準拠率: {data.get('iron_will_compliance', 0)}%")
print(f"品質スコア: {data.get('quality_score', 0)}/100")