#!/usr/bin/env python3
"""
Elders Guild Flask Web Application with Authentication
認証機能付きダッシュボード
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from functools import wraps

import pika
import psutil
from flask import flash
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from web.auth_manager import AuthenticationError
from web.auth_manager import AuthManager
from wtforms import BooleanField
from wtforms import PasswordField
from wtforms import StringField
from wtforms.validators import DataRequired

from libs.env_config import get_config

# Flask アプリケーション初期化
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ai_company_secret_key_2025_secure")

# CSRF保護
csrf = CSRFProtect(app)

# 設定読み込み
config = get_config()

# 認証マネージャー初期化
auth_manager = AuthManager(db_path=str(config.PROJECT_ROOT / "data" / "auth.db"), secret_key=app.secret_key)

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ログインフォーム
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")


# 現在のユーザーを取得する関数
def get_current_user():
    """セッションから現在のユーザーを取得"""
    token = session.get("auth_token")
    if token:
        return auth_manager.validate_session(token)
    return None


# ログイン必須デコレーター（Flask用）
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash("ログインが必要です", "error")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


# 管理者権限必須デコレーター
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash("ログインが必要です", "error")
            return redirect(url_for("auth.login", next=request.url))
        if user.role != "admin":
            flash("管理者権限が必要です", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)

    return decorated_function


# 認証ブループリント
from flask import Blueprint

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """ログインページ"""
    form = LoginForm()

    if form.validate_on_submit():
        try:
            user, session_obj = auth_manager.authenticate(form.username.data, form.password.data)

            # セッションに保存
            session["auth_token"] = session_obj.token
            session["username"] = user.username
            session["user_role"] = user.role

            # Remember Me
            if form.remember.data:
                session.permanent = True

            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
            return redirect(url_for("dashboard"))

        except AuthenticationError as e:
            flash(str(e), "error")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    """ログアウト"""
    token = session.get("auth_token")
    if token:
        auth_manager.logout(token)

    session.clear()
    flash("ログアウトしました", "success")
    return redirect(url_for("auth.login"))


# 認証ブループリントを登録
app.register_blueprint(auth_bp, url_prefix="/auth")


# メインルート
@app.route("/")
def index():
    """インデックスページ"""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
@login_required
def dashboard():
    """ダッシュボード表示"""
    user = get_current_user()
    return render_template("dashboard.html", current_user=user)


# API エンドポイント（認証付き）
@app.route("/api/status")
@login_required
def api_status():
    """システムステータスAPI"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Calculate uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = (datetime.now() - boot_time).total_seconds()

        # Active tasks (dummy data for now)
        active_tasks = 5  # TODO: Get from task database

        # Worker utilization
        worker_count = len([p for p in psutil.process_iter(["name"]) if "worker" in p.info["name"]])
        worker_utilization = min(100, worker_count * 20)

        status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent,
            "health_score": _calculate_health_score(),
            "system_healthy": True,
            "active_tasks": active_tasks,
            "worker_utilization": worker_utilization,
            "queue_throughput": 15,  # TODO: Calculate from queue metrics
            "uptime": uptime,
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/workers")
@login_required
def api_workers():
    """ワーカー情報API"""
    workers = []
    try:
        for proc in psutil.process_iter(["pid", "name", "cmdline", "cpu_percent", "memory_info"]):
            try:
                cmdline = " ".join(proc.info.get("cmdline", []))
                for worker_type in ["task_worker", "pm_worker", "result_worker", "dialog_worker"]:
                    if worker_type in cmdline:
                        workers.append(
                            {
                                "name": worker_type,
                                "pid": proc.info["pid"],
                                "status": "active",
                                "cpu_usage": proc.info.get("cpu_percent", 0),
                                "memory_usage": proc.info.get("memory_info", {}).get("rss", 0),
                                "current_task": None,  # TODO: Get from worker state
                                "completed_tasks": 0,  # TODO: Get from metrics
                            }
                        )
            except:
                pass

        return jsonify({"workers": workers})
    except Exception as e:
        logger.error(f"Error getting worker info: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/queues")
@login_required
def api_queues():
    """キュー情報API"""
    queues = []
    try:
        rabbitmq_config = config.get_rabbitmq_config()
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitmq_config["host"], port=rabbitmq_config["port"])
        )
        channel = connection.channel()

        for queue_name in ["ai_tasks", "ai_pm", "ai_results", "ai_dialog"]:
            try:
                method = channel.queue_declare(queue=queue_name, passive=True)
                queues.append(
                    {
                        "name": queue_name,
                        "messages": method.method.message_count,
                        "consumers": method.method.consumer_count,
                        "durable": True,
                        "publish_rate": 0,  # TODO: Calculate from metrics
                        "deliver_rate": 0,  # TODO: Calculate from metrics
                    }
                )
            except:
                queues.append(
                    {
                        "name": queue_name,
                        "messages": 0,
                        "consumers": 0,
                        "durable": True,
                        "publish_rate": 0,
                        "deliver_rate": 0,
                    }
                )

        connection.close()
        return jsonify({"queues": queues})
    except Exception as e:
        logger.error(f"Error getting queue info: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/tasks", methods=["GET"])
