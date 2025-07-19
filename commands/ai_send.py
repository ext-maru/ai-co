#!/usr/bin/env python3
"""
ai-send: Elders Guild タスク送信コマンド
"""
import json
import time
from datetime import datetime

import pika

from commands.base_command import BaseCommand


class SendCommand(BaseCommand):
    def __init__(self):
        super().__init__(name="send", description="Elders Guild にタスクを送信します")

    def setup_arguments(self):
        self.parser.add_argument("prompt", help="実行するタスクのプロンプト")
        self.parser.add_argument(
            "type",
            nargs="?",
            default="general",
            choices=["general", "code", "analysis", "report"],
            help="タスクタイプ (デフォルト: general)",
        )
        self.parser.add_argument(
            "--priority",
            type=int,
            default=5,
            choices=range(1, 11),
            help="優先度 1-10 (デフォルト: 5)",
        )
        self.parser.add_argument("--tags", nargs="+", help="タスクタグ")
        self.parser.add_argument(
            "--no-wait", action="store_true", help="送信後すぐに終了（結果を待たない）"
        )
        self.parser.add_argument("--json", action="store_true", help="JSON形式で結果を出力")
        self.parser.add_argument(
            "--test-first", action="store_true", help="TDDモード: テストを先に生成してから実装"
        )

    def check_system_ready(self):
        """システム準備確認"""
        # RabbitMQ確認
        result = self.run_command(["systemctl", "is-active", "rabbitmq-server"])
        if not result or result.stdout.strip() != "active":
            self.error("RabbitMQが起動していません")
            self.info("ai-start でシステムを起動してください")
            return False

        # ワーカー確認
        workers = self.check_process("task_worker")
        if not workers:
            self.warning("タスクワーカーが起動していません")
            self.info("ai-start でシステムを起動してください")
            return False

        return True

    def send_task(self, prompt, task_type, priority, tags, test_first=False):
        """タスク送信（TDDサポート付き）"""
        conn = self.get_rabbitmq_connection()
        if not conn:
            self.error("RabbitMQに接続できません")
            return None

        try:
            channel = conn.channel()
            channel.queue_declare(queue="task_queue", durable=True)

            # タスクID生成
            task_id = f"{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:17]}"

            # タスクデータ
            task = {
                "task_id": task_id,
                "type": task_type,
                "prompt": prompt,
                "priority": priority,
                "tags": tags or [],
                "test_first": test_first,
                "created_at": datetime.now().isoformat(),
            }

            # TDDモードの場合、先にテスト生成タスクを送信
            if test_first:
                test_task = {
                    "task_id": f"test_{task_id}",
                    "type": "test_generation",
                    "prompt": f"Generate tests for: {prompt}",
                    "original_task": task,
                    "priority": priority + 1,  # テスト生成を優先
                    "created_at": datetime.now().isoformat(),
                }

                # テスト生成タスクを送信
                channel.basic_publish(
                    exchange="",
                    routing_key="task_queue",
                    body=json.dumps(test_task),
                    properties=pika.BasicProperties(
                        delivery_mode=2, priority=priority + 1
                    ),
                )
                self.info("📝 TDDモード: テスト生成タスクを送信しました")

            # メインタスクを送信
            channel.basic_publish(
                exchange="",
                routing_key="task_queue",
                body=json.dumps(task),
                properties=pika.BasicProperties(delivery_mode=2, priority=priority),
            )

            conn.close()
            return task_id

        except Exception as e:
            self.error(f"タスク送信エラー: {e}")
            return None

    def wait_for_result(self, task_id, timeout=300):
        """結果待機"""
        start_time = datetime.now()
        result_path = None

        self.info("処理中", end="", flush=True)

        while (datetime.now() - start_time).seconds < timeout:
            # 結果ファイル検索
            for path in self.output_dir.rglob(f"*{task_id}*/result.txt"):
                result_path = path
                break

            if result_path and result_path.exists():
                print()  # 改行
                return result_path

            # プログレス表示
            print(".", end="", flush=True)
            time.sleep(2)

        print()  # 改行
        self.warning("タイムアウト: 結果を取得できませんでした")
        return None

    def display_result(self, result_path):
        """結果表示"""
        try:
            with open(result_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 結果セクション抽出
            sections = {}
            current_section = None
            section_content = []

            for line in content.split("\n"):
                if line.startswith("===") and line.endswith("==="):
                    if current_section:
                        sections[current_section] = "\n".join(section_content)
                    current_section = line.strip("= ")
                    section_content = []
                else:
                    section_content.append(line)

            if current_section:
                sections[current_section] = "\n".join(section_content)

            # 主要な情報表示
            self.section("タスク情報")
            if "Task Info" in sections:
                for line in sections["Task Info"].strip().split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        self.info(f"{key.strip()}: {value.strip()}")

            # 応答表示
            self.section("応答")
            if "Response" in sections:
                response = sections["Response"].strip()
                # 最初の500文字を表示
                if len(response) > 500:
                    print(response[:500] + "...")
                    self.info(f"\n(全体: {len(response)} 文字)")
                else:
                    print(response)

            # ファイルパス
            self.info(f"\n詳細: {result_path}")

        except Exception as e:
            self.error(f"結果表示エラー: {e}")

    def execute(self, args):
        """メイン実行"""
        # ヘッダー
        if not args.json:
            self.header("Elders Guild タスク送信")

        # システム確認
        if not self.check_system_ready():
            return

        # タスク送信
        if not args.json:
            self.section("タスク送信")
            self.info(
                f"プロンプト: {args.prompt[:100]}{'...' if len(args.prompt) > 100 else ''}"
            )
            self.info(f"タイプ: {args.type}")
            self.info(f"優先度: {args.priority}")
            if args.tags:
                self.info(f"タグ: {', '.join(args.tags)}")

        task_id = self.send_task(
            args.prompt, args.type, args.priority, args.tags, args.test_first
        )

        if not task_id:
            return

        if args.json:
            # JSON出力
            result = {
                "task_id": task_id,
                "status": "sent",
                "timestamp": datetime.now().isoformat(),
            }

            if not args.no_wait:
                result_path = self.wait_for_result(task_id)
                if result_path:
                    with open(result_path, "r", encoding="utf-8") as f:
                        result["result"] = f.read()
                    result["status"] = "completed"
                else:
                    result["status"] = "timeout"

            print(json.dumps(result, indent=2))

        else:
            # 通常出力
            self.success(f"タスク送信成功: {task_id}")

            # 結果待機
            if not args.no_wait:
                self.section("結果待機")
                result_path = self.wait_for_result(task_id)

                if result_path:
                    self.success("処理完了！")
                    self.display_result(result_path)
                else:
                    self.info("後で ai-task-info コマンドで結果を確認できます")


if __name__ == "__main__":
    cmd = SendCommand()
    cmd.run()
