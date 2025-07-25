#!/usr/bin/env python3
"""
🏛️ True Complete Elder Tree Migration
真の完全移行 - 元ファイル削除・完全移動実行
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import time

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [TRUE Migration] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TrueCompleteElderMigrator:
    """真の完全Elder Tree移行"""
    
    def __init__(self):
        self.base_path = Path("/home/aicompany/ai_co")
        self.elder_tree_path = self.base_path / "elders_guild" / "elder_tree"
        
        # バックアップディレクトリ
        timestamp = int(time.time())
        self.backup_path = self.base_path / f"true_migration_backup_{timestamp}"
        
        # 移行対象ディレクトリ（完全削除対象）
        self.target_dirs_for_deletion = ["libs", "scripts", "tests", "configs", "data", "docs", "workers", "templates"]
    
    def create_comprehensive_backup(self):
        """包括的バックアップ作成"""
        logger.info(f"📦 包括的バックアップ作成: {self.backup_path}")
        
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        for dir_name in self.target_dirs_for_deletion:
            source_dir = self.base_path / dir_name
            if source_dir.exists():
                backup_dest = self.backup_path / dir_name
                logger.info(f"  📦 {dir_name} バックアップ中...")
                shutil.copytree(source_dir, backup_dest, dirs_exist_ok=True)
                logger.info(f"  ✅ {dir_name} バックアップ完了")
    
    def verify_elder_tree_readiness(self) -> bool:
        """Elder Tree準備状況確認"""
        logger.info("🔍 Elder Tree準備状況確認...")
        
        if not self.elder_tree_path.exists():
            logger.error("❌ Elder Tree ディレクトリが存在しません")
            return False
        
        # 必須ディレクトリ確認
        required_dirs = [
            "four_sages",
            "claude_elder", 
            "elder_servants",
            "ancient_elder"
        ]
        
        for req_dir in required_dirs:
            dir_path = self.elder_tree_path / req_dir
            if not dir_path.exists():
                logger.error(f"❌ 必須ディレクトリ不存在: {req_dir}")
                return False
        
        # Elder Tree内のファイル数確認
        elder_files = list(self.elder_tree_path.rglob("*"))
        elder_file_count = len([f for f in elder_files if f.is_file()])
        
        logger.info(f"📊 Elder Tree内ファイル数: {elder_file_count}")
        
        if elder_file_count < 10000:
            logger.warning(f"⚠️ Elder Tree内ファイル数が少ない: {elder_file_count}")
            return False
        
        logger.info("✅ Elder Tree準備完了")
        return True
    
    def execute_true_migration(self) -> bool:
        """真の移行実行（元ディレクトリ削除）"""
        logger.info("🏛️ 真の完全移行開始...")
        
        # Step 1: バックアップ作成
        self.create_comprehensive_backup()
        
        # Step 2: Elder Tree準備確認
        if not self.verify_elder_tree_readiness():
            logger.error("❌ Elder Tree準備不完全 - 移行中止")
            return False
        
        # Step 3: 元ディレクトリの段階的削除
        deleted_counts = {}
        total_deleted = 0
        
        for dir_name in self.target_dirs_for_deletion:
            source_dir = self.base_path / dir_name
            if source_dir.exists():
                try:
                    # ディレクトリ内ファイル数カウント
                    files_in_dir = list(source_dir.rglob("*"))
                    file_count = len([f for f in files_in_dir if f.is_file()])
                    
                    logger.info(f"🗑️ {dir_name} 削除中 ({file_count}ファイル)...")
                    
                    # ディレクトリ完全削除
                    shutil.rmtree(source_dir)
                    
                    deleted_counts[dir_name] = file_count
                    total_deleted += file_count
                    
                    logger.info(f"✅ {dir_name} 削除完了")
                    
                except Exception as e:
                    logger.error(f"❌ {dir_name} 削除エラー: {e}")
                    return False
            else:
                logger.info(f"⏭️ {dir_name} は存在しないためスキップ")
        
        # Step 4: 最終検証
        remaining_files = 0
        for dir_name in self.target_dirs_for_deletion:
            check_dir = self.base_path / dir_name
            if check_dir.exists():
                remaining = list(check_dir.rglob("*"))
                remaining_count = len([f for f in remaining if f.is_file()])
                remaining_files += remaining_count
                logger.error(f"❌ {dir_name} に残存ファイル: {remaining_count}")
        
        if remaining_files == 0:
            logger.info("🎉 真の完全移行成功！")
            logger.info(f"📊 削除統計:")
            for dir_name, count in deleted_counts.items():
                logger.info(f"  - {dir_name}: {count}ファイル削除")
            logger.info(f"📈 総削除ファイル数: {total_deleted}")
            logger.info(f"📦 バックアップ場所: {self.backup_path}")
            return True
        else:
            logger.error(f"❌ 移行失敗 - 残存ファイル: {remaining_files}")
            return False
    
    def create_migration_report(self):
        """移行レポート作成"""
        report_path = self.base_path / "true_migration_report.md"
        
        # Elder Tree内ファイル数再カウント
        elder_files = list(self.elder_tree_path.rglob("*"))
        elder_file_count = len([f for f in elder_files if f.is_file()])
        
        report_content = f"""# True Complete Elder Tree Migration Report

