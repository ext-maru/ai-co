#!/usr/bin/env python3
"""
タスクテンプレートシステム
よく使うタスクをテンプレート化して簡単に実行
"""

import json
import logging
import re
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class TaskTemplate:
    """タスクテンプレート"""

    template_id: str
    name: str
    description: str
    task_type: str
    worker_type: str
    template_data: Dict[str, Any]
    parameters: List[Dict[str, Any]]  # パラメータ定義
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    created_by: str
    is_public: bool = True
    usage_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskTemplate":
        """辞書から作成"""
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)


class TemplateParameter:
    """テンプレートパラメータの定義"""

    def __init__(
        """初期化メソッド"""
        self,
        name: str,
        param_type: str = None,
        type: str = None,
        description: str = "",
        default: Any = None,
        required: bool = True,
        choices: Optional[List[Any]] = None,
        validation: Optional[str] = None,
    ):
        # 後方互換性のため、typeとparam_typeの両方を受け入れる
        self.name = name
        self.param_type = param_type or type or "string"
        self.description = description
        self.default = default
        self.required = required
        self.choices = choices
        self.validation = validation  # 正規表現パターン

    def validate(self, value: Any) -> bool:
        """値の検証"""
        # 必須チェック
        if self.required and value is None:
            return False

        # 型チェック
        type_map = {
            "string": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "date": str,  # dateも文字列として扱う
        }

        expected_type = type_map.get(self.param_type)
        if expected_type and value is not None and not isinstance(value, expected_type):
            return False

        # 選択肢チェック
        if self.choices and value not in self.choices:
            return False

        # 正規表現チェック
        if self.validation and isinstance(value, str):
            if not re.match(self.validation, value):
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "name": self.name,
            "param_type": self.param_type,  # param_typeを使用
            "description": self.description,
            "default": self.default,
            "required": self.required,
            "choices": self.choices,
            "validation": self.validation,
        }


