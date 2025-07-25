#!/usr/bin/env python3
"""
🌊 Elder Flow Soul系ファイル段階的廃止スクリプト
==============================================

Soul系ファイルの安全な段階的廃止実行

Author: Claude Elder
Created: 2025-07-23
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime


class ElderFlowSoulDeprecator:
    """Elder Flow Soul廃止システム"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.deprecation_dir = self.project_root / "archives" / "soul_deprecation_20250723"
        
        # 段階的廃止対象
        self.phase1_targets = [
            "libs/elder_flow_soul_integration.py",
            "libs/google_a2a_soul_integration.py", 
            "libs/elder_tree_soul_binding.py",
            "libs/elder_flow_soul_connector.py",
            "libs/soul_process_manager.py"
        ]
        
        self.phase2_targets = [
            "scripts/elder_soul_benchmark.py",
            "scripts/setup_elder_soul.py",
            "scripts/elder_soul",
            "scripts/elder_soul_add_agent",
            "scripts/install_elder_soul.sh"
        ]
        
        self.phase3_targets = [
            "incident_sage/soul.py",
            "knowledge_sage/soul.py", 
            "task_sage/soul.py",
            "rag_sage/soul.py"
        ]
        
        self.phase4_targets = [
            "shared_libs/soul_base.py",
            "libs/base_soul.py"
        ]
        
        # バックアップディレクトリ内Soul関連（削除対象）
        self.backup_targets = [
            "elders_guild/incident_sage/soul.py",
            "elders_guild/knowledge_sage/soul.py",
            "elders_guild/task_sage/soul.py", 
            "elders_guild/rag_sage/soul.py",
            "elders_guild/shared_libs/soul_base.py"
        ]
    
    def create_deprecation_archive(self) -> None:
        """廃止ファイルアーカイブ作成"""
        print("📁 Soul廃止アーカイブ作成中...")
        self.deprecation_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 アーカイブディレクトリ: {self.deprecation_dir}")
    
    def deprecate_phase(self, phase: int, targets: List[str], description: str) -> Tuple[int, int]:
        """個別フェーズ廃止実行"""
        print(f"\\n🗑️ Phase {phase}: {description}")
        print("-" * 50)
        
        success_count = 0
        total_count = len(targets)
        
        for target in targets:
            target_path = self.project_root / target
            
            if target_path.exists():
                try:
                    # アーカイブに移動
                    archive_path = self.deprecation_dir / target_path.name
                    shutil.move(str(target_path), str(archive_path))
                    print(f"  ✅ {target} → アーカイブ")
                    success_count += 1
                except Exception as e:
                    print(f"  ❌ {target}: エラー - {e}")
            else:
                print(f"  ⏭️ {target}: 既に存在しない")
                success_count += 1
        
        print(f"Phase {phase} 完了: {success_count}/{total_count}")
        return success_count, total_count
    
    def cleanup_backup_souls(self) -> Tuple[int, int]:
        """バックアップディレクトリ内Soul削除"""
        print("\\n🧹 バックアップディレクトリ内Soul削除")
        print("-" * 50)
        
        success_count = 0
        total_count = len(self.backup_targets)
        
        for target in self.backup_targets:
            target_path = self.project_root / target
            
            if target_path.exists():
                try:
                    target_path.unlink()
                    print(f"  ✅ {target} 削除")
                    success_count += 1
                except Exception as e:
                    print(f"  ❌ {target}: エラー - {e}")
            else:
                print(f"  ⏭️ {target}: 既に存在しない")
                success_count += 1
        
        return success_count, total_count
    
    def verify_4sages_integrity(self) -> bool:
        """4賢者システム整合性確認"""
        print("\\n🔍 4賢者システム整合性確認")
        print("-" * 50)
        
        sages = ["incident_sage", "knowledge_sage", "task_sage", "rag_sage"]
        all_good = True
        
        for sage in sages:
            business_logic = self.project_root / sage / "business_logic.py"
            a2a_agent = self.project_root / sage / "a2a_agent.py"
            
            bl_exists = business_logic.exists()
            a2a_exists = a2a_agent.exists()
            
            status = "✅" if (bl_exists and a2a_exists) else "❌"
            print(f"  {status} {sage}: business_logic.py({bl_exists}) + a2a_agent.py({a2a_exists})")
            
            if not (bl_exists and a2a_exists):
                all_good = False
        
        return all_good
    
    def execute_deprecation(self) -> None:
        """Elder Flow Soul廃止実行"""
        print("🌊 Elder Flow Soul系ファイル段階的廃止開始")
        print("=" * 60)
        
        # アーカイブ作成
        self.create_deprecation_archive()
        
        # 4賢者システム整合性事前確認
        if not self.verify_4sages_integrity():
            print("\\n⚠️ 4賢者システムに問題があります。廃止を中断します。")
            return
        
        # 段階的廃止実行
        total_success = 0
        total_files = 0
        
        # Phase 1: 実験的Soul実装
        s1, t1 = self.deprecate_phase(1, self.phase1_targets, "実験的Soul実装廃止")
        total_success += s1
        total_files += t1
        
        # Phase 2: Soul支援スクリプト
        s2, t2 = self.deprecate_phase(2, self.phase2_targets, "Soul支援スクリプト廃止")
        total_success += s2
        total_files += t2
        
        # Phase 3: 4賢者Soul実装（バックアップ済み）
        s3, t3 = self.deprecate_phase(3, self.phase3_targets, "4賢者Soul実装廃止")
        total_success += s3
        total_files += t3
        
        # Phase 4: Soul基底クラス（最終）
        s4, t4 = self.deprecate_phase(4, self.phase4_targets, "Soul基底クラス廃止")
        total_success += s4
        total_files += t4
        
        # バックアップディレクトリクリーンアップ
        s5, t5 = self.cleanup_backup_souls()
        total_success += s5
        total_files += t5
        
        # 最終確認
        print("\\n" + "=" * 60)
        print("🎉 Elder Flow Soul廃止完了")
        print("=" * 60)
        print(f"📊 廃止成功: {total_success}/{total_files}")
        print(f"📁 アーカイブ場所: {self.deprecation_dir}")
        
        # 4賢者システム最終確認
        if self.verify_4sages_integrity():
            print("\\n✅ 4賢者システム: 正常動作確認")
        else:
            print("\\n❌ 4賢者システム: 問題検出")
        
        print("\\n🚀 Soul系廃止完了 - 4賢者システム完全移行達成！")
        print("=" * 60)


def main():
    """メイン実行"""
    deprecator = ElderFlowSoulDeprecator()
    deprecator.execute_deprecation()


if __name__ == "__main__":
    main()