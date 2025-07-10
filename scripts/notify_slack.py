#!/usr/bin/env python3
"""Slack通知スクリプト"""
import json
import os
import sys
import urllib.request

status = sys.argv[1] if len(sys.argv) > 1 else "unknown"
webhook_url = os.getenv("SLACK_WEBHOOK_URL")

if webhook_url:
    message = {
        "text": f"🛡️ Incident Knights実行完了: {status}",
        "attachments": [
            {
                "color": "good" if status == "success" else "danger",
                "fields": [{"title": "Status", "value": status, "short": True}],
            }
        ],
    }

    req = urllib.request.Request(
        webhook_url, data=json.dumps(message).encode("utf-8"), headers={"Content-Type": "application/json"}
    )

    try:
        urllib.request.urlopen(req)
        print("Slack notification sent")
    except Exception as e:
        print(f"Failed to send Slack notification: {e}")
