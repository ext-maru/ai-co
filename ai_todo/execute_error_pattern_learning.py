import re
from pathlib import Path
from collections import Counter
import json
from datetime import datetime

log_dir = Path("/home/aicompany/ai_co/logs")
error_patterns = Counter()

# 最近のログファイルからエラーを抽出
for log_file in sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime)[-10:]:
    try:
        with open(log_file, 'r', errors='ignore') as f:
            content = f.read()
            errors = re.findall(r'ERROR.*?(?=\n|$)', content)
            for error in errors:
                # エラータイプを抽出
                if "ModuleNotFoundError" in error:
                    error_patterns["ModuleNotFoundError"] += 1
                elif "FileNotFoundError" in error:
                    error_patterns["FileNotFoundError"] += 1
                elif "PermissionError" in error:
                    error_patterns["PermissionError"] += 1
                else:
                    error_patterns["Other"] += 1
    except:
        pass

print("エラーパターン分析結果:")
for pattern, count in error_patterns.most_common():
    print(f"  {pattern}: {count}回")

# 学習結果を知識ベースに保存
kb_dir = Path("/home/aicompany/ai_co/knowledge_base/ai_learning")
kb_dir.mkdir(parents=True, exist_ok=True)

learning_entry = {
    "timestamp": datetime.now().isoformat(),
    "type": "error_analysis",
    "patterns": dict(error_patterns),
    "recommendation": "Most common errors should be auto-fixed"
}

with open(kb_dir / "error_patterns.jsonl", "a") as f:
    f.write(json.dumps(learning_entry) + "\n")
    
print(f"\n学習結果を {kb_dir}/error_patterns.jsonl に保存しました")