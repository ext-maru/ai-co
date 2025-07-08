#!/usr/bin/env python3
"""
Grand Elder Approval System
グランドエルダー解呪許可・承認システム
"""

import os
import sys
import json
import uuid
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import hashlib

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.grimoire_database import GrimoireDatabase, EvolutionType

logger = logging.getLogger(__name__)

class PermissionType(Enum):
    """許可種別"""
    DISPEL = "dispel"           # 解呪（削除）
    ARCHIVE = "archive"         # アーカイブ化
    MERGE = "merge"            # 統合
    DEPRECATE = "deprecate"    # 非推奨化
    MODIFY = "modify"          # 重要修正

class ApprovalStatus(Enum):
    """承認状況"""
    PENDING = "pending"         # 申請中
    SAGE_REVIEW = "sage_review" # 4賢者審査中
    ELDER_REVIEW = "elder_review" # エルダー審査中
    APPROVED = "approved"       # 承認済み
    REJECTED = "rejected"       # 却下
    EXECUTED = "executed"       # 実行済み
    EXPIRED = "expired"         # 期限切れ

class RiskLevel(Enum):
    """リスクレベル"""
    CRITICAL = "critical"       # 致命的影響
    HIGH = "high"              # 高リスク
    MEDIUM = "medium"          # 中リスク
    LOW = "low"               # 低リスク
    MINIMAL = "minimal"        # 最小リスク

@dataclass
class SageReview:
    """4賢者審査結果"""
    sage_name: str
    sage_type: str
    assessment: str
    risk_evaluation: RiskLevel
    recommendation: str
    confidence_score: float
    reviewed_at: datetime
    additional_notes: Optional[str] = None

@dataclass
class ImpactAnalysis:
    """影響分析"""
    affected_systems: List[str]
    dependency_count: int
    usage_frequency: int
    related_spells: List[str]
    risk_factors: List[str]
    mitigation_strategies: List[str]
    overall_risk: RiskLevel
    estimated_downtime: str
    rollback_complexity: str

@dataclass
class ApprovalRequest:
    """承認申請"""
    request_id: str
    spell_id: str
    permission_type: PermissionType
    request_reason: str
    impact_analysis: ImpactAnalysis
    requested_by: str
    requested_at: datetime
    deadline: datetime
    status: ApprovalStatus
    sage_reviews: List[SageReview]
    elder_notes: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_reason: Optional[str] = None
    execution_notes: Optional[str] = None

