#!/usr/bin/env python3
"""
🏛️ プロジェクト自動化エンジン
テンプレートに従って自動的にプロジェクトを進行する
"""

import json
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.project_template_system import ProjectTemplateSystem

logger = logging.getLogger(__name__)


class ProjectAutomationEngine:
    """プロジェクト自動化エンジン"""

    def __init__(self):
        """初期化メソッド"""
        self.template_system = ProjectTemplateSystem()
        self.automation_rules = self._load_automation_rules()

    def _load_automation_rules(self) -> Dict[str, Any]:
        """自動化ルールの読み込み"""
        return {
            "web_development": {
                "phase_1": {
                    "auto_create_files": [
                        "requirements.md",
                        "architecture.md",
                        "database_schema.sql",
                        "tech_stack.md",
                    ],
                    "auto_commands": [
                        "mkdir -p docs/design",
                        "mkdir -p src",
                        "mkdir -p tests",
                        "touch .gitignore",
                    ],
                    "auto_templates": {
                        "requirements.md": "requirement_template",
                        "architecture.md": "architecture_template",
                    },
                },
                "phase_2": {
                    "auto_create_files": [
                        "src/auth/auth.py",
                        "src/database/models.py",
                        "src/api/main.py",
                        "frontend/package.json",
                    ],
                    "auto_commands": [
                        "python -m venv venv",
                        "pip install -r requirements.txt",
                        "npm init -y",
                    ],
                },
                "phase_3": {
                    "auto_create_files": [
                        "tests/test_auth.py",
                        "tests/test_api.py",
                        "src/core/business_logic.py",
                    ],
                    "auto_commands": ["pytest --cov=src tests/", "npm test"],
                },
                "phase_4": {
                    "auto_create_files": [
                        "Dockerfile",
                        "docker-compose.yml",
                        "deploy.sh",
                    ],
                    "auto_commands": ["docker build -t app .", "docker-compose up -d"],
                },
            },
            "ai_development": {
                "phase_1": {
                    "auto_create_files": [
                        "data_analysis.ipynb",
                        "problem_definition.md",
                        "dataset_info.md",
                    ],
                    "auto_commands": [
                        "mkdir -p data/raw",
                        "mkdir -p data/processed",
                        "mkdir -p notebooks",
                        "mkdir -p models",
                    ],
                },
                "phase_2": {
                    "auto_create_files": [
                        "src/model.py",
                        "src/preprocessing.py",
                        "src/training.py",
                        "requirements.txt",
                    ],
                    "auto_commands": [
                        "pip install pandas numpy scikit-learn",
                        "jupyter notebook --generate-config",
                    ],
                },
            },
        }

    def auto_execute_phase(
        self, project_id: str, execute_commands: bool = False
    ) -> Dict[str, Any]:
        """フェーズを自動実行"""
        context = self.template_system.get_project_context(project_id)

        if not context:
            return {"success": False, "error": "プロジェクトが見つかりません"}

        template_name = context["project_info"]["template_name"]
        phase_index = context["project_info"]["phase_index"]

        # フェーズ名を取得
        phase_key = f"phase_{phase_index + 1}"

        if template_name not in self.automation_rules:
            return {
                "success": False,
                "error": f"テンプレート {template_name} の自動化ルールが見つかりません",
            }

        phase_rules = self.automation_rules[template_name].get(phase_key, {})

        results = {
            "success": True,
            "project_id": project_id,
            "phase": phase_key,
            "actions_taken": [],
            "files_created": [],
            "commands_executed": [],
        }

        # 1. ファイル自動作成
        if "auto_create_files" in phase_rules:
            for file_path in phase_rules["auto_create_files"]:
                self._create_project_file(
                    project_id, file_path, phase_rules.get("auto_templates", {})
                )
                results["files_created"].append(file_path)

        # 2. コマンド自動実行
        if execute_commands and "auto_commands" in phase_rules:
            for command in phase_rules["auto_commands"]:
                try:
                    result = self._execute_command(project_id, command)
                    results["commands_executed"].append(
                        {
                            "command": command,
                            "success": result["success"],
                            "output": result.get("output", ""),
                        }
                    )
                except Exception as e:
                    results["commands_executed"].append(
                        {"command": command, "success": False, "error": str(e)}
                    )

        # 3. チェックリスト自動生成
        checklist_updates = self._generate_checklist_updates(template_name, phase_key)
        if checklist_updates:
            results["checklist_updated"] = checklist_updates

        return results

    def _create_project_file(
        self, project_id: str, file_path: str, templates: Dict[str, str]
    ):
        """プロジェクトファイルを自動作成"""
        project_dir = Path(f"projects/{project_id}")
        project_dir.mkdir(parents=True, exist_ok=True)

        full_path = project_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # テンプレートがある場合は適用
        template_name = templates.get(Path(file_path).name)
        if template_name:
            content = self._get_file_template(template_name)
        else:
            content = self._get_default_content(file_path)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _execute_command(self, project_id: str, command: str) -> Dict[str, Any]:
        """コマンドを実行"""
        project_dir = Path(f"projects/{project_id}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "コマンドがタイムアウトしました"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_file_template(self, template_name: str) -> str:
        """ファイルテンプレートを取得"""
        templates = {
            "requirement_template": """# 要件定義書

## 1. プロジェクト概要
- プロジェクト名:
- 目的:
- 対象ユーザー:

## 2. 機能要件
### 2.1 必須機能
- [ ]

### 2.2 希望機能
- [ ]

## 3. 非機能要件
### 3.1 パフォーマンス
-

### 3.2 セキュリティ
-

## 4. 制約事項
-

## 5. 受け入れ条件
- [ ]
""",
            "architecture_template": """# アーキテクチャ設計書

## 1. システム概要
- アーキテクチャパターン:
- 主要技術:

## 2. システム構成
### 2.1 フロントエンド
- フレームワーク:
- 言語:

### 2.2 バックエンド
- フレームワーク:
- 言語:

### 2.3 データベース
- DBMS:
- 設計方針:

## 3. API設計
### 3.1 エンドポイント
- GET /api/
- POST /api/

## 4. デプロイメント
- インフラ:
- CI/CD:
""",
        }

        return templates.get(
            template_name, f"# {template_name}\n\n# TODO: 内容を記述してください\n"
        )

    def _get_default_content(self, file_path: str) -> str:
        """デフォルトファイル内容を生成"""
        file_ext = Path(file_path).suffix.lower()

        if file_ext == ".py":
            return f'''#!/usr/bin/env python3
"""
{Path(file_path).stem}
"""

# TODO: 実装してください
'''
        elif file_ext == ".md":
            return f"""# {Path(file_path).stem}

## 概要

TODO: 内容を記述してください

## 詳細

"""
        elif file_ext == ".sql":
            return f"""-- {Path(file_path).stem}
-- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

-- TODO: SQLを記述してください
"""
        elif file_ext == ".json":
            return json.dumps(
                {
                    "name": Path(file_path).stem,
                    "created": datetime.now().isoformat(),
                    "description": "TODO: 設定を記述してください",
                },
                indent=2,
            )
        else:
                        return f"# {Path(file_path).name}\n# Created: { \
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n# TODO: 内容を記述してください\n"

    def _generate_checklist_updates(
        self, template_name: str, phase_key: str
    ) -> List[str]:
        """チェックリスト更新を生成"""
        updates = []

        if template_name == "web_development":
            if phase_key == "phase_2":
                updates.extend(
                    [
                        "認証システムの基本実装完了",
                        "データベースマイグレーション実行",
                        "API基盤の動作確認",
                    ]
                )
            elif phase_key == "phase_3":
                updates.extend(
                    [
                        "ユニットテストの実装",
                        "統合テストの実行",
                        "コードカバレッジ80%以上",
                    ]
                )

        return updates

    def generate_automation_plan(self, project_id: str) -> Dict[str, Any]:
        """自動化計画を生成"""
        context = self.template_system.get_project_context(project_id)

        if not context:
            return {"success": False, "error": "プロジェクトが見つかりません"}

        template_name = context["project_info"]["template_name"]
        current_phase = context["project_info"]["phase_index"]

        plan = {
            "project_id": project_id,
            "template_name": template_name,
            "automation_available": template_name in self.automation_rules,
            "phases": [],
        }

        if template_name in self.automation_rules:
            template_rules = self.automation_rules[template_name]

            for phase_key, phase_rules in template_rules.items():
                phase_plan = {
                    "phase": phase_key,
                    "files_to_create": phase_rules.get("auto_create_files", []),
                    "commands_to_execute": phase_rules.get("auto_commands", []),
                    "estimated_time": _estimate_phase_time(phase_rules),
                }
                plan["phases"].append(phase_plan)

        return plan


def _estimate_phase_time(phase_rules: Dict[str, Any]) -> str:
    """フェーズ実行時間を推定"""
    file_count = len(phase_rules.get("auto_create_files", []))
    command_count = len(phase_rules.get("auto_commands", []))

    # 簡単な時間推定
    minutes = file_count * 2 + command_count * 5

    if minutes < 5:
        return "1-2分"
    elif minutes < 15:
        return "5-10分"
    elif minutes < 30:
        return "15-30分"
    else:
        return "30分以上"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="プロジェクト自動化エンジン")
    parser.add_argument("project_id", help="プロジェクトID")
    parser.add_argument("--execute", action="store_true", help="コマンドを実際に実行")
    parser.add_argument("--plan", action="store_true", help="自動化計画を表示")

    args = parser.parse_args()

    engine = ProjectAutomationEngine()

    if args.plan:
        plan = engine.generate_automation_plan(args.project_id)
        print(json.dumps(plan, indent=2, ensure_ascii=False))
    else:
        result = engine.auto_execute_phase(args.project_id, args.execute)
        print(json.dumps(result, indent=2, ensure_ascii=False))
