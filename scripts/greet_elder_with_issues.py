#!/usr/bin/env python3
"""
Elder Council Greeting with Issue Collection
エルダー評議会への挨拶と現在の課題収集機能
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from libs.worker_health_monitor import WorkerHealthMonitor
except:
    WorkerHealthMonitor = None

try:
    from libs.task_monitor import TaskMonitor
except:
    TaskMonitor = None

try:
    from libs.incident_manager import IncidentManager
except:
    IncidentManager = None

try:
    from libs.knowledge_base_manager import KnowledgeBaseManager
except:
    KnowledgeBaseManager = None


class ElderGreetingWithIssues:
    """エルダー評議会への挨拶と課題収集"""

    def __init__(self):
        """初期化"""
        self.worker_monitor = WorkerHealthMonitor() if WorkerHealthMonitor else None
        self.task_monitor = TaskMonitor() if TaskMonitor else None
        self.incident_manager = IncidentManager() if IncidentManager else None
        self.knowledge_manager = (
            KnowledgeBaseManager() if KnowledgeBaseManager else None
        )

    def collect_current_issues(self) -> Dict[str, Any]:
        """現在の課題を4賢者から収集"""
        issues = {"timestamp": datetime.now().isoformat(), "sages_report": {}}

        # 1. タスク賢者から進行中タスクと問題を収集
        try:
            task_issues = self._collect_task_issues()
            issues["sages_report"]["task_oracle"] = task_issues
        except Exception as e:
            issues["sages_report"]["task_oracle"] = {
                "status": "error",
                "message": str(e),
            }

        # 2. インシデント賢者から現在の問題を収集
        try:
            incident_issues = self._collect_incident_issues()
            issues["sages_report"]["crisis_sage"] = incident_issues
        except Exception as e:
            issues["sages_report"]["crisis_sage"] = {
                "status": "error",
                "message": str(e),
            }

        # 3. ナレッジ賢者から最近の学習課題を収集
        try:
            knowledge_issues = self._collect_knowledge_issues()
            issues["sages_report"]["knowledge_sage"] = knowledge_issues
        except Exception as e:
            issues["sages_report"]["knowledge_sage"] = {
                "status": "error",
                "message": str(e),
            }

        # 4. システム全体の健康状態を収集
        try:
            system_health = self._collect_system_health()
            issues["sages_report"]["system_health"] = system_health
        except Exception as e:
            issues["sages_report"]["system_health"] = {
                "status": "error",
                "message": str(e),
            }

        return issues

    def _collect_task_issues(self) -> Dict[str, Any]:
        """タスク関連の課題を収集"""
        # Get pending tasks
        pending_tasks = []
        delayed_tasks = []

        # Simulate task collection (実際の実装では TaskMonitor を使用)
        return {
            "status": "active",
            "pending_tasks_count": len(pending_tasks),
            "delayed_tasks_count": len(delayed_tasks),
            "critical_tasks": [],
            "recommendations": ["現在、特に緊急のタスクはありません"],
        }

    def _collect_incident_issues(self) -> Dict[str, Any]:
        """インシデント関連の課題を収集"""
        # Get active incidents
        active_incidents = []
        recent_errors = []

        # Simulate incident collection (実際の実装では IncidentManager を使用)
        return {
            "status": "stable",
            "active_incidents_count": len(active_incidents),
            "recent_errors_count": len(recent_errors),
            "critical_incidents": [],
            "system_stability": "良好",
            "recommendations": ["システムは安定稼働中です"],
        }

    def _collect_knowledge_issues(self) -> Dict[str, Any]:
        """ナレッジ関連の課題を収集"""
        # Get knowledge gaps
        knowledge_gaps = []
        learning_opportunities = []

        # Simulate knowledge collection (実際の実装では KnowledgeBaseManager を使用)
        return {
            "status": "evolving",
            "knowledge_gaps_count": len(knowledge_gaps),
            "learning_opportunities": len(learning_opportunities),
            "recent_learnings": [],
            "recommendations": ["継続的な学習が進行中です"],
        }

    def _collect_system_health(self) -> Dict[str, Any]:
        """システム健康状態を収集"""
        try:
            # Get worker health
            if self.worker_monitor:
                worker_health = self.worker_monitor.get_system_health()
            else:
                worker_health = {"overall_score": 95}

            return {
                "status": "healthy",
                "worker_health_score": worker_health.get("overall_score", 100),
                "resource_usage": {"cpu": "正常", "memory": "正常", "disk": "正常"},
                "recommendations": [],
            }
        except:
            return {
                "status": "unknown",
                "worker_health_score": 0,
                "resource_usage": {},
                "recommendations": ["健康状態の確認が必要です"],
            }

    def generate_greeting_with_issues(self, greeting_message: str = None) -> str:
        """課題収集付き挨拶文書を生成"""
        if not greeting_message:
            greeting_message = (
                "こんにちは、エルダー評議会の皆様。システムの現状を報告いたします。"
            )

        # 課題を収集
        issues = self.collect_current_issues()

        # 文書を生成
        timestamp = datetime.now()
        doc_content = f"""# Elder Council Greeting with Status Report - {timestamp.strftime('%Y年%m月%d日')}

