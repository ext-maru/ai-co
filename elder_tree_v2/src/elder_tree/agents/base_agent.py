"""
Elder Tree Base Agent
python-a2aを継承した基底エージェント実装
"""

from python_a2a import Agent, Message, Protocol
from typing import Dict, Any, Optional
import structlog
from prometheus_client import Counter, Histogram, Gauge
import time


class ElderTreeAgent(Agent):
    """
    Elder Tree用基底エージェント
    python-a2aのAgentクラスを拡張
    """
    
    def __init__(self, name: str, domain: str, port: Optional[int] = None, **kwargs):
        """
        初期化
        
        Args:
            name: エージェント名
            domain: ドメイン（knowledge, task, incident, rag）
            port: ポート番号（オプション）
        """
        super().__init__(name=name, port=port, **kwargs)
        
        self.domain = domain
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
        self.message_counter = Counter(
            'elder_tree_agent_messages_total',
            'Total messages processed',
            ['agent_name', 'message_type', 'status']
        )
        
        self.message_duration = Histogram(
            'elder_tree_agent_message_duration_seconds',
            'Message processing duration',
            ['agent_name', 'message_type']
        )
        
        self.active_connections = Gauge(
            'elder_tree_agent_active_connections',
            'Number of active connections',
            ['agent_name']
        )
    
    def _register_base_handlers(self):
        """基本メッセージハンドラー登録"""
        
        @self.on_message("health_check")
        async def handle_health_check(message: Message) -> Dict[str, Any]:
            """ヘルスチェック処理"""
            uptime = time.time() - self.start_time
            
            return {
                "status": "healthy",
                "agent": self.name,
                "domain": self.domain,
                "uptime_seconds": uptime,
                "version": "2.0.0"
            }
        
        @self.on_message("get_metrics")
        async def handle_get_metrics(message: Message) -> Dict[str, Any]:
            """メトリクス取得"""
            return {
                "agent": self.name,
                "metrics_endpoint": "/metrics",
                "total_messages": self.message_counter._value.get()
            }
    
    async def process_message(self, message: Message) -> Any:
        """
        メッセージ処理（メトリクス記録付き）
        
        Args:
            message: 処理するメッセージ
            
        Returns:
            処理結果
        """
        with self.message_duration.labels(
            agent_name=self.name,
            message_type=message.message_type
        ).time():
            try:
                # 親クラスのprocess_message呼び出し
                result = await super().process_message(message)
                
                # 成功カウント
                self.message_counter.labels(
                    agent_name=self.name,
                    message_type=message.message_type,
                    status="success"
                ).inc()
                
                return result
                
            except Exception as e:
                # エラーカウント
                self.message_counter.labels(
                    agent_name=self.name,
                    message_type=message.message_type,
                    status="error"
                ).inc()
                
                self.logger.error(
                    "Message processing failed",
                    message_type=message.message_type,
                    error=str(e)
                )
                raise
    
    async def collaborate_with_sage(self, sage_name: str, request: Dict[str, Any]) -> Message:
        """
        他の賢者との協調
        
        Args:
            sage_name: 協調先の賢者名
            request: リクエストデータ
            
        Returns:
            応答メッセージ
        """
        self.logger.info(
            "Collaborating with sage",
            target_sage=sage_name
        )
        
        return await self.send_message(
            target=sage_name,
            message_type="collaboration_request",
            data=request
        )
