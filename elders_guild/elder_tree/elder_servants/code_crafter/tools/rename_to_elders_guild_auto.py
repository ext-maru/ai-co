#!/usr/bin/env python3
"""
Elders Guild → Elders Guild 名称統一スクリプト（自動実行版）
"""

import re
from pathlib import Path


def replace_in_file(file_path: Path) -> bool:
    """ファイル内の文字列を置換"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 重要: ディレクトリ名 /home/aicompany/ai_co は変更しない
        # URLやパスも保持
        original_content = content

        # 大文字小文字を考慮して置換（ただしパスは除外）
        patterns = [
            # コメント、ドキュメント、テキスト内の置換
            (r"(?<!/)Elders Guild(?![/_])", "Elders Guild"),
            (r"(?<!/)AI company(?![/_])", "Elders Guild"),
            (r"(?<!/)ai company(?![/_])", "elders guild"),
            # 変数名やコード内の置換（パスを除外）
            (r"(?<!/)AI_COMPANY(?![/_])", "ELDERS_GUILD"),
            (r"(?<!/)ai_company(?![/_])", "elders_guild"),
            (r"(?<!/)AICompany(?![/_])", "EldersGuild"),
            # ただし、ディレクトリ名は保持
        ]

        modified = False
        for old, new in patterns:
            if re.search(old, content):
                content = re.sub(old, new, content)
                modified = True

        if modified and content != original_content:
            # バックアップ作成
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(original_content)

            # 更新
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")

    return False


def main():
    """メイン処理"""
    root_dir = Path(__file__).parent.parent

    print("🏛️ Elders Guild 名称統一スクリプト（自動実行版）")
    print("=" * 60)

    # 対象拡張子（重要なものに限定）
    extensions = [".py", ".md"]

    # 除外ディレクトリ

    # 重要ファイルのみ処理
    important_patterns = [
        "README.md",
        "CLAUDE.md",
        "docs/*.md",
        "scripts/setup_pgvector_database.py",
        "scripts/migrate_a2a_to_pgvector.py",
        "scripts/pgvector_a2a_integration.py",
        "commands/*.py",
        "workers/*.py",
        "libs/*.py",
    ]

    files_to_process = []

    # ファイル収集
    for pattern in important_patterns:
        if "*" in pattern:
            base_path = root_dir / pattern.replace("*", "")
            base_dir = base_path.parent
            if base_dir.exists():
                # 繰り返し処理
                for ext in extensions:
                    # Deep nesting detected (depth: 5) - consider refactoring
                    for file_path in base_dir.glob(f"*{ext}"):
                        if not (file_path.is_file()):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if file_path.is_file():
                            files_to_process.append(file_path)
        else:
            file_path = root_dir / pattern
            if file_path.exists() and file_path.is_file():
                files_to_process.append(file_path)

    # 重複除去
    files_to_process = list(set(files_to_process))

    print(f"\n📊 処理対象: {len(files_to_process)} ファイル")

    # 置換実行
    print("\n🔄 置換を実行中...")
    success_count = 0

    for file_path in files_to_process:
        if replace_in_file(file_path):
            success_count += 1
            print(f"  ✅ {file_path.relative_to(root_dir)}")

    print(f"\n✨ 完了! {success_count} ファイルを更新しました")

    # バックアップファイルの確認
    backup_files = list(root_dir.rglob("*.bak"))
    if backup_files:
        print(f"\n💾 バックアップファイルが {len(backup_files)} 個作成されました")
        print("   必要に応じて後で削除してください: find . -name '*.bak' -delete")

    # 確認
    print("\n📋 主要ファイルの確認:")
    check_files = ["README.md", "CLAUDE.md", "docs/pgvector_integration_guide.md"]
    for file_name in check_files:
        file_path = root_dir / file_name
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "Elders Guild" in content and "Elders Guild" not in content:
                    print(f"  ✅ {file_name}")
                elif "Elders Guild" in content:
                    print(f"  ⚠️  {file_name} (まだ Elders Guild が含まれています)")
                else:
                    print(f"  📄 {file_name} (対象文字列なし)")


if __name__ == "__main__":
    main()
