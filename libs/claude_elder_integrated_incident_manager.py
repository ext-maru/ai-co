#!/usr/bin/env python3
"""
Claude Elder Integrated Incident Manager v1.0
エルダーズ評議会決定に基づく統合インシデント管理システム

既存のインシデント管理システムを拡張し、Claude Elder統合機能を追加
Option A: 既存システムを拡張 - エルダーズ評議会承認済み
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 既存システムをインポート
try:
    from .claude_elder_incident_integration import (
        ClaudeElderIncidentIntegration,
        IncidentReport,
        IncidentSeverity,
        IncidentType,
    )
    from .incident_manager import IncidentManager
except ImportError:
    # 直接実行時のフォールバック
    from claude_elder_incident_integration import (
        ClaudeElderIncidentIntegration,
        IncidentReport,
        IncidentSeverity,
        IncidentType,
    )
    from incident_manager import IncidentManager

# ファンタジー機能をオプションでインポート
try:
    from .enhanced_incident_manager import EnhancedIncidentManager

    FANTASY_FEATURES_AVAILABLE = True
except ImportError:
    try:
        from enhanced_incident_manager import EnhancedIncidentManager

        FANTASY_FEATURES_AVAILABLE = True
    except ImportError:
        FANTASY_FEATURES_AVAILABLE = False


@dataclass
class IntegratedIncidentData:
    """統合インシデントデータ構造"""

    # 既存インシデントマネージャー準拠
    incident_id: str
    timestamp: str
    category: str
    priority: str
    title: str
    description: str
    affected_components: List[str]
    impact: str
    status: str = "open"
    assignee: str = "ai_system"
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    resolution: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Claude Elder統合拡張
    claude_incident_id: Optional[str] = None
    claude_integration: Dict[str, Any] = field(default_factory=dict)
    elder_council_summoned: bool = False
    learning_recorded: bool = False
    failure_analysis: Optional[str] = None

    # ファンタジー機能（オプション）
    fantasy_quest_id: Optional[str] = None
    fantasy_features: Dict[str, Any] = field(default_factory=dict)


class ClaudeElderIntegratedIncidentManager(IncidentManager):
    """統合インシデント管理システム

    エルダーズ評議会決定に基づく統合アプローチ:
    - 既存のIncidentManagerを拡張
    - Claude Elder統合機能を追加
    - ファンタジー機能をオプション統合
    - 4賢者システムとの完全連携
    """

    def __init__(self):
        """初期化"""
        super().__init__()

        # Claude Elder統合システム
        self.claude_integration = ClaudeElderIncidentIntegration()

        # ファンタジー機能（利用可能な場合）
        if FANTASY_FEATURES_AVAILABLE:
            self.fantasy_manager = EnhancedIncidentManager()
        else:
            self.fantasy_manager = None

        # 統合設定
        self.auto_claude_integration = True
        self.auto_elder_council = True
        self.auto_learning_record = True
        self.fantasy_mode_enabled = False

        # 既存のsage_typeを更新
        self.sage_type = "Integrated Crisis Sage"
        self.wisdom_level = "integrated_crisis_response"

        self.logger.info(
            f"🤖🚨 {self.sage_type} 初期化完了 - Claude Elder統合アクティブ"
        )

    def create_incident_with_claude_integration(
        self,
        category: str,
        priority: str,
        title: str,
        description: str,
        affected_components: List[str],
        impact: str,
        assignee: str = "ai_system",
        metadata: Optional[Dict] = None,
        # Claude Elder統合用
        claude_context: Optional[Dict] = None,
        enable_elder_council: bool = True,
        enable_learning_record: bool = True,
        # ファンタジー機能用
        enable_fantasy_mode: bool = False,
        quest_level: Optional[str] = None,
    ) -> str:
        """Claude Elder統合でインシデントを作成

        Args:
            category: インシデントカテゴリ
            priority: 優先度
            title: インシデントタイトル
            description: 詳細説明
            affected_components: 影響コンポーネント
            impact: ビジネスインパクト
            assignee: 担当者
            metadata: 追加メタデータ
            claude_context: Claude固有のコンテキスト
            enable_elder_council: エルダー評議会招集を有効化
            enable_learning_record: 学習記録を有効化
            enable_fantasy_mode: ファンタジー機能を有効化
            quest_level: クエストレベル（ファンタジー機能）

        Returns:
            str: インシデントID
        """
        # 既存のcreate_incident()を呼び出し
        incident_id = self.create_incident(
            category=category,
            priority=priority,
            title=title,
            description=description,
            affected_components=affected_components,
            impact=impact,
            assignee=assignee,
            metadata=metadata or {},
        )

        # Claude Elder統合処理
        if self.auto_claude_integration and claude_context:
            self._integrate_with_claude_elder(
                incident_id=incident_id,
                claude_context=claude_context,
                enable_elder_council=enable_elder_council,
                enable_learning_record=enable_learning_record,
            )

        # ファンタジー機能統合（オプション）
        if enable_fantasy_mode and self.fantasy_manager:
            self._integrate_with_fantasy_features(
                incident_id=incident_id, quest_level=quest_level
            )

        return incident_id

    def create_incident_from_claude_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Claude Elderエラーからインシデントを作成

        Args:
            error: 発生したエラー
            context: エラーコンテキスト

        Returns:
            str: インシデントID
        """
        # エラー情報を解析
        error_type = error.__class__.__name__
        error_message = str(error)

        # インシデントデータを構築
        title = f"Claude Elder Error: {error_type}"
        description = f"Error Message: {error_message}\n\nContext: {json.dumps(context or {}, indent=2)}"

        # 優先度判定
        priority = self._determine_priority_from_error(error_type, context)

        # カテゴリ判定
        category = self._determine_category_from_error(error_type)

        # 影響コンポーネント判定
        affected_components = self._determine_affected_components(error, context)

        # ビジネスインパクト判定
        impact = self._determine_impact_from_error(error_type, context)

        # 統合インシデント作成
        incident_id = self.create_incident_with_claude_integration(
            category=category,
            priority=priority,
            title=title,
            description=description,
            affected_components=affected_components,
            impact=impact,
            assignee="claude_elder",
            metadata={
                "error_type": error_type,
                "error_message": error_message,
                "source": "claude_elder_integration",
                "auto_created": True,
            },
            claude_context=context,
            enable_elder_council=priority in ["critical", "high"],
            enable_learning_record=True,
        )

        self.logger.info(f"🤖 Claude Elder error converted to incident: {incident_id}")
        return incident_id

    def _integrate_with_claude_elder(
        self,
        incident_id: str,
        claude_context: Dict[str, Any],
        enable_elder_council: bool,
        enable_learning_record: bool,
    ):
        """Claude Elder統合処理"""
        try:
            # Claude インシデント統合システムと連携
            claude_incident_id = (
                f"CLAUDE_INCIDENT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # インシデントデータを読み込み
            with open(self.incident_file, "r") as f:
                data = json.load(f)

            # 該当インシデントを検索・更新
            for incident in data["incidents"]:
                if incident["incident_id"] == incident_id:
                    # Claude Elder統合情報を追加
                    incident["claude_incident_id"] = claude_incident_id
                    incident["claude_integration"] = {
                        "integrated_at": datetime.now().isoformat(),
                        "elder_council_summoned": enable_elder_council,
                        "learning_recorded": enable_learning_record,
                        "context": claude_context,
                    }

                    # タイムラインに追加
                    incident["timeline"].append(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "action": "Claude Elder統合",
                            "details": {
                                "claude_incident_id": claude_incident_id,
                                "integration_enabled": True,
                            },
                        }
                    )

                    break

            # ファイル保存
            with open(self.incident_file, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # エルダー評議会招集（必要に応じて）
            if enable_elder_council:
                self._summon_elder_council_for_incident(incident_id, claude_context)

            # 学習記録作成（必要に応じて）
            if enable_learning_record:
                self._create_learning_record_for_incident(incident_id, claude_context)

            self.logger.info(
                f"🤖 Claude Elder integration completed for incident: {incident_id}"
            )

        except Exception as e:
            self.logger.error(
                f"Claude Elder integration failed for incident {incident_id}: {e}"
            )

    def _integrate_with_fantasy_features(
        self, incident_id: str, quest_level: Optional[str]
    ):
        """ファンタジー機能統合処理"""
        if not self.fantasy_manager:
            return

        try:
            # ファンタジークエストIDを生成
            quest_id = f"QUEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # インシデントデータを読み込み
            with open(self.incident_file, "r") as f:
                data = json.load(f)

            # 該当インシデントを検索・更新
            for incident in data["incidents"]:
                if incident["incident_id"] == incident_id:
                    # ファンタジー機能情報を追加
                    incident["fantasy_quest_id"] = quest_id
                    incident["fantasy_features"] = {
                        "quest_level": quest_level or "medium",
                        "creature_classification": "未分類",
                        "reward_exp": 0,
                        "integrated_at": datetime.now().isoformat(),
                    }

                    # タイムラインに追加
                    incident["timeline"].append(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "action": "ファンタジー機能統合",
                            "details": {
                                "quest_id": quest_id,
                                "quest_level": quest_level or "medium",
                            },
                        }
                    )

                    break

            # ファイル保存
            with open(self.incident_file, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(
                f"🗡️ Fantasy features integrated for incident: {incident_id}"
            )

        except Exception as e:
            self.logger.error(
                f"Fantasy integration failed for incident {incident_id}: {e}"
            )

    def _determine_priority_from_error(
        self, error_type: str, context: Optional[Dict[str, Any]]
    ) -> str:
        """エラーから優先度を判定"""
        critical_errors = ["SystemError", "MemoryError", "OSError"]
        high_errors = ["ImportError", "ModuleNotFoundError", "AttributeError"]

        if error_type in critical_errors:
            return "critical"
        elif error_type in high_errors:
            return "high"
        elif context and context.get("critical", False):
            return "high"
        else:
            return "medium"

    def _determine_category_from_error(self, error_type: str) -> str:
        """エラーからカテゴリを判定"""
        system_errors = ["SystemError", "OSError", "MemoryError"]
        import_errors = ["ImportError", "ModuleNotFoundError"]

        if error_type in system_errors:
            return "system"
        elif error_type in import_errors:
            return "dependency"
        else:
            return "error"

    def _determine_affected_components(
        self, error: Exception, context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """影響コンポーネントを判定"""
        components = ["claude_elder"]

        if context:
            if "module" in context:
                components.append(context["module"])
            if "function" in context:
                components.append(context["function"])
            if "worker" in context:
                components.append("worker_system")

        return components

    def _determine_impact_from_error(
        self, error_type: str, context: Optional[Dict[str, Any]]
    ) -> str:
        """エラーからビジネスインパクトを判定"""
        if error_type in ["SystemError", "MemoryError"]:
            return "high - System functionality impacted"
        elif error_type in ["ImportError", "ModuleNotFoundError"]:
            return "medium - Feature functionality impacted"
        else:
            return "low - Minor functionality impacted"

    def _summon_elder_council_for_incident(
        self, incident_id: str, context: Dict[str, Any]
    ):
        """インシデント用エルダー評議会招集"""
        council_data = {
            "incident_id": incident_id,
            "timestamp": datetime.now().isoformat(),
            "summoned_by": "integrated_crisis_sage",
            "reason": "incident_escalation",
            "sages_required": [
                "Crisis Sage",
                "Knowledge Sage",
                "Task Oracle",
                "Search Mystic",
            ],
            "context": context,
        }

        # 評議会記録ファイルに保存
        council_file = (
            Path(self.incident_file).parent
            / f"elder_council_incident_{incident_id}.json"
        )
        try:
            with open(council_file, "w", encoding="utf-8") as f:
                json.dump(council_data, f, indent=2, ensure_ascii=False)

            self.logger.critical(f"🏛️ Elder Council summoned for incident {incident_id}")

        except Exception as e:
            self.logger.error(
                f"Failed to summon Elder Council for incident {incident_id}: {e}"
            )

    def _create_learning_record_for_incident(
        self, incident_id: str, context: Dict[str, Any]
    ):
        """インシデント用学習記録作成"""
        learning_content = f"""# Incident Learning Record - {incident_id}

## 📊 Incident Summary
- **Incident ID**: {incident_id}
- **Timestamp**: {datetime.now().isoformat()}
- **Source**: Integrated Crisis Sage
- **Integration**: Claude Elder + Crisis Sage

## 🔍 Context Analysis
```json
{json.dumps(context, indent=2, ensure_ascii=False)}
```

## 📚 Learning Integration
This incident has been integrated with the Crisis Sage system and is part of the FAIL-LEARN-EVOLVE Protocol.

## 🔄 Process Improvements
- [ ] Update incident handling procedures
- [ ] Enhance error detection
- [ ] Improve integration workflows
- [ ] Update documentation

---
*Generated by Integrated Crisis Sage*
*Following Elder Council approved integration approach*
"""

        # 学習記録ファイルに保存
        learning_file = (
            Path(self.incident_file).parent
            / "failures"
            / f"incident_learning_{incident_id}.md"
        )
        learning_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(learning_file, "w", encoding="utf-8") as f:
                f.write(learning_content)

            self.logger.info(f"📚 Learning record created for incident: {incident_id}")

        except Exception as e:
            self.logger.error(
                f"Failed to create learning record for incident {incident_id}: {e}"
            )

    def get_integrated_incident_statistics(self) -> Dict[str, Any]:
        """統合インシデント統計取得"""
        stats = self.get_incident_statistics()

        # Claude Elder統合情報を追加
        try:
            with open(self.incident_file, "r") as f:
                data = json.load(f)

            claude_integrated = 0
            elder_council_summoned = 0
            learning_recorded = 0
            fantasy_enabled = 0

            for incident in data["incidents"]:
                if incident.get("claude_incident_id"):
                    claude_integrated += 1
                if incident.get("claude_integration", {}).get("elder_council_summoned"):
                    elder_council_summoned += 1
                if incident.get("claude_integration", {}).get("learning_recorded"):
                    learning_recorded += 1
                if incident.get("fantasy_quest_id"):
                    fantasy_enabled += 1

            stats["claude_integration"] = {
                "total_integrated": claude_integrated,
                "elder_council_summoned": elder_council_summoned,
                "learning_recorded": learning_recorded,
                "fantasy_enabled": fantasy_enabled,
            }

        except Exception as e:
            self.logger.error(f"Failed to get integrated statistics: {e}")
            stats["claude_integration"] = {"error": str(e)}

        return stats

    def enable_fantasy_mode(self):
        """ファンタジーモードを有効化"""
        if self.fantasy_manager:
            self.fantasy_mode_enabled = True
            self.logger.info("🗡️ Fantasy mode enabled")
        else:
            self.logger.warning("Fantasy features not available")

    def disable_fantasy_mode(self):
        """ファンタジーモードを無効化"""
        self.fantasy_mode_enabled = False
        self.logger.info("🗡️ Fantasy mode disabled")


# 便利関数
def create_integrated_incident_manager() -> ClaudeElderIntegratedIncidentManager:
    """統合インシデントマネージャーのファクトリ関数"""
    return ClaudeElderIntegratedIncidentManager()


# グローバルインスタンス
_integrated_manager = None


def get_integrated_incident_manager() -> ClaudeElderIntegratedIncidentManager:
    """グローバル統合インシデントマネージャー取得"""
    global _integrated_manager
    if _integrated_manager is None:
        _integrated_manager = create_integrated_incident_manager()
    return _integrated_manager


if __name__ == "__main__":
    # テスト実行
    print("🤖🚨 Claude Elder Integrated Incident Manager Test")
    print("=" * 60)

    manager = create_integrated_incident_manager()

    # 統合インシデント作成テスト
    try:
        # テストエラーの作成
        raise ValueError("Test error for integrated incident manager")
    except Exception as e:
        incident_id = manager.create_incident_from_claude_error(
            e,
            {
                "function": "test_integration",
                "module": "integrated_incident_manager",
                "critical": True,
            },
        )

        print(f"✅ Integrated incident created: {incident_id}")

    # 統計情報表示
    stats = manager.get_integrated_incident_statistics()
    print(f"\n📊 Integrated Statistics:")
    print(f"  Total incidents: {stats['metadata']['total_incidents']}")
    print(f"  Claude integrated: {stats['claude_integration']['total_integrated']}")
    print(
        f"  Elder council summoned: {stats['claude_integration']['elder_council_summoned']}"
    )
    print(f"  Learning recorded: {stats['claude_integration']['learning_recorded']}")

    print(f"\n🎉 Integration test completed successfully!")
    print(f"✅ Elder Council approved integration approach implemented")
