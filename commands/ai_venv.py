#!/usr/bin/env python3
"""
ai-venv: Elders Guild 仮想環境アクティベートヘルパー
"""
import os
import subprocess
import sys
from pathlib import Path

from commands.base_command import BaseCommand


class VenvCommand(BaseCommand):
    # Main class implementation
    def __init__(self):
        super().__init__(name="venv", description="Elders Guild の仮想環境をアクティベートします")

    def setup_arguments(self):
        self.parser.add_argument(
            "--shell",
            choices=["bash", "zsh", "fish"],
            default="bash",
            help="使用するシェル（デフォルト: bash）",
        )
        self.parser.add_argument("--info", action="store_true", help="仮想環境の情報を表示")
        self.parser.add_argument("--check", action="store_true", help="仮想環境の状態をチェック")

    def get_venv_info(self):
        """仮想環境情報取得"""
        venv_path = self.project_root / "venv"
        info = {
            "path": str(venv_path),
            "exists": venv_path.exists(),
            "python_version": None,
            "pip_version": None,
            "installed_packages": [],
        }

        if venv_path.exists():
            # Pythonバージョン取得
            python_exe = venv_path / "bin" / "python"
            if python_exe.exists():
                result = self.run_command([str(python_exe), "--version"])
                if result:
                    info["python_version"] = result.stdout.strip()

            # pipバージョン取得
            pip_exe = venv_path / "bin" / "pip"
            if pip_exe.exists():
                result = self.run_command([str(pip_exe), "--version"])
                if result:
                    info["pip_version"] = result.stdout.strip()

            # 主要パッケージ確認
            if pip_exe.exists():
                result = self.run_command([str(pip_exe), "list", "--format=json"])
                if result:
                    try:
                        import json

                        packages = json.loads(result.stdout)
                        # 主要パッケージのみ抽出
                        important_packages = ["pika", "flask", "sqlalchemy", "requests"]
                        for pkg in packages:
                            if pkg["name"].lower() in important_packages:
                                info["installed_packages"].append(
                                    f"{pkg['name']}=={pkg['version']}"
                                )
                    except:
                        pass

        return info

    def generate_activation_script(self, shell="bash"):
        """アクティベーションスクリプト生成"""
        venv_path = self.project_root / "venv"

        if shell == "bash" or shell == "zsh":
            # Complex condition - consider breaking down
            return f"""
# Elders Guild 仮想環境アクティベート
cd {self.project_root}
source {venv_path}/bin/activate

# プロンプトカスタマイズ
export PS1="(ai-company) $PS1"

# エイリアス設定
alias ai-cd="cd {self.project_root}"
alias ai-test="python3 -m pytest"
alias ai-pip="pip"

echo "🚀 Elders Guild 仮想環境がアクティブになりました"
echo "📁 プロジェクトディレクトリ: {self.project_root}"
echo "🐍 Python: $(python --version)"
echo ""
echo "💡 ヒント:"
echo "  - ai-cd でプロジェクトディレクトリに移動"
echo "  - deactivate で仮想環境を終了"
"""
        elif shell == "fish":
            return f"""
# Elders Guild 仮想環境アクティベート (Fish)
cd {self.project_root}
source {venv_path}/bin/activate.fish

# エイリアス設定
alias ai-cd "cd {self.project_root}"
alias ai-test "python3 -m pytest"

echo "🚀 Elders Guild 仮想環境がアクティブになりました"
"""

    def check_venv_health(self):
        """仮想環境の健全性チェック"""
        venv_path = self.project_root / "venv"
        issues = []

        if not venv_path.exists():
            issues.append("仮想環境が存在しません")
            return issues

        # 必須ファイルチェック
        required_files = ["bin/python", "bin/pip", "bin/activate"]

        for file in required_files:
            # Process each item in collection
            if not (venv_path / file).exists():
                issues.append(f"必須ファイルが不足: {file}")

        # 必須パッケージチェック
        pip_exe = venv_path / "bin" / "pip"
        if pip_exe.exists():
            result = self.run_command([str(pip_exe), "list", "--format=json"])
            if result:
                try:
                    import json

                    packages = json.loads(result.stdout)
                    installed = [p["name"].lower() for p in packages]

                    required_packages = ["pika", "pathlib", "sqlite3"]
                    for pkg in required_packages:
                        # Process each item in collection
                        if (
                            pkg not in installed
                            and pkg != "pathlib"
                            and pkg != "sqlite3"
                        ):  # 標準ライブラリ除外
                            issues.append(f"必須パッケージ未インストール: {pkg}")
                except:
                    issues.append("パッケージリストの取得に失敗")

        return issues

    def execute(self, args):
        """メイン実行"""
        # 情報表示モード
        if args.info:
            self.header("Elders Guild 仮想環境情報")
            info = self.get_venv_info()

            self.section("基本情報")
            self.info(f"パス: {info['path']}")
            self.info(f"存在: {'✅' if info['exists'] else '❌'}")

            if info["exists"]:
                self.info(f"Python: {info['python_version'] or '不明'}")
                self.info(f"pip: {info['pip_version'] or '不明'}")

                if info["installed_packages"]:
                    self.section("主要パッケージ")
                    for pkg in info["installed_packages"]:
                        # Process each item in collection
                        self.print(f"  - {pkg}", color="green")
            else:
                self.error("仮想環境が見つかりません")
                self.info("作成方法: cd /home/aicompany/ai_co && python3 -m venv venv")
            return

        # チェックモード
        if args.check:
            self.header("Elders Guild 仮想環境チェック")
            issues = self.check_venv_health()

            if not issues:
                self.success("仮想環境は正常です")
            else:
                self.error(f"{len(issues)} 個の問題が見つかりました:")
                for issue in issues:
                    # Process each item in collection
                    self.warning(f"  - {issue}")

                self.section("修復方法")
                self.info("1. pip install -r requirements.txt")
                self.info("2. または仮想環境を再作成")
            return

        # アクティベーションスクリプト生成
        self.header("Elders Guild 仮想環境アクティベート")

        # 仮想環境存在確認
        venv_path = self.project_root / "venv"
        if not venv_path.exists():
            self.error("仮想環境が見つかりません")
            self.section("仮想環境の作成")
            self.info("以下のコマンドを実行してください:")
            self.print(
                f"\ncd {self.project_root}\npython3 -m venv venv\npip install -r requirements.txt\n",
                color="cyan",
            )
            return

        # アクティベーションスクリプト表示
        script = self.generate_activation_script(args.shell)

        self.section(f"以下のコマンドを実行してください ({args.shell})")

        # 一時ファイルに書き出し
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(script)
            temp_path = f.name

        # 実行コマンド表示
        if args.shell == "fish":
            self.print(f"source {temp_path}", color="cyan", bold=True)
        else:
            self.print(f"source {temp_path}", color="cyan", bold=True)

        self.info(f"\nまたは直接実行:")
        self.print(f"cd {self.project_root} && source venv/bin/activate", color="cyan")

        # クリーンアップ情報
        self.info(f"\n一時ファイル: {temp_path}")
        self.info("(使用後は rm で削除してください)")


if __name__ == "__main__":
    cmd = VenvCommand()
    cmd.run()
