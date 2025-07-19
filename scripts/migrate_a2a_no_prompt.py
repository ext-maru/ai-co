#!/usr/bin/env python3
"""
A2A通信データのpgvectorへの移行スクリプト（プロンプトなし版）
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.migrate_a2a_to_pgvector import A2APgVectorMigration


def main():
    """メイン処理"""
    print("🚀 A2A to pgvector Migration (No Embeddings)")
    print("=" * 60)

    try:
        migration = A2APgVectorMigration()
        report = migration.execute_migration()

        # レポート保存
        import json
        from datetime import datetime

        report_file = (
            PROJECT_ROOT
            / "logs"
            / f"pgvector_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n💾 Migration report saved to: {report_file}")

        # 結果表示
        print("\n📊 Migration Summary")
        print("-" * 40)
        print(
            f"Communications migrated: {report['statistics']['migrated_communications']}/{report['statistics']['total_communications']}"
        )
        print(
            f"Anomaly patterns migrated: {report['statistics']['migrated_anomalies']}/{report['statistics']['total_anomalies']}"
        )
        print(f"Embeddings generated: {report['statistics']['embeddings_generated']}")
        print(f"Errors: {len(report['statistics']['errors'])}")

        if report.get("recommendations"):
            print("\n💡 Recommendations")
            print("-" * 40)
            for rec in report["recommendations"]:
                print(f"- {rec}")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
