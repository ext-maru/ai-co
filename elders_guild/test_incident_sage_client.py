#!/usr/bin/env python3
"""
🚨 Incident Sage A2A Client - 実通信テスト
=====================================

Elder Loop Phase 5: 分散通信実証
16スキル個別動作確認用クライアント

Author: Claude Elder
Created: 2025-07-23
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List


class IncidentSageTestClient:
    """Incident Sage A2Aテストクライアント"""
    
    def __init__(self, base_url: str = "http://localhost:8810"):
        self.base_url = base_url
        self.conversation_id = str(uuid.uuid4())
        self.messages = []
    
    def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        try:
            response = requests.get(f"{self.base_url}/health")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def list_skills(self) -> Dict[str, Any]:
        """スキル一覧取得"""
        try:
            response = requests.get(f"{self.base_url}/skills")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def send_a2a_request(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """A2Aリクエスト送信"""
        try:
            # ユーザーメッセージ追加
            user_message = {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": json.dumps(command_data, ensure_ascii=False)
                },
                "timestamp": datetime.now().isoformat()
            }
            self.messages.append(user_message)
            
            # A2Aリクエスト構築
            request_data = {
                "conversation_id": self.conversation_id,
                "messages": self.messages
            }
            
            # リクエスト送信
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/a2a",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            end_time = time.time()
            
            response_data = response.json()
            
            # レスポンスメッセージ取得
            if "messages" in response_data:
                self.messages = response_data["messages"]
                
                # 最新のアシスタントメッセージ取得
                for msg in reversed(response_data["messages"]):
                    if msg.get("role") == "assistant":
                        result = json.loads(msg["content"]["text"])
                        result["response_time_ms"] = int((end_time - start_time) * 1000)
                        return result
            
            return response_data
            
        except Exception as e:
            return {"error": str(e)}
    
    def test_all_skills(self):
        """全スキルテスト実行"""
        print("🚨 Incident Sage A2A Client - 全スキルテスト開始")
        print("=" * 70)
        
        # 1. ヘルスチェック
        print("\n🏥 ヘルスチェック...")
        health = self.health_check()
        print(f"   状態: {health.get('status', 'unknown')}")
        
        # 2. スキル一覧
        print("\n📋 利用可能スキル確認...")
        skills_info = self.list_skills()
        if "total_skills" in skills_info:
            print(f"   総スキル数: {skills_info['total_skills']}")
            print(f"   カテゴリ: {json.dumps(skills_info['categories'], indent=2)}")
        
        # 3. 各スキルテスト
        test_cases = [
            {
                "name": "インシデント検知",
                "data": {
                    "anomaly_data": {
                        "component": "payment_service",
                        "metric": "error_rate",
                        "value": 15.5,
                        "threshold": 10.0,
                        "severity": "critical",
                        "confidence": 0.95
                    }
                }
            },
            {
                "name": "品質評価",
                "data": {
                    "standard_id": "elder_guild_quality_standard_20250723000000",
                    "component": "api_gateway",
                    "metrics": {
                        "test_coverage": 92.5,
                        "iron_will_compliance": 100.0,
                        "code_quality_score": 88.0
                    }
                }
            },
            {
                "name": "アラートルール作成",
                "data": {
                    "alert_rule": {
                        "name": "High CPU Alert",
                        "description": "CPU使用率監視",
                        "condition_expression": "cpu_usage > 90.0",
                        "severity": "high",
                        "enabled": True
                    }
                }
            },
            {
                "name": "監視対象登録",
                "data": {
                    "target": {
                        "name": "Production API",
                        "type": "api_service",
                        "endpoint_url": "https://api.production.com",
                        "health_check_enabled": True
                    }
                }
            },
            {
                "name": "統計情報取得",
                "data": {
                    "query": "get statistics"
                }
            },
            {
                "name": "パターン学習",
                "data": {
                    "query": "learn incident patterns"
                }
            }
        ]
        
        print("\n🧪 スキルテスト実行:")
        print("-" * 70)
        
        for i, test_case in enumerate(test_cases):
            print(f"\n{i+1}. {test_case['name']}テスト")
            result = self.send_a2a_request(test_case['data'])
            
            if result.get("success"):
                print(f"   ✅ 成功 (応答時間: {result.get('response_time_ms', 0)}ms)")
                if "data" in result:
                    # 主要な結果を表示
                    data = result["data"]
                    if "incident_id" in data:
                        print(f"      - インシデントID: {data['incident_id']}")
                    if "assessment_id" in data:
                        print(f"      - 評価ID: {data['assessment_id']}")
                        print(f"      - 総合スコア: {data.get('overall_score', 0):.1f}%")
                    if "rule_id" in data:
                        print(f"      - ルールID: {data['rule_id']}")
                    if "target_id" in data:
                        print(f"      - 監視対象ID: {data['target_id']}")
            else:
                print(f"   ❌ 失敗: {result.get('error', 'Unknown error')}")
        
        # 4. 複雑なワークフローテスト
        print("\n\n🔄 複雑ワークフローテスト:")
        print("-" * 70)
        
        # インシデント検知→対応→修復フロー
        print("\n1. インシデント検知→対応→修復フロー")
        
        # 検知
        detection_result = self.send_a2a_request({
            "anomaly_data": {
                "component": "database_cluster",
                "metric": "connection_timeout",
                "severity": "critical",
                "value": 5000,
                "threshold": 1000
            }
        })
        
        if detection_result.get("success"):
            incident_id = detection_result["data"]["incident_id"]
            print(f"   ✅ インシデント検知: {incident_id}")
            
            # 対応
            response_result = self.send_a2a_request({
                "incident_id": incident_id,
                "query": "respond to incident"
            })
            
            if response_result.get("success"):
                print(f"   ✅ インシデント対応: {response_result['data']['response_status']}")
                
                # 自動修復
                remediation_result = self.send_a2a_request({
                    "incident_id": incident_id,
                    "query": "attempt automated remediation"
                })
                
                if remediation_result.get("success"):
                    print(f"   ✅ 自動修復: {remediation_result['data']['status']}")
        
        print("\n" + "=" * 70)
        print("🎯 全スキルテスト完了")


def main():
    """メイン実行"""
    client = IncidentSageTestClient()
    
    # サーバー起動待機
    print("⏳ サーバー起動を待機中...")
    for i in range(10):
        health = client.health_check()
        if health.get("status") == "healthy":
            print("✅ サーバー起動確認")
            break
        time.sleep(1)
    else:
        print("❌ サーバー起動タイムアウト")
        return
    
    # 全スキルテスト実行
    client.test_all_skills()


if __name__ == "__main__":
    main()