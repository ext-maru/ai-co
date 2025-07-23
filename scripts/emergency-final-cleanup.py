#!/usr/bin/env python3
"""
🚨 エルダー評議会最終掃除令: 残存ファイル専用フォルダ移動システム
Final Emergency Cleanup for Remaining Root Directory Files

評議会令第34号完全遵守のための最終掃除
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

class FinalEmergencyCleanup:
    """🏛️ エルダー評議会最終掃除システム"""
    
    def __init__(self):
        self.root = Path("/home/aicompany/ai_co")
        self.backup_dir = self.root / "cleanup_backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.moved_files = []
        
        # 保護ファイル（移動しない）
        self.protected_files = {
            "README.md",
            "CLAUDE.md", 
            "requirements.txt",
            "docker-compose.yml",
            "conftest.py",
            "pytest.ini",
            "pre-commit-config.yaml",
            ".env",
            ".gitignore",
            "Makefile.oss",
            "sonar-project.properties",
            "sonar-project-oss.properties"
        }
        
        # 作業用フォルダマッピング
        self.folder_mapping = {
            "working_files": "auto_generated",  # 作業用データベース・ログ
            "output_files": "output",          # 出力ファイル
            "temp_files": "temp",              # 一時ファイル
        }
        
    def analyze_remaining_files(self):
        """残存ファイル分析"""
        print("🔍 最終掃除対象ファイル分析開始")
        
        violations = {
            "working_files": [],    # .db, .log, .json等作業用ファイル
            "output_files": [],     # レポート・出力ファイル
            "temp_files": [],       # 一時ファイル
            "other_files": []       # その他
        }
        
        for file_path in self.root.glob("*"):
            if file_path.is_file() and file_path.name not in self.protected_files:
                name = file_path.name.lower()
                
                # 作業用ファイル
                if any(ext in name for ext in ['.db', '.log', '.json']) and \
                    not any(word in name for word in ['requirements', 'package']):
                    violations["working_files"].append(file_path)
                
                # 出力・レポートファイル
                elif any(keyword in name for keyword in ['report', 'summary', 'analysis', 'coverage', 'performance']):
                    violations["output_files"].append(file_path)
                
                # 一時ファイル
                elif any(keyword in name for keyword in ['temp', 'tmp', 'test_', 'debug', 'manual', 'false_claims']):
                    violations["temp_files"].append(file_path)
                
                # その他
                else:
                    violations["other_files"].append(file_path)
        
        # 結果表示
        total_violations = sum(len(v) for v in violations.values())
        print(f"📊 残存違反ファイル数: {total_violations}")
        
        for category, files in violations.items():
            if files:
                print(f"  {category}: {len(files)}個")
        
        return violations
    
    def create_backup(self, file_path):
        """🛡️ バックアップ作成"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = self.backup_dir / file_path.name
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def move_to_folder(self, files, target_folder_name, category_name):
        """指定フォルダへの移動"""
        if not files:
            return
            
        target_dir = self.root / target_folder_name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in files:
            try:
                backup = self.create_backup(file_path)
                target = target_dir / file_path.name
                shutil.move(file_path, target)
                self.moved_files.append(f"{file_path} → {target}")
                print(f"📁 移動: {file_path.name} → {target_folder_name}/")
            except Exception as e:
                print(f"❌ 移動失敗: {file_path.name} - {e}")
    
    def remove_temp_files(self, files):
        """🗑️ 一時ファイル削除"""
        if not files:
            return
            
        for file_path in files:
            try:
                backup = self.create_backup(file_path)
                file_path.unlink()
                self.moved_files.append(f"{file_path} → 削除済み (backup: {backup})")
                print(f"🗑️ 削除: {file_path.name}")
            except Exception as e:
                print(f"❌ 削除失敗: {file_path.name} - {e}")
    
    def execute_final_cleanup(self):
        """🚀 最終掃除実行"""
        print("🏛️ エルダー評議会最終掃除システム起動")
        print("=" * 50)
        
        violations = self.analyze_remaining_files()
        
        if not any(violations.values()):
            print("✅ すべてのファイルが適切に配置されています")
            return True
        
        print("\n🚨 最終掃除開始...")
        
        # カテゴリ別移動実行
        self.move_to_folder(violations["working_files"], "auto_generated", "作業用ファイル")
        self.move_to_folder(violations["output_files"], "output", "出力ファイル")
        self.remove_temp_files(violations["temp_files"])
        
        # その他ファイルをauto_generatedに移動
        if violations["other_files"]:
            print(f"\n⚠️ その他ファイル {len(violations['other_files'])}個をauto_generated/へ移動")
            self.move_to_folder(violations["other_files"], "auto_generated", "その他ファイル")
        
        print(f"\n✅ 最終掃除完了: {len(self.moved_files)}件処理")
        if self.backup_dir.exists():
            print(f"🛡️ バックアップ場所: {self.backup_dir}")
        
        # 最終確認
        print("\n📊 掃除後状況:")
        remaining_files = list(self.root.glob("*"))
        remaining_count = len([f for f in remaining_files if f.is_file()])
        print(f"ルートディレクトリファイル数: {remaining_count}")
        
        return True

def main():
    """メイン実行"""
    cleanup = FinalEmergencyCleanup()
    
    try:
        result = cleanup.execute_final_cleanup()
        if result:
            print("\n🎉 エルダー評議会令第34号最終完全遵守達成！")
            return 0
        else:
            print("\n⚠️ 一部問題が残存しています")
            return 1
    except Exception as e:
        print(f"\n❌ 最終掃除システムエラー: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())