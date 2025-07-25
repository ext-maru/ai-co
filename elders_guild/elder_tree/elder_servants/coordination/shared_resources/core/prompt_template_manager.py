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

sys.path.append(str(Path(__file__).parent.parent))

from core import EMOJI, BaseManager, get_config
from libs.rag_manager import RAGManager

    """プロンプトテンプレート管理マネージャー"""

    def __init__(self):
        """初期化メソッド"""

        self.config = get_config()

        )
        self.rag_manager = RAGManager()
        self.jinja_env = None

    def initialize(self) -> bool:
        """マネージャーの初期化"""
        try:
            # ディレクトリ作成
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # データベース初期化
            self._init_database()

            # Jinja2環境設定
            self.jinja_env = Environment(

                trim_blocks=True,
                lstrip_blocks=True,
            )

            # デフォルトテンプレート作成

            return True

        except Exception as e:
            self.handle_error(e, "initialize")
            return False

    def _init_database(self):
        """データベース初期化"""
        with sqlite3connect(self.db_path) as conn:
            conn.executescript(
                """

                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    worker_type TEXT NOT NULL,

                    version INTEGER NOT NULL DEFAULT 1,

                    variables TEXT,  -- JSON形式の変数定義
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'system',
                    hash TEXT UNIQUE,

                );

                CREATE TABLE IF NOT EXISTS prompt_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    worker_type TEXT NOT NULL,

                    generated_prompt TEXT NOT NULL,
                    variables_used TEXT,  -- JSON形式
                    task_id TEXT,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    performance_score REAL  -- 0-1のスコア（後で評価）
                );

                CREATE INDEX IF NOT EXISTS idx_history_task
                ON prompt_history(task_id);
            """
            )

        """デフォルトテンプレートの作成"""

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
1.0 Understand the user's request completely
2.0 Implement a complete solution
3.0 Use FileSystem tools to create all necessary files
4.0 Ensure the code is immediately executable
5.0 Include error handling and logging
6.0 Follow Elders Guild coding standards

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
1.0 Analyze the files and determine appropriate placement
2.0 Follow Elders Guild's file organization rules
3.0 Create necessary directories
4.0 Move files to their correct locations
5.0 Update any import paths if needed
6.0 Commit changes to Git with appropriate messages

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
1.0 Maintain conversation continuity
2.0 Ask clarifying questions when needed
3.0 Provide helpful and accurate responses
4.0 Remember previous context
5.0 Guide the user towards actionable outcomes

