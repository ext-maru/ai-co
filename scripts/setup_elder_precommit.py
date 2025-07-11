#!/usr/bin/env python3
"""
🏛️ エルダーズギルド Pre-commit セットアップ
開発標準の自動適用を設定
"""

import subprocess
import sys
from pathlib import Path


# カラー出力
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header():
    """ヘッダー表示"""
    print(f"\n{Colors.PURPLE}{Colors.BOLD}🏛️ エルダーズギルド Pre-commit Setup{Colors.ENDC}")
    print("=" * 50)


def check_pre_commit_installed():
    """pre-commitインストール確認"""
    try:
        result = subprocess.run(["pre-commit", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"{Colors.GREEN}✅ {version} がインストール済み{Colors.ENDC}")
            return True
    except FileNotFoundError:
        pass

    print(f"{Colors.YELLOW}⚠️  pre-commit がインストールされていません{Colors.ENDC}")
    return False


def install_pre_commit():
    """pre-commitインストール"""
    print(f"\n{Colors.BLUE}📦 pre-commit をインストール中...{Colors.ENDC}")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pre-commit"], check=True)
        print(f"{Colors.GREEN}✅ pre-commit インストール完了{Colors.ENDC}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}❌ インストール失敗: {e}{Colors.ENDC}")
        return False


def install_hooks():
    """pre-commitフックインストール"""
    print(f"\n{Colors.BLUE}🔗 フックをインストール中...{Colors.ENDC}")
    try:
        subprocess.run(["pre-commit", "install"], check=True)
        subprocess.run(["pre-commit", "install", "--hook-type", "post-commit"], check=True)
        print(f"{Colors.GREEN}✅ フックインストール完了{Colors.ENDC}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}❌ フックインストール失敗: {e}{Colors.ENDC}")
        return False


def run_initial_check():
    """初回チェック実行"""
    print(f"\n{Colors.BLUE}🔍 初回チェックを実行中...{Colors.ENDC}")
    print(f"{Colors.YELLOW}（初回は依存関係のダウンロードに時間がかかります）{Colors.ENDC}")

    try:
        # すべてのファイルに対して実行（初回のみ）
        subprocess.run(["pre-commit", "run", "--all-files"], check=False)
        print(f"\n{Colors.GREEN}✅ 初回チェック完了{Colors.ENDC}")
        return True
    except subprocess.CalledProcessError:
        print(f"\n{Colors.YELLOW}⚠️  一部のチェックで問題が検出されました{Colors.ENDC}")
        return False


def create_gitignore_entries():
    """必要な.gitignoreエントリ追加"""
    gitignore_path = Path(".gitignore")
    entries_to_add = ["\n# Pre-commit", ".pre-commit-config.yaml.lock", ".pdca/", "COSTAR_*.md"]

    if gitignore_path.exists():
        content = gitignore_path.read_text()
        new_entries = []
        for entry in entries_to_add:
            if entry.strip() and entry.strip() not in content:
                new_entries.append(entry)

        if new_entries:
            with gitignore_path.open("a") as f:
                f.write("\n")
                f.write("\n".join(new_entries))
                f.write("\n")
            print(f"\n{Colors.GREEN}✅ .gitignore 更新完了{Colors.ENDC}")


def display_usage_guide():
    """使用ガイド表示"""
    print(f"\n{Colors.PURPLE}{Colors.BOLD}📚 使用ガイド{Colors.ENDC}")
    print("=" * 50)
    print(
        f"""
{Colors.BLUE}通常のコミット:{Colors.ENDC}
  git add .
  git commit -m "コミットメッセージ"
  → 自動的にエルダー標準チェックが実行されます

{Colors.BLUE}手動チェック:{Colors.ENDC}
  pre-commit run --all-files   # 全ファイルチェック
  pre-commit run --files <file> # 特定ファイルチェック

{Colors.BLUE}フック一時無効化:{Colors.ENDC}
  git commit --no-verify       # 緊急時のみ使用

{Colors.BLUE}エルダー標準チェックのみ:{Colors.ENDC}
  python scripts/check_elder_standards.py

{Colors.PURPLE}品質基準:{Colors.ENDC}
  ✅ CO-STAR文書
  ✅ TDD準拠
  ✅ PDCAトラッキング
  ✅ GUI標準
  ✅ エルダーデコレーター
"""
    )


def main():
    """メイン処理"""
    print_header()

    # 1. pre-commit確認とインストール
    if not check_pre_commit_installed():
        if not install_pre_commit():
            print(f"\n{Colors.RED}セットアップ失敗: pre-commitをインストールしてください{Colors.ENDC}")
            return 1

    # 2. フックインストール
    if not install_hooks():
        return 1

    # 3. gitignore更新
    create_gitignore_entries()

    # 4. 初回チェック（オプション）
    response = input(f"\n{Colors.YELLOW}初回チェックを実行しますか？ (y/N): {Colors.ENDC}")
    if response.lower() == "y":
        run_initial_check()

    # 5. 使用ガイド表示
    display_usage_guide()

    print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 エルダーズギルド Pre-commit セットアップ完了！{Colors.ENDC}")
    print(f"{Colors.BLUE}品質第一の開発を実現しましょう！{Colors.ENDC}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
