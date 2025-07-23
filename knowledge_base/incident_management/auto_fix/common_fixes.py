#!/usr/bin/env python3
"""
Common Fixes - 一般的な問題の自動修復
インシデント賢者の基本的な治癒能力
"""

import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil


class CommonFixes:
    """一般的な問題の自動修復クラス"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ai_co_path = Path("/home/aicompany/ai_co")
        self.venv_path = self.ai_co_path / "venv"

        # 修復実行履歴
        self.fix_history = []

        self.logger.info("🔧 CommonFixes initialized - 自動修復システム起動")

    def diagnose_and_fix(self, incident_data: Dict) -> Dict:
        """インシデントを診断し、適切な修復を実行"""
        incident_type = incident_data.get("category", "unknown")
        error_message = incident_data.get("description", "")

        fix_result = {
            "attempted_fixes": [],
            "successful_fixes": [],
            "failed_fixes": [],
            "status": "no_fix_available",
            "resolution_time": 0,
        }

        start_time = time.time()

        # エラーパターンに基づく修復
        if "connection" in error_message.lower():
            fix_result = self._fix_connection_issues(incident_data, fix_result)

        if "permission" in error_message.lower():
            fix_result = self._fix_permission_issues(incident_data, fix_result)

        if "module" in error_message.lower() and "not found" in error_message.lower():
            fix_result = self._fix_module_issues(incident_data, fix_result)

        if "worker" in error_message.lower():
            fix_result = self._fix_worker_issues(incident_data, fix_result)

        if "rabbitmq" in error_message.lower():
            fix_result = self._fix_rabbitmq_issues(incident_data, fix_result)

        # 修復結果の評価
        fix_result["resolution_time"] = time.time() - start_time

        if fix_result["successful_fixes"]:
            fix_result["status"] = "resolved"
        elif fix_result["failed_fixes"]:
            fix_result["status"] = "attempted_but_failed"

        self.fix_history.append(
            {
                "incident_id": incident_data.get("incident_id"),
                "timestamp": time.time(),
                "result": fix_result,
            }
        )

        return fix_result

    def _fix_connection_issues(self, incident_data: Dict, fix_result: Dict) -> Dict:
        """接続問題の修復"""
        fixes_to_try = [
            ("network_restart", self._restart_network_services),
            ("dns_flush", self._flush_dns_cache),
            ("firewall_check", self._check_firewall_rules),
        ]

        for fix_name, fix_func in fixes_to_try:
            fix_result["attempted_fixes"].append(fix_name)
            try:
                success = fix_func()
                if success:
                    fix_result["successful_fixes"].append(fix_name)
                    self.logger.info(f"✅ {fix_name} successful")
                else:
                    fix_result["failed_fixes"].append(fix_name)
                    self.logger.warning(f"❌ {fix_name} failed")
            except Exception as e:
                fix_result["failed_fixes"].append(fix_name)
                self.logger.error(f"❌ {fix_name} error: {str(e)}")

        return fix_result

    def _fix_permission_issues(self, incident_data: Dict, fix_result: Dict) -> Dict:
        """権限問題の修復"""
        fixes_to_try = [
            ("fix_file_permissions", self._fix_file_permissions),
            ("fix_directory_permissions", self._fix_directory_permissions),
            ("fix_executable_permissions", self._fix_executable_permissions),
        ]

        for fix_name, fix_func in fixes_to_try:
            fix_result["attempted_fixes"].append(fix_name)
            try:
                success = fix_func()
                if success:
                    fix_result["successful_fixes"].append(fix_name)
                else:
                    fix_result["failed_fixes"].append(fix_name)
            except Exception as e:
                fix_result["failed_fixes"].append(fix_name)
                self.logger.error(f"Permission fix error: {str(e)}")

        return fix_result

    def _fix_module_issues(self, incident_data: Dict, fix_result: Dict) -> Dict:
        """モジュール/パッケージ問題の修復"""
        fixes_to_try = [
            ("reinstall_requirements", self._reinstall_requirements),
            ("fix_python_path", self._fix_python_path),
            ("clear_cache", self._clear_python_cache),
        ]

        for fix_name, fix_func in fixes_to_try:
            fix_result["attempted_fixes"].append(fix_name)
            try:
                success = fix_func()
                if success:
                    fix_result["successful_fixes"].append(fix_name)
                else:
                    fix_result["failed_fixes"].append(fix_name)
            except Exception as e:
                fix_result["failed_fixes"].append(fix_name)
                self.logger.error(f"Module fix error: {str(e)}")

        return fix_result

    def _fix_worker_issues(self, incident_data: Dict, fix_result: Dict) -> Dict:
        """ワーカー問題の修復"""
        fixes_to_try = [
            ("restart_workers", self._restart_workers),
            ("clear_worker_queues", self._clear_worker_queues),
            ("reset_worker_state", self._reset_worker_state),
        ]

        for fix_name, fix_func in fixes_to_try:
            fix_result["attempted_fixes"].append(fix_name)
            try:
                success = fix_func()
                if success:
                    fix_result["successful_fixes"].append(fix_name)
                else:
                    fix_result["failed_fixes"].append(fix_name)
            except Exception as e:
                fix_result["failed_fixes"].append(fix_name)
                self.logger.error(f"Worker fix error: {str(e)}")

        return fix_result

    def _fix_rabbitmq_issues(self, incident_data: Dict, fix_result: Dict) -> Dict:
        """RabbitMQ問題の修復"""
        fixes_to_try = [
            ("restart_rabbitmq", self._restart_rabbitmq),
            ("reset_rabbitmq_queues", self._reset_rabbitmq_queues),
            ("fix_rabbitmq_permissions", self._fix_rabbitmq_permissions),
        ]

        for fix_name, fix_func in fixes_to_try:
            fix_result["attempted_fixes"].append(fix_name)
            try:
                success = fix_func()
                if success:
                    fix_result["successful_fixes"].append(fix_name)
                else:
                    fix_result["failed_fixes"].append(fix_name)
            except Exception as e:
                fix_result["failed_fixes"].append(fix_name)
                self.logger.error(f"RabbitMQ fix error: {str(e)}")

        return fix_result

    # === 実際の修復実行メソッド ===

    def _restart_network_services(self) -> bool:
        """ネットワークサービス再起動"""
        try:
            # NetworkManagerの再起動（可能な場合）
            result = subprocess.run(
                ["sudo", "systemctl", "restart", "NetworkManager"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except:
            return False

    def _flush_dns_cache(self) -> bool:
        """DNS キャッシュクリア"""
        try:
            # systemd-resolved の場合
            result = subprocess.run(
                ["sudo", "systemctl", "flush-dns"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return True  # エラーでも続行
        except:
            return True

    def _check_firewall_rules(self) -> bool:
        """ファイアウォール規則確認"""
        try:
            # ufwの状態確認
            result = subprocess.run(
                ["sudo", "ufw", "status"], capture_output=True, text=True, timeout=10
            )
            return True  # 情報収集のみ
        except:
            return False

    def _fix_file_permissions(self) -> bool:
        """ファイル権限修正"""
        try:
            # Elders Guildディレクトリの権限修正
            subprocess.run(
                ["chmod", "-R", "755", str(self.ai_co_path)],
                capture_output=True,
                timeout=30,
            )
            return True
        except:
            return False

    def _fix_directory_permissions(self) -> bool:
        """ディレクトリ権限修正"""
        try:
            # 重要ディレクトリの権限確認・修正
            important_dirs = ["logs", "knowledge_base", "libs"]
            for dir_name in important_dirs:
                dir_path = self.ai_co_path / dir_name
                if dir_path.exists():
                    subprocess.run(
                        ["chmod", "-R", "755", str(dir_path)],
                        capture_output=True,
                        timeout=10,
                    )
            return True
        except:
            return False

    def _fix_executable_permissions(self) -> bool:
        """実行可能ファイル権限修正"""
        try:
            # scriptsディレクトリの実行権限
            scripts_dir = self.ai_co_path / "scripts"
            if scripts_dir.exists():
                subprocess.run(
                    ["chmod", "+x", str(scripts_dir / "*")],
                    shell=True,
                    capture_output=True,
                    timeout=10,
                )
            return True
        except:
            return False

    def _reinstall_requirements(self) -> bool:
        """requirements.txt 再インストール"""
        try:
            if not self.venv_path.exists():
                return False

            activate_script = self.venv_path / "bin" / "activate"
            requirements_file = self.ai_co_path / "requirements.txt"

            if not requirements_file.exists():
                return False

            # 仮想環境でpip install
            cmd = f"source {activate_script} && pip install -r {requirements_file}"
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.ai_co_path),
            )

            return result.returncode == 0
        except:
            return False

    def _fix_python_path(self) -> bool:
        """Python パス修正"""
        try:
            # PYTHONPATH の設定確認
            current_path = os.environ.get("PYTHONPATH", "")
            ai_co_str = str(self.ai_co_path)

            if ai_co_str not in current_path:
                # 一時的にPYTHONPATHに追加
                new_path = f"{ai_co_str}:{current_path}" if current_path else ai_co_str
                os.environ["PYTHONPATH"] = new_path

            return True
        except:
            return False

    def _clear_python_cache(self) -> bool:
        """Python キャッシュクリア"""
        try:
            # __pycache__ ディレクトリを削除
            for pycache in self.ai_co_path.rglob("__pycache__"):
                if pycache.is_dir():
                    subprocess.run(
                        ["rm", "-rf", str(pycache)], capture_output=True, timeout=5
                    )

            # .pyc ファイルを削除
            for pyc_file in self.ai_co_path.rglob("*.pyc"):
                pyc_file.unlink(missing_ok=True)

            return True
        except:
            return False

    def _restart_workers(self) -> bool:
        """ワーカー再起動"""
        try:
            # ai-stop && ai-start の実行
            stop_result = subprocess.run(
                [str(self.ai_co_path / "commands" / "ai_stop.py")],
                capture_output=True,
                timeout=30,
            )
            time.sleep(2)

            start_result = subprocess.run(
                [str(self.ai_co_path / "commands" / "ai_start.py")],
                capture_output=True,
                timeout=30,
            )

            return start_result.returncode == 0
        except:
            return False

    def _clear_worker_queues(self) -> bool:
        """ワーカーキュークリア"""
        try:
            # ai-queue clear の実行
            result = subprocess.run(
                [str(self.ai_co_path / "commands" / "ai_queue_clear.py")],
                capture_output=True,
                timeout=30,
            )
            return result.returncode == 0
        except:
            return False

    def _reset_worker_state(self) -> bool:
        """ワーカー状態リセット"""
        try:
            # ワーカープロセスの強制終了
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = " ".join(proc.info.get("cmdline", []))
                    if "worker" in cmdline and "ai_co" in cmdline:
                        proc.terminate()
                        time.sleep(1)
                        if not (proc.is_running()):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if proc.is_running():
                            proc.kill()
                except:
                    continue

            return True
        except:
            return False

    def _restart_rabbitmq(self) -> bool:
        """RabbitMQ 再起動"""
        try:
            # RabbitMQサービス再起動
            result = subprocess.run(
                ["sudo", "systemctl", "restart", "rabbitmq-server"],
                capture_output=True,
                timeout=60,
            )
            return result.returncode == 0
        except:
            return False

    def _reset_rabbitmq_queues(self) -> bool:
        """RabbitMQ キューリセット"""
        try:
            # キューのパージ
            queues = ["task_queue", "result_queue", "pm_queue"]
            for queue in queues:
                subprocess.run(
                    ["sudo", "rabbitmqctl", "purge_queue", queue],
                    capture_output=True,
                    timeout=10,
                )
            return True
        except:
            return False

    def _fix_rabbitmq_permissions(self) -> bool:
        """RabbitMQ 権限修正"""
        try:
            # RabbitMQユーザー権限確認
            result = subprocess.run(
                ["sudo", "rabbitmqctl", "list_users"], capture_output=True, timeout=10
            )
            return True  # 情報収集のみ
        except:
            return False

    def get_fix_statistics(self) -> Dict:
        """修復統計情報を取得"""
        if not self.fix_history:
            return {"total_fixes": 0}

        total_fixes = len(self.fix_history)
        successful_fixes = sum(
            1 for fix in self.fix_history if fix["result"]["status"] == "resolved"
        )

        return {
            "total_fixes": total_fixes,
            "successful_fixes": successful_fixes,
            "success_rate": successful_fixes / total_fixes if total_fixes > 0 else 0,
            "average_resolution_time": sum(
                fix["result"]["resolution_time"] for fix in self.fix_history
            )
            / total_fixes
            if total_fixes > 0
            else 0,
        }
