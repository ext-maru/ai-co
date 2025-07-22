#!/usr/bin/env python3
"""
手動Todo同期システムの厳密なテスト
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.todo_hook_system import TodoHookSystem
from libs.todo_tracker_integration import TodoTrackerIntegration


class TestManualTodoSync:
    """手動同期システムの統合テスト"""
    
    def __init__(self):
        self.test_results = []
        self.failed_tests = []
    
    def add_result(self, test_name: str, passed: bool, message: str = ""):
        """テスト結果を記録"""
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
        if not passed:
            self.failed_tests.append(test_name)
    
    async def test_no_auto_sync_on_todo_change(self):
        """TodoWrite変更時に自動同期されないことを確認"""
        test_name = "test_no_auto_sync_on_todo_change"
        
        try:
            # モックの統合オブジェクト
            mock_integration = MagicMock()
            mock_integration.update_todo_list = MagicMock()
            mock_integration.sync_both_ways = AsyncMock()
            
            # TodoHookSystemを初期化
            hook_system = TodoHookSystem(integration_module=mock_integration)
            
            # last_todosを初期化して変更を検出できるようにする
            hook_system.last_todos = []
            
            # テスト用のフックファイルを作成
            test_todos = [
                {"id": "1", "content": "Test todo", "status": "pending", "priority": "high"}
            ]
            hook_system.create_hook_file(test_todos)
            
            # フックファイルを処理
            await hook_system._process_hook_file()
            
            # デバッグ: 実際に抽出されたtodosを確認
            if not mock_integration.update_todo_list.called:
                # フックファイルの内容を確認
                if hook_system.hook_file.exists():
                    with open(hook_system.hook_file, 'r') as f:
                        content = f.read()
                    extracted = hook_system._extract_todos_from_content(content)
                    raise AssertionError(f"update_todo_list not called. File content: {content}, Extracted: {extracted}")
            
            # update_todo_listは呼ばれるべき
            mock_integration.update_todo_list.assert_called_once()
            
            # sync_both_waysは呼ばれてはいけない
            mock_integration.sync_both_ways.assert_not_called()
            
            self.add_result(test_name, True, "自動同期が正しく無効化されています")
            
        except Exception as e:
            self.add_result(test_name, False, f"エラー: {str(e)}")
    
    async def test_default_auto_sync_disabled(self):
        """TodoTrackerIntegrationのデフォルトauto_syncがFalseであることを確認"""
        test_name = "test_default_auto_sync_disabled"
        
        try:
            # モックのトラッカーを作成
            with patch('libs.todo_tracker_integration.create_postgres_task_tracker') as mock_create:
                mock_tracker = AsyncMock()
                mock_create.return_value = mock_tracker
                
                # auto_syncパラメータなしで初期化
                integration = TodoTrackerIntegration(user_id="test_user")
                
                # auto_syncがFalseであることを確認
                assert integration.auto_sync == False, "デフォルトのauto_syncがTrueになっています"
                
                await integration.initialize()
                
                # 自動同期タスクが起動していないことを確認
                assert integration._sync_task is None, "自動同期タスクが起動しています"
                assert integration._running == False, "_runningフラグがTrueです"
                
                self.add_result(test_name, True, "デフォルトで自動同期が無効です")
                
        except Exception as e:
            self.add_result(test_name, False, f"エラー: {str(e)}")
    
    async def test_update_task_no_auto_sync(self):
        """update_task_with_todo_syncでステータス更新時に自動同期されないことを確認"""
        test_name = "test_update_task_no_auto_sync"
        
        try:
            with patch('libs.todo_tracker_integration.create_postgres_task_tracker') as mock_create:
                mock_tracker = AsyncMock()
                mock_tracker.update_task = AsyncMock()
                mock_create.return_value = mock_tracker
                
                integration = TodoTrackerIntegration(user_id="test_user")
                await integration.initialize()
                
                # sync_both_waysをモック
                integration.sync_both_ways = AsyncMock()
                
                # ステータス更新
                await integration.update_task_with_todo_sync(
                    task_id="test-123",
                    status="completed"
                )
                
                # update_taskは呼ばれるべき
                mock_tracker.update_task.assert_called_once()
                
                # sync_both_waysは呼ばれてはいけない
                integration.sync_both_ways.assert_not_called()
                
                self.add_result(test_name, True, "タスク更新時の自動同期が無効です")
                
        except Exception as e:
            self.add_result(test_name, False, f"エラー: {str(e)}")
    
    async def test_inherit_tasks_no_auto_sync(self):
        """inherit_pending_tasksで自動同期されないことを確認"""
        test_name = "test_inherit_tasks_no_auto_sync"
        
        try:
            with patch('libs.todo_tracker_integration.create_postgres_task_tracker') as mock_create:
                mock_tracker = AsyncMock()
                mock_tracker.list_tasks = AsyncMock(return_value=[
                    {
                        "task_id": "test-123",
                        "title": "Test task",
                        "status": "pending",
                        "tags": ["session-old"],
                        "metadata": {"session_id": "session-old"}
                    }
                ])
                mock_tracker.update_task = AsyncMock()
                mock_create.return_value = mock_tracker
                
                integration = TodoTrackerIntegration(user_id="test_user")
                await integration.initialize()
                
                # sync_both_waysをモック
                integration.sync_both_ways = AsyncMock()
                
                # タスクを引き継ぐ（確認なし）
                inherited_count = await integration.inherit_pending_tasks(confirm_prompt=False)
                
                # タスクが引き継がれたことを確認
                assert inherited_count == 1, f"引き継ぎ数が期待値と異なります: {inherited_count}"
                
                # sync_both_waysは呼ばれてはいけない
                integration.sync_both_ways.assert_not_called()
                
                self.add_result(test_name, True, "タスク引き継ぎ時の自動同期が無効です")
                
        except Exception as e:
            self.add_result(test_name, False, f"エラー: {str(e)}")
    
    async def test_todo_sync_command_confirmation(self):
        """todo-syncコマンドが確認プロンプトを表示することを確認"""
        test_name = "test_todo_sync_command_confirmation"
        
        try:
            # todo-syncスクリプトの存在確認
            todo_sync_path = project_root / "scripts" / "todo-sync"
            assert todo_sync_path.exists(), "todo-syncコマンドが存在しません"
            
            # 実行可能であることを確認
            assert os.access(todo_sync_path, os.X_OK), "todo-syncが実行可能ではありません"
            
            # スクリプトの内容を確認
            with open(todo_sync_path, 'r') as f:
                content = f.read()
                
            # 確認プロンプトが含まれていることを確認
            assert "同期しますか？" in content, "確認プロンプトが見つかりません"
            assert "[Y/n]" in content, "Y/n選択肢が見つかりません"
            assert "choice != 'n'" in content, "選択処理が見つかりません"
            
            self.add_result(test_name, True, "todo-syncコマンドに確認プロンプトがあります")
            
        except Exception as e:
            self.add_result(test_name, False, f"エラー: {str(e)}")
    
    async def test_hook_file_notification_only(self):
        """フックファイル処理時に通知のみ表示されることを確認"""
        test_name = "test_hook_file_notification_only"
        
        try:
            # 標準出力をキャプチャ
            from io import StringIO
            import contextlib
            
            output = StringIO()
            
            mock_integration = MagicMock()
            mock_integration.update_todo_list = MagicMock()
            
            hook_system = TodoHookSystem(integration_module=mock_integration)
            
            # last_todosを初期化
            hook_system.last_todos = []
            
            # テスト用のフックファイル
            test_todos = [
                {"id": "1", "content": "Test", "status": "pending", "priority": "medium"}
            ]
            hook_system.create_hook_file(test_todos)
            
            # 標準出力をキャプチャして処理
            with contextlib.redirect_stdout(output):
                await hook_system._process_hook_file()
            
            output_text = output.getvalue()
            
            # 通知メッセージが含まれていることを確認
            assert "Todoリストが変更されました" in output_text, "変更通知が表示されていません"
            assert "todo-sync" in output_text, "todo-syncコマンドの案内がありません"
            
            self.add_result(test_name, True, "フック処理で通知のみ表示されます")
            
        except Exception as e:
            self.add_result(test_name, False, f"エラー: {str(e)}")
    
    async def test_no_auto_sync_in_5min_interval(self):
        """5分間隔の自動同期が実行されないことを確認"""
        test_name = "test_no_auto_sync_in_5min_interval"
        
        try:
            with patch('libs.todo_tracker_integration.create_postgres_task_tracker') as mock_create:
                mock_tracker = AsyncMock()
                mock_create.return_value = mock_tracker
                
                # auto_sync=Falseで初期化
                integration = TodoTrackerIntegration(
                    auto_sync=False,
                    sync_interval=1,  # テスト用に1秒に設定
                    user_id="test_user"
                )
                await integration.initialize()
                
                # sync_both_waysをモック
                integration.sync_both_ways = AsyncMock()
                
                # 2秒待機
                await asyncio.sleep(2)
                
                # sync_both_waysが呼ばれていないことを確認
                integration.sync_both_ways.assert_not_called()
                
                # 自動同期タスクが起動していないことを確認
                assert integration._sync_task is None, "自動同期タスクが起動しています"
                
                self.add_result(test_name, True, "定期自動同期が無効です")
                
        except Exception as e:
            self.add_result(test_name, False, f"エラー: {str(e)}")
    
    def print_results(self):
        """テスト結果を表示"""
        print("\n" + "=" * 60)
        print("🧪 手動Todo同期システム 厳密テスト結果")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["passed"])
        
        for result in self.test_results:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"\n{status} {result['test']}")
            if result["message"]:
                print(f"   {result['message']}")
        
        print("\n" + "-" * 60)
        print(f"総テスト数: {total_tests}")
        print(f"成功: {passed_tests}")
        print(f"失敗: {len(self.failed_tests)}")
        
        if self.failed_tests:
            print(f"\n❌ 失敗したテスト:")
            for test in self.failed_tests:
                print(f"   - {test}")
        else:
            print(f"\n✅ すべてのテストが成功しました！")
        
        print("=" * 60)
        
        return len(self.failed_tests) == 0


async def main():
    """メインテスト実行"""
    tester = TestManualTodoSync()
    
    # すべてのテストを実行
    tests = [
        tester.test_no_auto_sync_on_todo_change,
        tester.test_default_auto_sync_disabled,
        tester.test_update_task_no_auto_sync,
        tester.test_inherit_tasks_no_auto_sync,
        tester.test_todo_sync_command_confirmation,
        tester.test_hook_file_notification_only,
        tester.test_no_auto_sync_in_5min_interval,
    ]
    
    print("🧪 手動Todo同期システムの厳密テストを開始...")
    
    for test in tests:
        await test()
    
    # 結果を表示
    all_passed = tester.print_results()
    
    # 終了コード
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())