"""
Elder Tree Base Agent
python-a2aを継承した基底エージェント実装
"""

from typing import Dict, Any, Optional
import structlog
from prometheus_client import Counter, Histogram, Gauge
import time
import asyncio
from flask import Flask, jsonify, request


class ElderTreeAgent:
    """
    Elder Tree用基底エージェント
    Flaskベースのシンプルな実装
    """
    
    def __init__(self, name: str, domain: str, port: Optional[int] = None):
        """
        初期化
        
        Args:
            name: エージェント名
            domain: ドメイン（knowledge, task, incident, rag）
            port: ポート番号（オプション）
        """
        self.name = name
        self.domain = domain
        self.port = port or 50000  # デフォルトポート
        self.start_time = time.time()
        
        # 構造化ログ
        self.logger = structlog.get_logger().bind(
            agent=name,
            domain=domain
        )
        
        # Prometheusメトリクス設定
        self._setup_metrics()
        
        # 基本ハンドラー登録
        self._register_base_handlers()
        
        self.logger.info("ElderTreeAgent initialized")
    
    def _setup_metrics(self):
        """Prometheusメトリクス設定"""
        agent_name = getattr(self, 'name', f'elder_agent_{id(self)}')
        
        self.message_counter = Counter(
            f'elder_tree_{agent_name}_messages_total',
            'Total messages processed',
            ['message_type', 'status']
        )
        
        self.message_duration = Histogram(
            f'elder_tree_{agent_name}_duration_seconds',
            'Message processing duration',
            ['message_type']
        )
        
        self.active_connections = Gauge(
            f'elder_tree_{agent_name}_connections',
            'Number of active connections'
        )
    
    def _register_base_handlers(self):
        """基本メッセージハンドラー登録"""
        pass  # A2AServerでは直接ハンドラー登録方法が異なる
    
    def create_app(self) -> Flask:
        """Flask appを作成"""
        app = Flask(self.name)
        
        # ヘルスチェックエンドポイント
        @app.route('/health')
        def health():
            return jsonify(self.get_health_status())
        
        # メトリクスエンドポイント
        @app.route('/metrics')
        def metrics():
            return jsonify(self.get_metrics_info())
        
        # メッセージ受信エンドポイント
        @app.route('/message', methods=['POST'])
        def receive_message():
            data = request.get_json()
            result = self.handle_message(data)
            return jsonify(result)
        
        return app
    
    def handle_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """メッセージハンドラー"""
        message_type = data.get('type', 'unknown')
        
        if message_type == "health_check":
            return self.get_health_status()
        elif message_type == "get_metrics":
            return self.get_metrics_info()
        else:
            return {"status": "error", "message": f"Unknown message type: {message_type}"}
    
    def get_health_status(self) -> Dict[str, Any]:
        """ヘルスチェック処理"""
        uptime = time.time() - self.start_time
        
        return {
            "status": "healthy",
            "agent": self.name,
            "domain": self.domain,
            "uptime_seconds": uptime,
            "version": "2.0.0"
        }
    
    def get_metrics_info(self) -> Dict[str, Any]:
        """メトリクス取得"""
        return {
            "agent": self.name,
            "metrics_endpoint": "/metrics",
            "active": True
        }
    
    def process_message_with_metrics(self, data: Dict[str, Any]) -> Any:
        """
        メッセージ処理（メトリクス記録付き）
        
        Args:
            data: 処理するメッセージデータ
            
        Returns:
            処理結果
        """
        message_type = data.get('type', 'unknown')
        
        with self.message_duration.labels(
            message_type=message_type
        ).time():
            try:
                # メッセージハンドラー呼び出し
                result = self.handle_message(data)
                
                # 成功カウント
                self.message_counter.labels(
                    message_type=message_type,
                    status="success"
                ).inc()
                
                return result
                
            except Exception as e:
                # エラーカウント
                self.message_counter.labels(
                    message_type=message_type,
                    status="error"
                ).inc()
                
                self.logger.error(
                    "Message processing failed",
                    message_type=message_type,
                    error=str(e)
                )
                raise
    
    def collaborate_with_sage(self, sage_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        他の賢者との協調
        
        Args:
            sage_name: 協調先の賢者名
            request: リクエストデータ
            
        Returns:
            応答データ
        """
        self.logger.info(
            "Collaborating with sage",
            target_sage=sage_name
        )
        
        # 実際の送信は実装する各賢者で個別に処理
        return {
            "status": "collaboration_initiated",
            "target": sage_name,
            "request": request
        }
