#!/usr/bin/env python3
"""
ai-prophecy-status - 予言書状態確認コマンド
エルダーズギルド 予言書システムの軽量な状態確認インターフェース
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from commands.base_command import BaseCommand


class ProphecyStatusCommand(BaseCommand):
    """予言書状態確認コマンド"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(
            name="ai-prophecy-status",
            description="🏛️ エルダーズギルド 予言書状態確認"
        )

    def setup_parser(self):
        """パーサーのセットアップ"""
        parser = argparse.ArgumentParser(
            description="🏛️ エルダーズギルド 予言書状態確認",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
🏛️ 予言書システムの軽量な状態確認:

現在の予言書の状態を素早く確認できます。

使用例:
  ai-prophecy-status                          # 基本状態確認
  ai-prophecy-status --files                  # ファイル詳細
  ai-prophecy-status --systems                # システム状態
  ai-prophecy-status --json                   # JSON出力
            """,
        )

        parser.add_argument("--files", action="store_true", help="ファイル詳細表示")
        parser.add_argument("--systems", action="store_true", help="システム状態表示")
        parser.add_argument("--json", action="store_true", help="JSON形式で出力")
        parser.add_argument("--compact", action="store_true", help="コンパクト表示")

        return parser

    def run(self, args):
        """コマンド実行"""
        parser = self.setup_parser()
        parsed_args = parser.parse_args(args)

        # 状態データ収集
        status_data = self.collect_status_data()

        if parsed_args.json:
            # JSON出力
            print(json.dumps(status_data, indent=2, ensure_ascii=False, default=str))
        else:
            # 通常表示
            self.show_status(status_data, parsed_args)

        return 0

    def collect_status_data(self) -> Dict:
        """状態データ収集"""
        status_data = {
            'timestamp': datetime.now().isoformat(),
            'prophecy_files': self.scan_prophecy_files(),
            'system_state': self.check_system_state(),
            'engine_state': self.check_engine_state(),
            'management_state': self.check_management_state()
        }

        return status_data

    def scan_prophecy_files(self) -> List[Dict]:
        """予言書ファイルのスキャン"""
        prophecy_files = []

        # propheciesディレクトリ
        prophecies_dir = PROJECT_ROOT / "prophecies"
        if prophecies_dir.exists():
            for file_path in prophecies_dir.glob("*.yaml"):
                # Process each item in collection
                prophecy_files.append(self.get_file_info(file_path))
            for file_path in prophecies_dir.glob("*.yml"):
                # Process each item in collection
                prophecy_files.append(self.get_file_info(file_path))

        # その他の場所
        for pattern in ["*prophecy*.yaml", "*prophecy*.yml"]:
            for file_path in PROJECT_ROOT.glob(pattern):
                prophecy_files.append(self.get_file_info(file_path))

        return prophecy_files

    def get_file_info(self, file_path: Path) -> Dict:
        """ファイル情報取得"""
        try:
            stat = file_path.stat()
            return {
                'name': file_path.name,
                'path': str(file_path),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'readable': file_path.is_file() and file_path.exists()
            }
        except Exception as e:
            # Handle specific exception case
            return {
                'name': file_path.name,
                'path': str(file_path),
                'error': str(e),
                'readable': False
            }

    def check_system_state(self) -> Dict:
        """システム状態確認"""
        system_state = {
            'quality_daemon': self.check_quality_daemon(),
            'directories': self.check_directories(),
            'config_files': self.check_config_files()
        }

        return system_state

    def check_quality_daemon(self) -> Dict:
        """品質デーモン状態確認"""
        try:
            import subprocess
            result = subprocess.run(
                ['systemctl', 'is-active', 'quality-evolution'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                status = "active"
            else:
                status = "inactive"
        except Exception:
            # Handle specific exception case
            status = "unknown"

        return {
            'status': status,
            'service_name': 'quality-evolution'
        }

    def check_directories(self) -> Dict:
        """ディレクトリ状態確認"""
        directories = {
            'prophecies': (PROJECT_ROOT / "prophecies").exists(),
            'logs': (PROJECT_ROOT / "logs").exists(),
            'scripts': (PROJECT_ROOT / "scripts").exists(),
            'libs': (PROJECT_ROOT / "libs").exists(),
            'commands': (PROJECT_ROOT / "commands").exists()
        }

        return directories

    def check_config_files(self) -> Dict:
        """設定ファイル確認"""
        config_files = {
            'precommit_config': (PROJECT_ROOT / ".pre-commit-config.yaml").exists(),
            'quality_config': (PROJECT_ROOT / "configs/auto_quality_config.yaml").exists(),
            'claude_md': (PROJECT_ROOT / "CLAUDE.md").exists(),
            'prophecy_system': (PROJECT_ROOT / "PROPHECY_SYSTEM.md").exists()
        }

        return config_files

    def check_engine_state(self) -> Dict:
        """エンジン状態確認"""
        engine_state = {
            'prophecy_engine': False,
            'state_files': {},
            'loaded_prophecies': 0
        }

        try:
            # 状態ファイルの存在確認
            prophecy_dir = PROJECT_ROOT / "prophecies"
            if prophecy_dir.exists():
                state_file = prophecy_dir / "prophecy_state.json"
                history_file = prophecy_dir / "prophecy_history.json"

                engine_state['state_files'] = {
                    'prophecy_state': state_file.exists(),
                    'prophecy_history': history_file.exists()
                }

                # 状態ファイルから情報取得
                if state_file.exists():
                    try:
                        # Deep nesting detected (depth: 5) - consider refactoring
                        with open(state_file, 'r', encoding='utf-8') as f:
                            state_data = json.load(f)
                            engine_state['loaded_prophecies'] = len(state_data)
                    except:
                        pass

            engine_state['prophecy_engine'] = True

        except Exception:
            # Handle specific exception case
            engine_state['prophecy_engine'] = False

        return engine_state

    def check_management_state(self) -> Dict:
        """管理システム状態確認"""
        management_state = {
            'management_system': False,
            'templates': 0,
            'managed_prophecies': 0
        }

        try:
            # 管理システムの初期化テスト
            from libs.prophecy_management_system import ProphecyManagementSystem
            pms = ProphecyManagementSystem()

            management_state['management_system'] = True
            management_state['templates'] = len(pms.templates)
            management_state['managed_prophecies'] = len(pms.managed_prophecies)

        except Exception:
            # Handle specific exception case
            management_state['management_system'] = False

        return management_state

    def show_status(self, status_data: Dict, args):
        """状態表示"""
        if args.compact:
            self.show_compact_status(status_data)
        else:
            self.show_detailed_status(status_data, args)

    def show_compact_status(self, status_data: Dict):
        """コンパクト状態表示"""
        timestamp = status_data['timestamp'][:19]  # 秒まで

        print(f"🏛️ 予言書システム状態 ({timestamp})")

        # ファイル
        file_count = len(status_data['prophecy_files'])
        print(f"📄 {file_count}個の予言書ファイル")

        # システム
        daemon_status = status_data['system_state']['quality_daemon']['status']
        daemon_icon = "✅" if daemon_status == "active" else "❌"
        print(f"🤖 品質デーモン: {daemon_icon}")

        # エンジン
        engine_active = status_data['engine_state']['prophecy_engine']
        engine_icon = "✅" if engine_active else "❌"
        loaded = status_data['engine_state']['loaded_prophecies']
        print(f"🔮 予言書エンジン: {engine_icon} ({loaded}個読み込み)")

        # 管理システム
        mgmt_active = status_data['management_state']['management_system']
        mgmt_icon = "✅" if mgmt_active else "❌"
        managed = status_data['management_state']['managed_prophecies']
        print(f"🏛️ 管理システム: {mgmt_icon} ({managed}個管理)")

    def show_detailed_status(self, status_data: Dict, args):
        """詳細状態表示"""
        self.info("🏛️ エルダーズギルド 予言書システム状態")
        self.info("=" * 60)
        self.info(f"⏰ 確認時刻: {status_data['timestamp'][:19]}")
        self.info("")

        # 予言書ファイル
        prophecy_files = status_data['prophecy_files']
        self.info(f"📄 予言書ファイル: {len(prophecy_files)}件")

        if args.files and prophecy_files:
            # Complex condition - consider breaking down
            self.info("   詳細:")
            for file_info in prophecy_files:
                # Process each item in collection
                if file_info['readable']:
                    size_kb = file_info['size'] / 1024
                    modified = file_info['modified'][:19]
                    self.info(f"   📋 {file_info['name']} ({size_kb:0.1f}KB, {modified})")
                else:
                    self.info(f"   ❌ {file_info['name']} (読み取り不可)")

        self.info("")

        # システム状態
        if args.systems:
            self.info("🔧 システム状態:")

            # 品質デーモン
            daemon_info = status_data['system_state']['quality_daemon']
            daemon_status = daemon_info['status']
            daemon_icon = "✅" if daemon_status == "active" else "❌"
            self.info(f"   🤖 品質デーモン: {daemon_icon} {daemon_status}")

            # ディレクトリ
            directories = status_data['system_state']['directories']
            self.info("   📁 ディレクトリ:")
            for dir_name, exists in directories.items():
                # Process each item in collection
                icon = "✅" if exists else "❌"
                self.info(f"      {icon} {dir_name}")

            # 設定ファイル
            config_files = status_data['system_state']['config_files']
            self.info("   ⚙️ 設定ファイル:")
            for file_name, exists in config_files.items():
                # Process each item in collection
                icon = "✅" if exists else "❌"
                self.info(f"      {icon} {file_name}")

            self.info("")

        # エンジン状態
        engine_state = status_data['engine_state']
        engine_icon = "✅" if engine_state['prophecy_engine'] else "❌"
        loaded = engine_state['loaded_prophecies']
        self.info(f"🔮 予言書エンジン: {engine_icon} ({loaded}個読み込み済み)")

        # 管理システム状態
        mgmt_state = status_data['management_state']
        mgmt_icon = "✅" if mgmt_state['management_system'] else "❌"
        managed = mgmt_state['managed_prophecies']
        templates = mgmt_state['templates']
        self.info(f"🏛️ 管理システム: {mgmt_icon} ({managed}個管理, {templates}個テンプレート)")

        self.info("")

        # 推奨事項
        self.show_recommendations(status_data)

    def show_recommendations(self, status_data: Dict):
        """推奨事項表示"""
        recommendations = []

        # 予言書ファイルがない場合
        if len(status_data['prophecy_files']) == 0:
            recommendations.append("📄 予言書ファイルが見つかりません - 予言書を作成してください")

        # デーモンが停止している場合
        if status_data['system_state']['quality_daemon']['status'] != "active":
            recommendations.append("🤖 品質デーモンが停止中です - 起動を検討してください")

        # エンジンが動作していない場合
        if not status_data['engine_state']['prophecy_engine']:
            recommendations.append("🔮 予言書エンジンが利用できません - システムを確認してください")

        # 読み込み済み予言書がない場合
        if status_data['engine_state']['loaded_prophecies'] == 0:
            recommendations.append("📋 予言書が読み込まれていません - 予言書を読み込んでください")

        if recommendations:
            self.info("💡 推奨事項:")
            for rec in recommendations:
                # Process each item in collection
                self.info(f"   • {rec}")
        else:
            self.info("✅ システム状態は良好です")

        self.info("")
        self.info("🔧 利用可能なコマンド:")
        self.info("   ai-prophecy load prophecies/quality_evolution.yaml  # 予言書読み込み")
        self.info("   ai-prophecy-dashboard                               # 詳細ダッシュボード")
        self.info("   ai-prophecy-management create --template quality   # 新規予言書作成")


def main():
    """メインエントリーポイント"""
    command = ProphecyStatusCommand()
    return command.run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
