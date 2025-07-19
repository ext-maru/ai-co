#!/usr/bin/env python3
"""
🧠 プロジェクト知能システム起動スクリプト
"""

import os
import subprocess
import sys
import time
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
    🧠  エルダーズギルド プロジェクト知能システム
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    日次自動学習・改善システム
    プロジェクトから学習し、テンプレートを自動改善
{Colors.ENDC}
    """
    )


def check_dependencies():
    """依存関係チェック"""
    required_modules = ["asyncio", "sqlite3", "json", "pathlib"]
    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        print(
            f"{Colors.RED}❌ 不足モジュール: {', '.join(missing_modules)}{Colors.ENDC}"
        )
        return False

    return True


def show_menu():
    """メニュー表示"""
    print(
        f"""
{Colors.BLUE}🎯 利用可能なオプション:{Colors.ENDC}

1. 📊 日次知能サイクル実行
2. 📅 自動スケジュール開始
3. 🏛️ 評議会状況確認
4. 📋 レポート表示
5. 📈 統計情報表示
6. 🔧 テストモード
7. 🚪 終了

{Colors.YELLOW}💡 ヒント:{Colors.ENDC}
- 通常は「2」で自動スケジュールを開始してください
- 初回は「1」で手動実行して動作確認をお勧めします
    """
    )


def run_option(option: str):
    """オプション実行"""
    project_root = Path(__file__).parent
    intelligence_cmd = project_root / "commands" / "ai_project_intelligence.py"

    commands = {
        "1": ["python3", str(intelligence_cmd), "daily"],
        "2": ["python3", str(intelligence_cmd), "schedule", "--daemon"],
        "3": ["python3", str(intelligence_cmd), "council-status"],
        "4": ["python3", str(intelligence_cmd), "report", "2025-07-11"],
        "5": ["python3", str(intelligence_cmd), "stats"],
        "6": ["python3", str(intelligence_cmd), "daily", "--force"],
    }

    if option not in commands:
        print(f"{Colors.RED}❌ 無効なオプション: {option}{Colors.ENDC}")
        return False

    try:
        print(f"{Colors.BLUE}🚀 実行中...{Colors.ENDC}")
        subprocess.run(commands[option], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}❌ 実行エラー: {e}{Colors.ENDC}")
        return False
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}🛑 ユーザーによる中断{Colors.ENDC}")
        return True


def create_systemd_service():
    """systemdサービス作成"""
    service_content = f"""[Unit]
Description=Elders Guild Project Intelligence System
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'aicompany')}
WorkingDirectory={Path(__file__).parent}
ExecStart=/usr/bin/python3 {Path(__file__).parent}/commands/ai_project_intelligence.py schedule --daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    service_file = Path("/etc/systemd/system/elders-guild-intelligence.service")

    try:
        with open(service_file, "w") as f:
            f.write(service_content)

        print(f"{Colors.GREEN}✅ systemdサービス作成完了{Colors.ENDC}")
        print(f"{Colors.BLUE}📋 サービス管理コマンド:{Colors.ENDC}")
        print(f"  sudo systemctl start elders-guild-intelligence")
        print(f"  sudo systemctl enable elders-guild-intelligence")
        print(f"  sudo systemctl status elders-guild-intelligence")

        return True

    except PermissionError:
        print(
            f"{Colors.YELLOW}⚠️  systemdサービス作成にはsudo権限が必要です{Colors.ENDC}"
        )
        print(f"{Colors.BLUE}💡 手動でサービスを作成してください:{Colors.ENDC}")
        print(
            f"  sudo tee /etc/systemd/system/elders-guild-intelligence.service << 'EOF'"
        )
        print(service_content)
        print("EOF")
        return False
    except Exception as e:
        print(f"{Colors.RED}❌ systemdサービス作成エラー: {e}{Colors.ENDC}")
        return False


def show_quick_start():
    """クイックスタートガイド"""
    print(
        f"""
{Colors.GREEN}{Colors.BOLD}🚀 クイックスタートガイド{Colors.ENDC}

{Colors.BLUE}1. 初回セットアップ{Colors.ENDC}
   このスクリプトを実行 → オプション「1」で動作確認

{Colors.BLUE}2. 自動運用開始{Colors.ENDC}
   オプション「2」で自動スケジュール開始
   または systemd サービスとして登録

{Colors.BLUE}3. 日常運用{Colors.ENDC}
   - 毎日午前6時に自動実行
   - エルダー評議会への自動報告
   - 承認された改善の自動適用

{Colors.BLUE}4. 監視・管理{Colors.ENDC}
   - オプション「3」で評議会状況確認
   - オプション「4」で日次レポート確認
   - オプション「5」で統計情報確認

{Colors.PURPLE}💡 効果:{Colors.ENDC}
- プロジェクトから自動学習
- テンプレートの継続的改善
- 開発効率の向上
- 品質の自動向上
    """
    )


def main():
    """メイン処理"""
    print_banner()

    # 依存関係チェック
    if not check_dependencies():
        return 1

    # 実行権限確認
    intelligence_cmd = Path(__file__).parent / "commands" / "ai_project_intelligence.py"
    if not intelligence_cmd.exists():
        print(
            f"{Colors.RED}❌ コマンドファイルが見つかりません: {intelligence_cmd}{Colors.ENDC}"
        )
        return 1

    # 実行権限付与
    try:
        intelligence_cmd.chmod(0o755)
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  実行権限設定エラー: {e}{Colors.ENDC}")

    # メニュー表示
    while True:
        show_menu()

        try:
            option = input(
                f"{Colors.BLUE}選択してください (1-7): {Colors.ENDC}"
            ).strip()

            if option == "7":
                print(
                    f"{Colors.GREEN}👋 エルダーズギルドがプロジェクトを見守っています{Colors.ENDC}"
                )
                break
            elif option == "h" or option == "help":
                show_quick_start()
                input(f"\n{Colors.BLUE}Enterキーで続行...{Colors.ENDC}")
                continue
            elif option == "service":
                create_systemd_service()
                input(f"\n{Colors.BLUE}Enterキーで続行...{Colors.ENDC}")
                continue

            success = run_option(option)

            if not success:
                input(f"\n{Colors.BLUE}Enterキーで続行...{Colors.ENDC}")
            elif option == "2":
                # スケジュール開始の場合は継続実行
                break
            else:
                input(f"\n{Colors.BLUE}Enterキーで続行...{Colors.ENDC}")

        except KeyboardInterrupt:
            print(
                f"\n{Colors.GREEN}👋 エルダーズギルドがプロジェクトを見守っています{Colors.ENDC}"
            )
            break
        except Exception as e:
            print(f"{Colors.RED}❌ エラー: {e}{Colors.ENDC}")
            input(f"\n{Colors.BLUE}Enterキーで続行...{Colors.ENDC}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
