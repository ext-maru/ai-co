#!/usr/bin/env python3
"""
エルダーズギルド プロジェクト自動削除スクリプト
7日間の保護期間が過ぎたプロジェクトを自動削除
"""

import json
import logging
import os
import shutil
from datetime import date, datetime

# ログ設定
logging.basicConfig(
    filename="/home/aicompany/ai_co/logs/project_deletions.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

BASE_DIR = "/home/aicompany/ai_co"
DELETION_DIR = os.path.join(BASE_DIR, "projects_to_delete")
SCHEDULE_FILE = os.path.join(DELETION_DIR, "deletion_schedule.json")


def load_schedule():
    """削除スケジュールを読み込む"""
    if not os.path.exists(SCHEDULE_FILE):
        return {"projects": []}

    with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_schedule(schedule):
    """削除スケジュールを保存"""
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)


def delete_expired_projects():
    """期限切れプロジェクトを削除"""
    schedule = load_schedule()
    today = date.today()
    remaining_projects = []

    for project in schedule["projects"]:
        deletion_date = datetime.strptime(project["deletion_date"], "%Y-%m-%d").date()

        if deletion_date <= today:
            # 削除実行
            project_path = os.path.join(
                DELETION_DIR, f"{project['deletion_date']}_{project['name']}"
            )

            if os.path.exists(project_path):
                try:
                    shutil.rmtree(project_path)
                    logging.info(
                        f"削除完了: {project['name']} (理由: {project['reason']})"
                    )

                    # ナレッジベースに記録
                    record_deletion(project)

                except Exception as e:
                    logging.error(f"削除失敗: {project['name']} - {str(e)}")
                    remaining_projects.append(project)
            else:
                logging.warning(f"プロジェクトが見つかりません: {project_path}")
        else:
            # まだ削除期限前
            remaining_projects.append(project)

    # スケジュール更新
    schedule["projects"] = remaining_projects
    save_schedule(schedule)


def record_deletion(project):
    """削除をナレッジベースに記録"""
    kb_dir = os.path.join(BASE_DIR, "knowledge_base/project_lifecycle/deletions")
    os.makedirs(kb_dir, exist_ok=True)

    record_file = os.path.join(
        kb_dir, f"{datetime.now().strftime('%Y%m%d')}_{project['name']}.json"
    )

    with open(record_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                **project,
                "deleted_at": datetime.now().isoformat(),
                "deleted_by": "elders_project_cleanup.py",
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def main():
    """メイン処理"""
    logging.info("エルダーズギルド プロジェクト削除処理開始")

    try:
        delete_expired_projects()
        logging.info("削除処理完了")
    except Exception as e:
        logging.error(f"削除処理エラー: {str(e)}")


if __name__ == "__main__":
    main()
