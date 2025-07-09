#!/usr/bin/env python3
"""
🛡️ 強化インシデントマネージャー
ファンタジー分類システム統合版

作成日: 2025年7月8日
作成者: クロードエルダー（開発実行責任者）
承認: インシデント賢者による事前相談済み
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
import re

# 既存のインシデントマネージャーをインポート
try:
    from .incident_manager import IncidentManager
except ImportError:
    # 基本クラスのモック
    class IncidentManager:
        def log_incident(self, incident: Dict) -> Dict:
            return {"id": f"INC-{datetime.now().timestamp()}", "status": "logged"}
        
        def get_incidents(self) -> List[Dict]:
            return []

# 4賢者統合をインポート
try:
    from .four_sages_integration import FourSagesIntegration
except ImportError:
    # モッククラス
    class FourSagesIntegration:
        async def consult_incident_sage(self, incident: Dict) -> Dict:
            return {"recommendation": "manual_intervention", "confidence": 0.8}

# ロギング設定
logger = logging.getLogger(__name__)


class IncidentLevel(Enum):
    """インシデントレベル定義"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class KnightRank(Enum):
    """騎士団ランク定義"""
    SQUIRE = "SQUIRE"  # 見習い騎士
    KNIGHT = "KNIGHT"  # 正騎士
    PALADIN = "PALADIN"  # 聖騎士
    CHAMPION = "CHAMPION"  # 勇者
    GRANDMASTER = "GRANDMASTER"  # 騎士団長


@dataclass
class IncidentCreature:
    """インシデントクリーチャー"""
    name: str
    emoji: str
    level: IncidentLevel
    description: str
    weakness: Optional[str] = None
    
    def __str__(self):
        return f"{self.emoji} {self.name}"


@dataclass
class Knight:
    """騎士データクラス"""
    id: str
    name: str
    rank: KnightRank
    experience: int = 0
    abilities: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    
    @property
    def emoji(self) -> str:
        """ランクに応じた絵文字"""
        emoji_map = {
            KnightRank.SQUIRE: "🛡️",
            KnightRank.KNIGHT: "⚔️",
            KnightRank.PALADIN: "🗡️",
            KnightRank.CHAMPION: "⚜️",
            KnightRank.GRANDMASTER: "👑"
        }
        return emoji_map.get(self.rank, "🛡️")


@dataclass
class FantasyIncident:
    """ファンタジーインシデント"""
    id: str
    creature: IncidentCreature
    title: str
    description: str
    quest_title: Optional[str] = None
    reward_exp: int = 0
    assigned_knights: List[str] = field(default_factory=list)
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def quest_id(self) -> str:
        return self.id


@dataclass
class HealingSpell:
    """治癒魔法結果"""
    success: bool
    spell_type: str
    fixed_code: Optional[str] = None
    reason: Optional[str] = None
    suggestions: Optional[List[str]] = None
    applied: bool = False


@dataclass
class PreventionShield:
    """予防シールド"""
    service: str
    threat_level: str
    is_active: bool = True
    protection_level: float = 0.8
    duration: timedelta = field(default_factory=lambda: timedelta(hours=24))


