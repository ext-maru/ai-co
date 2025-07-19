#!/usr/bin/env python3
"""
プロジェクトマネージャーエルダー
既存のタスクエルダーシステムを拡張し、プロジェクト管理機能を提供
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ProjectManagerElder:
    """プロジェクト管理を司るエルダー"""

    def __init__(self, db_path: str = "task_history.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """データベースの初期化と拡張"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # プロジェクトテーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                status TEXT DEFAULT 'active',
                owner TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                start_date DATE,
                end_date DATE,
                progress REAL DEFAULT 0.0,
                fantasy_rank TEXT DEFAULT '⭐ HIGH',
                elder_assignment TEXT
            )
        """
        )

        # マイルストーンテーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                due_date DATE,
                status TEXT DEFAULT 'pending',
                progress REAL DEFAULT 0.0,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """
        )

        # タスクテーブル（拡張版）
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                milestone_id INTEGER,
                parent_task_id INTEGER,
                category TEXT NOT NULL,
                task_name TEXT NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 5,
                status TEXT DEFAULT 'pending',
                estimated_hours REAL,
                actual_hours REAL DEFAULT 0,
                dependencies TEXT,
                assigned_team TEXT,
                assigned_user TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                start_date DATE,
                due_date DATE,
                completion_rate REAL DEFAULT 0.0,
                fantasy_classification TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (milestone_id) REFERENCES milestones(id),
                FOREIGN KEY (parent_task_id) REFERENCES tasks(id)
            )
        """
        )

        # タスク履歴テーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                status_from TEXT,
                status_to TEXT,
                comment TEXT,
                changed_by TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """
        )

        conn.commit()
        conn.close()

    # プロジェクト管理メソッド
    def create_project(
        self,
        name: str,
        description: str = None,
        owner: str = "Grand Elder maru",
        start_date: str = None,
        end_date: str = None,
        fantasy_rank: str = "⭐ HIGH",
    ) -> int:
        """新規プロジェクトを作成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # エルダー自動割り当て
        elder_assignment = self._assign_elder_by_category(name, description)

        cursor.execute(
            """
            INSERT INTO projects (name, description, owner, start_date, end_date, fantasy_rank, elder_assignment)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                name,
                description,
                owner,
                start_date,
                end_date,
                fantasy_rank,
                elder_assignment,
            ),
        )

        project_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(
            f"🏰 プロジェクト '{name}' を作成しました (ID: {project_id}, 担当: {elder_assignment})"
        )
        return project_id

    def _assign_elder_by_category(self, name: str, description: str = None) -> str:
        """プロジェクト内容に基づいてエルダーを自動割り当て"""
        content = f"{name} {description or ''}".lower()

        if any(
            word in content
            for word in ["障害", "バグ", "修正", "incident", "error", "fix"]
        ):
            return "🛡️ インシデント騎士団"
        elif any(
            word in content
            for word in ["開発", "実装", "新機能", "develop", "feature", "implement"]
        ):
            return "🔨 ドワーフ工房"
        elif any(
            word in content
            for word in [
                "調査",
                "研究",
                "ドキュメント",
                "research",
                "analyze",
                "document",
            ]
        ):
            return "🧙‍♂️ RAGウィザーズ"
        elif any(
            word in content
            for word in ["監視", "最適化", "テスト", "monitor", "optimize", "test"]
        ):
            return "🧝‍♂️ エルフの森"
        else:
            return "📋 タスクエルダー"

    def create_milestone(
        self, project_id: int, name: str, description: str = None, due_date: str = None
    ) -> int:
        """マイルストーンを作成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO milestones (project_id, name, description, due_date)
            VALUES (?, ?, ?, ?)
        """,
            (project_id, name, description, due_date),
        )

        milestone_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"🎯 マイルストーン '{name}' を作成しました (ID: {milestone_id})")
        return milestone_id

    def create_task(
        self,
        project_id: int,
        task_name: str,
        category: str = "development",
        milestone_id: int = None,
        parent_task_id: int = None,
        description: str = None,
        priority: int = 5,
        estimated_hours: float = None,
        assigned_team: str = None,
        assigned_user: str = None,
        dependencies: List[int] = None,
        due_date: str = None,
    ) -> int:
        """タスクを作成（既存のタスクシステムと互換性維持）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # ファンタジー分類を自動判定
        fantasy_classification = self._classify_task(task_name, description, priority)

        cursor.execute(
            """
            INSERT INTO tasks (
                project_id, milestone_id, parent_task_id, category, task_name,
                description, priority, estimated_hours, assigned_team, assigned_user,
                dependencies, due_date, fantasy_classification
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                project_id,
                milestone_id,
                parent_task_id,
                category,
                task_name,
                description,
                priority,
                estimated_hours,
                assigned_team,
                assigned_user,
                json.dumps(dependencies) if dependencies else None,
                due_date,
                fantasy_classification,
            ),
        )

        task_id = cursor.lastrowid

        # タスク履歴に記録
        cursor.execute(
            """
            INSERT INTO task_history (task_id, status_to, comment, changed_by)
            VALUES (?, 'pending', 'タスク作成', 'Task Elder')
        """,
            (task_id,),
        )

        conn.commit()
        conn.close()

        logger.info(
            f"📋 タスク '{task_name}' を作成しました (ID: {task_id}, 分類: {fantasy_classification})"
        )
        return task_id

    def _classify_task(
        self, task_name: str, description: str = None, priority: int = 5
    ) -> str:
        """タスクをファンタジー世界観で分類"""
        content = f"{task_name} {description or ''}".lower()

        # 緊急度による分類
        if priority >= 9:
            return "🐉 古龍討伐"
        elif priority >= 7:
            return "⚔️ オーク軍団制圧"

        # 内容による分類
        if any(word in content for word in ["メモリリーク", "memory leak"]):
            return "🌊 スライム増殖対策"
        elif any(word in content for word in ["無限ループ", "infinite loop"]):
            return "🗿 ゴーレム鎮圧"
        elif any(word in content for word in ["デッドロック", "deadlock"]):
            return "🕷️ クモの巣除去"
        elif any(word in content for word in ["バグ", "bug", "エラー", "error"]):
            return "🧚‍♀️ 妖精の悪戯修正"
        elif any(word in content for word in ["新機能", "new feature"]):
            return "⚒️ 伝説装備鍛造"
        elif any(word in content for word in ["調査", "research"]):
            return "📜 古代知識解読"
        elif any(word in content for word in ["最適化", "optimize"]):
            return "🌿 森の癒し"
        else:
            return "✨ 日常任務"

    def update_task_status(
        self,
        task_id: int,
        new_status: str,
        comment: str = None,
        changed_by: str = "Task Elder",
    ) -> bool:
        """タスクステータスを更新"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 現在のステータスを取得
        cursor.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False

        old_status = result[0]

        # ステータス更新
        cursor.execute(
            """
            UPDATE tasks
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """,
            (new_status, task_id),
        )

        # 履歴記録
        cursor.execute(
            """
            INSERT INTO task_history (task_id, status_from, status_to, comment, changed_by)
            VALUES (?, ?, ?, ?, ?)
        """,
            (task_id, old_status, new_status, comment, changed_by),
        )

        # プロジェクトとマイルストーンの進捗を再計算
        self._update_progress(cursor, task_id)

        conn.commit()
        conn.close()

        logger.info(
            f"📝 タスク {task_id} のステータスを '{old_status}' → '{new_status}' に更新"
        )
        return True

    def _update_progress(self, cursor, task_id: int):
        """プロジェクトとマイルストーンの進捗を再計算"""
        # タスクが属するプロジェクトとマイルストーンを取得
        cursor.execute(
            """
            SELECT project_id, milestone_id FROM tasks WHERE id = ?
        """,
            (task_id,),
        )
        result = cursor.fetchone()
        if not result:
            return

        project_id, milestone_id = result

        # マイルストーンの進捗計算
        if milestone_id:
            cursor.execute(
                """
                SELECT COUNT(*), SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)
                FROM tasks WHERE milestone_id = ?
            """,
                (milestone_id,),
            )
            total, completed = cursor.fetchone()
            if total > 0:
                progress = (completed / total) * 100
                cursor.execute(
                    """
                    UPDATE milestones SET progress = ? WHERE id = ?
                """,
                    (progress, milestone_id),
                )

        # プロジェクトの進捗計算
        cursor.execute(
            """
            SELECT COUNT(*), SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)
            FROM tasks WHERE project_id = ?
        """,
            (project_id,),
        )
        total, completed = cursor.fetchone()
        if total > 0:
            progress = (completed / total) * 100
            cursor.execute(
                """
                UPDATE projects SET progress = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
            """,
                (progress, project_id),
            )

    def get_project_gantt_data(self, project_id: int) -> Dict:
        """ガントチャート用のデータを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # プロジェクト情報
        cursor.execute(
            """
            SELECT name, description, start_date, end_date, progress, elder_assignment
            FROM projects WHERE id = ?
        """,
            (project_id,),
        )
        project = cursor.fetchone()

        if not project:
            conn.close()
            return None

        # マイルストーン情報
        cursor.execute(
            """
            SELECT id, name, due_date, progress
            FROM milestones WHERE project_id = ?
            ORDER BY due_date
        """,
            (project_id,),
        )
        milestones = cursor.fetchall()

        # タスク情報（階層構造を保持）
        cursor.execute(
            """
            SELECT id, parent_task_id, milestone_id, task_name, status,
                   start_date, due_date, completion_rate, assigned_team,
                   fantasy_classification, dependencies
            FROM tasks WHERE project_id = ?
            ORDER BY milestone_id, parent_task_id, id
        """,
            (project_id,),
        )
        tasks = cursor.fetchall()

        conn.close()

        # ガントチャート用データ構造に変換
        gantt_data = {
            "project": {
                "id": project_id,
                "name": project[0],
                "description": project[1],
                "start_date": project[2],
                "end_date": project[3],
                "progress": project[4],
                "elder_assignment": project[5],
            },
            "milestones": [
                {"id": m[0], "name": m[1], "due_date": m[2], "progress": m[3]}
                for m in milestones
            ],
            "tasks": self._build_task_hierarchy(tasks),
        }

        return gantt_data

    def _build_task_hierarchy(self, tasks: List[Tuple]) -> List[Dict]:
        """タスクを階層構造に変換"""
        task_dict = {}
        root_tasks = []

        # まずすべてのタスクを辞書に格納
        for task in tasks:
            task_data = {
                "id": task[0],
                "parent_id": task[1],
                "milestone_id": task[2],
                "name": task[3],
                "status": task[4],
                "start_date": task[5],
                "due_date": task[6],
                "completion_rate": task[7],
                "assigned_team": task[8],
                "fantasy_classification": task[9],
                "dependencies": json.loads(task[10]) if task[10] else [],
                "children": [],
            }
            task_dict[task[0]] = task_data

        # 階層構造を構築
        for task_id, task_data in task_dict.items():
            if task_data["parent_id"]:
                parent = task_dict.get(task_data["parent_id"])
                if parent:
                    parent["children"].append(task_data)
            else:
                root_tasks.append(task_data)

        return root_tasks

    def get_dashboard_stats(self) -> Dict:
        """ダッシュボード用の統計情報を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # プロジェクト統計
        cursor.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                AVG(progress) as avg_progress
            FROM projects
        """
        )
        stats["projects"] = dict(
            zip(["total", "active", "completed", "avg_progress"], cursor.fetchone())
        )

        # タスク統計
        cursor.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN priority >= 7 THEN 1 ELSE 0 END) as high_priority
            FROM tasks
        """
        )
        stats["tasks"] = dict(
            zip(
                ["total", "pending", "in_progress", "completed", "high_priority"],
                cursor.fetchone(),
            )
        )

        # エルダー別タスク分布
        cursor.execute(
            """
            SELECT assigned_team, COUNT(*) as count
            FROM tasks
            WHERE assigned_team IS NOT NULL
            GROUP BY assigned_team
        """
        )
        stats["elder_distribution"] = dict(cursor.fetchall())

        # ファンタジー分類別統計
        cursor.execute(
            """
            SELECT fantasy_classification, COUNT(*) as count
            FROM tasks
            WHERE fantasy_classification IS NOT NULL
            GROUP BY fantasy_classification
            ORDER BY count DESC
            LIMIT 10
        """
        )
        stats["fantasy_distribution"] = cursor.fetchall()

        conn.close()
        return stats


# エルダーズギルド統合用のAPI
class ElderGuildIntegration:
    """4賢者システムとの統合インターフェース"""

    def __init__(self, project_manager: ProjectManagerElder):
        self.pm = project_manager

    def consult_knowledge_sage(self, project_id: int) -> List[str]:
        """ナレッジ賢者に過去の類似プロジェクトを相談"""
        # knowledge_base/からの知識検索をシミュレート
        return [
            "過去の類似プロジェクト: Web Portal実装 (2024)",
            "推奨アーキテクチャ: React + FastAPI + PostgreSQL",
            "注意点: 認証システムの早期実装が重要",
        ]

    def consult_task_sage(self, project_id: int) -> Dict:
        """タスク賢者に最適な実行順序を相談"""
        # タスクの依存関係を分析して最適順序を提案
        return {
            "critical_path": [
                "認証システム",
                "データベース設計",
                "API実装",
                "フロントエンド",
            ],
            "parallel_tasks": [["ドキュメント作成", "テスト環境構築"]],
            "estimated_duration": "3週間",
        }

    def consult_incident_sage(self, task_id: int) -> List[Dict]:
        """インシデント賢者に潜在的リスクを相談"""
        return [
            {
                "risk": "メモリリーク",
                "probability": 0.3,
                "impact": "高",
                "mitigation": "定期的なプロファイリング",
            },
            {
                "risk": "認証脆弱性",
                "probability": 0.2,
                "impact": "重大",
                "mitigation": "セキュリティ監査実施",
            },
        ]

    def consult_rag_sage(self, query: str) -> str:
        """RAG賢者に技術的な質問"""
        # 実際のRAGシステムとの統合をシミュレート
        return f"RAG賢者の回答: {query}に関する最新のベストプラクティスは..."


if __name__ == "__main__":
    # 使用例
    pm = ProjectManagerElder()

    # プロジェクト作成
    project_id = pm.create_project(
        name="エルダーズギルド Web Portal",
        description="プロジェクト管理システムのWeb UI実装",
        fantasy_rank="🏆 EPIC",
    )

    # マイルストーン作成
    m1 = pm.create_milestone(project_id, "Phase 1: 基盤構築", due_date="2025-01-20")
    m2 = pm.create_milestone(project_id, "Phase 2: 機能実装", due_date="2025-02-01")

    # タスク作成
    t1 = pm.create_task(
        project_id=project_id,
        milestone_id=m1,
        task_name="認証システム実装",
        category="development",
        priority=8,
        estimated_hours=16,
        assigned_team="🔨 ドワーフ工房",
    )

    # 統計情報表示
    stats = pm.get_dashboard_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
