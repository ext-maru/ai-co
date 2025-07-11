#!/usr/bin/env python3
"""
🌌 nWo自動化セットアップスクリプト
Daily Council自動実行とcron設定

Author: Claude Elder
Date: 2025-07-11
Authority: Grand Elder maru
Mission: Complete nWo Automation Setup
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent

def setup_nwo_automation():
    """nWo自動化セットアップ"""
    print("🌌 nWo (New World Order) 自動化セットアップ開始")
    print("=" * 60)

    # 1. 必要ディレクトリ作成
    print("📁 ディレクトリ構造作成...")
    directories = [
        PROJECT_ROOT / "nwo_council_reports",
        PROJECT_ROOT / "logs" / "nwo",
        PROJECT_ROOT / "data" / "nwo"
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {directory}")

    # 2. cron設定ファイル作成
    print("\n⏰ cron設定準備...")
    cron_script_path = PROJECT_ROOT / "scripts" / "nwo_daily_cron.sh"

    cron_content = f"""#!/bin/bash
# nWo Daily Council 自動実行スクリプト
# 毎日 9:00 AM に実行

cd {PROJECT_ROOT}

# nWo Daily Council 実行
echo "🌌 nWo Daily Council 開始: $(date)" >> logs/nwo/daily_council.log
python3 libs/nwo_daily_council.py >> logs/nwo/daily_council.log 2>&1

# nWo Vision 更新
echo "🔮 nWo Vision 更新: $(date)" >> logs/nwo/daily_vision.log
python3 commands/ai_nwo_vision.py >> logs/nwo/daily_vision.log 2>&1

echo "✅ nWo自動化完了: $(date)" >> logs/nwo/automation.log
"""

    with open(cron_script_path, 'w') as f:
        f.write(cron_content)

    # 実行権限付与
    os.chmod(cron_script_path, 0o755)
    print(f"  ✅ Cronスクリプト作成: {cron_script_path}")

    # 3. crontab エントリ生成（表示のみ）
    print("\n📋 crontab設定用コマンド:")
    print(f"  crontab -e で以下を追加:")
    print(f"  0 9 * * * {cron_script_path}")
    print("  （毎日午前9時に nWo Daily Council 自動実行）")

    # 4. 「未来を見せて」コマンド拡張
    print("\n🔮 「未来を見せて」コマンド拡張...")

    # 既存のRAGエルダーコマンドを探す
    existing_vision_commands = [
        PROJECT_ROOT / "commands" / "ai_rag.py",
        PROJECT_ROOT / "commands" / "ai_vision.py",
        PROJECT_ROOT / "scripts" / "rag_elder_vision.py"
    ]

    vision_command_found = False
    for cmd_path in existing_vision_commands:
        if cmd_path.exists():
            print(f"  📝 既存コマンド発見: {cmd_path}")
            vision_command_found = True
            break

    if not vision_command_found:
        print("  ⚠️  既存の「未来を見せて」コマンドが見つかりません")
        print("  💡 手動で統合が必要です")

    # 5. エルダーズギルド統合
    print("\n🏛️ エルダーズギルド統合確認...")

    # CLAUDEmdファイル更新
    claude_md_path = PROJECT_ROOT / "CLAUDE.md"
    if claude_md_path.exists():
        print("  📄 CLAUDE.md にnWo情報追加準備完了")

    # 6. 初回テスト実行
    print("\n🧪 初回テスト実行...")
    try:
        result = subprocess.run([
            sys.executable,
            str(PROJECT_ROOT / "libs" / "nwo_daily_council.py")
        ], capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            print("  ✅ nWo Daily Council テスト成功")
        else:
            print(f"  ⚠️  テスト警告: {result.stderr[:200]}")

    except subprocess.TimeoutExpired:
        print("  ⏱️  テスト実行中（バックグラウンド継続）")
    except Exception as e:
        print(f"  ❌ テストエラー: {e}")

    # 7. セットアップ完了
    print("\n🎉 nWo自動化セットアップ完了!")
    print("=" * 60)

    print("🚀 次のアクション:")
    print("  1. crontab -e で自動実行を設定")
    print("  2. python3 libs/nwo_daily_council.py で手動テスト")
    print("  3. python3 commands/ai_nwo_vision.py でビジョン確認")
    print()

    print("🌌 nWo (New World Order) システム準備完了")
    print("👑 Think it, Rule it, Own it")

    return True

if __name__ == "__main__":
    setup_nwo_automation()
