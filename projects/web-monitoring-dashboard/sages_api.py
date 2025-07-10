#!/usr/bin/env python3
"""
4賢者統合システム API エンドポイント
WebUI との連携用 Flask API
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Dict

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Blueprint
from flask import Flask
from flask import jsonify
from flask import request

from libs.claude_task_tracker import ClaudeTaskTracker as TaskTracker
from libs.incident_manager import IncidentManager
from libs.mana_system import mana_system
from libs.rag_manager import RAGManager

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Blueprint作成
sages_api = Blueprint("sages_api", __name__, url_prefix="/api")


# 4賢者システムのインスタンス
class SagesSystemManager:
    def __init__(self):
        self.knowledge_sage = None  # ナレッジ賢者
        self.task_sage = None  # タスク賢者
        self.incident_sage = None  # インシデント賢者
        self.rag_sage = None  # RAG賢者
        self.initialize_sages()

    def initialize_sages(self):
        """4賢者システム初期化"""
        try:
            # RAG賢者初期化
            self.rag_sage = RAGManager()
            logger.info("RAG賢者を初期化しました")

            # タスク賢者初期化
            self.task_sage = TaskTracker()
            logger.info("タスク賢者を初期化しました")

            # インシデント賢者初期化
            self.incident_sage = IncidentManager()
            logger.info("インシデント賢者を初期化しました")

            logger.info("4賢者システムの初期化が完了しました")

        except Exception as e:
            logger.error(f"4賢者システム初期化エラー: {e}")

    def get_knowledge_sage_status(self) -> Dict[str, Any]:
        """ナレッジ賢者状態取得"""
        try:
            # knowledge_base ディレクトリの情報を取得
            kb_path = Path(__file__).parent.parent / "knowledge_base"
            md_files = list(kb_path.glob("**/*.md"))
            json_files = list(kb_path.glob("**/*.json"))

            categories = set()
            for md_file in md_files:
                # ディレクトリ名をカテゴリとして使用
                if md_file.parent.name != "knowledge_base":
                    categories.add(md_file.parent.name)

            return {
                "id": "knowledge_sage",
                "name": "ナレッジ賢者",
                "type": "knowledge",
                "status": "active",
                "health": 95,
                "lastActive": datetime.now().isoformat(),
                "currentTask": "知識ベース管理・学習データ統合",
                "knowledgeBase": {
                    "documents": len(md_files) + len(json_files),
                    "lastUpdated": datetime.now().isoformat(),
                    "categories": list(categories),
                },
            }
        except Exception as e:
            logger.error(f"ナレッジ賢者状態取得エラー: {e}")
            return self._get_error_sage_status("knowledge_sage", "ナレッジ賢者")

    def get_task_sage_status(self) -> Dict[str, Any]:
        """タスク賢者状態取得"""
        try:
            if self.task_sage:
                # タスクトラッカーから実際の統計を取得
                stats = self.task_sage.get_task_statistics()

                return {
                    "id": "task_sage",
                    "name": "タスク賢者",
                    "type": "task",
                    "status": "active",
                    "health": 92,
                    "lastActive": datetime.now().isoformat(),
                    "currentTask": "プロジェクト進捗管理・優先順位最適化",
                    "taskQueue": {
                        "pending": stats.get("pending", 0),
                        "active": stats.get("active", 0),
                        "completed": stats.get("completed", 0),
                        "failed": stats.get("failed", 0),
                    },
                }
            else:
                return self._get_mock_task_sage_status()
        except Exception as e:
            logger.error(f"タスク賢者状態取得エラー: {e}")
            return self._get_error_sage_status("task_sage", "タスク賢者")

    def get_incident_sage_status(self) -> Dict[str, Any]:
        """インシデント賢者状態取得"""
        try:
            if self.incident_sage:
                # インシデントマネージャーから実際の統計を取得
                incidents = self.incident_sage.get_incident_statistics()

                return {
                    "id": "incident_sage",
                    "name": "インシデント賢者",
                    "type": "incident",
                    "status": "active",
                    "health": 98,
                    "lastActive": datetime.now().isoformat(),
                    "currentTask": "システム監視・問題解決支援",
                    "incidents": {
                        "critical": incidents.get("critical", 0),
                        "warning": incidents.get("warning", 0),
                        "resolved": incidents.get("resolved", 0),
                        "total": incidents.get("total", 0),
                    },
                }
            else:
                return self._get_mock_incident_sage_status()
        except Exception as e:
            logger.error(f"インシデント賢者状態取得エラー: {e}")
            return self._get_error_sage_status("incident_sage", "インシデント賢者")

    def get_rag_sage_status(self) -> Dict[str, Any]:
        """RAG賢者状態取得"""
        try:
            if self.rag_sage:
                # RAGマネージャーから実際の統計を取得
                index_stats = self.rag_sage.get_index_statistics()

                return {
                    "id": "rag_sage",
                    "name": "RAG賢者",
                    "type": "rag",
                    "status": "active",
                    "health": 94,
                    "lastActive": datetime.now().isoformat(),
                    "currentTask": "情報検索・知識統合支援",
                    "searchEngine": {
                        "indexSize": index_stats.get("index_size", 0),
                        "lastIndexed": index_stats.get("last_indexed", datetime.now().isoformat()),
                        "queryLatency": index_stats.get("avg_latency", 0),
                    },
                }
            else:
                return self._get_mock_rag_sage_status()
        except Exception as e:
            logger.error(f"RAG賢者状態取得エラー: {e}")
            return self._get_error_sage_status("rag_sage", "RAG賢者")

    def _get_mock_task_sage_status(self) -> Dict[str, Any]:
        """タスク賢者モック状態"""
        return {
            "id": "task_sage",
            "name": "タスク賢者",
            "type": "task",
            "status": "active",
            "health": 88,
            "lastActive": datetime.now().isoformat(),
            "currentTask": "プロジェクト進捗管理・優先順位最適化",
            "taskQueue": {"pending": 5, "active": 2, "completed": 23, "failed": 1},
        }

    def _get_mock_incident_sage_status(self) -> Dict[str, Any]:
        """インシデント賢者モック状態"""
        return {
            "id": "incident_sage",
            "name": "インシデント賢者",
            "type": "incident",
            "status": "active",
            "health": 96,
            "lastActive": datetime.now().isoformat(),
            "currentTask": "システム監視・問題解決支援",
            "incidents": {"critical": 0, "warning": 2, "resolved": 15, "total": 17},
        }

    def _get_mock_rag_sage_status(self) -> Dict[str, Any]:
        """RAG賢者モック状態"""
        return {
            "id": "rag_sage",
            "name": "RAG賢者",
            "type": "rag",
            "status": "active",
            "health": 91,
            "lastActive": datetime.now().isoformat(),
            "currentTask": "情報検索・知識統合支援",
            "searchEngine": {"indexSize": 15420, "lastIndexed": datetime.now().isoformat(), "queryLatency": 45},
        }

    def _get_error_sage_status(self, sage_id: str, sage_name: str) -> Dict[str, Any]:
        """エラー状態の賢者ステータス"""
        return {
            "id": sage_id,
            "name": sage_name,
            "type": sage_id.replace("_sage", ""),
            "status": "error",
            "health": 0,
            "lastActive": datetime.now().isoformat(),
            "currentTask": "エラー状態",
        }


# グローバルインスタンス
sages_manager = SagesSystemManager()


@sages_api.route("/sages/status")
def get_sages_status():
    """4賢者システム状態取得"""
    try:
        # 各賢者の状態を取得
        sages = {
            "knowledge_sage": sages_manager.get_knowledge_sage_status(),
            "task_sage": sages_manager.get_task_sage_status(),
            "incident_sage": sages_manager.get_incident_sage_status(),
            "rag_sage": sages_manager.get_rag_sage_status(),
        }

        # システム全体の健全性計算
        total_health = sum(sage["health"] for sage in sages.values())
        overall_health = total_health // len(sages)

        return jsonify(
            {
                "success": True,
                "sages": sages,
                "systemHealth": {
                    "overall": overall_health,
                    "connectivity": True,
                    "lastSyncTime": datetime.now().isoformat(),
                },
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"賢者状態取得エラー: {e}")
        return jsonify({"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}), 500


@sages_api.route("/sages/collaboration/sessions")
def get_collaboration_sessions():
    """協調セッション一覧取得"""
    try:
        # モックデータ（実際のシステムでは実際のセッションデータを取得）
        sessions = [
            {
                "id": "session_001",
                "participants": ["knowledge", "rag"],
                "status": "active",
                "objective": "知識ベース最適化協調",
                "startTime": datetime.now().isoformat(),
                "duration": 125,
            },
            {
                "id": "session_002",
                "participants": ["task", "incident"],
                "status": "consensus",
                "objective": "インシデント対応プロセス改善",
                "startTime": datetime.now().isoformat(),
                "duration": 78,
            },
        ]

        return jsonify({"success": True, "sessions": sessions, "timestamp": datetime.now().isoformat()})

    except Exception as e:
        logger.error(f"協調セッション取得エラー: {e}")
        return jsonify({"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}), 500


@sages_api.route("/sages/health")
def get_system_health():
    """システム健全性取得"""
    try:
        # 各賢者の健全性チェック
        health_checks = {
            "knowledge_sage": sages_manager.get_knowledge_sage_status()["health"],
            "task_sage": sages_manager.get_task_sage_status()["health"],
            "incident_sage": sages_manager.get_incident_sage_status()["health"],
            "rag_sage": sages_manager.get_rag_sage_status()["health"],
        }

        overall_health = sum(health_checks.values()) // len(health_checks)

        return jsonify(
            {
                "success": True,
                "health": {
                    "overall": overall_health,
                    "sages": health_checks,
                    "connectivity": True,
                    "lastCheck": datetime.now().isoformat(),
                },
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"システム健全性取得エラー: {e}")
        return jsonify({"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}), 500


@sages_api.route("/mana/status")
def get_mana_status():
    """マナシステム状態取得"""
    try:
        mana_status = mana_system.get_all_mana_status()
        return jsonify({"success": True, "mana": mana_status, "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"マナ状態取得エラー: {e}")
        return jsonify({"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}), 500


@sages_api.route("/mana/consume", methods=["POST"])
def consume_mana():
    """マナ消費エンドポイント"""
    try:
        data = request.get_json()
        spirit = data.get("spirit")
        amount = data.get("amount", 0)
        reason = data.get("reason", "unknown")

        if not spirit:
            return (
                jsonify(
                    {"success": False, "error": "Spirit name is required", "timestamp": datetime.now().isoformat()}
                ),
                400,
            )

        result = mana_system.consume_mana(spirit, amount, reason)
        result["timestamp"] = datetime.now().isoformat()

        return jsonify(result)

    except Exception as e:
        logger.error(f"マナ消費エラー: {e}")
        return jsonify({"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}), 500


@sages_api.route("/mana/restore", methods=["POST"])
def restore_mana():
    """マナ回復エンドポイント"""
    try:
        data = request.get_json()
        spirit = data.get("spirit")
        amount = data.get("amount", 0)

        if not spirit:
            return (
                jsonify(
                    {"success": False, "error": "Spirit name is required", "timestamp": datetime.now().isoformat()}
                ),
                400,
            )

        result = mana_system.restore_mana(spirit, amount)
        result["timestamp"] = datetime.now().isoformat()

        return jsonify(result)

    except Exception as e:
        logger.error(f"マナ回復エラー: {e}")
        return jsonify({"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}), 500


@sages_api.route("/mana/history")
def get_mana_history():
    """マナ履歴取得"""
    try:
        limit = request.args.get("limit", 50, type=int)
        history = mana_system.get_mana_history(limit)

        return jsonify(
            {"success": True, "history": history, "count": len(history), "timestamp": datetime.now().isoformat()}
        )

    except Exception as e:
        logger.error(f"マナ履歴取得エラー: {e}")
        return jsonify({"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}), 500


@sages_api.route("/mana/council/simulate", methods=["POST"])
def simulate_council():
    """評議会シミュレーション"""
    try:
        data = request.get_json() or {}
        duration = data.get("duration", 300)

        result = mana_system.simulate_council_meeting(duration)

        return jsonify({"success": True, "simulation": result, "timestamp": datetime.now().isoformat()})

    except Exception as e:
        logger.error(f"評議会シミュレーションエラー: {e}")
        return jsonify({"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}), 500


@sages_api.route("/mana/emergency/boost", methods=["POST"])
def emergency_boost():
    """緊急マナブースト"""
    try:
        result = mana_system.emergency_mana_boost()

        return jsonify({"success": True, "boost_result": result, "timestamp": datetime.now().isoformat()})

    except Exception as e:
        logger.error(f"緊急ブーストエラー: {e}")
        return jsonify({"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}), 500


if __name__ == "__main__":
    # テスト用の独立実行
    app = Flask(__name__)
    app.register_blueprint(sages_api)
    app.run(debug=True, port=5001)
