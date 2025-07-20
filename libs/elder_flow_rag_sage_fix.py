#!/usr/bin/env python3
"""
Elder Flow RAG Sage メモリ修正パッチ
Elder Flow実行時のRAG賢者メモリエラーを解決

作成者: クロードエルダー
作成日: 2025-07-20
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def patch_rag_sage_imports():
    """RAG賢者のインポートを軽量版にパッチ"""
    try:
        # 通常のrag_managerの代わりに軽量版を使用
        if "libs.rag_manager" in sys.modules:
            logger.info("🔧 既存のRAG Managerモジュールをアンロード")
            del sys.modules["libs.rag_manager"]

        # 軽量版をインポート
        import libs.lightweight_rag_sage as rag_module

        # rag_managerとして登録
        sys.modules["libs.rag_manager"] = rag_module

        # RagManagerクラスのエイリアスを作成
        rag_module.RagManager = rag_module.LightweightRAGSage

        logger.info("✅ RAG賢者を軽量版にパッチ完了")
        return True

    except Exception as e:
        logger.error(f"❌ RAG賢者パッチエラー: {e}")
        return False


def create_lightweight_rag_sage():
    """軽量版RAG賢者インスタンスを作成"""
    try:
        from libs.lightweight_rag_sage import LightweightRAGSage

        # メモリ効率的な設定で初期化
        sage = LightweightRAGSage(
            max_cache_size=50,  # キャッシュサイズを制限
            enable_connection_pool=True,  # コネクションプーリング有効化
        )

        logger.info("✅ 軽量版RAG賢者インスタンス作成成功")
        return sage

    except Exception as e:
        logger.error(f"❌ 軽量版RAG賢者作成エラー: {e}")
        return None


class ElderFlowRAGSageWrapper:
    """Elder Flow用RAG賢者ラッパー"""

    def __init__(self):
        """軽量版で初期化"""
        self.sage = create_lightweight_rag_sage()
        self.is_ready = self.sage is not None

    def consult_on_issue(self, issue_title: str, issue_body: str) -> Dict[str, Any]:
        """イシューに対する相談（Elder Flow互換）"""
        if not self.is_ready:
            return {
                "status": "error",
                "error": "RAG Sage not initialized",
                "sage": "RAG賢者（軽量版）",
            }

        return self.sage.consult_on_issue(issue_title, issue_body)

    def search_knowledge(self, query: str, limit: int = 5) -> List:
        """知識検索（Elder Flow互換）"""
        if not self.is_ready:
            return []

        return self.sage.search_knowledge(query, limit=limit)

    def add_knowledge(self, content: str, source: str, category: str) -> str:
        """知識追加（Elder Flow互換）"""
        if not self.is_ready:
            return ""

        return self.sage.add_knowledge(content, source, category)

    def cleanup(self):
        """リソースクリーンアップ"""
        if self.sage:
            self.sage.cleanup()


def apply_elder_flow_fix():
    """Elder Flow RAG賢者修正を適用"""
    logger.info("🔧 Elder Flow RAG賢者メモリ修正適用開始")

    # 1. インポートパッチ適用
    if not patch_rag_sage_imports():
        return False

    # 2. 軽量版が動作することを確認
    test_sage = create_lightweight_rag_sage()
    if not test_sage:
        return False

    # テスト実行
    try:
        result = test_sage.consult_on_issue("テスト", "軽量版RAG賢者の動作確認")

        if result.get("status") == "success":
            logger.info("✅ 軽量版RAG賢者動作確認成功")
            test_sage.cleanup()
            return True
        else:
            logger.error("❌ 軽量版RAG賢者動作確認失敗")
            test_sage.cleanup()
            return False

    except Exception as e:
        logger.error(f"❌ 動作確認エラー: {e}")
        if test_sage:
            test_sage.cleanup()
        return False


# 自動修正適用
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if apply_elder_flow_fix():
        print("✅ Elder Flow RAG賢者メモリ修正完了")
        sys.exit(0)
    else:
        print("❌ Elder Flow RAG賢者メモリ修正失敗")
        sys.exit(1)
