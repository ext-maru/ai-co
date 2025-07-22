#!/usr/bin/env python3
"""
Todo同期システムの統合テスト - 実際の動作確認
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestTodoSyncIntegration:
    """統合テスト - 実際のコマンド動作を確認"""
    
    def __init__(self):
        self.test_results = []
    
    def run_command(self, cmd: list, input_text: str = None) -> tuple:
        """コマンドを実行して結果を返す"""
        try:
            if input_text:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    input=input_text,
                    cwd=str(project_root)
                )
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(project_root)
                )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)
    
    def test_todo_sync_command_exists(self):
        """todo-syncコマンドが存在し実行可能であることを確認"""
        print("\n1. todo-syncコマンドの存在確認")
        
        todo_sync_path = project_root / "scripts" / "todo-sync"
        
        # ファイル存在確認
        if not todo_sync_path.exists():
            print("   ❌ FAIL: todo-syncコマンドが存在しません")
            return False
        
        # 実行権限確認
        if not os.access(todo_sync_path, os.X_OK):
            print("   ❌ FAIL: todo-syncに実行権限がありません")
            return False
        
        print("   ✅ PASS: todo-syncコマンドが存在し実行可能です")
        return True
    
    def test_todo_sync_shows_confirmation(self):
        """todo-syncが確認プロンプトを表示することを確認"""
        print("\n2. todo-sync確認プロンプトテスト")
        
        # 'n'を入力してキャンセル
        returncode, stdout, stderr = self.run_command(
            ["python3", "scripts/todo-sync"],
            input_text="n\n"
        )
        
        # 出力を確認
        if "同期しますか？" not in stdout:
            print("   ❌ FAIL: 確認プロンプトが表示されませんでした")
            print(f"   stdout: {stdout}")
            return False
        
        if "同期をキャンセルしました" not in stdout:
            print("   ❌ FAIL: キャンセルメッセージが表示されませんでした")
            return False
        
        print("   ✅ PASS: 確認プロンプトが正しく動作します")
        return True
    
    def test_todo_hook_notification(self):
        """TodoHookSystemが変更通知のみ行うことを確認"""
        print("\n3. TodoHookSystem通知テスト")
        
        test_script = """
import asyncio
import sys
sys.path.insert(0, '/home/aicompany/ai_co')

from libs.todo_hook_system import TodoHookSystem

async def test():
    # モックintegration
    class MockIntegration:
        def __init__(self):
            self.synced = False
            self.todos = []
        
        def update_todo_list(self, todos):
            self.todos = todos
        
        async def sync_both_ways(self):
            self.synced = True
    
    mock = MockIntegration()
    hook = TodoHookSystem(integration_module=mock)
    hook.last_todos = []
    
    # テストtodo
    todos = [{"id": "1", "content": "Test", "status": "pending", "priority": "high"}]
    hook.create_hook_file(todos)
    
    # 処理
    await hook._process_hook_file()
    
    # 結果確認
    print(f"update_todo_list called: {len(mock.todos) > 0}")
    print(f"sync_both_ways called: {mock.synced}")
    
    return mock.synced

result = asyncio.run(test())
sys.exit(0 if not result else 1)
"""
        
        # テストスクリプトを実行
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            temp_script = f.name
        
        try:
            returncode, stdout, stderr = self.run_command(["python3", temp_script])
            
            if returncode != 0:
                print("   ❌ FAIL: 自動同期が実行されました")
                print(f"   stdout: {stdout}")
                return False
            
            if "sync_both_ways called: False" not in stdout:
                print("   ❌ FAIL: sync_both_waysの状態が不明です")
                print(f"   stdout: {stdout}")
                return False
            
            print("   ✅ PASS: TodoHookSystemは通知のみ行います（自動同期なし）")
            return True
            
        finally:
            os.unlink(temp_script)
    
    def test_no_periodic_sync(self):
        """定期的な自動同期が動作しないことを確認"""
        print("\n4. 定期自動同期無効化テスト")
        
        test_script = """
import asyncio
import sys
sys.path.insert(0, '/home/aicompany/ai_co')

from libs.todo_tracker_integration import TodoTrackerIntegration

async def test():
    # モックトラッカー
    class MockTracker:
        def __init__(self):
            self.initialized = True
    
    integration = TodoTrackerIntegration(
        auto_sync=False,  # 明示的に無効
        sync_interval=1,  # 1秒間隔
        user_id="test"
    )
    
    # トラッカーを直接設定（初期化をスキップ）
    integration.tracker = MockTracker()
    
    # sync_both_waysをカウント
    sync_count = 0
    original_sync = integration.sync_both_ways
    
    async def mock_sync(*args, **kwargs):
        nonlocal sync_count
        sync_count += 1
        return await original_sync(*args, **kwargs)
    
    integration.sync_both_ways = mock_sync
    
    # 3秒待機
    await asyncio.sleep(3)
    
    print(f"sync_count: {sync_count}")
    print(f"_sync_task: {integration._sync_task}")
    print(f"_running: {integration._running}")
    
    return sync_count == 0

result = asyncio.run(test())
sys.exit(0 if result else 1)
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            temp_script = f.name
        
        try:
            returncode, stdout, stderr = self.run_command(["python3", temp_script])
            
            if returncode != 0:
                print("   ❌ FAIL: 定期同期が実行されました")
                print(f"   stdout: {stdout}")
                return False
            
            if "sync_count: 0" not in stdout:
                print("   ❌ FAIL: 同期カウントが0ではありません")
                print(f"   stdout: {stdout}")
                return False
            
            print("   ✅ PASS: 定期自動同期は無効です")
            return True
            
        finally:
            os.unlink(temp_script)
    
    def run_all_tests(self):
        """すべてのテストを実行"""
        print("🧪 Todo同期システム統合テスト開始")
        print("=" * 60)
        
        tests = [
            self.test_todo_sync_command_exists(),
            self.test_todo_sync_shows_confirmation(),
            self.test_todo_hook_notification(),
            self.test_no_periodic_sync()
        ]
        
        passed = sum(1 for t in tests if t)
        total = len(tests)
        
        print("\n" + "=" * 60)
        print(f"結果: {passed}/{total} テスト成功")
        
        if passed == total:
            print("✅ すべての統合テストが成功しました！")
            print("\n手動同期システムの実装:")
            print("- TodoWrite/TodoReadの変更は検出・通知のみ")
            print("- PostgreSQLへの同期は todo-sync コマンドで手動実行")
            print("- すべての自動同期は無効化済み")
        else:
            print(f"❌ {total - passed} 個のテストが失敗しました")
        
        return passed == total


def main():
    tester = TestTodoSyncIntegration()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()