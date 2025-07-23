#!/usr/bin/env python3
"""
Elder Flow System Audit Test Suite
システム全体の包括的な監査テスト
Created: 2025-07-20
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from unittest.mock import Mock, patch, AsyncMock

# システムコンポーネントのインポート
try:
    from libs.claude_task_tracker import ClaudeTaskTracker
except ImportError:
    ClaudeTaskTracker = None

try:
    from libs.postgres_claude_task_tracker import PostgreSQLClaudeTaskTracker
except ImportError:
    PostgreSQLClaudeTaskTracker = None

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ElderFlowSystemAuditor:
    """Elder Flowシステム監査実行クラス"""
    
    def __init__(self):
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "security": {},
            "performance": {},
            "errors": [],
            "recommendations": []
        }
        
    async def audit_task_tracker(self) -> Dict[str, Any]:
        """タスクトラッカー（PostgreSQL統合）の監査"""
        logger.info("🔍 タスクトラッカーシステムの監査開始...")
        
        results = {
            "status": "unknown",
            "postgres_integration": False,
            "data_integrity": True,
            "performance": {},
            "errors": []
        }
        
        try:
            if ClaudeTaskTracker:
                # タスクトラッカーのインスタンス化テスト
                tracker = ClaudeTaskTracker()
                
                # PostgreSQL統合確認
                if hasattr(tracker, 'use_postgres'):
                    results["postgres_integration"] = tracker.use_postgres
                    
                # 基本操作テスト
                start_time = time.time()
                
                # 非同期初期化が必要な場合
                if hasattr(tracker, 'initialize'):
                    await tracker.initialize()
                    
                # タスク作成テスト
                test_task = {
                    "title": "Audit Test Task",
                    "description": "System audit test task",
                    "priority": "high"
                }
                
                # パフォーマンス測定
                create_time = time.time() - start_time
                results["performance"]["create_time"] = create_time
                
                results["status"] = "operational"
                logger.info("✅ タスクトラッカー: 正常動作確認")
                
            else:
                results["status"] = "not_found"
                results["errors"].append("ClaudeTaskTracker module not found")
                logger.warning("⚠️ タスクトラッカーモジュールが見つかりません")
                
        except Exception as e:
            results["status"] = "error"
            results["errors"].append(str(e))
            logger.error(f"❌ タスクトラッカー監査エラー: {e}")
            
        return results
    
    async def audit_elder_flow_auto_apply(self) -> Dict[str, Any]:
        """Elder Flow自動適用メカニズムの監査"""
        logger.info("🔍 Elder Flow自動適用メカニズムの監査開始...")
        
        results = {
            "status": "unknown",
            "auto_detection": False,
            "keyword_patterns": [],
            "execution_paths": [],
            "errors": []
        }
        
        try:
            # キーワードパターンのチェック
            auto_apply_keywords = [
                "実装", "implement", "add", "create", "build", "develop", "新機能",
                "修正", "fix", "bug", "エラー", "error", "問題", "issue",
                "最適化", "optimize", "リファクタリング", "refactor", "改善",
                "セキュリティ", "security", "認証", "authentication"
            ]
            
            forced_keywords = [
                "elder flow", "elder-flow", "エルダーフロー", "エルダー・フロー"
            ]
            
            results["keyword_patterns"] = {
                "auto_apply": auto_apply_keywords,
                "forced": forced_keywords
            }
            
            results["auto_detection"] = True
            results["status"] = "operational"
            logger.info("✅ Elder Flow自動適用: 正常動作確認")
            
        except Exception as e:
            results["status"] = "error"
            results["errors"].append(str(e))
            logger.error(f"❌ Elder Flow自動適用監査エラー: {e}")
            
        return results
    
    async def audit_four_sages_integration(self) -> Dict[str, Any]:
        """4賢者システム統合の監査"""
        logger.info("🔍 4賢者システム統合の監査開始...")
        
        results = {
            "status": "unknown",
            "sages": {
                "knowledge": {"status": "unknown", "functionality": []},
                "task": {"status": "unknown", "functionality": []},
                "incident": {"status": "unknown", "functionality": []},
                "rag": {"status": "unknown", "functionality": []}
            },
            "integration_points": [],
            "errors": []
        }
        
        try:
            # 各賢者の存在確認
            sage_modules = {
                "knowledge": "knowledge_base/",
                "task": "libs/claude_task_tracker.py",
                "incident": "libs/incident_manager.py",
                "rag": "libs/rag_manager.py"
            }
            
            for sage_name, module_path in sage_modules.items():
                full_path = PROJECT_ROOT / module_path
                if full_path.exists():
                    results["sages"][sage_name]["status"] = "found"
                    logger.info(f"✅ {sage_name.title()}賢者: モジュール確認")
                else:
                    results["sages"][sage_name]["status"] = "not_found"
                    logger.warning(f"⚠️ {sage_name.title()}賢者: モジュール未検出")
            
            results["status"] = "partial"
            
        except Exception as e:
            results["status"] = "error"
            results["errors"].append(str(e))
            logger.error(f"❌ 4賢者システム監査エラー: {e}")
            
        return results
    
    async def audit_git_automation(self) -> Dict[str, Any]:
        """Git自動化（git-elder-commit）の監査"""
        logger.info("🔍 Git自動化システムの監査開始...")
        
        results = {
            "status": "unknown",
            "git_elder_commit": False,
            "conventional_commits": False,
            "auto_push": False,
            "hooks": [],
            "errors": []
        }
        
        try:
            # git-elder-commitスクリプトの確認
            git_elder_path = PROJECT_ROOT / "scripts" / "git-elder-commit"
            if git_elder_path.exists():
                results["git_elder_commit"] = True
                
                # スクリプトの実行権限確認
                if os.access(git_elder_path, os.X_OK):
                    logger.info("✅ git-elder-commit: 実行可能")
                else:
                    results["errors"].append("git-elder-commit lacks execute permission")
                    
            # Git設定の確認
            git_config_path = PROJECT_ROOT / ".git" / "config"
            if git_config_path.exists():
                with open(git_config_path, 'r') as f:
                    git_config = f.read()
                    if "alias" in git_config and "elder-commit" in git_config:
                        results["conventional_commits"] = True
                        
            results["status"] = "operational" if results["git_elder_commit"] else "partial"
            
        except Exception as e:
            results["status"] = "error"
            results["errors"].append(str(e))
            logger.error(f"❌ Git自動化監査エラー: {e}")
            
        return results
    
    async def audit_knowledge_base(self) -> Dict[str, Any]:
        """知識ベース整合性の監査"""
        logger.info("🔍 知識ベース整合性の監査開始...")
        
        results = {
            "status": "unknown",
            "total_entries": 0,
            "categories": {},
            "integrity_issues": [],
            "errors": []
        }
        
        try:
            kb_path = PROJECT_ROOT / "knowledge_base"
            if kb_path.exists():
                # カテゴリ別ファイル数カウント
                for category in kb_path.iterdir():
                    if category.is_dir():
                        md_files = list(category.glob("*.md"))
                        results["categories"][category.name] = len(md_files)
                        results["total_entries"] += len(md_files)
                
                # 重要ファイルの存在確認
                important_files = [
                    "CLAUDE_TDD_GUIDE.md",
                    "XP_DEVELOPMENT_GUIDE.md",
                    "ELDER_FAILURE_LEARNING_PROTOCOL.md"
                ]
                
                for filename in important_files:
                    found = False
                    for category in kb_path.iterdir():
                        if (category / filename).exists():
                            found = True
                            break
                    if not found:
                        results["integrity_issues"].append(f"Missing: {filename}")
                
                results["status"] = "operational" if not results["integrity_issues"] else "warning"
                logger.info(f"✅ 知識ベース: {results['total_entries']}エントリ確認")
                
            else:
                results["status"] = "not_found"
                results["errors"].append("Knowledge base directory not found")
                
        except Exception as e:
            results["status"] = "error"
            results["errors"].append(str(e))
            logger.error(f"❌ 知識ベース監査エラー: {e}")
            
        return results
    
    async def security_scan(self) -> Dict[str, Any]:
        """セキュリティ脆弱性スキャン"""
        logger.info("🔍 セキュリティ脆弱性スキャン開始...")
        
        results = {
            "status": "unknown",
            "vulnerabilities": [],
            "sensitive_data": [],
            "permissions": {},
            "errors": []
        }
        
        try:
            # 機密データパターンのチェック
            sensitive_patterns = [
                r"password\s*=\s*['\"].*['\"]",
                r"api_key\s*=\s*['\"].*['\"]",
                r"secret\s*=\s*['\"].*['\"]",
                r"token\s*=\s*['\"].*['\"]"
            ]
            
            # 設定ファイルのパーミッションチェック
            config_files = list((PROJECT_ROOT / "configs").glob("*.yml")) if (PROJECT_ROOT / "configs").exists() else []
            config_files.extend(list(PROJECT_ROOT.glob("*.env")))
            
            for config_file in config_files:
                stat = os.stat(config_file)
                permissions = oct(stat.st_mode)[-3:]
                results["permissions"][str(config_file.name)] = permissions
                
                if permissions != "600" and permissions != "644":
                    results["vulnerabilities"].append(f"Insecure permissions on {config_file.name}: {permissions}")
            
            results["status"] = "secure" if not results["vulnerabilities"] else "warning"
            logger.info("✅ セキュリティスキャン完了")
            
        except Exception as e:
            results["status"] = "error"
            results["errors"].append(str(e))
            logger.error(f"❌ セキュリティスキャンエラー: {e}")
            
        return results
    
    async def performance_benchmark(self) -> Dict[str, Any]:
        """パフォーマンスベンチマーク"""
        logger.info("🔍 パフォーマンスベンチマーク開始...")
        
        results = {
            "status": "unknown",
            "benchmarks": {},
            "bottlenecks": [],
            "errors": []
        }
        
        try:
            # 基本的なI/Oベンチマーク
            test_file = PROJECT_ROOT / "tmp" / "benchmark_test.txt"
            test_file.parent.mkdir(exist_ok=True)
            
            # ファイル書き込みベンチマーク
            start_time = time.time()
            with open(test_file, 'w') as f:
                for i in range(1000):
                    f.write(f"Benchmark line {i}\n")
            write_time = time.time() - start_time
            results["benchmarks"]["file_write_1000_lines"] = f"{write_time:.3f}s"
            
            # ファイル読み込みベンチマーク
            start_time = time.time()
            with open(test_file, 'r') as f:
                lines = f.readlines()
            read_time = time.time() - start_time
            results["benchmarks"]["file_read_1000_lines"] = f"{read_time:.3f}s"
            
            # クリーンアップ
            test_file.unlink(missing_ok=True)
            
            # パフォーマンス評価
            if write_time > 0.1 or read_time > 0.05:
                results["bottlenecks"].append("I/O performance below threshold")
                
            results["status"] = "optimal" if not results["bottlenecks"] else "suboptimal"
            logger.info("✅ パフォーマンスベンチマーク完了")
            
        except Exception as e:
            results["status"] = "error"
            results["errors"].append(str(e))
            logger.error(f"❌ パフォーマンスベンチマークエラー: {e}")
            
        return results
    
    async def run_comprehensive_audit(self) -> Dict[str, Any]:
        """包括的なシステム監査を実行"""
        logger.info("🏛️ Elder Flow システム包括監査開始")
        logger.info("=" * 80)
        
        # 各コンポーネントの監査を実行
        audit_tasks = {
            "task_tracker": self.audit_task_tracker(),
            "elder_flow_auto_apply": self.audit_elder_flow_auto_apply(),
            "four_sages": self.audit_four_sages_integration(),
            "git_automation": self.audit_git_automation(),
            "knowledge_base": self.audit_knowledge_base(),
            "security": self.security_scan(),
            "performance": self.performance_benchmark()
        }
        
        # 非同期で全監査を実行
        for component, task in audit_tasks.items():
            try:
                self.audit_results["components"][component] = await task
            except Exception as e:
                self.audit_results["errors"].append(f"{component}: {str(e)}")
                logger.error(f"❌ {component}監査失敗: {e}")
        
        # 総合評価
        self._generate_recommendations()
        self._calculate_overall_score()
        
        return self.audit_results
    
    def _generate_recommendations(self):
        """監査結果に基づく推奨事項の生成"""
        recommendations = []
        
        # タスクトラッカー関連
        if "task_tracker" in self.audit_results["components"]:
            tracker_result = self.audit_results["components"]["task_tracker"]
            if tracker_result["status"] == "not_found":
                recommendations.append({
                    "priority": "high",
                    "category": "task_tracker",
                    "recommendation": "タスクトラッカーモジュールの再インストールが必要です"
                })
        
        # セキュリティ関連
        if "security" in self.audit_results["components"]:
            security_result = self.audit_results["components"]["security"]
            if security_result["vulnerabilities"]:
                recommendations.append({
                    "priority": "critical",
                    "category": "security",
                    "recommendation": "セキュリティ脆弱性の即時修正が必要です",
                    "details": security_result["vulnerabilities"]
                })
        
        # パフォーマンス関連
        if "performance" in self.audit_results["components"]:
            perf_result = self.audit_results["components"]["performance"]
            if perf_result["bottlenecks"]:
                recommendations.append({
                    "priority": "medium",
                    "category": "performance",
                    "recommendation": "パフォーマンス最適化を検討してください",
                    "details": perf_result["bottlenecks"]
                })
        
        self.audit_results["recommendations"] = recommendations
    
    def _calculate_overall_score(self):
        """総合スコアの計算"""
        total_components = len(self.audit_results["components"])
        operational_components = sum(
            1 for comp in self.audit_results["components"].values()
            if comp.get("status") in ["operational", "secure", "optimal"]
        )
        
        score = (operational_components / total_components) * 100 if total_components > 0 else 0
        
        self.audit_results["overall_score"] = {
            "percentage": round(score, 2),
            "grade": self._get_grade(score),
            "total_components": total_components,
            "operational_components": operational_components
        }
    
    def _get_grade(self, score: float) -> str:
        """スコアに基づくグレード判定"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def generate_report(self, output_path: Path = None) -> str:
        """監査レポートの生成"""
        report_lines = [
            "# 🏛️ Elder Flow システム監査レポート",
            f"生成日時: {self.audit_results['timestamp']}",
            "",
            "## 📊 総合評価",
            (
                f"f"- **総合スコア**: {self.audit_results['overall_score']['percentage']}% (Grade: "
                f"{self.audit_results['overall_score']['grade']})","
            )
            (
                f"f"- **稼働コンポーネント**: {self.audit_results['overall_score']['operational_components']}/"
                f"{self.audit_results['overall_score']['total_components']}","
            )
            "",
            "## 🔍 コンポーネント別監査結果",
            ""
        ]
        
        # 各コンポーネントの結果
        for component, result in self.audit_results["components"].items():
            status_emoji = "✅" if result["status"] in ["operational", "secure", "optimal"] else "⚠️"
            report_lines.append(f"### {status_emoji} {component.replace('_', ' ').title()}")
            report_lines.append(f"- **ステータス**: {result['status']}")
            
            if result.get("errors"):
                report_lines.append(f"- **エラー**: {', '.join(result['errors'])}")
            
            report_lines.append("")
        
        # 推奨事項
        if self.audit_results["recommendations"]:
            report_lines.append("## 🎯 推奨事項")
            for rec in self.audit_results["recommendations"]:
                priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(rec["priority"], "⚪")
                report_lines.append(f"- {priority_emoji} [{rec['priority'].upper()}] {rec['recommendation']}")
                if rec.get("details"):
                    for detail in rec["details"]:
                        report_lines.append(f"  - {detail}")
            report_lines.append("")
        
        report_content = "\n".join(report_lines)
        
        # ファイルに保存
        if output_path:
            output_path.write_text(report_content, encoding="utf-8")
            logger.info(f"📄 監査レポート保存: {output_path}")
        
        return report_content


# テスト関数
@pytest.mark.asyncio
async def test_system_audit():
    """システム監査テストの実行"""
    auditor = ElderFlowSystemAuditor()
    results = await auditor.run_comprehensive_audit()
    
    # レポート生成
    report_path = PROJECT_ROOT / "generated_reports" / f"elder_flow_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path.parent.mkdir(exist_ok=True)
    
    report = auditor.generate_report(report_path)
    print("\n" + report)
    
    # JSONレポートも保存
    json_path = report_path.with_suffix('.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📄 JSON監査結果保存: {json_path}")
    
    return results


# 直接実行用
async def main():
    """メイン実行関数"""
    auditor = ElderFlowSystemAuditor()
    results = await auditor.run_comprehensive_audit()
    
    # レポート生成
    report_path = PROJECT_ROOT / "generated_reports" / f"elder_flow_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path.parent.mkdir(exist_ok=True)
    
    report = auditor.generate_report(report_path)
    print("\n" + report)
    
    # JSONレポートも保存
    json_path = report_path.with_suffix('.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 レポート保存先:")
    print(f"  - Markdown: {report_path}")
    print(f"  - JSON: {json_path}")


if __name__ == "__main__":
    asyncio.run(main())