#!/usr/bin/env python3
"""
ai-code: Elders Guild コード生成タスクショートカット
ai-send "..." code のエイリアス
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ai_send import SendCommand


class CodeCommand(SendCommand):
    def __init__(self):
        # SendCommandを継承して初期化
        super().__init__()
        self.name = "code"
        self.description = "Elders Guild にコード生成タスクを送信します（ai-send のショートカット）"

        # パーサーを再設定
        self.parser.prog = "ai-code"
        self.parser.description = self.description

    def setup_arguments(self):
        # プロンプトのみ必須、タイプは自動的に'code'
        self.parser.add_argument("prompt", help="生成するコードの説明")
        # タイプ引数は削除（常に'code'）
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

    def execute(self, args):
        # タイプを'code'に固定
        args.type = "code"
        # 親クラスのexecuteを呼び出し
        super().execute(args)


def main():
    cmd = CodeCommand()
    return cmd.run()


if __name__ == "__main__":
    import sys

    sys.exit(main())
