#!/usr/bin/env python3
"""
AI Command Migration Script
既存のスクリプトやドキュメントを新コマンド体系に移行
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class AICommandMigrator:
    """AIコマンド移行ツール"""

    def __init__(self):
        self.timestamp = datetime.now()
        self.migration_map = self.load_migration_map()
        self.stats = {
            "files_scanned": 0,
            "files_modified": 0,
            "commands_replaced": 0,
            "errors": 0,
        }

    def load_migration_map(self) -> Dict[str, str]:
        """移行マッピングをロード"""
        # Basic migration map
        return {
            # Core commands
            "ai-start": "ai start",
            "ai-stop": "ai stop",
            "ai-status": "ai status",
            "ai-env": "ai env",
            # Elder commands
            "ai-elder": "ai elder status",
            "ai-elder-council": "ai elder council",
            "ai-elder-settings": "ai elder settings",
            "ai-elder-tree": "ai elder tree",
            "ai-elder-compliance": "ai elder compliance",
            "ai-elder-proactive-monitor": "ai monitor proactive",
            "ai-servant": "ai elder servant",
            # Worker commands
            "ai-worker-comm": "ai worker status",
            "ai-worker-recovery": "ai worker recovery",
            "ai-dlq": "ai worker dlq",
            # Dev commands
            "ai-codegen": "ai dev codegen",
            "ai-document": "ai dev document",
            "ai-git": "ai dev git",
            "ai-tdd": "ai dev tdd",
            # Test commands
            "ai-test-coverage": "ai test coverage",
            "ai-test-quality": "ai test quality",
            "ai-test-runner": "ai test runner",
            "ai-elf-test-magic": "ai test magic",
            # Ops commands
            "ai-dashboard": "ai ops dashboard",
            "ai-api-status": "ai ops api-status",
            "ai-api-health": "ai ops api-health",
            "ai-api-reset": "ai ops api-reset",
            # Monitor commands
            "ai-logs": "ai monitor logs",
            # Integration commands
            "ai-slack": "ai integrate slack",
            "ai-mcp": "ai integrate mcp",
            "ai-send": "ai integrate send",
            # Special cases
            "ai-elf-forest": "ai elder elf-forest",
            "ai-knights-auto": "ai elder knights-auto",
            "ai-knights-dispatch": "ai elder knights-dispatch",
            "ai-rag-wizards": "ai elder rag-wizards",
        }

    def should_skip_file(self, file_path: Path) -> bool:
        """スキップすべきファイルかチェック"""
        skip_patterns = [
            ".git/",
            "__pycache__/",
            ".pyc",
            ".log",
            ".db",
            ".sqlite",
            "venv/",
            "node_modules/",
            ".egg-info/",
        ]

        file_str = str(file_path)
        for pattern in skip_patterns:
            if pattern in file_str:
                return True

        # Binary files
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                f.read(1)
            return False
        except:
            return True

    def migrate_file(self, file_path: Path) -> Tuple[bool, int]:
        """ファイル内のコマンドを移行"""
        if self.should_skip_file(file_path):
            return False, 0

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content
            replacements = 0

            # Replace commands
            for old_cmd, new_cmd in self.migration_map.items():
                # Match various patterns
                patterns = [
                    # In quotes
                    (f'"{old_cmd}"', f'"{new_cmd}"'),
                    (f"'{old_cmd}'", f"'{new_cmd}'"),
                    # In backticks (markdown)
                    (f"`{old_cmd}`", f"`{new_cmd}`"),
                    # Command line usage
                    (f" {old_cmd} ", f" {new_cmd} "),
                    (f"^{old_cmd} ", f"{new_cmd} "),
                    (f" {old_cmd}$", f" {new_cmd}"),
                    # With arguments
                    (f"{old_cmd} --", f"{new_cmd} --"),
                    (f"{old_cmd} -", f"{new_cmd} -"),
                ]

                for pattern, replacement in patterns:
                    new_content = re.sub(
                        pattern, replacement, content, flags=re.MULTILINE
                    )
                    if new_content != content:
                        replacements += content.count(pattern)
                        content = new_content

            # Save if modified
            if content != original_content:
                # Create backup
                backup_path = file_path.with_suffix(file_path.suffix + ".pre-migration")
                if not backup_path.exists():
                    with open(backup_path, "w", encoding="utf-8") as f:
                        f.write(original_content)

                # Write updated content
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                return True, replacements

            return False, 0

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            self.stats["errors"] += 1
            return False, 0

    def scan_directory(self, directory: Path, extensions: List[str] = None):
        """ディレクトリをスキャンして移行"""
        if extensions is None:
            extensions = [".py", ".sh", ".md", ".txt", ".yml", ".yaml", ".json"]

        print(f"📁 Scanning: {directory}")

        for file_path in directory.rglob("*"):
            if file_path.is_file():
                self.stats["files_scanned"] += 1

                # Check extension
                if extensions and file_path.suffix not in extensions:
                    continue

                # Skip this migration script itself
                if file_path.name == "migrate_ai_commands.py":
                    continue

                modified, count = self.migrate_file(file_path)
                if modified:
                    self.stats["files_modified"] += 1
                    self.stats["commands_replaced"] += count
                    print(f"  ✅ Updated: {file_path} ({count} replacements)")

    def generate_report(self) -> Dict:
        """移行レポートを生成"""
        report = {
            "timestamp": self.timestamp.isoformat(),
            "statistics": self.stats,
            "migration_map": self.migration_map,
            "summary": {
                "success_rate": (
                    self.stats["files_modified"] / max(self.stats["files_scanned"], 1)
                )
                * 100,
                "total_replacements": self.stats["commands_replaced"],
            },
        }

        # Save report
        reports_dir = Path("/home/aicompany/ai_co/reports")
        report_path = (
            reports_dir
            / f"ai_command_migration_report_{self.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report

    def create_markdown_report(self, report: Dict):
        """Markdown形式のレポート作成"""
        md_content = f"""# AI Command Migration Report

