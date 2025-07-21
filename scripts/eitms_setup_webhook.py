#!/usr/bin/env python3
"""
EITMS GitHub Webhook Setup Script
GitHubリポジトリにWebhookを自動設定
"""

import os
import sys
import json
import requests
from urllib.parse import urljoin

def setup_github_webhook():
    """GitHub Webhookの設定"""
    
    # 環境変数から設定を読み込み
    github_token = os.getenv('GITHUB_TOKEN')
    webhook_secret = os.getenv('GITHUB_WEBHOOK_SECRET', 'eitms-webhook-secret')
    webhook_url = os.getenv('EITMS_WEBHOOK_URL', 'http://localhost:8001/webhook')
    
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set")
        return False
    
    # リポジトリ情報
    owner = "aicompany"
    repo = "ai_co"
    
    # GitHub API URL
    api_url = f"https://api.github.com/repos/{owner}/{repo}/hooks"
    
    # Webhook設定
    webhook_config = {
        "name": "web",
        "active": True,
        "events": [
            "issues",
            "issue_comment",
            "pull_request",
            "pull_request_review",
            "pull_request_review_comment",
            "push",
            "release",
            "milestone",
            "project",
            "project_card",
            "project_column"
        ],
        "config": {
            "url": webhook_url,
            "content_type": "json",
            "secret": webhook_secret,
            "insecure_ssl": "0"
        }
    }
    
    # 既存のWebhookを確認
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        # 既存のWebhook一覧を取得
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        
        existing_webhooks = response.json()
        
        # EITMSのWebhookが既に存在するか確認
        eitms_webhook_exists = False
        for webhook in existing_webhooks:
            if webhook.get('config', {}).get('url') == webhook_url:
                eitms_webhook_exists = True
                print(f"EITMS webhook already exists: {webhook['id']}")
                
                # 設定を更新
                update_url = f"{api_url}/{webhook['id']}"
                response = requests.patch(update_url, json=webhook_config, headers=headers)
                response.raise_for_status()
                print("Webhook configuration updated successfully")
                break
        
        # 新規作成
        if not eitms_webhook_exists:
            response = requests.post(api_url, json=webhook_config, headers=headers)
            response.raise_for_status()
            webhook_data = response.json()
            print(f"Webhook created successfully: {webhook_data['id']}")
        
        print("\nWebhook Setup Complete!")
        print(f"URL: {webhook_url}")
        print(f"Events: {', '.join(webhook_config['events'])}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error setting up webhook: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False

def test_webhook():
    """Webhookのテスト"""
    print("\nTesting webhook connection...")
    
    webhook_url = os.getenv('EITMS_WEBHOOK_URL', 'http://localhost:8001/webhook')
    
    try:
        # ヘルスチェック
        health_url = webhook_url.replace('/webhook', '/health')
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            print(f"✓ EITMS GitHub Connector is running at {health_url}")
            return True
        else:
            print(f"✗ EITMS GitHub Connector returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to EITMS GitHub Connector: {e}")
        return False

def main():
    """メイン関数"""
    print("=== EITMS GitHub Webhook Setup ===\n")
    
    # Webhookエンドポイントの確認
    if not test_webhook():
        print("\nWarning: EITMS GitHub Connector is not running.")
        print("Please start EITMS first: ./scripts/eitms_start.sh")
        response = input("\nContinue anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    # Webhook設定
    if setup_github_webhook():
        print("\n✓ GitHub webhook configuration complete!")
        print("\nNext steps:")
        print("1. Ensure EITMS is running: ./scripts/eitms_start.sh")
        print("2. Create or update an issue in the repository to test")
        print("3. Check logs: tail -f logs/eitms_github_connector.log")
    else:
        print("\n✗ Failed to setup GitHub webhook")
        sys.exit(1)

if __name__ == "__main__":
    main()