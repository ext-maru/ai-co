#!/usr/bin/env python3
"""
Elders Guild Grand Commit Command
至高の品質を追求する最高位コミットプロトコル

Grand Protocol の特徴:
- 4賢者全員の詳細レビュー（時間制限なし）
- 多段階承認プロセス
- 包括的影響分析
- エルダー評議会への自動報告

使用場面:
- アーキテクチャ変更
- 破壊的変更
- セキュリティ関連変更
- 20ファイル以上の大規模変更

設計: クロードエルダー
承認: エルダーズ評議会
実装日: 2025年7月9日
"""

import sys
import asyncio
import argparse
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.elders_harmony_system import (
    SagesHarmonyEngine,
    CommitUrgency,
    DevelopmentLayer,
    HarmonyDecision
)
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GrandCommitCLI:
    """Grand Commit コマンドラインインターフェース"""
    
    def __init__(self):
        self.harmony_engine = SagesHarmonyEngine()
        self.project_root = Path("/home/aicompany/ai_co")
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
    def get_git_changes(self) -> Dict:
        """Git変更状況を取得"""
        try:
            # ステージングされたファイル
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True, text=True, cwd=self.project_root
            )
            staged_files = [f for f in result.stdout.strip().split('\n') if f]
            
            # 未ステージングのファイル
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True, text=True, cwd=self.project_root
            )
            unstaged_files = [f for f in result.stdout.strip().split('\n') if f]
            
            # 未追跡ファイル
            result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True, text=True, cwd=self.project_root
            )
            untracked_files = [f for f in result.stdout.strip().split('\n') if f]
            
            total_files = len(set(staged_files + unstaged_files + untracked_files))
            
            return {
                "staged": staged_files,
                "unstaged": unstaged_files,
                "untracked": untracked_files,
                "total_files": total_files
            }
            
        except Exception as e:
            logger.error(f"Git状態取得エラー: {e}")
            return {
                "staged": [],
                "unstaged": [],
                "untracked": [],
                "total_files": 0
            }
    
    def analyze_change_impact(self, files: List[str]) -> Dict:
        """変更の影響度を分析"""
        impact = {
            "security_impact": False,
            "architecture_impact": False,
            "breaking_changes": False,
            "affected_modules": set(),
            "risk_level": "LOW"
        }
        
        for file in files:
            # セキュリティ関連ファイル
            if any(keyword in file.lower() for keyword in ['security', 'auth', 'crypto', 'password']):
                impact["security_impact"] = True
            
            # アーキテクチャ関連ファイル
            if any(keyword in file.lower() for keyword in ['core/', 'libs/', 'config', 'architecture']):
                impact["architecture_impact"] = True
            
            # 破壊的変更の可能性
            if any(keyword in file.lower() for keyword in ['api/', 'interface', 'protocol']):
                impact["breaking_changes"] = True
            
            # 影響モジュールの追跡
            if '/' in file:
                module = file.split('/')[0]
                impact["affected_modules"].add(module)
        
        # リスクレベル判定
        risk_score = 0
        if impact["security_impact"]:
            risk_score += 3
        if impact["architecture_impact"]:
            risk_score += 2
        if impact["breaking_changes"]:
            risk_score += 2
        if len(impact["affected_modules"]) > 5:
            risk_score += 1
        
        if risk_score >= 5:
            impact["risk_level"] = "HIGH"
        elif risk_score >= 3:
            impact["risk_level"] = "MEDIUM"
        else:
            impact["risk_level"] = "LOW"
        
        impact["affected_modules"] = list(impact["affected_modules"])
        return impact
    
    def display_grand_banner(self):
        """Grand Protocol バナー表示"""
        print("👑" * 50)
        print("✨  Grand Protocol - 至高の品質追求  ✨")
        print("👑  時間制限なし・完全レビュー・多段階承認  👑")
        print("👑" * 50)
        print()
    
    def display_change_analysis(self, git_changes: Dict, impact: Dict):
        """変更分析結果を表示"""
        print("📊 変更分析結果")
        print("=" * 60)
        
        print(f"📁 変更ファイル数: {git_changes['total_files']}")
        print(f"  ✅ ステージング済み: {len(git_changes['staged'])}")
        print(f"  📝 未ステージング: {len(git_changes['unstaged'])}")
        print(f"  🆕 新規ファイル: {len(git_changes['untracked'])}")
        print()
        
        print("🎯 影響度分析:")
        print(f"  🔐 セキュリティ影響: {'あり' if impact['security_impact'] else 'なし'}")
        print(f"  🏗️ アーキテクチャ影響: {'あり' if impact['architecture_impact'] else 'なし'}")
        print(f"  💥 破壊的変更: {'あり' if impact['breaking_changes'] else 'なし'}")
        print(f"  📦 影響モジュール: {', '.join(impact['affected_modules']) if impact['affected_modules'] else 'なし'}")
        print(f"  ⚠️ リスクレベル: {impact['risk_level']}")
        print()
    
    async def execute_grand_commit(self, message: str, args) -> bool:
        """Grand Protocol 実行"""
        start_time = time.time()
        
        self.display_grand_banner()
        
        try:
            # 1. Git状態確認
            print("🔍 Git状態を確認中...")
            git_changes = self.get_git_changes()
            
            if git_changes['total_files'] == 0:
                print("⚠️ 変更されたファイルがありません")
                return False
            
            # 2. 影響度分析
            all_files = git_changes['staged'] + git_changes['unstaged'] + git_changes['untracked']
            impact = self.analyze_change_impact(all_files)
            
            self.display_change_analysis(git_changes, impact)
            
            # 3. Grand Protocol 実行確認
            print("👑 Grand Protocol を実行しますか？")
            print("   • 4賢者全員による詳細レビュー")
            print("   • 多段階承認プロセス")
            print("   • 時間制限なし（完了まで待機）")
            print()
            
            confirm = input("実行しますか？ (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Grand Protocol 中止")
                return False
            
            # 4. コンテキスト準備
            context = {
                "urgency": CommitUrgency.LOW,  # Grandは急がない
                "files": all_files,
                "complexity": 0.9,  # Grand は高複雑度想定
                "description": message,
                "git_changes": git_changes,
                "impact_analysis": impact
            }
            
            # 5. ファイルステージング
            if args.files:
                self.stage_specific_files(args.files)
            else:
                self.stage_all_changes(git_changes)
            
            # 6. Grand Protocol 4賢者相談（詳細版）
            print("\n🧙‍♂️ 4賢者による詳細レビュー開始...")
            print("   時間制限なし - 完全な品質保証を優先\n")
            
            sage_results = await self.harmony_engine.grand_consultation(context)
            
            # 7. 各賢者の詳細結果表示
            self.display_sage_consultations(sage_results)
            
            # 8. 多段階承認プロセス
            print("\n🏛️ 多段階承認プロセス")
            print("=" * 60)
            
            # 第1段階: 賢者承認
            sage_decision = self.evaluate_sage_decision(sage_results)
            print(f"✅ 第1段階 - 賢者承認: {sage_decision['status']}")
            print(f"   承認数: {sage_decision['approvals']}/4")
            
            if not sage_decision['approved']:
                print("❌ 賢者承認が得られませんでした")
                self.save_rejection_report(context, sage_results, sage_decision)
                return False
            
            # 第2段階: リスク評価
            risk_decision = self.evaluate_risk_level(sage_results, impact)
            print(f"✅ 第2段階 - リスク評価: {risk_decision['status']}")
            print(f"   総合リスクスコア: {risk_decision['total_risk']:.2f}")
            
            if not risk_decision['approved']:
                print("❌ リスクレベルが高すぎます")
                self.save_rejection_report(context, sage_results, risk_decision)
                return False
            
            # 第3段階: 最終承認
            print("✅ 第3段階 - 最終承認: 承認")
            
            # 9. コミット実行
            print(f"\n🚀 Grand Protocol コミット実行中...")
            success = self._execute_git_commit(message)
            
            if success:
                elapsed = time.time() - start_time
                print(f"\n✅ Grand Protocol 完了!")
                print(f"⏱️ 総実行時間: {elapsed:.1f}秒")
                
                # 10. エルダー評議会への報告
                await self.report_to_elder_council(context, sage_results, elapsed)
                
                # 11. Grand レポート保存
                await self.save_grand_report(context, sage_results, elapsed)
                
                return True
            else:
                print("❌ コミット実行に失敗しました")
                return False
                
        except Exception as e:
            logger.error(f"Grand Protocol エラー: {e}")
            print(f"💥 予期しないエラーが発生しました: {e}")
            return False
    
    def display_sage_consultations(self, sage_results):
        """賢者相談結果の詳細表示"""
        for i, result in enumerate(sage_results, 1):
            print(f"\n🧙‍♂️ {result.sage_name} (相談 {i}/4)")
            print("-" * 40)
            print(f"📊 判定: {'✅ 承認' if result.approval else '❌ 却下'}")
            print(f"⚠️ リスクスコア: {result.risk_score:.2f}")
            print(f"💡 助言: {result.advice}")
    
    def evaluate_sage_decision(self, sage_results) -> Dict:
        """賢者の決定を評価"""
        approvals = sum(1 for r in sage_results if r.approval)
        total = len(sage_results)
        
        # Grand Protocol は全員一致が理想だが、3/4でも可
        approved = approvals >= 3
        
        status = "全員一致" if approvals == total else f"{approvals}/{total}承認"
        
        return {
            "approved": approved,
            "approvals": approvals,
            "total": total,
            "status": status
        }
    
    def evaluate_risk_level(self, sage_results, impact) -> Dict:
        """総合リスクレベルを評価"""
        # 賢者のリスクスコア平均
        sage_risk = sum(r.risk_score for r in sage_results) / len(sage_results)
        
        # 影響度によるリスク加算
        impact_risk = 0.0
        if impact["risk_level"] == "HIGH":
            impact_risk = 0.3
        elif impact["risk_level"] == "MEDIUM":
            impact_risk = 0.2
        elif impact["risk_level"] == "LOW":
            impact_risk = 0.1
        
        total_risk = sage_risk + impact_risk
        
        # Grand Protocol は厳格な基準（0.6以下）
        approved = total_risk <= 0.6
        
        status = "低リスク" if total_risk < 0.3 else "中リスク" if total_risk < 0.6 else "高リスク"
        
        return {
            "approved": approved,
            "total_risk": total_risk,
            "sage_risk": sage_risk,
            "impact_risk": impact_risk,
            "status": status
        }
    
    def stage_specific_files(self, files: List[str]):
        """特定ファイルをステージング"""
        for file in files:
            try:
                subprocess.run(
                    ["git", "add", file],
                    cwd=self.project_root,
                    check=True
                )
                print(f"✅ ステージング: {file}")
            except:
                print(f"⚠️ ステージング失敗: {file}")
    
    def stage_all_changes(self, git_changes: Dict):
        """すべての変更をステージング"""
        # 未追跡ファイルを追加
        for file in git_changes['untracked']:
            try:
                subprocess.run(
                    ["git", "add", file],
                    cwd=self.project_root,
                    check=True
                )
            except:
                pass
        
        # 変更ファイルを追加
        try:
            subprocess.run(
                ["git", "add", "-u"],
                cwd=self.project_root,
                check=True
            )
        except:
            pass
    
    def _execute_git_commit(self, message: str) -> bool:
        """Git コミット実行"""
        try:
            # Grand Protocol は pre-commit hooks を完全実行
            cmd = ["git", "commit", "-m", message]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                cwd=self.project_root,
                timeout=300  # 5分のタイムアウト
            )
            
            if result.returncode == 0:
                print("✅ コミット成功")
                return True
            else:
                print(f"❌ コミット失敗: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ コミットタイムアウト（5分超過）")
            return False
        except Exception as e:
            print(f"❌ コミットエラー: {e}")
            return False
    
    async def report_to_elder_council(self, context: Dict, sage_results: List, elapsed_time: float):
        """エルダー評議会への報告"""
        print("\n📜 エルダー評議会への報告書作成中...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "protocol": "Grand Protocol",
            "executor": "クロードエルダー",
            "message": context["description"],
            "execution_time": elapsed_time,
            "files_changed": len(context["files"]),
            "impact_analysis": context["impact_analysis"],
            "sage_consultations": [
                {
                    "sage": r.sage_name,
                    "approval": r.approval,
                    "risk_score": r.risk_score,
                    "advice": r.advice
                }
                for r in sage_results
            ],
            "status": "COMPLETED"
        }
        
        # 評議会報告ディレクトリ
        council_dir = self.project_root / "knowledge_base" / "elder_council_reports"
        council_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = council_dir / f"grand_protocol_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 評議会報告書保存: {report_file.name}")
    
    async def save_grand_report(self, context: Dict, sage_results: List, elapsed_time: float):
        """Grand Protocol レポート保存"""
        report = {
            "protocol": "Grand",
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "sage_consultations": [
                {
                    "sage": r.sage_name,
                    "approval": r.approval,
                    "risk_score": r.risk_score,
                    "advice": r.advice,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in sage_results
            ],
            "execution_time": elapsed_time,
            "status": "completed"
        }
        
        report_file = self.logs_dir / f"grand_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Grand レポート保存: {report_file}")
    
    def save_rejection_report(self, context: Dict, sage_results: List, decision: Dict):
        """却下レポート保存"""
        report = {
            "protocol": "Grand",
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "sage_consultations": [
                {
                    "sage": r.sage_name,
                    "approval": r.approval,
                    "risk_score": r.risk_score,
                    "advice": r.advice
                }
                for r in sage_results
            ],
            "rejection_reason": decision,
            "status": "rejected"
        }
        
        report_file = self.logs_dir / f"grand_rejection_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(
        description="Elders Guild Grand Commit - 至高の品質追求",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  ai-commit-grand "アーキテクチャ大規模変更"
  ai-commit-grand "セキュリティシステム刷新" --files security/*.py
  ai-commit-grand "API v2.0 破壊的変更" --skip-hooks

👑 Grand Protocol 使用基準:
  • 20ファイル以上の変更
  • アーキテクチャ変更
  • セキュリティ関連変更
  • 破壊的変更（Breaking Changes）
  • 重要な意思決定を伴う変更
        """
    )
    
    parser.add_argument(
        "message",
        help="コミットメッセージ"
    )
    
    parser.add_argument(
        "--files",
        nargs="+",
        help="特定ファイルのみコミット"
    )
    
    parser.add_argument(
        "--skip-hooks",
        action="store_true",
        help="pre-commit hooks をスキップ（非推奨）"
    )
    
    args = parser.parse_args()
    
    # Grand CLI実行
    cli = GrandCommitCLI()
    
    # 実際の実行
    try:
        success = asyncio.run(cli.execute_grand_commit(args.message, args))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Grand Protocol 中断")
        sys.exit(1)
    except Exception as e:
        print(f"💥 予期しないエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()