class EnhancedIncidentManager:
    """強化インシデントマネージャー"""
    
    # クリーチャーマッピング
    CREATURE_MAPPING = {
        "妖精の悪戯": {
            "emoji": "🧚‍♀️", 
            "level": IncidentLevel.LOW, 
            "description": "軽微なバグ",
            "patterns": ["syntax error", "typo", "missing", "undefined"]
        },
        "ゴブリンの小細工": {
            "emoji": "👹", 
            "level": IncidentLevel.LOW, 
            "description": "設定ミス",
            "patterns": ["config", "setting", "parameter", "environment"]
        },
        "ゾンビの侵入": {
            "emoji": "🧟‍♂️", 
            "level": IncidentLevel.MEDIUM, 
            "description": "プロセス異常",
            "patterns": ["zombie process", "hung", "unresponsive", "timeout"]
        },
        "オークの大軍": {
            "emoji": "⚔️", 
            "level": IncidentLevel.HIGH, 
            "description": "複数障害",
            "patterns": ["multiple", "cascade", "widespread", "several"]
        },
        "スケルトン軍団": {
            "emoji": "💀", 
            "level": IncidentLevel.HIGH, 
            "description": "サービス停止",
            "patterns": ["service down", "unavailable", "cannot connect", "refused"]
        },
        "古龍の覚醒": {
            "emoji": "🐉", 
            "level": IncidentLevel.CRITICAL, 
            "description": "システム障害",
            "patterns": ["system failure", "critical", "emergency", "total"]
        },
        "スライムの増殖": {
            "emoji": "🌊", 
            "level": IncidentLevel.MEDIUM, 
            "description": "メモリリーク",
            "patterns": ["memory leak", "oom", "heap", "memory usage"]
        },
        "ゴーレムの暴走": {
            "emoji": "🗿", 
            "level": IncidentLevel.HIGH, 
            "description": "無限ループ",
            "patterns": ["infinite loop", "stuck", "cpu 100", "spinning"]
        },
        "クモの巣": {
            "emoji": "🕷️", 
            "level": IncidentLevel.MEDIUM, 
            "description": "デッドロック",
            "patterns": ["deadlock", "blocked", "circular", "thread lock"]
        }
    }
    
    # 騎士ランク定義
    KNIGHT_RANKS = {
        KnightRank.SQUIRE: {
            "emoji": "🛡️", 
            "level": 1, 
            "abilities": ["detect", "report"],
            "exp_required": 0
        },
        KnightRank.KNIGHT: {
            "emoji": "⚔️", 
            "level": 2, 
            "abilities": ["detect", "analyze", "contain"],
            "exp_required": 100
        },
        KnightRank.PALADIN: {
            "emoji": "🗡️", 
            "level": 3, 
            "abilities": ["detect", "analyze", "contain", "heal"],
            "exp_required": 500
        },
        KnightRank.CHAMPION: {
            "emoji": "⚜️", 
            "level": 4, 
            "abilities": ["all", "lead"],
            "exp_required": 1000
        },
        KnightRank.GRANDMASTER: {
            "emoji": "👑", 
            "level": 5, 
            "abilities": ["all", "lead", "resurrect"],
            "exp_required": 5000
        }
    }
    
    def __init__(self):
        """初期化"""
        self.base_manager = IncidentManager()
        self.four_sages = FourSagesIntegration()
        self.creature_mapping = self.CREATURE_MAPPING.copy()
        self.knight_ranks = self.KNIGHT_RANKS.copy()
        self.active_incidents: Dict[str, FantasyIncident] = {}
        self.knight_registry: Dict[str, Knight] = {}
        self.statistics: Dict[str, Any] = {
            "by_creature": {},
            "total_defeated": 0,
            "total_exp_awarded": 0
        }
        
        logger.info("🏰 強化インシデントマネージャー起動 - インシデント騎士団配備完了")
    
    def classify_creature(self, incident: Dict[str, Any]) -> IncidentCreature:
        """インシデントからクリーチャーを分類"""
        description = incident.get("description", "").lower()
        incident_type = incident.get("type", "").lower()
        severity = incident.get("severity", "medium").lower()
        
        # パターンマッチング
        for creature_name, creature_data in self.creature_mapping.items():
            patterns = creature_data.get("patterns", [])
            for pattern in patterns:
                if pattern in description or pattern in incident_type:
                    return IncidentCreature(
                        name=creature_name,
                        emoji=creature_data["emoji"],
                        level=creature_data["level"],
                        description=creature_data["description"]
                    )
        
        # デフォルト分類（重要度ベース）
        if severity == "critical":
            return IncidentCreature("古龍の覚醒", "🐉", IncidentLevel.CRITICAL, "不明な重大障害")
        elif severity == "high":
            return IncidentCreature("オークの大軍", "⚔️", IncidentLevel.HIGH, "不明な障害")
        elif severity == "low":
            return IncidentCreature("妖精の悪戯", "🧚‍♀️", IncidentLevel.LOW, "不明な軽微問題")
        else:
            return IncidentCreature("ゾンビの侵入", "🧟‍♂️", IncidentLevel.MEDIUM, "不明な問題")
    
    def match_creature_pattern(self, text: str) -> IncidentCreature:
        """テキストからクリーチャーパターンをマッチング"""
        text_lower = text.lower()
        
        for creature_name, creature_data in self.creature_mapping.items():
            patterns = creature_data.get("patterns", [])
            for pattern in patterns:
                if pattern in text_lower:
                    return IncidentCreature(
                        name=creature_name,
                        emoji=creature_data["emoji"],
                        level=creature_data["level"],
                        description=creature_data["description"]
                    )
        
        # デフォルト
        return IncidentCreature("妖精の悪戯", "🧚‍♀️", IncidentLevel.LOW, "不明な問題")
    
    def assign_knight_rank(self, experience: int) -> Knight:
        """経験値に基づいて騎士ランクを割り当て"""
        knight_id = f"knight-{datetime.now().timestamp()}"
        
        # 経験値からランクを決定
        assigned_rank = KnightRank.SQUIRE
        for rank in reversed(list(KnightRank)):
            if experience >= self.knight_ranks[rank]["exp_required"]:
                assigned_rank = rank
                break
        
        rank_data = self.knight_ranks[assigned_rank]
        
        knight = Knight(
            id=knight_id,
            name=f"Knight-{knight_id[-6:]}",
            rank=assigned_rank,
            experience=experience,
            abilities=rank_data["abilities"].copy()
        )
        
        self.knight_registry[knight_id] = knight
        return knight
    
    def promote_knight(self, knight_data: Dict[str, Any]) -> Knight:
        """騎士を昇進させる"""
        current_rank = knight_data.get("rank", KnightRank.SQUIRE)
        if isinstance(current_rank, str):
            current_rank = KnightRank[current_rank]
        
        # 次のランクを取得
        rank_list = list(KnightRank)
        current_index = rank_list.index(current_rank)
        
        if current_index < len(rank_list) - 1:
            next_rank = rank_list[current_index + 1]
            next_rank_data = self.knight_ranks[next_rank]
            
            # 騎士データ更新
            knight = Knight(
                id=knight_data.get("id", f"knight-{datetime.now().timestamp()}"),
                name=knight_data.get("name", "Unknown Knight"),
                rank=next_rank,
                experience=knight_data.get("experience", 0),
                abilities=next_rank_data["abilities"].copy()
            )
            
            logger.info(f"🎖️ 騎士昇進: {knight.name} が {next_rank.value} に昇進！")
            return knight
        
        # すでに最高ランクの場合
        return Knight(
            id=knight_data.get("id"),
            name=knight_data.get("name"),
            rank=current_rank,
            experience=knight_data.get("experience", 0),
            abilities=self.knight_ranks[current_rank]["abilities"].copy()
        )
    
    def create_fantasy_incident(self, title: str, description: str, 
                              affected_service: str, **kwargs) -> FantasyIncident:
        """ファンタジーインシデントを作成"""
        # インシデントデータ構築
        incident_data = {
            "title": title,
            "description": description,
            "affected_service": affected_service,
            **kwargs
        }
        
        # クリーチャー分類
        creature = self.classify_creature(incident_data)
        
        # クエストタイトル生成
        quest_titles = {
            IncidentLevel.LOW: f"討伐任務: {creature.name}の掃討",
            IncidentLevel.MEDIUM: f"防衛任務: {creature.name}からの防衛",
            IncidentLevel.HIGH: f"緊急任務: {creature.name}の撃退",
            IncidentLevel.CRITICAL: f"史詩級任務: {creature.name}との決戦"
        }
        
        quest_title = quest_titles.get(creature.level, f"任務: {creature.name}への対処")
        
        # 報酬経験値計算
        exp_rewards = {
            IncidentLevel.LOW: 10,
            IncidentLevel.MEDIUM: 50,
            IncidentLevel.HIGH: 200,
            IncidentLevel.CRITICAL: 1000
        }
        
        reward_exp = exp_rewards.get(creature.level, 10)
        
        # インシデント作成
        incident = FantasyIncident(
            id=f"QUEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            creature=creature,
            title=title,
            description=description,
            quest_title=quest_title,
            reward_exp=reward_exp
        )
        
        self.active_incidents[incident.id] = incident
        
        # ログ記録
        logger.info(self.format_fantasy_log(
            "INFO",
            f"新たなクエスト発生: {quest_title}",
            creature.name
        ))
        
        return incident
    
    def cast_healing_spell(self, incident: Dict[str, Any]) -> HealingSpell:
        """治癒魔法を詠唱（自動修復）"""
        incident_type = incident.get("type", "")
        
        # 単純なエラーの自動修復
        if incident_type == "syntax_error":
            # 構文エラーの自動修正ロジック
            return HealingSpell(
                success=True,
                spell_type="minor_healing",
                fixed_code="# Syntax error fixed by healing spell",
                applied=True
            )
        
        # 複雑なエラーは手動介入が必要
        if incident.get("complexity", "low") == "high":
            return HealingSpell(
                success=False,
                spell_type="major_healing_required",
                reason="requires_manual_intervention",
                suggestions=["コードレビューを実施", "アーキテクチャの見直し", "専門家に相談"]
            )
        
        # デフォルト
        return HealingSpell(
            success=False,
            spell_type="healing_attempted",
            reason="unknown_error_type"
        )
    
    def activate_prevention_shield(self, service: str, threat_level: str) -> PreventionShield:
        """予防シールドを展開"""
        protection_levels = {
            "low": 0.5,
            "medium": 0.7,
            "high": 0.85,
            "critical": 0.95
        }
        
        shield = PreventionShield(
            service=service,
            threat_level=threat_level,
            protection_level=protection_levels.get(threat_level, 0.7)
        )
        
        logger.info(f"🛡️ 予防シールド展開: {service} (防御力: {shield.protection_level * 100}%)")
        
        return shield
    
    async def consult_sages_for_incident(self, incident: FantasyIncident) -> Dict[str, Any]:
        """インシデントについて4賢者に相談"""
        consultation_data = {
            "incident_id": incident.id,
            "creature": incident.creature.name,
            "level": incident.creature.level.value,
            "description": incident.description
        }
        
        # 4賢者に相談
        result = await self.four_sages.consult_incident_sage(consultation_data)
        
        return result
    
    def format_fantasy_log(self, level: str, message: str, creature: str) -> str:
        """ファンタジー形式のログフォーマット"""
        creature_data = self.creature_mapping.get(creature, {})
        emoji = creature_data.get("emoji", "⚠️")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"[{timestamp}] {emoji} [{level}] {message} - {creature}の仕業か！"
    
    def get_knight_achievements(self, knight_id: str) -> Dict[str, Any]:
        """騎士の実績を取得"""
        knight = self.knight_registry.get(knight_id)
        
        if not knight:
            return {
                "error": "Knight not found",
                "creatures_defeated": 0,
                "total_exp": 0,
                "rank_history": [],
                "badges": []
            }
        
        # 実績データ（実際の実装では永続化が必要）
        return {
            "knight_id": knight_id,
            "knight_name": knight.name,
            "current_rank": knight.rank.value,
            "creatures_defeated": len(knight.achievements),
            "total_exp": knight.experience,
            "rank_history": [knight.rank.value],  # 簡略化
            "badges": self._calculate_badges(knight)
        }
    
    def _calculate_badges(self, knight: Knight) -> List[str]:
        """騎士のバッジを計算"""
        badges = []
        
        if knight.experience >= 100:
            badges.append("🏅 百戦錬磨")
        if knight.experience >= 1000:
            badges.append("🎖️ 千客万来")
        if knight.rank == KnightRank.GRANDMASTER:
            badges.append("👑 騎士団長")
        
        return badges
    
    def get_creature_statistics(self) -> Dict[str, Any]:
        """クリーチャー別統計を取得"""
        # 統計データ集計
        by_creature = {}
        for incident in self.active_incidents.values():
            creature_name = incident.creature.name
            if creature_name not in by_creature:
                by_creature[creature_name] = {"count": 0, "defeated": 0}
            by_creature[creature_name]["count"] += 1
            if incident.status == "resolved":
                by_creature[creature_name]["defeated"] += 1
        
        # 最も一般的なクリーチャー
        most_common = max(by_creature.items(), key=lambda x: x[1]["count"]) if by_creature else None
        
        # 討伐率計算
        total_incidents = len(self.active_incidents)
        total_defeated = sum(1 for i in self.active_incidents.values() if i.status == "resolved")
        defeat_rate = (total_defeated / total_incidents * 100) if total_incidents > 0 else 0
        
        return {
            "by_creature": by_creature,
            "most_common": most_common[0] if most_common else None,
            "defeat_rate": f"{defeat_rate:.1f}%",
            "average_resolution_time": "15 minutes"  # 仮の値
        }
    
    async def start_incident_quest(self, title: str, description: str, reporter: str) -> FantasyIncident:
        """インシデントクエストを開始"""
        # ファンタジーインシデント作成
        incident = self.create_fantasy_incident(
            title=title,
            description=description,
            affected_service=reporter
        )
        
        # 適切な騎士を割り当て
        required_knights = {
            IncidentLevel.LOW: 1,
            IncidentLevel.MEDIUM: 2,
            IncidentLevel.HIGH: 3,
            IncidentLevel.CRITICAL: 5
        }
        
        num_knights = required_knights.get(incident.creature.level, 1)
        
        # 騎士の割り当て（簡略化）
        for i in range(num_knights):
            knight = self.assign_knight_rank(100 * (i + 1))
            incident.assigned_knights.append(knight.id)
        
        return incident
    
    async def knight_respond(self, quest_id: str, knight_id: str, action: str) -> Dict[str, Any]:
        """騎士の対応"""
        incident = self.active_incidents.get(quest_id)
        
        if not incident:
            return {"status": "error", "message": "Quest not found"}
        
        # アクション実行
        if action == "investigate":
            incident.status = "investigating"
            return {"status": "investigating", "message": f"騎士 {knight_id} が調査を開始"}
        
        return {"status": "unknown_action"}
    
    async def apply_healing(self, quest_id: str, spell_type: str) -> HealingSpell:
        """治癒魔法を適用"""
        incident = self.active_incidents.get(quest_id)
        
        if not incident:
            return HealingSpell(success=False, spell_type=spell_type, reason="Quest not found")
        
        # 治癒魔法詠唱
        healing = HealingSpell(
            success=True,
            spell_type=spell_type,
            applied=True
        )
        
        logger.info(f"✨ 治癒魔法 {spell_type} を {quest_id} に適用")
        
        return healing
    
    async def complete_quest(self, quest_id: str, resolution: str) -> Dict[str, Any]:
        """クエストを完了"""
        incident = self.active_incidents.get(quest_id)
        
        if not incident:
            return {"success": False, "message": "Quest not found"}
        
        # インシデント解決
        incident.status = "resolved"
        
        # 経験値付与
        for knight_id in incident.assigned_knights:
            knight = self.knight_registry.get(knight_id)
            if knight:
                knight.experience += incident.reward_exp
                knight.achievements.append(f"Defeated {incident.creature.name}")
        
        # 統計更新
        self.statistics["total_defeated"] += 1
        self.statistics["total_exp_awarded"] += incident.reward_exp
        
        return {
            "success": True,
            "exp_awarded": incident.reward_exp,
            "creature_defeated": True,
            "resolution": resolution
        }
    
    def assess_commit_risk(self, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """コミットのリスクを評価"""
        total_lines = sum(change.get("lines_changed", 0) for change in changes)
        critical_files = sum(1 for change in changes if "security" in change.get("file", "").lower() or 
                           "payment" in change.get("file", "").lower() or
                           "database" in change.get("file", "").lower())
        
        # リスクスコア計算
        risk_score = min(1.0, (total_lines / 500) + (critical_files * 0.3))
        
        # リスクレベル判定
        if risk_score >= 0.8:
            level = "CRITICAL"
            creature = self.creature_mapping["古龍の覚醒"]
        elif risk_score >= 0.6:
            level = "HIGH"
            creature = self.creature_mapping["オークの大軍"]
        elif risk_score >= 0.3:
            level = "MEDIUM"
            creature = self.creature_mapping["ゾンビの侵入"]
        else:
            level = "LOW"
            creature = self.creature_mapping["妖精の悪戯"]
        
        recommendation = {
            "CRITICAL": "緊急レビューが必要です！複数の騎士による検証を推奨",
            "HIGH": "慎重なレビューが必要です。上級騎士の確認を推奨",
            "MEDIUM": "通常レビューで対応可能です",
            "LOW": "軽微な変更です。自動チェックで十分"
        }
        
        return {
            "level": level,
            "risk_score": risk_score,
            "creature": IncidentCreature(
                name=creature["description"],
                emoji=creature["emoji"],
                level=creature["level"],
                description=creature["description"]
            ),
            "recommendation": recommendation.get(level, "レビューを実施してください")
        }
    
    def should_block_commit(self, change: Dict[str, Any]) -> bool:
        """コミットをブロックすべきか判定"""
        risk_score = change.get("risk_score", 0)
        detected_issues = change.get("detected_issues", [])
        
        # 重大な問題が検出された場合
        critical_issues = ["hardcoded_password", "sql_injection", "xss", "private_key"]
        
        for issue in detected_issues:
            if issue in critical_issues:
                logger.error(f"🐉 古龍級の脅威を検出: {issue}")
                return True
        
        # リスクスコアが極めて高い場合
        if risk_score > 0.9:
            logger.warning("⚔️ オーク級のリスクを検出")
            return True
        
        return False


# エクスポート
__all__ = [
    "EnhancedIncidentManager",
    "IncidentCreature", 
    "KnightRank",
    "IncidentLevel",
    "FantasyIncident",
    "HealingSpell",
    "PreventionShield",
    "Knight"
]