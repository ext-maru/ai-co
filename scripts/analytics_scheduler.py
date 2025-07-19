#!/usr/bin/env python3
"""
データアナリティクススケジューラー
定期的に分析を実行し、レポートを生成

設計: クロードエルダー
実装日: 2025年7月9日
"""

import asyncio
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import schedule

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.data_analytics_platform import DataAnalyticsPlatform

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(PROJECT_ROOT / "logs" / "analytics_scheduler.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class AnalyticsScheduler:
    """アナリティクススケジューラー"""

    def __init__(self):
        self.platform = DataAnalyticsPlatform(PROJECT_ROOT)
        self.running = False

    async def run_scheduled_analysis(self):
        """スケジュールされた分析を実行"""
        try:
            logger.info("📊 定期分析開始")
            report_path = await self.platform.run_full_analysis()

            # 分析結果の要約をログ出力
            logger.info(f"✅ 定期分析完了: {report_path}")

            # 重要な洞察があれば通知（将来的にSlack連携など）
            self._check_important_insights(report_path)

        except Exception as e:
            logger.error(f"❌ 定期分析エラー: {e}")

    def _check_important_insights(self, report_path: Path):
        """重要な洞察をチェック"""
        try:
            import json

            with open(report_path, "r", encoding="utf-8") as f:
                report = json.load(f)

            # アクションアイテムがある場合はログに記録
            action_items = report.get("action_items", [])
            if action_items:
                logger.warning(
                    f"⚠️ {len(action_items)}個のアクションアイテムが検出されました"
                )
                for item in action_items:
                    logger.warning(f"  • {item}")

            # システムヘルスが低い場合は警告
            for result in report.get("detailed_results", []):
                if result["type"] == "system_health":
                    health_score = result["metrics"].get("current_health_score", 100)
                    if health_score < 80:
                        logger.warning(
                            f"🚨 システムヘルススコアが低下: {health_score}点"
                        )

        except Exception as e:
            logger.error(f"洞察チェックエラー: {e}")

    def schedule_jobs(self):
        """ジョブをスケジュール"""
        # 毎日9時と18時に実行
        schedule.every().day.at("09:00").do(
            lambda: asyncio.run(self.run_scheduled_analysis())
        )
        schedule.every().day.at("18:00").do(
            lambda: asyncio.run(self.run_scheduled_analysis())
        )

        # 1時間ごとの簡易チェック（将来実装）
        # schedule.every().hour.do(self.run_quick_check)

        logger.info("📅 分析スケジュール設定完了")
        logger.info("  • 毎日 09:00 - 包括的分析")
        logger.info("  • 毎日 18:00 - 包括的分析")

    def start(self):
        """スケジューラー開始"""
        self.running = True
        self.schedule_jobs()

        logger.info("🚀 アナリティクススケジューラー起動")

        # 起動時に1回実行
        asyncio.run(self.run_scheduled_analysis())

        # スケジュールループ
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 1分ごとにチェック
            except KeyboardInterrupt:
                logger.info("⏹️ スケジューラー停止")
                self.running = False
                break
            except Exception as e:
                logger.error(f"スケジューラーエラー: {e}")
                time.sleep(60)

    def stop(self):
        """スケジューラー停止"""
        self.running = False


def main():
    """メイン処理"""
    scheduler = AnalyticsScheduler()

    try:
        scheduler.start()
    except Exception as e:
        logger.error(f"致命的エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
