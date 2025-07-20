#!/usr/bin/env python3
"""
🚨 エルダー評議会緊急令: ルートディレクトリ大掃除システム
Emergency Cleanup Script for Elders Guild Root Directory

エルダー評議会令第34号完全遵守のための緊急実行スクリプト
"""

import os
import shutil
from pathlib import Path
import subprocess
from datetime import datetime

class EmergencyElderCleanup:
    """🏛️ エルダー評議会緊急掃除システム"""
    
    def __init__(self):
        self.root = Path("/home/aicompany/ai_co")
        self.backup_dir = self.root / "cleanup_backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.moved_files = []
        
        # 保護ファイル（移動しない）
        self.protected_files = {
            "README.md",
            "CLAUDE.md", 
            "requirements.txt",
            "Dockerfile",
            "docker-compose.yml",
            "conftest.py",
            "pytest.ini",
            "pre-commit-config.yaml",
            ".env",
            ".gitignore"
        }
        
    def analyze_violations(self):
        """評議会令第34号違反状況分析"""
        print("🔍 エルダー評議会令第34号違反分析開始")
        
        violations = {
            "reports": [],
            "docs": [],
            "scripts": [],
            "tests": [],
            "configs": [],
            "temp_files": []
        }
        
        for file_path in self.root.glob("*"):
            if file_path.is_file() and file_path.name not in self.protected_files:
                name = file_path.name.lower()
                
                # レポート系
                if any(keyword in name for keyword in ["report", "analysis", "summary", "audit"]):
                    violations["reports"].append(file_path)
                
                # ドキュメント系  
                elif name.endswith(".md"):
                    violations["docs"].append(file_path)
                
                # スクリプト系
                elif name.startswith("ai_") and name.endswith(".py"):
                    violations["scripts"].append(file_path)
                
                # テスト系
                elif name.startswith("test_") and name.endswith(".py"):
                    violations["tests"].append(file_path)
                
                # 設定系
                elif any(ext in name for ext in ["config", "compose", ".ini", ".conf"]):
                    violations["configs"].append(file_path)
                
                # 一時ファイル
                elif any(keyword in name for keyword in ["temp", "tmp", "debug", "manual"]):
                    violations["temp_files"].append(file_path)
        
        # 結果表示
        total_violations = sum(len(v) for v in violations.values())
        print(f"📊 総違反ファイル数: {total_violations}")
        
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
    
    def move_to_docs_reports(self, files):
        """📋 docs/reports/ への移動"""
        if not files:
            return
            
        target_dir = self.root / "docs" / "reports"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in files:
            try:
                backup = self.create_backup(file_path)
                target = target_dir / file_path.name
                shutil.move(file_path, target)
                self.moved_files.append(f"{file_path} → {target}")
                print(f"📋 移動: {file_path.name} → docs/reports/")
            except Exception as e:
                print(f"❌ 移動失敗: {file_path.name} - {e}")
    
    def move_to_docs_technical(self, files):
        """📚 docs/technical/ への移動"""
        if not files:
            return
            
        target_dir = self.root / "docs" / "technical"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in files:
            try:
                backup = self.create_backup(file_path)
                target = target_dir / file_path.name
                shutil.move(file_path, target)
                self.moved_files.append(f"{file_path} → {target}")
                print(f"📚 移動: {file_path.name} → docs/technical/")
            except Exception as e:
                print(f"❌ 移動失敗: {file_path.name} - {e}")
    
    def move_to_scripts(self, files):
        """⚡ scripts/ への移動"""
        if not files:
            return
            
        target_dir = self.root / "scripts"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in files:
            try:
                backup = self.create_backup(file_path)
                target = target_dir / file_path.name
                shutil.move(file_path, target)
                self.moved_files.append(f"{file_path} → {target}")
                print(f"⚡ 移動: {file_path.name} → scripts/")
            except Exception as e:
                print(f"❌ 移動失敗: {file_path.name} - {e}")
    
    def move_to_tests(self, files):
        """🧪 tests/ への移動"""
        if not files:
            return
            
        target_dir = self.root / "tests"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in files:
            try:
                backup = self.create_backup(file_path)
                target = target_dir / file_path.name
                shutil.move(file_path, target)
                self.moved_files.append(f"{file_path} → {target}")
                print(f"🧪 移動: {file_path.name} → tests/")
            except Exception as e:
                print(f"❌ 移動失敗: {file_path.name} - {e}")
    
    def move_to_configs(self, files):
        """⚙️ configs/ への移動"""
        if not files:
            return
            
        target_dir = self.root / "configs"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in files:
            try:
                backup = self.create_backup(file_path)
                target = target_dir / file_path.name
                shutil.move(file_path, target)
                self.moved_files.append(f"{file_path} → {target}")
                print(f"⚙️ 移動: {file_path.name} → configs/")
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
    
    def execute_cleanup(self):
        """🚀 緊急クリーンアップ実行"""
        print("🏛️ エルダー評議会緊急掃除システム起動")
        print("=" * 50)
        
        violations = self.analyze_violations()
        
        if not any(violations.values()):
            print("✅ 評議会令第34号完全遵守状態です")
            return True
        
        print("\n🚨 緊急掃除開始...")
        
        # カテゴリ別移動実行
        self.move_to_docs_reports(violations["reports"])
        self.move_to_docs_technical(violations["docs"])
        self.move_to_scripts(violations["scripts"])
        self.move_to_tests(violations["tests"])
        self.move_to_configs(violations["configs"])
        self.remove_temp_files(violations["temp_files"])
        
        print(f"\n✅ 緊急掃除完了: {len(self.moved_files)}件処理")
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
    cleanup = EmergencyElderCleanup()
    
    try:
        result = cleanup.execute_cleanup()
        if result:
            print("\n🎉 エルダー評議会令第34号完全遵守達成！")
            return 0
        else:
            print("\n⚠️ 一部問題が残存しています")
            return 1
    except Exception as e:
        print(f"\n❌ 緊急掃除システムエラー: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())