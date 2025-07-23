#!/usr/bin/env python3
"""
📝 Logging Crafter Servant (D14)
================================

ログシステム構築専門のドワーフサーバント。
ログ設定、フォーマット、ハンドラー、分析ツールの実装を担当。

Author: Claude Elder
Created: 2025-07-23
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter, defaultdict
from pathlib import Path
import textwrap

from ..base import DwarfServant, ServantCapability


class LoggingCrafterServant(DwarfServant):
    """
    Logging Crafter - ログシステム専門家
    
    主な責務：
    - ログ設定の生成と最適化
    - カスタムハンドラー・フォーマッターの実装
    - ログ分析ツールの提供
    - フレームワーク・監視システムとの統合
    """
    
    def __init__(self):
        super().__init__(
            servant_id="D14",
            name="Logging Crafter",
            specialization="ログシステム構築・設定・分析"
        )
        
        # 能力定義
        self.capabilities = [
            ServantCapability.CODE_GENERATION,
            ServantCapability.MONITORING,
            ServantCapability.PERFORMANCE_TUNING,
            ServantCapability.SAGE_INTEGRATION
        ]
        
        # ログレベルマッピング
        self.log_levels = {
            "debug": "DEBUG",
            "info": "INFO",
            "warning": "WARNING",
            "error": "ERROR",
            "critical": "CRITICAL"
        }
        
    async def generate_config(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """ログ設定を生成"""
        try:
            environment = requirements.get("environment", "development")
            output = requirements.get("output", "console")
            level = requirements.get("level", "info")
            
            # 基本設定
            config = {
                "version": 1,
                "disable_existing_loggers": False,
                "level": self.log_levels.get(level.lower(), "INFO")
            }
            
            # ハンドラー設定
            handlers = []
            if isinstance(output, str):
                output = [output]
            elif not isinstance(output, list):
                output = ["console"]
                
            config["handlers"] = {}
            
            # コンソールハンドラー
            if "console" in output:
                config["handlers"]["console"] = {
                    "class": "logging.StreamHandler",
                    "level": config["level"],
                    "formatter": "standard",
                    "stream": "ext://sys.stdout"
                }
                handlers.append("console")
                
            # ファイルハンドラー
            if "file" in output:
                config["handlers"]["file"] = {
                    "class": "logging.FileHandler",
                    "level": config["level"],
                    "formatter": "standard",
                    "filename": requirements.get("file_path", "app.log"),
                    "mode": "a",
                    "encoding": "utf-8"
                }
                handlers.append("file")
                
            # syslogハンドラー（本番環境）
            if "syslog" in output:
                config["handlers"]["syslog"] = {
                    "class": "logging.handlers.SysLogHandler",
                    "level": config["level"],
                    "formatter": "syslog",
                    "address": "/dev/log"
                }
                handlers.append("syslog")
                
            # ローテーション設定
            if requirements.get("rotation") == "daily":
                retention_days = 30  # デフォルト
                if requirements.get("retention"):
                    # "30 days" から数値を抽出
                    retention_match = re.search(r'(\d+)', requirements["retention"])
                    if retention_match:
                        retention_days = int(retention_match.group(1))
                        
                config["rotation"] = {
                    "when": "midnight",
                    "interval": 1,
                    "backup_count": retention_days
                }
                
                # ローテーティングハンドラーに変更
                if "file" in config["handlers"]:
                    config["handlers"]["file"]["class"] = "logging.handlers.TimedRotatingFileHandler"
                    config["handlers"]["file"]["when"] = "midnight"
                    config["handlers"]["file"]["backupCount"] = retention_days
                    
            # フォーマッター設定
            config["formatters"] = {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
                "syslog": {
                    "format": "%(name)s[%(process)d]: %(levelname)s %(message)s"
                }
            }
            
            # JSON形式の場合
            if requirements.get("format") == "json":
                config["format_type"] = "json"
                config["fields"] = requirements.get("fields", [
                    "timestamp", "level", "logger", "message"
                ])
                config["enrichment"] = {
                    "enabled": requirements.get("enrichment", False)
                }
                
            # ルートロガー設定
            config["root"] = {
                "level": config["level"],
                "handlers": handlers
            }
            
            return {
                "success": True,
                "config": config,
                "handlers": handlers
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate config: {str(e)}"
            }
            
    async def implement_handler(self, handler_config: Dict[str, Any]) -> Dict[str, Any]:
        """ログハンドラーを実装"""
        try:
            handler_type = handler_config.get("type", "file")
            
            if handler_type == "file":
                implementation = self._implement_file_handler(handler_config)
            elif handler_type == "rotating":
                implementation = self._implement_rotating_handler(handler_config)
            elif handler_type == "custom":
                implementation = self._implement_custom_handler(handler_config)
            else:
                return {
                    "success": False,
                    "error": f"Unknown handler type: {handler_type}"
                }
                
            return {
                "success": True,
                "implementation": implementation
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to implement handler: {str(e)}"
            }
            
    def _implement_file_handler(self, config: Dict[str, Any]) -> str:
        """ファイルハンドラーの実装コードを生成"""
        filename = config.get("filename", "app.log")
        mode = config.get("mode", "a")
        encoding = config.get("encoding", "utf-8")
        
        return f"""
