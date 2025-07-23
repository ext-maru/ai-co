#!/usr/bin/env python3
"""
クリーンアップ
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult


class AICleanCommand(BaseCommand):
    """クリーンアップ"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(name="ai-clean", description="クリーンアップ", version="1.0.0")

    def execute(self, args) -> CommandResult:
        """実行"""
        dry_run = "--dry-run" in args
        force = "--force" in args
        
        try:
            cleaned_items = []
            total_size = 0
            
            project_root = Path(__file__).parent.parent
            
            # クリーンアップ対象の定義
            cleanup_targets = [
                ("tmp", "tmp/*"),
                ("logs_old", "logs/*.log.old"),
                ("cache", "**/__pycache__"),
                ("pyc_files", "**/*.pyc"),
                ("test_outputs", "test_outputs/*"),
                ("generated_reports_old", "generated_reports/*.old"),
                ("backup_files", "**/*.bak"),
                ("temp_files", "**/*~")
            ]
            
            for category, pattern in cleanup_targets:
                # Process each item in collection
                import glob
                
                # パターンに応じてファイルを検索
                if pattern.startswith("**"):
                    # recursive glob
                    files = list(project_root.rglob(pattern.replace("**/", "")))
                else:
                    # simple glob
                    files = list(project_root.glob(pattern))
                
                for file_path in files:
                    # Process each item in collection
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        
                        if dry_run:
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if not dry_run:
                            file_path.unlink()
                        
                        cleaned_items.append({
                            "category": category,
                            "file": str(file_path.relative_to(project_root)),
                            "size": size
                        })
                        total_size += size
                    
                    elif file_path.is_dir() and not any(file_path.iterdir()):
                        # Complex condition - consider breaking down
                        # 空のディレクトリも削除
                        if dry_run:
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if not dry_run:
                            file_path.rmdir()
                        
                        cleaned_items.append({
                            "category": category,
                            "file": str(file_path.relative_to(project_root)) + "/",
                            "size": 0
                        })
            
            # 結果サマリー
            if not cleaned_items:
                return CommandResult(
                    success=True,
                    message="🧹 クリーンアップ対象が見つかりませんでした"
                )
            
            # サイズを人間に読みやすい形式に変換
            def human_readable_size(bytes_size):
                """human_readable_sizeメソッド"""
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if bytes_size < 1024.0:
                        return f"{bytes_size:.1f} {unit}"
                    bytes_size /= 1024.0
                return f"{bytes_size:.1f} TB"
            
            # カテゴリ別統計
            categories = {}
            for item in cleaned_items:
                cat = item["category"]
                if cat not in categories:
                    categories[cat] = {"count": 0, "size": 0}
                categories[cat]["count"] += 1
                categories[cat]["size"] += item["size"]
            
            action = "🔍 発見" if dry_run else "🧹 クリーンアップ"
            message = f"{action}完了:\n\n"
            
            for category, stats in categories.items():
                # Process each item in collection
                message += f"  📁 {category}: {stats['count']}個 ({human_readable_size(stats['size'])})\n"
            
            message += f"\n📊 合計: {len(cleaned_items)}個のアイテム ({human_readable_size(total_size)})"
            
            if dry_run:
                message += "\n\n💡 実際にクリーンアップするには --dry-run を外して実行してください"
            
            return CommandResult(success=True, message=message)
            
        except Exception as e:
            # Handle specific exception case
            return CommandResult(
                success=False, 
                message=f"❌ クリーンアップエラー: {e}"
            )


def main():
    # Core functionality implementation
    command = AICleanCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
