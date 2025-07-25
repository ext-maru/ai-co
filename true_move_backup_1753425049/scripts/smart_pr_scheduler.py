#!/usr/bin/env python3
"""
⚡ Smart PR Scheduler
コンフリクト回避機能付きインテリジェントPR自動化システム
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from github import Github

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SmartPRScheduler")


class ConflictAwarePRScheduler:
    """コンフリクト回避機能付きPRスケジューラー"""

    def __init__(self):
        self.github = None
        self.repo = None
        self.schedule_file = Path("logs/pr_schedule.json")
        self.schedule_file.parent.mkdir(exist_ok=True)

    async def initialize(self):
        """GitHub API初期化"""
        github_token = os.environ.get("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN環境変数が設定されていません")

        self.github = Github(github_token)
        self.repo = self.github.get_repo("ext-maru/ai-co")
        logger.info("✅ GitHub API初期化完了")

    def analyze_activity_pattern(self) -> Dict:
        """リポジトリの活動パターン分析"""
        try:
            # 過去7日のコミット活動を分析
            since = datetime.now() - timedelta(days=7)
            commits = list(self.repo.get_commits(since=since))

            # 時間帯別活動分析
            hourly_activity = {}
            for commit in commits:
                hour = commit.commit.author.date.hour
                hourly_activity[hour] = hourly_activity.get(hour, 0) + 1

            # PR作成活動分析
            prs = list(self.repo.get_pulls(state="all", sort="created"))[:50]
            pr_creation_hours = []
            for pr in prs:
                if pr.created_at:
                    pr_creation_hours.append(pr.created_at.hour)

            # 低活動時間帯を特定
            low_activity_hours = [
                hour for hour in range(24) if hourly_activity.get(hour, 0) <= 1
            ]

            return {
                "hourly_activity": hourly_activity,
                "pr_creation_hours": pr_creation_hours,
                "low_activity_hours": low_activity_hours,
                "total_commits_week": len(commits),
                "analysis_date": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.warning(f"活動パターン分析失敗: {e}")
            return {
                "low_activity_hours": [2, 3, 4, 5, 6],  # デフォルト深夜時間帯
                "analysis_date": datetime.now().isoformat(),
            }

    def get_optimal_schedule(self) -> List[Dict]:
        """最適なPR作成スケジュール生成"""
        activity = self.analyze_activity_pattern()
        low_activity_hours = activity.get("low_activity_hours", [2, 3, 4, 5, 6])

        # コンフリクト回避スケジュール
        schedules = [
            {
                "time": "02:00",
                "cron": "0 2 * * *",
                "description": "深夜処理 - 最低コンフリクトリスク",
                "frequency": "daily",
                "max_issues": 1,
            },
            {
                "time": "06:00",
                "cron": "0 6 * * *",
                "description": "早朝処理 - 低コンフリクトリスク",
                "frequency": "daily",
                "max_issues": 2,
            },
            {
                "time": "12:00",
                "cron": "0 */6 * * *",
                "description": "6時間毎処理 - バランス重視",
                "frequency": "4times_daily",
                "max_issues": 1,
            },
            {
                "time": "*/30 * * * *",
                "cron": "*/30 * * * *",
                "description": "30分毎処理 - 即座対応",
                "frequency": "continuous",
                "max_issues": 1,
            },
        ]

        return schedules

    def recommend_strategy(self) -> Dict:
        """推奨戦略提案"""
        activity = self.analyze_activity_pattern()
        schedules = self.get_optimal_schedule()

        # リポジトリ活動レベルに基づく推奨
        weekly_commits = activity.get("total_commits_week", 0)

        if weekly_commits > 50:
            # 高活動リポジトリ
            recommended = schedules[3]  # 30分毎
            risk_level = "high"
            recommendation = "高活動リポジトリのため30分毎の小刻み処理を推奨"
        elif weekly_commits > 20:
            # 中活動リポジトリ
            recommended = schedules[2]  # 6時間毎
            risk_level = "medium"
            recommendation = "中活動リポジトリのため6時間毎処理を推奨"
        else:
            # 低活動リポジトリ
            recommended = schedules[1]  # 6:00日次
            risk_level = "low"
            recommendation = "低活動リポジトリのため早朝日次処理を推奨"

        return {
            "recommended_schedule": recommended,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "activity_analysis": activity,
            "all_options": schedules,
        }


async def main():
    """メイン処理"""
    logger.info("⚡ Smart PR Scheduler 分析開始")

    scheduler = ConflictAwarePRScheduler()
    await scheduler.initialize()

    # 推奨戦略取得
    strategy = scheduler.recommend_strategy()

    print("\n" + "=" * 60)
    print("🧠 コンフリクト回避PR自動化戦略分析")
    print("=" * 60)

    print(f"\n📊 リポジトリ活動分析:")
    activity = strategy["activity_analysis"]
    print(f"  週間コミット数: {activity.get('total_commits_week', 0)}")
    print(f"  低活動時間帯: {activity.get('low_activity_hours', [])}")

    print(f"\n🎯 推奨戦略:")
    recommended = strategy["recommended_schedule"]
    print(f"  実行時間: {recommended['time']}")
    print(f"  Cron設定: {recommended['cron']}")
    print(f"  説明: {recommended['description']}")
    print(f"  処理頻度: {recommended['frequency']}")
    print(f"  最大Issue数: {recommended['max_issues']}")
    print(f"  コンフリクトリスク: {strategy['risk_level']}")

    print(f"\n💡 理由: {strategy['recommendation']}")

    print(f"\n📋 全オプション:")
    for i, option in enumerate(strategy["all_options"], 1):
        print(f"  {i}. {option['description']}")
        print(f"     Cron: {option['cron']}")
        print(f"     頻度: {option['frequency']}")

    print(f"\n🔧 設定方法:")
    print(f"crontab -e")
    print(
        f"{recommended['cron']} /home/aicompany/ai_co/scripts/enhanced_auto_pr_cron.sh"
    )

    print("=" * 60)

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
