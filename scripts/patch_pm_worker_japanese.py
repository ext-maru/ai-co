#!/usr/bin/env python3
"""
PMWorker日本語化＆情報充実化パッチ
ResultWorkerへの送信情報を拡充し、日本語化も適用
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def patch_pm_worker():
    """PMWorkerを日本語化し、ResultWorkerへの送信情報を拡充"""

    pm_worker_path = PROJECT_ROOT / "workers" / "pm_worker.py"
    if not pm_worker_path.exists():
        print("❌ pm_worker.py が見つかりません")
        return False

    content = pm_worker_path.read_text(encoding="utf-8")

    # handle_task_completionメソッドを探して、ResultWorkerへの送信部分を改善
    new_handle_task_completion = '''    def handle_task_completion(self, ch, method, properties, body):
        """タスク完了時の自動Git処理（テスト実行付きGit Flow対応版）"""
        try:
            result = json.loads(body)
            task_id = result.get('task_id', 'unknown')
            status = result.get('status', 'unknown')

            logger.info(f"📋 タスク完了検知: {task_id} ({status})")

            # ResultWorkerへの転送用データを準備
            result_data = {
                'task_id': task_id,
                'task_type': result.get('task_type', 'general'),
                'status': status,
                'worker_id': result.get('worker_id', 'worker-1'),
                'rag_applied': result.get('rag_applied', False),
                'prompt': result.get('prompt', ''),
                'response': result.get('response', ''),
                'files_created': [],
                'output_file': result.get('output_file', ''),
                'duration': result.get('duration', 0.0),
                'error': result.get('error'),
                'error_trace': result.get('error_trace', '')
            }

            if status == "completed":
                # 新しいファイルが生成されたかチェック
                new_files = self.detect_new_files()
                result_data['files_created'] = new_files

                if new_files:
                    logger.info(f"📁 新規ファイル検出: {len(new_files)}件")
                    for file_path in new_files:
                        logger.info(f"  - {file_path}")

                    # Git Flow対応の処理
                    git_result_data = {
                        'task_id': task_id,
                        'files_created': new_files,
                        'files_updated': [],
                        'summary': result.get('prompt', 'Task completion')[:100]
                    }

                    # 作業ブランチ作成
                    branch_name = self.git_flow.create_feature_branch(task_id)
                    logger.info(f"🌿 作業ブランチ作成: {branch_name}")

                    # テスト実行（オプション）
                    test_passed = True
                    if self.test_before_commit:
                        test_passed = self._run_tests_for_files(new_files, task_id)

                    if test_passed:
                        # ファイルをコミット
                        commit_message = f"Task {task_id}: {git_result_data['summary']}"
                        if self.git_flow.commit_changes(commit_message, new_files):
                            logger.info(f"✅ {branch_name} にコミット成功")

                            # mainへPR作成またはマージ
                            if self.git_flow.create_pull_request(branch_name, f"feat: Task {task_id}", f"Auto-generated task completion"):
                                logger.info(f"🔀 main へのPR作成成功")

                                # 成功通知
                                if self.slack:
                                    self._send_success_notification(task_id, branch_name, new_files, test_passed)
                            else:
                                logger.warning(f"⚠️ develop へのマージ失敗")
                                if self.slack:
                                    self._send_merge_failure_notification(task_id, branch_name)
                        else:
                            logger.warning(f"⚠️ コミット失敗")
                    else:
                        logger.error(f"❌ テスト失敗のためコミットをスキップ")
                        # テスト失敗通知
                        if self.slack:
                            self._send_test_failure_notification(task_id, new_files)
                else:
                    logger.info(f"📁 新規ファイル未検出: {task_id}")

            # ResultWorkerへ転送（情報を拡充）
            self._send_to_result_worker(result_data)

        except Exception as e:
            logger.error(f"タスク完了処理エラー: {e}")
            traceback.print_exc()'''

    # _send_to_result_workerメソッドを追加
    send_to_result_method = '''
    def _send_to_result_worker(self, result_data):
        """ResultWorkerへタスク結果を送信"""
        try:
            # result_queueではなくai_resultsキューに送信
            self.channel.queue_declare(queue='ai_results', durable=True)

            self.channel.basic_publish(
                exchange='',
                routing_key='ai_results',
                body=json.dumps(result_data, ensure_ascii=False),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # 永続化
                )
            )

            logger.info(f"📤 ResultWorkerへ転送: {result_data['task_id']}")

        except Exception as e:
            logger.error(f"ResultWorker転送エラー: {e}")'''

    # handle_task_completionメソッドを置換
    start_marker = "    def handle_task_completion(self, ch, method, properties, body):"
    end_marker = "            traceback.print_exc()"

    if start_marker in content:
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker, start_idx) + len(end_marker)
        content = (
            content[:start_idx]
            + new_handle_task_completion
            + send_to_result_method
            + content[end_idx:]
        )

    # ログメッセージを日本語化
    replacements = [
        ("Git Flow対応PMWorker起動準備", "Git Flow対応PMWorker起動準備"),
        ("Git状態 - ブランチ:", "Git状態 - ブランチ:"),
        ("PM Worker起動完了", "PMワーカー起動完了"),
        ("監視中:", "監視中:"),
        ("PM Worker停止中...", "PMワーカー停止中..."),
        ("RabbitMQ接続成功", "RabbitMQ接続成功"),
        ("RabbitMQ接続失敗:", "RabbitMQ接続失敗:"),
        ("タスク完了検知:", "タスク完了検知:"),
        ("新規ファイル検出:", "新規ファイル検出:"),
        ("作業ブランチ作成:", "作業ブランチ作成:"),
        ("にコミット成功", "にコミット成功"),
        ("へのマージ成功", "へのマージ成功"),
        ("へのマージ失敗", "へのマージ失敗"),
        ("テスト失敗のためコミットをスキップ", "テスト失敗のためコミットをスキップ"),
        ("新規ファイル未検出:", "新規ファイル未検出:"),
        ("スケーリング監視開始", "スケーリング監視開始"),
        ("ヘルスチェック監視開始", "ヘルスチェック監視開始"),
        ("Git Flow自動処理（テスト実行付き）", "Git Flow自動処理（テスト実行付き）"),
        ("テスト実行: 有効", "テスト実行: 有効"),
        ("テスト実行: 無効", "テスト実行: 無効"),
    ]

    for old, new in replacements:
        content = content.replace(f'"{old}"', f'"{new}"')
        content = content.replace(f"'{old}'", f"'{new}'")
        content = content.replace(f'f"{old}', f'f"{new}')
        content = content.replace(f"f'{old}", f"f'{new}")

    # 保存
    pm_worker_path.write_text(content, encoding="utf-8")
    print("✅ PMWorkerを日本語化し、ResultWorkerへの送信情報を拡充しました")
    return True


def main():
    """メイン処理"""
    print("🌏 PMWorker日本語化＆情報拡充パッチを適用中...")

    if patch_pm_worker():
        print("\n✅ パッチ適用完了！")
        print("\n変更内容:")
        print("  - ResultWorkerへの送信情報を拡充")
        print("    - task_type, worker_id, rag_applied を追加")
        print("    - prompt, response を完全送信")
        print("  - ログメッセージを日本語化")
        print("  - ai_resultsキューへ正しく転送")
        print("\n次の手順:")
        print("  1. PMWorkerを再起動: ai-restart")
        print("  2. 新しいタスクを実行してSlack通知を確認")
    else:
        print("\n❌ パッチ適用に失敗しました")


if __name__ == "__main__":
    main()
