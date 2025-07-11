#!/usr/bin/env python3
"""
軽量品質ステータスチェック用スクリプト
大規模処理を避けて、現在の状態を素早く確認
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def get_current_phase():
    """現在のフェーズを判定"""
    config_file = PROJECT_ROOT / '.pre-commit-config.yaml'
    if not config_file.exists():
        return 0

    content = config_file.read_text()

    if 'mypy' in content and 'tdd-compliance' in content:
        return 4
    elif 'black' in content and 'flake8' in content:
        return 3
    elif 'black' in content:
        return 2
    elif 'check-ast' in content:
        return 1
    else:
        return 0

def get_git_activity():
    """Git活動を取得"""
    try:
        # 過去7日のコミット数
        result = subprocess.run(
            ['git', 'log', '--since=7 days ago', '--oneline'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            commits_7d = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            return commits_7d
        else:
            return 0

    except Exception:
        return 0

def check_precommit_config():
    """Pre-commit設定をチェック"""
    config_file = PROJECT_ROOT / '.pre-commit-config.yaml'
    if not config_file.exists():
        return False, "設定ファイルが存在しません"

    try:
        content = config_file.read_text()
        hooks = content.count('- id:')
        return True, f"{hooks}個のフックが設定済み"
    except Exception as e:
        return False, f"設定読み込みエラー: {e}"

def check_daemon_status():
    """デーモンの状態をチェック"""
    try:
        # systemdサービスの状態確認
        result = subprocess.run(
            ['systemctl', 'is-active', 'quality-evolution'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, "サービスが停止中"

    except Exception:
        return False, "状態確認不可"

def check_recent_logs():
    """最新のログをチェック"""
    log_file = PROJECT_ROOT / 'logs/quality_daemon.log'
    if not log_file.exists():
        return "ログファイルが存在しません"

    try:
        lines = log_file.read_text().strip().split('\n')
        if lines:
            return lines[-1]  # 最新のログ行
        else:
            return "ログが空です"
    except Exception as e:
        return f"ログ読み込みエラー: {e}"

def main():
    """メイン関数"""
    print("🏛️ エルダーズギルド 品質進化システム状態")
    print("=" * 50)

    # 現在のフェーズ
    current_phase = get_current_phase()
    print(f"📊 現在のフェーズ: Phase {current_phase}")

    # Git活動
    git_activity = get_git_activity()
    print(f"📈 Git活動: 過去7日で{git_activity}コミット")

    # Pre-commit設定
    precommit_ok, precommit_msg = check_precommit_config()
    status_icon = "✅" if precommit_ok else "❌"
    print(f"⚙️ Pre-commit: {status_icon} {precommit_msg}")

    # デーモン状態
    daemon_ok, daemon_msg = check_daemon_status()
    daemon_icon = "🟢" if daemon_ok else "🔴"
    print(f"🤖 デーモン: {daemon_icon} {daemon_msg}")

    # 最新ログ
    recent_log = check_recent_logs()
    print(f"📋 最新ログ: {recent_log}")

    # 現在時刻
    print(f"⏰ 確認時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 簡単な品質スコア
    quality_score = 0
    if precommit_ok:
        quality_score += 30
    if git_activity > 0:
        quality_score += 20
    if daemon_ok:
        quality_score += 30
    quality_score += current_phase * 5

    print(f"🎯 品質スコア: {quality_score}/100")

    # 次のアクション提案
    print("\n💡 推奨アクション:")
    if not precommit_ok:
        print("   - Pre-commit設定を確認してください")
    if not daemon_ok:
        print("   - デーモンを開始してください: scripts/quality_system_manager.sh start")
    if git_activity == 0:
        print("   - 定期的なコミットを心がけてください")
    if quality_score >= 80:
        print("   - 品質レベルが高い状態です！継続してください")

    return 0

if __name__ == "__main__":
    sys.exit(main())
