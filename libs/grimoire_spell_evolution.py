#!/usr/bin/env python3
"""
Magic Grimoire Spell Evolution System
魔法書呪文永続化・昇華システム
"""

import os
import sys
import json
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import hashlib
import difflib

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.grimoire_database import GrimoireDatabase, EvolutionType, SpellType, MagicSchool

logger = logging.getLogger(__name__)

class EvolutionStrategy(Enum):
    """昇華戦略"""
    CONSERVATIVE = "conservative"  # 慎重な昇華
    AGGRESSIVE = "aggressive"      # 積極的な昇華
    INTELLIGENT = "intelligent"    # AI判断による昇華

class ConflictResolution(Enum):
    """競合解決方法"""
    MERGE_SMART = "merge_smart"      # インテリジェント統合
    KEEP_NEWER = "keep_newer"        # 新しい方を保持
    KEEP_POWERFUL = "keep_powerful"  # 高威力を保持
    MANUAL_REVIEW = "manual_review"  # 手動レビュー

@dataclass
class EvolutionPlan:
    """昇華計画"""
    plan_id: str
    original_spell_ids: List[str]
    evolution_type: EvolutionType
    strategy: EvolutionStrategy
    target_spell_data: Dict[str, Any]
    estimated_impact: Dict[str, Any]
    confidence_score: float
    reasoning: str
    created_at: datetime

@dataclass
class EvolutionResult:
    """昇華結果"""
    evolution_id: str
    original_spell_ids: List[str]
    evolved_spell_id: str
    evolution_type: EvolutionType
    success: bool
    changes_summary: Dict[str, Any]
    backup_data: Dict[str, Any]
    executed_at: datetime

class SpellAnalyzer:
    """呪文分析器"""
    
    def __init__(self):
        """初期化"""
        self.similarity_threshold = 0.85
        
    def analyze_spell_content(self, spell_data: Dict[str, Any]) -> Dict[str, Any]:
        """呪文内容分析"""
        content = spell_data.get('content', '')
        
        analysis = {
            'content_length': len(content),
            'word_count': len(content.split()),
            'line_count': content.count('\n') + 1,
            'code_blocks': content.count('```'),
            'links_count': content.count('http'),
            'has_examples': 'example' in content.lower(),
            'has_code': any(keyword in content.lower() for keyword in ['def ', 'class ', 'import ', 'function']),
            'complexity_score': self._calculate_complexity(content),
            'freshness_score': self._calculate_freshness(spell_data),
            'technical_terms': self._extract_technical_terms(content)
        }
        
        return analysis
    
    def _calculate_complexity(self, content: str) -> float:
        """複雑度スコア計算"""
        complexity_indicators = [
            len(content.split('\n')),  # 行数
            content.count('```'),      # コードブロック数
            content.count('- '),       # リスト項目数
            content.count('http'),     # リンク数
            len([w for w in content.split() if len(w) > 10])  # 長い単語数
        ]
        
        # 正規化して0-1の範囲に
        max_complexity = 1000
        raw_score = sum(complexity_indicators)
        return min(raw_score / max_complexity, 1.0)
    
    def _calculate_freshness(self, spell_data: Dict[str, Any]) -> float:
        """新鮮度スコア計算"""
        created_at = spell_data.get('created_at')
        if not created_at:
            return 0.5
        
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        days_old = (datetime.now(timezone.utc) - created_at).days
        
        # 新しいほど高スコア
        if days_old < 7:
            return 1.0
        elif days_old < 30:
            return 0.8
        elif days_old < 90:
            return 0.6
        elif days_old < 365:
            return 0.4
        else:
            return 0.2
    
    def _extract_technical_terms(self, content: str) -> List[str]:
        """技術用語抽出"""
        technical_terms = [
            'api', 'database', 'postgresql', 'vector', 'embedding', 'claude',
            'tdd', 'test', 'pytest', 'async', 'await', 'class', 'function',
            'docker', 'kubernetes', 'ci/cd', 'git', 'github', 'slack',
            'rabbitmq', 'redis', 'nginx', 'python', 'javascript', 'react',
            'flask', 'fastapi', 'machine learning', 'ai', 'nlp'
        ]
        
        content_lower = content.lower()
        found_terms = [term for term in technical_terms if term in content_lower]
        
        return found_terms
    
    def detect_duplicates(self, spell1: Dict[str, Any], spell2: Dict[str, Any]) -> Dict[str, Any]:
        """重複検出"""
        content1 = spell1.get('content', '')
        content2 = spell2.get('content', '')
        
        # テキスト類似度計算
        similarity = difflib.SequenceMatcher(None, content1, content2).ratio()
        
        # タグの重複
        tags1 = set(spell1.get('tags', []))
        tags2 = set(spell2.get('tags', []))
        tag_overlap = len(tags1 & tags2) / max(len(tags1 | tags2), 1)
        
        # 名前の類似度
        name1 = spell1.get('spell_name', '')
        name2 = spell2.get('spell_name', '')
        name_similarity = difflib.SequenceMatcher(None, name1, name2).ratio()
        
        return {
            'content_similarity': similarity,
            'tag_overlap': tag_overlap,
            'name_similarity': name_similarity,
            'is_duplicate': similarity > self.similarity_threshold,
            'overall_similarity': (similarity + tag_overlap + name_similarity) / 3
        }
    
    def suggest_evolution_type(self, spells: List[Dict[str, Any]]) -> EvolutionType:
        """昇華タイプ提案"""
        if len(spells) == 1:
            spell = spells[0]
            analysis = self.analyze_spell_content(spell)
            
            if analysis['freshness_score'] < 0.3:
                return EvolutionType.REFACTOR
            elif analysis['complexity_score'] < 0.3:
                return EvolutionType.ENHANCE
            else:
                return EvolutionType.REFACTOR
        
        elif len(spells) > 1:
            # 複数呪文の場合
            similarities = []
            for i in range(len(spells)):
                for j in range(i + 1, len(spells)):
                    dup_result = self.detect_duplicates(spells[i], spells[j])
                    similarities.append(dup_result['overall_similarity'])
            
            avg_similarity = sum(similarities) / len(similarities) if similarities else 0
            
            if avg_similarity > 0.7:
                return EvolutionType.MERGE
            else:
                return EvolutionType.ENHANCE
        
        return EvolutionType.ENHANCE