{{ additional_instructions }}""",
                    "variables": [
                        "conversation_id",
                        "turn_number",
                        "conversation_history",
                        "user_input",
                        "context",
                        "additional_instructions",
                    ],

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
1.0 Determine if this message requires Elders Guild action
2.0 Extract the user's intent clearly
3.0 Route to appropriate worker if action needed
4.0 Respond professionally and helpfully
5.0 Use appropriate Slack formatting

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

                }
            },
        }

        # データベースに保存

                    worker_type=worker_type,

                )

        self,
        worker_type: str,

        variables: List[str] = None,
        description: str = None,
    ) -> bool:
        """新しいテンプレートを作成"""
        try:
            # コンテンツのハッシュ生成
            content_hash = hashlib.sha256(

            ).hexdigest()

            with sqlite3connect(self.db_path) as conn:
                # 既存のアクティブなテンプレートを非アクティブ化
                conn.execute(
                    """

                    SET is_active = 0

                """,

                )

                # 新しいバージョンを取得
                result = conn.execute(
                    """

                """,

                ).fetchone()

                new_version = (result[0] or 0) + 1

                # 新しいテンプレートを挿入
                conn.execute(
                    """

                     variables, description, hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        worker_type,

                        new_version,

                        json.dumps(variables) if variables else None,
                        description,
                        content_hash,
                    ),
                )

                # ファイルにも保存

                self.logger.info(

                )
                return True

        except sqlite3IntegrityError:

            return False
        except Exception as e:

            return False

        """テンプレートをファイルに保存"""

        worker_dir.mkdir(parents=True, exist_ok=True)

        self,
        worker_type: str,

        version: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """テンプレートを取得"""
        try:
            with sqlite3connect(self.db_path) as conn:
                cursor = conn.cursor()

                if version:
                    # 特定バージョンを取得
                    cursor.execute(
                        """

                    """,

                    )
                else:
                    # アクティブなテンプレートを取得
                    cursor.execute(
                        """

                        ORDER BY version DESC LIMIT 1
                    """,

                    )

                result = cursor.fetchone()

                if result:
                    columns = [col[0] for col in cursor.description]

                    # 変数をパース

                        )

                return None

        except Exception as e:

            return None

    def generate_prompt(
        self,
        worker_type: str,

        variables: Dict[str, Any] = None,
        include_rag: bool = True,
    ) -> Optional[str]:
        """動的にプロンプトを生成"""
        try:
            # テンプレート取得

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

            # 履歴に記録
            self._record_prompt_history(
                worker_type,

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

        generated_prompt: str,
        variables: Dict[str, Any],
        task_id: Optional[str] = None,
    ):
        """プロンプト生成履歴を記録"""
        try:
            with sqlite3connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO prompt_history

                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        worker_type,

                        generated_prompt,
                        json.dumps(variables),
                        task_id,
                    ),
                )
        except Exception as e:
            self.logger.warning(f"Failed to record prompt history: {e}")

        self,
        worker_type: str,

        new_content: str,
        variables: List[str] = None,
        description: str = None,
    ) -> bool:
        """テンプレートを更新（新しいバージョンを作成）"""

        )

    ) -> bool:
        """テンプレートを特定バージョンにロールバック"""
        try:
            with sqlite3connect(self.db_path) as conn:
                # 現在のアクティブを非アクティブ化
                conn.execute(
                    """

                    SET is_active = 0

                """,

                )

                # 指定バージョンをアクティブ化
                result = conn.execute(
                    """

                    SET is_active = 1

                """,

                )

                if result.rowcount > 0:
                    self.logger.info(

                    )
                    return True
                else:
                    self.logger.error(f"Version {target_version} not found")
                    return False

        except Exception as e:

            return False

        """テンプレート一覧を取得"""
        try:
            with sqlite3connect(self.db_path) as conn:
                if worker_type:
                    query = """

                               is_active, created_at, updated_at

                        WHERE worker_type = ?

                    """
                    results = conn.execute(query, (worker_type,)).fetchall()
                else:
                    query = """

                               is_active, created_at, updated_at

                    """
                    results = conn.execute(query).fetchall()

                for row in results:

                        {
                            "worker_type": row[0],

                            "version": row[2],
                            "description": row[3],
                            "is_active": bool(row[4]),
                            "created_at": row[5],
                            "updated_at": row[6],
                        }
                    )

        except Exception as e:

            return []

    ) -> List[Dict[str, Any]]:
        """テンプレートの使用履歴を取得"""
        try:
            with sqlite3connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM prompt_history

                    ORDER BY generated_at DESC
                    LIMIT ?
                """,

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

            return []

    def evaluate_prompt_performance(self, task_id: str, score: float) -> bool:
        """プロンプトのパフォーマンスを評価"""
        try:
            with sqlite3connect(self.db_path) as conn:
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

        """全テンプレートをエクスポート"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # ワーカータイプごとにグループ化
            grouped = {}

                if worker_type not in grouped:
                    grouped[worker_type] = []

            # エクスポート

                # 詳細データを含める
                export_data = []

                    )

                worker_file.write_text(json.dumps(export_data, indent=2))

            return True

        except Exception as e:

            return False

        """テンプレートをインポート"""
        try:
            import_path = Path(import_file)
            if not import_path.exists():
                self.logger.error(f"Import file not found: {import_file}")
                return False

            with open(import_path, "r") as f:

            imported_count = 0

                )
                if success:
                    imported_count += 1

            self.logger.info(

            )
            return True

        except Exception as e:

            return False

# 使用例
if __name__ == "__main__":
    # マネージャー初期化

    if manager.initialize():
        # テンプレート一覧表示

                print(

                )

        # プロンプト生成テスト
        print("\n=== Generate Prompt Test ===")
        prompt = manager.generate_prompt(
            worker_type="task",

            variables={
                "task_type": "code",
                "task_id": "test_001",
                "user_prompt": "Create a Python web scraper",
                "additional_instructions": "Use requests and BeautifulSoup",
            },
        )

        if prompt:
            print(f"Generated prompt:\n{prompt[:200]}...")
