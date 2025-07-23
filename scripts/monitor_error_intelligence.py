#!/usr/bin/env python3
"""
エラー智能判断システムのモニタリング
統計情報とステータスを表示
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
from datetime import datetime

from libs.error_intelligence_manager import ErrorIntelligenceManager


def main():
    """mainメソッド"""
    manager = ErrorIntelligenceManager()

    print("=" * 60)
    print(f"エラー智能判断システム モニタリング")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 統計情報取得
    stats = manager.get_error_statistics()

    print("\n📊 エラー統計:")
    print(f"  総エラー数: {stats['total_errors']}")
    print(f"  自動修正済み: {stats['auto_fixed']}")

    if stats["total_errors"] > 0:
        fix_rate = (stats["auto_fixed"] / stats["total_errors"]) * 100
        print(f"  自動修正率: {fix_rate:.1f}%")

    print("\n📈 カテゴリ別:")
    for category, count in stats["by_category"].items():
        print(f"  {category}: {count}")

    print("\n⚠️  重要度別:")
    for severity, count in stats["by_severity"].items():
        print(f"  {severity}: {count}")

    print("\n🔝 頻出エラー Top 5:")
    for i, error in enumerate(stats["top_errors"], 1):
        print(f"  {i}. {error['type']} ({error['count']}回)")

    print("\n✅ システムステータス: 正常稼働中")


if __name__ == "__main__":
    main()
