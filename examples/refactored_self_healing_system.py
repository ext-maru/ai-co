#!/usr/bin/env python3
"""
🏥 Refactored Self-Healing System - AI判定者パラダイム適用版
AIは判定のみ、実行は人間が承認後に行う
"""

import asyncio
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import psutil
import shutil

class HealthStatus(Enum):
    """システム健康状態"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class HealingRecommendation:
    """治癒推奨事項"""
    issue_type: str
    severity: HealthStatus
    description: str
    recommended_actions: List[str]
    reasoning: str
    estimated_impact: str
    requires_sudo: bool = False
    data_loss_risk: bool = False

class SelfHealingJudge:
    """
    🧠 AI判定者 - システム健康状態の判定と推奨のみ
    実行は一切行わない
    """
    
    def __init__(self):
        self.judgment_history = []
        self.feedback_data = []
    
    async def analyze_system_health(self) -> Dict:
        """システム健康状態の分析（読み取りのみ）"""
        health_metrics = {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "disk_space_gb": psutil.disk_usage('/').free / (1024**3),
            "process_count": len(psutil.pids()),
            "timestamp": datetime.now().isoformat()
        }
        
        # ログサイズ分析（読み取りのみ）
        log_analysis = await self._analyze_log_sizes()
        health_metrics["log_analysis"] = log_analysis
        
        return health_metrics
    
    async def generate_healing_recommendations(self, health_metrics: Dict) -> List[HealingRecommendation]:
        """
        健康状態から治癒推奨事項を生成
        判定と推奨のみ、実行はしない
        """
        recommendations = []
        
        # メモリ使用率の判定
        if health_metrics["memory_usage"] > 90:
            recommendations.append(HealingRecommendation(
                issue_type="high_memory_usage",
                severity=HealthStatus.CRITICAL,
                description="メモリ使用率が90%を超えています",
                recommended_actions=[
                    "大量メモリ使用プロセスの特定: ps aux --sort=-%mem | head",
                    "不要なプロセスの停止を検討",
                    "メモリリークの可能性を調査"
                ],
                reasoning="高メモリ使用はシステムパフォーマンスを著しく低下させます",
                estimated_impact="システム応答性の改善、OOMキラー回避",
                requires_sudo=False
            ))
        
        # ディスク容量の判定
        if health_metrics["disk_space_gb"] < 10:
            recommendations.append(HealingRecommendation(
                issue_type="low_disk_space",
                severity=HealthStatus.WARNING if health_metrics["disk_space_gb"] > 5 else HealthStatus.CRITICAL,
                description=f"ディスク空き容量が{health_metrics['disk_space_gb']:.1f}GBしかありません",
                recommended_actions=[
                    "大容量ファイルの確認: du -h / 2>/dev/null | sort -rh | head -20",
                    "古いログファイルの確認: find /var/log -type f -name '*.log' -mtime +30",
                    "不要なDockerイメージの確認: docker images"
                ],
                reasoning="ディスク容量不足はシステム動作に深刻な影響を与えます",
                estimated_impact="ディスク容量確保によるシステム安定性向上",
                requires_sudo=True,
                data_loss_risk=False
            ))
        
        # ログファイルサイズの判定
        if health_metrics["log_analysis"]["total_size_mb"] > 1000:
            recommendations.append(HealingRecommendation(
                issue_type="large_log_files",
                severity=HealthStatus.WARNING,
                description=f"ログファイル合計が{health_metrics['log_analysis']['total_size_mb']:.0f}MBあります",
                recommended_actions=[
                    "ログローテーション設定の確認",
                    f"最大ファイル: {health_metrics['log_analysis']['largest_file']}",
                    "古いログのアーカイブを検討"
                ],
                reasoning="大量のログファイルはディスク容量を圧迫し、パフォーマンスに影響します",
                estimated_impact="ディスク容量解放とI/O性能改善",
                requires_sudo=False,
                data_loss_risk=True  # ログ削除は情報損失リスクあり
            ))
        
        return recommendations
    
    async def _analyze_log_sizes(self) -> Dict:
        """ログサイズ分析（読み取りのみ）"""
        log_dirs = ["/var/log", "/tmp", "logs"]
        total_size = 0
        largest_file = ""
        largest_size = 0
        
        for log_dir in log_dirs:
            try:
                for root, dirs, files in os.walk(log_dir):
                    for file in files:
                        if file.endswith('.log'):
                            filepath = os.path.join(root, file)
                            try:
                                size = os.path.getsize(filepath)
                                total_size += size
                                if size > largest_size:
                                    largest_size = size
                                    largest_file = filepath
                            except:
                                pass
            except:
                pass
        
        return {
            "total_size_mb": total_size / (1024 * 1024),
            "largest_file": largest_file,
            "largest_size_mb": largest_size / (1024 * 1024)
        }
    
    def learn_from_feedback(self, recommendation_id: str, feedback: Dict):
        """フィードバックから学習"""
        self.feedback_data.append({
            "recommendation_id": recommendation_id,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        })
        # 実際の学習ロジックはここに実装

class HumanExecutor:
    """
    👤 人間実行者 - 実際の実行を担当
    AIの推奨を確認してから実行
    """
    
    def __init__(self):
        self.execution_log = []
    
    async def review_and_execute(self, recommendations: List[HealingRecommendation]):
        """推奨事項を確認して実行"""
        if not recommendations:
            print("✅ システムは健康です。対応不要です。")
            return
        
        print("\n🏥 === Self-Healing 推奨事項 ===\n")
        
        for i, rec in enumerate(recommendations, 1):
            self._display_recommendation(i, rec)
        
        # 人間の判断を待つ
        while True:
            choice = input("\n実行する推奨事項の番号を入力 (0で終了、aで全詳細): ").strip()
            
            if choice == "0":
                print("終了します。")
                break
            elif choice == "a":
                self._show_all_details(recommendations)
            elif choice.isdigit() and 1 <= int(choice) <= len(recommendations):
                await self._execute_recommendation(recommendations[int(choice)-1])
            else:
                print("無効な入力です。")
    
    def _display_recommendation(self, index: int, rec: HealingRecommendation):
        """推奨事項の表示"""
        severity_emoji = {
            HealthStatus.HEALTHY: "🟢",
            HealthStatus.WARNING: "🟡",
            HealthStatus.CRITICAL: "🔴",
            HealthStatus.EMERGENCY: "🚨"
        }
        
        print(f"{index}. {severity_emoji[rec.severity]} [{rec.severity.value}] {rec.description}")
        print(f"   理由: {rec.reasoning}")
        print(f"   影響: {rec.estimated_impact}")
        
        if rec.requires_sudo:
            print("   ⚠️  要sudo権限")
        if rec.data_loss_risk:
            print("   ⚠️  データ損失リスクあり")
    
    def _show_all_details(self, recommendations: List[HealingRecommendation]):
        """全推奨事項の詳細表示"""
        for i, rec in enumerate(recommendations, 1):
            print(f"\n--- 推奨事項 {i} 詳細 ---")
            self._display_recommendation(i, rec)
            print("   推奨アクション:")
            for action in rec.recommended_actions:
                print(f"     - {action}")
    
    async def _execute_recommendation(self, rec: HealingRecommendation):
        """推奨事項の実行（人間が実際にコマンドを実行）"""
        print(f"\n実行準備: {rec.description}")
        print("\n推奨コマンド:")
        for action in rec.recommended_actions:
            print(f"  $ {action}")
        
        confirm = input("\n上記のコマンドを手動で実行してください。完了したら Enter: ")
        
        # 実行記録
        self.execution_log.append({
            "recommendation": rec,
            "executed_at": datetime.now().isoformat(),
            "executed_by": "human"
        })
        
        print("✅ 実行を記録しました。")

# 使用例
async def main():
    """
    新しいSelf-Healingパターンのデモ
    AIは判定、人間は実行
    """
    print("🏥 Self-Healing System (AI判定者パラダイム版)")
    print("=" * 50)
    
    # AI判定者と人間実行者のインスタンス化
    ai_judge = SelfHealingJudge()
    human_executor = HumanExecutor()
    
    # Step 1: AIがシステム健康状態を分析
    print("\n📊 システム健康状態を分析中...")
    health_metrics = await ai_judge.analyze_system_health()
    
    print(f"\nCPU使用率: {health_metrics['cpu_usage']:.1f}%")
    print(f"メモリ使用率: {health_metrics['memory_usage']:.1f}%")
    print(f"ディスク使用率: {health_metrics['disk_usage']:.1f}%")
    print(f"空きディスク: {health_metrics['disk_space_gb']:.1f}GB")
    
    # Step 2: AIが推奨事項を生成
    print("\n🧠 AI判定者が推奨事項を生成中...")
    recommendations = await ai_judge.generate_healing_recommendations(health_metrics)
    
    # Step 3: 人間が確認して実行
    await human_executor.review_and_execute(recommendations)
    
    # Step 4: フィードバック（オプション）
    if recommendations:
        feedback = input("\n実行結果はいかがでしたか？ (good/bad/skip): ").strip()
        if feedback in ["good", "bad"]:
            ai_judge.learn_from_feedback("demo_session", {"result": feedback})
            print("✅ フィードバックを記録しました。")

if __name__ == "__main__":
    import os
    asyncio.run(main())