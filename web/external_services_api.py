#!/usr/bin/env python3
"""
外部サービス統合 API
Slack, GitHub, Teams などの外部サービス連携
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
import asyncio
import aiohttp

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, Blueprint, jsonify, request
from libs.env_config import get_config

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Blueprint作成
external_api = Blueprint('external_api', __name__, url_prefix='/api/external')

# 設定読み込み
config = get_config()

class SlackIntegrationManager:
    """Slack統合マネージャー"""
    
    def __init__(self):
        self.webhook_url = getattr(config, 'SLACK_WEBHOOK_URL', '')
        self.bot_token = getattr(config, 'SLACK_BOT_TOKEN', '')
        self.channels = []
        self.is_connected = False
        self._test_connection()
    
    def _test_connection(self):
        """Slack接続テスト"""
        # 実際の接続テストは省略（本番では実装）
        self.is_connected = bool(self.webhook_url or self.bot_token)
        if self.is_connected:
            logger.info("Slack接続を確立しました")
        else:
            logger.warning("Slack接続情報が設定されていません")
    
    def send_message(self, channel: str, message: str, attachments: List[Dict] = None) -> Dict[str, Any]:
        """Slackメッセージ送信"""
        try:
            # 実際の送信処理（簡略版）
            payload = {
                "channel": channel,
                "text": message,
                "attachments": attachments or [],
                "timestamp": datetime.now().isoformat()
            }
            
            # ここで実際のSlack APIを呼び出す
            # 今回はモックレスポンス
            return {
                "success": True,
                "message_id": f"msg_{datetime.now().timestamp()}",
                "channel": channel,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Slackメッセージ送信エラー: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_channels(self) -> List[Dict[str, Any]]:
        """利用可能なチャンネル一覧取得"""
        # モックデータ
        return [
            {"id": "C001", "name": "general", "is_private": False},
            {"id": "C002", "name": "ai-company", "is_private": False},
            {"id": "C003", "name": "incidents", "is_private": False},
            {"id": "C004", "name": "dev-team", "is_private": True}
        ]
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Slack統合状態取得"""
        return {
            "service": "slack",
            "connected": self.is_connected,
            "features": {
                "messaging": True,
                "notifications": True,
                "slash_commands": True,
                "workflows": True
            },
            "channels_count": len(self.get_channels()),
            "last_activity": datetime.now().isoformat()
        }

class GitHubIntegrationManager:
    """GitHub統合マネージャー"""
    
    def __init__(self):
        self.token = getattr(config, 'GITHUB_TOKEN', '')
        self.org = getattr(config, 'GITHUB_ORG', 'ai-company')
        self.is_connected = bool(self.token)
    
    def get_repositories(self) -> List[Dict[str, Any]]:
        """リポジトリ一覧取得"""
        # モックデータ
        return [
            {
                "id": 1,
                "name": "ai-company-core",
                "full_name": f"{self.org}/ai-company-core",
                "private": True,
                "open_issues": 5,
                "open_prs": 3
            },
            {
                "id": 2,
                "name": "4sages-system",
                "full_name": f"{self.org}/4sages-system",
                "private": False,
                "open_issues": 2,
                "open_prs": 1
            }
        ]
    
    def create_issue(self, repo: str, title: str, body: str, labels: List[str] = None) -> Dict[str, Any]:
        """GitHub Issue作成"""
        try:
            # モック実装
            return {
                "success": True,
                "issue": {
                    "number": 123,
                    "title": title,
                    "state": "open",
                    "html_url": f"https://github.com/{self.org}/{repo}/issues/123",
                    "created_at": datetime.now().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"GitHub Issue作成エラー: {e}")
            return {"success": False, "error": str(e)}
    
    def get_integration_status(self) -> Dict[str, Any]:
        """GitHub統合状態取得"""
        return {
            "service": "github",
            "connected": self.is_connected,
            "features": {
                "issues": True,
                "pull_requests": True,
                "actions": True,
                "webhooks": True
            },
            "repositories_count": len(self.get_repositories()),
            "organization": self.org
        }

class TeamsIntegrationManager:
    """Microsoft Teams統合マネージャー"""
    
    def __init__(self):
        self.webhook_url = getattr(config, 'TEAMS_WEBHOOK_URL', '')
        self.tenant_id = getattr(config, 'TEAMS_TENANT_ID', '')
        self.is_connected = bool(self.webhook_url)
    
    def send_card(self, title: str, text: str, actions: List[Dict] = None) -> Dict[str, Any]:
        """Teams アダプティブカード送信"""
        try:
            # アダプティブカード形式
            card = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": title,
                "themeColor": "0078D7",
                "title": title,
                "text": text,
                "potentialAction": actions or []
            }
            
            # モック送信
            return {
                "success": True,
                "message_id": f"teams_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Teams カード送信エラー: {e}")
            return {"success": False, "error": str(e)}
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Teams統合状態取得"""
        return {
            "service": "teams",
            "connected": self.is_connected,
            "features": {
                "messaging": True,
                "adaptive_cards": True,
                "connectors": True,
                "apps": False
            },
            "tenant_id": self.tenant_id[:8] + "..." if self.tenant_id else None
        }

class WebhookManager:
    """Webhook管理システム"""
    
    def __init__(self):
        self.webhooks = []
        self.load_webhooks()
    
    def load_webhooks(self):
        """保存されたWebhook設定を読み込み"""
        # モックデータ
        self.webhooks = [
            {
                "id": "wh_001",
                "name": "Incident Alert",
                "url": "https://example.com/webhook/incidents",
                "events": ["incident.created", "incident.resolved"],
                "active": True,
                "created_at": "2025-07-09T10:00:00Z"
            },
            {
                "id": "wh_002", 
                "name": "Task Completion",
                "url": "https://example.com/webhook/tasks",
                "events": ["task.completed", "task.failed"],
                "active": True,
                "created_at": "2025-07-09T10:00:00Z"
            }
        ]
    
    def create_webhook(self, name: str, url: str, events: List[str]) -> Dict[str, Any]:
        """新規Webhook作成"""
        webhook = {
            "id": f"wh_{len(self.webhooks) + 1:03d}",
            "name": name,
            "url": url,
            "events": events,
            "active": True,
            "created_at": datetime.now().isoformat()
        }
        self.webhooks.append(webhook)
        return {"success": True, "webhook": webhook}
    
    def trigger_webhook(self, event: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Webhookトリガー"""
        results = []
        for webhook in self.webhooks:
            if webhook["active"] and event in webhook["events"]:
                # 実際の送信処理（モック）
                results.append({
                    "webhook_id": webhook["id"],
                    "status": "sent",
                    "timestamp": datetime.now().isoformat()
                })
        return results

