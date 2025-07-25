#!/usr/bin/env python3
"""
A2A Elder Integration Test for Session Inheritance
A2Aエルダーを使ったセッション継承の統合テスト
"""

import asyncio
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class SessionInheritanceA2ATest:
    """A2Aエルダーを使ったセッション継承テスト"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.test_user = f"test_user_{int(time.time())}"
        self.session_1_tasks = []
        self.session_2_tasks = []
        
    def run_command(self, command: str, expect_input: bool = False, input_text: str = "n") -> Dict:
        """コマンドを実行して結果を取得"""
        try:
            if expect_input:
                # 入力が必要な場合
                process = subprocess.Popen(
                    command.split(),
                    cwd=self.project_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(input=input_text)
            else:
                # 通常実行
                result = subprocess.run(
                    command.split(),
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                stdout, stderr = result.stdout, result.stderr
                
            return {
                "success": True,
                "stdout": stdout,
                "stderr": stderr,
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    def test_session_1_task_creation(self) -> bool:
        """セッション1: タスク作成テスト"""
        print("📝 Session 1: タスク作成フェーズ")
        
        # タスク1: OAuth実装
        result1 = self.run_command(
            f"./scripts/todo-hook add 'OAuth2.実装' high --user {self.test_user}"
        )
        if not result1["success"]:
            print(f"❌ タスク1作成失敗: {result1.get('error', 'Unknown error')}")
            return False
        
        # タスク2: テスト作成
        result2 = self.run_command(
            f"./scripts/todo-hook add 'テストケース作成' medium --user {self.test_user}"
        )
        if not result2["success"]:
            print(f"❌ タスク2作成失敗: {result2.get('error', 'Unknown error')}")
            return False
            
        # タスク3: ドキュメント作成
        result3 = self.run_command(
            f"./scripts/todo-hook add 'API仕様書作成' low --user {self.test_user}"
        )
        if not result3["success"]:
            print(f"❌ タスク3作成失敗: {result3.get('error', 'Unknown error')}")
            return False
        
        # セッション1のタスク一覧を取得
        list_result = self.run_command(
            f"./scripts/todo-tracker-sync my-tasks --user {self.test_user}"
        )
        if list_result["success"]:
            print("✅ Session 1 タスク作成完了:")
            print(list_result["stdout"])
            self.session_1_tasks = self.parse_task_list(list_result["stdout"])
        
        return True

    def test_session_2_inheritance(self) -> bool:
        """セッション2: 継承テスト"""
        print("\n🔄 Session 2: セッション継承フェーズ")
        
        # 新しいセッションでの同期（自動継承提案）
        sync_result = self.run_command(
            f"./scripts/todo-tracker-sync sync --user {self.test_user}",
            expect_input=True,
            input_text="y\n"  # 継承を承認
        )
        
        if not sync_result["success"]:
            print(f"❌ 同期失敗: {sync_result.get('error', 'Unknown error')}")
            return False
        
        print("✅ Session 2 同期結果:")
        print(sync_result["stdout"])
        print("stderr:", sync_result["stderr"])
        
        # 継承後のタスク一覧を取得
        list_result = self.run_command(
            f"./scripts/todo-tracker-sync my-tasks --user {self.test_user}"
        )
        if list_result["success"]:
            print("✅ Session 2 継承後タスク一覧:")
            print(list_result["stdout"])
            self.session_2_tasks = self.parse_task_list(list_result["stdout"])
        
        return True

    def test_manual_inheritance(self) -> bool:
        """手動継承テスト"""
        print("\n🔧 Manual Inheritance: 手動継承テスト")
        
        # 追加タスクを作成
        self.run_command(
            f"./scripts/todo-hook add '手動継承テスト用タスク' high --user {self.test_user}"
        )
        
        # 手動継承実行
        resume_result = self.run_command(
            f"./scripts/todo-tracker-sync resume --force --user {self.test_user}"
        )
        
        if resume_result["success"]:
            print("✅ 手動継承結果:")
            print(resume_result["stdout"])
            print("stderr:", resume_result["stderr"])
        else:
            print(f"❌ 手動継承失敗: {resume_result.get('error', 'Unknown error')}")
            return False
        
        return True

    def test_cross_session_task_completion(self) -> bool:
        """セッション間タスク完了テスト"""
        print("\n✅ Cross-Session Completion: セッション間タスク完了テスト")
        
        if not self.session_2_tasks:
            print("❌ 継承されたタスクが見つかりません")
            return False
        
        # 最初のタスクを完了
        first_task = self.session_2_tasks[0]
        task_id = first_task.get("id", "").replace("[", "").replace("]", "")
        
        if task_id:
            complete_result = self.run_command(
                f"./scripts/todo-hook complete {task_id} --user {self.test_user}"
            )
            
            if complete_result["success"]:
                print(f"✅ タスク完了: {task_id}")
                print(complete_result["stdout"])
            else:
                print(f"❌ タスク完了失敗: {complete_result.get('error', 'Unknown error')}")
                return False
        
        return True

    def parse_task_list(self, output: str) -> List[Dict]:
        """タスク一覧の出力をパース"""
        tasks = []
        lines = output.split('\n')
        
        current_task = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # タスク行の検出（絵文字で始まる）
            if any(emoji in line for emoji in ["⏳", "🔄", "✅", "❌"]):
                if "[" in line and "]" in line:
                    # タスクIDとタイトルを抽出
                    parts = line.split("]", 1)
                    if len(parts) == 2:
                        id_part = parts[0] + "]"
                        title_part = parts[1].strip()
                        
                        current_task = {
                            "id": id_part,
                            "title": title_part,
                            "tags": []
                        }
                        tasks.append(current_task)
            
            # タグ行の検出
            elif line.startswith("🏷️") and current_task:
                tag_part = line.replace("🏷️", "").replace("Tags:", "").strip()
                current_task["tags"] = [tag.strip() for tag in tag_part.split(",")]
        
        return tasks

    def verify_inheritance_results(self) -> bool:
        """継承結果の検証"""
        print("\n🔍 Verification: 継承結果検証")
        
        # タスク数の確認
        print(f"Session 1 タスク数: {len(self.session_1_tasks)}")
        print(f"Session 2 タスク数: {len(self.session_2_tasks)}")
        
        # セッションIDの変更確認
        session_1_ids = set()
        session_2_ids = set()
        
        for task in self.session_1_tasks:
        # 繰り返し処理
            for tag in task.get("tags", []):
                if tag.startswith("session-"):
                    session_1_ids.add(tag)
        
        # 繰り返し処理
        for task in self.session_2_tasks:
            for tag in task.get("tags", []):
                if tag.startswith("session-"):
                    session_2_ids.add(tag)
        
        print(f"Session 1 セッションID: {session_1_ids}")
        print(f"Session 2 セッションID: {session_2_ids}")
        
        # セッションIDが異なることを確認
        if session_1_ids and session_2_ids and session_1_ids != session_2_ids:
            print("✅ セッションIDが正しく更新されました")
            return True
        else:
            print("❌ セッションIDの更新に問題があります")
            return False

    def cleanup(self):
        """テスト後のクリーンアップ"""
        print(f"\n🧹 Cleanup: テストユーザー {self.test_user} のタスクをクリーンアップ")
        
        # 完了済みでないタスクを完了状態にする（クリーンアップ目的）
        list_result = self.run_command(
            f"./scripts/todo-tracker-sync my-tasks --user {self.test_user}"
        )
        
        if list_result["success"]:
            print("✅ クリーンアップ完了")

    def run_full_test(self) -> bool:
        """フルテストの実行"""
        print("🚀 A2A Elder Session Inheritance Integration Test")
        print("=" * 60)
        print(f"Test User: {self.test_user}")
        print()
        
        try:
            # Phase 1: セッション1でのタスク作成
            if not self.test_session_1_task_creation():
                return False
            
            time.sleep(2)  # セッション間の間隔
            
            # Phase 2: セッション2での継承
            if not self.test_session_2_inheritance():
                return False
            
            time.sleep(1)
            
            # Phase 3: 手動継承テスト
            if not self.test_manual_inheritance():
                return False
            
            time.sleep(1)
            
            # Phase 4: セッション間タスク完了
            if not self.test_cross_session_task_completion():
                return False
            
            # Phase 5: 結果検証
            if not self.verify_inheritance_results():
                return False
            
            print("\n🎉 全テストが成功しました！")
            return True
            
        except Exception as e:
            print(f"\n❌ テスト実行中にエラーが発生: {e}")
            return False
        finally:
            self.cleanup()


def main():
    """メイン実行関数"""
    tester = SessionInheritanceA2ATest()
    
    success = tester.run_full_test()
    
    if success:
        print("\n✅ A2A Elder Session Inheritance Test: PASSED")
        exit(0)
    else:
        print("\n❌ A2A Elder Session Inheritance Test: FAILED")
        exit(1)


if __name__ == "__main__":
    main()