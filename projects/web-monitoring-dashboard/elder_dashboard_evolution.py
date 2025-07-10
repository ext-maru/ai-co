#!/usr/bin/env python3
"""
Elder Dashboard Evolution - 基礎UI
エルダーズ・ハーモニー・システム監視ダッシュボード

設計: クロードエルダー
承認: エルダーズ評議会
実装日: 2025年7月9日
"""

import json
import logging
import sqlite3
import threading
import time
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Dict
from typing import List

from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request
from flask_socketio import emit
from flask_socketio import SocketIO

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# プロジェクトパス
project_root = Path("/home/aicompany/ai_co")


class ElderDashboardEvolution:
    """エルダーズ・ハーモニー・システム監視ダッシュボード"""

    def __init__(self):
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "elders_harmony_2025"
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        self.project_root = project_root
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)

        # データベース初期化
        self.init_database()

        # ルート設定
        self.setup_routes()

        # WebSocketハンドラー
        self.setup_websocket_handlers()

        # アナリティクスダッシュボードを統合
        from web.analytics_dashboard_view import analytics_bp

        self.app.register_blueprint(analytics_bp)

        # 監視スレッド
        self.monitoring_thread = None
        self.monitoring_active = False

        # 高度機能統合
        from web.elder_dashboard_advanced import init_advanced_dashboard

        self.advanced_dashboard = init_advanced_dashboard(self.socketio, self.project_root)

        logger.info("🏛️ Elder Dashboard Evolution 初期化完了")

    def init_database(self):
        """データベース初期化"""
        db_path = self.project_root / "elder_dashboard.db"

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # プロトコル実行履歴テーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS protocol_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                protocol TEXT NOT NULL,
                message TEXT NOT NULL,
                approved BOOLEAN NOT NULL,
                execution_time REAL,
                sage_count INTEGER,
                risk_score REAL,
                files_changed INTEGER,
                complexity REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # 4賢者相談履歴テーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sage_consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protocol_id INTEGER,
                sage_name TEXT NOT NULL,
                approval BOOLEAN NOT NULL,
                risk_score REAL,
                advice TEXT,
                timestamp TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (protocol_id) REFERENCES protocol_history (id)
            )
        """
        )

        conn.commit()
        conn.close()

        logger.info("📊 Elder Dashboard データベース初期化完了")

    def setup_routes(self):
        """Flaskルート設定"""

        @self.app.route("/")
        def dashboard():
            """メインダッシュボード"""
            return render_template("elder_dashboard.html")

        @self.app.route("/api/protocol-stats")
        def protocol_stats():
            """プロトコル統計データ"""
            return jsonify(self.get_protocol_statistics())

        @self.app.route("/api/recent-commits")
        def recent_commits():
            """最近のコミット履歴"""
            return jsonify(self.get_recent_commits())

        @self.app.route("/api/sage-activity")
        def sage_activity():
            """4賢者活動状況"""
            return jsonify(self.get_sage_activity())

        @self.app.route("/api/system-health")
        def system_health():
            """システムヘルス状況"""
            return jsonify(self.get_system_health())

        @self.app.route("/api/commit-trends")
        def commit_trends():
            """コミット傾向分析"""
            return jsonify(self.get_commit_trends())

        @self.app.route("/api/advanced-overview")
        def advanced_overview():
            """高度機能概要"""
            if self.advanced_dashboard:
                return jsonify(self.advanced_dashboard.get_system_overview())
            return jsonify({"error": "Advanced dashboard not initialized"})

        @self.app.route("/api/optimization-suggestions")
        def optimization_suggestions():
            """最適化提案"""
            if self.advanced_dashboard:
                return jsonify(self.advanced_dashboard.get_optimization_suggestions())
            return jsonify({"error": "Advanced dashboard not initialized"})

        @self.app.route("/api/elder-council-reports")
        def elder_council_reports():
            """エルダー評議会レポート"""
            if self.advanced_dashboard:
                return jsonify(self.advanced_dashboard.get_elder_council_reports())
            return jsonify({"error": "Advanced dashboard not initialized"})

        @self.app.route("/advanced")
        def advanced_dashboard():
            """高度機能ダッシュボード"""
            return render_template("elder_dashboard_advanced.html")

    def setup_websocket_handlers(self):
        """WebSocketハンドラー設定"""

        @self.socketio.on("connect")
        def handle_connect():
            """クライアント接続"""
            logger.info("🔗 クライアント接続")
            emit("status", {"message": "Elder Dashboard に接続しました"})

        @self.socketio.on("disconnect")
        def handle_disconnect():
            """クライアント切断"""
            logger.info("❌ クライアント切断")

        @self.socketio.on("start_monitoring")
        def handle_start_monitoring():
            """リアルタイム監視開始"""
            logger.info("📡 リアルタイム監視開始")
            self.start_monitoring()

        @self.socketio.on("stop_monitoring")
        def handle_stop_monitoring():
            """リアルタイム監視停止"""
            logger.info("⏹️ リアルタイム監視停止")
            self.stop_monitoring()

        @self.socketio.on("start_advanced_monitoring")
        def handle_start_advanced_monitoring():
            """高度監視開始"""
            logger.info("🚀 高度監視開始")
            if self.advanced_dashboard:
                self.advanced_dashboard.start_advanced_monitoring()

        @self.socketio.on("stop_advanced_monitoring")
        def handle_stop_advanced_monitoring():
            """高度監視停止"""
            logger.info("⏹️ 高度監視停止")
            if self.advanced_dashboard:
                self.advanced_dashboard.stop_advanced_monitoring()

        @self.socketio.on("advanced_connect")
        def handle_advanced_connect():
            """高度機能クライアント接続"""
            if self.advanced_dashboard:
                self.advanced_dashboard.handle_client_connect(request.sid)

        @self.socketio.on("advanced_disconnect")
        def handle_advanced_disconnect():
            """高度機能クライアント切断"""
            if self.advanced_dashboard:
                self.advanced_dashboard.handle_client_disconnect(request.sid)

    def start_monitoring(self):
        """監視スレッド開始"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self.monitor_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            logger.info("🔍 監視スレッド開始")

            # 高度監視も開始
            if self.advanced_dashboard:
                self.advanced_dashboard.start_advanced_monitoring()

    def stop_monitoring(self):
        """監視スレッド停止"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
        logger.info("⏸️ 監視スレッド停止")

        # 高度監視も停止
        if self.advanced_dashboard:
            self.advanced_dashboard.stop_advanced_monitoring()

    def monitor_loop(self):
        """監視ループ"""
        while self.monitoring_active:
            try:
                # 新しいログファイルをスキャン
                self.scan_new_logs()

                # リアルタイムデータを送信
                self.socketio.emit(
                    "realtime_update",
                    {
                        "timestamp": datetime.now().isoformat(),
                        "stats": self.get_protocol_statistics(),
                        "recent": self.get_recent_commits(limit=5),
                        "health": self.get_system_health(),
                    },
                )

                time.sleep(2)  # 2秒間隔

            except Exception as e:
                logger.error(f"❌ 監視ループエラー: {e}")
                time.sleep(5)  # エラー時は5秒待機

    def scan_new_logs(self):
        """新しいログファイルをスキャン"""
        try:
            # Lightning レポートスキャン
            lightning_files = list(self.logs_dir.glob("lightning_report_*.json"))
            for file_path in lightning_files:
                self.process_lightning_report(file_path)

            # Council レポートスキャン
            council_files = list(self.logs_dir.glob("council_report_*.json"))
            for file_path in council_files:
                self.process_council_report(file_path)

        except Exception as e:
            logger.error(f"❌ ログスキャンエラー: {e}")

    def process_lightning_report(self, file_path: Path):
        """Lightning レポート処理"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # JSONファイルが完全かチェック
            if not content.strip().endswith("}"):
                logger.warning(f"⚠️ 不完全なJSONファイル: {file_path}")
                return

            report = json.loads(content)

            # 必須フィールドのチェック
            if "context" not in report or "sage_consultations" not in report:
                logger.warning(f"⚠️ 不完全なレポート構造: {file_path}")
                return

            # データベースに保存
            conn = sqlite3.connect(str(self.project_root / "elder_dashboard.db"))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR IGNORE INTO protocol_history
                (timestamp, protocol, message, approved, execution_time, sage_count, risk_score, files_changed, complexity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    report["timestamp"],
                    "Lightning",
                    report["context"].get("description", ""),
                    True,  # Lightning は基本的に承認
                    0.5,  # Lightning は高速
                    len(report["sage_consultations"]),
                    report["sage_consultations"][0]["risk_score"] if report["sage_consultations"] else 0.0,
                    len(report["context"].get("files", [])),
                    report["context"].get("complexity", 0.0),
                ),
            )

            protocol_id = cursor.lastrowid

            # 4賢者相談結果を保存
            for sage in report["sage_consultations"]:
                cursor.execute(
                    """
                    INSERT INTO sage_consultations
                    (protocol_id, sage_name, approval, risk_score, advice, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        protocol_id,
                        sage["sage"],
                        sage["approval"],
                        sage["risk_score"],
                        sage["advice"],
                        sage["timestamp"],
                    ),
                )

            conn.commit()
            conn.close()

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"⚠️ Lightning レポート形式エラー: {file_path} - {e}")
        except Exception as e:
            logger.error(f"❌ Lightning レポート処理エラー: {e}")

    def process_council_report(self, file_path: Path):
        """Council レポート処理"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                report = json.load(f)

            # データベースに保存
            conn = sqlite3.connect(str(self.project_root / "elder_dashboard.db"))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR IGNORE INTO protocol_history
                (timestamp, protocol, message, approved, execution_time, sage_count, risk_score, files_changed, complexity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    report["timestamp"],
                    "Council",
                    report["context"].get("description", ""),
                    report["decision"]["approved"],
                    5.0,  # Council は標準時間
                    len(report["sage_consultations"]),
                    sum(s["risk_score"] for s in report["sage_consultations"]) / len(report["sage_consultations"]),
                    len(report["context"].get("files", [])),
                    report["context"].get("complexity", 0.0),
                ),
            )

            protocol_id = cursor.lastrowid

            # 4賢者相談結果を保存
            for sage in report["sage_consultations"]:
                cursor.execute(
                    """
                    INSERT INTO sage_consultations
                    (protocol_id, sage_name, approval, risk_score, advice, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        protocol_id,
                        sage["sage"],
                        sage["approval"],
                        sage["risk_score"],
                        sage["advice"],
                        sage["timestamp"],
                    ),
                )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"❌ Council レポート処理エラー: {e}")

    def get_protocol_statistics(self) -> Dict:
        """プロトコル統計データ取得"""
        conn = sqlite3.connect(str(self.project_root / "elder_dashboard.db"))
        cursor = conn.cursor()

        # 全体統計
        cursor.execute(
            """
            SELECT
                protocol,
                COUNT(*) as count,
                AVG(execution_time) as avg_time,
                SUM(CASE WHEN approved = 1 THEN 1 ELSE 0 END) as approved_count,
                AVG(risk_score) as avg_risk
            FROM protocol_history
            GROUP BY protocol
        """
        )

        stats = {}
        for row in cursor.fetchall():
            protocol, count, avg_time, approved_count, avg_risk = row
            stats[protocol] = {
                "count": count,
                "avg_time": avg_time or 0,
                "approval_rate": (approved_count / count) * 100 if count > 0 else 0,
                "avg_risk": avg_risk or 0,
            }

        conn.close()

        return {
            "total_commits": sum(s["count"] for s in stats.values()),
            "protocols": stats,
            "timestamp": datetime.now().isoformat(),
        }

    def get_recent_commits(self, limit: int = 10) -> List[Dict]:
        """最近のコミット履歴取得"""
        conn = sqlite3.connect(str(self.project_root / "elder_dashboard.db"))
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                timestamp, protocol, message, approved, execution_time,
                sage_count, risk_score, files_changed, complexity
            FROM protocol_history
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )

        commits = []
        for row in cursor.fetchall():
            commits.append(
                {
                    "timestamp": row[0],
                    "protocol": row[1],
                    "message": row[2],
                    "approved": row[3],
                    "execution_time": row[4],
                    "sage_count": row[5],
                    "risk_score": row[6],
                    "files_changed": row[7],
                    "complexity": row[8],
                }
            )

        conn.close()
        return commits

    def get_sage_activity(self) -> Dict:
        """4賢者活動状況取得"""
        conn = sqlite3.connect(str(self.project_root / "elder_dashboard.db"))
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                sage_name,
                COUNT(*) as consultations,
                AVG(risk_score) as avg_risk,
                SUM(CASE WHEN approval = 1 THEN 1 ELSE 0 END) as approvals
            FROM sage_consultations
            GROUP BY sage_name
        """
        )

        activity = {}
        for row in cursor.fetchall():
            sage_name, consultations, avg_risk, approvals = row
            activity[sage_name] = {
                "consultations": consultations,
                "avg_risk": avg_risk or 0,
                "approval_rate": (approvals / consultations) * 100 if consultations > 0 else 0,
            }

        conn.close()
        return activity

    def get_system_health(self) -> Dict:
        """システムヘルス状況取得"""
        try:
            # 最近1時間の状況
            one_hour_ago = datetime.now() - timedelta(hours=1)

            conn = sqlite3.connect(str(self.project_root / "elder_dashboard.db"))
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT COUNT(*) FROM protocol_history
                WHERE timestamp > ?
            """,
                (one_hour_ago.isoformat(),),
            )

            recent_activity = cursor.fetchone()[0]

            # エラー率計算
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN approved = 0 THEN 1 ELSE 0 END) as errors
                FROM protocol_history
                WHERE timestamp > ?
            """,
                (one_hour_ago.isoformat(),),
            )

            row = cursor.fetchone()
            total, errors = row[0], row[1] or 0
            error_rate = (errors / total) * 100 if total > 0 else 0

            conn.close()

            # ヘルス状態判定
            if error_rate < 5:
                health_status = "excellent"
            elif error_rate < 15:
                health_status = "good"
            elif error_rate < 30:
                health_status = "warning"
            else:
                health_status = "critical"

            return {
                "status": health_status,
                "recent_activity": recent_activity,
                "error_rate": error_rate,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ システムヘルス取得エラー: {e}")
            return {"status": "unknown", "recent_activity": 0, "error_rate": 0, "timestamp": datetime.now().isoformat()}

    def get_commit_trends(self) -> Dict:
        """コミット傾向分析"""
        conn = sqlite3.connect(str(self.project_root / "elder_dashboard.db"))
        cursor = conn.cursor()

        # 過去7日間の日別統計
        cursor.execute(
            """
            SELECT
                DATE(timestamp) as date,
                protocol,
                COUNT(*) as count
            FROM protocol_history
            WHERE timestamp > DATE('now', '-7 days')
            GROUP BY DATE(timestamp), protocol
            ORDER BY date
        """
        )

        trends = {}
        for row in cursor.fetchall():
            date, protocol, count = row
            if date not in trends:
                trends[date] = {}
            trends[date][protocol] = count

        conn.close()

        return trends

    def run(self, host="0.0.0.0", port=5000, debug=False):
        """ダッシュボード起動"""
        logger.info(f"🚀 Elder Dashboard Evolution 起動: http://{host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)


def main():
    """メイン実行"""
    dashboard = ElderDashboardEvolution()
    dashboard.run(debug=True)


if __name__ == "__main__":
    main()
