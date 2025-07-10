#!/usr/bin/env python3
"""
権限設定問題を修正するスクリプト
root/sudo権限とClaude CLIの競合を解決
"""

import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_current_permissions():
    """現在の権限状態をチェック"""
    uid = os.getuid()
    euid = os.geteuid()
    username = os.getenv("USER", "unknown")

    logger.info(f"Current user: {username}")
    logger.info(f"UID: {uid}, EUID: {euid}")
    logger.info(f"Running as root: {euid == 0}")

    # sudoで実行されているかチェック
    sudo_user = os.getenv("SUDO_USER")
    if sudo_user:
        logger.warning(f"Script was run with sudo by user: {sudo_user}")
        return False

    if euid == 0:
        logger.error("Script is running as root! This will cause issues with Claude CLI.")
        return False

    return True


def fix_ai_start_permissions():
    """ai_start.pyの権限問題を修正"""
    ai_start_path = PROJECT_ROOT / "commands" / "ai_start.py"

    if not ai_start_path.exists():
        logger.warning(f"ai_start.py not found at {ai_start_path}")
        return False

    # ファイルを読み込み
    content = ai_start_path.read_text()

    # sudo systemctl start rabbitmq-serverの部分を修正
    original_line = "self.run_command(['sudo', 'systemctl', 'start', 'rabbitmq-server'])"

    if original_line in content:
        # RabbitMQが既に起動しているかチェックする処理を追加
        replacement = """# RabbitMQの起動（sudoが必要な場合は事前に起動しておく）
        try:
            # まずステータスをチェック
            result = subprocess.run(['systemctl', 'is-active', 'rabbitmq-server'],
                                    capture_output=True, text=True)
            if result.returncode != 0:
                self.console.print("[yellow]⚠️  RabbitMQが起動していません。")
                self.console.print("[yellow]   事前に以下のコマンドを実行してください:")
                self.console.print("[blue]   sudo systemctl start rabbitmq-server[/blue]")
                # sudoなしでの起動を試みる（権限があれば成功）
                self.run_command(['systemctl', 'start', 'rabbitmq-server'])
        except subprocess.CalledProcessError:
            self.console.print("[yellow]⚠️  RabbitMQ起動をスキップしました（権限不足）[/yellow]")"""

        content = content.replace(original_line, replacement)

        # バックアップを作成
        backup_path = ai_start_path.with_suffix(".py.bak")
        ai_start_path.rename(backup_path)
        logger.info(f"Backup created: {backup_path}")

        # 修正版を保存
        ai_start_path.write_text(content)
        logger.info("Fixed ai_start.py permissions")
        return True
    else:
        logger.info("ai_start.py already fixed or has different content")
        return True


def fix_claude_startup_permissions():
    """claude_auto_startup_workflow.pyにroot権限チェックを追加"""
    claude_startup_path = PROJECT_ROOT / "claude_auto_startup_workflow.py"

    if not claude_startup_path.exists():
        logger.warning("claude_auto_startup_workflow.py not found")
        return False

    content = claude_startup_path.read_text()

    # _start_claude_cli_dangerousメソッドを探す
    if "def _start_claude_cli_dangerous(self):" in content:
        # root権限チェックを追加
        check_code = '''def _start_claude_cli_dangerous(self):
        """Claudeを危険モードで起動（権限チェック付き）"""
        # Root権限チェック
        if os.geteuid() == 0:
            self.console.print("❌ [red]エラー: Claude CLIはroot/sudo権限では実行できません[/red]")
            self.console.print("💡 [yellow]通常ユーザーとして実行してください[/yellow]")
            self.console.print("   例: ai-elder-cc (sudoなし)")
            return None

        '''

        # 既存のチェックがない場合のみ追加
        if "os.geteuid() == 0" not in content:
            content = content.replace("def _start_claude_cli_dangerous(self):", check_code)

            # importも追加
            if "import os" not in content:
                content = "import os\n" + content

            # バックアップ作成
            backup_path = claude_startup_path.with_suffix(".py.bak")
            claude_startup_path.rename(backup_path)
            logger.info(f"Backup created: {backup_path}")

            # 修正版を保存
            claude_startup_path.write_text(content)
            logger.info("Added root permission check to claude_auto_startup_workflow.py")
            return True
        else:
            logger.info("Root permission check already exists")
            return True
    else:
        logger.warning("Could not find _start_claude_cli_dangerous method")
        return False


def create_permission_wrapper():
    """権限チェックラッパースクリプトを作成"""
    wrapper_content = '''#!/usr/bin/env python3
"""
Elders Guild コマンド実行時の権限チェックラッパー
root/sudo実行を防ぐ
"""
import os
import sys
import subprocess

def check_and_run(command_args):
    """権限チェックしてからコマンドを実行"""
    if os.geteuid() == 0:
        print("❌ エラー: このコマンドはroot/sudo権限では実行できません")
        print("💡 通常ユーザーとして実行してください")
        print(f"   例: {' '.join(command_args)} (sudoなし)")
        sys.exit(1)

    # sudoで実行されているかチェック
    if os.getenv('SUDO_USER'):
        print("❌ エラー: sudoを使用しないでください")
        print(f"💡 直接実行してください: {' '.join(command_args)}")
        sys.exit(1)

    # 権限OKなら元のコマンドを実行
    try:
        subprocess.run(command_args, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: permission_check.py <command> [args...]")
        sys.exit(1)

    check_and_run(sys.argv[1:])
'''

    wrapper_path = PROJECT_ROOT / "scripts" / "permission_check.py"
    wrapper_path.write_text(wrapper_content)
    wrapper_path.chmod(0o755)  # 実行権限付与
    logger.info(f"Permission wrapper created: {wrapper_path}")

    return wrapper_path


def show_recommendations():
    """推奨事項を表示"""
    print("\n" + "=" * 60)
    print("🔧 権限設定修正完了！")
    print("=" * 60)
    print("\n📋 今後の推奨事項:")
    print("1. Elders Guildコマンドは通常ユーザーで実行:")
    print("   ✅ ai-elder-cc")
    print("   ✅ ai-start")
    print("   ❌ sudo ai-elder-cc")
    print("   ❌ sudo ai-start")
    print("\n2. RabbitMQは事前に起動:")
    print("   sudo systemctl start rabbitmq-server")
    print("   (一度起動すれば、その後はsudo不要)")
    print("\n3. 権限エラーが出た場合:")
    print("   - 現在のユーザーを確認: whoami")
    print("   - root以外であることを確認")
    print("   - sudoを使っていないことを確認")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    logger.info("Starting permission configuration fix...")

    # 現在の権限チェック
    if not check_current_permissions():
        logger.error("Please run this script as a regular user (not root/sudo)")
        sys.exit(1)

    # 修正実行
    success = True

    # ai_start.pyの修正
    if not fix_ai_start_permissions():
        success = False

    # claude_auto_startup_workflow.pyの修正
    if not fix_claude_startup_permissions():
        success = False

    # 権限チェックラッパーの作成
    create_permission_wrapper()

    if success:
        show_recommendations()
        logger.info("Permission fixes completed successfully!")
    else:
        logger.error("Some fixes failed. Please check the logs.")
        sys.exit(1)
