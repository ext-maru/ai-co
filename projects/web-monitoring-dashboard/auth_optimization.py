#!/usr/bin/env python3
"""
認証処理パフォーマンス最適化システム
目標: 認証処理を50ms以下に最適化
"""

import logging
import sys
import threading
import time
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import jwt

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Blueprint
from flask import jsonify
from flask import request

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 認証最適化Blueprint
auth_optimization = Blueprint("auth_optimization", __name__, url_prefix="/api/auth")


class FastAuthenticationEngine:
    """高速認証エンジン"""

    def __init__(self):
        # インメモリキャッシュ
        self.token_cache = {}  # token -> user_data
        self.user_cache = {}  # user_id -> user_data
        self.permission_cache = {}  # user_id -> permissions

        # キャッシュTTL設定
        self.cache_ttl = {"token": 300, "user": 600, "permission": 900}  # 5分  # 10分  # 15分

        # パフォーマンス統計
        self.performance_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_response_time": 0,
            "response_times": [],
        }

        # セキュリティ設定
        self.jwt_secret = "ai_company_super_secret_key_2025"
        self.algorithm = "HS256"

        # レート制限
        self.rate_limits = defaultdict(list)
        self.max_requests_per_minute = 1000

        # バックグラウンドクリーンアップ
        self._start_cleanup_thread()

    def authenticate_fast(self, token: str) -> Optional[Dict[str, Any]]:
        """高速認証（目標: 50ms以下）"""
        start_time = time.time()

        try:
            # 1. キャッシュチェック（最優先）
            cached_data = self._get_cached_token(token)
            if cached_data:
                self._record_performance(start_time, cache_hit=True)
                return cached_data

            # 2. JWT検証（高速化版）
            user_data = self._verify_jwt_fast(token)
            if not user_data:
                self._record_performance(start_time, cache_hit=False)
                return None

            # 3. ユーザー情報取得（キャッシュ優先）
            user_id = user_data.get("user_id")
            user_info = self._get_user_info_fast(user_id)
            if not user_info:
                self._record_performance(start_time, cache_hit=False)
                return None

            # 4. 権限情報取得（キャッシュ優先）
            permissions = self._get_permissions_fast(user_id)

            # 5. 結果統合とキャッシュ保存
            result = {
                "user_id": user_id,
                "username": user_info.get("username"),
                "role": user_info.get("role", "user"),
                "permissions": permissions,
                "authenticated_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(minutes=5)).isoformat(),
            }

            # キャッシュ保存
            self._cache_token(token, result)

            self._record_performance(start_time, cache_hit=False)
            return result

        except Exception as e:
            logger.error(f"認証エラー: {e}")
            self._record_performance(start_time, cache_hit=False)
            return None

    def _get_cached_token(self, token: str) -> Optional[Dict[str, Any]]:
        """トークンキャッシュ取得"""
        if token in self.token_cache:
            cached_data, cached_time = self.token_cache[token]
            if (time.time() - cached_time) < self.cache_ttl["token"]:
                return cached_data
            else:
                # 期限切れキャッシュ削除
                del self.token_cache[token]
        return None

    def _verify_jwt_fast(self, token: str) -> Optional[Dict[str, Any]]:
        """高速JWT検証"""
        try:
            # JWT デコード（検証込み）
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.algorithm])

            # 期限チェック
            if payload.get("exp", 0) < time.time():
                return None

            return payload

        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            logger.error(f"JWT検証エラー: {e}")
            return None

    def _get_user_info_fast(self, user_id: str) -> Optional[Dict[str, Any]]:
        """高速ユーザー情報取得"""
        # キャッシュチェック
        if user_id in self.user_cache:
            cached_data, cached_time = self.user_cache[user_id]
            if (time.time() - cached_time) < self.cache_ttl["user"]:
                return cached_data

        # モックユーザーデータ（実際はDBから取得）
        mock_users = {
            "admin_001": {"username": "admin", "role": "admin", "active": True},
            "user_001": {"username": "user1", "role": "user", "active": True},
            "user_002": {"username": "user2", "role": "user", "active": True},
            "analyst_001": {"username": "analyst1", "role": "analyst", "active": True},
        }

        user_info = mock_users.get(user_id)
        if user_info and user_info.get("active"):
            # キャッシュ保存
            self.user_cache[user_id] = (user_info, time.time())
            return user_info

        return None

    def _get_permissions_fast(self, user_id: str) -> List[str]:
        """高速権限取得"""
        # キャッシュチェック
        if user_id in self.permission_cache:
            cached_data, cached_time = self.permission_cache[user_id]
            if (time.time() - cached_time) < self.cache_ttl["permission"]:
                return cached_data

        # ユーザー情報から権限を導出
        user_info = self._get_user_info_fast(user_id)
        if not user_info:
            return []

        role = user_info.get("role", "user")

        # ロールベース権限マッピング
        role_permissions = {
            "admin": ["read", "write", "delete", "admin", "analytics", "reports"],
            "analyst": ["read", "analytics", "reports"],
            "user": ["read"],
        }

        permissions = role_permissions.get(role, ["read"])

        # キャッシュ保存
        self.permission_cache[user_id] = (permissions, time.time())

        return permissions

    def _cache_token(self, token: str, user_data: Dict[str, Any]):
        """トークンキャッシュ保存"""
        self.token_cache[token] = (user_data, time.time())

        # キャッシュサイズ制限（メモリ最適化）
        if len(self.token_cache) > 10000:
            # 古いエントリを削除
            oldest_tokens = sorted(self.token_cache.items(), key=lambda x: x[1][1])[:1000]

            for token_to_remove, _ in oldest_tokens:
                del self.token_cache[token_to_remove]

    def _record_performance(self, start_time: float, cache_hit: bool):
        """パフォーマンス記録"""
        response_time = (time.time() - start_time) * 1000  # ms

        self.performance_stats["total_requests"] += 1
        self.performance_stats["response_times"].append(response_time)

        if cache_hit:
            self.performance_stats["cache_hits"] += 1
        else:
            self.performance_stats["cache_misses"] += 1

        # 最新100件の平均を計算
        recent_times = self.performance_stats["response_times"][-100:]
        self.performance_stats["average_response_time"] = sum(recent_times) / len(recent_times)

        # メモリ最適化: 古い記録を削除
        if len(self.performance_stats["response_times"]) > 1000:
            self.performance_stats["response_times"] = self.performance_stats["response_times"][-500:]

    def _start_cleanup_thread(self):
        """バックグラウンドクリーンアップ開始"""

        def cleanup_loop():
            while True:
                try:
                    time.sleep(300)  # 5分間隔
                    self._cleanup_expired_cache()
                except Exception as e:
                    logger.error(f"クリーンアップエラー: {e}")

        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()

    def _cleanup_expired_cache(self):
        """期限切れキャッシュクリーンアップ"""
        current_time = time.time()

        # トークンキャッシュクリーンアップ
        expired_tokens = [
            token
            for token, (_, cached_time) in self.token_cache.items()
            if (current_time - cached_time) > self.cache_ttl["token"]
        ]
        for token in expired_tokens:
            del self.token_cache[token]

        # ユーザーキャッシュクリーンアップ
        expired_users = [
            user_id
            for user_id, (_, cached_time) in self.user_cache.items()
            if (current_time - cached_time) > self.cache_ttl["user"]
        ]
        for user_id in expired_users:
            del self.user_cache[user_id]

        # 権限キャッシュクリーンアップ
        expired_permissions = [
            user_id
            for user_id, (_, cached_time) in self.permission_cache.items()
            if (current_time - cached_time) > self.cache_ttl["permission"]
        ]
        for user_id in expired_permissions:
            del self.permission_cache[user_id]

        logger.info(
            f"キャッシュクリーンアップ完了: tokens={len(expired_tokens)}, users={len(expired_users)}, permissions={len(expired_permissions)}"
        )

    def get_performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計取得"""
        cache_hit_rate = 0
        if self.performance_stats["total_requests"] > 0:
            cache_hit_rate = (self.performance_stats["cache_hits"] / self.performance_stats["total_requests"]) * 100

        return {
            "total_requests": self.performance_stats["total_requests"],
            "cache_hit_rate": round(cache_hit_rate, 2),
            "average_response_time_ms": round(self.performance_stats["average_response_time"], 2),
            "cache_sizes": {
                "tokens": len(self.token_cache),
                "users": len(self.user_cache),
                "permissions": len(self.permission_cache),
            },
            "performance_target_met": self.performance_stats["average_response_time"] <= 50,
        }

    def generate_test_token(self, user_id: str, expires_in_minutes: int = 60) -> str:
        """テスト用トークン生成"""
        payload = {"user_id": user_id, "iat": time.time(), "exp": time.time() + (expires_in_minutes * 60)}

        return jwt.encode(payload, self.jwt_secret, algorithm=self.algorithm)


class AdvancedCacheManager:
    """高度キャッシュ管理システム"""

    def __init__(self):
        self.cache_layers = {
            "l1": {},  # L1: 超高速キャッシュ (100件)
            "l2": {},  # L2: 高速キャッシュ (1000件)
            "l3": {},  # L3: 大容量キャッシュ (10000件)
        }

        self.cache_limits = {"l1": 100, "l2": 1000, "l3": 10000}

        self.access_counts = defaultdict(int)
        self.last_access = defaultdict(float)

    def get(self, key: str) -> Optional[Any]:
        """多層キャッシュ取得"""
        # L1キャッシュチェック
        if key in self.cache_layers["l1"]:
            self.access_counts[key] += 1
            self.last_access[key] = time.time()
            return self.cache_layers["l1"][key]

        # L2キャッシュチェック
        if key in self.cache_layers["l2"]:
            value = self.cache_layers["l2"][key]
            # L1に昇格
            self._promote_to_l1(key, value)
            self.access_counts[key] += 1
            self.last_access[key] = time.time()
            return value

        # L3キャッシュチェック
        if key in self.cache_layers["l3"]:
            value = self.cache_layers["l3"][key]
            # L2に昇格
            self._promote_to_l2(key, value)
            self.access_counts[key] += 1
            self.last_access[key] = time.time()
            return value

        return None

    def set(self, key: str, value: Any):
        """多層キャッシュ設定"""
        # アクセス頻度に基づいて適切な層に配置
        access_count = self.access_counts[key]

        if access_count > 10:
            self._set_l1(key, value)
        elif access_count > 3:
            self._set_l2(key, value)
        else:
            self._set_l3(key, value)

        self.last_access[key] = time.time()

    def _promote_to_l1(self, key: str, value: Any):
        """L1キャッシュに昇格"""
        self._set_l1(key, value)
        # 元の層から削除
        self.cache_layers["l2"].pop(key, None)
        self.cache_layers["l3"].pop(key, None)

    def _promote_to_l2(self, key: str, value: Any):
        """L2キャッシュに昇格"""
        self._set_l2(key, value)
        # L3から削除
        self.cache_layers["l3"].pop(key, None)

    def _set_l1(self, key: str, value: Any):
        """L1キャッシュ設定"""
        if len(self.cache_layers["l1"]) >= self.cache_limits["l1"]:
            self._evict_lru("l1")
        self.cache_layers["l1"][key] = value

    def _set_l2(self, key: str, value: Any):
        """L2キャッシュ設定"""
        if len(self.cache_layers["l2"]) >= self.cache_limits["l2"]:
            self._evict_lru("l2")
        self.cache_layers["l2"][key] = value

    def _set_l3(self, key: str, value: Any):
        """L3キャッシュ設定"""
        if len(self.cache_layers["l3"]) >= self.cache_limits["l3"]:
            self._evict_lru("l3")
        self.cache_layers["l3"][key] = value

    def _evict_lru(self, layer: str):
        """LRU方式で古いキャッシュを削除"""
        cache = self.cache_layers[layer]
        if not cache:
            return

        # 最も古いアクセスのキーを特定
        oldest_key = min(cache.keys(), key=lambda k: self.last_access.get(k, 0))

        # 削除
        del cache[oldest_key]
        self.access_counts.pop(oldest_key, None)
        self.last_access.pop(oldest_key, None)


# グローバルインスタンス
fast_auth_engine = FastAuthenticationEngine()
advanced_cache_manager = AdvancedCacheManager()


# API エンドポイント
@auth_optimization.route("/fast-login", methods=["POST"])
def fast_login():
    """高速ログインエンドポイント"""
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400

        # 簡易認証（実際はハッシュ比較）
        valid_credentials = {"admin": "admin123", "user1": "user123", "user2": "user456", "analyst1": "analyst123"}

        if username not in valid_credentials or valid_credentials[username] != password:
            return jsonify({"error": "Invalid credentials"}), 401

        # ユーザーIDマッピング
        user_id_mapping = {"admin": "admin_001", "user1": "user_001", "user2": "user_002", "analyst1": "analyst_001"}

        user_id = user_id_mapping[username]

        # トークン生成
        token = fast_auth_engine.generate_test_token(user_id)

        return jsonify({"success": True, "token": token, "user_id": user_id, "username": username})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_optimization.route("/verify-fast", methods=["POST"])
def verify_fast():
    """高速認証検証エンドポイント"""
    try:
        data = request.json
        token = data.get("token")

        if not token:
            return jsonify({"error": "Token required"}), 400

        # 高速認証実行
        start_time = time.time()
        user_data = fast_auth_engine.authenticate_fast(token)
        response_time = (time.time() - start_time) * 1000

        if not user_data:
            return jsonify({"error": "Invalid or expired token"}), 401

        return jsonify(
            {
                "success": True,
                "user": user_data,
                "response_time_ms": round(response_time, 2),
                "performance_target_met": response_time <= 50,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_optimization.route("/performance-stats")
def get_performance_stats():
    """パフォーマンス統計エンドポイント"""
    try:
        stats = fast_auth_engine.get_performance_stats()
        return jsonify(stats)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_optimization.route("/cache-warm-up", methods=["POST"])
def cache_warm_up():
    """キャッシュウォームアップ"""
    try:
        # テストユーザーでキャッシュをウォームアップ
        test_users = ["admin_001", "user_001", "user_002", "analyst_001"]
        warmed_up = 0

        for user_id in test_users:
            token = fast_auth_engine.generate_test_token(user_id)
            user_data = fast_auth_engine.authenticate_fast(token)
            if user_data:
                warmed_up += 1

        return jsonify(
            {
                "success": True,
                "warmed_up_users": warmed_up,
                "cache_stats": fast_auth_engine.get_performance_stats()["cache_sizes"],
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_optimization.route("/benchmark", methods=["POST"])
def run_benchmark():
    """認証パフォーマンスベンチマーク"""
    try:
        data = request.json or {}
        iterations = data.get("iterations", 100)

        # ベンチマーク実行
        test_token = fast_auth_engine.generate_test_token("user_001")
        response_times = []

        for _ in range(iterations):
            start_time = time.time()
            fast_auth_engine.authenticate_fast(test_token)
            response_time = (time.time() - start_time) * 1000
            response_times.append(response_time)

        # 統計計算
        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        target_met_count = sum(1 for t in response_times if t <= 50)

        return jsonify(
            {
                "success": True,
                "benchmark_results": {
                    "iterations": iterations,
                    "average_response_time_ms": round(avg_time, 2),
                    "min_response_time_ms": round(min_time, 2),
                    "max_response_time_ms": round(max_time, 2),
                    "target_achievement_rate": round((target_met_count / iterations) * 100, 2),
                    "performance_target_met": avg_time <= 50,
                },
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # テスト実行
    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(auth_optimization)

    print("=== 認証最適化システム ===")
    print("エンドポイント:")
    print("- POST /api/auth/fast-login")
    print("- POST /api/auth/verify-fast")
    print("- GET  /api/auth/performance-stats")
    print("- POST /api/auth/cache-warm-up")
    print("- POST /api/auth/benchmark")

    # 初期キャッシュウォームアップ
    print("\n初期キャッシュウォームアップ中...")
    test_users = ["admin_001", "user_001", "user_002", "analyst_001"]
    for user_id in test_users:
        token = fast_auth_engine.generate_test_token(user_id)
        fast_auth_engine.authenticate_fast(token)

    stats = fast_auth_engine.get_performance_stats()
    print(f"初期統計: {stats}")

    app.run(debug=True, port=5006)