class FourSagesReviewer:
    """4賢者審査システム"""
    
    def __init__(self, database: Optional[GrimoireDatabase] = None):
        """初期化"""
        self.database = database or GrimoireDatabase()
        
        # 4賢者の審査基準
        self.sage_criteria = {
            'knowledge_sage': {
                'focus': 'knowledge_preservation',
                'concerns': ['data_loss', 'knowledge_gap', 'historical_value'],
                'expertise': 'content_analysis'
            },
            'task_oracle': {
                'focus': 'operational_impact',
                'concerns': ['workflow_disruption', 'dependency_break', 'productivity_loss'],
                'expertise': 'process_analysis'
            },
            'crisis_sage': {
                'focus': 'risk_assessment',
                'concerns': ['system_stability', 'error_propagation', 'emergency_response'],
                'expertise': 'risk_management'
            },
            'search_mystic': {
                'focus': 'discoverability',
                'concerns': ['search_accuracy', 'knowledge_accessibility', 'user_experience'],
                'expertise': 'information_retrieval'
            }
        }
    
    async def conduct_sage_review(self, request: ApprovalRequest) -> List[SageReview]:
        """4賢者による審査実行"""
        try:
            spell_data = await self.database.get_spell_by_id(request.spell_id)
            if not spell_data:
                raise ValueError(f"Spell not found: {request.spell_id}")
            
            reviews = []
            
            for sage_type, criteria in self.sage_criteria.items():
                review = await self._conduct_individual_review(
                    sage_type, criteria, spell_data, request
                )
                reviews.append(review)
            
            logger.info(f"🧙‍♂️ 4賢者審査完了: {request.request_id}")
            return reviews
            
        except Exception as e:
            logger.error(f"❌ 4賢者審査エラー: {e}")
            raise
    
    async def _conduct_individual_review(self, sage_type: str, criteria: Dict[str, Any],
                                       spell_data: Dict[str, Any], request: ApprovalRequest) -> SageReview:
        """個別賢者審査"""
        # 賢者ごとの専門的分析
        if sage_type == 'knowledge_sage':
            return await self._knowledge_sage_review(spell_data, request)
        elif sage_type == 'task_oracle':
            return await self._task_oracle_review(spell_data, request)
        elif sage_type == 'crisis_sage':
            return await self._crisis_sage_review(spell_data, request)
        elif sage_type == 'search_mystic':
            return await self._search_mystic_review(spell_data, request)
        else:
            raise ValueError(f"Unknown sage type: {sage_type}")
    
    async def _knowledge_sage_review(self, spell_data: Dict[str, Any], 
                                   request: ApprovalRequest) -> SageReview:
        """ナレッジ賢者審査"""
        # 知識価値の評価
        power_level = spell_data.get('power_level', 1)
        is_eternal = spell_data.get('is_eternal', False)
        content_length = len(spell_data.get('content', ''))
        tags = spell_data.get('tags', [])
        
        risk_factors = []
        if is_eternal:
            risk_factors.append("永続化知識の消失")
        if power_level >= 8:
            risk_factors.append("高威力知識の損失")
        if content_length > 5000:
            risk_factors.append("大量知識の削除")
        if 'critical' in tags or 'important' in tags:
            risk_factors.append("重要タグ付き知識")
        
        # リスク評価
        if is_eternal and power_level >= 8:
            risk_level = RiskLevel.CRITICAL
        elif is_eternal or power_level >= 7:
            risk_level = RiskLevel.HIGH
        elif power_level >= 5 or content_length > 3000:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # 推奨事項
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            recommendation = "昇華による保持を強く推奨"
        elif risk_level == RiskLevel.MEDIUM:
            recommendation = "アーカイブ化を推奨"
        else:
            recommendation = "承認可能"
        
        # 信頼度計算
        confidence = 0.9 if is_eternal else 0.8
        
        return SageReview(
            sage_name="Knowledge Sage",
            sage_type="knowledge_sage",
            assessment=f"威力レベル{power_level}、{len(risk_factors)}個のリスク要因を検出",
            risk_evaluation=risk_level,
            recommendation=recommendation,
            confidence_score=confidence,
            reviewed_at=datetime.now(timezone.utc),
            additional_notes=f"リスク要因: {', '.join(risk_factors)}" if risk_factors else None
        )
    
    async def _task_oracle_review(self, spell_data: Dict[str, Any], 
                                request: ApprovalRequest) -> SageReview:
        """タスク賢者審査"""
        casting_frequency = spell_data.get('casting_frequency', 0)
        magic_school = spell_data.get('magic_school', '')
        
        # 運用影響の評価
        risk_factors = []
        if casting_frequency > 50:
            risk_factors.append("高頻度使用呪文")
        if magic_school == 'task_oracle':
            risk_factors.append("タスク管理系の重要呪文")
        if request.impact_analysis.dependency_count > 5:
            risk_factors.append("多数の依存関係")
        
        # リスク評価
        if casting_frequency > 100 and request.impact_analysis.dependency_count > 10:
            risk_level = RiskLevel.CRITICAL
        elif casting_frequency > 50 or request.impact_analysis.dependency_count > 5:
            risk_level = RiskLevel.HIGH
        elif casting_frequency > 20:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # 推奨事項
        if risk_level == RiskLevel.CRITICAL:
            recommendation = "代替手段確立後に実行"
        elif risk_level == RiskLevel.HIGH:
            recommendation = "段階的移行を推奨"
        else:
            recommendation = "運用影響は最小限"
        
        return SageReview(
            sage_name="Task Oracle",
            sage_type="task_oracle",
            assessment=f"詠唱{casting_frequency}回、依存関係{request.impact_analysis.dependency_count}個",
            risk_evaluation=risk_level,
            recommendation=recommendation,
            confidence_score=0.85,
            reviewed_at=datetime.now(timezone.utc),
            additional_notes=f"影響要因: {', '.join(risk_factors)}" if risk_factors else None
        )
    
    async def _crisis_sage_review(self, spell_data: Dict[str, Any], 
                                request: ApprovalRequest) -> SageReview:
        """インシデント賢者審査"""
        magic_school = spell_data.get('magic_school', '')
        tags = spell_data.get('tags', [])
        
        # 危機対応への影響評価
        risk_factors = []
        if magic_school == 'crisis_sage':
            risk_factors.append("インシデント対応の重要呪文")
        if any(tag in ['error', 'debug', 'fix', 'emergency'] for tag in tags):
            risk_factors.append("エラー対処関連知識")
        if 'critical' in spell_data.get('content', '').lower():
            risk_factors.append("クリティカル情報含有")
        
        # システム安定性への影響
        system_impact = request.impact_analysis.affected_systems
        if len(system_impact) > 3:
            risk_factors.append("複数システムへの影響")
        
        # リスク評価
        if magic_school == 'crisis_sage' and len(system_impact) > 3:
            risk_level = RiskLevel.CRITICAL
        elif magic_school == 'crisis_sage' or len(risk_factors) > 2:
            risk_level = RiskLevel.HIGH
        elif len(risk_factors) > 1:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # 推奨事項
        if risk_level == RiskLevel.CRITICAL:
            recommendation = "緊急対応計画策定後に実行"
        elif risk_level == RiskLevel.HIGH:
            recommendation = "バックアップ体制確立を推奨"
        else:
            recommendation = "システム安定性への影響は軽微"
        
        return SageReview(
            sage_name="Crisis Sage",
            sage_type="crisis_sage",
            assessment=f"危機対応影響度評価: {len(risk_factors)}個の懸念事項",
            risk_evaluation=risk_level,
            recommendation=recommendation,
            confidence_score=0.9,
            reviewed_at=datetime.now(timezone.utc),
            additional_notes=f"懸念事項: {', '.join(risk_factors)}" if risk_factors else None
        )
    
    async def _search_mystic_review(self, spell_data: Dict[str, Any], 
                                  request: ApprovalRequest) -> SageReview:
        """RAG賢者審査"""
        content = spell_data.get('content', '')
        tags = spell_data.get('tags', [])
        magic_school = spell_data.get('magic_school', '')
        
        # 検索・発見可能性への影響評価
        risk_factors = []
        if magic_school == 'search_mystic':
            risk_factors.append("検索システムの重要呪文")
        if len(tags) > 5:
            risk_factors.append("多数のタグによる高い発見可能性")
        if 'search' in content.lower() or 'find' in content.lower():
            risk_factors.append("検索関連の重要情報")
        
        # 関連呪文への影響
        related_count = len(request.impact_analysis.related_spells)
        if related_count > 10:
            risk_factors.append("多数の関連呪文への影響")
        
        # リスク評価
        if magic_school == 'search_mystic' and related_count > 10:
            risk_level = RiskLevel.HIGH
        elif magic_school == 'search_mystic' or related_count > 5:
            risk_level = RiskLevel.MEDIUM
        elif related_count > 2:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.MINIMAL
        
        # 推奨事項
        if risk_level == RiskLevel.HIGH:
            recommendation = "関連呪文の更新も併せて実行"
        elif risk_level == RiskLevel.MEDIUM:
            recommendation = "検索インデックスの再構築を推奨"
        else:
            recommendation = "検索への影響は最小限"
        
        return SageReview(
            sage_name="Search Mystic",
            sage_type="search_mystic",
            assessment=f"検索影響度: 関連呪文{related_count}個、{len(risk_factors)}個の要因",
            risk_evaluation=risk_level,
            recommendation=recommendation,
            confidence_score=0.87,
            reviewed_at=datetime.now(timezone.utc),
            additional_notes=f"影響要因: {', '.join(risk_factors)}" if risk_factors else None
        )

