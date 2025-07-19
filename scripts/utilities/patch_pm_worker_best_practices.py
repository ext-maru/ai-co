#!/usr/bin/env python3
"""
PMWorkerをコミットメッセージベストプラクティス対応にパッチ
"""

import sys
from pathlib import Path


def patch_pm_worker():
    """PMWorkerにベストプラクティス対応を追加"""

    pm_worker_path = Path("/home/aicompany/ai_co/workers/pm_worker.py")

    if not pm_worker_path.exists():
        print("❌ pm_worker.py not found")
        return False

    # ファイルを読み込み
    content = pm_worker_path.read_text()

    # インポート追加
    if "from libs.github_flow_manager import GitHubFlowManager" not in content:
        # インポート部分を見つけて追加
        import_section = content.find("import logging")
        if import_section != -1:
            end_of_line = content.find("\n", import_section)
            new_import = "\nfrom libs.github_flow_manager import GitHubFlowManager"
            content = content[:end_of_line] + new_import + content[end_of_line:]

    # auto_commit_task_resultメソッドの更新を探す
    method_start = content.find("def _handle_file_placement(")
    if method_start != -1:
        # Git操作部分を見つける
        git_section = content.find("# Git操作", method_start)
        if git_section != -1:
            # 新しいGit操作コードに置き換え
            git_end = content.find("except Exception as e:", git_section)
            if git_end != -1:
                new_git_code = """# Git操作（ベストプラクティス対応）
                try:
                    git_manager = GitHubFlowManager()
                    if git_manager.auto_commit_task_result(
                        task_data['task_id'],
                        files_created,
                        task_data.get('summary', 'Automated file placement')
                    ):
                        self.logger.info("Git commit with best practices completed")
                """

                # 既存のGit操作コードを置き換え
                content = content[:git_section] + new_git_code + content[git_end:]

    # パッチ適用済みマーカーを追加
    if "# BEST_PRACTICES_PATCH_APPLIED" not in content:
        content = "# BEST_PRACTICES_PATCH_APPLIED\n" + content

    # バックアップを作成
    backup_path = pm_worker_path.with_suffix(".py.bak")
    pm_worker_path.rename(backup_path)

    # 新しい内容を書き込み
    pm_worker_path.write_text(content)

    print("✅ PMWorker patched successfully")
    print(f"📦 Backup saved to: {backup_path}")
    return True


if __name__ == "__main__":
    if patch_pm_worker():
        print("\n🎉 PMWorker now uses commit message best practices!")
        print("All future automated commits will follow Conventional Commits format.")
    else:
        print("\n❌ Failed to patch PMWorker")
