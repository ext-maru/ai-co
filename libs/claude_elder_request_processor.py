#!/usr/bin/env python3
"""
Claude Elder Request Processor - クロードエルダーリクエスト処理統合システム
Created: 2025-01-20
Author: Claude Elder

クロードエルダーのすべてのリクエストを統合的に処理し、自動Elder Flow適用を制御する
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.lightweight_logger import get_logger
from libs.claude_elder_auto_flow_interceptor import get_claude_elder_interceptor

logger = get_logger("claude_elder_request_processor")


class ClaudeElderRequestProcessor:
    """クロードエルダーリクエスト処理統合システム"""

    def __init__(self):
        """初期化メソッド"""
        self.interceptor = get_claude_elder_interceptor()
        self.processing_stats = {
            "total_requests": 0,
            "elder_flow_applied": 0,
            "bypass_count": 0,
            "fallback_count": 0,
            "error_count": 0,
            "start_time": datetime.now().isoformat(),
        }

    async def process_claude_elder_request(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """クロードエルダーリクエストの統合処理"""
        self.processing_stats["total_requests"] += 1

        logger.info(f"📥 クロードエルダーリクエスト受信: {user_input[:50]}...")

        # コンテキスト情報の初期化
        processing_context = {
            "user_input": user_input,
            "timestamp": datetime.now().isoformat(),
            "request_id": f"ce_{self.processing_stats['total_requests']:06d}",
            "context": context or {},
        }

        try:
            # Elder Flow自動適用判定・実行
            result = await self.interceptor.process_user_request(user_input)

            # 統計更新
            if result["status"] == "success":
                self.processing_stats["elder_flow_applied"] += 1
                logger.info("✅ Elder Flowで正常処理完了")

                return {
                    "processing_result": "elder_flow_success",
                    "message": "🌊 Elder Flowで自動処理されました",
                    "elder_flow_result": result,
                    "should_continue_normal_processing": False,
                    "context": processing_context,
                }

            elif result["status"] == "bypass":
                self.processing_stats["bypass_count"] += 1
                logger.info("⏭️ Elder Flow適用対象外、通常処理継続")

                return {
                    "processing_result": "normal_processing",
                    "message": "通常のクロードエルダー処理で実行します",
                    "bypass_reason": result.get("reason"),
                    "should_continue_normal_processing": True,
                    "context": processing_context,
                }

            elif result["status"] == "fallback":
                self.processing_stats["fallback_count"] += 1
                logger.warning("⚠️ Elder Flow失敗、通常処理にフォールバック")

                return {
                    "processing_result": "fallback_processing",
                    "message": "Elder Flow実行に失敗しました。通常処理で実行します",
                    "elder_flow_error": result.get("elder_flow_error"),
                    "should_continue_normal_processing": True,
                    "context": processing_context,
                }

            else:  # error
                self.processing_stats["error_count"] += 1
                logger.error(f"❌ Elder Flow処理エラー: {result.get('error')}")

                return {
                    "processing_result": "error_fallback",
                    "message": "Elder Flow処理エラー。通常処理で実行します",
                    "error": result.get("error"),
                    "should_continue_normal_processing": True,
                    "context": processing_context,
                }

        except Exception as e:
            self.processing_stats["error_count"] += 1
            logger.error(f"❌ リクエスト処理中の予期しないエラー: {e}")

            return {
                "processing_result": "unexpected_error",
                "message": "予期しないエラーが発生しました。通常処理で実行します",
                "error": str(e),
                "should_continue_normal_processing": True,
                "context": processing_context,
            }

    def get_processing_stats(self) -> Dict[str, Any]:
        """処理統計の取得"""
        total = self.processing_stats["total_requests"]

        stats = self.processing_stats.copy()

        if total > 0:
            stats["elder_flow_success_rate"] = (
                stats["elder_flow_applied"] / total
            ) * 100
            stats["bypass_rate"] = (stats["bypass_count"] / total) * 100
            stats["fallback_rate"] = (stats["fallback_count"] / total) * 100
            stats["error_rate"] = (stats["error_count"] / total) * 100
        else:
            stats["elder_flow_success_rate"] = 0
            stats["bypass_rate"] = 0
            stats["fallback_rate"] = 0
            stats["error_rate"] = 0

        return stats

    def reset_stats(self) -> None:
        """統計をリセット"""
        self.processing_stats = {
            "total_requests": 0,
            "elder_flow_applied": 0,
            "bypass_count": 0,
            "fallback_count": 0,
            "error_count": 0,
            "start_time": datetime.now().isoformat(),
        }
        logger.info("📊 処理統計をリセットしました")

    def configure_interceptor(self, config: Dict[str, Any]) -> None:
        """インターセプター設定の変更"""
        if "enabled" in config:
            if config["enabled"]:
                self.interceptor.enable_auto_flow()
            else:
                self.interceptor.disable_auto_flow()

        if "bypass_keywords" in config:
            # 既存のバイパスキーワードをクリア（デフォルト以外）
            default_keywords = ["help", "status", "explain", "show", "list", "describe"]
            current_keywords = self.interceptor.bypass_keywords.copy()

            for keyword in current_keywords:
                if keyword not in default_keywords:
                    self.interceptor.remove_bypass_keyword(keyword)

            # 新しいキーワードを追加
            for keyword in config["bypass_keywords"]:
                if keyword not in default_keywords:
                    self.interceptor.add_bypass_keyword(keyword)

        logger.info(f"🔧 インターセプター設定を更新しました: {config}")

    async def test_request_processing(self, test_inputs: list) -> Dict[str, Any]:
        """リクエスト処理のテスト"""
        test_results = []

        for i, test_input in enumerate(test_inputs):
            logger.info(f"🧪 テスト {i+1}/{len(test_inputs)}: {test_input}")

            # パターンマッチングテスト（実際には実行しない）
            pattern_result = self.interceptor.test_pattern_matching(test_input)

            test_results.append(
                {
                    "test_number": i + 1,
                    "input": test_input,
                    "pattern_analysis": pattern_result,
                    "would_apply_elder_flow": pattern_result["should_apply_elder_flow"],
                    "flow_info": pattern_result.get("flow_info"),
                }
            )

        return {
            "test_count": len(test_inputs),
            "results": test_results,
            "summary": {
                "would_apply_elder_flow": sum(
                    1 for r in test_results if r["would_apply_elder_flow"]
                ),
                "would_bypass": sum(
                    1 for r in test_results if not r["would_apply_elder_flow"]
                ),
            },
        }


# シングルトンインスタンス
_claude_elder_processor = None


def get_claude_elder_processor() -> ClaudeElderRequestProcessor:
    """Claude Elder Request Processorのシングルトンインスタンス取得"""
    global _claude_elder_processor
    if _claude_elder_processor is None:
        _claude_elder_processor = ClaudeElderRequestProcessor()
    return _claude_elder_processor


# 便利関数
async def process_claude_elder_input(
    user_input: str, context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """クロードエルダー入力の簡易処理"""
    processor = get_claude_elder_processor()
    return await processor.process_claude_elder_request(user_input, context)


# CLI実行用
async def main():
    """mainメソッド"""
    import argparse

    parser = argparse.ArgumentParser(description="Claude Elder Request Processor")
    parser.add_argument(
        "action", choices=["stats", "test", "config", "reset"], help="実行するアクション"
    )
    parser.add_argument("--input", help="テスト用入力文字列")
    parser.add_argument("--config-file", help="設定ファイルパス")
    parser.add_argument("--test-file", help="テスト入力ファイルパス")

    args = parser.parse_args()

    processor = get_claude_elder_processor()

    if args.action == "stats":
        stats = processor.get_processing_stats()
        print("📊 Claude Elder Request Processor 統計")
        print("=" * 50)
        print(json.dumps(stats, indent=2, ensure_ascii=False))

    elif args.action == "test":
        if args.test_file:
            with open(args.test_file, "r", encoding="utf-8") as f:
                test_inputs = [line.strip() for line in f if line.strip()]
        elif args.input:
            test_inputs = [args.input]
        else:
            test_inputs = [
                "OAuth2.0認証システムを実装してください",
                "バグを修正してください",
                "Elder Flowでユーザー管理機能を作成",
                "help",
                "現在の状況を説明してください",
                "パフォーマンスを最適化したい",
                "セキュリティ脆弱性を修正",
                "テストカバレッジを向上させる",
            ]

        result = await processor.test_request_processing(test_inputs)
        print("🧪 Claude Elder Request Processor テスト結果")
        print("=" * 50)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.action == "config":
        if args.config_file:
            # Deep nesting detected (depth: 5) - consider refactoring
            with open(args.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            processor.configure_interceptor(config)
            print("✅ 設定を更新しました")
        else:
            current_config = processor.interceptor.get_status()
            print("🔧 現在の設定")
            print("=" * 50)
            print(json.dumps(current_config, indent=2, ensure_ascii=False))

    elif args.action == "reset":
        processor.reset_stats()
        print("✅ 統計をリセットしました")

    return 0


if __name__ == "__main__":
    asyncio.run(main())