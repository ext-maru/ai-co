#!/usr/bin/env python3
"""
🏛️ エルダーズギルド プロジェクトテンプレートシステム
Project Template System for Elders Guild

コンテキスト制限対応とプロジェクト標準化を実現
- プロジェクト開始時のテンプレート
- 状態管理とチェックリスト
- 4賢者統合による自動相談
- 継続性の確保
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import uuid
import sys

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)


class ProjectTemplate:
    """プロジェクトテンプレート定義"""

    def __init__(self, name: str, description: str = ""):
        """初期化メソッド"""
        self.name = name
        self.description = description
        self.phases = []
        self.checklists = {}
        self.elder_consultations = {}
        self.status_triggers = {}

    def add_phase(
        self, phase_name: str, tasks: List[str], estimated_days: int = 7
    ) -> "ProjectTemplate":
        """フェーズを追加"""
        self.phases.append(
            {
                "name": phase_name,
                "tasks": tasks,
                "estimated_days": estimated_days,
                "checklist": [],
            }
        )
        return self

    def add_checklist(
        self, phase_name: str, checklist_items: List[str]
    ) -> "ProjectTemplate":
        """チェックリストを追加"""
        self.checklists[phase_name] = checklist_items
        return self

    def add_elder_consultation(
        self, phase_name: str, sage_type: str, consultation_prompt: str
    ) -> "ProjectTemplate":
        """エルダー相談を追加"""
        if phase_name not in self.elder_consultations:
            self.elder_consultations[phase_name] = []
        self.elder_consultations[phase_name].append(
            {"sage_type": sage_type, "prompt": consultation_prompt}
        )
        return self

    def add_status_trigger(
        self, trigger_condition: str, action: str
    ) -> "ProjectTemplate":
        """状態トリガーを追加"""
        trigger_id = str(uuid.uuid4())
        self.status_triggers[trigger_id] = {
            "condition": trigger_condition,
            "action": action,
        }
        return self


class ProjectStatusManager:
    """プロジェクト状態管理"""

    def __init__(self, db_path: str = "project_status.db"):
        """初期化メソッド"""
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """データベース初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # プロジェクト状態テーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS project_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT UNIQUE NOT NULL,
                project_name TEXT NOT NULL,
                template_name TEXT,
                current_phase TEXT,
                phase_index INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                context_data TEXT,
                checklist_state TEXT,
                elder_consultation_log TEXT
            )
        """
        )

        # フェーズ履歴テーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS phase_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                phase_name TEXT NOT NULL,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                completed BOOLEAN DEFAULT FALSE,
                checklist_completion TEXT,
                notes TEXT,
                FOREIGN KEY (project_id) REFERENCES project_status(project_id)
            )
        """
        )

        # 継続性ログテーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS continuity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                session_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action TEXT,
                context_snapshot TEXT,
                previous_actions TEXT,
                next_actions TEXT,
                FOREIGN KEY (project_id) REFERENCES project_status(project_id)
            )
        """
        )

        conn.commit()
        conn.close()

    def create_project_status(
        self,
        project_id: str,
        project_name: str,
        template_name: str = None,
        context_data: Dict = None,
    ) -> bool:
        """プロジェクト状態を作成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO project_status
                (project_id, project_name, template_name, context_data)
                VALUES (?, ?, ?, ?)
            """,
                (
                    project_id,
                    project_name,
                    template_name,
                    json.dumps(context_data) if context_data else None,
                ),
            )

            conn.commit()
            logger.info(f"プロジェクト状態を作成: {project_name} (ID: {project_id})")
            return True

        except sqlite3.IntegrityError:
            logger.warning(f"プロジェクト状態は既に存在: {project_id}")
            return False
        finally:
            conn.close()

    def get_project_status(self, project_id: str) -> Optional[Dict]:
        """プロジェクト状態を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM project_status WHERE project_id = ?
        """,
            (project_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "project_id": row[1],
                "project_name": row[2],
                "template_name": row[3],
                "current_phase": row[4],
                "phase_index": row[5],
                "status": row[6],
                "created_at": row[7],
                "updated_at": row[8],
                "context_data": json.loads(row[9]) if row[9] else {},
                "checklist_state": json.loads(row[10]) if row[10] else {},
                "elder_consultation_log": json.loads(row[11]) if row[11] else [],
            }
        return None

    def update_project_phase(
        self,
        project_id: str,
        phase_name: str,
        phase_index: int,
        context_data: Dict = None,
    ) -> bool:
        """プロジェクトフェーズを更新"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 現在のフェーズを完了としてマーク
        cursor.execute(
            """
            UPDATE phase_history
            SET end_date = CURRENT_TIMESTAMP, completed = TRUE
            WHERE project_id = ? AND completed = FALSE
        """,
            (project_id,),
        )

        # 新しいフェーズを開始
        cursor.execute(
            """
            INSERT INTO phase_history (project_id, phase_name, start_date)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """,
            (project_id, phase_name),
        )

        # プロジェクト状態を更新
        cursor.execute(
            """
            UPDATE project_status
            SET current_phase = ?, phase_index = ?, updated_at = CURRENT_TIMESTAMP,
                context_data = COALESCE(?, context_data)
            WHERE project_id = ?
        """,
            (
                phase_name,
                phase_index,
                json.dumps(context_data) if context_data else None,
                project_id,
            ),
        )

        conn.commit()
        conn.close()

        logger.info(f"フェーズ更新: {project_id} → {phase_name}")
        return True

    def log_continuity(
        self,
        project_id: str,
        session_id: str,
        action: str,
        context_snapshot: Dict,
        previous_actions: List[str] = None,
        next_actions: List[str] = None,
    ) -> bool:
        """継続性ログを記録"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO continuity_log
            (project_id, session_id, action, context_snapshot, previous_actions, next_actions)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                project_id,
                session_id,
                action,
                json.dumps(context_snapshot),
                json.dumps(previous_actions) if previous_actions else None,
                json.dumps(next_actions) if next_actions else None,
            ),
        )

        conn.commit()
        conn.close()

        return True

    def get_continuity_log(self, project_id: str, limit: int = 10) -> List[Dict]:
        """継続性ログを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM continuity_log
            WHERE project_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (project_id, limit),
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "session_id": row[2],
                "timestamp": row[3],
                "action": row[4],
                "context_snapshot": json.loads(row[5]) if row[5] else {},
                "previous_actions": json.loads(row[6]) if row[6] else [],
                "next_actions": json.loads(row[7]) if row[7] else [],
            }
            for row in rows
        ]


