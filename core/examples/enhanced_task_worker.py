#!/usr/bin/env python3
"""
Enhanced Task Worker - 基底クラスを使用した改良版

BaseWorkerを継承したTaskWorkerの実装例。
既存の機能を維持しつつ、コードの重複を削減。
"""

import glob
import json
import os
import subprocess

# core基盤の使用
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(str(Path(__file__).parent.parent.parent))
from core import EMOJI, BaseWorker, get_config
from libs.github_aware_rag import GitHubAwareRAGManager
from libs.self_evolution_manager import SelfEvolutionManager
from libs.slack_notifier import SlackNotifier


class EnhancedTaskWorker(BaseWorker):
    """改良版TaskWorker - 基底クラスを活用"""

    def __init__(self, worker_id: Optional[str] = None):
        # 基底クラスの初期化
        super().__init__(worker_type="task", worker_id=worker_id)

        # 設定の読み込み
        self.config = get_config()
        self.model = self.config.worker.default_model

        # マネージャーの初期化
        self.rag = GitHubAwareRAGManager(model=self.model)
        self.slack = SlackNotifier()
        self.evolution = SelfEvolutionManager()

        self.logger.info(f"{EMOJI['ai']} Model: {self.model}")

    def process_message(self, ch, method, properties, body) -> None:
        """
        メッセージ処理の実装（BaseWorkerの抽象メソッド）
        """
        task = json.loads(body)
        task_id = task.get("task_id", self._generate_task_id())
        prompt = task.get("prompt", "")
        task_type = task.get("type", "general")

        self.logger.info(f"{EMOJI['process']} Processing {task_type} task")

        # RAGコンテキスト構築
        enhanced_prompt = self._build_enhanced_prompt(prompt)
        rag_applied = len(enhanced_prompt) > len(prompt)

        # 出力ディレクトリ準備
        task_output_dir = self.output_dir / task_type / task_id
        task_output_dir.mkdir(parents=True, exist_ok=True)

        # Claude CLI実行
        result = self._execute_claude_cli(enhanced_prompt, str(self.output_dir))

        # 自己進化処理
        evolution_result = None
        if result["success"]:
            evolution_result = self._handle_evolution(result["output"], task_id, prompt)

        # 結果保存
        self._save_result(
            task_output_dir,
            task_id,
            prompt,
            result["output"],
            rag_applied,
            evolution_result,
        )

        # RAG履歴保存
        self._save_to_rag(
            task_id, prompt, result["output"], result["status"], task_type
        )

        # Slack通知
        self._send_slack_notification(
            task_id,
            prompt,
            result["output"],
            result["status"],
            task_type,
            rag_applied,
            evolution_result,
        )

        # 結果送信
        self.send_result(
            {
                "task_id": task_id,
                "worker": self.worker_id,
                "status": result["status"],
                "output_file": str(task_output_dir / "result.txt"),
                "evolution_result": evolution_result,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def _generate_task_id(self) -> str:
        """タスクID生成"""
        return f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _build_enhanced_prompt(self, prompt: str) -> str:
        """RAG強化プロンプト構築"""
        try:
            enhanced = self.rag.build_context_with_github(prompt, include_code=True)

            # 権限付与プロンプト追加
            permission = """I'll help you with this task. I have full access to create and edit files.

Task to complete:
"""
            enhanced = (
                permission
                + "\n"
                + enhanced
                + "\n\nPlease complete this task by creating the necessary files."
            )

            self.logger.info(
                f"{EMOJI['learn']} RAG enhancement: "
                f"{len(prompt)} → {len(enhanced)} chars"
            )

            return enhanced

        except Exception as e:
            self.logger.warning(f"RAG enhancement failed: {e}")
            return prompt

    def _execute_claude_cli(self, prompt: str, cwd: str) -> Dict[str, Any]:
        """Claude CLI実行"""
        if not self._check_claude_cli():
            return self._simulate_response(prompt)

        cmd = [
            "claude",
            "--model",
            self.model,
            "--allowedTools",
            "Edit,Write,FileSystem",
            "--print",
        ]

        self.logger.info(f"{EMOJI['ai']} Executing Claude CLI...")

        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=self.config.worker.timeout,
            )

            if result.returncode == 0:
                output = result.stdout.strip()

                # 短い応答の場合、生成ファイルを確認
                if len(output) < 50:
                    generated_files = self._find_recent_files(cwd)
                    if generated_files:
                        output = self._read_generated_file(generated_files[0])

                return {"success": True, "status": "completed", "output": output}
            else:
                return {
                    "success": False,
                    "status": "failed",
                    "output": f"Error: {result.stderr}",
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "status": "failed",
                "output": f"Timeout after {self.config.worker.timeout}s",
            }
        except Exception as e:
            return {
                "success": False,
                "status": "failed",
                "output": f"Execution error: {str(e)}",
            }

    def _check_claude_cli(self) -> bool:
        """Claude CLI利用可能チェック"""
        try:
            result = subprocess.run(["which", "claude"], capture_output=True)
            return result.returncode == 0
        except:
            return False

    def _find_recent_files(
        self, directory: str, max_age_seconds: int = 30
    ) -> List[str]:
        """最近生成されたファイルを検索"""
        current_time = time.time()
        recent_files = []

        patterns = ["*.py", "*.js", "*.html", "*.sh", "*.json"]

        for pattern in patterns:
            for file_path in glob.glob(os.path.join(directory, pattern)):
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age < max_age_seconds:
                        recent_files.append(file_path)

        return sorted(recent_files, key=lambda x: os.path.getmtime(x), reverse=True)

    def _read_generated_file(self, file_path: str) -> str:
        """生成されたファイルを読み込み"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            filename = os.path.basename(file_path)
            return f"Created {filename}:\n\n```python\n{content}\n```"
        except Exception as e:
            self.logger.error(f"Failed to read file {file_path}: {e}")
            return f"File created: {file_path}"

    def _handle_evolution(
        self, output: str, task_id: str, prompt: str
    ) -> Optional[Dict[str, Any]]:
        """自己進化処理"""
        try:
            self.logger.info(f"{EMOJI['evolution']} Starting self-evolution...")

            # SelfEvolutionManagerのメソッドを適切に呼び出す
            # 注: 実際のメソッド名に合わせて調整が必要
            result = None
            # TODO: self.evolution.auto_place_from_output(output, task_id, prompt)

            if result and result.get("success"):
                self.logger.info(
                    f"{EMOJI['success']} Self-evolution completed: "
                    f"{result.get('count', 0)} files"
                )
                return result
            else:
                self.logger.info(f"{EMOJI['info']} No evolution candidates found")
                return None

        except Exception as e:
            self.handle_error(e, "self-evolution")
            return None

    def _save_result(
        self,
        output_dir: Path,
        task_id: str,
        prompt: str,
        output: str,
        rag_applied: bool,
        evolution_result: Optional[Dict],
    ) -> None:
        """結果ファイル保存"""
        result_file = output_dir / "result.txt"

        try:
            with open(result_file, "w", encoding="utf-8") as f:
                f.write(f"=== Task Info ===\n")
                f.write(f"Task ID: {task_id}\n")
                f.write(f"Worker: {self.worker_id}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Model: {self.model}\n")
                f.write(f"RAG Applied: {'Yes' if rag_applied else 'No'}\n")
                f.write(f"Evolution: {'Yes' if evolution_result else 'No'}\n")
                f.write(f"\n=== Original Prompt ===\n{prompt}\n")
                f.write(f"\n=== Response ===\n{output}\n")

                if evolution_result:
                    f.write(f"\n=== Evolution Result ===\n")
                    f.write(json.dumps(evolution_result, indent=2))
                    f.write("\n")

                f.write("=== End ===\n")

            self.logger.info(f"{EMOJI['file']} Result saved: {result_file}")

        except Exception as e:
            self.handle_error(e, "save_result")

    def _save_to_rag(
        self, task_id: str, prompt: str, response: str, status: str, task_type: str
    ) -> None:
        """RAG履歴保存"""
        try:
            self.rag.save_task_with_summary(
                task_id=task_id,
                worker=self.worker_id,
                prompt=prompt,
                response=response,
                status=status,
                task_type=task_type,
            )
            self.logger.info(f"{EMOJI['database']} RAG history saved")
        except Exception as e:
            self.handle_error(e, "save_to_rag")

    def _send_slack_notification(
        self,
        task_id: str,
        prompt: str,
        response: str,
        status: str,
        task_type: str,
        rag_applied: bool,
        evolution_result: Optional[Dict],
    ) -> None:
        """Slack通知送信"""
        if not self.config.slack.enabled:
            return

        try:
            # 自己進化情報を追加
            if evolution_result and evolution_result.get("success"):
                evolved_files = evolution_result.get("evolved_files", [])
                if evolved_files:
                    response += f"\n{EMOJI['evolution']} Self-evolution: "
                    response += evolved_files[0]["relative_path"]

            success = self.slack.send_task_completion_simple(
                task_id=task_id,
                worker=self.worker_id,
                prompt=prompt,
                response=response,
                status=status,
                task_type=task_type,
                rag_applied=rag_applied,
            )

            if success:
                self.logger.info(f"{EMOJI['mobile']} Slack notification sent")
            else:
                self.logger.warning("Slack notification failed")

        except Exception as e:
            self.handle_error(e, "slack_notification")

    def _simulate_response(self, prompt: str) -> Dict[str, Any]:
        """シミュレーション応答（Claude CLI不在時）"""
        self.logger.warning("Running in simulation mode")

        prompt_lower = prompt.lower()

        if "hello" in prompt_lower:
            output = """print("Hello, Elders Guild!")"""
        elif "fibonacci" in prompt_lower:
            output = """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

for i in range(10):
    print(f"fibonacci({i}) = {fibonacci(i)}")"""
        else:
            output = f"[Simulated] Task completed: {prompt[:50]}..."

        return {"success": True, "status": "completed", "output": output}


def main():
    """メイン実行"""
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced Task Worker with base class")
    parser.add_argument(
        "--worker-id", default=None, help="Worker ID (default: auto-generated)"
    )

    args = parser.parse_args()

    # ワーカー起動
    worker = EnhancedTaskWorker(worker_id=args.worker_id)
    worker.start()


if __name__ == "__main__":
    main()
