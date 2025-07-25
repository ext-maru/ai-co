#!/usr/bin/env python3
"""
⚡ Optimized Manual Quality Check
High-performance quality analysis for immediate feedback
"""
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.optimized_quality_daemon import run_optimized_quality_check

async def main():
    """Run optimized quality check"""
    print("🚀 Running optimized quality check...")
    await run_optimized_quality_check()
    print("✅ Optimized quality check completed")

if __name__ == "__main__":
    asyncio.run(main())