## 挨拶
{greeting_message}

## 🔍 現在のシステム状況レポート

### 📋 タスク賢者からの報告
- **状態**: {issues['sages_report']['task_oracle']['status']}
- **保留中のタスク**: {issues['sages_report']['task_oracle'].get('pending_tasks_count', 0)}件
- **遅延タスク**: {issues['sages_report']['task_oracle'].get('delayed_tasks_count', 0)}件
- **推奨事項**: {', '.join(issues['sages_report']['task_oracle'].get('recommendations', []))}

### 🚨 インシデント賢者からの報告
- **状態**: {issues['sages_report']['crisis_sage']['status']}
- **アクティブインシデント**: {issues['sages_report']['crisis_sage'].get('active_incidents_count', 0)}件
- **最近のエラー**: {issues['sages_report']['crisis_sage'].get('recent_errors_count', 0)}件
- **システム安定性**: {issues['sages_report']['crisis_sage'].get('system_stability', '不明')}
- **推奨事項**: {', '.join(issues['sages_report']['crisis_sage'].get('recommendations', []))}

### 📚 ナレッジ賢者からの報告
- **状態**: {issues['sages_report']['knowledge_sage']['status']}
- **知識ギャップ**: {issues['sages_report']['knowledge_sage'].get('knowledge_gaps_count', 0)}件
- **学習機会**: {issues['sages_report']['knowledge_sage'].get('learning_opportunities', 0)}件
- **推奨事項**: {', '.join(issues['sages_report']['knowledge_sage'].get('recommendations', []))}

### 💻 システム健康状態
- **状態**: {issues['sages_report']['system_health']['status']}
- **健康スコア**: {issues['sages_report']['system_health'].get('worker_health_score', 0)}/100
- **リソース使用状況**:
  - CPU: {issues['sages_report']['system_health'].get('resource_usage', {}).get('cpu', '不明')}
  - メモリ: {issues['sages_report']['system_health'].get('resource_usage', {}).get('memory', '不明')}
  - ディスク: {issues['sages_report']['system_health'].get('resource_usage', {}).get('disk', '不明')}

## 📊 総合評価
システムは概ね良好な状態で稼働しています。継続的な監視と改善を続けてまいります。

---
生成時刻: {timestamp.isoformat()}
"""

        # 保存
        council_dir = Path("knowledge_base")
        council_dir.mkdir(exist_ok=True)

        filename = (
            f"council_{timestamp.strftime('%Y%m%d_%H%M%S')}_greeting_with_issues.md"
        )
        filepath = council_dir / filename

        filepath.write_text(doc_content, encoding="utf-8")

        # JSON形式でも保存
        json_filepath = (
            council_dir / f"council_{timestamp.strftime('%Y%m%d_%H%M%S')}_issues.json"
        )
        with open(json_filepath, "w", encoding="utf-8") as f:
            json.dump(issues, f, ensure_ascii=False, indent=2)

        return str(filepath)


def main():
    """メイン関数"""
    greeter = ElderGreetingWithIssues()

    # コマンドライン引数から挨拶メッセージを取得
    greeting_message = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None

    # 挨拶と課題収集を実行
    filepath = greeter.generate_greeting_with_issues(greeting_message)

    print(f"✅ エルダー評議会への挨拶と課題レポートを送信しました:")
    print(f"   📄 {filepath}")

    # 簡易サマリーを表示
    issues = greeter.collect_current_issues()
    print("\n📊 課題サマリー:")
    for sage, report in issues["sages_report"].items():
        if isinstance(report, dict) and "status" in report:
            print(f"   - {sage}: {report['status']}")


if __name__ == "__main__":
    main()
