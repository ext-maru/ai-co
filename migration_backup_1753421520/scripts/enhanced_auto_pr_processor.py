#!/usr/bin/env python3
"""
🚀 Enhanced Auto PR Processor
PR自動作成機能付きの改良版Issue処理システム
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.integrations.github.enhanced_auto_issue_processor import (
    EnhancedAutoIssueProcessor,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("EnhancedAutoPRProcessor")


async def main():
    """メイン処理"""

    # 環境変数チェック
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.error("❌ GITHUB_TOKEN環境変数が設定されていません")
        return False

    # リポジトリ設定
    os.environ["GITHUB_REPOSITORY"] = "ext-maru/ai-co"

    logger.info("🚀 Enhanced Auto PR Processor 開始")
    logger.info(f"🔑 GitHub Token: {github_token[:10]}...")
    logger.info(f"📦 Repository: {os.environ['GITHUB_REPOSITORY']}")

    try:
        # Enhanced Auto Issue Processor初期化
        processor = EnhancedAutoIssueProcessor()

        # 拡張版実行
        await processor.run_enhanced()

        # メトリクス取得
        metrics = await processor.get_metrics_report()

        logger.info("📊 処理結果:")
        logger.info(f"  処理済みIssue数: {metrics['metrics']['processed_issues']}")
        logger.info(f"  成功PR数: {metrics['metrics']['successful_prs']}")
        logger.info(f"  失敗数: {metrics['metrics']['failed_attempts']}")
        logger.info(f"  成功率: {metrics['success_rate']:0.1f}%")

        logger.info("✅ Enhanced Auto PR Processor 完了")
        return True

    except Exception as e:
        logger.error(f"❌ エラー: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
