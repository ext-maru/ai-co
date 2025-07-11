#!/usr/bin/env python3
"""
手動品質チェック用スクリプト
デーモンを使わずに一度だけ品質チェックを実行
"""
import asyncio
import sys
from pathlib import Path

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.quality_daemon import QualityEvolutionDaemon

async def main():
    """メイン関数"""
    daemon = QualityEvolutionDaemon()

    print("🔍 品質チェックを実行中...")
    await daemon.run_monitoring_cycle()
    print("✅ 品質チェック完了")

if __name__ == "__main__":
    asyncio.run(main())
