#!/usr/bin/env python3
"""
エルダー評議会 - カバレッジ60%達成実行スクリプト
"""
import subprocess
import os
from pathlib import Path

# 環境設定
os.environ['PROJECT_ROOT'] = str(Path.cwd())
os.environ['TESTING'] = 'true'

print("🏛️ エルダー評議会 - カバレッジ向上作戦開始")
print("="*80)

# Phase 1: 基本テスト実行
print("\n📊 Phase 1: 基本テスト実行 (目標: 10%)")
cmd1 = [
    "python3", "-m", "pytest",
    "tests/unit/core/",
    "tests/unit/test_simple*.py",
    "tests/unit/test_sample.py",
    "--cov=core", "--cov=libs", "--cov=workers",
    "--cov-report=term",
    "--tb=short",
    "-v"
]
subprocess.run(cmd1)

# Phase 2: 修復済みテスト実行
print("\n📊 Phase 2: 修復済みテスト実行 (目標: 30%)")
cmd2 = [
    "python3", "-m", "pytest",
    "tests/unit/",
    "-k", "test_module_import or test_basic_functionality or test_initialization",
    "--cov=core", "--cov=libs", "--cov=workers",
    "--cov-report=term",
    "--cov-report=json",
    "--maxfail=100",
    "-x"
]
subprocess.run(cmd2)

# 最終結果表示
print("\n📊 最終カバレッジ結果")
if Path("coverage.json").exists():
    import json
    with open("coverage.json") as f:
        data = json.load(f)
        coverage = data['totals']['percent_covered']
        print(f"✨ 達成カバレッジ: {coverage:.1f}%")
        if coverage >= 60:
            print("🎉 目標達成！")
        else:
            print(f"📈 目標まで: {60 - coverage:.1f}%")
