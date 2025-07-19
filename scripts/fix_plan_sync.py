#!/usr/bin/env python3
"""Plan Projects Sync の aiofiles 依存を削除するスクリプト"""

import re

# ファイルパス
file_path = "/home/aicompany/ai_co/libs/task_elder/plan_projects_sync.py"

# ファイルを読み込み
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# aiofiles関連のインポートを削除/変更
content = re.sub(r"import aiofiles\n", "", content)
content = re.sub(
    r"try:\n    import aiofiles\.os\nexcept ImportError:\n    # aiofiles\.osが利用できない場合は標準のosを使用\n    import os as aiofiles_os\n",
    "import os\n",
    content,
)

# async with aiofiles.open を通常のopen に変更
content = re.sub(
    r"async with aiofiles\.open\((.*?)\) as f:\n(\s+)content = await f\.read\(\)",
    r"with open(\1) as f:\n\2content = f.read()",
    content,
)

# await aiofiles.os.stat を os.stat に変更
content = re.sub(
    r"try:\n\s+stat = await aiofiles\.os\.stat\(plan_path\)\n\s+except:\n\s+# aiofiles\.osが使えない場合は標準のosを使用\n\s+import os\n\s+stat = os\.stat\(plan_path\)",
    r"stat = os.stat(plan_path)",
    content,
)

# ファイルを書き戻し
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ aiofiles依存を削除しました")
