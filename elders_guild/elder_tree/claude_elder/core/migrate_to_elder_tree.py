#!/usr/bin/env python3
"""
Elder Tree移行バッチスクリプト
既存のai_coプロジェクトからElders Guildへの資産移行を自動化
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# 基本パス設定
SOURCE_BASE = Path("/home/aicompany/ai_co")
TARGET_BASE = Path("/home/aicompany/elders_guild")

# 移行マッピング定義
MIGRATION_MAPPING = {
    # 4賢者システム
    "knowledge_sage": {
        "files": [
            "libs/knowledge_sage.py",
            "libs/knowledge_sage_enhanced.py",
            "libs/knowledge_sage_manager.py",
            "libs/four_sages/knowledge/",
        ],
        "target": "knowledge_sage/abilities/",
        "priority": 3
    },
    "task_sage": {
        "files": [
            "libs/task_sage.py",
            "libs/task_sage_enhanced.py",
            "libs/claude_task_tracker.py",
            "libs/claude_task_tracker_v2.0py",
            "libs/four_sages/task/",
        ],
        "target": "task_sage/abilities/",
        "priority": 3
    },
    "incident_sage": {
        "files": [
            "libs/incident_sage.py",
            "libs/incident_manager.py",
            "libs/four_sages/incident/",
        ],
        "target": "incident_sage/abilities/",
        "priority": 3
    },
    "rag_sage": {
        "files": [
            "libs/rag_sage.py",
            "libs/rag_manager.py",
            "libs/enhanced_rag_manager.py",
            "libs/four_sages/rag/",
        ],
        "target": "rag_sage/abilities/",
        "priority": 3
    },
    
    # Elder Flow（Claude Elder統括機能）
    "claude_elder": {
        "files": [
            "libs/elder_flow/",
            "libs/elder_system/",
            "libs/perfect_a2a/",
        ],
        "target": "claude_elder/abilities/",
        "priority": 3
    },
    
    # Elder Servants
    "code_craftsman": {
        "files": [
            "libs/elder_servants/dwarf_workshop/",
        ],
        "target": "elder_servants/code_craftsman/abilities/",
        "priority": 2
    },
    "quality_inspector": {
        "files": [
            "libs/elders_code_quality_engine.py",
            "libs/automated_code_review.py",
            "libs/integration_test_framework.py",
        ],
        "target": "elder_servants/quality_inspector/abilities/",
        "priority": 2
    },
    "test_guardian": {
        "files": [
            "libs/test_coverage_analyzer.py",
            "libs/integration_test_framework.py",
        ],
        "target": "elder_servants/test_guardian/abilities/",
        "priority": 2
    },
    "security_auditor": {
        "files": [
            "libs/security_audit_system.py",
            "libs/elder_guild_security_validator.py",
        ],
        "target": "elder_servants/security_auditor/abilities/",
        "priority": 2
    },
    
    # Ancient Magic
    "learning_magic": {
        "files": [
            "libs/ai_self_evolution_engine.py",
            "libs/automated_learning_system.py",
            "libs/meta_learning_system.py",
            "libs/knowledge_evolution.py",
        ],
        "target": "ancient_magic/learning_magic/abilities/",
        "priority": 2
    },
    "search_magic": {
        "files": [
            "libs/rag_manager.py",
            "libs/enhanced_rag_manager.py",
        ],
        "target": "ancient_magic/search_magic/abilities/",
        "priority": 2
    },
    "optimization_magic": {
        "files": [
            "libs/performance_optimizer.py",
            "libs/async_worker_optimization.py",
        ],
        "target": "ancient_magic/optimization_magic/abilities/",
        "priority": 2
    },
    
    # インフラストラクチャ
    "a2a_broker": {
        "files": [
            "libs/a2a_communication.py",
            "libs/rabbitmq_manager.py",
        ],
        "target": "infrastructure/a2a_broker/",
        "priority": 2
    },
    
    # 共有ライブラリ
    "shared_libs": {
        "files": [
            "libs/utilities/",
            "libs/base_manager.py",
            "libs/common_utils.py",
            "libs/config_manager.py",
        ],
        "target": "shared_libs/",
        "priority": 3
    },
    
    # MCP Tools
    "mcp_tools": {
        "files": [
            "libs/mcp_servers/",
        ],
        "target": "mcp_tools/",
        "priority": 1
    }
}


class ElderTreeMigrator:
    """Elder Tree移行管理クラス"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.migration_log = []
        self.errors = []
        
    def migrate(self, components: List[str] = None):
        """指定されたコンポーネントを移行"""
        if components is None:
            # 優先度順にすべてのコンポーネントを移行
            components = sorted(
                MIGRATION_MAPPING.keys(),
                key=lambda x: MIGRATION_MAPPING[x]["priority"],
                reverse=True
            )
        
        print(f"🚀 Elder Tree移行開始 (Dry Run: {self.dry_run})")
        print(f"対象コンポーネント: {', '.join(components)}")
        print("-" * 60)
        
        for component in components:
            if component in MIGRATION_MAPPING:
                self._migrate_component(component)
            else:
                print(f"❌ 不明なコンポーネント: {component}")
        
        self._save_migration_report()
        
    def _migrate_component(self, component: str):
        """単一コンポーネントの移行"""
        config = MIGRATION_MAPPING[component]
        target_dir = TARGET_BASE / config["target"]
        
        print(f"\n📦 {component} の移行開始...")
        
        # ターゲットディレクトリの作成
        if not self.dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
        
        for source_path in config["files"]:
            source_full = SOURCE_BASE / source_path
            
            if source_full.exists():
                if source_full.is_dir():
                    self._migrate_directory(source_full, target_dir)
                else:
                    self._migrate_file(source_full, target_dir)
            else:
                error_msg = f"ソースが見つかりません: {source_full}"
                print(f"  ⚠️  {error_msg}")
                self.errors.append(error_msg)
    
    def _migrate_file(self, source: Path, target_dir: Path):
        """ファイルの移行"""
        target_file = target_dir / source.name
        
        if self.dry_run:
            print(f"  📄 {source.relative_to(SOURCE_BASE)} → {target_file.relative_to(TARGET_BASE)}")
        else:
            try:
                shutil.copy2(source, target_file)
                print(f"  ✅ {source.name} をコピーしました")
                self.migration_log.append({
                    "type": "file",
                    "source": str(source),
                    "target": str(target_file),
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                error_msg = f"コピー失敗: {source} - {str(e)}"
                print(f"  ❌ {error_msg}")
                self.errors.append(error_msg)
    
    def _migrate_directory(self, source: Path, target_dir: Path):
        """ディレクトリの移行"""
        target_subdir = target_dir / source.name
        
        if self.dry_run:
            print(f"  📁 {source.relative_to(SOURCE_BASE)}/ → {target_subdir.relative_to(TARGET_BASE)}/")
            # ドライランでは中身も表示
            for item in source.rglob("*.py"):
                if item.is_file():
                    print(f"     - {item.relative_to(source)}")
        else:
            try:
                shutil.copytree(source, target_subdir, dirs_exist_ok=True)
                file_count = len(list(target_subdir.rglob("*.py")))
                print(f"  ✅ {source.name}/ をコピーしました ({file_count}ファイル)")
                self.migration_log.append({
                    "type": "directory",
                    "source": str(source),
                    "target": str(target_subdir),
                    "file_count": file_count,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                error_msg = f"コピー失敗: {source} - {str(e)}"
                print(f"  ❌ {error_msg}")
                self.errors.append(error_msg)
    
    def _save_migration_report(self):
        """移行レポートの保存"""
        if self.dry_run:
            print("\n📊 Dry Run完了 - 実際の移行は行われていません")
            return
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "migration_log": self.migration_log,
            "errors": self.errors,
            "summary": {
                "total_items": len(self.migration_log),
                "files": len([x for x in self.migration_log if x["type"] == "file"]),
                "directories": len([x for x in self.migration_log if x["type"] == "directory"]),
                "errors": len(self.errors)
            }
        }
        
        report_path = TARGET_BASE / "migration_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 移行レポート: {report_path}")
        print(f"  - 移行項目数: {report['summary']['total_items']}")
        print(f"  - エラー数: {report['summary']['errors']}")


def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Elder Tree移行バッチ")
    parser.add_argument("--execute", action="store_true", help="実際に移行を実行（デフォルトはDry Run）")
    parser.add_argument("--components", nargs="+", help="移行するコンポーネントを指定")
    parser.add_argument("--priority", type=int, help="指定優先度以上のコンポーネントのみ移行")
    
    args = parser.parse_args()
    
    # 移行対象の決定
    components = args.components
    if args.priority:
        components = [
            k for k, v in MIGRATION_MAPPING.items()
            if v["priority"] >= args.priority
        ]
    
    # 移行実行
    migrator = ElderTreeMigrator(dry_run=not args.execute)
    migrator.migrate(components)


if __name__ == "__main__":
    main()