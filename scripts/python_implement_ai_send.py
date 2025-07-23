#!/usr/bin/env python3
"""
ai-send拡張の直接実装（Python版）
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルート
PROJECT_ROOT = Path("/home/aicompany/ai_co")
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))


def implement_ai_send_extension():
    print("🚀 ai-send拡張を直接実装します（Python版）")
    print("=" * 60)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 実装スクリプトの存在確認
    impl_script = PROJECT_ROOT / "implement_ai_send_extension.sh"
    if not impl_script.exists():
        print("❌ implement_ai_send_extension.sh が見つかりません")
        return False

    print("✅ 実装スクリプトが存在します")

    # 実行権限を付与
    try:
        subprocess.run(["chmod", "+x", str(impl_script)], check=True)
        print("✅ 実行権限を付与しました")
    except Exception as e:
        print(f"❌ 権限付与エラー: {e}")
        return False

    # スクリプトを実行
    print("\n📝 実装スクリプトを実行中...")
    try:
        result = subprocess.run(
            [str(impl_script)], capture_output=True, text=True, cwd=str(PROJECT_ROOT)
        )

        if result.returncode == 0:
            print("✅ 実装スクリプトが正常に完了しました")
            if result.stdout:
                print("\n実行結果（抜粋）:")
                print("-" * 40)
                lines = result.stdout.split("\n")
                for line in lines[:20]:  # 最初の20行
                    print(line)
                if len(lines) > 20:
                    print("...")
                print("-" * 40)
        else:
            print(f"❌ 実装スクリプトがエラーで終了しました (Exit Code: {result.returncode})")
            if result.stderr:
                print("\nエラー内容:")
                print(result.stderr[:500])
            return False

    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        return False

    # 結果確認
    print("\n🔍 実装結果の確認:")
    config_file = PROJECT_ROOT / "config" / "task_types.json"

    if config_file.exists():
        print("✅ タスクタイプ設定ファイル: 作成成功")
        try:
            with open(config_file) as f:
                data = json.load(f)
                task_types = data.get("task_types", {})
                print(f"\n📋 登録されたタスクタイプ ({len(task_types)}個):")

                # カテゴリ別に表示
                categories = {
                    "開発系": ["code", "test", "fix", "optimize"],
                    "管理系": ["deploy", "review", "docs", "backup"],
                    "分析系": ["analysis", "report", "monitor"],
                    "その他": ["general", "security"],
                }

                for category, types in categories.items():
                    print(f"\n  {category}:")
                    for task_type in types:
                        if task_type in task_types:
                            info = task_types[task_type]
                            print(
                                (
                                    f"f"    - {task_type:<10} : {info.get('description', 'N/A')} (優先度: "
                                    f"{info.get('default_priority', 5)})""
                                )
                            )

        except Exception as e:
            print(f"❌ 設定ファイル読み込みエラー: {e}")
            return False
    else:
        print("❌ タスクタイプ設定ファイル: 作成失敗")
        return False

    # Slack通知
    print("\n📢 Slack通知を送信中...")
    try:
        from libs.slack_notifier import SlackNotifier

        notifier = SlackNotifier()

        message = f"""🎉 ai-send拡張版の実装が完了しました！

📋 追加されたタスクタイプ:
• test - テスト作成・実行
• fix - バグ修正・問題解決
• deploy - デプロイ・リリース
• review - コードレビュー
• docs - ドキュメント生成
• optimize - パフォーマンス最適化
• security - セキュリティ監査
• monitor - システム監視
• backup - バックアップ作業

🚀 使用例:
```
ai-send 'テストを作成' test
ai-send 'バグを修正' fix --priority 9
ai-send --list-types
```

実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
実行方法: Python直接実行
"""

        notifier.send_message(message)
        print("✅ Slack通知を送信しました")

    except Exception as e:
        print(f"⚠️ Slack通知エラー: {e}")

    print("\n🎉 全ての処理が完了しました！")
    return True


if __name__ == "__main__":
    success = implement_ai_send_extension()
    sys.exit(0 if success else 1)