import logging

# ファイルハンドラーの設定
file_handler = logging.FileHandler(
    filename='{filename}',
    mode='{mode}',
    encoding='{encoding}'
)

# フォーマッターを設定
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)

# ロガーに追加
logger = logging.getLogger()
logger.addHandler(file_handler)
"""
        
    def _implement_rotating_handler(self, config: Dict[str, Any]) -> str:
        """ローテーティングハンドラーの実装コードを生成"""
        filename = config.get("filename", "app.log")
        max_bytes = config.get("max_bytes", 10485760)
        backup_count = config.get("backup_count", 5)
        
        return f"""
import logging
from logging.handlers import RotatingFileHandler

# ローテーティングファイルハンドラーの設定
rotating_handler = RotatingFileHandler(
    filename='{filename}',
    maxBytes={max_bytes},
    backupCount={backup_count},
    encoding='utf-8'
)

# フォーマッターを設定
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
rotating_handler.setFormatter(formatter)

# ロガーに追加
logger = logging.getLogger()
logger.addHandler(rotating_handler)
"""
        
    def _implement_custom_handler(self, config: Dict[str, Any]) -> str:
        """カスタムハンドラーの実装コードを生成"""
        class_name = config.get("class", "CustomHandler")
        params = config.get("params", {})
        
        # ElasticSearchハンドラーの例
        if class_name == "ElasticSearchHandler":
            hosts = params.get("hosts", ["localhost:9200"])
            index = params.get("index", "application-logs")
            
            return f"""
import logging
import json
from datetime import datetime
from elasticsearch import Elasticsearch

