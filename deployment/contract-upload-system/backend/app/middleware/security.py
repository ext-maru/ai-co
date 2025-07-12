"""
セキュリティミドルウェア - Elder Flow準拠
本番環境セキュリティ強化機能
"""

from fastapi import FastAPI, Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
import time
from typing import Dict, Set
import json
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """セキュリティヘッダー設定ミドルウェア"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # セキュリティヘッダーの設定
        if os.getenv('ENABLE_SECURITY_HEADERS', 'true').lower() == 'true':
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

            # HSTS (本番環境でHTTPS使用時)
            if os.getenv('ENABLE_HSTS', 'true').lower() == 'true':
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

            # CSP (Content Security Policy)
            if os.getenv('ENABLE_CSP', 'true').lower() == 'true':
                csp = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
                response.headers['Content-Security-Policy'] = csp

        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """レート制限ミドルウェア"""

    def __init__(self, app, requests_per_minute: int = 100, requests_per_hour: int = 1000):
        super().__init__(app)
        self.requests_per_minute = int(os.getenv('RATE_LIMIT_PER_MINUTE', requests_per_minute))
        self.requests_per_hour = int(os.getenv('RATE_LIMIT_PER_HOUR', requests_per_hour))

        # リクエスト履歴 (IP別)
        self.minute_requests: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.requests_per_minute))
        self.hour_requests: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.requests_per_hour))

        self.enabled = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)

        # クライアントIPアドレス取得
        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # レート制限チェック
        if self._is_rate_limited(client_ip, current_time):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )

        # リクエスト記録
        self._record_request(client_ip, current_time)

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """クライアントIP取得 (プロキシ対応)"""
        # X-Forwarded-For ヘッダーをチェック (プロキシ経由時)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        # X-Real-IP ヘッダーをチェック
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip

        # 直接接続の場合
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """レート制限チェック"""
        minute_requests = self.minute_requests[client_ip]
        hour_requests = self.hour_requests[client_ip]

        # 1分間の制限チェック
        minute_cutoff = current_time - 60
        while minute_requests and minute_requests[0] < minute_cutoff:
            minute_requests.popleft()

        if len(minute_requests) >= self.requests_per_minute:
            return True

        # 1時間の制限チェック
        hour_cutoff = current_time - 3600
        while hour_requests and hour_requests[0] < hour_cutoff:
            hour_requests.popleft()

        if len(hour_requests) >= self.requests_per_hour:
            return True

        return False

    def _record_request(self, client_ip: str, current_time: float):
        """リクエスト記録"""
        self.minute_requests[client_ip].append(current_time)
        self.hour_requests[client_ip].append(current_time)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """構造化リクエストログミドルウェア"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # リクエスト情報記録
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client_ip": request.client.host if request.client else "unknown",
            "timestamp": start_time
        }

        response = await call_next(request)

        # レスポンス情報記録
        process_time = time.time() - start_time
        response_info = {
            "status_code": response.status_code,
            "process_time": process_time,
            "response_headers": dict(response.headers)
        }

        # 構造化ログ出力
        log_data = {
            "event": "http_request",
            "request": request_info,
            "response": response_info
        }

        # ログレベル判定
        if response.status_code >= 500:
            logger.error(json.dumps(log_data))
        elif response.status_code >= 400:
            logger.warning(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))

        # レスポンスヘッダーに処理時間追加
        response.headers["X-Process-Time"] = str(process_time)

        return response

class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF保護ミドルウェア"""

    def __init__(self, app):
        super().__init__(app)
        self.allowed_origins = set(
            origin.strip()
            for origin in os.getenv('ALLOWED_ORIGINS', '').split(',')
            if origin.strip()
        )
        self.enabled = len(self.allowed_origins) > 0

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)

        # 状態変更メソッドのみチェック
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            origin = request.headers.get('Origin')
            referer = request.headers.get('Referer')

            # Originヘッダーチェック
            if origin and origin not in self.allowed_origins:
                raise HTTPException(
                    status_code=403,
                    detail="CSRF: Invalid origin"
                )

            # Refererヘッダーチェック (Originがない場合)
            if not origin and referer:
                referer_origin = '/'.join(referer.split('/')[:3])
                if referer_origin not in self.allowed_origins:
                    raise HTTPException(
                        status_code=403,
                        detail="CSRF: Invalid referer"
                    )

        return await call_next(request)

def configure_security_middleware(app: FastAPI):
    """セキュリティミドルウェア設定"""

    # CORS設定
    if os.getenv('CORS_ENABLED', 'true').lower() == 'true':
        allowed_origins = [
            origin.strip()
            for origin in os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
            if origin.strip()
        ]

        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=os.getenv('CORS_ALLOW_CREDENTIALS', 'true').lower() == 'true',
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # セッション管理
    session_secret = os.getenv('SECRET_KEY', 'development-secret-key')
    app.add_middleware(SessionMiddleware, secret_key=session_secret)

    # カスタムセキュリティミドルウェア
    app.add_middleware(CSRFProtectionMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    logger.info("Security middleware configured successfully")

# ファイルアップロードセキュリティ
class FileUploadSecurity:
    """ファイルアップロードセキュリティ機能"""

    def __init__(self):
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE', 31457280))  # 30MB
        self.allowed_types = set(
            ext.strip().lower()
            for ext in os.getenv('ALLOWED_FILE_TYPES', 'pdf,doc,docx,txt').split(',')
            if ext.strip()
        )

    def validate_file(self, file_content: bytes, filename: str) -> dict:
        """ファイル検証"""
        result = {
            "valid": True,
            "errors": []
        }

        # ファイルサイズチェック
        if len(file_content) > self.max_file_size:
            result["valid"] = False
            result["errors"].append(f"File size exceeds limit ({self.max_file_size} bytes)")

        # ファイル拡張子チェック
        if '.' not in filename:
            result["valid"] = False
            result["errors"].append("File extension required")
        else:
            ext = filename.rsplit('.', 1)[1].lower()
            if ext not in self.allowed_types:
                result["valid"] = False
                result["errors"].append(f"File type '{ext}' not allowed")

        # ファイル内容の基本検証
        if len(file_content) == 0:
            result["valid"] = False
            result["errors"].append("Empty file not allowed")

        return result

# グローバルインスタンス
file_upload_security = FileUploadSecurity()
