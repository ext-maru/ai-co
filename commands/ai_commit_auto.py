#!/usr/bin/env python3
"""
Elders Guild Auto Commit Command
最適なプロトコルを自動選択する統合コミットシステム

使用方法:
  ai-commit-auto "機能追加: 新しいAPI"
  ai-commit-auto "緊急修正: セキュリティ脆弱性" --analyze
  ai-commit-auto "リファクタリング: コード整理" --force-layer council

設計: クロードエルダー
実装: エルダーズ・ハーモニー・システム 統合版
"""

import sys
import asyncio
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.elders_harmony_system import (
    LightningCommitSystem, 
    CommitUrgency, 
    DevelopmentLayer,
    SageConsultationResult
)
from commands.ai_commit_lightning import LightningCommitCLI
from commands.ai_commit_council import CouncilCommitCLI
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutoCommitCLI:
    """Auto Commit 統合コマンドラインインターフェース"""
    
    def __init__(self):
        self.lightning_system = LightningCommitSystem()
        self.lightning_cli = LightningCommitCLI()
        self.council_cli = CouncilCommitCLI()
        self.project_root = Path("/home/aicompany/ai_co")
    
    def analyze_commit_context(self, message: str, args) -> Dict:
        """コミットコンテキストの詳細分析"""
        git_changes = self.lightning_cli.get_git_changes()
        
        # メッセージから緊急度を推定
        urgency_keywords = {
            CommitUrgency.EMERGENCY: ['緊急', 'emergency', 'hotfix', 'critical', '停止', '障害'],
            CommitUrgency.HIGH: ['重要', 'important', 'urgent', 'fix', 'bug', '修正'],
            CommitUrgency.NORMAL: ['feat', 'feature', '機能', 'add', '追加'],
            CommitUrgency.LOW: ['docs', 'doc', 'readme', 'comment', 'test', 'refactor']
        }
        
        detected_urgency = CommitUrgency.NORMAL
        for urgency, keywords in urgency_keywords.items():
            if any(keyword in message.lower() for keyword in keywords):
                detected_urgency = urgency
                break
        
        # args から緊急度を上書き
        if args.emergency:
            detected_urgency = CommitUrgency.EMERGENCY
        elif args.high_priority:
            detected_urgency = CommitUrgency.HIGH
        
        # 複雑度分析
        all_files = git_changes["staged"] + (args.files if args.files else [])
        complexity = self.lightning_cli.analyze_complexity(all_files)
        
        return {
            "urgency": detected_urgency,
            "files": all_files,
            "complexity": complexity,
            "description": message,
            "git_changes": git_changes,
            "message_analysis": {
                "keywords_found": [kw for urgency, keywords in urgency_keywords.items() 
                                 for kw in keywords if kw in message.lower()],
                "estimated_urgency": detected_urgency.value
            }
        }
    
    def recommend_optimal_layer(self, context: Dict) -> tuple:
        """最適なレイヤーを推奨・理由付きで返す"""
        urgency = context["urgency"]
        file_count = len(context["files"])
        complexity = context["complexity"]
        
        reasons = []
        
        # Lightning Protocol判定
        if urgency == CommitUrgency.EMERGENCY:
            if file_count <= 5 and complexity <= 0.5:
                reasons.append("🚨 緊急事態のため Lightning Protocol が最適")
                reasons.append(f"📁 ファイル数: {file_count} (≤5)")
                reasons.append(f"🎯 複雑度: {complexity:.2f} (≤0.5)")
                return DevelopmentLayer.LIGHTNING, reasons
            else:
                reasons.append("🚨 緊急事態だが Lightning 条件を超過")
                reasons.append(f"📁 ファイル数: {file_count} (>5)" if file_count > 5 else "")
                reasons.append(f"🎯 複雑度: {complexity:.2f} (>0.5)" if complexity > 0.5 else "")
        
        elif urgency == CommitUrgency.HIGH:
            if file_count <= 3 and complexity <= 0.3:
                reasons.append("🔥 高優先度で Lightning Protocol が適用可能")
                reasons.append(f"📁 ファイル数: {file_count} (≤3)")
                reasons.append(f"🎯 複雑度: {complexity:.2f} (≤0.3)")
                return DevelopmentLayer.LIGHTNING, reasons
        
        # Grand Protocol判定
        if complexity > 0.8 or file_count > 20:
            reasons.append("👑 Grand Protocol が必要な大規模変更")
            if complexity > 0.8:
                reasons.append(f"🎯 高複雑度: {complexity:.2f} (>0.8)")
            if file_count > 20:
                reasons.append(f"📁 大量ファイル: {file_count} (>20)")
            return DevelopmentLayer.GRAND, reasons
        
        # Council Protocol（標準）
        reasons.append("🏛️ Council Protocol が最適（標準開発）")
        reasons.append(f"📁 ファイル数: {file_count} (3-20)")
        reasons.append(f"🎯 複雑度: {complexity:.2f} (0.3-0.8)")
        reasons.append(f"🚀 緊急度: {urgency.value}")
        
        return DevelopmentLayer.COUNCIL, reasons
    
    def display_analysis_report(self, context: Dict, recommended_layer: DevelopmentLayer, reasons: List[str]):
        """詳細分析レポートを表示"""
        print("\n📊 Elders Guild Auto Commit Analysis Report")
        print("=" * 60)
        
        # 基本情報
        print(f"💬 メッセージ: {context['description']}")
        print(f"📁 変更ファイル: {len(context['files'])}個")
        print(f"🎯 複雑度: {context['complexity']:.2f}")
        print(f"🚀 緊急度: {context['urgency'].value}")
        
        # メッセージ分析
        if context['message_analysis']['keywords_found']:
            print(f"🔍 検出キーワード: {', '.join(context['message_analysis']['keywords_found'])}")
        
        # 推奨レイヤー
        layer_icons = {
            DevelopmentLayer.LIGHTNING: "⚡",
            DevelopmentLayer.COUNCIL: "🏛️", 
            DevelopmentLayer.GRAND: "👑"
        }
        
        print(f"\n{layer_icons[recommended_layer]} 推奨プロトコル: {recommended_layer.value.upper()}")
        print("\n📋 推奨理由:")
        for reason in reasons:
            if reason:  # 空文字列をスキップ
                print(f"  {reason}")
        
        print("\n" + "=" * 60)
    
    async def execute_auto_commit(self, message: str, args) -> bool:
        """Auto Commit 自動実行"""
        print("🤖 Elders Guild Auto Commit 開始...")
        print("🔍 最適なプロトコルを自動選択中...")
        
        try:
            # 1. コンテキスト分析
            context = self.analyze_commit_context(message, args)
            
            # 2. 最適レイヤー推奨
            recommended_layer, reasons = self.recommend_optimal_layer(context)
            
            # 3. 強制レイヤー指定チェック
            if args.force_layer:
                force_layer = DevelopmentLayer(args.force_layer)
                print(f"⚠️ 強制レイヤー指定: {force_layer.value}")
                recommended_layer = force_layer
                reasons = [f"🔧 ユーザーが {force_layer.value} を強制指定"]
            
            # 4. 分析レポート表示
            if args.analyze:
                self.display_analysis_report(context, recommended_layer, reasons)
                return True
            
            # 5. 選択されたプロトコルで実行
            print(f"\n{self.get_layer_icon(recommended_layer)} {recommended_layer.value.upper()} Protocol 選択")
            
            if recommended_layer == DevelopmentLayer.LIGHTNING:
                return await self.lightning_cli.execute_lightning_commit(message, args)
            elif recommended_layer == DevelopmentLayer.COUNCIL:
                return await self.council_cli.execute_council_commit(message, args)
            elif recommended_layer == DevelopmentLayer.GRAND:
                from commands.ai_commit_grand import GrandCommitCLI
                grand_cli = GrandCommitCLI()
                return await grand_cli.execute_grand_commit(message, args)
            
            return False
            
        except Exception as e:
            print(f"💥 Auto Commit エラー: {e}")
            return False
    
    def get_layer_icon(self, layer: DevelopmentLayer) -> str:
        """レイヤーアイコンを取得"""
        icons = {
            DevelopmentLayer.LIGHTNING: "⚡",
            DevelopmentLayer.COUNCIL: "🏛️",
            DevelopmentLayer.GRAND: "👑"
        }
        return icons.get(layer, "🤖")

