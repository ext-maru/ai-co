#!/usr/bin/env python3
"""
Elders Guild プロンプトテンプレートマネージャー
各ワーカー専用の最適化されたプロンプトを管理
"""

import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Template

sys.path.append(str(Path(__file__).parent.parent))

from core import EMOJI, BaseManager, get_config
from libs.rag_manager import RAGManager


class PromptTemplateManager(BaseManager):
    """プロンプトテンプレート管理マネージャー"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__("PromptTemplateManager")
        self.config = get_config()
        self.db_path = Path(self.config.get("prompt.db_path", "db/prompt_templates.db"))
        self.template_dir = Path(
            self.config.get("prompt.template_dir", "config/prompts")
        )
        self.rag_manager = RAGManager()
        self.jinja_env = None

    def initialize(self) -> bool:
        """マネージャーの初期化"""
        try:
            # ディレクトリ作成
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.template_dir.mkdir(parents=True, exist_ok=True)

            # データベース初期化
            self._init_database()

            # Jinja2環境設定
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )

            # デフォルトテンプレート作成
            self._create_default_templates()

            self.logger.info(f"{EMOJI['success']} PromptTemplateManager initialized")
            return True

        except Exception as e:
            self.handle_error(e, "initialize")
            return False

    def _init_database(self):
        """データベース初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS prompt_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    worker_type TEXT NOT NULL,
                    template_name TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    template_content TEXT NOT NULL,
                    variables TEXT,  -- JSON形式の変数定義
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'system',
                    hash TEXT UNIQUE,
                    UNIQUE(worker_type, template_name, version)
                );

                CREATE TABLE IF NOT EXISTS prompt_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    worker_type TEXT NOT NULL,
                    template_name TEXT NOT NULL,
                    generated_prompt TEXT NOT NULL,
                    variables_used TEXT,  -- JSON形式
                    task_id TEXT,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    performance_score REAL  -- 0-1のスコア（後で評価）
                );

                CREATE INDEX IF NOT EXISTS idx_worker_template
                ON prompt_templates(worker_type, template_name, is_active);

                CREATE INDEX IF NOT EXISTS idx_history_task
                ON prompt_history(task_id);
            """
            )

    def _create_default_templates(self):
        """デフォルトテンプレートの作成"""
        default_templates = {
            "task": {
                "default": {
                    "content": """You are TaskWorker, an AI assistant that executes specific tasks.

Task Type: {{ task_type }}
Task ID: {{ task_id }}

User Request:
{{ user_prompt }}

{% if rag_context %}
Relevant Past Tasks:
{{ rag_context }}
{% endif %}

Instructions:
1. Understand the user's request completely
2. Implement a complete solution
3. Use FileSystem tools to create all necessary files
4. Ensure the code is immediately executable
5. Include error handling and logging
6. Follow Elders Guild coding standards

{{ additional_instructions }}

You have permission to use all tools including Edit, Write, and FileSystem.
Please proceed with the task without asking for permissions.""",
                    "variables": [
                        "task_type",
                        "task_id",
                        "user_prompt",
                        "rag_context",
                        "additional_instructions",
                    ],
                    "description": "Default template for task worker",
                },
                "code_generation": {
                    "content": """You are specialized in code generation tasks.

Task: Generate code for the following requirement
Task ID: {{ task_id }}

Requirement:
{{ user_prompt }}

{% if language %}
Target Language: {{ language }}
{% endif %}

{% if rag_context %}
Similar Past Implementations:
{{ rag_context }}
{% endif %}

Guidelines:
- Write clean, efficient, and well-documented code
- Include comprehensive error handling
- Follow best practices for {{ language if language else "the appropriate language" }}
- Create complete, runnable solutions
- Use Elders Guild's Core modules where applicable

{{ additional_instructions }}""",
                    "variables": [
                        "task_id",
                        "user_prompt",
                        "language",
                        "rag_context",
                        "additional_instructions",
                    ],
                    "description": "Specialized template for code generation",
                },
            },
            "pm": {
                "default": {
                    "content": """You are PMWorker, responsible for project management and file organization.

Task: Organize and manage the following deliverables
Task ID: {{ task_id }}

Files to Process:
{{ file_list }}

Project Structure:
{{ project_structure }}

Instructions:
1. Analyze the files and determine appropriate placement
2. Follow Elders Guild's file organization rules
3. Create necessary directories
4. Move files to their correct locations
5. Update any import paths if needed
6. Commit changes to Git with appropriate messages

Git Flow Rules:
- Work on auto/{{ task_id }} branch
- Commit with emoji prefixes
- Auto-merge to develop when complete

{{ additional_instructions }}""",
                    "variables": [
                        "task_id",
                        "file_list",
                        "project_structure",
                        "additional_instructions",
                    ],
                    "description": "Default template for PM worker",
                }
            },
            "dialog": {
                "default": {
                    "content": """You are DialogWorker, handling interactive conversations.