**実行日時**: {self.timestamp.strftime('%Y年%m月%d日 %H:%M:%S')}

## 📊 移行統計

- **スキャンしたファイル数**: {report['statistics']['files_scanned']}
- **更新したファイル数**: {report['statistics']['files_modified']}
- **置換したコマンド数**: {report['statistics']['commands_replaced']}
- **エラー数**: {report['statistics']['errors']}
- **成功率**: {report['summary']['success_rate']:0.1f}%

## 🔄 移行マッピング

| 旧コマンド | 新コマンド |
|-----------|-----------|
"""
        for old, new in sorted(report["migration_map"].items()):
            md_content += f"| `{old}` | `{new}` |\n"

        md_content += """
## 📝 注意事項

1.0 各ファイルのバックアップが `.pre-migration` 拡張子で作成されています
2.0 問題が発生した場合は、バックアップから復元してください
3.0 スクリプト内の文字列やコメントも更新されています

## 🔧 次のステップ

1.0 更新されたファイルの動作確認
2.0 テストスイートの実行
3.0 問題があればバックアップから復元

---
*AI Command Migration Tool*
"""

        md_path = (
            Path("/home/aicompany/ai_co/reports")
            / f"AI_COMMAND_MIGRATION_REPORT_{self.timestamp.strftime('%Y%m%d')}.md"
        )
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"\n📄 Markdownレポート: {md_path}")


def main():
    """メイン実行"""
    print("🔄 AI Command Migration Tool")
    print("=" * 60)

    migrator = AICommandMigrator()

    # Parse arguments
    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1])
    else:
        # Default to Elders Guild directory
        target_path = Path("/home/aicompany/ai_co")

    if not target_path.exists():
        print(f"❌ Path not found: {target_path}")
        sys.exit(1)

    # Confirm before proceeding
    print(f"\n⚠️  This will migrate commands in: {target_path}")
    print("Backups will be created for all modified files.")
    response = input("\nProceed? (y/N): ")

    if response.lower() != "y":
        print("❌ Migration cancelled.")
        sys.exit(0)

    print("\n🚀 Starting migration...")

    # Scan and migrate
    if target_path.is_file():
        modified, count = migrator.migrate_file(target_path)
        if modified:
            print(f"✅ Updated {target_path} ({count} replacements)")
    else:
        migrator.scan_directory(target_path)

    # Generate report
    report = migrator.generate_report()
    migrator.create_markdown_report(report)

    # Print summary
    print("\n✅ Migration completed!")
    print(f"\n📊 Summary:")
    print(f"  - Files scanned: {migrator.stats['files_scanned']}")
    print(f"  - Files modified: {migrator.stats['files_modified']}")
    print(f"  - Commands replaced: {migrator.stats['commands_replaced']}")
    print(f"  - Errors: {migrator.stats['errors']}")

    if migrator.stats["errors"] > 0:
        print("\n⚠️  Some errors occurred. Check the report for details.")


if __name__ == "__main__":
    main()