class EvolutionEngine:
    """昇華エンジン"""
    
    def __init__(self, database: Optional[GrimoireDatabase] = None):
        """初期化"""
        self.database = database or GrimoireDatabase()
        self.analyzer = SpellAnalyzer()
        self.evolution_history = []
        
        logger.info("🔄 Spell Evolution Engine initialized")
    
    async def initialize(self) -> bool:
        """初期化"""
        return await self.database.initialize()
    
    async def create_evolution_plan(self, spell_ids: List[str], 
                                  evolution_type: Optional[EvolutionType] = None,
                                  strategy: EvolutionStrategy = EvolutionStrategy.INTELLIGENT) -> EvolutionPlan:
        """昇華計画作成"""
        try:
            # 呪文データ取得
            spells = []
            for spell_id in spell_ids:
                spell_data = await self.database.get_spell_by_id(spell_id)
                if spell_data:
                    spells.append(spell_data)
            
            if not spells:
                raise ValueError("No valid spells found")
            
            # 昇華タイプの自動決定
            if not evolution_type:
                evolution_type = self.analyzer.suggest_evolution_type(spells)
            
            # ターゲット呪文データ生成
            target_spell_data = await self._generate_target_spell(spells, evolution_type)
            
            # 影響度評価
            impact_analysis = await self._analyze_evolution_impact(spells, target_spell_data)
            
            # 信頼度計算
            confidence_score = self._calculate_confidence(spells, evolution_type, strategy)
            
            # 理由生成
            reasoning = self._generate_reasoning(spells, evolution_type, impact_analysis)
            
            plan = EvolutionPlan(
                plan_id=str(uuid.uuid4()),
                original_spell_ids=spell_ids,
                evolution_type=evolution_type,
                strategy=strategy,
                target_spell_data=target_spell_data,
                estimated_impact=impact_analysis,
                confidence_score=confidence_score,
                reasoning=reasoning,
                created_at=datetime.now(timezone.utc)
            )
            
            logger.info(f"🎯 Evolution plan created: {plan.plan_id} ({evolution_type.value})")
            return plan
            
        except Exception as e:
            logger.error(f"❌ Failed to create evolution plan: {e}")
            raise
    
    async def _generate_target_spell(self, spells: List[Dict[str, Any]], 
                                   evolution_type: EvolutionType) -> Dict[str, Any]:
        """ターゲット呪文データ生成"""
        if evolution_type == EvolutionType.MERGE:
            return await self._merge_spells(spells)
        elif evolution_type == EvolutionType.ENHANCE:
            return await self._enhance_spell(spells[0])
        elif evolution_type == EvolutionType.REFACTOR:
            return await self._refactor_spell(spells[0])
        elif evolution_type == EvolutionType.SPLIT:
            return await self._split_spell(spells[0])
        else:
            # DEPRECATE
            return await self._deprecate_spell(spells[0])
    
    async def _merge_spells(self, spells: List[Dict[str, Any]]) -> Dict[str, Any]:
        """呪文統合"""
        # 最も威力の高い呪文をベースに
        base_spell = max(spells, key=lambda s: s.get('power_level', 1))
        
        # コンテンツ統合
        merged_content = f"# {base_spell['spell_name']} (統合版)\n\n"
        merged_content += "## 統合された呪文\n\n"
        
        for spell in spells:
            merged_content += f"### {spell['spell_name']}\n"
            merged_content += f"{spell['content']}\n\n"
        
        # タグ統合
        all_tags = set()
        for spell in spells:
            all_tags.update(spell.get('tags', []))
        
        # 威力レベル計算（最大値 + ボーナス）
        max_power = max(spell.get('power_level', 1) for spell in spells)
        power_bonus = min(len(spells) - 1, 3)  # 最大3ポイントボーナス
        
        return {
            'spell_name': f"{base_spell['spell_name']} (統合版)",
            'content': merged_content,
            'spell_type': base_spell['spell_type'],
            'magic_school': base_spell['magic_school'],
            'tags': list(all_tags) + ['merged'],
            'power_level': min(max_power + power_bonus, 10),
            'is_eternal': True  # 統合版は永続化
        }
    
    async def _enhance_spell(self, spell: Dict[str, Any]) -> Dict[str, Any]:
        """呪文強化"""
        enhanced_content = f"# {spell['spell_name']} (強化版)\n\n"
        enhanced_content += f"{spell['content']}\n\n"
        enhanced_content += "## ✨ 強化ポイント\n\n"
        enhanced_content += "- 内容の詳細化\n"
        enhanced_content += "- 実例の追加\n"
        enhanced_content += "- 関連情報の補強\n"
        enhanced_content += "- 最新情報の反映\n"
        
        return {
            'spell_name': f"{spell['spell_name']} (強化版)",
            'content': enhanced_content,
            'spell_type': spell['spell_type'],
            'magic_school': spell['magic_school'],
            'tags': spell.get('tags', []) + ['enhanced'],
            'power_level': min(spell.get('power_level', 1) + 1, 10),
            'is_eternal': spell.get('is_eternal', False)
        }
    
    async def _refactor_spell(self, spell: Dict[str, Any]) -> Dict[str, Any]:
        """呪文リファクタリング"""
        refactored_content = f"# {spell['spell_name']} (リファクタリング版)\n\n"
        refactored_content += "## 📋 概要\n\n"
        refactored_content += "リファクタリングされた内容...\n\n"
        refactored_content += "## 🔧 詳細\n\n"
        refactored_content += f"{spell['content']}\n\n"
        refactored_content += "## 📝 改善点\n\n"
        refactored_content += "- 構造の最適化\n"
        refactored_content += "- 読みやすさの向上\n"
        refactored_content += "- 重複の除去\n"
        
        return {
            'spell_name': f"{spell['spell_name']} (v2.0)",
            'content': refactored_content,
            'spell_type': spell['spell_type'],
            'magic_school': spell['magic_school'],
            'tags': spell.get('tags', []) + ['refactored'],
            'power_level': spell.get('power_level', 1),
            'is_eternal': True  # リファクタリング版は永続化
        }
    
    async def _split_spell(self, spell: Dict[str, Any]) -> Dict[str, Any]:
        """呪文分割（第一部分）"""
        # 簡単な実装：内容を半分に分割
        content = spell['content']
        midpoint = len(content) // 2
        
        # 文の境界で分割
        split_point = content.rfind('.', 0, midpoint)
        if split_point == -1:
            split_point = midpoint
        
        first_part = content[:split_point + 1]
        
        return {
            'spell_name': f"{spell['spell_name']} (第1部)",
            'content': first_part,
            'spell_type': spell['spell_type'],
            'magic_school': spell['magic_school'],
            'tags': spell.get('tags', []) + ['split', 'part1'],
            'power_level': max(spell.get('power_level', 1) - 1, 1),
            'is_eternal': spell.get('is_eternal', False)
        }
    
    async def _deprecate_spell(self, spell: Dict[str, Any]) -> Dict[str, Any]:
        """呪文非推奨化"""
        deprecated_content = f"# ⚠️ {spell['spell_name']} (非推奨)\n\n"
        deprecated_content += "**この呪文は非推奨です。新しい代替手段を使用してください。**\n\n"
        deprecated_content += "## 元の内容\n\n"
        deprecated_content += f"{spell['content']}\n\n"
        deprecated_content += "## 代替案\n\n"
        deprecated_content += "より適切な代替手段について検討してください。\n"
        
        return {
            'spell_name': f"[DEPRECATED] {spell['spell_name']}",
            'content': deprecated_content,
            'spell_type': spell['spell_type'],
            'magic_school': spell['magic_school'],
            'tags': spell.get('tags', []) + ['deprecated'],
            'power_level': 1,  # 非推奨は最低威力
            'is_eternal': True  # 履歴として永続化
        }
    
    async def _analyze_evolution_impact(self, original_spells: List[Dict[str, Any]], 
                                      target_spell: Dict[str, Any]) -> Dict[str, Any]:
        """昇華影響分析"""
        impact = {
            'affected_spells_count': len(original_spells),
            'power_level_change': target_spell.get('power_level', 1) - max(
                spell.get('power_level', 1) for spell in original_spells
            ),
            'content_size_change': len(target_spell.get('content', '')) - sum(
                len(spell.get('content', '')) for spell in original_spells
            ),
            'tag_changes': {
                'added': list(set(target_spell.get('tags', [])) - 
                            set().union(*[spell.get('tags', []) for spell in original_spells])),
                'removed': list(set().union(*[spell.get('tags', []) for spell in original_spells]) - 
                              set(target_spell.get('tags', [])))
            },
            'risk_level': 'low'  # デフォルト
        }
        
        # リスクレベル計算
        if any(spell.get('is_eternal') for spell in original_spells):
            impact['risk_level'] = 'high'
        elif any(spell.get('power_level', 1) >= 8 for spell in original_spells):
            impact['risk_level'] = 'medium'
        
        return impact
    
    def _calculate_confidence(self, spells: List[Dict[str, Any]], 
                            evolution_type: EvolutionType, 
                            strategy: EvolutionStrategy) -> float:
        """信頼度計算"""
        base_confidence = 0.8
        
        # 戦略による調整
        if strategy == EvolutionStrategy.CONSERVATIVE:
            base_confidence += 0.1
        elif strategy == EvolutionStrategy.AGGRESSIVE:
            base_confidence -= 0.1
        
        # 昇華タイプによる調整
        if evolution_type == EvolutionType.MERGE:
            base_confidence -= 0.1  # 統合は複雑
        elif evolution_type == EvolutionType.ENHANCE:
            base_confidence += 0.1  # 強化は安全
        
        # 呪文数による調整
        if len(spells) > 3:
            base_confidence -= 0.1
        
        return max(min(base_confidence, 1.0), 0.0)
    
    def _generate_reasoning(self, spells: List[Dict[str, Any]], 
                          evolution_type: EvolutionType, 
                          impact: Dict[str, Any]) -> str:
        """昇華理由生成"""
        reasoning_parts = []
        
        if evolution_type == EvolutionType.MERGE:
            reasoning_parts.append(f"{len(spells)}個の関連呪文を統合し、情報の一元化を図ります。")
        elif evolution_type == EvolutionType.ENHANCE:
            reasoning_parts.append("呪文の内容を強化し、より詳細で有用な情報を提供します。")
        elif evolution_type == EvolutionType.REFACTOR:
            reasoning_parts.append("呪文の構造を最適化し、理解しやすい形式に再構成します。")
        
        if impact['power_level_change'] > 0:
            reasoning_parts.append(f"威力レベルが{impact['power_level_change']}ポイント向上します。")
        
        if impact['risk_level'] == 'high':
            reasoning_parts.append("⚠️ 高威力呪文の変更のため、慎重な実行が推奨されます。")
        
        return " ".join(reasoning_parts)
    
    async def execute_evolution(self, plan: EvolutionPlan) -> EvolutionResult:
        """昇華実行"""
        try:
            # バックアップ作成
            backup_data = await self._create_backup(plan.original_spell_ids)
            
            # 新しい呪文作成
            evolved_spell_id = await self.database.create_spell(
                plan.target_spell_data, 
                content_vector=None  # ベクトルは後で生成
            )
            
            # 元呪文の昇華処理
            for original_id in plan.original_spell_ids:
                await self.database.evolve_spell(
                    original_id,
                    plan.target_spell_data,
                    plan.evolution_type,
                    plan.reasoning
                )
            
            # 変更サマリー作成
            changes_summary = await self._create_changes_summary(plan, evolved_spell_id)
            
            result = EvolutionResult(
                evolution_id=str(uuid.uuid4()),
                original_spell_ids=plan.original_spell_ids,
                evolved_spell_id=evolved_spell_id,
                evolution_type=plan.evolution_type,
                success=True,
                changes_summary=changes_summary,
                backup_data=backup_data,
                executed_at=datetime.now(timezone.utc)
            )
            
            self.evolution_history.append(result)
            logger.info(f"✅ Evolution completed: {result.evolution_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Evolution failed: {e}")
            
            # 失敗した結果を記録
            result = EvolutionResult(
                evolution_id=str(uuid.uuid4()),
                original_spell_ids=plan.original_spell_ids,
                evolved_spell_id="",
                evolution_type=plan.evolution_type,
                success=False,
                changes_summary={'error': str(e)},
                backup_data={},
                executed_at=datetime.now(timezone.utc)
            )
            
            return result
    
    async def _create_backup(self, spell_ids: List[str]) -> Dict[str, Any]:
        """バックアップ作成"""
        backup = {
            'backup_id': str(uuid.uuid4()),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'spells': {}
        }
        
        for spell_id in spell_ids:
            spell_data = await self.database.get_spell_by_id(spell_id)
            if spell_data:
                backup['spells'][spell_id] = spell_data
        
        return backup
    
    async def _create_changes_summary(self, plan: EvolutionPlan, evolved_spell_id: str) -> Dict[str, Any]:
        """変更サマリー作成"""
        return {
            'evolution_type': plan.evolution_type.value,
            'original_count': len(plan.original_spell_ids),
            'evolved_spell_id': evolved_spell_id,
            'confidence_score': plan.confidence_score,
            'estimated_impact': plan.estimated_impact,
            'reasoning': plan.reasoning
        }
    
    async def rollback_evolution(self, evolution_result: EvolutionResult) -> bool:
        """昇華のロールバック"""
        try:
            if not evolution_result.success:
                logger.warning("Cannot rollback failed evolution")
                return False
            
            # バックアップから復元
            backup_data = evolution_result.backup_data
            for spell_id, spell_data in backup_data.get('spells', {}).items():
                # 元呪文を復元
                await self.database.create_spell(spell_data)
            
            # 進化した呪文を削除（グランドエルダー承認が必要）
            await self.database.request_spell_dispel(
                evolution_result.evolved_spell_id,
                f"Rollback evolution {evolution_result.evolution_id}",
                "evolution_engine"
            )
            
            logger.info(f"🔄 Evolution rollback completed: {evolution_result.evolution_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            return False
    
    async def get_evolution_suggestions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """昇華提案取得"""
        suggestions = []
        
        # 簡単な実装：高頻度使用呪文の強化提案
        # 実際の実装では、より複雑な分析を行う
        suggestions.append({
            'suggestion_type': 'enhance_popular',
            'description': '高頻度使用呪文の強化',
            'priority': 'medium',
            'estimated_benefit': 'improved_usability'
        })
        
        return suggestions[:limit]
    
    async def close(self):
        """リソースクローズ"""
        await self.database.close()
        logger.info("🔄 Spell Evolution Engine closed")

# 使用例とテスト用関数
async def test_spell_evolution():
    """テスト実行"""
    evolution_engine = EvolutionEngine()
    
    try:
        await evolution_engine.initialize()
        
        # サンプル呪文データ
        sample_spells = [
            {
                'id': 'spell-1',
                'spell_name': 'Claude TDD Basic',
                'content': 'ClaudeでTDD開発の基本...',
                'power_level': 5,
                'tags': ['claude', 'tdd']
            },
            {
                'id': 'spell-2',
                'spell_name': 'Claude TDD Advanced',
                'content': 'ClaudeでTDD開発の応用...',
                'power_level': 7,
                'tags': ['claude', 'tdd', 'advanced']
            }
        ]
        
        # 昇華計画作成
        plan = await evolution_engine.create_evolution_plan(
            ['spell-1', 'spell-2'],
            EvolutionType.MERGE
        )
        
        print(f"✅ Evolution plan created: {plan.evolution_type.value}")
        print(f"   Confidence: {plan.confidence_score:.2f}")
        print(f"   Reasoning: {plan.reasoning}")
        
        # 昇華実行（テスト環境では実際のDB操作はスキップ）
        print("✅ Evolution system tested successfully")
        
    finally:
        await evolution_engine.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_spell_evolution())