class ProjectTemplateSystem:
    """プロジェクトテンプレートシステム"""

    def __init__(self, db_path: str = "project_status.db"):
        """初期化メソッド"""
        self.status_manager = ProjectStatusManager(db_path)
        self.templates = {}
        self.current_session_id = str(uuid.uuid4())
        self._init_default_templates()

    def _init_default_templates(self):
        """デフォルトテンプレートを初期化"""
        # Web開発プロジェクトテンプレート
        web_template = (
            ProjectTemplate("web_development", "Web開発プロジェクト用テンプレート")
            .add_phase(
                "Phase 1: 要件定義・設計",
                ["要件整理", "技術選定", "アーキテクチャ設計", "データベース設計"],
                7,
            )
            .add_phase(
                "Phase 2: 基盤実装",
                ["認証システム", "データベース構築", "API基盤", "フロントエンド基盤"],
                14,
            )
            .add_phase(
                "Phase 3: 機能実装",
                ["コア機能実装", "UI/UX実装", "テスト実装", "統合テスト"],
                21,
            )
            .add_phase(
                "Phase 4: 最適化・デプロイ",
                [
                    "パフォーマンス最適化",
                    "セキュリティ強化",
                    "デプロイ準備",
                    "本番デプロイ",
                ],
                10,
            )
            .add_checklist(
                "Phase 1: 要件定義・設計",
                [
                    "要件書レビュー完了",
                    "技術選定理由書作成",
                    "アーキテクチャ図作成",
                    "データベース設計書作成",
                ],
            )
            .add_checklist(
                "Phase 2: 基盤実装",
                [
                    "認証システム実装・テスト",
                    "データベース作成・マイグレーション",
                    "API基盤実装",
                    "フロントエンド基盤実装",
                ],
            )
            .add_elder_consultation(
                "Phase 1: 要件定義・設計",
                "knowledge_sage",
                "類似プロジェクトの成功事例と失敗事例を教えて",
            )
            .add_elder_consultation(
                "Phase 2: 基盤実装",
                "incident_sage",
                "実装時に注意すべきセキュリティリスクを教えて",
            )
            .add_elder_consultation(
                "Phase 3: 機能実装",
                "task_sage",
                "機能実装の最適な順序と並列化可能なタスクを教えて",
            )
            .add_elder_consultation(
                "Phase 4: 最適化・デプロイ",
                "rag_sage",
                "最新のパフォーマンス最適化手法とデプロイベストプラクティスを教えて",
            )
        )

        # AI開発プロジェクトテンプレート
        ai_template = (
            ProjectTemplate("ai_development", "AI開発プロジェクト用テンプレート")
            .add_phase(
                "Phase 1: 問題定義・データ調査",
                ["問題定義", "データ収集", "データ分析", "仮説設定"],
                10,
            )
            .add_phase(
                "Phase 2: モデル開発",
                [
                    "ベースライン実装",
                    "モデル選定",
                    "特徴量エンジニアリング",
                    "モデル学習",
                ],
                14,
            )
            .add_phase(
                "Phase 3: 評価・改善",
                [
                    "モデル評価",
                    "ハイパーパラメータ調整",
                    "モデル改善",
                    "バリデーション",
                ],
                10,
            )
            .add_phase(
                "Phase 4: 統合・デプロイ",
                ["システム統合", "推論API実装", "モニタリング実装", "本番デプロイ"],
                7,
            )
            .add_checklist(
                "Phase 1: 問題定義・データ調査",
                ["問題定義書作成", "データ収集完了", "EDA実施", "仮説リスト作成"],
            )
            .add_elder_consultation(
                "Phase 1: 問題定義・データ調査",
                "rag_sage",
                "類似のAI問題解決事例と最新のアプローチを教えて",
            )
            .add_elder_consultation(
                "Phase 2: モデル開発",
                "knowledge_sage",
                "この問題に適したモデルアーキテクチャの選択肢を教えて",
            )
        )

        # 緊急修正プロジェクトテンプレート
        hotfix_template = (
            ProjectTemplate("hotfix", "緊急修正プロジェクト用テンプレート")
            .add_phase(
                "Phase 1: 緊急調査",
                ["問題特定", "影響範囲調査", "原因分析", "修正方針決定"],
                1,
            )
            .add_phase(
                "Phase 2: 修正実装",
                ["修正実装", "単体テスト", "統合テスト", "影響確認"],
                2,
            )
            .add_phase(
                "Phase 3: 緊急デプロイ",
                ["デプロイ準備", "本番デプロイ", "動作確認", "監視強化"],
                1,
            )
            .add_checklist(
                "Phase 1: 緊急調査",
                ["問題の根本原因特定", "影響範囲の完全把握", "修正方針の4賢者承認"],
            )
            .add_elder_consultation(
                "Phase 1: 緊急調査",
                "incident_sage",
                "この問題の根本原因と最適な修正アプローチを教えて",
            )
            .add_elder_consultation(
                "Phase 2: 修正実装",
                "task_sage",
                "修正実装の最速かつ安全な実行順序を教えて",
            )
        )

        # テンプレートを登録
        self.templates = {
            "web_development": web_template,
            "ai_development": ai_template,
            "hotfix": hotfix_template,
        }

    def create_project_from_template(
        self, project_name: str, template_name: str, context_data: Dict = None
    ) -> str:
        """テンプレートからプロジェクトを作成"""
        if template_name not in self.templates:
            raise ValueError(f"テンプレート '{template_name}' が見つかりません")

        project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

        # プロジェクト状態を作成
        self.status_manager.create_project_status(
            project_id, project_name, template_name, context_data
        )

        # 最初のフェーズを開始
        template = self.templates[template_name]
        if template.phases:
            first_phase = template.phases[0]
            self.status_manager.update_project_phase(
                project_id, first_phase["name"], 0, context_data
            )

        # 継続性ログを記録
        self.status_manager.log_continuity(
            project_id,
            self.current_session_id,
            "project_created",
            {
                "template_name": template_name,
                "project_name": project_name,
                "context_data": context_data or {},
            },
            previous_actions=[],
            next_actions=template.phases[0]["tasks"] if template.phases else [],
        )

        return project_id

    def get_project_context(self, project_id: str) -> Dict:
        """プロジェクトコンテキストを取得"""
        status = self.status_manager.get_project_status(project_id)
        if not status:
            return {}

        template = self.templates.get(status["template_name"])
        continuity_log = self.status_manager.get_continuity_log(project_id, 5)

        return {
            "project_info": status,
            "template": template,
            "continuity_log": continuity_log,
            "current_phase_tasks": self._get_current_phase_tasks(status, template),
            "checklist": self._get_current_checklist(status, template),
            "elder_consultations": self._get_elder_consultations(status, template),
        }

    def _get_current_phase_tasks(
        self, status: Dict, template: ProjectTemplate
    ) -> List[str]:
        """現在のフェーズのタスクを取得"""
        if not template or not template.phases:
            return []

        phase_index = status.get("phase_index", 0)
        if phase_index < len(template.phases):
            return template.phases[phase_index]["tasks"]
        return []

    def _get_current_checklist(
        self, status: Dict, template: ProjectTemplate
    ) -> List[str]:
        """現在のフェーズのチェックリストを取得"""
        if not template or not status.get("current_phase"):
            return []

        phase_name = status["current_phase"]
        return template.checklists.get(phase_name, [])

    def _get_elder_consultations(
        self, status: Dict, template: ProjectTemplate
    ) -> List[Dict]:
        """現在のフェーズのエルダー相談を取得"""
        if not template or not status.get("current_phase"):
            return []

        phase_name = status["current_phase"]
        return template.elder_consultations.get(phase_name, [])

    def advance_phase(self, project_id: str, context_data: Dict = None) -> bool:
        """フェーズを進める"""
        status = self.status_manager.get_project_status(project_id)
        if not status:
            return False

        template = self.templates.get(status["template_name"])
        if not template:
            return False

        current_phase_index = status.get("phase_index", 0)
        next_phase_index = current_phase_index + 1

        if next_phase_index >= len(template.phases):
            # プロジェクト完了
            return self._complete_project(project_id, context_data)

        next_phase = template.phases[next_phase_index]

        # フェーズを進める
        self.status_manager.update_project_phase(
            project_id, next_phase["name"], next_phase_index, context_data
        )

        # 継続性ログを記録
        self.status_manager.log_continuity(
            project_id,
            self.current_session_id,
            "phase_advanced",
            {
                "previous_phase": status["current_phase"],
                "current_phase": next_phase["name"],
                "phase_index": next_phase_index,
                "context_data": context_data or {},
            },
            previous_actions=self._get_current_phase_tasks(status, template),
            next_actions=next_phase["tasks"],
        )

        return True

    def _complete_project(self, project_id: str, context_data: Dict = None) -> bool:
        """プロジェクトを完了"""
        conn = sqlite3.connect(self.status_manager.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE project_status
            SET status = 'completed', updated_at = CURRENT_TIMESTAMP
            WHERE project_id = ?
        """,
            (project_id,),
        )

        # 最終フェーズを完了
        cursor.execute(
            """
            UPDATE phase_history
            SET end_date = CURRENT_TIMESTAMP, completed = TRUE
            WHERE project_id = ? AND completed = FALSE
        """,
            (project_id,),
        )

        conn.commit()
        conn.close()

        # 継続性ログを記録
        self.status_manager.log_continuity(
            project_id,
            self.current_session_id,
            "project_completed",
            {"completion_data": context_data or {}},
            previous_actions=["プロジェクト完了"],
            next_actions=[],
        )

        return True

    def generate_status_report(self, project_id: str) -> str:
        """状態レポートを生成"""
        context = self.get_project_context(project_id)
        if not context:
            return "プロジェクトが見つかりません"

        project_info = context["project_info"]
        template = context["template"]
        continuity_log = context["continuity_log"]
        current_tasks = context["current_phase_tasks"]
        checklist = context["checklist"]
        elder_consultations = context["elder_consultations"]

        report = f"""
🏛️ エルダーズギルド プロジェクト状況レポート
=============================================

📋 プロジェクト情報
- 名前: {project_info['project_name']}
- ID: {project_info['project_id']}
- テンプレート: {project_info['template_name']}
- 現在のフェーズ: {project_info['current_phase']}
- 状態: {project_info['status']}
- 作成日: {project_info['created_at']}
- 更新日: {project_info['updated_at']}

🎯 現在のタスク
{chr(10).join(f"- {task}" for task in current_tasks)}

✅ チェックリスト
{chr(10).join(f"- [ ] {item}" for item in checklist)}

🧙‍♂️ エルダー相談事項
{chr(10).join(f"- {consul['sage_type']}: {consul['prompt']}" for consul in elder_consultations)}

📈 最近の活動
{chr(10).join(f"- {log['timestamp']}: {log['action']}" for log in continuity_log[:3])}

🔄 フェーズ進捗
Phase {project_info['phase_index'] + 1} / {len(template.phases) if template else 'N/A'}
"""

        return report

    def get_project_list(self) -> List[Dict]:
        """プロジェクト一覧を取得"""
        conn = sqlite3.connect(self.status_manager.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT project_id, project_name, template_name, current_phase, status, updated_at
            FROM project_status
            ORDER BY updated_at DESC
        """
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "project_id": row[0],
                "project_name": row[1],
                "template_name": row[2],
                "current_phase": row[3],
                "status": row[4],
                "updated_at": row[5],
            }
            for row in rows
        ]


