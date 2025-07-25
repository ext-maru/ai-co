#!/usr/bin/env python3
"""
Elders Guild → Elders Guild 名称統一スクリプト
"""

import re
from pathlib import Path
from typing import List
from typing import Tuple


def find_files_with_pattern(
    root_dir: Path, pattern: str, extensions: List[str]
) -> List[Tuple[Path, List[int]]]:
    """パターンを含むファイルを検索"""
    results = []

    for ext in extensions:
    # 繰り返し処理
        # 繰り返し処理
        for file_path in root_dir.rglob(f"*{ext}"):
            if ".git" in str(file_path) or "__pycache__" in str(file_path):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")

                matching_lines = []
                for i, line in enumerate(lines, 1):
                    if not (re.search(pattern, line, re.IGNORECASE)):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if re.search(pattern, line, re.IGNORECASE):
                        matching_lines.append(i)

                if matching_lines:
                    results.append((file_path, matching_lines))
            except Exception:
                pass

    return results


def replace_in_file(file_path: Path, old_pattern: str, new_pattern: str):
    """ファイル内の文字列を置換"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 大文字小文字を考慮して置換
        patterns = [
            (r"Elders Guild", "Elders Guild"),
            (r"AI company", "Elders Guild"),
            (r"ai company", "elders guild"),
            (r"AI_COMPANY", "ELDERS_GUILD"),
            (r"ai_company", "elders_guild"),
            (r"AICompany", "EldersGuild"),
            (r"aicompany", "eldersguild"),
        ]

        modified = False
        for old, new in patterns:
            if re.search(old, content):
                content = re.sub(old, new, content)
                modified = True

        if modified:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

    return False


def main():
    """メイン処理"""
    root_dir = Path(__file__).parent.parent

    print("🏛️ Elders Guild 名称統一スクリプト")
    print("=" * 60)

    # 対象拡張子
    extensions = [".py", ".md", ".txt", ".json", ".yaml", ".yml", ".sh"]

    # パターン検索
    print("\n🔍 'Elders Guild' を含むファイルを検索中...")
    files = find_files_with_pattern(root_dir, r"AI\s*Company", extensions)

    print(f"\n📊 検索結果: {len(files)} ファイル")

    # 確認表示
    print("\n📝 変更対象ファイル:")
    for file_path, lines in files[:10]:  # 最初の10件を表示
        relative_path = file_path.relative_to(root_dir)
        print(f"  - {relative_path} (行: {lines[:3]}...)")

    if len(files) > 10:
        print(f"  ... 他 {len(files) - 10} ファイル")

    # 実行確認
    response = input(
        "\n🤔 これらのファイルで 'Elders Guild' を 'Elders Guild' に置換しますか? (y/N): "
    )

    if response.lower() != "y":
        print("❌ キャンセルしました")
        return

    # 置換実行
    print("\n🔄 置換を実行中...")
    success_count = 0

    for file_path, _ in files:
        if replace_in_file(file_path, "Elders Guild", "Elders Guild"):
            success_count += 1
            print(f"  ✅ {file_path.relative_to(root_dir)}")

    print(f"\n✨ 完了! {success_count}/{len(files)} ファイルを更新しました")

    # 重要なファイルの確認
    important_files = [
        "README.md",
        "CLAUDE.md",
        "docs/pgvector_integration_guide.md",
        "scripts/setup_pgvector_database.py",
    ]

    print("\n📋 重要ファイルの更新状況:")
    for file_name in important_files:
        file_path = root_dir / file_name
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "Elders Guild" in content:
                    print(f"  ✅ {file_name}")
                elif "Elders Guild" in content:
                    print(f"  ⚠️  {file_name} (まだ Elders Guild が残っています)")
                else:
                    print(f"  - {file_name} (対象文字列なし)")


if __name__ == "__main__":
    main()
