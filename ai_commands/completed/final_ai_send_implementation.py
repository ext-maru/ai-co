#!/usr/bin/env python3
import sys
from pathlib import Path

# プロジェクトルートを追加
PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

# 最終実装スクリプトを実行
import subprocess

print("🚀 ai-send拡張の最終実装を開始...")
print("=" * 50)

# final_implement_ai_send.pyを実行
result = subprocess.run(
    [sys.executable, str(PROJECT_ROOT / "final_implement_ai_send.py")],
    capture_output=True,
    text=True,
    cwd=str(PROJECT_ROOT),
)

print("\n📊 実行結果:")
print("=" * 50)
if result.stdout:
    print(result.stdout)
if result.stderr:
    print("\n❌ エラー出力:")
    print(result.stderr)

print(f"\nExit Code: {result.returncode}")

if result.returncode == 0:
    print("\n✅ 実装が正常に完了しました！")
else:
    print("\n❌ 実装中にエラーが発生しました")