## 移行実行時刻
{time.strftime('%Y-%m-%d %H:%M:%S')}

## 移行結果
- **移行タイプ**: 真の完全移行（元ディレクトリ削除）
- **Elder Tree内ファイル数**: {elder_file_count}
- **バックアップ場所**: {self.backup_path}

## 削除されたディレクトリ
{', '.join(self.target_dirs_for_deletion)}

## Elder Tree構造
```
{self.elder_tree_path}/
├── four_sages/          # 4賢者システム
├── claude_elder/        # クロードエルダー中枢
├── elder_servants/      # エルダーサーバント組織
└── ancient_elder/       # 古代エルダー知識
```

## 注意事項
- 元ファイルは完全削除されました
- 復元が必要な場合はバックアップを使用してください
- Elder Tree内のファイルのみが残存しています

## 検証コマンド
```bash
# 残存確認（結果は0であるべき）
find /home/aicompany/ai_co -name "*.py" | grep -E "(libs|scripts)" | wc -l

# Elder Tree確認
find /home/aicompany/ai_co/elders_guild/elder_tree -name "*.py" | wc -l
```
"""
        
        report_path.write_text(report_content)
        logger.info(f"📄 移行レポート作成: {report_path}")

def main():
    """メイン実行"""
    migrator = TrueCompleteElderMigrator()
    
    print("🏛️ True Complete Elder Tree Migration")
    print("=====================================")
    print("⚠️ この操作は元ディレクトリを完全削除します")
    print("📦 自動的にバックアップが作成されます")
    print("🔄 Elder Tree内のファイルのみが残存します")
    print("")
    
    # 最終確認
    print("対象削除ディレクトリ:")
    for dir_name in migrator.target_dirs_for_deletion:
        dir_path = migrator.base_path / dir_name
        if dir_path.exists():
            file_count = len(list(dir_path.rglob("*.py")))
            print(f"  - {dir_name}: {file_count}ファイル")
    
    print("\n⚠️ この操作は不可逆です！")
    response = input("真の完全移行を実行しますか？ (yes/no): ")
    if response.lower() != "yes":
        print("移行をキャンセルしました。")
        return
    
    # 真の完全移行実行
    success = migrator.execute_true_migration()
    
    if success:
        migrator.create_migration_report()
        print("\n🎉 True Complete Migration 成功！")
        print("✅ 元ディレクトリ完全削除完了")
        print("✅ Elder Tree のみが残存")
        print("✅ バックアップ作成完了")
    else:
        print("\n🚨 True Complete Migration 失敗")
        print("❌ 移行を中断しました")

if __name__ == "__main__":
    main()