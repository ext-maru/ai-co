#!/usr/bin/env python3
"""
Elders Guild コマンドクリーンアップスクリプト
古いコマンド、バックアップファイル、未使用コマンドを整理
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class CommandCleaner:
    def __init__(self, dry_run=True):
    """CommandCleanerクラス"""
        self.project_root = PROJECT_ROOT
        self.dry_run = dry_run
        self.backup_dir = (
            self.project_root
            / "backups"
            / f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        self.cleanup_summary = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run,
            "backed_up": [],
            "removed": [],
            "kept": [],
            "errors": [],
        }

        # 確実に削除すべきコマンド（非推奨・未実装）
        self.deprecated_commands = [
            # 未実装または古いコマンド候補
            # 監査結果を基に追加
        ]

        # 保持すべきコア機能
        self.core_commands = [
            "ai",
            "ai-start",
            "ai-stop",
            "ai-status",
            "ai-send",
            "ai-logs",
            "ai-tasks",
            "ai-workers",
            "ai-config",
            "ai-help",
            "ai-version",
            "ai-rag-search",
            "ai-git",
            "ai-monitor",
            "ai-venv",
        ]

    def create_backup(self, file_path):
        """ファイルをバックアップ"""
        if not self.dry_run:
            if not self.backup_dir.exists():
                self.backup_dir.mkdir(parents=True)

            relative_path = file_path.relative_to(self.project_root)
            backup_path = self.backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                shutil.copy2(file_path, backup_path)
                self.cleanup_summary["backed_up"].append(str(relative_path))
                return True
            except Exception as e:
                self.cleanup_summary["errors"].append(
                    f"Backup failed for {file_path}: {e}"
                )
                return False
        return True

    def clean_backup_files(self):
        """*.bakファイルをクリーンアップ"""
        print("\n🧹 バックアップファイル(.bak)のクリーンアップ...")

        bak_files = []
        for dir_path in [
            self.project_root / "scripts",
            self.project_root / "commands",
            self.project_root / "libs",
            self.project_root / "workers",
        ]:
            if dir_path.exists():
                bak_files.extend(dir_path.glob("*.bak"))

        for bak_file in bak_files:
            print(f"  {'[DRY-RUN]' if self.dry_run else ''} 削除: {bak_file.name}")
            if not self.dry_run:
                self.create_backup(bak_file)
                try:
                    bak_file.unlink()
                    self.cleanup_summary["removed"].append(str(bak_file))
                except Exception as e:
                    self.cleanup_summary["errors"].append(
                        f"Failed to remove {bak_file}: {e}"
                    )

        print(f"  → {len(bak_files)}個のバックアップファイルを処理")

    def clean_pycache(self):
        """__pycache__ディレクトリをクリーンアップ"""
        print("\n🧹 __pycache__ディレクトリのクリーンアップ...")

        pycache_dirs = list(self.project_root.rglob("__pycache__"))

        for pycache_dir in pycache_dirs:
            print(f"  {'[DRY-RUN]' if self.dry_run else ''} 削除: {pycache_dir}")
            if not self.dry_run:
                try:
                    shutil.rmtree(pycache_dir)
                    self.cleanup_summary["removed"].append(str(pycache_dir))
                except Exception as e:
                    self.cleanup_summary["errors"].append(
                        f"Failed to remove {pycache_dir}: {e}"
                    )

        print(f"  → {len(pycache_dirs)}個のキャッシュディレクトリを処理")

    def consolidate_dialog_commands(self):
        """対話型コマンドの整理"""
        print("\n🔄 対話型コマンド(ai-dialog, ai-reply)の確認...")

        # 現在の実装状況を確認
        dialog_implementations = {
            "ai-dialog": {
                "bin": self.project_root / "bin" / "ai-dialog",
                "script": self.project_root / "scripts" / "ai-dialog",
                "module": self.project_root / "commands" / "ai_dialog.py",
            },
            "ai-reply": {
                "bin": self.project_root / "bin" / "ai-reply",
                "script": self.project_root / "scripts" / "ai-reply",
                "module": self.project_root / "commands" / "ai_reply.py",
            },
        }

        # 繰り返し処理
        for cmd, paths in dialog_implementations.items():
            print(f"\n  {cmd}:")
            has_implementation = False

            for impl_type, path in paths.items():
                if path.exists():
                    print(f"    ✅ {impl_type}: {path}")
                    has_implementation = True
                else:
                    print(f"    ❌ {impl_type}: なし")

            # 実装が存在し、DialogTaskWorkerが使われているか確認
            if has_implementation and paths["module"].exists():
                with open(paths["module"], "r", encoding="utf-8") as f:
                    content = f.read()
                    if "DialogTaskWorker" in content or "dialog_task_queue" in content:
                        print(f"    → DialogTaskWorkerシステムを使用中")
                        self.cleanup_summary["kept"].append(cmd)
                    else:
                        print(f"    → 古い実装の可能性")
                        self.deprecated_commands.append(cmd)

    def check_duplicate_commands(self):
        """重複機能のコマンドを確認"""
        print("\n🔍 重複機能のチェック...")

        duplicates = {
            "ai-code": "ai-send のショートカット（code タスク専用）",
            "ai-restart": "ai-stop && ai-start の組み合わせ",
            "ai-run": "ai-template run のショートカット",
        }

        for cmd, description in duplicates.items():
            cmd_exists = any(
                [
                    (self.project_root / "bin" / cmd).exists(),
                    (self.project_root / "scripts" / cmd).exists(),
                    (
                        self.project_root / "commands" / f"{cmd.replace('-', '_')}.py"
                    ).exists(),
                ]
            )

            if cmd_exists:
                print(f"  {cmd}: {description}")
                # ショートカットは便利なので保持
                self.cleanup_summary["kept"].append(f"{cmd} (shortcut)")

    def analyze_test_scripts(self):
        """テストスクリプトの整理提案"""
        print("\n🧪 テストスクリプトの分析...")

        test_scripts = []
        scripts_dir = self.project_root / "scripts"

        if scripts_dir.exists():
            test_scripts = [f for f in scripts_dir.glob("test_*.py") if f.is_file()]

        print(f"  検出されたテストスクリプト: {len(test_scripts)}個")

        # testsディレクトリへの移動を提案
        tests_dir = self.project_root / "tests"
        if not tests_dir.exists() and test_scripts:
            print("  💡 提案: tests/ディレクトリを作成してテストスクリプトを整理")

    def generate_cleanup_script(self):
        """実際のクリーンアップを実行するスクリプトを生成"""
        script_content = f"""#!/bin/bash
