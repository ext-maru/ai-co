#!/usr/bin/env python3
"""
インシデント管理とエラー管理の統合ブリッジ
既存のエラー履歴をインシデント管理システムに移行・同期
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

# 親ディレクトリのインポート
sys.path.append(str(Path(__file__).parent))
from incident_manager import IncidentManager


class ErrorIncidentBridge:
    """エラー管理とインシデント管理を橋渡しするクラス"""

    def __init__(self):
        self.incident_manager = IncidentManager()
        self.error_handling_path = Path(__file__).parent.parent / "error_handling"
        self.error_history_file = self.error_handling_path / "error_history.json"
        self.error_patterns_file = self.error_handling_path / "ERROR_PATTERNS_KB.md"

    def migrate_error_history(self):
        """既存のエラー履歴をインシデント管理に移行"""
        if not self.error_history_file.exists():
            print("エラー履歴ファイルが見つかりません")
            return

        with open(self.error_history_file, "r", encoding="utf-8") as f:
            error_history = json.load(f)

        migrated_count = 0
        for error in error_history.get("error_history", []):
            # 既に移行済みかチェック
            if "incident_id" in error:
                continue

            # エラーをインシデントとして作成
            incident_id = self.incident_manager.create_incident(
                category="error",
                priority=self._determine_priority(error),
                title=f"{error.get(
                    'error_type',
                    'Unknown Error')} in {error.get('file',
                    'unknown'
                )}",
                description=error.get("error_message", "No description"),
                affected_components=[error.get("file", "unknown")],
                impact="システムエラーによる処理中断",
                assignee="error_handler",
            )

            # エラーが解決済みの場合
            if error.get("success", False):
                self.incident_manager.resolve_incident(
                    incident_id=incident_id,
                    actions_taken=[error.get("fix_applied", "unknown fix")],
                    root_cause=f"Pattern: {error.get('pattern_id', 'unknown')}",
                    preventive_measures=[],
                )

            # 元のエラー履歴にインシデントIDを追記
            error["incident_id"] = incident_id
            migrated_count += 1

        # 更新したエラー履歴を保存
        with open(self.error_history_file, "w", encoding="utf-8") as f:
            json.dump(error_history, f, indent=2, ensure_ascii=False)

        print(f"✅ {migrated_count}件のエラーをインシデント管理に移行しました")

    def sync_new_errors(self):
        """新しいエラーを自動的にインシデントとして登録"""
        # この機能は diagnostic_helper.py などから呼び出される想定
        pass

    def _determine_priority(self, error: Dict) -> str:
        """エラーの内容から優先度を判定"""
        error_type = error.get("error_type", "").lower()
        pattern_id = error.get("pattern_id", "").lower()

        # Critical: システム停止につながるエラー
        if any(word in error_type for word in ["critical", "fatal", "crash"]):
            return "critical"

        # High: 重要な機能のエラー
        if any(
            word in error_type
            for word in ["connection", "permission", "authentication"]
        ):
            return "high"

        # Medium: 通常のエラー
        if any(word in error_type for word in ["error", "exception", "failed"]):
            return "medium"

        # Low: 警告レベル
        return "low"

    def generate_integrated_report(self) -> str:
        """エラー管理とインシデント管理の統合レポート"""
        report = []
        report.append("# 📊 Elders Guild 統合インシデント・エラー管理レポート")
        report.append(f"\n生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # インシデント管理の統計
        incident_report = self.incident_manager.generate_report()
        report.append("\n## 📋 インシデント管理")
        report.append(incident_report)

        # エラー管理の統計
        if self.error_history_file.exists():
            with open(self.error_history_file, "r", encoding="utf-8") as f:
                error_history = json.load(f)

            report.append("\n## 🔧 エラー管理統計")
            meta = error_history.get("metadata", {})
            report.append(f"- 総エラー数: {meta.get('total_errors', 0)}")
            report.append(f"- 解決済み: {meta.get('resolved_errors', 0)}")

            # パターン別統計
            report.append("\n### エラーパターン別統計")
            report.append("| パターン | 発生回数 | 解決率 |")
            report.append("|----------|----------|---------|")
            for pattern, stats in error_history.get("pattern_statistics", {}).items():
                count = stats.get("count", 0)
                rate = stats.get("resolution_rate", 0)
                report.append(f"| {pattern} | {count} | {rate}% |")

        return "\n".join(report)

    def check_error_incident_consistency(self):
        """エラー履歴とインシデント履歴の整合性チェック"""
        inconsistencies = []

        if self.error_history_file.exists():
            with open(self.error_history_file, "r", encoding="utf-8") as f:
                error_history = json.load(f)

            for error in error_history.get("error_history", []):
                if "incident_id" in error:
                    # インシデントが存在するか確認
                    incident = self.incident_manager.get_incident_by_id(
                        error["incident_id"]
                    )
                    if not incident:
                        inconsistencies.append(
                            {
                                "type": "missing_incident",
                                "error": error,
                                "message": f"エラーに記録されたインシデントID {error['incident_id']} が見つかりません",
                            }
                        )

        if inconsistencies:
            print(f"⚠️  {len(inconsistencies)}件の不整合が見つかりました")
            for inc in inconsistencies:
                print(f"  - {inc['message']}")
        else:
            print("✅ エラー履歴とインシデント履歴は整合しています")

        return inconsistencies


# 自動エラー登録フック（diagnostic_helper.pyから呼び出し可能）
def register_error_as_incident(error_data: Dict) -> str:
    """エラーを自動的にインシデントとして登録"""
    bridge = ErrorIncidentBridge()

    # エラーの重要度を判定
    priority = bridge._determine_priority(error_data)

    # インシデント作成
    incident_id = bridge.incident_manager.create_incident(
        category="error",
        priority=priority,
        title=f"{error_data.get(
            'error_type',
            'Unknown Error')} - {error_data.get('pattern_id',
            'NEW'
        )}",
        description=error_data.get("error_message", "No description"),
        affected_components=[error_data.get("file", "unknown")],
        impact="エラーによる処理中断",
        assignee="error_handler",
    )

    print(f"✅ エラーをインシデントとして登録: {incident_id}")
    return incident_id


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="エラー管理とインシデント管理の統合")
    parser.add_argument(
        "action", choices=["migrate", "report", "check"], help="実行するアクション"
    )

    args = parser.parse_args()
    bridge = ErrorIncidentBridge()

    if args.action == "migrate":
        bridge.migrate_error_history()
    elif args.action == "report":
        report = bridge.generate_integrated_report()
        print(report)
    elif args.action == "check":
        bridge.check_error_incident_consistency()
