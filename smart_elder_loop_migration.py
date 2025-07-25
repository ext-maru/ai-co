#!/usr/bin/env python3
"""
🧠 Smart Elder Loop Migration System
賢い内容分析による真の Elder Tree 移行（95%品質基準達成）
"""

import os
import shutil
import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set
import time
import ast

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [Smart Elder Loop] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SmartElderLoopMigrator:
    """賢いElder Loop完全移行システム"""
    
    def __init__(self):
        self.base_path = Path("/home/aicompany/ai_co")
        self.elder_tree_path = self.base_path / "elders_guild" / "elder_tree"
        
        # Elder Loop品質基準
        self.quality_threshold = 95  # 95%以上の移行率必須
        self.phase4_max_iterations = 15  # Phase 4最大反復回数
        
        # バックアップディレクトリ
        timestamp = int(time.time())
        self.backup_path = self.base_path / f"smart_elder_backup_{timestamp}"
        
        # ファイル分類キーワード
        self.classification_keywords = {
            "four_sages": {
                "incident": ["incident", "error", "exception", "crisis", "emergency", "alert"],
                "knowledge": ["knowledge", "learn", "memory", "database", "store", "cache"],
                "rag": ["search", "query", "retrieve", "find", "index", "vector"],
                "task": ["task", "job", "queue", "schedule", "workflow", "process"]
            },
            "claude_elder": {
                "flow": ["elder_flow", "orchestrat", "pipeline", "workflow"],
                "core": ["claude", "elder", "main", "primary", "central"],
                "integration": ["cli", "api", "interface", "gateway"]
            },
            "elder_servants": {
                "dwarf_tribe": ["script", "tool", "command", "utility", "helper", "git", "deploy"],
                "quality_tribe": ["test", "quality", "lint", "check", "validate", "review"],
                "elf_tribe": ["monitor", "watch", "observe", "metric", "log", "health"],
                "wizard_tribe": ["mcp", "magic", "transform", "generate", "wizard"]
            },
            "ancient_elder": {
                "documentation": ["doc", "readme", "guide", "manual", "spec"],
                "legacy": ["old", "deprecated", "ancient", "legacy", "archive"]
            }
        }
    
    def analyze_file_content(self, file_path: Path) -> Dict[str, float]:
        """ファイル内容を分析してカテゴリスコアを算出"""
        try:
            if file_path.suffix == '.py':
                content = file_path.read_text(encoding='utf-8', errors='ignore')
            else:
                content = file_path.read_text(encoding='utf-8', errors='ignore')[:1000]  # 最初の1000文字のみ
                
            content_lower = content.lower()
            scores = {}
            
            # ファイル名・パススコア
            path_str = str(file_path).lower()
            
            for main_category, subcategories in self.classification_keywords.items():
                category_score = 0
                
                if isinstance(subcategories, dict):
                    for sub_category, keywords in subcategories.items():
                        sub_score = 0
                        for keyword in keywords:
                            # パス内のキーワード（高スコア）
                            if keyword in path_str:
                                sub_score += 3
                            # 内容内のキーワード（中スコア）
                            content_matches = len(re.findall(rf'\b{keyword}\w*', content_lower))
                            sub_score += content_matches * 0.5
                        
                        scores[f"{main_category}/{sub_category}"] = sub_score
                        category_score = max(category_score, sub_score)
                else:
                    for keyword in subcategories:
                        if keyword in path_str:
                            category_score += 3
                        content_matches = len(re.findall(rf'\b{keyword}\w*', content_lower))
                        category_score += content_matches * 0.5
                
                scores[main_category] = category_score
            
            return scores
            
        except Exception as e:
            logger.warning(f"⚠️ ファイル分析エラー {file_path.name}: {e}")
            return {}
    
    def categorize_file(self, file_path: Path) -> str:
        """ファイルを最適なカテゴリに分類"""
        scores = self.analyze_file_content(file_path)
        
        if not scores:
            return "elder_servants/coordination/shared_resources/core"
        
        # 最高スコアのカテゴリを選択
        best_category = max(scores.items(), key=lambda x: x[1])
        category_name, score = best_category
        
        # スコアが低い場合はデフォルト
        if score < 1.0:
            return "elder_servants/coordination/shared_resources/core"
        
        # カテゴリマッピング
        category_mappings = {
            "four_sages/incident": "four_sages/incident",
            "four_sages/knowledge": "four_sages/knowledge", 
            "four_sages/rag": "four_sages/rag",
            "four_sages/task": "four_sages/task",
            "claude_elder/flow": "claude_elder/flow/engine",
            "claude_elder/core": "claude_elder/core",
            "claude_elder/integration": "claude_elder/integration/cli",
            "elder_servants/dwarf_tribe": "elder_servants/dwarf_tribe/tools",
            "elder_servants/quality_tribe": "elder_servants/quality_tribe/engines",
            "elder_servants/elf_tribe": "elder_servants/elf_tribe/monitoring",
            "elder_servants/wizard_tribe": "elder_servants/wizard_tribe/mcp_tools",
            "ancient_elder/documentation": "ancient_elder/documentation",
            "ancient_elder/legacy": "ancient_elder/legacy"
        }
        
        return category_mappings.get(category_name, "elder_servants/coordination/shared_resources/core")
    
    def smart_analyze_all_files(self) -> Dict[str, List[Path]]:
        """全ファイルの賢い分析"""
        logger.info("🧠 Phase 1: 賢いファイル分析開始...")
        
        file_categories = {}
        total_files = 0
        
        # 分析対象ディレクトリ
        target_dirs = ["libs", "scripts", "tests", "configs", "data", "docs", "workers", "templates"]
        
        for dir_name in target_dirs:
            dir_path = self.base_path / dir_name
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file() and not self._is_in_elder_tree(file_path):
                        category = self.categorize_file(file_path)
                        
                        if category not in file_categories:
                            file_categories[category] = []
                        file_categories[category].append(file_path)
                        total_files += 1
        
        # 統計情報
        logger.info(f"📊 賢い分析結果:")
        for category, files in sorted(file_categories.items()):
            logger.info(f"  - {category}: {len(files)}ファイル")
        logger.info(f"📈 総分析ファイル数: {total_files}")
        
        return file_categories
    
    def _is_in_elder_tree(self, file_path: Path) -> bool:
        """ファイルが既にElder Tree内にあるかチェック"""
        try:
            file_path.relative_to(self.elder_tree_path)
            return True
        except ValueError:
            return False
    
    def create_smart_mapping(self, file_categories: Dict[str, List[Path]]) -> Dict[Path, Path]:
        """賢いマッピング作成"""
        logger.info("🗺️ Phase 2: 賢いマッピング作成...")
        
        mapping = {}
        
        for category, files in file_categories.items():
            for file_path in files:
                # 相対パス維持
                try:
                    # ベースディレクトリからの相対パス
                    for base_dir in ["libs", "scripts", "tests", "configs", "data", "docs", "workers", "templates"]:
                        base_path = self.base_path / base_dir
                        if file_path.is_relative_to(base_path):
                            relative_path = file_path.relative_to(base_path)
                            dest = self.elder_tree_path / category / relative_path
                            mapping[file_path] = dest
                            break
                    else:
                        # フォールバック
                        dest = self.elder_tree_path / category / file_path.name
                        mapping[file_path] = dest
                        
                except Exception as e:
                    logger.warning(f"⚠️ マッピングエラー {file_path.name}: {e}")
                    dest = self.elder_tree_path / category / file_path.name
                    mapping[file_path] = dest
        
        logger.info(f"🗺️ 賢いマッピング作成完了: {len(mapping)}個のファイル")
        return mapping
    
    def execute_smart_migration(self, mapping: Dict[Path, Path]) -> Tuple[int, int, List[str]]:
        """賢い移行実行"""
        logger.info(f"🧠 Phase 3: 賢い移行実行...")
        
        success_count = 0
        error_count = 0
        errors = []
        
        # バックアップ作成
        if not self.backup_path.exists():
            self.backup_path.mkdir(parents=True)
            logger.info(f"📦 バックアップディレクトリ作成: {self.backup_path}")
        
        for i, (source, dest) in enumerate(mapping.items()):
            try:
                # 宛先ディレクトリ作成
                dest.parent.mkdir(parents=True, exist_ok=True)
                
                # ファイル移行（コピー）
                if source.is_file():
                    shutil.copy2(source, dest)
                    success_count += 1
                    
                    if i % 500 == 0:
                        logger.info(f"🧠 進捗: {i}/{len(mapping)} ({(i/len(mapping)*100):.1f}%)")
                
            except Exception as e:
                error_count += 1
                error_msg = f"❌ {source.name}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        logger.info(f"🧠 賢い移行完了: 成功 {success_count}, エラー {error_count}")
        return success_count, error_count, errors
    
    def phase4_smart_verification(self, expected_files: int) -> Tuple[bool, float, List[str]]:
        """Phase 4: 賢い厳密検証"""
        logger.info("🔍 Phase 4: 賢い厳密検証開始...")
        
        issues = []
        
        # Elder Tree内のファイル数カウント
        elder_tree_files = []
        for file_path in self.elder_tree_path.rglob("*"):
            if file_path.is_file():
                elder_tree_files.append(file_path)
        
        migration_rate = (len(elder_tree_files) / expected_files) * 100
        
        logger.info(f"📊 移行率: {migration_rate:.1f}% ({len(elder_tree_files)}/{expected_files})")
        
        if migration_rate < self.quality_threshold:
            issues.append(f"移行率が基準値未満: {migration_rate:.1f}% < {self.quality_threshold}%")
        
        # ディレクトリ構造チェック
        required_dirs = [
            "four_sages/incident",
            "four_sages/knowledge", 
            "four_sages/rag",
            "four_sages/task",
            "claude_elder/core",
            "elder_servants/dwarf_tribe/tools",
            "elder_servants/quality_tribe/engines",
            "ancient_elder/documentation"
        ]
        
        for req_dir in required_dirs:
            dir_path = self.elder_tree_path / req_dir
            if not dir_path.exists():
                issues.append(f"必須ディレクトリ不存在: {req_dir}")
            else:
                file_count = len(list(dir_path.rglob("*.py")))
                if file_count == 0:
                    issues.append(f"空ディレクトリ: {req_dir}")
        
        # ファイル分散チェック
        categories = {}
        for file_path in elder_tree_files:
            try:
                relative_path = file_path.relative_to(self.elder_tree_path)
                category = str(relative_path.parts[0]) if relative_path.parts else "root"
                categories[category] = categories.get(category, 0) + 1
            except:
                pass
        
        # 分散が適切かチェック
        if len(categories) < 4:
            issues.append(f"ファイル分散不足: {len(categories)}カテゴリのみ")
        
        is_passed = len(issues) == 0 and migration_rate >= self.quality_threshold
        
        logger.info(f"🔍 Phase 4検証結果: {'✅ 合格' if is_passed else '❌ 不合格'}")
        if issues:
            for issue in issues:
                logger.error(f"🚨 {issue}")
        
        return is_passed, migration_rate, issues
    
    def execute_smart_elder_loop(self):
        """賢いElder Loop完全実行"""
        logger.info("🧠 Smart Elder Loop Complete Migration 開始...")
        
        iteration = 0
        
        while iteration < self.phase4_max_iterations:
            iteration += 1
            logger.info(f"🔄 Smart Elder Loop 反復 {iteration}/{self.phase4_max_iterations}")
            
            # Phase 1: 賢い要件分析・設計
            file_categories = self.smart_analyze_all_files()
            total_expected = sum(len(files) for files in file_categories.values())
            
            if total_expected == 0:
                logger.info("✅ 移行対象ファイルなし - Smart Elder Loop完了")
                break
            
            # Phase 2: 賢いマッピング設計
            mapping = self.create_smart_mapping(file_categories)
            
            # Phase 3: 賢い実装・移行
            success_count, error_count, errors = self.execute_smart_migration(mapping)
            
            # Phase 4: 賢い厳密検証
            is_passed, migration_rate, issues = self.phase4_smart_verification(total_expected)
            
            if is_passed:
                logger.info("✅ Phase 4合格 - Phase 5に進む")
                break
            else:
                logger.warning(f"⚠️ Phase 4不合格 - 反復継続 (残り{self.phase4_max_iterations - iteration}回)")
                if iteration == self.phase4_max_iterations:
                    logger.error("🚨 Smart Elder Loop最大反復回数到達")
                    return False, migration_rate
        
        # Phase 5-7: 最終検証・承認
        final_passed, final_rate, final_issues = self.phase4_smart_verification(total_expected)
        
        if final_passed:
            logger.info("🎉 Smart Elder Loop Complete Migration 成功！")
            logger.info(f"📊 最終移行率: {final_rate:.1f}%")
            return True, final_rate
        else:
            logger.error("🚨 Smart Elder Loop Complete Migration 失敗")
            return False, final_rate

def main():
    """メイン実行"""
    migrator = SmartElderLoopMigrator()
    
    print("🧠 Smart Elder Loop Complete Migration System")
    print("============================================")
    print("🎯 賢い内容分析による真のElder Tree移行")
    print("📊 品質基準95%以上達成必須")
    print("")
    
    # Smart Elder Loop実行
    success, final_rate = migrator.execute_smart_elder_loop()
    
    if success:
        print(f"\n🎉 Smart Elder Loop Complete Migration 成功！")
        print(f"📊 最終移行率: {final_rate:.1f}%")
        print("✅ 賢い分析による適切なファイル配置完了")
        print("✅ Elder Tree 品質基準達成")
    else:
        print(f"\n🚨 Smart Elder Loop Complete Migration 失敗")
        print(f"📊 最終移行率: {final_rate:.1f}%")
        print("❌ 品質基準未達成")

if __name__ == "__main__":
    main()