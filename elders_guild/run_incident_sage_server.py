#!/usr/bin/env python3
"""
🚨 Incident Sage A2A Server - Flask分散実行
========================================

Elder Loop Phase 5: 実動作検証
Google A2A Protocol準拠のHTTPサーバー実装

Author: Claude Elder
Created: 2025-07-23
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from flask import Flask, request, jsonify
from typing import Dict, Any
from datetime import datetime
import uuid

# Elders Guildパス設定
sys.path.append(str(Path(__file__).parent))
from incident_sage.a2a_agent import IncidentSageAgent

# Flask App設定
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("incident_sage_server")

# グローバルエージェントインスタンス
incident_sage_agent = None

# 非同期ループ管理
loop = None


def get_or_create_event_loop():
    """イベントループ取得または作成"""
    global loop
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


async def initialize_agent():
    """エージェント初期化"""
    global incident_sage_agent
    try:
        logger.info("Initializing Incident Sage Agent...")
        incident_sage_agent = IncidentSageAgent()
        success = await incident_sage_agent.initialize()
        
        if success:
            logger.info("✅ Incident Sage Agent initialized successfully")
            
            # スキル情報表示
            skills_info = incident_sage_agent.get_skills_info()
            logger.info(f"📊 Agent Info:")
            logger.info(f"   - Agent Name: {skills_info['agent_name']}")
            logger.info(f"   - Total Skills: {skills_info['total_skills']}")
            logger.info(f"   - Categories: {json.dumps(skills_info['categories'], indent}")
        else:
            logger.error("❌ Failed to initialize Incident Sage Agent")
            
        return success
        
    except Exception as e:
        logger.error(f"💥 Agent initialization error: {e}")
        return False


@app.route('/', methods=['GET'])
def home():
    """ホームエンドポイント"""
    return jsonify({
        "service": "Incident Sage A2A Server",
        "status": "running" if incident_sage_agent else "initializing",
        "version": "1.0.0",
        "protocol": "Google A2A",
        "description": "Incident management and quality monitoring specialist",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/health', methods=['GET'])
def health():
    """ヘルスチェックエンドポイント"""
    health_status = {
        "status": "healthy" if incident_sage_agent else "unhealthy",
        "agent_initialized": incident_sage_agent is not None,
        "timestamp": datetime.now().isoformat()
    }
    
    # エージェントヘルスチェック
    if incident_sage_agent:
        try:
            loop = get_or_create_event_loop()
            from python_a2a import Message, MessageRole, TextContent
            
            health_message = Message(
                role=MessageRole.USER,
                content=TextContent(text="{}")
            )
            
            response = loop.run_until_complete(
                incident_sage_agent.health_check_skill(health_message)
            )
            
            response_data = json.loads(response.content.text)
            health_status["agent_health"] = response_data.get("data", {})
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            health_status["error"] = str(e)
    
    return jsonify(health_status)


@app.route('/a2a', methods=['POST'])
def a2a_endpoint():
    """A2A通信エンドポイント"""
    try:
        # リクエストデータ取得
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({
                "error": "Invalid request: No JSON data provided"
            }), 400
        
        # A2Aメッセージ構造確認
        messages = request_data.get("messages", [])
        if not messages:
            return jsonify({
                "error": "Invalid request: No messages provided"
            }), 400
        
        # 最後のユーザーメッセージ取得
        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg
                break
        
        if not user_message:
            return jsonify({
                "error": "Invalid request: No user message found"
            }), 400
        
        # メッセージ内容解析
        content = user_message.get("content", {})
        if isinstance(content, dict):
            text = content.get("text", "")
        else:
            text = str(content)
        
        # コマンド解析
        try:
            command_data = json.loads(text) if text.startswith("{") else {"query": text}
        except:
            command_data = {"query": text}
        
        # スキル判定とルーティング
        skill_name = determine_skill(command_data)
        
        logger.info(f"🎯 Routing to skill: {skill_name}")
        logger.info(f"📨 Command data: {json.dumps(command_data, ensure_ascii}")
        
        # スキル実行
        loop = get_or_create_event_loop()
        response = loop.run_until_complete(
            execute_skill(skill_name, command_data)
        )
        
        # A2Aレスポンス構築
        conversation_id = request_data.get("conversation_id", str(uuid.uuid4()))
        
        a2a_response = {
            "conversation_id": conversation_id,
            "messages": messages + [{
                "role": "assistant",
                "content": {
                    "type": "text",
                    "text": json.dumps(response, ensure_ascii=False)
                },
                "timestamp": datetime.now().isoformat()
            }],
            "metadata": {
                "skill_used": skill_name,
                "processing_time_ms": response.get("processing_time_ms", 0)
            }
        }
        
        return jsonify(a2a_response)
        
    except Exception as e:
        logger.error(f"A2A endpoint error: {e}")
        return jsonify({
            "error": f"Internal server error: {str(e)}"
        }), 500


def determine_skill(data: Dict[str, Any]) -> str:
    """コマンドデータからスキルを判定"""
    # 明示的スキル指定
    if "skill" in data:
        return data["skill"]
    
    # anomaly_dataがあればインシデント検知
    if "anomaly_data" in data:
        return "detect_incident"
    
    # incident_idベースの判定
    if "incident_id" in data:
        if "response" in data or "action" in data.get("query", "").lower():
            return "respond_to_incident"
        elif "remediat" in data.get("query", "").lower():
            return "attempt_automated_remediation"
    
    # standard_idがあれば品質評価
    if "standard_id" in data and "metrics" in data:
        return "assess_quality"
    
    # alert_ruleがあればアラート作成
    if "alert_rule" in data:
        return "create_alert_rule"
    
    # metricsのみの場合はアラート評価
    if "metrics" in data and not "standard_id" in data:
        return "evaluate_alert_rules"
    
    # targetがあれば監視対象登録
    if "target" in data:
        return "register_monitoring_target"
    
    # target_idがあればヘルスチェック
    if "target_id" in data:
        return "check_target_health"
    
    # queryベースの判定
    query = data.get("query", "").lower()
    
    if "statistic" in query or "stats" in query:
        return "get_statistics"
    elif "metric" in query or "operational" in query:
        return "get_operational_metrics"
    elif "pattern" in query or "learn" in query:
        return "learn_incident_patterns"
    elif "correlat" in query:
        return "analyze_correlations"
    elif "similar" in query or "search" in query:
        return "search_similar_incidents"
    elif "health" in query:
        return "health_check"
    
    # デフォルト
    return "health_check"


async def execute_skill(skill_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """スキル実行"""
    try:
        from python_a2a import Message, MessageRole, TextContent
        
        # メッセージ作成
        message = Message(
            role=MessageRole.USER,
            content=TextContent(text=json.dumps(data, ensure_ascii=False))
        )
        
        # スキルマッピング
        skill_map = {
            "detect_incident": incident_sage_agent.detect_incident_skill,
            "register_incident": incident_sage_agent.register_incident_skill,
            "respond_to_incident": incident_sage_agent.respond_to_incident_skill,
            "assess_quality": incident_sage_agent.assess_quality_skill,
            "register_quality_standard": incident_sage_agent.register_quality_standard_skill,
            "create_alert_rule": incident_sage_agent.create_alert_rule_skill,
            "evaluate_alert_rules": incident_sage_agent.evaluate_alert_rules_skill,
            "register_monitoring_target": incident_sage_agent.register_monitoring_target_skill,
            "check_target_health": incident_sage_agent.check_target_health_skill,
            "learn_incident_patterns": incident_sage_agent.learn_incident_patterns_skill,
            "analyze_correlations": incident_sage_agent.analyze_correlations_skill,
            "search_similar_incidents": incident_sage_agent.search_similar_incidents_skill,
            "attempt_automated_remediation": incident_sage_agent.attempt_automated_remediation_skill,
            "get_statistics": incident_sage_agent.get_statistics_skill,
            "get_operational_metrics": incident_sage_agent.get_operational_metrics_skill,
            "health_check": incident_sage_agent.health_check_skill
        }
        
        # スキル実行
        if skill_name in skill_map:
            response = await skill_map[skill_name](message)
            return json.loads(response.content.text)
        else:
            return {
                "success": False,
                "error": f"Unknown skill: {skill_name}"
            }
            
    except Exception as e:
        logger.error(f"Skill execution error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.route('/skills', methods=['GET'])
def list_skills():
    """利用可能スキル一覧"""
    if incident_sage_agent:
        return jsonify(incident_sage_agent.get_skills_info())
    else:
        return jsonify({
            "error": "Agent not initialized"
        }), 503


def main()logger.info("🚨 Starting Incident Sage A2A Server...")
"""メイン実行"""
    
    # エージェント初期化
    loop = get_or_create_event_loop()
    init_success = loop.run_until_complete(initialize_agent())
    
    if not init_success:
        logger.error("❌ Failed to initialize agent. Exiting.")
        sys.exit(1)
    
    # サーバー起動
    logger.info("🚀 Starting Flask server on port 8810.0..")
    logger.info("📡 A2A endpoint: http://localhost:8810/a2a")
    logger.info("🏥 Health check: http://localhost:8810/health")
    logger.info("📋 Skills list: http://localhost:8810/skills")
    
    try:
        app.run(
            host='0.0.0.0',
            port=8810,
            debug=False  # 本番モード
        )
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down Incident Sage A2A Server...")
        if incident_sage_agent:
            loop.run_until_complete(incident_sage_agent.shutdown())
    except Exception as e:
        logger.error(f"💥 Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()