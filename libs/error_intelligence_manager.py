#!/usr/bin/env python3
"""
エラー智能判断マネージャー
エラーパターンの学習、分類、修正戦略の提案を行う
"""

import json
import logging
import re
import sqlite3

# プロジェクトルートをPythonパスに追加
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseManager


class ErrorIntelligenceManager(BaseManager):
    """エラー智能判断を行うマネージャー"""

    def __init__(self):
        super().__init__("ErrorIntelligenceManager")
        self.db_path = PROJECT_ROOT / "db" / "error_patterns.db"
        self.patterns_cache = {}
        self.initialize()

        # エラーパターン定義
        self.error_patterns = {
            "import_error": {
                "regex": r"(ModuleNotFoundError|ImportError).*'(\w+)'",
                "category": "dependency",
                "severity": "medium",
                "auto_fix": True,
            },
            "syntax_error": {
                "regex": r"SyntaxError: (.+)",
                "category": "syntax",
                "severity": "high",
                "auto_fix": True,  # 安全なパターンのみ自動修正可能
            },
            "connection_error": {
                "regex": r"(ConnectionError|ConnectionRefusedError|TimeoutError)",
                "category": "network",
                "severity": "low",
                "auto_fix": True,
            },
            "permission_error": {
                "regex": r"(PermissionError|Permission denied)",
                "category": "permission",
                "severity": "medium",
                "auto_fix": True,
            },
            "file_not_found": {
                "regex": r"(FileNotFoundError|No such file or directory).*'(.+)'",
                "category": "filesystem",
                "severity": "medium",
                "auto_fix": True,
            },
            "type_error": {
                "regex": r"TypeError: (.+)",
                "category": "type",
                "severity": "medium",
                "auto_fix": False,
            },
            "value_error": {
                "regex": r"ValueError: (.+)",
                "category": "value",
                "severity": "low",
                "auto_fix": False,
            },
            "rabbitmq_error": {
                "regex": r"(AMQPConnectionError|pika\.exceptions)",
                "category": "rabbitmq",
                "severity": "high",
                "auto_fix": True,
            },
        }

    def initialize(self) -> bool:
        """初期化処理"""
        try:
            self._init_database()
            self._load_patterns()
            return True
        except Exception as e:
            self.handle_error(e, "初期化")
            return False

    def _init_database(self):
        """エラーパターンデータベースの初期化"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS error_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT NOT NULL,
                    error_message TEXT,
                    category TEXT,
                    severity TEXT,
                    fix_strategy TEXT,
                    occurrence_count INTEGER DEFAULT 1,
                    last_seen TIMESTAMP,
                    auto_fixed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS error_fixes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id INTEGER,
                    fix_command TEXT,
                    success BOOLEAN,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pattern_id) REFERENCES error_patterns (id)
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_error_type ON error_patterns(error_type)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_category ON error_patterns(category)
            """
            )

    def _load_patterns(self):
        """既知のパターンをキャッシュに読み込む"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT error_type, category, severity, fix_strategy FROM error_patterns"
            )
            for row in cursor:
                self.patterns_cache[row[0]] = {
                    "category": row[1],
                    "severity": row[2],
                    "fix_strategy": row[3],
                }

    def analyze_error(self, error_text: str, context: Optional[Dict] = None) -> Dict:
        """エラーを分析して分類・対策を返す"""
        analysis = {
            "original_error": error_text,
            "timestamp": datetime.now().isoformat(),
            "matched_pattern": None,
            "category": "unknown",
            "severity": "low",
            "requires_human": False,
            "auto_fixable": False,
            "fix_strategies": [],
            "confidence": 0.0,
        }

        # パターンマッチング
        for pattern_name, pattern_info in self.error_patterns.items():
            match = re.search(pattern_info["regex"], error_text, re.IGNORECASE)
            if match:
                analysis["matched_pattern"] = pattern_name
                analysis["category"] = pattern_info["category"]
                analysis["severity"] = pattern_info["severity"]
                analysis["auto_fixable"] = pattern_info["auto_fix"]
                analysis["confidence"] = 0.9

                # 修正戦略の生成
                strategies = self._generate_fix_strategies(
                    pattern_name, match.groups(), context
                )
                analysis["fix_strategies"] = strategies

                # 高度な判断
                if pattern_info["severity"] == "high" and not pattern_info["auto_fix"]:
                    analysis["requires_human"] = True

                # データベースに記録
                self._record_error_pattern(error_text, analysis)
                break

        # パターンに一致しない場合、学習済みパターンを確認
        if not analysis["matched_pattern"]:
            learned = self._check_learned_patterns(error_text)
            if learned:
                analysis.update(learned)

        return analysis

    def _generate_fix_strategies(
        self, pattern: str, groups: Tuple, context: Optional[Dict]
    ) -> List[Dict]:
        """エラーパターンに基づいて修正戦略を生成"""
        strategies = []

        if pattern == "import_error" and len(groups) >= 2:
            module = groups[1]
            strategies.extend(
                [
                    {
                        "strategy": "install_package",
                        "command": f"pip install {module}",
                        "description": f"パッケージ {module} をインストール",
                    },
                    {
                        "strategy": "check_venv",
                        "command": "source venv/bin/activate && pip list",
                        "description": "仮想環境の確認",
                    },
                ]
            )

        elif pattern == "file_not_found" and len(groups) >= 2:
            filepath = groups[1]
            strategies.extend(
                [
                    {
                        "strategy": "create_file",
                        "command": f"touch {filepath}",
                        "description": f"ファイル {filepath} を作成",
                    },
                    {
                        "strategy": "check_path",
                        "command": f"ls -la $(dirname {filepath})",
                        "description": "ディレクトリの存在確認",
                    },
                ]
            )

        elif pattern == "permission_error":
            strategies.extend(
                [
                    {
                        "strategy": "change_permission",
                        "command": "chmod +x",
                        "description": "実行権限の付与",
                    },
                    {
                        "strategy": "change_owner",
                        "command": "chown aicompany:aicompany",
                        "description": "所有者の変更",
                    },
                ]
            )

        elif pattern == "rabbitmq_error":
            strategies.extend(
                [
                    {
                        "strategy": "restart_rabbitmq",
                        "command": "sudo systemctl restart rabbitmq-server",
                        "description": "RabbitMQサービスの再起動",
                    },
                    {
                        "strategy": "check_status",
                        "command": "sudo systemctl status rabbitmq-server",
                        "description": "RabbitMQの状態確認",
                    },
                ]
            )

        elif pattern == "syntax_error" and len(groups) >= 1:
            syntax_detail = groups[0]
            strategies.extend(
                [
                    {
                        "strategy": "fix_syntax_error",
                        "command": f"syntax_fix:{syntax_detail}",
                        "description": f"Syntax修正: {syntax_detail}",
                    },
                    {
                        "strategy": "validate_fix",
                        "command": "python -m py_compile",
                        "description": "修正コードの構文検証",
                    },
                ]
            )

        elif pattern == "connection_error":
            strategies.extend(
                [
                    {
                        "strategy": "retry_with_delay",
                        "command": "sleep 5 && retry",
                        "description": "5秒後に再試行",
                    },
                    {
                        "strategy": "check_network",
                        "command": "ping -c 1 google.com",
                        "description": "ネットワーク接続確認",
                    },
                ]
            )

        return strategies

    def _record_error_pattern(self, error_text: str, analysis: Dict):
        """エラーパターンをデータベースに記録"""
        with sqlite3.connect(self.db_path) as conn:
            # 既存のパターンを確認
            cursor = conn.execute(
                "SELECT id, occurrence_count FROM error_patterns WHERE error_type = ?",
                (analysis["matched_pattern"],),
            )
            row = cursor.fetchone()

            if row:
                # カウントを更新
                conn.execute(
                    "UPDATE error_patterns SET occurrence_count = ?, last_seen = ? WHERE id = ?",
                    (row[1] + 1, datetime.now(), row[0]),
                )
            else:
                # 新規登録
                conn.execute(
                    """INSERT INTO error_patterns
                    (error_type, error_message, category, severity, fix_strategy)
                    VALUES (?, ?, ?, ?, ?)""",
                    (
                        analysis["matched_pattern"],
                        error_text[:500],  # 最初の500文字
                        analysis["category"],
                        analysis["severity"],
                        json.dumps(analysis["fix_strategies"]),
                    ),
                )

    def _check_learned_patterns(self, error_text: str) -> Optional[Dict]:
        """学習済みパターンから類似のエラーを検索"""
        # 簡易的な類似度チェック（将来的にはより高度な実装）
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """SELECT error_type, category, severity, fix_strategy
                FROM error_patterns
                WHERE error_message LIKE ?
                ORDER BY occurrence_count DESC
                LIMIT 1""",
                (f"%{error_text[:50]}%",),
            )
            row = cursor.fetchone()

            if row:
                return {
                    "matched_pattern": row[0],
                    "category": row[1],
                    "severity": row[2],
                    "fix_strategies": json.loads(row[3]) if row[3] else [],
                    "confidence": 0.7,
                    "auto_fixable": True,
                }

        return None

    def get_error_statistics(self) -> Dict:
        """エラー統計情報を取得"""
        with sqlite3.connect(self.db_path) as conn:
            stats = {
                "total_errors": 0,
                "by_category": {},
                "by_severity": {},
                "auto_fixed": 0,
                "top_errors": [],
            }

            # 総エラー数
            cursor = conn.execute("SELECT SUM(occurrence_count) FROM error_patterns")
            stats["total_errors"] = cursor.fetchone()[0] or 0

            # カテゴリ別
            cursor = conn.execute(
                """SELECT category, SUM(occurrence_count)
                FROM error_patterns GROUP BY category"""
            )
            stats["by_category"] = dict(cursor.fetchall())

            # 重要度別
            cursor = conn.execute(
                """SELECT severity, SUM(occurrence_count)
                FROM error_patterns GROUP BY severity"""
            )
            stats["by_severity"] = dict(cursor.fetchall())

            # 自動修正数
            cursor = conn.execute(
                "SELECT COUNT(*) FROM error_patterns WHERE auto_fixed = 1"
            )
            stats["auto_fixed"] = cursor.fetchone()[0]

            # トップエラー
            cursor = conn.execute(
                """SELECT error_type, occurrence_count
                FROM error_patterns
                ORDER BY occurrence_count DESC
                LIMIT 5"""
            )
            stats["top_errors"] = [{"type": row[0], "count": row[1]} for row in cursor]

            return stats

    def record_fix_result(self, pattern_id: int, command: str, success: bool):
        """修正結果を記録"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO error_fixes (pattern_id, fix_command, success) VALUES (?, ?, ?)",
                (pattern_id, command, success),
            )

            if success:
                conn.execute(
                    "UPDATE error_patterns SET auto_fixed = 1 WHERE id = ?",
                    (pattern_id,),
                )

    def should_ignore_error(self, error_text: str) -> bool:
        """エラーを無視すべきか判断"""
        ignore_patterns = [
            r"UserWarning:",
            r"DeprecationWarning:",
            r"FutureWarning:",
            r"InsecureRequestWarning:",
            r"ResourceWarning:",
            r"RuntimeWarning: numpy",
            r"DEBUG:",
            r"INFO:",
        ]

        for pattern in ignore_patterns:
            if re.search(pattern, error_text, re.IGNORECASE):
                return True

        return False


if __name__ == "__main__":
    # テスト実行
    manager = ErrorIntelligenceManager()

    # テストケース
    test_errors = [
        "ModuleNotFoundError: No module named 'requests'",
        "FileNotFoundError: [Errno 2] No such file or directory: '/tmp/test.txt'",
        "PermissionError: [Errno 13] Permission denied: './script.sh'",
        "ConnectionRefusedError: [Errno 111] Connection refused",
        "SyntaxError: invalid syntax (line 42)",
    ]

    print("=== Error Intelligence Manager Test ===")
    for error in test_errors:
        print(f"\nAnalyzing: {error}")
        result = manager.analyze_error(error)
        print(f"Category: {result['category']}")
        print(f"Severity: {result['severity']}")
        print(f"Auto-fixable: {result['auto_fixable']}")
        if result["fix_strategies"]:
            print("Fix strategies:")
            for strategy in result["fix_strategies"]:
                print(f"  - {strategy['description']}: {strategy['command']}")

    print("\n=== Error Statistics ===")
    stats = manager.get_error_statistics()
    print(json.dumps(stats, indent=2))
