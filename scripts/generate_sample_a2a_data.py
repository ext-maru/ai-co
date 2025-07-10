#!/usr/bin/env python3
"""
サンプルA2A通信データの生成
pgvector移行テスト用のデータ生成
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import os

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent

def generate_sample_data():
    """サンプルデータの生成"""
    
    # エージェントリスト
    agents = [
        "system-monitor", "task-scheduler", "error-handler", 
        "performance-analyzer", "security-scanner", "data-processor",
        "api-gateway", "cache-manager", "queue-worker", "log-aggregator",
        "health-checker", "metric-collector", "alert-manager", "backup-service",
        "config-manager", "deployment-agent", "test-runner", "code-analyzer"
    ]
    
    # メッセージタイプ
    message_types = [
        "status_update", "error_report", "performance_metric",
        "task_assignment", "task_completion", "alert_notification",
        "config_change", "health_check", "data_sync", "backup_status",
        "deployment_update", "test_result", "security_alert"
    ]
    
    # 通信データ生成
    communications = []
    base_time = datetime.now() - timedelta(days=7)
    
    for i in range(500):
        sender = random.choice(agents)
        receiver = random.choice([a for a in agents if a != sender])
        message_type = random.choice(message_types)
        
        # タイムスタンプ
        timestamp = base_time + timedelta(
            hours=random.randint(0, 168),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        
        # コンテンツ生成
        content = ""
        if message_type == "error_report":
            content = f"Error in {random.choice(['module_A', 'module_B', 'module_C'])}: {random.choice(['Connection timeout', 'Memory overflow', 'Invalid input', 'Permission denied'])}"
        elif message_type == "performance_metric":
            content = f"CPU: {random.randint(10, 90)}%, Memory: {random.randint(20, 80)}%, Response time: {random.randint(50, 500)}ms"
        elif message_type == "task_assignment":
            content = f"Task #{random.randint(1000, 9999)}: {random.choice(['Process data batch', 'Run backup', 'Execute test suite', 'Deploy update'])}"
        elif message_type == "alert_notification":
            content = f"Alert: {random.choice(['High CPU usage', 'Low disk space', 'Service degradation', 'Security threat detected'])}"
        else:
            content = f"{message_type} from {sender} to {receiver}"
        
        # メタデータ
        metadata = {
            "priority": random.choice(["low", "medium", "high", "critical"]),
            "status": random.choice(["success", "pending", "failed", "warning"]),
            "retry_count": random.randint(0, 3)
        }
        
        communication = {
            "id": f"comm_{i+1:04d}",
            "timestamp": timestamp.isoformat(),
            "sender": sender,
            "receiver": receiver,
            "type": message_type,
            "content": content,
            "metadata": metadata
        }
        
        communications.append(communication)
    
    # 異常パターン生成
    anomaly_patterns = []
    
    anomaly_types = [
        {
            "pattern": "system-overload",
            "type": "performance",
            "severity": "high",
            "description": "System experiencing high load with degraded performance"
        },
        {
            "pattern": "repeated-errors",
            "type": "error",
            "severity": "critical",
            "description": "Multiple error occurrences from the same component"
        },
        {
            "pattern": "security-breach-attempt",
            "type": "security",
            "severity": "critical",
            "description": "Potential security breach detected"
        },
        {
            "pattern": "service-unavailable",
            "type": "availability",
            "severity": "high",
            "description": "Critical service not responding"
        },
        {
            "pattern": "data-inconsistency",
            "type": "data",
            "severity": "medium",
            "description": "Data synchronization issues detected"
        },
        {
            "pattern": "resource-exhaustion",
            "type": "resource",
            "severity": "high",
            "description": "System resources approaching limits"
        },
        {
            "pattern": "network-latency",
            "type": "network",
            "severity": "medium",
            "description": "Abnormal network latency detected"
        },
        {
            "pattern": "authentication-failure",
            "type": "security",
            "severity": "high",
            "description": "Multiple authentication failures detected"
        },
        {
            "pattern": "deployment-failure",
            "type": "deployment",
            "severity": "high",
            "description": "Deployment process failed multiple times"
        },
        {
            "pattern": "backup-failure",
            "type": "backup",
            "severity": "medium",
            "description": "Backup operations not completing successfully"
        }
    ]
    
    for i, anomaly in enumerate(anomaly_types):
        pattern = {
            "id": f"anomaly_{i+1:03d}",
            "pattern": anomaly["pattern"],
            "type": anomaly["type"],
            "category": anomaly["type"],
            "severity": anomaly["severity"],
            "description": anomaly["description"],
            "count": random.randint(5, 50),
            "last_detected": (base_time + timedelta(hours=random.randint(0, 168))).isoformat(),
            "agents": random.sample(agents, k=random.randint(2, 5)),
            "keywords": anomaly["pattern"].split("-"),
            "threshold": random.uniform(0.6, 0.9)
        }
        anomaly_patterns.append(pattern)
    
    # 分析結果データ
    analysis_results = []
    
    for i in range(816):  # 元のログと同じ数
        agent_from = random.choice(agents)
        agent_to = random.choice([a for a in agents if a != agent_from])
        
        result = {
            "id": f"analysis_{i+1:04d}",
            "timestamp": (base_time + timedelta(minutes=random.randint(0, 10080))).isoformat(),
            "sender": agent_from,
            "receiver": agent_to,
            "flow": f"{agent_from} -> {agent_to}",
            "message_count": random.randint(1, 10),
            "is_anomaly": random.choice([True, False]) if i < 10 else False,
            "confidence": random.uniform(0.7, 0.99)
        }
        analysis_results.append(result)
    
    # データ保存
    data_dir = PROJECT_ROOT / "analysis_results"
    data_dir.mkdir(exist_ok=True)
    
    # 通信データ保存
    comm_file = data_dir / f"a2a_communications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(comm_file, 'w', encoding='utf-8') as f:
        json.dump(communications, f, indent=2, ensure_ascii=False)
    print(f"✅ Generated {len(communications)} communications: {comm_file}")
    
    # 異常パターン保存
    anomaly_file = data_dir / f"anomaly_patterns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(anomaly_file, 'w', encoding='utf-8') as f:
        json.dump(anomaly_patterns, f, indent=2, ensure_ascii=False)
    print(f"✅ Generated {len(anomaly_patterns)} anomaly patterns: {anomaly_file}")
    
    # 分析結果保存
    analysis_file = data_dir / f"semantic_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    print(f"✅ Generated {len(analysis_results)} analysis results: {analysis_file}")
    
    return {
        "communications": len(communications),
        "anomaly_patterns": len(anomaly_patterns),
        "analysis_results": len(analysis_results),
        "files": [str(comm_file), str(anomaly_file), str(analysis_file)]
    }

def main():
    """メイン処理"""
    print("🎲 Generating sample A2A data for pgvector migration...")
    print("=" * 60)
    
    result = generate_sample_data()
    
    print("\n📊 Summary:")
    print(f"- Communications: {result['communications']}")
    print(f"- Anomaly patterns: {result['anomaly_patterns']}")
    print(f"- Analysis results: {result['analysis_results']}")
    
    print("\n💾 Files created:")
    for file in result['files']:
        print(f"- {file}")
    
    print("\n✅ Sample data generation completed!")

if __name__ == "__main__":
    main()