class ElasticSearchHandler(logging.Handler):
    \"\"\"ElasticSearchへログを送信するカスタムハンドラー\"\"\"
    
    def __init__(self, hosts, index_name):
        super().__init__()
        self.es = Elasticsearch(hosts)
        self.index_name = index_name
        
    def emit(self, record):
        try:
            # ログレコードをElasticSearch用に変換
            doc = {{
                'timestamp': datetime.utcnow(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }}
            
            # extra フィールドを追加
            if hasattr(record, 'extra'):
                doc.update(record.extra)
                
            # ElasticSearchにインデックス
            self.es.index(
                index=self.index_name,
                body=doc
            )
        except Exception as e:
            self.handleError(record)

# ハンドラーのインスタンス化と設定
es_handler = ElasticSearchHandler(
    hosts={hosts},
    index_name='{index}'
)

# ロガーに追加
logger = logging.getLogger()
logger.addHandler(es_handler)
"""
        
        # 汎用カスタムハンドラー
        return f"""
class {class_name}(logging.Handler):
    \"\"\"カスタムログハンドラー\"\"\"
    
    def __init__(self, **kwargs):
        super().__init__()
        # パラメータを設定
        {self._format_params(params)}
        
    def emit(self, record):
        \"\"\"ログレコードを処理\"\"\"
        try:
            # カスタム処理をここに実装
            msg = self.format(record)
            # TODO: 実際の送信処理を実装
            pass
        except Exception:
            self.handleError(record)
"""
        
    def _format_params(self, params: Dict[str, Any]) -> str:
        """パラメータを初期化コードに変換"""
        lines = []
        for key, value in params.items():
            if isinstance(value, str):
                lines.append(f"self.{key} = '{value}'")
            else:
                lines.append(f"self.{key} = {value}")
        return "\n        ".join(lines)
        
    async def create_formatter(self, format_config: Dict[str, Any]) -> Dict[str, Any]:
        """ログフォーマッターを作成"""
        try:
            format_type = format_config.get("type", "basic")
            
            if format_type == "basic":
                formatter = self._create_basic_formatter(format_config)
            elif format_type == "json":
                formatter = self._create_json_formatter(format_config)
            else:
                return {
                    "success": False,
                    "error": f"Unknown formatter type: {format_type}"
                }
                
            return {
                "success": True,
                "formatter": formatter
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create formatter: {str(e)}"
            }
            
    def _create_basic_formatter(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """基本フォーマッターを作成"""
        pattern = config.get("pattern", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        
        return {
            "type": "basic",
            "pattern": pattern,
            "implementation": f"""
formatter = logging.Formatter('{pattern}')
"""
        }
        
    def _create_json_formatter(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """JSONフォーマッターを作成"""
        fields = config.get("fields", {
            "timestamp": "%(asctime)s",
            "level": "%(levelname)s",
            "logger": "%(name)s",
            "message": "%(message)s"
        })
        
        implementation = """
import json
import logging

class JSONFormatter(logging.Formatter):
    \"\"\"JSON形式でログを出力するフォーマッター\"\"\"
    
    def format(self, record):
        log_data = {
"""
        
        for field, pattern in fields.items():
            implementation += f"            '{field}': self._format_field(record, '{pattern}'),\n"
            
        implementation += """        }
        
        # extra フィールドを追加
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
            
        return json.dumps(log_data, ensure_ascii=False)
        
    def _format_field(self, record, pattern):
        \"\"\"個別フィールドをフォーマット\"\"\"
        if pattern.startswith('%(') and pattern.endswith(')s'):
            attr = pattern[2:-2]
            return getattr(record, attr, '')
        return pattern

# フォーマッターのインスタンス化
json_formatter = JSONFormatter()
"""
        
        return {
            "type": "json",
            "fields": fields,
            "implementation": implementation
        }
        
    async def analyze_patterns(self, log_samples: List[str]) -> Dict[str, Any]:
        """ログパターンを分析"""
        try:
            patterns = []
            
            # エラーパターンを抽出
            error_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(\w+)\s+(.*)')
            
            # ログをパース
            parsed_logs = []
            for log in log_samples:
                match = error_pattern.match(log)
                if match:
                    parsed_logs.append({
                        "timestamp": match.group(1),
                        "level": match.group(2),
                        "message": match.group(3)
                    })
                    
            # メッセージをグループ化
            message_groups = defaultdict(list)
            for log in parsed_logs:
                # メッセージの主要部分を抽出
                msg_parts = log["message"].split()
                if len(msg_parts) >= 3:
                    key = " ".join(msg_parts[:3])
                    message_groups[key].append(log)
                    
            # パターンを生成
            for key, logs in message_groups.items():
                if len(logs) >= 2:  # 2回以上出現
                    patterns.append({
                        "pattern": key,
                        "count": len(logs),
                        "severity": logs[0]["level"],
                        "first_occurrence": logs[0]["timestamp"],
                        "last_occurrence": logs[-1]["timestamp"]
                    })
                    
            # 重要度でソート
            patterns.sort(key=lambda p: (p["severity"] == "ERROR", p["count"]), reverse=True)
            
            return {
                "success": True,
                "patterns": patterns
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze patterns: {str(e)}"
            }
            
    async def suggest_improvements(self, current_config: Dict[str, Any], issues: List[str]) -> Dict[str, Any]:
        """ログ改善提案を生成"""
        try:
            suggestions = []
            
            for issue in issues:
                issue_lower = issue.lower()
                
                if "debug" in issue_lower and "production" in issue_lower:
                    suggestions.append({
                        "issue": issue,
                        "improvement": "level",
                        "suggestion": "本番環境ではログレベルをINFO以上に設定",
                        "config_change": {"level": "INFO"}
                    })
                    
                if "timestamp" in issue_lower:
                    suggestions.append({
                        "issue": issue,
                        "improvement": "timestamp",
                        "suggestion": "タイムスタンプをフォーマットに追加",
                        "config_change": {
                            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                        }
                    })
                    
                if "structured" in issue_lower:
                    suggestions.append({
                        "issue": issue,
                        "improvement": "json",
                        "suggestion": "構造化ログ（JSON形式）の採用",
                        "config_change": {
                            "formatter": "json",
                            "fields": ["timestamp", "level", "logger", "message", "extra"]
                        }
                    })
                    
            # 一般的な改善提案を追加
            if current_config.get("handlers") == ["console"]:
                suggestions.append({
                    "issue": "No persistent logging",
                    "improvement": "persistence",
                    "suggestion": "ファイルハンドラーを追加して永続化",
                    "config_change": {
                        "handlers": ["console", "file"]
                    }
                })
                
            return {
                "success": True,
                "suggestions": suggestions
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to suggest improvements: {str(e)}"
            }
            
    async def integrate_framework(self, framework_config: Dict[str, Any]) -> Dict[str, Any]:
        """フレームワークとの統合を実装"""
        try:
            framework = framework_config.get("framework", "fastapi")
            
            if framework == "fastapi":
                integration = self._integrate_fastapi(framework_config)
            elif framework == "django":
                integration = self._integrate_django(framework_config)
            elif framework == "flask":
                integration = self._integrate_flask(framework_config)
            else:
                return {
                    "success": False,
                    "error": f"Unknown framework: {framework}"
                }
                
            return {
                "success": True,
                "integration": integration
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to integrate framework: {str(e)}"
            }
            
    def _integrate_fastapi(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """FastAPI統合を実装"""
        middleware_code = """
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import time
import uuid
from contextvars import ContextVar

# コンテキスト変数for request ID
request_id_var: ContextVar[str] = ContextVar('request_id', default='')

class LoggingMiddleware:
    \"\"\"リクエストログ用ミドルウェア\"\"\"
    
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger("fastapi.access")
        
    async def __call__(self, request: Request, call_next):
        # リクエストIDを生成
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        
        # リクエスト開始時刻
        start_time = time.time()
        
        # リクエストログ
        self.logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }
        )
        
        # レスポンス処理
        response = await call_next(request)
        
        # 処理時間計算
        process_time = time.time() - start_time
        
        # レスポンスログ
        self.logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": f"{process_time:.3f}s"
            }
        )
        
        # レスポンスヘッダーにrequest_idを追加
        response.headers["X-Request-ID"] = request_id
        
        return response
