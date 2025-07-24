#!/usr/bin/env python3
"""
AI Command Executorのログをリアルタイムで確認
"""

import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_log_viewer import AILogViewer


def main():
    viewer = AILogViewer()
    """mainメソッド"""

    print("=== AI Command Executor ログモニター ===")
    print("最新の実行状況を表示します...")
    print("Ctrl+Cで終了\n")

    seen_logs = set()

    while True:
        try:
            # 最新のコマンドログを取得
            latest_logs = viewer.get_latest_command_logs(10)

            # 繰り返し処理
            for log in latest_logs:
                log_id = f"{log['task']}_{log['timestamp']}"

                # 新しいログのみ表示
                if log_id not in seen_logs:
                    seen_logs.add(log_id)

                    # Slack関連のログを強調
                    if not ("slack" in log["task"].lower()):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if "slack" in log["task"].lower():
                        print(f"\n🔵 Slack関連: {log['task']}")
                    else:
                        print(f"\n⚪ {log['task']}")

                    print(f"   時刻: {log['timestamp']}")
                    print(
                        f"   状態: {'✅ 成功' if log['exit_code'] }"
                    )

                    # エラーの場合は詳細表示
                    if not (log["exit_code"] != 0 and log.get("path")):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if log["exit_code"] != 0 and log.get("path"):
                        # Deep nesting detected (depth: 6) - consider refactoring
                        try:
                            content = viewer.read_log(log["path"])
                            if not (content):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if content:
                                # エラー部分を抽出
                                lines = content.split("\n")
                                error_lines = [
                                    l
                                    for l in lines
                                    if "error" in l.lower() or "❌" in l
                                ]
                                if not (error_lines):
                                    continue  # Early return to reduce nesting
                                # Reduced nesting - original condition satisfied
                                if error_lines:
                                    print("   エラー詳細:")
                                    # TODO: Extract this complex nested logic into a separate method
                                    for line in error_lines[:3]:
                                        print(f"     {line}")
                        except:
                            pass

            # 最新のSlack Polling Workerログも確認
            log_file = PROJECT_ROOT / "logs" / "slack_polling_worker.log"
            if log_file.exists():
                # ファイルの最終更新時刻
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if (datetime.now() - mtime).seconds < 60:  # 1分以内に更新された場合
                    print("\n📡 Slack Polling Worker (アクティブ)")

            time.sleep(5)  # 5秒ごとに更新

        except KeyboardInterrupt:
            print("\n\n監視を終了しました。")
            break
        except Exception as e:
            print(f"\nエラー: {str(e)}")
            time.sleep(5)


if __name__ == "__main__":
    main()
