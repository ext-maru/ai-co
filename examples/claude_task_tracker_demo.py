#!/usr/bin/env python3
"""
Claude CLI Task Tracker統合の実装例
Claude CLIのワーカーやツールに組み込む例
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import random
import time

from libs.claude_task_tracker import ClaudeTaskTracker, track_claude_task


class ClaudeDevelopmentWorker:
    """Claude CLIの開発ワーカー例（Task Tracker統合版）"""

    def __init__(self):
        self.tracker = ClaudeTaskTracker()
        self.project_root = Path("/home/aicompany/ai_co")

    def execute_development_task(self, prompt: str):
        """開発タスクを実行（Task Tracker統合）"""
        # タスク開始
        task_id = self.tracker.start_development_task(prompt, "development")
        print(f"📋 タスク開始: {task_id}")

        try:
            # ステップ1: 要件分析
            self.tracker.update_progress("要件を分析中...")
            time.sleep(1)  # 実際の処理の代わり

            # ステップ2: ファイル生成
            files_to_create = self._analyze_required_files(prompt)
            self.tracker.update_progress(
                f"{len(files_to_create)}個のファイルを生成予定", files_to_create
            )

            created_files = []
            for file_path in files_to_create:
                # サブタスク作成
                subtask_id = self.tracker.create_subtask(
                    task_id, f"ファイル生成: {file_path}", f"Claude CLIによる自動生成"
                )

                # ファイル生成（シミュレーション）
                success = self._create_file(file_path)

                if success:
                    self.tracker.log_file_operation("create", file_path, True)
                    created_files.append(file_path)
                else:
                    self.tracker.log_file_operation("create", file_path, False, "生成エラー")

            # ステップ3: テスト実行
            self.tracker.update_progress("生成ファイルのテストを実行中...")
            test_passed = self._run_tests(created_files)

            if test_passed:
                self.tracker.update_progress("✅ テスト成功")
            else:
                self.tracker.update_progress("❌ テスト失敗")

            # タスク完了
            self.tracker.complete_task(success=True, files_created=created_files)

            print(f"✅ タスク完了: {task_id}")
            return created_files

        except Exception as e:
            # エラー時
            self.tracker.complete_task(success=False, error_message=str(e))
            print(f"❌ タスクエラー: {task_id} - {e}")
            raise

    def _analyze_required_files(self, prompt: str) -> list:
        """必要なファイルを分析（ダミー実装）"""
        # 実際にはClaudeが分析
        if "worker" in prompt.lower():
            return ["workers/new_worker.py", "tests/test_new_worker.py"]
        elif "library" in prompt.lower():
            return ["libs/new_library.py", "tests/test_new_library.py"]
        else:
            return ["output/generated_file.py"]

    def _create_file(self, file_path: str) -> bool:
        """ファイルを生成（ダミー実装）"""
        # 実際にはClaudeがコード生成
        time.sleep(0.5)
        return random.random() > 0.1  # 90%の確率で成功

    def _run_tests(self, files: list) -> bool:
        """テストを実行（ダミー実装）"""
        time.sleep(1)
        return random.random() > 0.2  # 80%の確率で成功


# デコレータを使った簡単な例
@track_claude_task("シンプルなユーティリティ関数を生成", "utility")
def create_utility_function():
    """Task Trackerデコレータの使用例"""
    print("ユーティリティ関数を生成中...")
    time.sleep(2)
    print("生成完了!")
    return "utils/new_util.py"


def demonstrate_integration():
    """統合デモンストレーション"""
    print("🤖 Claude CLI × Task Tracker 統合デモ")
    print("=" * 60)

    # 1. クラスベースの例
    worker = ClaudeDevelopmentWorker()

    # 複数のタスクを実行
    tasks = ["新しいワーカーを作成してください", "エラーハンドリングライブラリを実装してください", "テストカバレッジレポートを生成してください"]

    for task_prompt in tasks:
        print(f"\n📋 実行: {task_prompt}")
        try:
            worker.execute_development_task(task_prompt)
        except Exception as e:
            print(f"エラー: {e}")

        time.sleep(2)

    # 2. デコレータベースの例
    print("\n📋 デコレータ例:")
    create_utility_function()

    print("\n✅ デモ完了!")
    print("\n💡 Task Trackerで確認:")
    print("1. Webダッシュボード: http://localhost:5555")
    print("2. CLIコマンド: ./scripts/task list -a claude_cli")


def create_claude_cli_integration_script():
    """Claude CLI統合用のスクリプトを生成"""
    script_content = '''#!/usr/bin/env python3
"""
Claude CLI起動時にTask Tracker統合を有効化
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from libs.claude_task_tracker import get_tracker
import os

# 環境変数でTask Tracker統合を有効化
os.environ['CLAUDE_TASK_TRACKER_ENABLED'] = 'true'

# Trackerインスタンスを初期化
tracker = get_tracker()

print("📋 Task Tracker統合が有効になりました")
print("  - 全ての開発タスクが自動的に記録されます")
print("  - 進捗はWebダッシュボードで確認できます: http://localhost:5555")

# Claude CLIのメイン処理を継続...
'''

    script_path = PROJECT_ROOT / "scripts" / "enable_claude_tracker.py"
    with open(script_path, "w") as f:
        f.write(script_content)
    os.chmod(str(script_path), 0o755)
    print(f"\n✅ Claude CLI統合スクリプトを作成: {script_path}")


if __name__ == "__main__":
    # デモを実行
    demonstrate_integration()

    # 統合スクリプトを作成
    create_claude_cli_integration_script()