"""
        
        setup_code = """
# FastAPIアプリケーションのセットアップ
app = FastAPI()

# ロギング設定
logging.config.dictConfig(logging_config)

# ミドルウェアを追加
app.add_middleware(LoggingMiddleware)

# リクエストIDフィルター
class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True

# すべてのロガーにフィルターを追加
for handler in logging.getLogger().handlers:
    handler.addFilter(RequestIdFilter())
"""
        
        return {
            "middleware": middleware_code,
            "setup_code": setup_code,
            "request_id": True,
            "features": ["request_logging", "response_logging", "correlation_id"]
        }
        
    def _integrate_django(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Django統合を実装（簡易版）"""
        return {
            "middleware": "django.middleware.logging.LoggingMiddleware",
            "settings": {
                "LOGGING": {
                    "version": 1,
                    "disable_existing_loggers": False,
                    "handlers": {
                        "file": {
                            "level": "INFO",
                            "class": "logging.FileHandler",
                            "filename": "django.log",
                        }
                    }
                }
            }
        }
        
    def _integrate_flask(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Flask統合を実装（簡易版）"""
        return {
            "setup_code": """
from flask import Flask, g, request
import logging
import uuid

app = Flask(__name__)

@app.before_request
def before_request():
    g.request_id = str(uuid.uuid4())
    app.logger.info(f"Request: {request.method} {request.path}", 
                   extra={"request_id": g.request_id})

@app.after_request
def after_request(response):
    response.headers["X-Request-ID"] = g.request_id
    return response
"""
        }
        
    async def integrate_monitoring(self, monitoring_config: Dict[str, Any]) -> Dict[str, Any]:
        """監視システムとの統合を実装"""
        try:
            system = monitoring_config.get("system", "prometheus")
            metrics = monitoring_config.get("metrics", [])
            
            if system == "prometheus":
                exporter_code = self._create_prometheus_exporter(metrics)
            else:
                return {
                    "success": False,
                    "error": f"Unknown monitoring system: {system}"
                }
                
            return {
                "success": True,
                "integration": {
                    "system": system,
                    "exporter": exporter_code,
                    "metrics": metrics,
                    "export_interval": monitoring_config.get("export_interval", 60)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to integrate monitoring: {str(e)}"
            }
            
    def _create_prometheus_exporter(self, metrics: List[str]) -> str:
        """Prometheusエクスポーターを作成"""
        return f"""
from prometheus_client import Counter, Histogram, generate_latest
import logging

# メトリクス定義
log_counter = Counter('log_entries_total', 'Total log entries', ['level'])
error_counter = Counter('log_errors_total', 'Total error logs')
warning_counter = Counter('log_warnings_total', 'Total warning logs')
log_volume = Histogram('log_volume_bytes', 'Log message size in bytes')

class PrometheusLogHandler(logging.Handler):
    \"\"\"Prometheusメトリクスを収集するログハンドラー\"\"\"
    
    def emit(self, record):
        # レベル別カウンター
        log_counter.labels(level=record.levelname).inc()
        
        # エラー・警告カウンター
        if record.levelname == 'ERROR':
            error_counter.inc()
        elif record.levelname == 'WARNING':
            warning_counter.inc()
            
        # ログサイズ
        message_size = len(record.getMessage().encode('utf-8'))
        log_volume.observe(message_size)

# ハンドラーを追加
prometheus_handler = PrometheusLogHandler()
logging.getLogger().addHandler(prometheus_handler)

# メトリクスエンドポイント
def metrics_endpoint():
    return generate_latest()
"""
        
    async def implement_correlation(self, correlation_config: Dict[str, Any]) -> Dict[str, Any]:
        """相関ID実装を生成"""
        try:
            header_name = correlation_config.get("header_name", "X-Correlation-ID")
            
            implementation = {
                "filter": f"""
import logging
from contextvars import ContextVar
import uuid

# 相関IDのコンテキスト変数
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')

class CorrelationIdFilter(logging.Filter):
    \"\"\"相関IDをログレコードに追加するフィルター\"\"\"
    
    def filter(self, record):
        record.correlation_id = correlation_id_var.get() or str(uuid.uuid4())
        return True
""",
                "context_manager": """
from contextlib import contextmanager
from contextvars import ContextVar
import uuid

@contextmanager
def correlation_context(correlation_id=None):
    \"\"\"相関IDコンテキストマネージャー\"\"\"
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    
    token = correlation_id_var.set(correlation_id)
    try:
        yield correlation_id
    finally:
        correlation_id_var.reset(token)
""",
                "middleware": f"""
async def correlation_middleware(request, call_next):
    # ヘッダーから相関IDを取得または生成
    correlation_id = request.headers.get('{header_name}')
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
    
    # コンテキストに設定
    correlation_id_var.set(correlation_id)
    
    # レスポンス処理
    response = await call_next(request)
    
    # レスポンスヘッダーに追加
    response.headers['{header_name}'] = correlation_id
    
    return response
"""
            }
            
            return {
                "success": True,
                "implementation": implementation
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to implement correlation: {str(e)}"
            }
            
    async def implement_sampling(self, sampling_config: Dict[str, Any]) -> Dict[str, Any]:
        """ログサンプリングを実装"""
        try:
            strategy = sampling_config.get("strategy", "probabilistic")
            rate = sampling_config.get("rate", 0.1)
            always_sample = sampling_config.get("always_sample", [])
            
            implementation = f"""
import logging
import random

class SamplingFilter(logging.Filter):
    \"\"\"確率的サンプリングを行うフィルター\"\"\"
    
    def __init__(self, sample_rate={rate}, always_sample={always_sample}):
        self.sample_rate = sample_rate
        self.always_sample = always_sample
        
    def filter(self, record):
        # 特定レベルは常にサンプリング
        if record.levelname in self.always_sample:
            return True
            
        # 確率的サンプリング
        return random.random() < self.sample_rate

# フィルターを追加
sampling_filter = SamplingFilter()
for handler in logging.getLogger().handlers:
    handler.addFilter(sampling_filter)
"""
            
            return {
                "success": True,
                "implementation": implementation
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to implement sampling: {str(e)}"
            }
            
    async def implement_sanitization(self, sanitization_config: Dict[str, Any]) -> Dict[str, Any]:
        """ログサニタイゼーションを実装"""
        try:
            patterns = sanitization_config.get("patterns", [])
            replacement = sanitization_config.get("replacement", "[REDACTED]")
            
            # パターンコードを生成
            pattern_code = "patterns = [\n"
            for pattern in patterns:
                pattern_code += f"    {{'name': '{pattern['name']}', 'regex': re.compile(r'{pattern['regex']}')}},\n"
            pattern_code += "]"
            
            implementation = {
                "filter": f"""
import logging
import re

class SanitizationFilter(logging.Filter):
    \"\"\"機密情報をサニタイズするフィルター\"\"\"
    
    def __init__(self):
        {pattern_code}
        self.patterns = patterns
        self.replacement = '{replacement}'
        
    def filter(self, record):
        # メッセージをサニタイズ
        message = record.getMessage()
        
        for pattern in self.patterns:
            message = re.sub(pattern['regex'], self.replacement, message)
            
        record.msg = message
        record.args = ()  # 引数をクリア
        
        return True
""",
                "code": f"""
# サニタイゼーションフィルターを追加
# re.subで機密情報を除去
sanitization_filter = SanitizationFilter()
for handler in logging.getLogger().handlers:
    handler.addFilter(sanitization_filter)
"""
            }
            
            return {
                "success": True,
                "implementation": implementation
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to implement sanitization: {str(e)}"
            }
            
    async def optimize_for_performance(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """パフォーマンス最適化を実装"""
        try:
            throughput = requirements.get("throughput", "1000 logs/second")
            use_async = requirements.get("async", True)
            use_buffering = requirements.get("buffering", True)
            
            # スループット数値を抽出
            throughput_match = re.search(r'(\d+)', throughput)
            target_throughput = int(throughput_match.group(1)) if throughput_match else 1000
            
            # バッファサイズを計算
            buffer_size = max(1000, target_throughput // 10)
            
            optimization = {
                "async_handler": use_async,
                "buffer_size": buffer_size,
                "estimated_throughput": target_throughput * 1.2,  # 20%マージン
                "implementation": ""
            }
            
            if use_async:
                optimization["implementation"] = f"""
import logging
from logging.handlers import QueueHandler, QueueListener
import queue

# 非同期ログ処理用のキュー
log_queue = queue.Queue(maxsize={buffer_size})

# 既存のハンドラーをキューリスナーに移動
existing_handlers = logging.getLogger().handlers[:]
for handler in existing_handlers:
    logging.getLogger().removeHandler(handler)

# キューハンドラーを追加
queue_handler = QueueHandler(log_queue)
logging.getLogger().addHandler(queue_handler)

# キューリスナーを開始
queue_listener = QueueListener(log_queue, *existing_handlers)
queue_listener.start()

# アプリケーション終了時にリスナーを停止
import atexit
atexit.register(queue_listener.stop)
"""
            
            return {
                "success": True,
                "optimization": optimization
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to optimize for performance: {str(e)}"
            }
            
    async def implement_complete_system(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """完全なログシステムを実装"""
        try:
            system = {
                "configuration": {},
                "handlers": {},
                "formatters": {},
                "filters": {},
                "integration_code": []
            }
            
            # 基本設定を生成
            config_result = await self.generate_config({
                "environment": requirements.get("environment", "production"),
                "output": requirements.get("outputs", ["file"]),
                "level": "INFO"
            })
            
            if config_result["success"]:
                system["configuration"] = config_result["config"]
                
            # 構造化ログが必要な場合
            if "structured_logging" in requirements.get("features", []):
                formatter_result = await self.create_formatter({
                    "type": "json",
                    "fields": {
                        "timestamp": "%(asctime)s",
                        "level": "%(levelname)s",
                        "logger": "%(name)s",
                        "message": "%(message)s"
                    }
                })
                if formatter_result["success"]:
                    system["formatters"]["json"] = formatter_result["formatter"]
                    
            # 相関IDが必要な場合
            if "correlation_id" in requirements.get("features", []):
                correlation_result = await self.implement_correlation({
                    "header_name": "X-Correlation-ID",
                    "generate_if_missing": True
                })
                if correlation_result["success"]:
                    system["filters"]["correlation_id"] = correlation_result["implementation"]
                    
            # ハンドラーを実装
            for output in requirements.get("outputs", ["file"]):
                if output == "file":
                    handler_result = await self.implement_handler({
                        "type": "rotating",
                        "filename": str(Path(requirements.get("log_dir", ".")) / "app.log"),
                        "max_bytes": 10485760,
                        "backup_count": 5
                    })
                    if handler_result["success"]:
                        system["handlers"]["file"] = handler_result["implementation"]
                        
                elif output == "elasticsearch":
                    handler_result = await self.implement_handler({
                        "type": "custom",
                        "class": "ElasticSearchHandler",
                        "params": {
                            "hosts": ["localhost:9200"],
                            "index": "application-logs"
                        }
                    })
                    if handler_result["success"]:
                        system["handlers"]["elasticsearch"] = handler_result["implementation"]
                        
            # 統合コードを生成
            system["integration_code"] = self._generate_integration_code(system)
            
            return {
                "success": True,
                "system": system
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to implement complete system: {str(e)}"
            }
            
    def _generate_integration_code(self, system: Dict[str, Any]) -> List[str]:
        """統合コードを生成"""
        code_parts = []
        
        # インポート
        code_parts.append("""
import logging
import logging.config
from pathlib import Path
""")
        
        # 設定適用
        code_parts.append("""
# ログ設定を適用
logging.config.dictConfig(logging_config)
""")
        
        # フィルター適用
        if system["filters"]:
            for name, filter_impl in system["filters"].items():
                if isinstance(filter_impl, dict) and "filter" in filter_impl:
                    code_parts.append(filter_impl["filter"])
                    
        # ハンドラー適用
        for name, handler_code in system["handlers"].items():
            if isinstance(handler_code, str):
                code_parts.append(handler_code)
                
        return code_parts
        
    async def perform_craft(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """ログシステム構築の具体的な作業を実行"""
        action = task_data.get("action")
        data = task_data.get("data", {})
        
        if action == "generate_config":
            return await self.generate_config(data)
        elif action == "implement_handler":
            return await self.implement_handler(data)
        elif action == "create_formatter":
            return await self.create_formatter(data)
        elif action == "analyze_patterns":
            return await self.analyze_patterns(data.get("log_samples", []))
        elif action == "suggest_improvements":
            return await self.suggest_improvements(
                data.get("current_config", {}),
                data.get("issues", [])
            )
        elif action == "integrate_framework":
            return await self.integrate_framework(data)
        elif action == "integrate_monitoring":
            return await self.integrate_monitoring(data)
        elif action == "implement_correlation":
            return await self.implement_correlation(data)
        elif action == "implement_sampling":
            return await self.implement_sampling(data)
        elif action == "implement_sanitization":
            return await self.implement_sanitization(data)
        elif action == "optimize_performance":
            return await self.optimize_for_performance(data)
        elif action == "implement_complete_system":
            return await self.implement_complete_system(data)
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }
            
    async def process_elder_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Elder Treeシステムからのメッセージを処理"""
        try:
            action = message.get("action")
            data = message.get("data", {})
            
            if action == "setup_logging":
                project = data.get("project", {})
                requirements = data.get("requirements", {})
                
                # プロジェクトタイプに基づいて設定
                system_requirements = {
                    "application": project.get("type", "fastapi"),
                    "environment": project.get("environment", "production"),
                    "features": [],
                    "outputs": ["file", "console"]
                }
                
                # 要件から機能を抽出
                if requirements.get("structured_logging"):
                    system_requirements["features"].append("structured_logging")
                if requirements.get("distributed_tracing"):
                    system_requirements["features"].append("correlation_id")
                    
                # 完全なシステムを実装
                result = await self.implement_complete_system(system_requirements)
                
                if not result["success"]:
                    return result
                    
                # Task Sageに通知
                await self.report_to_sage("task", {
                    "task": "logging_system_implemented",
                    "project": project["name"],
                    "features": system_requirements["features"]
                })
                
                return {
                    "success": True,
                    "data": {
                        "logging_config": result["system"]["configuration"],
                        "implementation_files": {
                            "logging_config.py": "\n".join(result["system"]["integration_code"]),
                            "handlers.py": "\n".join(result["system"]["handlers"].values()),
                            "formatters.py": "\n".join(str(f) for f in result["system"]["formatters"].values())
                        },
                        "sage_notified": True
                    }
                }
                
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process Elder message: {str(e)}"
            }


# エクスポート
__all__ = ["LoggingCrafterServant"]