# Elders Guild コマンドクリーンアップ実行スクリプト
# 生成日時: {datetime.now().isoformat()}

set -e

echo "🧹 Elders Guild コマンドクリーンアップ開始..."

# バックアップディレクトリ作成
BACKUP_DIR="{self.backup_dir}"
mkdir -p "$BACKUP_DIR"

# .bakファイルの削除
echo "📁 バックアップファイルの削除..."
find {self.project_root} -name "*.bak" -type f | while read file; do
    echo "  削除: $file"
    rm -f "$file"
done

# __pycache__の削除
echo "📁 Pythonキャッシュの削除..."
find {self.project_root} -name "__pycache__" -type d | while read dir; do
    echo "  削除: $dir"
    rm -rf "$dir"
done

# 非推奨コマンドの削除（確認付き）
DEPRECATED_COMMANDS=({' '.join(self.deprecated_commands)})

if [ ${{#DEPRECATED_COMMANDS[@]}} -gt 0 ]; then
    echo ""
    echo "⚠️  以下のコマンドを削除しますか？"
    for cmd in "${{DEPRECATED_COMMANDS[@]}}"; do
        echo "  - $cmd"
    done

    read -p "削除を実行しますか？ (y/N): " confirm
    if [[ $confirm == [yY] ]]; then
        for cmd in "${{DEPRECATED_COMMANDS[@]}}"; do
            # bin/のラッパー削除
            [ -f "{self.project_root}/bin/$cmd" ] && rm -f "{self.project_root}/bin/$cmd"
            # scripts/の実装削除
            [ -f "{self.project_root}/scripts/$cmd" ] && rm -f "{self.project_root}/scripts/$cmd"
            # commands/のモジュール削除
            module_name=$(echo "$cmd" | sed 's/-/_/g').py
            [ -f "{self.project_root}/commands/$module_name" ] && rm -f "{self.project_root}/commands/$module_name"
        done
    fi
fi

echo ""
echo "✅ クリーンアップ完了！"
echo "📊 結果:"
echo "  - バックアップ先: $BACKUP_DIR"
echo "  - 削除されたファイル数: $(find "$BACKUP_DIR" -type f | wc -l)"
"""

        return script_content

    def run_cleanup(self):
        """クリーンアップ実行"""
        print(
            f"🔧 Elders Guild コマンドクリーンアップ {'(DRY-RUN)' if self.dry_run else ''}"
        )
        print("=" * 60)

        # 各種クリーンアップ実行
        self.clean_backup_files()
        self.clean_pycache()
        self.consolidate_dialog_commands()
        self.check_duplicate_commands()
        self.analyze_test_scripts()

        # サマリー表示
        print("\n📊 クリーンアップサマリー:")
        print(f"  - バックアップ: {len(self.cleanup_summary['backed_up'])}個")
        print(f"  - 削除対象: {len(self.cleanup_summary['removed'])}個")
        print(f"  - 保持: {len(self.cleanup_summary['kept'])}個")
        print(f"  - エラー: {len(self.cleanup_summary['errors'])}個")

        if self.dry_run:
            print(
                "\n💡 実際にクリーンアップを実行するには --execute オプションを使用してください"
            )

            # 実行スクリプト生成
            script_path = self.project_root / "execute_cleanup.sh"
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(self.generate_cleanup_script())
            os.chmod(script_path, 0o755)
            print(f"📝 実行スクリプト生成: {script_path}")

        # 結果をJSONで保存
        result_path = self.project_root / "cleanup_summary.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(self.cleanup_summary, f, indent=2, ensure_ascii=False)

        print(f"📄 詳細結果: {result_path}")


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description="Elders Guild コマンドクリーンアップ")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="実際にクリーンアップを実行（デフォルトはdry-run）",
    )
    args = parser.parse_args()

    cleaner = CommandCleaner(dry_run=not args.execute)
    cleaner.run_cleanup()


if __name__ == "__main__":
    main()
