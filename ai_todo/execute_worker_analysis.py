import json
import subprocess
from datetime import datetime

# ワーカープロセスを確認
result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
workers = [line for line in result.stdout.split("\n") if "worker" in line.lower()]

print(f"アクティブなワーカー数: {len(workers)}")
for w in workers[:5]:
    print(f"  - {w[:80]}...")

# 分析結果を保存
analysis = {"worker_count": len(workers), "timestamp": str(datetime.now())}
with open("/tmp/worker_analysis.json", "w") as f:
    json.dump(analysis, f)

print(f"\n分析結果を /tmp/worker_analysis.json に保存しました")
