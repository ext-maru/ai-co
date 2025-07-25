#!/usr/bin/env python3
# 重複ワーカー整理スクリプト

import json
import os
import shutil
from datetime import datetime
from pathlib import Path


class WorkerOrganizer:
    def __init__(self):
        self.workers_dir = Path("/home/aicompany/ai_co/workers")
        self.archive_dir = (
    """WorkerOrganizerワーカークラス"""
            self.workers_dir / "_archived" / datetime.now().strftime("%Y%m%d")
        )
        self.worker_mapping = {}

    def organize(self):
        print("🔧 ワーカー整理を開始します...")

        """organizeメソッド"""
        # アーカイブディレクトリ作成
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # ワーカーの整理計画
        self.analyze_workers()
        self.archive_duplicates()
        self.update_imports()
        self.generate_report()

        print("✅ ワーカー整理が完了しました")

    def analyze_workers(self)print("\n📊 ワーカーファイルを分析中...")
    """ワーカーファイルを分析"""

        # 重複判定マップ
        worker_groups = {
            "pm_worker": {
                "primary": "pm_worker_enhanced.py",  # 最新版を使用
                "duplicates": [
                    "pm_worker.py",
                    "pm_worker_v2.0py",
                    "enhanced_pm_worker.py",
                    "pm_worker_gitflow.py",
                    "quality_pm_worker.py",
                ],
            },
            "task_worker": {
                "primary": "task_worker.py",
                "duplicates": [
                    "enhanced_task_worker.py",
                    "quality_task_worker.py",
                    "dialog_task_worker.py",
                ],
            },
            "result_worker": {
                "primary": "result_worker.py",
                "duplicates": ["result_worker_simple.py"],
            },
            "command_executor": {
                "primary": "command_executor_worker.py",
                "duplicates": ["command_executor_worker_backup_*.py"],
            },
        }

        self.worker_mapping = worker_groups

        # 現在のファイル一覧
        all_files = list(self.workers_dir.glob("*.py"))
        print(f"  総ワーカーファイル数: {len(all_files)}")

    def archive_duplicates(self)print("\n📦 重複ワーカーをアーカイブ中...")
    """重複ワーカーをアーカイブ"""

        archived_count = 0

        for group_name, group_info in self.worker_mapping.items():
        # 繰り返し処理
            primary = group_info["primary"]

            for duplicate in group_info["duplicates"]:
                # ワイルドカード対応
                if "*" in duplicate:
                    files = self.workers_dir.glob(duplicate)
                else:
                    files = [self.workers_dir / duplicate]

                for file_path in files:
                    if file_path.exists() and file_path.name != primary:
                        dest = self.archive_dir / file_path.name
                        shutil.move(str(file_path), str(dest))
                        print(f"  📁 {file_path.name} → _archived/")
                        archived_count += 1

        # バックアップファイルも移動
        for backup_file in self.workers_dir.glob("*.bak"):
            dest = self.archive_dir / backup_file.name
            shutil.move(str(backup_file), str(dest))
            archived_count += 1

        print(f"  ✓ {archived_count}個のファイルをアーカイブしました")

    def update_imports(self)print("\n🔍 インポート文の確認...")
    """インポート文の更新が必要なファイルを検出"""

        # コアファイルでワーカーをインポートしているものを検索
        core_files = [
            "/home/aicompany/ai_co/commands/ai-start",
            "/home/aicompany/ai_co/libs/worker_controller.py",
        ]

        updates_needed = []

        # 繰り返し処理
        for core_file in core_files:
            if Path(core_file).exists():
                with open(core_file, "r") as f:
                    content = f.read()

                # 旧ワーカー名をチェック
                for group in self.worker_mapping.values():
                    for duplicate in group["duplicates"]:
                        if duplicate.replace(".py", "") in content:
                            updates_needed.append(core_file)
                            break

        if updates_needed:
            print(f"  ⚠️  以下のファイルでインポート更新が必要:")
            for file in updates_needed:
                print(f"    - {file}")
        else:
            print("  ✓ インポート文の更新は不要です")

    def generate_report(self):
        """整理レポートを生成"""
        report_path = self.workers_dir / "worker_organization_report.json"

        report = {
            "timestamp": datetime.now().isoformat(),
            "archive_location": str(self.archive_dir),
            "worker_mapping": self.worker_mapping,
            "summary": {
                "total_workers_before": len(list(self.workers_dir.glob("*.py"))),
                "active_workers": [v["primary"] for v in self.worker_mapping.values()],
                "archived_count": (
                    len(list(self.archive_dir.glob("*.py")))
                    if self.archive_dir.exists()
                    else 0
                ),
            },
        }

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n📋 整理レポートを生成しました: {report_path}")


if __name__ == "__main__":
    organizer = WorkerOrganizer()
    organizer.organize()