# マネージャーインスタンス
slack_manager = SlackIntegrationManager()
github_manager = GitHubIntegrationManager()
teams_manager = TeamsIntegrationManager()
webhook_manager = WebhookManager()

# API エンドポイント

@external_api.route('/services/status')
def get_services_status():
    """外部サービス統合状態一覧"""
    try:
        services = {
            "slack": slack_manager.get_integration_status(),
            "github": github_manager.get_integration_status(),
            "teams": teams_manager.get_integration_status()
        }
        
        # 統合サマリー
        connected_count = sum(1 for s in services.values() if s["connected"])
        total_features = sum(len(s["features"]) for s in services.values())
        
        return jsonify({
            "success": True,
            "services": services,
            "summary": {
                "total_services": len(services),
                "connected_services": connected_count,
                "total_features": total_features
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"サービス状態取得エラー: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@external_api.route('/slack/send', methods=['POST'])
def send_slack_message():
    """Slackメッセージ送信"""
    try:
        data = request.json
        channel = data.get('channel', '#general')
        message = data.get('message', '')
        attachments = data.get('attachments', [])
        
        result = slack_manager.send_message(channel, message, attachments)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Slackメッセージ送信エラー: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@external_api.route('/slack/channels')
def get_slack_channels():
    """Slackチャンネル一覧取得"""
    try:
        channels = slack_manager.get_channels()
        return jsonify({
            "success": True,
            "channels": channels,
            "count": len(channels)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@external_api.route('/github/issues', methods=['POST'])
def create_github_issue():
    """GitHub Issue作成"""
    try:
        data = request.json
        repo = data.get('repository', 'ai-company-core')
        title = data.get('title', '')
        body = data.get('body', '')
        labels = data.get('labels', [])
        
        result = github_manager.create_issue(repo, title, body, labels)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"GitHub Issue作成エラー: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@external_api.route('/github/repositories')
def get_github_repositories():
    """GitHubリポジトリ一覧取得"""
    try:
        repos = github_manager.get_repositories()
        return jsonify({
            "success": True,
            "repositories": repos,
            "count": len(repos)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@external_api.route('/teams/card', methods=['POST'])
def send_teams_card():
    """Teams アダプティブカード送信"""
    try:
        data = request.json
        title = data.get('title', '')
        text = data.get('text', '')
        actions = data.get('actions', [])
        
        result = teams_manager.send_card(title, text, actions)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Teams カード送信エラー: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@external_api.route('/webhooks')
def get_webhooks():
    """Webhook一覧取得"""
    return jsonify({
        "success": True,
        "webhooks": webhook_manager.webhooks,
        "count": len(webhook_manager.webhooks)
    })

@external_api.route('/webhooks', methods=['POST'])
def create_webhook():
    """Webhook作成"""
    try:
        data = request.json
        name = data.get('name', '')
        url = data.get('url', '')
        events = data.get('events', [])
        
        result = webhook_manager.create_webhook(name, url, events)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@external_api.route('/webhooks/trigger', methods=['POST'])
def trigger_webhook():
    """Webhookトリガー"""
    try:
        data = request.json
        event = data.get('event', '')
        payload = data.get('data', {})
        
        results = webhook_manager.trigger_webhook(event, payload)
        return jsonify({
            "success": True,
            "triggered": len(results),
            "results": results
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    # テスト用実行
    app = Flask(__name__)
    app.register_blueprint(external_api)
    app.run(debug=True, port=5002)