Conversation ID: {{ conversation_id }}
Current Turn: {{ turn_number }}

Conversation History:
{{ conversation_history }}

User's Latest Input:
{{ user_input }}

Context:
{{ context }}

Instructions:
1. Maintain conversation continuity
2. Ask clarifying questions when needed
3. Provide helpful and accurate responses
4. Remember previous context
5. Guide the user towards actionable outcomes

{{ additional_instructions }}""",
                    "variables": [
                        "conversation_id",
                        "turn_number",
                        "conversation_history",
                        "user_input",
                        "context",
                        "additional_instructions",
                    ],
                    "description": "Default template for dialog worker",
                }
            },
            "slack": {
                "default": {
                    "content": """You are SlackWorker, monitoring and responding to Slack messages.

Channel: {{ channel }}
User: {{ user }}
Message: {{ message }}

Recent Channel Context:
{{ channel_context }}

Instructions:
1. Determine if this message requires Elders Guild action
2. Extract the user's intent clearly
3. Route to appropriate worker if action needed
4. Respond professionally and helpfully
5. Use appropriate Slack formatting

Response Format:
- Be concise and clear
- Use emoji for visual clarity
- Include relevant links or references

{{ additional_instructions }}""",
                    "variables": [
                        "channel",
                        "user",
                        "message",
                        "channel_context",
                        "additional_instructions",
                    ],
                    "description": "Default template for Slack worker",
                }
            },
        }

        # データベースに保存
        for worker_type, templates in default_templates.items():
            for template_name, template_data in templates.items():
                self.create_template(
                    worker_type=worker_type,
                    template_name=template_name,
                    template_content=template_data["content"],
                    variables=template_data["variables"],
                    description=template_data["description"],
                )

    def create_template(
        self,
        worker_type: str,
        template_name: str,
        template_content: str,
        variables: List[str] = None,
        description: str = None,
    ) -> bool:
        """新しいテンプレートを作成"""
        try:
            # コンテンツのハッシュ生成
            content_hash = hashlib.sha256(
                f"{worker_type}:{template_name}:{template_content}".encode()
            ).hexdigest()

            with sqlite3.connect(self.db_path) as conn:
                # 既存のアクティブなテンプレートを非アクティブ化
                conn.execute(
                    """
                    UPDATE prompt_templates
                    SET is_active = 0
                    WHERE worker_type = ? AND template_name = ? AND is_active = 1
                """,
                    (worker_type, template_name),
                )

                # 新しいバージョンを取得
                result = conn.execute(
                    """
                    SELECT MAX(version) FROM prompt_templates
                    WHERE worker_type = ? AND template_name = ?
                """,
                    (worker_type, template_name),
                ).fetchone()

                new_version = (result[0] or 0) + 1

                # 新しいテンプレートを挿入
                conn.execute(
                    """
                    INSERT INTO prompt_templates
                    (worker_type, template_name, version, template_content,
                     variables, description, hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        worker_type,
                        template_name,
                        new_version,
                        template_content,
                        json.dumps(variables) if variables else None,
                        description,
                        content_hash,
                    ),
                )

                # ファイルにも保存
                self._save_template_file(worker_type, template_name, template_content)

                self.logger.info(
                    f"{EMOJI['success']} Created template: {worker_type}/{template_name} v{new_version}"
                )
                return True

        except sqlite3.IntegrityError:
            self.logger.warning(f"Template already exists with same content")
            return False
        except Exception as e:
            self.handle_error(e, "create_template")
            return False

    def _save_template_file(self, worker_type: str, template_name: str, content: str):
        """テンプレートをファイルに保存"""
        worker_dir = self.template_dir / worker_type
        worker_dir.mkdir(parents=True, exist_ok=True)

        template_file = worker_dir / f"{template_name}.j2"
        template_file.write_text(content)

    def get_template(
        self,
        worker_type: str,
        template_name: str = "default",
        version: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """テンプレートを取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if version:
                    # 特定バージョンを取得
                    cursor.execute(
                        """
                        SELECT * FROM prompt_templates
                        WHERE worker_type = ? AND template_name = ? AND version = ?
                    """,
                        (worker_type, template_name, version),
                    )
                else:
                    # アクティブなテンプレートを取得
                    cursor.execute(
                        """
                        SELECT * FROM prompt_templates
                        WHERE worker_type = ? AND template_name = ? AND is_active = 1
                        ORDER BY version DESC LIMIT 1
                    """,
                        (worker_type, template_name),
                    )

                result = cursor.fetchone()

                if result:
                    columns = [col[0] for col in cursor.description]
                    template_data = dict(zip(columns, result))

                    # 変数をパース
                    if template_data.get("variables"):
                        template_data["variables"] = json.loads(
                            template_data["variables"]
                        )

                    return template_data

                return None

        except Exception as e:
            self.handle_error(e, "get_template")
            return None

    def generate_prompt(
        self,
        worker_type: str,
        template_name: str = "default",
        variables: Dict[str, Any] = None,
        include_rag: bool = True,
    ) -> Optional[str]:
        """動的にプロンプトを生成"""
        try:
            # テンプレート取得
            template_data = self.get_template(worker_type, template_name)
            if not template_data:
                self.logger.error(f"Template not found: {worker_type}/{template_name}")
                return None

            # 変数の準備
            context_vars = variables or {}

            # RAGコンテキストの追加
            if include_rag and "user_prompt" in context_vars:
                rag_context = self._get_rag_context(
                    context_vars.get("user_prompt", ""), worker_type
                )
                if rag_context:
                    context_vars["rag_context"] = rag_context

            # 環境変数やシークレットの処理
            context_vars = self._process_secrets(context_vars)

            # Jinja2でレンダリング
            template = Template(template_data["template_content"])
            generated_prompt = template.render(**context_vars)

            # 履歴に記録
            self._record_prompt_history(
                worker_type,
                template_name,
                generated_prompt,
                context_vars,
                context_vars.get("task_id"),
            )

            return generated_prompt

        except Exception as e:
            self.handle_error(e, "generate_prompt")
            return None

    def _get_rag_context(self, user_prompt: str, worker_type: str) -> Optional[str]:
        """RAGコンテキストを取得"""
        try:
            # RAGManagerを使用して関連タスクを検索
            # get_related_historyメソッドを使用
            results = self.rag_manager.get_related_history(user_prompt, limit=3)

            if not results:
                return None

            # コンテキストを整形
            context_parts = []
            for result in results:
                # プロンプトを適切な長さに切り詰める
                prompt_text = result.get("prompt", "N/A")
                if len(prompt_text) > 100:
                    prompt_text = prompt_text[:100] + "..."

                context_parts.append(
                    f"Task: {prompt_text}\n"
                    f"Summary: {result.get('summary', 'N/A')}\n"
                    f"Status: {result.get('status', 'N/A')}"
                )

            return "\n\n".join(context_parts)

        except Exception as e:
            self.logger.warning(f"Failed to get RAG context: {e}")
            return None

    def _process_secrets(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """環境変数やシークレットを処理"""
        processed = variables.copy()

        # 環境変数のプレースホルダーを置換
        for key, value in processed.items():
            if (
                isinstance(value, str)
                and value.startswith("${")
                and value.endswith("}")
            ):
                env_var = value[2:-1]
                env_value = os.environ.get(env_var)
                if env_value:
                    processed[key] = env_value
                else:
                    self.logger.warning(f"Environment variable not found: {env_var}")
                    processed[key] = f"[MISSING: {env_var}]"

        return processed

    def _record_prompt_history(
        self,
        worker_type: str,
        template_name: str,
        generated_prompt: str,
        variables: Dict[str, Any],
        task_id: Optional[str] = None,
    ):
        """プロンプト生成履歴を記録"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO prompt_history
                    (worker_type, template_name, generated_prompt, variables_used, task_id)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        worker_type,
                        template_name,
                        generated_prompt,
                        json.dumps(variables),
                        task_id,
                    ),
                )
        except Exception as e:
            self.logger.warning(f"Failed to record prompt history: {e}")

    def update_template(
        self,
        worker_type: str,
        template_name: str,
        new_content: str,
        variables: List[str] = None,
        description: str = None,
    ) -> bool:
        """テンプレートを更新（新しいバージョンを作成）"""
        return self.create_template(
            worker_type, template_name, new_content, variables, description
        )

    def rollback_template(
        self, worker_type: str, template_name: str, target_version: int
    ) -> bool:
        """テンプレートを特定バージョンにロールバック"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 現在のアクティブを非アクティブ化
                conn.execute(
                    """
                    UPDATE prompt_templates
                    SET is_active = 0
                    WHERE worker_type = ? AND template_name = ? AND is_active = 1
                """,
                    (worker_type, template_name),
                )

                # 指定バージョンをアクティブ化
                result = conn.execute(
                    """
                    UPDATE prompt_templates
                    SET is_active = 1
                    WHERE worker_type = ? AND template_name = ? AND version = ?
                """,
                    (worker_type, template_name, target_version),
                )

                if result.rowcount > 0:
                    self.logger.info(
                        f"{EMOJI['success']} Rolled back {worker_type}/{template_name} to v{target_version}"
                    )
                    return True
                else:
                    self.logger.error(f"Version {target_version} not found")
                    return False

        except Exception as e:
            self.handle_error(e, "rollback_template")
            return False

    def list_templates(self, worker_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """テンプレート一覧を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if worker_type:
                    query = """
                        SELECT worker_type, template_name, version, description,
                               is_active, created_at, updated_at
                        FROM prompt_templates
                        WHERE worker_type = ?
                        ORDER BY worker_type, template_name, version DESC
                    """
                    results = conn.execute(query, (worker_type,)).fetchall()
                else:
                    query = """
                        SELECT worker_type, template_name, version, description,
                               is_active, created_at, updated_at
                        FROM prompt_templates
                        ORDER BY worker_type, template_name, version DESC
                    """
                    results = conn.execute(query).fetchall()

                templates = []
                for row in results:
                    templates.append(
                        {
                            "worker_type": row[0],
                            "template_name": row[1],
                            "version": row[2],
                            "description": row[3],
                            "is_active": bool(row[4]),
                            "created_at": row[5],
                            "updated_at": row[6],
                        }
                    )

                return templates

        except Exception as e:
            self.handle_error(e, "list_templates")
            return []

    def get_template_history(
        self, worker_type: str, template_name: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """テンプレートの使用履歴を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM prompt_history
                    WHERE worker_type = ? AND template_name = ?
                    ORDER BY generated_at DESC
                    LIMIT ?
                """,
                    (worker_type, template_name, limit),
                )

                results = cursor.fetchall()

                history = []
                columns = [col[0] for col in cursor.description]
                for row in results:
                    history_item = dict(zip(columns, row))
                    if history_item.get("variables_used"):
                        history_item["variables_used"] = json.loads(
                            history_item["variables_used"]
                        )
                    history.append(history_item)

                return history

        except Exception as e:
            self.handle_error(e, "get_template_history")
            return []

    def evaluate_prompt_performance(self, task_id: str, score: float) -> bool:
        """プロンプトのパフォーマンスを評価"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE prompt_history
                    SET performance_score = ?
                    WHERE task_id = ?
                """,
                    (score, task_id),
                )

                return True

        except Exception as e:
            self.handle_error(e, "evaluate_prompt_performance")
            return False

    def export_templates(self, output_dir: str) -> bool:
        """全テンプレートをエクスポート"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            templates = self.list_templates()

            # ワーカータイプごとにグループ化
            grouped = {}
            for template in templates:
                worker_type = template["worker_type"]
                if worker_type not in grouped:
                    grouped[worker_type] = []
                grouped[worker_type].append(template)

            # エクスポート
            for worker_type, worker_templates in grouped.items():
                worker_file = output_path / f"{worker_type}_templates.json"

                # 詳細データを含める
                export_data = []
                for template_info in worker_templates:
                    full_template = self.get_template(
                        template_info["worker_type"],
                        template_info["template_name"],
                        template_info["version"],
                    )
                    if full_template:
                        export_data.append(full_template)

                worker_file.write_text(json.dumps(export_data, indent=2))

            self.logger.info(f"{EMOJI['success']} Exported templates to {output_dir}")
            return True

        except Exception as e:
            self.handle_error(e, "export_templates")
            return False

    def import_templates(self, import_file: str) -> bool:
        """テンプレートをインポート"""
        try:
            import_path = Path(import_file)
            if not import_path.exists():
                self.logger.error(f"Import file not found: {import_file}")
                return False

            with open(import_path, "r") as f:
                templates = json.load(f)

            imported_count = 0
            for template in templates:
                success = self.create_template(
                    worker_type=template["worker_type"],
                    template_name=template["template_name"],
                    template_content=template["template_content"],
                    variables=template.get("variables"),
                    description=template.get("description"),
                )
                if success:
                    imported_count += 1

            self.logger.info(
                f"{EMOJI['success']} Imported {imported_count}/{len(templates)} templates"
            )
            return True

        except Exception as e:
            self.handle_error(e, "import_templates")
            return False


# 使用例
if __name__ == "__main__":
    # マネージャー初期化
    manager = PromptTemplateManager()
    if manager.initialize():
        # テンプレート一覧表示
        print("\n=== Available Templates ===")
        templates = manager.list_templates()
        for template in templates:
            if template["is_active"]:
                print(
                    f"- {template['worker_type']}/{template['template_name']} "
                    f"v{template['version']} [ACTIVE]"
                )

        # プロンプト生成テスト
        print("\n=== Generate Prompt Test ===")
        prompt = manager.generate_prompt(
            worker_type="task",
            template_name="default",
            variables={
                "task_type": "code",
                "task_id": "test_001",
                "user_prompt": "Create a Python web scraper",
                "additional_instructions": "Use requests and BeautifulSoup",
            },
        )

        if prompt:
            print(f"Generated prompt:\n{prompt[:200]}...")