class TaskTemplateManager:
    """タスクテンプレート管理"""

    def __init__(
        """初期化メソッド"""
        self, db_path: Optional[Path] = None, template_dir: Optional[Path] = None
    ):
        self.db_path = db_path or Path("/home/aicompany/ai_co/db/templates.db")
        self.template_dir = template_dir or Path("/home/aicompany/ai_co/templates")
        self.logger = logging.getLogger(__name__)

        # ディレクトリ作成
        self.db_path.parent.mkdir(exist_ok=True)
        self.template_dir.mkdir(exist_ok=True)

        # データベース初期化
        self._init_db()

        # 組み込みテンプレートをロード
        self._load_builtin_templates()

    def _init_db(self):
        """データベース初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS templates (
                    template_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    task_type TEXT NOT NULL,
                    worker_type TEXT NOT NULL,
                    template_data TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    tags TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    created_by TEXT,
                    is_public INTEGER DEFAULT 1,
                    usage_count INTEGER DEFAULT 0
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS template_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_id TEXT NOT NULL,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    parameters_used TEXT,
                    task_id TEXT,
                    FOREIGN KEY (template_id) REFERENCES templates(template_id)
                )
            """
            )

    def _load_builtin_templates(self):
        """組み込みテンプレートをロード"""
        builtin_templates = [
            {
                "template_id": "daily_report",
                "name": "Daily Report Generator",
                "description": "Generate daily report with statistics",
                "task_type": "code",
                "worker_type": "task",
                "template_data": {
                    "prompt": "Generate a daily report for {{date}} including:\n"
                    "- Task completion statistics\n"
                    "- System performance metrics\n"
                    "- Error summary\n"
                    "Format as markdown."
                },
                "parameters": [
                    TemplateParameter(
                        "date",
                        param_type="date",
                        description="Report date",
                        default="today",
                    ).to_dict()
                ],
            },
            {
                "template_id": "code_review",
                "name": "Code Review Assistant",
                "description": "Perform code review on specified file",
                "task_type": "code",
                "worker_type": "task",
                "template_data": {
                    "prompt": "Review the code in {{file_path}} and provide:\n"
                    "- Code quality assessment\n"
                    "- Security vulnerabilities\n"
                    "- Performance suggestions\n"
                    "- Best practices compliance"
                },
                "parameters": [
                    TemplateParameter(
                        "file_path",
                        param_type="string",
                        description="Path to file",
                        required=True,
                    ).to_dict()
                ],
            },
            {
                "template_id": "api_client",
                "name": "API Client Generator",
                "description": "Generate API client code",
                "task_type": "code",
                "worker_type": "task",
                "template_data": {
                    "prompt": "Create a {{language}} API client for:\n"
                    "Base URL: {{base_url}}\n"
                    "Authentication: {{auth_type}}\n"
                    "Include methods for: {{endpoints}}"
                },
                "parameters": [
                    TemplateParameter(
                        "language",
                        param_type="string",
                        description="Programming language",
                        choices=["python", "javascript", "go"],
                        default="python",
                    ).to_dict(),
                    TemplateParameter(
                        "base_url",
                        param_type="string",
                        description="API base URL",
                        required=True,
                    ).to_dict(),
                    TemplateParameter(
                        "auth_type",
                        param_type="string",
                        description="Authentication type",
                        choices=["none", "api_key", "oauth2"],
                        default="api_key",
                    ).to_dict(),
                    TemplateParameter(
                        "endpoints",
                        param_type="list",
                        description="API endpoints",
                        default=[],
                    ).to_dict(),
                ],
            },
            {
                "template_id": "data_analysis",
                "name": "Data Analysis Pipeline",
                "description": "Analyze data and generate insights",
                "task_type": "code",
                "worker_type": "task",
                "template_data": {
                    "prompt": "Analyze the data in {{data_source}} and:\n"
                    "- Generate summary statistics\n"
                    "- Identify patterns and anomalies\n"
                    "- Create visualizations\n"
                    "- Provide actionable insights\n"
                    "Output format: {{output_format}}"
                },
                "parameters": [
                    TemplateParameter(
                        "data_source",
                        param_type="string",
                        description="Data source path",
                        required=True,
                    ).to_dict(),
                    TemplateParameter(
                        "output_format",
                        param_type="string",
                        description="Output format",
                        choices=["markdown", "html", "pdf"],
                        default="markdown",
                    ).to_dict(),
                ],
            },
        ]

        # 組み込みテンプレートを登録
        for template_data in builtin_templates:
            try:
                template = TaskTemplate(
                    template_id=template_data["template_id"],
                    name=template_data["name"],
                    description=template_data["description"],
                    task_type=template_data["task_type"],
                    worker_type=template_data["worker_type"],
                    template_data=template_data["template_data"],
                    parameters=template_data["parameters"],
                    tags=template_data.get("tags", []),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    is_public=True,
                )

                # 既に存在しない場合のみ保存
                if not self.get_template(template.template_id):
                    self.save_template(template)

            except Exception as e:
                self.logger.error(f"Failed to load builtin template: {str(e)}")

    def create_template(
        self,
        name: str,
        task_type: str,
        template_data: Dict[str, Any],
        parameters: List[Dict[str, Any]],
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> TaskTemplate:
        """テンプレートを作成"""
        template = TaskTemplate(
            template_id=name.lower().replace(" ", "_"),
            name=name,
            description=description,
            task_type=task_type,
            worker_type="task",  # デフォルト
            template_data=template_data,
            parameters=parameters,
            tags=tags or [],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="user",
            is_public=True,
        )

        self.save_template(template)
        return template

    def save_template(self, template: TaskTemplate):
        """テンプレートを保存"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO templates
                (template_id, name, description, task_type, worker_type,
                 template_data, parameters, tags, created_at, updated_at,
                 created_by, is_public, usage_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    template.template_id,
                    template.name,
                    template.description,
                    template.task_type,
                    template.worker_type,
                    json.dumps(template.template_data),
                    json.dumps(template.parameters),
                    json.dumps(template.tags),
                    template.created_at.isoformat(),
                    template.updated_at.isoformat(),
                    template.created_by,
                    1 if template.is_public else 0,
                    template.usage_count,
                ),
            )

    def get_template(self, template_id: str) -> Optional[TaskTemplate]:
        """テンプレートを取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM templates WHERE template_id = ?
            """,
                (template_id,),
            )

            row = cursor.fetchone()
            if row:
                return TaskTemplate(
                    template_id=row[0],
                    name=row[1],
                    description=row[2],
                    task_type=row[3],
                    worker_type=row[4],
                    template_data=json.loads(row[5]),
                    parameters=json.loads(row[6]),
                    tags=json.loads(row[7]),
                    created_at=datetime.fromisoformat(row[8]),
                    updated_at=datetime.fromisoformat(row[9]),
                    created_by=row[10],
                    is_public=bool(row[11]),
                    usage_count=row[12],
                )

        return None

    def list_templates(self, tags: Optional[List[str]] = None) -> List[TaskTemplate]:
        """テンプレート一覧を取得"""
        templates = []

        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM templates WHERE is_public = 1"

            cursor = conn.execute(query)
            for row in cursor.fetchall():
                template = TaskTemplate(
                    template_id=row[0],
                    name=row[1],
                    description=row[2],
                    task_type=row[3],
                    worker_type=row[4],
                    template_data=json.loads(row[5]),
                    parameters=json.loads(row[6]),
                    tags=json.loads(row[7]),
                    created_at=datetime.fromisoformat(row[8]),
                    updated_at=datetime.fromisoformat(row[9]),
                    created_by=row[10],
                    is_public=bool(row[11]),
                    usage_count=row[12],
                )

                # タグフィルタリング
                if tags:
                    if any(tag in template.tags for tag in tags):
                        templates.append(template)
                else:
                    templates.append(template)

        return templates

    def render_template(
        self, template_id: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """テンプレートをレンダリング"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        # パラメータ検証
        for param_def in template.parameters:
            param_name = param_def["name"]
            # typeとparam_typeの両方をサポート
            param_type = param_def.get("param_type") or param_def.get("type", "string")
            param_obj = TemplateParameter(
                name=param_name,
                param_type=param_type,
                description=param_def.get("description", ""),
                default=param_def.get("default"),
                required=param_def.get("required", True),
                choices=param_def.get("choices"),
                validation=param_def.get("validation"),
            )

            # デフォルト値を適用
            if param_name not in parameters and param_obj.default is not None:
                parameters[param_name] = param_obj.default

            # 検証
            if not param_obj.validate(parameters.get(param_name)):
                raise ValueError(f"Invalid parameter: {param_name}")

        # テンプレートレンダリング
        rendered_data = {}
        for key, value in template.template_data.items():
            if isinstance(value, str):
                # {{param}}形式の置換
                rendered_value = value
                for param_name, param_value in parameters.items():
                    rendered_value = rendered_value.replace(
                        f"{{{{{param_name}}}}}", str(param_value)
                    )
                rendered_data[key] = rendered_value
            else:
                rendered_data[key] = value

        # 使用回数を更新
        self._record_usage(template_id, parameters)

        return {
            "task_type": template.task_type,
            "worker_type": template.worker_type,
            **rendered_data,
        }

    def _record_usage(self, template_id: str, parameters: Dict[str, Any]):
        """使用履歴を記録"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO template_usage (template_id, parameters_used)
                VALUES (?, ?)
            """,
                (template_id, json.dumps(parameters)),
            )

            conn.execute(
                """
                UPDATE templates
                SET usage_count = usage_count + 1
                WHERE template_id = ?
            """,
                (template_id,),
            )

    def get_popular_templates(self, limit: int = 10) -> List[TaskTemplate]:
        """人気のテンプレートを取得"""
        templates = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM templates
                WHERE is_public = 1
                ORDER BY usage_count DESC
                LIMIT ?
            """,
                (limit,),
            )

            for row in cursor.fetchall():
                template = TaskTemplate(
                    template_id=row[0],
                    name=row[1],
                    description=row[2],
                    task_type=row[3],
                    worker_type=row[4],
                    template_data=json.loads(row[5]),
                    parameters=json.loads(row[6]),
                    tags=json.loads(row[7]),
                    created_at=datetime.fromisoformat(row[8]),
                    updated_at=datetime.fromisoformat(row[9]),
                    created_by=row[10],
                    is_public=bool(row[11]),
                    usage_count=row[12],
                )
                templates.append(template)

        return templates

    def export_template(self, template_id: str, format: str = "yaml") -> str:
        """テンプレートをエクスポート"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        if format == "yaml":
            return yaml.dump(template.to_dict(), default_flow_style=False)
        elif format == "json":
            return json.dumps(template.to_dict(), indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def import_template(self, content: str, format: str = "yaml") -> TaskTemplate:
        """テンプレートをインポート"""
        if format == "yaml":
            data = yaml.safe_load(content)
        elif format == "json":
            data = json.loads(content)
        else:
            raise ValueError(f"Unsupported format: {format}")

        template = TaskTemplate.from_dict(data)
        self.save_template(template)

        return template
