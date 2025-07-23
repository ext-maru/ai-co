#!/usr/bin/env python3
"""
📊 プロジェクトボード管理システム
Project Board Management System

GitHub Projectsとの統合を管理し、計画書からプロジェクトボードを自動生成・更新する
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from task_elder.github_projects_client import (
    GitHubProjectsClient,
    ProjectBoard,
    ProjectItem,
    ProjectItemPriority,
    ProjectItemStatus,
)
from task_elder.task_breakdown_engine import TaskBreakdown, TaskBreakdownEngine

logger = logging.getLogger(__name__)


class BoardTemplate(Enum):
    """ボードテンプレート"""

    KANBAN = "kanban"
    SCRUM = "scrum"
    CUSTOM = "custom"


@dataclass
class BoardConfig:
    """ボード設定"""

    template: BoardTemplate = BoardTemplate.KANBAN
    columns: List[str] = None
    auto_assign: bool = True
    priority_labels: bool = True
    progress_tracking: bool = True

    def __post_init__(self):
        if self.columns is None:
            if self.template == BoardTemplate.KANBAN:
                self.columns = ["📋 Todo", "🔄 In Progress", "👀 Review", "✅ Done"]
            elif self.template == BoardTemplate.SCRUM:
                self.columns = ["📝 Backlog", "🚀 Sprint", "🔄 In Progress", "✅ Done"]
            else:
                self.columns = ["Todo", "In Progress", "Done"]


@dataclass
class SyncMapping:
    """同期マッピング"""

    plan_file: str
    project_id: str
    board_config: BoardConfig
    last_sync: Optional[str] = None
    sync_count: int = 0

    def __post_init__(self):
        if not self.last_sync:
            self.last_sync = datetime.now().isoformat()


class ProjectBoardManager:
    """プロジェクトボード管理システム"""

    def __init__(self, github_token: Optional[str] = None):
        self.base_path = Path("/home/aicompany/ai_co")
        self.data_path = self.base_path / "data" / "project_boards"
        self.data_path.mkdir(parents=True, exist_ok=True)

        # GitHub Projects クライアント
        self.github_client = GitHubProjectsClient(token=github_token)

        # タスク分解エンジン
        self.task_engine = TaskBreakdownEngine()

        # 同期マッピング
        self.sync_mappings = self._load_sync_mappings()

        # 設定
        self.config_file = self.data_path / "board_manager_config.json"
        self.config = self._load_config()

        # 統計
        self.stats = {
            "total_boards": 0,
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "last_sync": None,
        }

    def _load_sync_mappings(self) -> Dict[str, SyncMapping]:
        """同期マッピングを読み込み"""
        mapping_file = self.data_path / "sync_mappings.json"
        if not mapping_file.exists():
            return {}

        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                mappings = {}
                for key, value in data.items():
                    config_data = value.get("board_config", {})
                    board_config = BoardConfig(
                        template=BoardTemplate(config_data.get("template", "kanban")),
                        columns=config_data.get("columns"),
                        auto_assign=config_data.get("auto_assign", True),
                        priority_labels=config_data.get("priority_labels", True),
                        progress_tracking=config_data.get("progress_tracking", True),
                    )

                    mapping = SyncMapping(
                        plan_file=value["plan_file"],
                        project_id=value["project_id"],
                        board_config=board_config,
                        last_sync=value.get("last_sync"),
                        sync_count=value.get("sync_count", 0),
                    )
                    mappings[key] = mapping
                return mappings
        except Exception as e:
            logger.error(f"同期マッピング読み込みエラー: {e}")
            return {}

    def _save_sync_mappings(self):
        """同期マッピングを保存"""
        mapping_file = self.data_path / "sync_mappings.json"
        try:
            data = {}
            for key, mapping in self.sync_mappings.items():
                data[key] = {
                    "plan_file": mapping.plan_file,
                    "project_id": mapping.project_id,
                    "board_config": {
                        "template": mapping.board_config.template.value,
                        "columns": mapping.board_config.columns,
                        "auto_assign": mapping.board_config.auto_assign,
                        "priority_labels": mapping.board_config.priority_labels,
                        "progress_tracking": mapping.board_config.progress_tracking,
                    },
                    "last_sync": mapping.last_sync,
                    "sync_count": mapping.sync_count,
                }

            with open(mapping_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"同期マッピング保存エラー: {e}")

    def _load_config(self) -> Dict:
        """設定を読み込み"""
        if not self.config_file.exists():
            default_config = {
                "default_board_template": "kanban",
                "auto_create_labels": True,
                "sync_interval_hours": 24,
                "max_items_per_sync": 100,
                "enable_progress_tracking": True,
                "notification_settings": {
                    "sync_completion": True,
                    "sync_errors": True,
                    "board_creation": True,
                },
            }
            self._save_config(default_config)
            return default_config

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"設定読み込みエラー: {e}")
            return {}

    def _save_config(self, config: Dict):
        """設定を保存"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"設定保存エラー: {e}")

    async def create_board_from_plan(
        self,
        plan_file: str,
        board_title: str,
        board_config: Optional[BoardConfig] = None,
    ) -> Optional[ProjectBoard]:
        """計画書からプロジェクトボードを作成"""
        if not board_config:
            board_config = BoardConfig()

        print(f"📊 プロジェクトボード作成開始: {board_title}")
        print(f"   📋 計画書: {plan_file}")
        print(f"   🎨 テンプレート: {board_config.template.value}")

        try:
            # 計画書を読み込み
            plan_path = self.base_path / "docs" / "plans" / plan_file
            if not plan_path.exists():
                logger.error(f"計画書が見つかりません: {plan_path}")
                return None

            # タスクを分解
            tasks = await self.task_engine.extract_tasks_from_plan(str(plan_path))
            if not tasks:
                logger.warning(f"計画書からタスクを抽出できませんでした: {plan_file}")
                return None

            print(f"   📝 抽出されたタスク数: {len(tasks)}")

            # GitHub Projectsクライアントでボードを作成
            async with self.github_client as client:
                # 組織のプロジェクトを取得して、同じタイトルのものがないかチェック
                existing_projects = await client.get_organization_projects()
                for project in existing_projects:
                    if project.title == board_title:
                        logger.info(
                            f"既存のプロジェクトが見つかりました: {board_title}"
                        )
                        return project

                # 新規プロジェクトの作成（dry runモードではダミーデータを返す）
                if client.dry_run:
                    project = ProjectBoard(
                        id=f"PVT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        number=len(existing_projects) + 1,
                        title=board_title,
                        description=f"計画書 '{plan_file}' から自動生成されたプロジェクトボード",
                        owner=client.owner,
                        url=f"https://github.com/orgs/{client." \
                            "owner}/projects/{len(existing_projects) + 1}",
                    )

                    # 同期マッピングを作成
                    mapping_key = f"{plan_file}_{project.id}"
                    self.sync_mappings[mapping_key] = SyncMapping(
                        plan_file=plan_file,
                        project_id=project.id,
                        board_config=board_config,
                    )
                    self._save_sync_mappings()

                    print(f"✅ プロジェクトボード作成完了: {board_title}")
                    print(f"   🆔 プロジェクトID: {project.id}")
                    print(f"   🔗 URL: {project.url}")

                    return project

                # 実際のプロジェクト作成はGraphQL APIを使用
                # ここでは実装の詳細を省略し、成功を想定
                logger.info(f"プロジェクトボード作成: {board_title}")
                return None

        except Exception as e:
            logger.error(f"プロジェクトボード作成エラー: {e}")
            return None

    async def sync_plan_to_board(
        self, plan_file: str, project_id: Optional[str] = None
    ) -> Dict:
        """計画書をプロジェクトボードに同期"""
        print(f"🔄 計画書同期開始: {plan_file}")

        # 同期マッピングを検索
        mapping = None
        if project_id:
            for key, m in self.sync_mappings.items():
                if m.project_id == project_id and m.plan_file == plan_file:
                    mapping = m
                    break
        else:
            # 計画書に対応するマッピングを検索
            for key, m in self.sync_mappings.items():
                if m.plan_file == plan_file:
                    mapping = m
                    project_id = m.project_id
                    break

        if not mapping:
            logger.error(f"同期マッピングが見つかりません: {plan_file}")
            return {"success": False, "error": "同期マッピングが見つかりません"}

        try:
            # 計画書からタスクを抽出
            plan_path = self.base_path / "docs" / "plans" / plan_file
            tasks = await self.task_engine.extract_tasks_from_plan(str(plan_path))

            if not tasks:
                logger.warning(f"タスクが見つかりません: {plan_file}")
                return {"success": False, "error": "タスクが見つかりません"}

            print(f"   📝 抽出されたタスク数: {len(tasks)}")

            # タスクをプロジェクトアイテム形式に変換
            project_tasks = []
            for task in tasks:
                project_tasks.append(
                    {
                        "title": task.title,
                        "description": task.description,
                        "priority": task.priority,
                        "category": task.category,
                        "estimated_hours": task.estimated_hours,
                        "dependencies": task.dependencies,
                    }
                )

            # GitHub Projectsに同期
            async with self.github_client as client:
                sync_result = await client.sync_plan_to_project(
                    project_id, plan_file, project_tasks
                )

                # 統計を更新
                self.stats["total_syncs"] += 1
                if sync_result.get("created_items") or sync_result.get("updated_items"):
                    self.stats["successful_syncs"] += 1
                else:
                    self.stats["failed_syncs"] += 1
                self.stats["last_sync"] = datetime.now().isoformat()

                # 同期マッピングを更新
                mapping.last_sync = datetime.now().isoformat()
                mapping.sync_count += 1
                self._save_sync_mappings()

                print(f"✅ 同期完了!")
                print(f"   ➕ 新規作成: {len(sync_result.get('created_items', []))}")
                print(f"   🔄 更新: {len(sync_result.get('updated_items', []))}")
                print(f"   ❌ 失敗: {len(sync_result.get('failed_items', []))}")

                return {
                    "success": True,
                    "sync_result": sync_result,
                    "mapping": asdict(mapping),
                }

        except Exception as e:
            logger.error(f"同期エラー: {e}")
            self.stats["failed_syncs"] += 1
            return {"success": False, "error": str(e)}

    async def get_board_progress(self, project_id: str) -> Dict:
        """プロジェクトボードの進捗を取得"""
        try:
            async with self.github_client as client:
                overview = await client.get_project_overview(project_id)

                # 進捗率を計算
                status_counts = overview.get("status_counts", {})
                total_items = overview.get("total_items", 0)

                if total_items == 0:
                    progress_rate = 0.0
                else:
                    completed = status_counts.get("Done", 0)
                    progress_rate = (completed / total_items) * 100

                # 詳細な進捗情報を計算
                in_progress = status_counts.get("In Progress", 0)
                todo = status_counts.get("Todo", 0)
                blocked = status_counts.get("Blocked", 0)

                return {
                    "project_id": project_id,
                    "total_items": total_items,
                    "progress_rate": round(progress_rate, 1),
                    "status_breakdown": {
                        "completed": status_counts.get("Done", 0),
                        "in_progress": in_progress,
                        "todo": todo,
                        "blocked": blocked,
                    },
                    "priority_breakdown": overview.get("priority_counts", {}),
                    "last_updated": overview.get("last_updated"),
                    "health_score": self._calculate_health_score(
                        status_counts, total_items
                    ),
                }

        except Exception as e:
            logger.error(f"進捗取得エラー: {e}")
            return {"error": str(e)}

    def _calculate_health_score(self, status_counts: Dict, total_items: int) -> float:
        """プロジェクトの健全性スコアを計算"""
        if total_items == 0:
            return 100.0

        # 各ステータスの重み
        weights = {"Done": 1.0, "In Progress": 0.7, "Todo": 0.3, "Blocked": -0.2}

        score = 0.0
        for status, count in status_counts.items():
            weight = weights.get(status, 0.5)
            score += (count / total_items) * weight * 100

        return max(0.0, min(100.0, score))

    async def get_all_boards_summary(self) -> Dict:
        """すべてのボードの概要を取得"""
        summary = {
            "total_boards": len(self.sync_mappings),
            "boards": [],
            "overall_stats": self.stats,
            "last_updated": datetime.now().isoformat(),
        }

        for key, mapping in self.sync_mappings.items():
            try:
                progress = await self.get_board_progress(mapping.project_id)
                board_info = {
                    "plan_file": mapping.plan_file,
                    "project_id": mapping.project_id,
                    "template": mapping.board_config.template.value,
                    "last_sync": mapping.last_sync,
                    "sync_count": mapping.sync_count,
                    "progress": progress,
                }
                summary["boards"].append(board_info)
            except Exception as e:
                logger.error(f"ボード情報取得エラー: {key} - {e}")

        return summary

    async def auto_sync_all_boards(self) -> Dict:
        """すべてのボードを自動同期"""
        print("🔄 全ボード自動同期開始")

        sync_results = {
            "timestamp": datetime.now().isoformat(),
            "total_boards": len(self.sync_mappings),
            "successful_syncs": 0,
            "failed_syncs": 0,
            "sync_details": [],
        }

        for key, mapping in self.sync_mappings.items():
            try:
                print(f"   📊 同期中: {mapping.plan_file}")
                result = await self.sync_plan_to_board(
                    mapping.plan_file, mapping.project_id
                )

                if result.get("success"):
                    sync_results["successful_syncs"] += 1
                else:
                    sync_results["failed_syncs"] += 1

                sync_results["sync_details"].append(
                    {
                        "plan_file": mapping.plan_file,
                        "project_id": mapping.project_id,
                        "result": result,
                    }
                )

            except Exception as e:
                logger.error(f"自動同期エラー: {key} - {e}")
                sync_results["failed_syncs"] += 1
                sync_results["sync_details"].append(
                    {
                        "plan_file": mapping.plan_file,
                        "project_id": mapping.project_id,
                        "result": {"success": False, "error": str(e)},
                    }
                )

        print(f"✅ 全ボード自動同期完了")
        print(f"   ✅ 成功: {sync_results['successful_syncs']}")
        print(f"   ❌ 失敗: {sync_results['failed_syncs']}")

        return sync_results

    async def create_board_mapping(
        self,
        plan_file: str,
        project_id: str,
        board_config: Optional[BoardConfig] = None,
    ) -> bool:
        """ボードマッピングを作成"""
        if not board_config:
            board_config = BoardConfig()

        mapping_key = f"{plan_file}_{project_id}"

        self.sync_mappings[mapping_key] = SyncMapping(
            plan_file=plan_file, project_id=project_id, board_config=board_config
        )

        self._save_sync_mappings()
        logger.info(f"ボードマッピング作成: {mapping_key}")
        return True

    async def remove_board_mapping(self, plan_file: str, project_id: str) -> bool:
        """ボードマッピングを削除"""
        mapping_key = f"{plan_file}_{project_id}"

        if mapping_key in self.sync_mappings:
            del self.sync_mappings[mapping_key]
            self._save_sync_mappings()
            logger.info(f"ボードマッピング削除: {mapping_key}")
            return True

        logger.warning(f"ボードマッピングが見つかりません: {mapping_key}")
        return False

    async def get_sync_recommendations(self) -> List[Dict]:
        """同期推奨事項を取得"""
        recommendations = []

        # 長期間同期されていないボードを検出
        for key, mapping in self.sync_mappings.items():
            if mapping.last_sync:
                last_sync = datetime.fromisoformat(mapping.last_sync)
                hours_since_sync = (datetime.now() - last_sync).total_seconds() / 3600

                if hours_since_sync > 48:  # 48時間以上
                    recommendations.append(
                        {
                            "type": "stale_sync",
                            "priority": "medium",
                            "plan_file": mapping.plan_file,
                            "project_id": mapping.project_id,
                            "message": f"48時間以上同期されていません ({hours_since_sync:.1f}時間)",
                            "action": "sync_plan_to_board",
                        }
                    )

        # 計画書ファイルの存在チェック
        for key, mapping in self.sync_mappings.items():
            plan_path = self.base_path / "docs" / "plans" / mapping.plan_file
            if not plan_path.exists():
                recommendations.append(
                    {
                        "type": "missing_plan",
                        "priority": "high",
                        "plan_file": mapping.plan_file,
                        "project_id": mapping.project_id,
                        "message": "計画書ファイルが見つかりません",
                        "action": "remove_mapping",
                    }
                )

        return recommendations


# 使用例
async def main():
    """メイン実行関数"""
    manager = ProjectBoardManager()

    # すべてのボードの概要を取得
    summary = await manager.get_all_boards_summary()
    print(f"📊 ボード管理システム概要:")
    print(f"   📋 総ボード数: {summary['total_boards']}")
    print(f"   🔄 総同期数: {summary['overall_stats']['total_syncs']}")
    print(f"   ✅ 成功同期数: {summary['overall_stats']['successful_syncs']}")

    # 同期推奨事項を取得
    recommendations = await manager.get_sync_recommendations()
    if recommendations:
        print(f"\n💡 同期推奨事項:")
        for rec in recommendations:
            print(f"   {rec['type']}: {rec['message']}")


if __name__ == "__main__":
    asyncio.run(main())
