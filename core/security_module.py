#!/usr/bin/env python3
"""
セキュリティモジュール
タスク実行時のセキュリティ検証と安全な実行環境を提供
"""

import asyncio
import hashlib
import os
import re
import shlex
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent))
from lightweight_logger import get_logger


class SecurityError(Exception):
    """セキュリティ違反時の例外"""

    pass


class SecureTaskExecutor:
    """
    セキュアなタスク実行クラス

    Features:
    - コマンドインジェクション対策
    - ファイルシステムサンドボックス
    - リソース制限
    - 実行ログの監査証跡
    """

    def __init__(self, config: Dict = None):
        """初期化メソッド"""
        self.config = config or {}
        self.logger = get_logger("security_module")

        # 許可されたコマンド（ホワイトリスト）
        self.allowed_commands = {
            "python",
            "python3",
            "node",
            "npm",
            "bash",
            "sh",
            "git",
            "pip",
            "pytest",
            "ruff",
            "black",
            "mypy",
            "ls",
            "cat",
            "echo",
            "grep",
            "find",
            "sed",
            "awk",
        }

        # 禁止パターン（ブラックリスト）
        self.forbidden_patterns = [
            r"rm\s+-rf\s+/",
            r"sudo",
            r"chmod\s+777",
            r"eval\s*\(",
            r"exec\s*\(",
            r"__import__",
            r"os\.system",
            r"subprocess\.call",
            r"curl.*\|.*sh",
            r"wget.*\|.*sh",  # リモートスクリプト実行
            r"dd\s+if=/dev/zero",  # ディスク埋め
            r":(){ :|:& };:",  # フォーク爆弾
            r">\s*/dev/sd",  # デバイス直接書き込み
            r"mkfs\.",
            r"fdisk",  # ファイルシステム操作
        ]

        # 環境変数のホワイトリスト
        self.allowed_env_vars = {
            "PATH",
            "HOME",
            "USER",
            "LANG",
            "LC_ALL",
            "PYTHONPATH",
            "NODE_PATH",
            "PWD",
            "TMPDIR",
        }

        # サンドボックスディレクトリ
        self.sandbox_base = Path(self.config.get("sandbox_base", "/tmp/ai_sandbox"))
        self.sandbox_base.mkdir(exist_ok=True, mode=0o700)

        # 実行履歴（監査用）
        self.execution_history = []

    async def validate_input(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        入力コマンドの検証

        Returns:
            (is_valid, error_message)
        """
        try:
            # 空コマンドチェック
            if not command or not command.strip():
                return False, "Empty command"

            # 長さ制限
            if len(command) > 10000:
                return False, "Command too long (max 10000 chars)"

            # 禁止パターンチェック
            for pattern in self.forbidden_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    self.logger.warning(
                        "Forbidden pattern detected",
                        pattern=pattern,
                        command=command[:100],
                    )
                    return False, f"Forbidden pattern detected: {pattern}"

            # コマンド解析
            try:
                cmd_parts = shlex.split(command)
                if not cmd_parts:
                    return False, "Invalid command format"

                base_command = os.path.basename(cmd_parts[0])

                # ホワイトリストチェック
                if base_command not in self.allowed_commands:
                    # フルパスの場合、実行ファイル名をチェック
                    if "/" in cmd_parts[0]:
                        exe_name = os.path.basename(cmd_parts[0])
                        if not (exe_name not in self.allowed_commands):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if exe_name not in self.allowed_commands:
                            return False, f"Command not allowed: {base_command}"
                    else:
                        return False, f"Command not allowed: {base_command}"

            except ValueError as e:
                return False, f"Invalid command syntax: {str(e)}"

            # パス遡り攻撃のチェック
            if "../" in command or "/.." in command:
                return False, "Path traversal detected"

            return True, None

        except Exception as e:
            self.logger.error("Validation error", error=str(e))
            return False, f"Validation error: {str(e)}"

    def _create_sandbox(self) -> Path:
        """サンドボックス環境の作成"""
        # 一意のサンドボックスディレクトリを作成
        sandbox_id = hashlib.md5(
            f"{datetime.utcnow().isoformat()}_{os.getpid()}".encode()
        ).hexdigest()[:8]

        sandbox_path = self.sandbox_base / f"sandbox_{sandbox_id}"
        sandbox_path.mkdir(mode=0o700)

        # 必要なディレクトリ構造を作成
        (sandbox_path / "work").mkdir(mode=0o755)
        (sandbox_path / "tmp").mkdir(mode=0o755)
        (sandbox_path / "output").mkdir(mode=0o755)

        return sandbox_path

    def _prepare_environment(self, sandbox_path: Path) -> Dict[str, str]:
        """安全な実行環境の準備"""
        # 基本的な環境変数のみを許可
        safe_env = {}

        for var in self.allowed_env_vars:
            if var in os.environ:
                safe_env[var] = os.environ[var]

        # サンドボックス用の環境変数を追加
        safe_env.update(
            {
                "HOME": str(sandbox_path),
                "TMPDIR": str(sandbox_path / "tmp"),
                "PWD": str(sandbox_path / "work"),
                "AI_SANDBOX": "1",  # サンドボックス内であることを示すフラグ
            }
        )

        # PATHを制限（システムの基本的なパスのみ）
        safe_env["PATH"] = "/usr/local/bin:/usr/bin:/bin"

        return safe_env

    async def execute_secure(
        self, command: str, timeout: int = 300, memory_limit_mb: int = 512
    ) -> Dict[str, any]:
        """
        セキュアなコマンド実行

        Args:
            command: 実行するコマンド
            timeout: タイムアウト（秒）
            memory_limit_mb: メモリ制限（MB）

        Returns:
            実行結果の辞書
        """
        # 入力検証
        is_valid, error_msg = await self.validate_input(command)
        if not is_valid:
            raise SecurityError(error_msg)

        # サンドボックス作成
        sandbox_path = self._create_sandbox()

        try:
            # 実行環境の準備
            env = self._prepare_environment(sandbox_path)

            # リソース制限の設定
            # 注: Linuxのulimitを使用
            resource_limits = f"ulimit -v {memory_limit_mb * 1024}; "

            # 実行ログの記録（監査証跡）
            execution_record = {
                "command": command,
                "sandbox_id": sandbox_path.name,
                "timestamp": datetime.utcnow().isoformat(),
                "timeout": timeout,
                "memory_limit_mb": memory_limit_mb,
            }

            # コマンド実行
            full_command = f"{resource_limits}{command}"

            self.logger.info(
                "Executing command in sandbox",
                sandbox=sandbox_path.name,
                command=command[:100],
            )

            # 非同期プロセス実行
            proc = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(sandbox_path / "work"),
                env=env,
                # 追加のセキュリティ設定
                preexec_fn=lambda: os.setpgrp(),  # プロセスグループ分離
            )

            # タイムアウト付き実行
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )

                execution_record["status"] = "completed"
                execution_record["return_code"] = proc.returncode

            except asyncio.TimeoutError:
                # タイムアウト時はプロセスグループ全体を終了
                try:
                    os.killpg(proc.pid, 9)
                except:
                    proc.kill()

                await proc.wait()

                execution_record["status"] = "timeout"
                raise TimeoutError(f"Command timed out after {timeout}s")

            # 実行結果の準備
            result = {
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "return_code": proc.returncode,
                "sandbox_id": sandbox_path.name,
                "execution_time": datetime.utcnow().isoformat(),
            }

            # 出力ファイルの収集
            output_files = []
            output_dir = sandbox_path / "output"
            for file_path in output_dir.rglob("*"):
                if file_path.is_file():
                    output_files.append(
                        {
                            "path": str(file_path.relative_to(output_dir)),
                            "size": file_path.stat().st_size,
                            "modified": datetime.fromtimestamp(
                                file_path.stat().st_mtime
                            ).isoformat(),
                        }
                    )

            result["output_files"] = output_files

            # 実行履歴に追加
            execution_record["result"] = result
            self.execution_history.append(execution_record)

            self.logger.info(
                "Command executed successfully",
                sandbox=sandbox_path.name,
                return_code=proc.returncode,
            )

            return result

        finally:
            # サンドボックスのクリーンアップ
            try:
                import shutil

                shutil.rmtree(sandbox_path)
            except Exception as e:
                self.logger.error(
                    "Failed to cleanup sandbox", sandbox=sandbox_path.name, error=str(e)
                )

    def get_execution_history(self, limit: int = 100) -> List[Dict]:
        """実行履歴の取得（監査用）"""
        return self.execution_history[-limit:]

    async def cleanup_old_sandboxes(self, max_age_hours: int = 24):
        """古いサンドボックスのクリーンアップ"""
        import shutil
        from datetime import timedelta

        now = datetime.utcnow()
        cleanup_count = 0

        for sandbox_dir in self.sandbox_base.iterdir():
            if sandbox_dir.is_dir() and sandbox_dir.name.startswith("sandbox_"):
                # ディレクトリの作成時刻をチェック
                created_time = datetime.fromtimestamp(sandbox_dir.stat().st_ctime)

                if now - created_time > timedelta(hours=max_age_hours):
                    try:
                        shutil.rmtree(sandbox_dir)
                        cleanup_count += 1
                        self.logger.info(
                            "Cleaned up old sandbox", sandbox=sandbox_dir.name
                        )
                    except Exception as e:
                        self.logger.error(
                            "Failed to cleanup sandbox",
                            sandbox=sandbox_dir.name,
                            error=str(e),
                        )

        return cleanup_count


class InputSanitizer:
    """入力サニタイゼーション用のユーティリティクラス"""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """ファイル名のサニタイズ"""
        # 危険な文字を除去
        dangerous_chars = ["/", "\\", "..", "~", "|", ">", "<", "&", ";", "$", "`"]
        safe_name = filename

        for char in dangerous_chars:
            safe_name = safe_name.replace(char, "_")

        # 英数字、ハイフン、アンダースコア、ピリオドのみ許可
        safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", safe_name)

        # 長さ制限
        if len(safe_name) > 255:
            safe_name = safe_name[:255]

        return safe_name

    @staticmethod
    def sanitize_path(path: str, base_path: str) -> Optional[str]:
        """パスのサニタイズと検証"""
        try:
            # 絶対パスに変換
            abs_path = os.path.abspath(os.path.join(base_path, path))

            # ベースパス内にあることを確認
            if not abs_path.startswith(os.path.abspath(base_path)):
                return None

            return abs_path

        except Exception:
            return None

    @staticmethod
    def sanitize_json_input(data: Dict) -> Dict:
        """JSON入力のサニタイズ"""

        def clean_value(value):
            """clean_valueメソッド"""
            if isinstance(value, str):
                # 制御文字を除去
                value = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", value)
                # 長さ制限
                if len(value) > 10000:
                    value = value[:10000]
            elif isinstance(value, dict):
                return {k: clean_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [clean_value(item) for item in value]

            return value

        return clean_value(data)


class SecurityModule:
    """
    Elder階層統合セキュリティモジュール
    統合認証システムと連携したセキュリティ機能を提供
    """

    def __init__(self):
        """初期化メソッド"""
        self.logger = get_logger("security_module")
        self.executor = SecureTaskExecutor()
        self.sanitizer = InputSanitizer()

        # セキュリティレベル設定
        self.security_levels = {
            "GRAND_ELDER": 5,
            "CLAUDE_ELDER": 4,
            "SAGE": 3,
            "SERVANT": 2,
            "GUEST": 1,
        }

    def validate_elder_operation(
        self, user_role: str, operation: str, user_context=None
    ) -> bool:
        """Elder階層に基づく操作権限検証（改ざん検出付き）"""
        # ユーザーコンテキストがある場合は権限整合性をチェック
        if user_context and hasattr(user_context, "elder_role"):
            # 渡されたロールとコンテキストのロールが一致しない場合はエラー
            if user_context.elder_role.value.upper() != user_role.upper():
                raise SecurityError(
                    f"権限不整合検出: 要求ロール={user_role}, コンテキストロール={user_context.elder_role.value}"
                )

        required_level = self._get_operation_security_level(operation)
        user_level = self.security_levels.get(user_role.upper(), 0)

        # 危険操作の場合は追加検証
        if required_level >= 4:  # GRAND_ELDER級操作
            self.logger.warning(f"高権限操作試行: user={user_role}, operation={operation}")

        return user_level >= required_level

    def _get_operation_security_level(self, operation: str) -> int:
        """操作に必要なセキュリティレベルを取得"""
        high_security_ops = ["deploy", "delete", "promote", "demote", "configure"]
        medium_security_ops = ["create", "modify", "update", "install"]

        if any(op in operation.lower() for op in high_security_ops):
            return 4  # CLAUDE_ELDER以上
        elif any(op in operation.lower() for op in medium_security_ops):
            return 3  # SAGE以上
        else:
            return 2  # SERVANT以上

    async def secure_execute(
        self, command: str, user_role: str, **kwargs
    ) -> Dict[str, Any]:
        """Elder階層権限に基づくセキュアな実行"""
        if not self.validate_elder_operation(user_role, command):
            raise SecurityError(f"Insufficient permissions for user role: {user_role}")

        return await self.executor.execute_secure(command, **kwargs)

    def sanitize_input(self, data: Any) -> Any:
        """入力データのサニタイズ"""
        if isinstance(data, str):
            return self.sanitizer.sanitize_filename(data)
        elif isinstance(data, dict):
            return self.sanitizer.sanitize_json_input(data)
        return data

    def get_security_audit_log(self) -> List[Dict]:
        """セキュリティ監査ログの取得"""
        return self.executor.get_execution_history()


# エイリアスを追加してBackward compatibility維持
security_module = SecurityModule()
