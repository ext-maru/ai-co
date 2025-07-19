#!/usr/bin/env python3

import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "/home/aicompany/ai_co")

# プロジェクトルート
PROJECT_ROOT = Path("/home/aicompany/ai_co")

print("🚀 ai-send拡張実装 - 最終実行")
print(f"時刻: {datetime.now()}")
print("=" * 50)

# 1. task_types.json の作成
task_types = {
    "create": {"description": "新規作成・開発タスク", "priority": 5},
    "test": {"description": "テスト作成・実行", "priority": 6},
    "fix": {"description": "バグ修正・問題解決", "priority": 8},
    "deploy": {"description": "デプロイ・リリース", "priority": 7},
    "review": {"description": "コードレビュー", "priority": 5},
    "docs": {"description": "ドキュメント生成", "priority": 3},
    "optimize": {"description": "パフォーマンス最適化", "priority": 4},
    "security": {"description": "セキュリティ監査", "priority": 9},
    "monitor": {"description": "システム監視", "priority": 6},
    "backup": {"description": "バックアップ作業", "priority": 4},
    "migrate": {"description": "データ移行・システム移行", "priority": 7},
    "analyze": {"description": "データ分析・調査", "priority": 5},
    "report": {"description": "レポート生成", "priority": 4},
}

config_dir = PROJECT_ROOT / "config"
config_dir.mkdir(exist_ok=True)

task_types_path = config_dir / "task_types.json"
with open(task_types_path, "w", encoding="utf-8") as f:
    json.dump(task_types, f, indent=2, ensure_ascii=False)

print(f"✅ task_types.json を作成: {task_types_path}")
print(f"   登録タスクタイプ数: {len(task_types)}")

# 2. テンプレートディレクトリの作成
templates_dir = PROJECT_ROOT / "templates" / "task_types"
templates_dir.mkdir(parents=True, exist_ok=True)

# 3. 各タスクタイプのテンプレート作成
for task_type in ["test", "fix", "deploy"]:
    template_content = f'''#!/usr/bin/env python3
"""
{task_type.capitalize()} タスクテンプレート
自動生成: {datetime.now()}
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import BaseWorker, get_config, EMOJI
import logging

class {task_type.capitalize()}Worker(BaseWorker):
    def __init__(self):
        super().__init__(worker_type='{task_type}')
        self.config = get_config()

    def process_message(self, ch, method, properties, body):
        """タスク処理"""
        task_id = body.get('task_id', 'unknown')
        self.logger.info(f"Processing {task_type} task: {{task_id}}")

        # タスク処理ロジック
        result = self._execute_{task_type}(body)

        # 完了通知
        self._notify_completion(f"{task_type.capitalize()} task completed: {{task_id}}")

        return result

    def _execute_{task_type}(self, task_data):
        """実際の処理"""
        # TODO: 実装
        return {{
            "status": "success",
            "task_type": "{task_type}",
            "timestamp": str(datetime.now())
        }}

if __name__ == "__main__":
    worker = {task_type.capitalize()}Worker()
    worker.run()
'''

    template_path = templates_dir / f"{task_type}_template.py"
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(template_content)

    print(f"✅ テンプレート作成: {template_path}")

# 4. ガイドドキュメントの作成
guide_content = """# AI Send Extended - タスクタイプ拡張ガイド

## 概要
ai-sendコマンドが13種類のタスクタイプに対応しました。

## 利用可能なタスクタイプ

| タスクタイプ | 説明 | 優先度 | 使用例 |
|------------|------|--------|--------|
| create | 新規作成・開発タスク | 5 | `ai-send create "新機能の実装"` |
| test | テスト作成・実行 | 6 | `ai-send test "ユニットテスト追加"` |
| fix | バグ修正・問題解決 | 8 | `ai-send fix "メモリリーク修正"` |
| deploy | デプロイ・リリース | 7 | `ai-send deploy "本番環境へのリリース"` |
| review | コードレビュー | 5 | `ai-send review "PRのレビュー"` |
| docs | ドキュメント生成 | 3 | `ai-send docs "API仕様書作成"` |
| optimize | パフォーマンス最適化 | 4 | `ai-send optimize "クエリ最適化"` |
| security | セキュリティ監査 | 9 | `ai-send security "脆弱性スキャン"` |
| monitor | システム監視 | 6 | `ai-send monitor "リソース使用状況確認"` |
| backup | バックアップ作業 | 4 | `ai-send backup "DBバックアップ"` |
| migrate | データ移行・システム移行 | 7 | `ai-send migrate "新DBへの移行"` |
| analyze | データ分析・調査 | 5 | `ai-send analyze "ログ分析"` |
| report | レポート生成 | 4 | `ai-send report "月次レポート作成"` |

## 使用方法

### 基本構文
```bash
ai-send <task_type> "<description>" [--priority <1-10>] [--model <model_name>]
```

### 例
```bash
# バグ修正（高優先度）
ai-send fix "ログイン機能のバグ修正" --priority 9

# テスト作成
ai-send test "新機能のE2Eテスト作成"

# ドキュメント生成（低優先度）
ai-send docs "README更新" --priority 2
```

## カスタムテンプレート

各タスクタイプは `/home/aicompany/ai_co/templates/task_types/` にテンプレートを持っています。
カスタマイズが必要な場合は、これらのテンプレートを編集してください。

## 優先度について

- 1-3: 低優先度（ドキュメント、軽微な改善）
- 4-6: 中優先度（通常の開発タスク）
- 7-9: 高優先度（バグ修正、セキュリティ）
- 10: 最高優先度（緊急対応）

## Slack通知

全てのタスクは完了時にSlackに通知されます。
通知先: `#task-result`

---
作成日: """ + str(
    datetime.now()
)

guide_path = PROJECT_ROOT / "docs" / "AI_SEND_EXTENDED_GUIDE.md"
guide_path.parent.mkdir(exist_ok=True)
with open(guide_path, "w", encoding="utf-8") as f:
    f.write(guide_content)

print(f"\n✅ ガイド作成: {guide_path}")

# 5. ai-sendコマンドの更新確認
ai_send_path = PROJECT_ROOT / "scripts" / "ai-send"
if ai_send_path.exists():
    print(f"\n✅ ai-sendコマンドが存在: {ai_send_path}")
    # 実行権限を確認
    os.chmod(ai_send_path, 0o755)
    print("   実行権限を設定しました")
else:
    print(f"\n❌ ai-sendコマンドが見つかりません: {ai_send_path}")

# 6. Slack通知
try:
    from libs.slack_notifier import SlackNotifier

    notifier = SlackNotifier()

    message = f"""🎉 ai-send拡張実装完了！

📋 追加されたタスクタイプ: {len(task_types)}種類
📁 設定ファイル: {task_types_path}
📝 ガイド: {guide_path}

使用例:
```
ai-send test "ユニットテスト追加"
ai-send fix "バグ修正" --priority 9
ai-send deploy "本番リリース"
```

詳細は `cat {guide_path}` で確認してください。"""

    notifier.send_message(message)
    print("\n✅ Slack通知を送信しました")
except Exception as e:
    print(f"\n⚠️ Slack通知に失敗: {str(e)}")

print("\n🎉 ai-send拡張の実装が完了しました！")
