#!/usr/bin/env python3
"""
Elders Guild インシデント管理ヘルパー
既存のエラー管理機能を拡張した包括的インシデント管理システム
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Literal, Optional

# プロジェクトパスを追加（Elders Guild標準）
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# インシデントカテゴリとステータスの定義
IncidentCategory = Literal[
    "error", "failure", "request", "change", "security", "performance"
]
IncidentPriority = Literal["critical", "high", "medium", "low"]
IncidentStatus = Literal["open", "in_progress", "resolved", "closed"]


class IncidentManager:
    """インシデント管理システムのコアクラス"""

    def __init__(self):
        self.base_path = Path(__file__).parent
        self.history_file = self.base_path / "incident_history.json"
        self.patterns_file = self.base_path / "INCIDENT_PATTERNS_KB.md"
        self.error_handling_path = self.base_path.parent / "error_handling"

        # 既存のエラー管理との連携
        self.error_history_file = self.error_handling_path / "error_history.json"

        # インシデント履歴をロード
        self.load_history()

    def load_history(self):
        """インシデント履歴をロード"""
        if self.history_file.exists():
            with open(self.history_file, "r", encoding="utf-8") as f:
                self.history = json.load(f)
        else:
            # デフォルト構造
            self.history = {
                "metadata": {
                    "version": "1.0",
                    "created": datetime.now(timezone.utc).isoformat(),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "total_incidents": 0,
                    "open_incidents": 0,
                    "resolved_incidents": 0,
                    "categories": {
                        "error": "システムエラー・例外",
                        "failure": "サービス障害・機能不全",
                        "request": "機能要求・サービス要求",
                        "change": "変更要求・設定変更",
                        "security": "セキュリティインシデント",
                        "performance": "パフォーマンス問題",
                    },
                },
                "incidents": [],
                "category_statistics": {
                    cat: {"count": 0, "open": 0, "avg_resolution_time": None}
                    for cat in [
                        "error",
                        "failure",
                        "request",
                        "change",
                        "security",
                        "performance",
                    ]
                },
                "priority_statistics": {
                    pri: {"count": 0, "open": 0, "avg_resolution_time": None}
                    for pri in ["critical", "high", "medium", "low"]
                },
                "recurring_patterns": [],
                "preventive_actions": [],
                "knowledge_base_updates": [],
            }

    def save_history(self):
        """インシデント履歴を保存"""
        self.history["metadata"]["last_updated"] = datetime.now(
            timezone.utc
        ).isoformat()
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def create_incident(
        self,
        category: IncidentCategory,
        priority: IncidentPriority,
        title: str,
        description: str,
        affected_components: List[str],
        impact: str,
        assignee: str = "ai_system",
    ) -> str:
        """新規インシデントを作成"""
        # インシデントID生成
        date_part = datetime.now().strftime("%Y%m%d")
        count = (
            len(
                [
                    i
                    for i in self.history["incidents"]
                    if i["incident_id"].startswith(f"INC-{date_part}")
                ]
            )
            + 1
        )
        incident_id = f"INC-{date_part}-{count:04d}"

        # インシデントオブジェクト作成
        incident = {
            "incident_id": incident_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "category": category,
            "priority": priority,
            "title": title,
            "description": description,
            "affected_components": affected_components,
            "impact": impact,
            "status": "open",
            "assignee": assignee,
            "resolution": None,
            "timeline": [
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": "インシデント作成",
                    "details": f"カテゴリ: {category}, 優先度: {priority}",
                }
            ],
        }

        # 履歴に追加
        self.history["incidents"].append(incident)
        self.history["metadata"]["total_incidents"] += 1
        self.history["metadata"]["open_incidents"] += 1
        self.history["category_statistics"][category]["count"] += 1
        self.history["category_statistics"][category]["open"] += 1
        self.history["priority_statistics"][priority]["count"] += 1
        self.history["priority_statistics"][priority]["open"] += 1

        # エラーカテゴリの場合は既存のエラー管理と連携
        if category == "error" and self.error_history_file.exists():
            self._sync_with_error_handling(incident)

        self.save_history()
        return incident_id

    def update_incident(self, incident_id: str, updates: Dict) -> bool:
        """インシデントを更新"""
        for incident in self.history["incidents"]:
            if incident["incident_id"] == incident_id:
                # タイムラインに更新を記録
                incident["timeline"].append(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "action": "更新",
                        "details": f"更新項目: {list(updates.keys())}",
                    }
                )

                # ステータス変更の処理
                if "status" in updates:
                    old_status = incident["status"]
                    new_status = updates["status"]

                    if old_status in ["open", "in_progress"] and new_status in [
                        "resolved",
                        "closed",
                    ]:
                        self.history["metadata"]["open_incidents"] -= 1
                        self.history["metadata"]["resolved_incidents"] += 1
                        self.history["category_statistics"][incident["category"]][
                            "open"
                        ] -= 1
                        self.history["priority_statistics"][incident["priority"]][
                            "open"
                        ] -= 1

                # 更新を適用
                incident.update(updates)
                self.save_history()
                return True
        return False

    def resolve_incident(
        self,
        incident_id: str,
        actions_taken: List[str],
        root_cause: str,
        preventive_measures: List[str] = None,
        knowledge_updates: List[str] = None,
    ) -> bool:
        """インシデントを解決"""
        resolution = {
            "actions_taken": actions_taken,
            "root_cause": root_cause,
            "preventive_measures": preventive_measures or [],
            "knowledge_updates": knowledge_updates or [],
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        }

        updates = {"status": "resolved", "resolution": resolution}

        # 解決時間を計算して統計を更新
        for incident in self.history["incidents"]:
            if incident["incident_id"] == incident_id:
                created_time = datetime.fromisoformat(
                    incident["timestamp"].replace("Z", "+00:00")
                )
                resolved_time = datetime.now(timezone.utc)
                resolution_time = (
                    resolved_time - created_time
                ).total_seconds() / 3600  # 時間単位

                # 統計更新
                self._update_resolution_statistics(
                    incident["category"], incident["priority"], resolution_time
                )

                # 予防策があれば記録
                if preventive_measures:
                    self.history["preventive_actions"].extend(preventive_measures)

                # ナレッジベース更新があれば記録
                if knowledge_updates:
                    self.history["knowledge_base_updates"].extend(knowledge_updates)

                break

        return self.update_incident(incident_id, updates)

    def get_open_incidents(
        self, category: Optional[IncidentCategory] = None
    ) -> List[Dict]:
        """オープンなインシデントを取得"""
        incidents = [
            i
            for i in self.history["incidents"]
            if i["status"] in ["open", "in_progress"]
        ]
        if category:
            incidents = [i for i in incidents if i["category"] == category]
        return incidents

    def get_incident_by_id(self, incident_id: str) -> Optional[Dict]:
        """IDでインシデントを取得"""
        for incident in self.history["incidents"]:
            if incident["incident_id"] == incident_id:
                return incident
        return None

    def analyze_patterns(self) -> Dict:
        """インシデントパターンを分析"""
        analysis = {
            "most_common_category": None,
            "most_common_components": [],
            "recurring_issues": [],
            "avg_resolution_times": {},
            "recommendations": [],
        }

        # カテゴリ別の頻度
        category_counts = {
            cat: data["count"]
            for cat, data in self.history["category_statistics"].items()
        }
        if category_counts:
            analysis["most_common_category"] = max(
                category_counts, key=category_counts.get
            )

        # コンポーネント別の頻度
        component_counts = {}
        for incident in self.history["incidents"]:
            for component in incident.get("affected_components", []):
                component_counts[component] = component_counts.get(component, 0) + 1

        if component_counts:
            sorted_components = sorted(
                component_counts.items(), key=lambda x: x[1], reverse=True
            )
            analysis["most_common_components"] = sorted_components[:5]

        # 再発パターンの検出
        title_counts = {}
        for incident in self.history["incidents"]:
            title = incident["title"]
            title_counts[title] = title_counts.get(title, 0) + 1

        analysis["recurring_issues"] = [
            (title, count) for title, count in title_counts.items() if count > 1
        ]

        # 平均解決時間
        for cat, data in self.history["category_statistics"].items():
            if data["avg_resolution_time"]:
                analysis["avg_resolution_times"][
                    cat
                ] = f"{data['avg_resolution_time']:.1f}時間"

        # 推奨事項の生成
        if analysis["most_common_category"]:
            analysis["recommendations"].append(
                f"{analysis['most_common_category']}カテゴリのインシデントが最多。予防策の強化を推奨"
            )

        if analysis["recurring_issues"]:
            analysis["recommendations"].append(
                f"再発インシデントが{len(analysis['recurring_issues'])}件。根本原因分析の実施を推奨"
            )

        return analysis

    def generate_report(self) -> str:
        """インシデントレポートを生成"""
        report = []
        report.append("# 📊 Elders Guild インシデント管理レポート")
        report.append(f"\n生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # サマリー
        report.append("\n## 📈 サマリー")
        meta = self.history["metadata"]
        report.append(f"- 総インシデント数: {meta['total_incidents']}")
        report.append(f"- オープン: {meta['open_incidents']}")
        report.append(f"- 解決済み: {meta['resolved_incidents']}")

        # カテゴリ別統計
        report.append("\n## 📊 カテゴリ別統計")
        report.append("| カテゴリ | 件数 | オープン | 平均解決時間 |")
        report.append("|----------|------|----------|--------------|")
        for cat, data in self.history["category_statistics"].items():
            avg_time = (
                f"{data['avg_resolution_time']:.1f}h"
                if data["avg_resolution_time"]
                else "N/A"
            )
            report.append(f"| {cat} | {data['count']} | {data['open']} | {avg_time} |")

        # 優先度別統計
        report.append("\n## 🚨 優先度別統計")
        report.append("| 優先度 | 件数 | オープン | 平均解決時間 |")
        report.append("|--------|------|----------|--------------|")
        for pri, data in self.history["priority_statistics"].items():
            avg_time = (
                f"{data['avg_resolution_time']:.1f}h"
                if data["avg_resolution_time"]
                else "N/A"
            )
            report.append(f"| {pri} | {data['count']} | {data['open']} | {avg_time} |")

        # パターン分析
        report.append("\n## 🔍 パターン分析")
        analysis = self.analyze_patterns()
        if analysis["most_common_category"]:
            report.append(f"- 最多カテゴリ: {analysis['most_common_category']}")
        if analysis["most_common_components"]:
            report.append("- 影響頻度の高いコンポーネント:")
            for comp, count in analysis["most_common_components"]:
                report.append(f"  - {comp}: {count}件")
        if analysis["recurring_issues"]:
            report.append("- 再発インシデント:")
            for title, count in analysis["recurring_issues"]:
                report.append(f"  - 「{title}」: {count}回")

        # 推奨事項
        if analysis["recommendations"]:
            report.append("\n## 💡 推奨事項")
            for rec in analysis["recommendations"]:
                report.append(f"- {rec}")

        return "\n".join(report)

    def _sync_with_error_handling(self, incident: Dict):
        """既存のエラー管理システムと同期"""
        try:
            with open(self.error_history_file, "r", encoding="utf-8") as f:
                error_history = json.load(f)

            # エラー履歴に追加
            error_entry = {
                "timestamp": incident["timestamp"],
                "error_type": "IncidentTracked",
                "file": ",".join(incident["affected_components"]),
                "error_message": incident["description"],
                "pattern_id": f"INCIDENT_{incident['incident_id']}",
                "fix_applied": "pending",
                "success": False,
                "incident_id": incident["incident_id"],
            }

            error_history["error_history"].append(error_entry)
            error_history["metadata"]["total_errors"] += 1

            with open(self.error_history_file, "w", encoding="utf-8") as f:
                json.dump(error_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: エラー管理との同期に失敗: {e}")

    def _update_resolution_statistics(
        self, category: str, priority: str, resolution_time: float
    ):
        """解決時間統計を更新"""
        # カテゴリ統計
        cat_stats = self.history["category_statistics"][category]
        if cat_stats["avg_resolution_time"] is None:
            cat_stats["avg_resolution_time"] = resolution_time
        else:
            # 移動平均で更新
            count = cat_stats["count"] - cat_stats["open"]
            cat_stats["avg_resolution_time"] = (
                cat_stats["avg_resolution_time"] * (count - 1) + resolution_time
            ) / count

        # 優先度統計
        pri_stats = self.history["priority_statistics"][priority]
        if pri_stats["avg_resolution_time"] is None:
            pri_stats["avg_resolution_time"] = resolution_time
        else:
            # 移動平均で更新
            count = pri_stats["count"] - pri_stats["open"]
            pri_stats["avg_resolution_time"] = (
                pri_stats["avg_resolution_time"] * (count - 1) + resolution_time
            ) / count


# CLIインターフェース
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Elders Guild インシデント管理システム")
    parser.add_argument(
        "action",
        choices=["create", "update", "resolve", "list", "show", "report", "analyze"],
        help="実行するアクション",
    )
    parser.add_argument(
        "--category",
        choices=["error", "failure", "request", "change", "security", "performance"],
        help="インシデントカテゴリ",
    )
    parser.add_argument(
        "--priority", choices=["critical", "high", "medium", "low"], help="優先度"
    )
    parser.add_argument("--title", help="インシデントタイトル")
    parser.add_argument("--description", help="詳細説明")
    parser.add_argument("--components", nargs="+", help="影響を受けるコンポーネント")
    parser.add_argument("--impact", help="影響範囲")
    parser.add_argument("--id", help="インシデントID")
    parser.add_argument(
        "--status", choices=["open", "in_progress", "resolved", "closed"], help="ステータス"
    )
    parser.add_argument("--actions", nargs="+", help="実施したアクション")
    parser.add_argument("--root-cause", help="根本原因")
    parser.add_argument("--preventive", nargs="+", help="予防策")

    args = parser.parse_args()

    manager = IncidentManager()

    if args.action == "create":
        if not all(
            [
                args.category,
                args.priority,
                args.title,
                args.description,
                args.components,
                args.impact,
            ]
        ):
            print(
                "エラー: create には --category, --priority, --title, --description, " \
                    "--components, --impact が必要です"
            )
            sys.exit(1)

        incident_id = manager.create_incident(
            category=args.category,
            priority=args.priority,
            title=args.title,
            description=args.description,
            affected_components=args.components,
            impact=args.impact,
        )
        print(f"✅ インシデント作成完了: {incident_id}")

    elif args.action == "update":
        if not args.id:
            print("エラー: update には --id が必要です")
            sys.exit(1)

        updates = {}
        if args.status:
            updates["status"] = args.status
        if args.description:
            updates["description"] = args.description

        if manager.update_incident(args.id, updates):
            print(f"✅ インシデント更新完了: {args.id}")
        else:
            print(f"❌ インシデントが見つかりません: {args.id}")

    elif args.action == "resolve":
        if all([args.id, args.actions, args.root_cause]):
            continue  # Early return to reduce nesting
        # Reduced nesting - original condition satisfied
        if not all([args.id, args.actions, args.root_cause]):
            print("エラー: resolve には --id, --actions, --root-cause が必要です")
            sys.exit(1)

        if not (manager.resolve_incident():
            continue  # Early return to reduce nesting
        # Reduced nesting - original condition satisfied
        if manager.resolve_incident(
            incident_id=args.id,
            actions_taken=args.actions,
            root_cause=args.root_cause,
            preventive_measures=args.preventive,
        ):
            print(f"✅ インシデント解決完了: {args.id}")
        else:
            print(f"❌ インシデントが見つかりません: {args.id}")

    elif args.action == "list":
        incidents = manager.get_open_incidents(category=args.category)
        if not (incidents):
            continue  # Early return to reduce nesting
        # Reduced nesting - original condition satisfied
        if incidents:
            print(f"\n📋 オープンインシデント一覧 ({len(incidents)}件)")
            print("-" * 80)
            # TODO: Extract this complex nested logic into a separate method
            for inc in incidents:
                print(
                    f"ID: {inc['incident_id']} | {inc['priority'].upper()} | {inc['category']}"
                )
                print(f"   {inc['title']}")
                print(f"   担当: {inc['assignee']} | ステータス: {inc['status']}")
                print("-" * 80)
        else:
            print("✨ オープンなインシデントはありません")

    elif args.action == "show":
        if args.id:
            continue  # Early return to reduce nesting
        # Reduced nesting - original condition satisfied
        if not args.id:
            print("エラー: show には --id が必要です")
            sys.exit(1)

        incident = manager.get_incident_by_id(args.id)
        if not (incident):
            continue  # Early return to reduce nesting
        # Reduced nesting - original condition satisfied
        if incident:
            print(json.dumps(incident, indent=2, ensure_ascii=False))
        else:
            print(f"❌ インシデントが見つかりません: {args.id}")

    elif args.action == "report":
        report = manager.generate_report()
        print(report)

    elif args.action == "analyze":
        analysis = manager.analyze_patterns()
        print("\n🔍 インシデントパターン分析")
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