# CLI インターフェース
class ProjectTemplateCLI:
    """プロジェクトテンプレートCLI"""

    def __init__(self):
        """初期化メソッド"""
        self.system = ProjectTemplateSystem()

    def create_project(self, project_name: str, template_name: str) -> str:
        """プロジェクト作成"""
        try:
            project_id = self.system.create_project_from_template(
                project_name, template_name
            )
            print(f"✅ プロジェクト作成完了: {project_name}")
            print(f"   ID: {project_id}")
            print(f"   テンプレート: {template_name}")

            # 初期レポートを表示
            print("\n📋 初期状況レポート:")
            print(self.system.generate_status_report(project_id))

            return project_id

        except Exception as e:
            print(f"❌ エラー: {e}")
            return ""

    def show_project_status(self, project_id: str):
        """プロジェクト状況表示"""
        report = self.system.generate_status_report(project_id)
        print(report)

    def list_projects(self):
        """プロジェクト一覧表示"""
        projects = self.system.get_project_list()

        if not projects:
            print("📭 プロジェクトが見つかりません")
            return

        print("📋 プロジェクト一覧")
        print("=" * 80)
        print(
            f"{'ID':<20} {'名前':<30} {'テンプレート':<15} {'フェーズ':<20} {'状態':<10}"
        )
        print("-" * 80)

        for project in projects:
            print(
                f"{project['project_id']:<20} {project['project_name']:<30} "
                f"{project['template_name']:<15} {project['current_phase']:<20} "
                f"{project['status']:<10}"
            )

    def advance_project_phase(self, project_id: str):
        """フェーズ進行"""
        success = self.system.advance_phase(project_id)
        if success:
            print(f"✅ フェーズを進めました: {project_id}")
            print("\n📋 更新後の状況:")
            self.show_project_status(project_id)
        else:
            print(f"❌ フェーズの進行に失敗しました: {project_id}")

    def list_templates(self):
        """テンプレート一覧表示"""
        print("📋 利用可能なテンプレート")
        print("=" * 50)

        for name, template in self.system.templates.items():
            print(f"\n🎯 {name}")
            print(f"   説明: {template.description}")
            print(f"   フェーズ数: {len(template.phases)}")
            for i, phase in enumerate(template.phases):
                print(f"   Phase {i+1}: {phase['name']} ({phase['estimated_days']}日)")


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(
        description="🏛️ エルダーズギルド プロジェクトテンプレートシステム"
    )
    subparsers = parser.add_subparsers(dest="command", help="コマンド")

    # create コマンド
    create_parser = subparsers.add_parser("create", help="プロジェクト作成")
    create_parser.add_argument("project_name", help="プロジェクト名")
    create_parser.add_argument("template_name", help="テンプレート名")

    # status コマンド
    status_parser = subparsers.add_parser("status", help="プロジェクト状況表示")
    status_parser.add_argument("project_id", help="プロジェクトID")

    # list コマンド
    list_parser = subparsers.add_parser("list", help="プロジェクト一覧")

    # advance コマンド
    advance_parser = subparsers.add_parser("advance", help="フェーズ進行")
    advance_parser.add_argument("project_id", help="プロジェクトID")

    # templates コマンド
    templates_parser = subparsers.add_parser("templates", help="テンプレート一覧")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = ProjectTemplateCLI()

    if args.command == "create":
        cli.create_project(args.project_name, args.template_name)
    elif args.command == "status":
        cli.show_project_status(args.project_id)
    elif args.command == "list":
        cli.list_projects()
    elif args.command == "advance":
        cli.advance_project_phase(args.project_id)
    elif args.command == "templates":
        cli.list_templates()


if __name__ == "__main__":
    main()