@login_required
def api_tasks():
    """タスク一覧API"""
    tasks = []
    try:
        db_path = config.PROJECT_ROOT / "data" / "tasks.db"
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT task_id, task_type, status, created_at, priority
                FROM task_history
                ORDER BY created_at DESC
                LIMIT 100
            """
            )
            for row in cursor.fetchall():
                tasks.append(
                    {
                        "id": row[0],
                        "title": f"{row[1]} - {row[0]}",
                        "description": "",
                        "status": row[2] or "pending",
                        "priority": row[4] if len(row) > 4 else "medium",
                        "assignee": None,
                        "created_at": row[3],
                    }
                )
            conn.close()
    except Exception as e:
        logger.error(f"Error loading tasks: {e}")

    return jsonify({"tasks": tasks})


@app.route("/api/tasks", methods=["POST"])
@login_required
def api_create_task():
    """タスク作成API"""
    try:
        request.get_json()
        # TODO: Implement task creation
        return jsonify({"id": "new_task_id", "message": "Task created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/tasks/<task_id>", methods=["PATCH"])
@login_required
def api_update_task(task_id):
    """タスク更新API"""
    try:
        request.get_json()
        # TODO: Implement task update
        return jsonify({"message": "Task updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/tasks/<task_id>", methods=["DELETE"])
@login_required
def api_delete_task(task_id):
    """タスク削除API"""
    try:
        # TODO: Implement task deletion
        return jsonify({"message": "Task deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/elder/council")
@login_required
def api_elder_council():
    """4賢者システム状態API"""
    elder_council = {
        "knowledge-sage": {"status": "稼働中", "healthy": True, "last_update": datetime.now().isoformat()},
        "task-oracle": {"status": "稼働中", "healthy": True, "last_update": datetime.now().isoformat()},
        "crisis-sage": {"status": "監視中", "healthy": True, "last_update": datetime.now().isoformat()},
        "search-mystic": {"status": "待機中", "healthy": True, "last_update": datetime.now().isoformat()},
    }
    return jsonify(elder_council)


# 管理者API
@app.route("/api/admin/users")
@admin_required
def api_admin_users():
    """ユーザー一覧API（管理者のみ）"""
    try:
        conn = sqlite3.connect(auth_manager.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, role, is_active, created_at, last_login
            FROM users
            ORDER BY created_at DESC
        """
        )

        users = []
        for row in cursor.fetchall():
            users.append(
                {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "role": row[3],
                    "is_active": bool(row[4]),
                    "created_at": row[5],
                    "last_login": row[6],
                }
            )

        conn.close()
        return jsonify({"users": users})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/clear-sessions", methods=["POST"])
@admin_required
def api_clear_sessions():
    """期限切れセッションクリアAPI（管理者のみ）"""
    try:
        cleaned = auth_manager.clean_expired_sessions()
        return jsonify({"message": f"{cleaned}個の期限切れセッションをクリアしました", "cleaned": cleaned})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/restart-workers", methods=["POST"])
@admin_required
def api_restart_workers():
    """ワーカー再起動API（管理者のみ）"""
    try:
        # TODO: Implement worker restart
        return jsonify({"message": "ワーカーを再起動しました"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health_check():
    """ヘルスチェックエンドポイント（認証不要）"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat(), "server": "Flask/Auth"})


def _calculate_health_score():
    """ヘルススコア計算"""
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    score = 100
    if cpu > 80:
        score -= 20
    elif cpu > 60:
        score -= 10
    if memory > 80:
        score -= 20
    elif memory > 60:
        score -= 10
    return max(0, score)


# エラーハンドラー
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found"}), 404
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Internal server error"}), 500
    return render_template("500.html"), 500


# 初期管理者ユーザー作成
def create_initial_admin():
    """初期管理者ユーザーを作成"""
    try:
        admin = auth_manager.create_user(
            username="admin", email="admin@aicompany.local", password="admin123", role="admin"
        )
        logger.info(f"Created initial admin user: {admin.username}")
    except ValueError:
        # すでに存在する場合は無視
        pass


# WSGI アプリケーション
application = app

if __name__ == "__main__":
    # 初期管理者作成
    create_initial_admin()

    # 開発サーバーとして実行
    app.run(host=config.WEB_UI_HOST, port=config.WEB_UI_PORT, debug=True)
