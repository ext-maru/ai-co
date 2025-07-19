#!/usr/bin/env python3
"""
🏛️ エルダーズギルド プロジェクトダッシュボード起動スクリプト
"""

import os
import subprocess
import sys
import time
import webbrowser
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


def print_banner():
    """バナー表示"""
    print(
        f"""
{Colors.PURPLE}{Colors.BOLD}
    🏛️  エルダーズギルド プロジェクト管理システム
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Redmineライクなプロジェクト管理をファンタジーの世界で
{Colors.ENDC}
    """
    )


def check_dependencies():
    """依存関係チェック"""
    try:
        import flask
        import flask_cors

        return True
    except ImportError:
        print(
            f"{Colors.YELLOW}⚠️  必要なパッケージがインストールされていません{Colors.ENDC}"
        )
        print(f"{Colors.BLUE}インストール中...{Colors.ENDC}")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "flask", "flask-cors"], check=True
        )
        return True


def start_dashboard():
    """ダッシュボード起動"""
    print_banner()

    if not check_dependencies():
        print(f"{Colors.RED}❌ 依存関係のインストールに失敗しました{Colors.ENDC}")
        return 1

    # プロジェクトパス設定
    project_root = Path(__file__).parent
    dashboard_path = project_root / "web" / "project_dashboard.py"

    if not dashboard_path.exists():
        print(
            f"{Colors.RED}❌ ダッシュボードファイルが見つかりません: {dashboard_path}{Colors.ENDC}"
        )
        return 1

    print(f"{Colors.BLUE}🚀 プロジェクトダッシュボードを起動中...{Colors.ENDC}")
    print(f"{Colors.GREEN}📍 URL: http://localhost:8080{Colors.ENDC}")
    print(f"{Colors.YELLOW}📋 Ctrl+C で終了{Colors.ENDC}\n")

    # 3秒後にブラウザを開く
    print(f"{Colors.BLUE}3秒後にブラウザを開きます...{Colors.ENDC}")
    time.sleep(3)

    try:
        # ブラウザを開く
        webbrowser.open("http://localhost:8080")
    except:
        print(
            f"{Colors.YELLOW}ブラウザを自動で開けませんでした。手動で http://localhost:8080 にアクセスしてください{Colors.ENDC}"
        )

    # ダッシュボード起動
    try:
        subprocess.run([sys.executable, str(dashboard_path)], check=True)
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}✅ ダッシュボードを終了しました{Colors.ENDC}")
        return 0
    except Exception as e:
        print(f"\n{Colors.RED}❌ エラーが発生しました: {e}{Colors.ENDC}")
        return 1


def main():
    """メイン処理"""
    return start_dashboard()


if __name__ == "__main__":
    sys.exit(main())
