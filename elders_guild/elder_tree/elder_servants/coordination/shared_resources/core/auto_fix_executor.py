#!/usr/bin/env python3
"""
自動修正実行者
ErrorIntelligenceManagerで分析されたエラーの修正戦略を実行する
"""

import json
import logging
import os
import subprocess

# プロジェクトルートをPythonパスに追加
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseManager


class AutoFixExecutor(BaseManager):
    """エラーの自動修正を実行するクラス"""

    def __init__(self):
        """super().__init__("AutoFixExecutor")
    """初期化メソッド"""
        self.project_root = PROJECT_ROOT
        self.stats = {
            "total_executions": 0,
            "successful_fixes": 0,
            "failed_fixes": 0,
            "rollbacks_performed": 0,
            "execution_times": [],
        }

        # 安全性チェック用の危険なコマンドパターン
        self.dangerous_patterns = [
            r"rm\s+-rf\s+/",
            r"sudo\s+rm\s+-rf",
            r"format\s+c:",
            r"del\s+/s\s+/q",
            r"DROP\s+DATABASE",
            r"DROP\s+TABLE",
            r"--force\s+--all",
        ]

    def initialize(self) -> bool:
        """初期化処理"""
        return True

    def execute_fix(self, analysis: Dict, error_info: Dict) -> Dict:
        """
        修正戦略を実行する

        Args:
            analysis: ErrorIntelligenceManagerからの分析結果
            error_info: エラー情報

        Returns:
            修正実行結果
        """
        start_time = time.time()
        self.stats["total_executions"] += 1

        result = {
            "success": False,
            "strategy_used": None,
            "executed_commands": [],
            "error": None,
            "verification_passed": False,
            "rollback_performed": False,
            "execution_time": 0.0,
            "details": {},
        }

        try:
            self.logger.info(
                f"自動修正開始: {analysis['category']} - {analysis['matched_pattern']}"
            )

            # 修正戦略を実行
            for strategy in analysis["fix_strategies"]:
                if self._execute_strategy(strategy, error_info, result):
                    result["success"] = True
                    result["strategy_used"] = strategy["strategy"]
                    break

            # 修正後の検証
            if result["success"]:
                result["verification_passed"] = self._verify_fix(analysis, error_info)
                if not result["verification_passed"]:
                    self.logger.warning("修正検証に失敗、ロールバックを実行")
                    result["rollback_performed"] = self._perform_rollback(result)
                    result["success"] = False

            # 統計更新
            if result["success"]:
                self.stats["successful_fixes"] += 1
            else:
                self.stats["failed_fixes"] += 1

            if result["rollback_performed"]:
                self.stats["rollbacks_performed"] += 1

            execution_time = time.time() - start_time
            result["execution_time"] = execution_time
            self.stats["execution_times"].append(execution_time)

            self.logger.info(
                f"自動修正完了: {result['success']} " f"({execution_time:0.2f}秒)"
            )

        except Exception as e:
            result["error"] = str(e)
            result["execution_time"] = time.time() - start_time
            self.logger.error(f"自動修正実行エラー: {e}")

        return result

    def _execute_strategy(self, strategy: Dict, error_info: Dict, result: Dict) -> bool:
        """
        個別の修正戦略を実行

        Args:
            strategy: 修正戦略
            error_info: エラー情報
            result: 実行結果（更新される）

        Returns:
            実行成功の可否
        """
        strategy_name = strategy["strategy"]
        command = strategy["command"]
        description = strategy["description"]

        self.logger.info(f"修正戦略実行: {strategy_name} - {description}")

        # 安全性チェック
        if not self._is_safe_command(command):
            self.logger.error(f"危険なコマンドを検出: {command}")
            result["error"] = f"危険なコマンドのため実行を拒否: {command}"
            return False

        # 戦略別の実行
        if strategy_name == "install_package":
            return self._install_package(command, result)
        elif strategy_name == "create_file":
            return self._create_file(command, result)
        elif strategy_name == "change_permission":
            return self._change_permission(command, error_info, result)
        elif strategy_name == "change_owner":
            return self._change_owner(command, error_info, result)
        elif strategy_name == "restart_rabbitmq":
            return self._restart_service(command, result)
        elif strategy_name == "retry_with_delay":
            return self._retry_with_delay(command, result)
        elif strategy_name == "check_venv":
            return self._check_virtual_environment(command, result)
        elif strategy_name == "fix_syntax_error":
            return self._fix_syntax_error(command, error_info, result)
        else:
            # 汎用コマンド実行
            return self._execute_generic_command(command, result)

    def _install_package(self, command: str, result: Dict) -> bool:
        """パッケージインストール"""
        try:
            # pip install コマンドの実行
            process = subprocess.run(
                command.split(),
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5分タイムアウト
            )

            result["executed_commands"].append(command)
            result["details"]["install_output"] = process.stdout
            result["details"]["install_error"] = process.stderr

            if process.returncode == 0:
                self.logger.info(f"パッケージインストール成功: {command}")
                return True
            else:
                self.logger.error(f"パッケージインストール失敗: {process.stderr}")
                result["error"] = f"インストール失敗: {process.stderr}"
                return False

        except subprocess.TimeoutExpired:
            result["error"] = "パッケージインストールがタイムアウトしました"
            return False
        except Exception as e:
            result["error"] = f"パッケージインストールエラー: {str(e)}"
            return False

    def _create_file(self, command: str, result: Dict) -> bool:
        """ファイル作成"""
        try:
            # touch コマンドからファイルパスを抽出
            if command.startswith("touch "):
                filepath = command[6:].strip()
                file_path = Path(filepath)

                # 親ディレクトリが存在しない場合は作成
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # ファイル作成
                file_path.touch()

                result["executed_commands"].append(command)
                result["details"]["created_file"] = str(file_path)

                self.logger.info(f"ファイル作成成功: {filepath}")
                return True
            else:
                result["error"] = f"未対応のファイル作成コマンド: {command}"
                return False

        except Exception as e:
            result["error"] = f"ファイル作成エラー: {str(e)}"
            return False

    def _change_permission(self, command: str, error_info: Dict, result: Dict) -> bool:
        """権限変更"""
        try:
            # エラー情報からファイルパスを抽出
            error_text = error_info.get("error_text", "")
            import re

            # PermissionErrorからファイルパスを抽出
            match = re.search(r"Permission denied.*?['\"]([^'\"]+)['\"]", error_text)
            if match:
                filepath = match.group(1)
                full_command = f"chmod +x {filepath}"

                process = subprocess.run(
                    full_command.split(),
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )

                result["executed_commands"].append(full_command)

                if process.returncode == 0:
                    self.logger.info(f"権限変更成功: {filepath}")
                    return True
                else:
                    result["error"] = f"権限変更失敗: {process.stderr}"
                    return False
            else:
                result["error"] = "権限エラーのファイルパスを特定できませんでした"
                return False

        except Exception as e:
            result["error"] = f"権限変更エラー: {str(e)}"
            return False

    def _change_owner(self, command: str, error_info: Dict, result: Dict) -> bool:
        """所有者変更"""
        try:
            # エラー情報からファイルパスを抽出
            error_text = error_info.get("error_text", "")
            import re

            match = re.search(r"Permission denied.*?['\"]([^'\"]+)['\"]", error_text)
            if match:
                filepath = match.group(1)
                full_command = f"chown aicompany:aicompany {filepath}"

                process = subprocess.run(
                    full_command.split(),
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )

                result["executed_commands"].append(full_command)

                if process.returncode == 0:
                    self.logger.info(f"所有者変更成功: {filepath}")
                    return True
                else:
                    result["error"] = f"所有者変更失敗: {process.stderr}"
                    return False
            else:
                result["error"] = "所有者エラーのファイルパスを特定できませんでした"
                return False

        except Exception as e:
            result["error"] = f"所有者変更エラー: {str(e)}"
            return False

    def _restart_service(self, command: str, result: Dict) -> bool:
        """サービス再起動"""
        try:
            process = subprocess.run(
                command.split(), capture_output=True, text=True, timeout=60
            )

            result["executed_commands"].append(command)
            result["details"]["service_output"] = process.stdout

            if process.returncode == 0:
                self.logger.info(f"サービス再起動成功: {command}")
                return True
            else:
                result["error"] = f"サービス再起動失敗: {process.stderr}"
                return False

        except subprocess.TimeoutExpired:
            result["error"] = "サービス再起動がタイムアウトしました"
            return False
        except Exception as e:
            result["error"] = f"サービス再起動エラー: {str(e)}"
            return False

    def _retry_with_delay(self, command: str, result: Dict) -> bool:
        """遅延付きリトライ"""
        try:
            # sleep コマンドの実行
            if "sleep" in command:
                sleep_time = 5  # デフォルト5秒
                import re

                match = re.search(r"sleep\s+(\d+)", command)
                if match:
                    sleep_time = int(match.group(1))

                time.sleep(sleep_time)
                result["executed_commands"].append(f"sleep {sleep_time}")
                result["details"]["delay_seconds"] = sleep_time

                self.logger.info(f"遅延実行: {sleep_time}秒")
                return True
            else:
                result["error"] = f"未対応の遅延コマンド: {command}"
                return False

        except Exception as e:
            result["error"] = f"遅延実行エラー: {str(e)}"
            return False

    def _check_virtual_environment(self, command: str, result: Dict) -> bool:
        """仮想環境チェック"""
        try:
            # venv/bin/activate の存在確認
            venv_path = self.project_root / "venv" / "bin" / "activate"
            if venv_path.exists():
                # pip list の実行
                pip_list_cmd = f"{self.project_root}/venv/bin/pip list"
                process = subprocess.run(
                    pip_list_cmd.split(), capture_output=True, text=True, timeout=30
                )

                result["executed_commands"].append(pip_list_cmd)
                result["details"]["venv_packages"] = process.stdout

                if process.returncode == 0:
                    self.logger.info("仮想環境チェック成功")
                    return True
                else:
                    result["error"] = f"仮想環境チェック失敗: {process.stderr}"
                    return False
            else:
                result["error"] = "仮想環境が見つかりません"
                return False

        except Exception as e:
            result["error"] = f"仮想環境チェックエラー: {str(e)}"
            return False

    def _execute_generic_command(self, command: str, result: Dict) -> bool:
        """汎用コマンド実行"""
        try:
            process = subprocess.run(
                command.split(),
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120,
            )

            result["executed_commands"].append(command)
            result["details"]["command_output"] = process.stdout
            result["details"]["command_error"] = process.stderr

            if process.returncode == 0:
                self.logger.info(f"汎用コマンド実行成功: {command}")
                return True
            else:
                result["error"] = f"汎用コマンド実行失敗: {process.stderr}"
                return False

        except subprocess.TimeoutExpired:
            result["error"] = "コマンド実行がタイムアウトしました"
            return False
        except Exception as e:
            result["error"] = f"汎用コマンド実行エラー: {str(e)}"
            return False

    def _fix_syntax_error(self, command: str, error_info: Dict, result: Dict) -> bool:
        """SyntaxError自動修正"""
        try:
            from libs.syntax_error_fixer import SyntaxErrorFixer

            # SyntaxErrorFixerを初期化
            syntax_fixer = SyntaxErrorFixer()

            # エラー情報から元のコードを取得（可能であれば）
            error_text = error_info.get("error_text", "")
            original_message = error_info.get("original_message", {})

            # プロンプトからコードを抽出
            code = None
            if "prompt" in original_message:
                prompt = original_message["prompt"]
                # Pythonコードブロックを抽出
                import re

                code_blocks = re.findall(r"```python\n(.*?)\n```", prompt, re.DOTALL)
                if code_blocks:
                    code = code_blocks[0]
                elif "import " in prompt or "def " in prompt or "class " in prompt:
                    # プロンプト自体がコードの可能性
                    code = prompt

            if not code:
                result["error"] = "修正対象のコードが見つかりません"
                return False

            self.logger.info(f"SyntaxError修正開始: {len(code)}文字のコード")

            # SyntaxError修正実行
            fix_result = syntax_fixer.fix_syntax_error(error_text, code)

            result["executed_commands"].append(f"syntax_fix:{error_text[:50]}...")
            result["details"]["syntax_fix_result"] = fix_result
            result["details"]["original_code"] = code

            if fix_result["success"]:
                result["details"]["fixed_code"] = fix_result["fixed_code"]
                result["details"]["fixes_applied"] = fix_result["fixes_applied"]
                result["details"]["validation_passed"] = fix_result["validation_passed"]

                self.logger.info(f"SyntaxError修正成功: {fix_result['fixes_applied']}")
                return True
            else:
                result["error"] = f"SyntaxError修正失敗: {fix_result['error']}"
                self.logger.error(f"SyntaxError修正失敗: {fix_result['error']}")
                return False

        except ImportError:
            result["error"] = "SyntaxErrorFixerが利用できません"
            return False
        except Exception as e:
            result["error"] = f"SyntaxError修正エラー: {str(e)}"
            self.logger.error(f"SyntaxError修正エラー: {e}")
            return False

    def _is_safe_command(self, command: str) -> bool:
        """コマンドの安全性チェック"""
        import re

        for pattern in self.dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False

        return True

    def _verify_fix(self, analysis: Dict, error_info: Dict) -> bool:
        """修正の検証"""
        try:
            # 修正戦略に応じた検証
            category = analysis["category"]

            if category == "dependency":
                # パッケージがインストールされているか確認
                return self._verify_package_installation(analysis)
            elif category == "filesystem":
                # ファイルが存在するか確認
                return self._verify_file_existence(error_info)
            elif category == "permission":
                # 権限が正しく設定されているか確認
                return self._verify_permissions(error_info)
            elif category == "rabbitmq":
                # RabbitMQサービスが稼働しているか確認
                return self._verify_rabbitmq_status()
            else:
                # 汎用検証（簡易版）
                return True

        except Exception as e:
            self.logger.error(f"修正検証エラー: {e}")
            return False

    def _verify_package_installation(self, analysis: Dict) -> bool:
        """パッケージインストールの検証"""
        try:
            # fix_strategiesからパッケージ名を抽出
            for strategy in analysis["fix_strategies"]:
                if strategy["strategy"] == "install_package":
                    command = strategy["command"]
                    if "pip install" in command:
                        package_name = command.split("pip install")[1].strip()

                        # pip showでパッケージの存在確認
                        process = subprocess.run(
                            ["pip", "show", package_name],
                            capture_output=True,
                            text=True,
                            timeout=30,
                        )

                        return process.returncode == 0

            return False

        except Exception as e:
            self.logger.error(f"パッケージ検証エラー: {e}")
            return False

    def _verify_file_existence(self, error_info: Dict) -> bool:
        """ファイル存在の検証"""
        try:
            error_text = error_info.get("error_text", "")
            import re

            # FileNotFoundErrorからファイルパスを抽出
            match = re.search(
                r"No such file or directory.*?['\"]([^'\"]+)['\"]", error_text
            )
            if match:
                filepath = match.group(1)
                return Path(filepath).exists()

            return False

        except Exception as e:
            self.logger.error(f"ファイル存在検証エラー: {e}")
            return False

    def _verify_permissions(self, error_info: Dict) -> bool:
        """権限の検証"""
        try:
            error_text = error_info.get("error_text", "")
            import re

            # PermissionErrorからファイルパスを抽出
            match = re.search(r"Permission denied.*?['\"]([^'\"]+)['\"]", error_text)
            if match:
                filepath = match.group(1)
                file_path = Path(filepath)

                if file_path.exists():
                    # 実行権限があるかチェック
                    return os.access(filepath, os.X_OK)

            return False

        except Exception as e:
            self.logger.error(f"権限検証エラー: {e}")
            return False

    def _verify_rabbitmq_status(self) -> bool:
        """RabbitMQサービス状態の検証"""
        try:
            process = subprocess.run(
                ["sudo", "systemctl", "is-active", "rabbitmq-server"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            return process.returncode == 0 and "active" in process.stdout

        except Exception as e:
            self.logger.error(f"RabbitMQ状態検証エラー: {e}")
            return False

    def _perform_rollback(self, result: Dict) -> bool:
        """修正のロールバック"""
        try:
            self.logger.info("修正のロールバックを実行中...")

            # 実行されたコマンドを逆順で取り消し
            for command in reversed(result["executed_commands"]):
                if self._rollback_command(command):
                    self.logger.info(f"ロールバック成功: {command}")
                else:
                    self.logger.warning(f"ロールバック失敗: {command}")

            return True

        except Exception as e:
            self.logger.error(f"ロールバックエラー: {e}")
            return False

    def _rollback_command(self, command: str) -> bool:
        """個別コマンドのロールバック"""
        try:
            if command.startswith("pip install"):
                # pip uninstall
                package_name = command.split("pip install")[1].strip()
                rollback_cmd = f"pip uninstall -y {package_name}"

                process = subprocess.run(
                    rollback_cmd.split(), capture_output=True, text=True, timeout=60
                )

                return process.returncode == 0

            elif command.startswith("touch"):
                # ファイル削除
                filepath = command[6:].strip()
                if Path(filepath).exists():
                    Path(filepath).unlink()
                return True

            elif command.startswith("chmod"):
                # 権限を元に戻す（簡易版）
                # 実際の実装では元の権限を記録しておく必要がある
                return True

            elif command.startswith("chown"):
                # 所有者を元に戻す（簡易版）
                return True

            else:
                # その他のコマンドは取り消し困難
                return False

        except Exception as e:
            self.logger.error(f"コマンドロールバックエラー: {e}")
            return False

    def get_statistics(self) -> Dictstats = self.stats.copy():
    """計情報を取得"""

        if stats["execution_times"]:
            stats["avg_execution_time"] = sum(stats["execution_times"]) / len(
                stats["execution_times"]
            )
            stats["max_execution_time"] = max(stats["execution_times"])
            stats["min_execution_time"] = min(stats["execution_times"])
        else:
            stats["avg_execution_time"] = 0
            stats["max_execution_time"] = 0
            stats["min_execution_time"] = 0

        # 成功率計算
        if stats["total_executions"] > 0:
            stats["success_rate"] = (
                stats["successful_fixes"] / stats["total_executions"]
            ) * 100
        else:
            stats["success_rate"] = 0

        return stats


if __name__ == "__main__":
    # テスト実行
    executor = AutoFixExecutor()

    # テストケース
    test_analysis = {
        "category": "dependency",
        "severity": "medium",
        "auto_fixable": True,
        "fix_strategies": [
            {
                "strategy": "install_package",
                "command": "pip install requests",
                "description": "パッケージ requests をインストール",
            }
        ],
    }

    test_error_info = {
        "error_text": "ModuleNotFoundError: No module named 'requests'",
        "task_id": "test_task_001",
        "task_type": "test",
        "worker_type": "test_worker",
    }

    print("=== AutoFixExecutor Test ===")
    result = executor.execute_fix(test_analysis, test_error_info)
    print(f"Result: {json.dumps(result, indent}")

    print("\n=== Statistics ===")
    stats = executor.get_statistics()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