def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(
        description="Elders Guild Auto Commit - 最適プロトコル自動選択",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  ai-commit-auto "機能追加: 新しいAPI"
  ai-commit-auto "緊急修正: セキュリティ脆弱性" --emergency
  ai-commit-auto "リファクタリング: コード整理" --analyze
  ai-commit-auto "実験: 新機能テスト" --force-layer lightning

🤖 自動プロトコル選択ルール:
  ⚡ Lightning: 緊急度 HIGH/EMERGENCY + 低複雑度
  🏛️ Council: 標準開発 (最も一般的)
  👑 Grand: 大規模変更 (20ファイル以上、高複雑度)
        """
    )
    
    parser.add_argument(
        "message",
        help="コミットメッセージ"
    )
    
    parser.add_argument(
        "--emergency",
        action="store_true",
        help="緊急対応フラグ"
    )
    
    parser.add_argument(
        "--high-priority",
        action="store_true", 
        help="高優先度フラグ"
    )
    
    parser.add_argument(
        "--files",
        nargs="+",
        help="特定ファイルのみコミット"
    )
    
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="分析のみ実行（実際のコミットは行わない）"
    )
    
    parser.add_argument(
        "--force-layer",
        choices=["lightning", "council", "grand"],
        help="プロトコルを強制指定"
    )
    
    args = parser.parse_args()
    
    # バナー表示
    print("🤖" * 50)
    print("🚀  Elders Guild Auto Commit System")
    print("🧠  Intelligent Protocol Selection")
    print("⚡  Lightning • 🏛️ Council • 👑 Grand")
    print("🤖" * 50)
    
    # Auto CLI実行
    cli = AutoCommitCLI()
    
    # 実際の実行
    try:
        success = asyncio.run(cli.execute_auto_commit(args.message, args))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Auto Commit 中断")
        sys.exit(1)
    except Exception as e:
        print(f"💥 予期しないエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()