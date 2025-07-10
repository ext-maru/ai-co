#!/usr/bin/env python3
"""
Elder Tree階層システム 異常検知アラートシステム
段階別アラートレベルによる監視と自動対応
"""

import asyncio
import json
import yaml
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict, deque
import os
import subprocess
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """アラートレベル"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class Alert:
    """アラート情報"""
    id: str
    name: str
    level: AlertLevel
    message: str
    timestamp: datetime
    component: str
    condition: str
    metrics: Dict[str, Any]
    actions_taken: List[str] = field(default_factory=list)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    auto_recovery_attempted: int = 0

@dataclass
class AlertRule:
    """アラートルール"""
    name: str
    level: AlertLevel
    condition: str
    message: str
    component: str
    actions: List[str]
    threshold_value: Optional[float] = None
    duration: Optional[int] = None  # seconds

class AlertConditionEvaluator:
    """アラート条件評価エンジン"""
    
    def __init__(self):
        self.metrics_history = defaultdict(lambda: deque(maxlen=300))  # 5分間の履歴
        self.condition_cache = {}
        
    def update_metrics(self, metrics: Dict[str, Any]):
        """メトリクスを更新"""
        timestamp = datetime.now()
        for key, value in metrics.items():
            self.metrics_history[key].append({
                'timestamp': timestamp,
                'value': value
            })
    
    def evaluate_condition(self, condition: str, current_metrics: Dict[str, Any]) -> bool:
        """条件を評価"""
        try:
            # 条件文字列を解析して評価
            # 例: "failed_workers > 16" or "avg_response_time > 1000ms for 60s"
            
            if " for " in condition:
                # 持続時間を含む条件
                base_condition, duration_str = condition.rsplit(" for ", 1)
                duration = self._parse_duration(duration_str)
                return self._evaluate_duration_condition(base_condition, duration, current_metrics)
            else:
                # 単純な条件
                return self._evaluate_simple_condition(condition, current_metrics)
                
        except Exception as e:
            logger.error(f"Condition evaluation error: {condition} - {e}")
            return False
    
    def _evaluate_simple_condition(self, condition: str, metrics: Dict[str, Any]) -> bool:
        """単純な条件を評価"""
        # 条件をパース（簡易実装）
        for op in ['>=', '<=', '>', '<', '==', '!=']:
            if op in condition:
                left, right = condition.split(op, 1)
                left = left.strip()
                right = right.strip()
                
                # メトリクス値を取得
                if left in metrics:
                    left_value = metrics[left]
                elif '.' in left:
                    # ネストされたメトリクス (例: grand_elder.status)
                    parts = left.split('.')
                    left_value = metrics
                    for part in parts:
                        if isinstance(left_value, dict) and part in left_value:
                            left_value = left_value[part]
                        else:
                            return False
                else:
                    return False
                
                # 右辺の値を解析
                right_value = self._parse_value(right)
                
                # 比較
                if op == '>':
                    return left_value > right_value
                elif op == '<':
                    return left_value < right_value
                elif op == '>=':
                    return left_value >= right_value
                elif op == '<=':
                    return left_value <= right_value
                elif op == '==':
                    return left_value == right_value
                elif op == '!=':
                    return left_value != right_value
        
        # OR条件
        if ' or ' in condition:
            conditions = condition.split(' or ')
            return any(self._evaluate_simple_condition(c.strip(), metrics) for c in conditions)
        
        # AND条件
        if ' and ' in condition:
            conditions = condition.split(' and ')
            return all(self._evaluate_simple_condition(c.strip(), metrics) for c in conditions)
        
        return False
    
    def _evaluate_duration_condition(self, condition: str, duration: int, metrics: Dict[str, Any]) -> bool:
        """持続時間を含む条件を評価"""
        # 指定された期間中、条件が継続して満たされているかチェック
        cutoff_time = datetime.now() - timedelta(seconds=duration)
        
        # 条件に関連するメトリクスを特定
        metric_name = condition.split()[0]
        if metric_name not in self.metrics_history:
            return False
        
        # 履歴から該当期間のデータを取得
        relevant_history = [
            entry for entry in self.metrics_history[metric_name]
            if entry['timestamp'] >= cutoff_time
        ]
        
        if not relevant_history:
            return False
        
        # すべての履歴エントリで条件が満たされているかチェック
        for entry in relevant_history:
            temp_metrics = metrics.copy()
            temp_metrics[metric_name] = entry['value']
            if not self._evaluate_simple_condition(condition, temp_metrics):
                return False
        
        return True
    
    def _parse_value(self, value_str: str) -> Any:
        """値文字列を適切な型に変換"""
        value_str = value_str.strip().strip("'\"")
        
        # 数値の単位を処理
        if value_str.endswith('%'):
            return float(value_str[:-1])
        elif value_str.endswith('ms'):
            return float(value_str[:-2])
        elif value_str.endswith('s'):
            return float(value_str[:-1]) * 1000  # ms に変換
        
        # 数値として解析
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            # 文字列として返す
            return value_str
    
    def _parse_duration(self, duration_str: str) -> int:
        """持続時間文字列を秒に変換"""
        duration_str = duration_str.strip()
        if duration_str.endswith('s'):
            return int(duration_str[:-1])
        elif duration_str.endswith('m'):
            return int(duration_str[:-1]) * 60
        elif duration_str.endswith('h'):
            return int(duration_str[:-1]) * 3600
        else:
            return int(duration_str)

class AlertManager:
    """アラート管理システム"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.evaluator = AlertConditionEvaluator()
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.suppressed_alerts: Set[str] = set()
        self.alert_rules: List[AlertRule] = self._load_alert_rules()
        
    def _load_config(self, config_path: str) -> Dict:
        """設定ファイルを読み込む"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _load_alert_rules(self) -> List[AlertRule]:
        """アラートルールを読み込む"""
        rules = []
        
        # 各カテゴリのアラートルールを読み込む
        for category in ['elder_tree_alerts', 'worker_alerts', 'four_sages_alerts', 'resource_alerts']:
            if category in self.config:
                for rule_name, rule_config in self.config[category].items():
                    rule = AlertRule(
                        name=rule_name,
                        level=AlertLevel(rule_config['level']),
                        condition=rule_config['condition'],
                        message=rule_config['message'],
                        component=category.replace('_alerts', ''),
                        actions=rule_config.get('actions', [])
                    )
                    rules.append(rule)
        
        return rules
    
    async def check_alerts(self, metrics: Dict[str, Any]):
        """アラートをチェック"""
        # メトリクスを更新
        self.evaluator.update_metrics(metrics)
        
        # 各ルールを評価
        for rule in self.alert_rules:
            try:
                if self.evaluator.evaluate_condition(rule.condition, metrics):
                    await self._trigger_alert(rule, metrics)
                else:
                    # 条件が満たされなくなった場合、アラートを解決
                    await self._resolve_alert(rule.name)
            except Exception as e:
                logger.error(f"Alert check error for {rule.name}: {e}")
    
    async def _trigger_alert(self, rule: AlertRule, metrics: Dict[str, Any]):
        """アラートをトリガー"""
        alert_id = f"{rule.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 既存のアクティブアラートをチェック
        if rule.name in self.active_alerts:
            # 既にアクティブな場合はスキップ
            return
        
        # 抑制ルールをチェック
        if self._is_suppressed(rule):
            self.suppressed_alerts.add(alert_id)
            return
        
        # アラートを作成
        alert = Alert(
            id=alert_id,
            name=rule.name,
            level=rule.level,
            message=rule.message,
            timestamp=datetime.now(),
            component=rule.component,
            condition=rule.condition,
            metrics=metrics.copy()
        )
        
        # アクティブアラートに追加
        self.active_alerts[rule.name] = alert
        self.alert_history.append(alert)
        
        logger.warning(f"Alert triggered: {rule.name} - {rule.message}")
        
        # 通知を送信
        await self._send_notifications(alert)
        
        # 自動アクションを実行
        if rule.actions:
            await self._execute_actions(alert, rule.actions)
    
    async def _resolve_alert(self, alert_name: str):
        """アラートを解決"""
        if alert_name in self.active_alerts:
            alert = self.active_alerts[alert_name]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            del self.active_alerts[alert_name]
            
            logger.info(f"Alert resolved: {alert_name}")
            
            # 解決通知を送信
            await self._send_resolution_notification(alert)
    
    def _is_suppressed(self, rule: AlertRule) -> bool:
        """アラートが抑制されているかチェック"""
        # 抑制ルールの実装
        for suppression_rule in self.config.get('suppression_rules', []):
            if suppression_rule['name'] == 'maintenance_window':
                # メンテナンスウィンドウのチェック
                if self._is_maintenance_window() and rule.level.value in suppression_rule['suppress']:
                    return True
            
            elif suppression_rule['name'] == 'duplicate_prevention':
                # 重複防止のチェック
                recent_alerts = [
                    a for a in self.alert_history
                    if a.name == rule.name and 
                    (datetime.now() - a.timestamp).total_seconds() < 300
                ]
                if recent_alerts:
                    return True
        
        return False
    
    def _is_maintenance_window(self) -> bool:
        """メンテナンスウィンドウかチェック"""
        # 実装は環境に応じて調整
        return False
    
    async def _send_notifications(self, alert: Alert):
        """通知を送信"""
        notification_config = self.config['alert_levels'][alert.level.value]['notification']
        
        for notification in notification_config:
            for channel, timing in notification.items():
                if timing == 'immediate':
                    await self._send_immediate_notification(alert, channel)
                elif timing == 'batch':
                    # バッチ通知はキューに追加
                    pass
    
    async def _send_immediate_notification(self, alert: Alert, channel: str):
        """即座に通知を送信"""
        try:
            if channel == 'slack':
                await self._send_slack_notification(alert)
            elif channel == 'email':
                await self._send_email_notification(alert)
            elif channel == 'pager':
                await self._send_pager_notification(alert)
        except Exception as e:
            logger.error(f"Notification send error ({channel}): {e}")
    
    async def _send_slack_notification(self, alert: Alert):
        """Slack通知を送信"""
        # 環境変数からWebhook URLを取得
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return
        
        # チャンネルを決定
        channel_config = self.config['notifications']['channels']['slack']
        if alert.level == AlertLevel.CRITICAL:
            channel = channel_config['critical_channel']
        elif alert.level == AlertLevel.HIGH:
            channel = channel_config['high_channel']
        else:
            channel = channel_config['default_channel']
        
        # メッセージを構築
        message = {
            "channel": channel,
            "username": "Elder Tree Alert System",
            "icon_emoji": self.config['alert_levels'][alert.level.value]['symbol'],
            "attachments": [{
                "color": self._get_alert_color(alert.level),
                "title": f"{alert.level.value.upper()}: {alert.name}",
                "text": alert.message,
                "fields": [
                    {"title": "Component", "value": alert.component, "short": True},
                    {"title": "Time", "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"), "short": True},
                    {"title": "Condition", "value": alert.condition, "short": False}
                ],
                "footer": "Elder Tree Monitoring",
                "ts": int(alert.timestamp.timestamp())
            }]
        }
        
        # Slackに送信
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=message) as response:
                if response.status != 200:
                    logger.error(f"Slack notification failed: {response.status}")
    
    async def _send_email_notification(self, alert: Alert):
        """メール通知を送信"""
        # 実装は環境に応じて調整
        pass
    
    async def _send_pager_notification(self, alert: Alert):
        """ページャー通知を送信"""
        # 実装は環境に応じて調整
        pass
    
    async def _send_resolution_notification(self, alert: Alert):
        """解決通知を送信"""
        # 解決通知の実装
        pass
    
    def _get_alert_color(self, level: AlertLevel) -> str:
        """アラートレベルに応じた色を取得"""
        colors = {
            AlertLevel.CRITICAL: "#FF0000",
            AlertLevel.HIGH: "#FF9800",
            AlertLevel.MEDIUM: "#FFEB3B",
            AlertLevel.LOW: "#4CAF50"
        }
        return colors.get(level, "#808080")
    
    async def _execute_actions(self, alert: Alert, actions: List[str]):
        """自動アクションを実行"""
        for action in actions:
            try:
                logger.info(f"Executing action: {action} for alert: {alert.name}")
                
                # アクションタイプに応じて実行
                if action == 'restart_worker':
                    await self._restart_worker(alert)
                elif action == 'notify_all_channels':
                    await self._notify_all_channels(alert)
                elif action == 'activate_emergency_protocol':
                    await self._activate_emergency_protocol(alert)
                elif action == 'attempt_auto_recovery':
                    await self._attempt_auto_recovery(alert)
                
                alert.actions_taken.append(action)
                
            except Exception as e:
                logger.error(f"Action execution error: {action} - {e}")
    
    async def _restart_worker(self, alert: Alert):
        """ワーカーを再起動"""
        # 実装は環境に応じて調整
        worker_id = alert.metrics.get('failed_worker_id')
        if worker_id:
            cmd = f"systemctl restart aicompany-worker@{worker_id}"
            subprocess.run(cmd, shell=True, check=True)
    
    async def _notify_all_channels(self, alert: Alert):
        """すべてのチャンネルに通知"""
        await asyncio.gather(
            self._send_slack_notification(alert),
            self._send_email_notification(alert),
            self._send_pager_notification(alert)
        )
    
    async def _activate_emergency_protocol(self, alert: Alert):
        """緊急プロトコルを有効化"""
        logger.critical(f"EMERGENCY PROTOCOL ACTIVATED: {alert.name}")
        # 緊急対応の実装
    
    async def _attempt_auto_recovery(self, alert: Alert):
        """自動回復を試行"""
        if not self.config['auto_recovery']['enabled']:
            return
        
        max_attempts = self.config['auto_recovery']['max_attempts']
        if alert.auto_recovery_attempted >= max_attempts:
            logger.warning(f"Auto recovery max attempts reached for {alert.name}")
            return
        
        alert.auto_recovery_attempted += 1
        
        # 回復アクションを実行
        # 実装は環境に応じて調整
        
    def get_dashboard_data(self) -> Dict[str, Any]:
        """ダッシュボード用のデータを取得"""
        return {
            "active_alerts": [
                {
                    "id": alert.id,
                    "name": alert.name,
                    "level": alert.level.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "component": alert.component,
                    "actions_taken": alert.actions_taken
                }
                for alert in self.active_alerts.values()
            ],
            "alert_summary": {
                "critical": len([a for a in self.active_alerts.values() if a.level == AlertLevel.CRITICAL]),
                "high": len([a for a in self.active_alerts.values() if a.level == AlertLevel.HIGH]),
                "medium": len([a for a in self.active_alerts.values() if a.level == AlertLevel.MEDIUM]),
                "low": len([a for a in self.active_alerts.values() if a.level == AlertLevel.LOW])
            },
            "recent_alerts": [
                {
                    "name": alert.name,
                    "level": alert.level.value,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved
                }
                for alert in sorted(self.alert_history[-10:], key=lambda a: a.timestamp, reverse=True)
            ]
        }

async def main():
    """メイン関数"""
    config_path = "/home/aicompany/ai_co/monitoring/alerts/alert_config.yaml"
    alert_manager = AlertManager(config_path)
    
    # テスト用のメトリクス
    test_metrics = {
        "grand_elder": {"status": "active"},
        "active_council_members": 8,
        "failed_workers": 2,
        "idle_workers": 10,
        "avg_worker_cpu": 45.2,
        "avg_worker_memory": 62.3,
        "system_cpu": 72.5,
        "system_memory": 68.4,
        "disk_free": 25.3,
        "avg_response_time": 234.5
    }
    
    # アラートチェックループ
    while True:
        try:
            await alert_manager.check_alerts(test_metrics)
            
            # ダッシュボードデータを保存
            dashboard_data = alert_manager.get_dashboard_data()
            output_path = Path("/home/aicompany/ai_co/monitoring/alerts/current_alerts.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dashboard_data, f, indent=2, default=str)
            
            await asyncio.sleep(10)  # 10秒ごとにチェック
            
        except Exception as e:
            logger.error(f"Alert system error: {e}")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())