class GrandElderApprovalSystem:
    """グランドエルダー承認システム"""
    
    def __init__(self, database: Optional[GrimoireDatabase] = None):
        """初期化"""
        self.database = database or GrimoireDatabase()
        self.four_sages = FourSagesReviewer(database)
        
        # 承認基準
        self.approval_thresholds = {
            RiskLevel.MINIMAL: {'sage_consensus': 0.75, 'elder_required': False},
            RiskLevel.LOW: {'sage_consensus': 0.8, 'elder_required': False},
            RiskLevel.MEDIUM: {'sage_consensus': 0.85, 'elder_required': True},
            RiskLevel.HIGH: {'sage_consensus': 0.9, 'elder_required': True},
            RiskLevel.CRITICAL: {'sage_consensus': 1.0, 'elder_required': True}
        }
        
        logger.info("🏛️ Grand Elder Approval System initialized")
    
    async def initialize(self) -> bool:
        """初期化"""
        return await self.database.initialize()
    
    async def submit_approval_request(self, spell_id: str, permission_type: PermissionType,
                                    reason: str, requester: str) -> str:
        """承認申請提出"""
        try:
            # 影響分析実行
            impact_analysis = await self._analyze_spell_impact(spell_id, permission_type)
            
            # 申請作成
            request = ApprovalRequest(
                request_id=str(uuid.uuid4()),
                spell_id=spell_id,
                permission_type=permission_type,
                request_reason=reason,
                impact_analysis=impact_analysis,
                requested_by=requester,
                requested_at=datetime.now(timezone.utc),
                deadline=self._calculate_deadline(impact_analysis.overall_risk),
                status=ApprovalStatus.PENDING,
                sage_reviews=[]
            )
            
            # データベースに保存
            await self._save_approval_request(request)
            
            # 4賢者審査を自動開始
            await self._initiate_sage_review(request)
            
            logger.info(f"🏛️ 承認申請提出: {request.request_id}")
            return request.request_id
            
        except Exception as e:
            logger.error(f"❌ 承認申請エラー: {e}")
            raise
    
    async def _analyze_spell_impact(self, spell_id: str, 
                                  permission_type: PermissionType) -> ImpactAnalysis:
        """呪文影響分析"""
        try:
            spell_data = await self.database.get_spell_by_id(spell_id)
            if not spell_data:
                raise ValueError(f"Spell not found: {spell_id}")
            
            # 基本情報
            casting_frequency = spell_data.get('casting_frequency', 0)
            power_level = spell_data.get('power_level', 1)
            is_eternal = spell_data.get('is_eternal', False)
            
            # 依存関係分析（簡略化実装）
            dependency_count = await self._count_dependencies(spell_id)
            related_spells = await self._find_related_spells(spell_id)
            
            # 影響システム分析
            affected_systems = self._identify_affected_systems(spell_data)
            
            # リスク要因
            risk_factors = []
            if is_eternal:
                risk_factors.append("永続化呪文")
            if power_level >= 8:
                risk_factors.append("高威力呪文")
            if casting_frequency > 50:
                risk_factors.append("高頻度使用")
            if dependency_count > 5:
                risk_factors.append("多数依存関係")
            if permission_type == PermissionType.DISPEL:
                risk_factors.append("完全削除要求")
            
            # 全体リスク評価
            overall_risk = self._calculate_overall_risk(
                power_level, casting_frequency, dependency_count, is_eternal, permission_type
            )
            
            # 軽減戦略
            mitigation_strategies = self._generate_mitigation_strategies(
                risk_factors, permission_type, overall_risk
            )
            
            return ImpactAnalysis(
                affected_systems=affected_systems,
                dependency_count=dependency_count,
                usage_frequency=casting_frequency,
                related_spells=related_spells,
                risk_factors=risk_factors,
                mitigation_strategies=mitigation_strategies,
                overall_risk=overall_risk,
                estimated_downtime=self._estimate_downtime(overall_risk),
                rollback_complexity=self._assess_rollback_complexity(dependency_count, is_eternal)
            )
            
        except Exception as e:
            logger.error(f"❌ 影響分析エラー: {e}")
            raise
    
    async def _count_dependencies(self, spell_id: str) -> int:
        """依存関係数の計算"""
        # 簡略化実装：実際は詳細な依存関係分析を行う
        evolution_history = await self.database.get_evolution_history(spell_id)
        return len(evolution_history)
    
    async def _find_related_spells(self, spell_id: str) -> List[str]:
        """関連呪文の検索"""
        # 簡略化実装：実際はベクトル検索で関連呪文を探す
        return []  # 実装時に実際の関連呪文IDのリストを返す
    
    def _identify_affected_systems(self, spell_data: Dict[str, Any]) -> List[str]:
        """影響システムの特定"""
        systems = []
        content = spell_data.get('content', '').lower()
        magic_school = spell_data.get('magic_school', '')
        
        if 'database' in content or 'postgresql' in content:
            systems.append('database')
        if 'api' in content or 'endpoint' in content:
            systems.append('api')
        if 'worker' in content or 'task' in content:
            systems.append('worker_system')
        if 'search' in content or magic_school == 'search_mystic':
            systems.append('search_engine')
        if 'web' in content or 'ui' in content:
            systems.append('web_interface')
        
        return systems
    
    def _calculate_overall_risk(self, power_level: int, casting_frequency: int,
                              dependency_count: int, is_eternal: bool,
                              permission_type: PermissionType) -> RiskLevel:
        """全体リスク計算"""
        risk_score = 0
        
        # 威力レベル
        if power_level >= 9:
            risk_score += 3
        elif power_level >= 7:
            risk_score += 2
        elif power_level >= 5:
            risk_score += 1
        
        # 使用頻度
        if casting_frequency > 100:
            risk_score += 3
        elif casting_frequency > 50:
            risk_score += 2
        elif casting_frequency > 20:
            risk_score += 1
        
        # 依存関係
        if dependency_count > 10:
            risk_score += 2
        elif dependency_count > 5:
            risk_score += 1
        
        # 永続化
        if is_eternal:
            risk_score += 2
        
        # 操作種別
        if permission_type == PermissionType.DISPEL:
            risk_score += 2
        elif permission_type == PermissionType.MODIFY:
            risk_score += 1
        
        # スコアからリスクレベルを決定
        if risk_score >= 8:
            return RiskLevel.CRITICAL
        elif risk_score >= 6:
            return RiskLevel.HIGH
        elif risk_score >= 4:
            return RiskLevel.MEDIUM
        elif risk_score >= 2:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL
    
    def _generate_mitigation_strategies(self, risk_factors: List[str],
                                      permission_type: PermissionType,
                                      risk_level: RiskLevel) -> List[str]:
        """軽減戦略生成"""
        strategies = []
        
        if "永続化呪文" in risk_factors:
            strategies.append("昇華による知識保持")
        
        if "高頻度使用" in risk_factors:
            strategies.append("代替呪文の準備")
        
        if "多数依存関係" in risk_factors:
            strategies.append("依存呪文の事前更新")
        
        if permission_type == PermissionType.DISPEL:
            strategies.append("完全バックアップの作成")
        
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            strategies.append("段階的実行")
            strategies.append("ロールバック計画")
        
        return strategies
    
    def _estimate_downtime(self, risk_level: RiskLevel) -> str:
        """ダウンタイム予測"""
        downtime_estimates = {
            RiskLevel.MINIMAL: "0分",
            RiskLevel.LOW: "1-5分",
            RiskLevel.MEDIUM: "5-15分",
            RiskLevel.HIGH: "15-60分",
            RiskLevel.CRITICAL: "1-4時間"
        }
        return downtime_estimates.get(risk_level, "未知")
    
    def _assess_rollback_complexity(self, dependency_count: int, is_eternal: bool) -> str:
        """ロールバック複雑度評価"""
        if is_eternal and dependency_count > 10:
            return "非常に複雑"
        elif is_eternal or dependency_count > 5:
            return "複雑"
        elif dependency_count > 2:
            return "中程度"
        else:
            return "簡単"
    
    def _calculate_deadline(self, risk_level: RiskLevel) -> datetime:
        """申請期限計算"""
        now = datetime.now(timezone.utc)
        
        deadline_hours = {
            RiskLevel.MINIMAL: 24,      # 1日
            RiskLevel.LOW: 72,          # 3日
            RiskLevel.MEDIUM: 168,      # 1週間
            RiskLevel.HIGH: 336,        # 2週間
            RiskLevel.CRITICAL: 720     # 1ヶ月
        }
        
        hours = deadline_hours.get(risk_level, 168)
        return now + timedelta(hours=hours)
    
    async def _initiate_sage_review(self, request: ApprovalRequest):
        """4賢者審査開始"""
        try:
            # 4賢者審査実行
            sage_reviews = await self.four_sages.conduct_sage_review(request)
            
            # 審査結果を申請に追加
            request.sage_reviews = sage_reviews
            request.status = ApprovalStatus.SAGE_REVIEW
            
            # データベース更新
            await self._update_approval_request(request)
            
            # 賢者コンセンサス評価
            await self._evaluate_sage_consensus(request)
            
        except Exception as e:
            logger.error(f"❌ 4賢者審査開始エラー: {e}")
            raise
    
    async def _evaluate_sage_consensus(self, request: ApprovalRequest):
        """4賢者コンセンサス評価"""
        try:
            if not request.sage_reviews:
                return
            
            # 各賢者のリスク評価を集計
            risk_scores = []
            for review in request.sage_reviews:
                risk_scores.append(self._risk_level_to_score(review.risk_evaluation))
            
            # 平均リスクスコア
            avg_risk_score = sum(risk_scores) / len(risk_scores)
            consensus_risk = self._score_to_risk_level(avg_risk_score)
            
            # 承認基準取得
            threshold = self.approval_thresholds[consensus_risk]
            
            # 賢者の推奨に基づくコンセンサス率計算
            positive_reviews = sum(1 for review in request.sage_reviews 
                                 if "承認" in review.recommendation or "可能" in review.recommendation)
            consensus_rate = positive_reviews / len(request.sage_reviews)
            
            # 自動承認の判定
            if (consensus_rate >= threshold['sage_consensus'] and 
                not threshold['elder_required']):
                # 自動承認
                request.status = ApprovalStatus.APPROVED
                request.approved_by = "auto_sage_consensus"
                request.approved_at = datetime.now(timezone.utc)
                request.elder_notes = f"4賢者コンセンサス率{consensus_rate:.1%}による自動承認"
            else:
                # グランドエルダー審査へ
                request.status = ApprovalStatus.ELDER_REVIEW
            
            await self._update_approval_request(request)
            
            logger.info(f"🏛️ 4賢者コンセンサス評価完了: {request.request_id} - {request.status.value}")
            
        except Exception as e:
            logger.error(f"❌ コンセンサス評価エラー: {e}")
            raise
    
    def _risk_level_to_score(self, risk_level: RiskLevel) -> int:
        """リスクレベルをスコアに変換"""
        score_map = {
            RiskLevel.MINIMAL: 1,
            RiskLevel.LOW: 2,
            RiskLevel.MEDIUM: 3,
            RiskLevel.HIGH: 4,
            RiskLevel.CRITICAL: 5
        }
        return score_map.get(risk_level, 3)
    
    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """スコアをリスクレベルに変換"""
        if score >= 4.5:
            return RiskLevel.CRITICAL
        elif score >= 3.5:
            return RiskLevel.HIGH
        elif score >= 2.5:
            return RiskLevel.MEDIUM
        elif score >= 1.5:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL
    
    async def grand_elder_approval(self, request_id: str, approved: bool,
                                 elder_name: str, notes: str = "") -> bool:
        """グランドエルダーによる最終承認"""
        try:
            # 申請取得
            request = await self._get_approval_request(request_id)
            if not request:
                raise ValueError(f"Approval request not found: {request_id}")
            
            if request.status != ApprovalStatus.ELDER_REVIEW:
                raise ValueError(f"Request not ready for elder approval: {request.status}")
            
            if approved:
                request.status = ApprovalStatus.APPROVED
                request.approved_by = elder_name
                request.approved_at = datetime.now(timezone.utc)
                request.elder_notes = notes
            else:
                request.status = ApprovalStatus.REJECTED
                request.rejected_reason = notes
            
            await self._update_approval_request(request)
            
            logger.info(f"🏛️ グランドエルダー決定: {request_id} - {'承認' if approved else '却下'}")
            return True
            
        except Exception as e:
            logger.error(f"❌ グランドエルダー承認エラー: {e}")
            return False
    
    async def get_pending_requests(self, elder_name: Optional[str] = None) -> List[ApprovalRequest]:
        """保留中申請一覧取得"""
        # 実装簡略化：実際はデータベースから取得
        return []
    
    async def _save_approval_request(self, request: ApprovalRequest):
        """承認申請保存"""
        # PostgreSQLのgrand_elder_permissionsテーブルに保存
        await self.database.request_spell_dispel(
            request.spell_id,
            request.request_reason,
            request.requested_by
        )
    
    async def _update_approval_request(self, request: ApprovalRequest):
        """承認申請更新"""
        # 実装簡略化：実際はデータベース更新
        pass
    
    async def _get_approval_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """承認申請取得"""
        # 実装簡略化：実際はデータベースから取得
        return None
    
    async def close(self):
        """リソースクローズ"""
        await self.database.close()
        logger.info("🏛️ Grand Elder Approval System closed")

# 使用例とテスト用関数
async def test_grand_elder_system():
    """テスト実行"""
    approval_system = GrandElderApprovalSystem()
    
    try:
        await approval_system.initialize()
        
        # 承認申請テスト
        request_id = await approval_system.submit_approval_request(
            spell_id="test-spell-id",
            permission_type=PermissionType.DISPEL,
            reason="テスト用の解呪申請",
            requester="test_user"
        )
        
        print(f"✅ 承認申請作成: {request_id}")
        
        # グランドエルダー承認テスト
        approval_result = await approval_system.grand_elder_approval(
            request_id=request_id,
            approved=True,
            elder_name="Grand Elder Test",
            notes="テスト承認"
        )
        
        print(f"✅ グランドエルダー承認: {approval_result}")
        
    finally:
        await approval_system.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_grand_elder_system())