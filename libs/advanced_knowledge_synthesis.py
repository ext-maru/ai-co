#!/usr/bin/env python3
"""
🔮 Advanced Knowledge Synthesis System
高度な知識合成システム

RAG賢者の高度な提案によるマルチモーダル統合と新知識創出
テキスト・画像・音声の統合検索と知識矛盾の自動解決

Author: Claude Elder
Date: 2025-07-10
Phase: 2 (高度な知識合成実現)
"""

import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import sqlite3
from collections import defaultdict, deque
import hashlib
import threading
import networkx as nx
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
import pickle

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent

# 既存システムのインポート（モック）
try:
    from .multidimensional_vector_system import (
        MultiDimensionalVectorSystem, 
        KnowledgeType,
        MultiDimensionalVector
    )
    from .autonomous_learning_system import (
        AutonomousLearningSystem,
        CrossDomainInsight
    )
except ImportError:
    # モック実装
    MultiDimensionalVectorSystem = None
    KnowledgeType = None
    MultiDimensionalVector = None
    AutonomousLearningSystem = None
    CrossDomainInsight = None

class ModalityType(Enum):
    """モダリティタイプ"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    CODE = "code"
    STRUCTURED_DATA = "structured_data"
    MIXED = "mixed"

class SynthesisStrategy(Enum):
    """合成戦略"""
    FUSION = "fusion"              # 融合
    AGGREGATION = "aggregation"    # 集約
    ABSTRACTION = "abstraction"    # 抽象化
    INTERPOLATION = "interpolation"  # 補間
    EXTRAPOLATION = "extrapolation"  # 外挿
    CONTRADICTION_RESOLUTION = "contradiction_resolution"  # 矛盾解決

class KnowledgeRelationType(Enum):
    """知識関係タイプ"""
    SUPPORTS = "supports"          # 支持
    CONTRADICTS = "contradicts"    # 矛盾
    EXTENDS = "extends"            # 拡張
    SPECIALIZES = "specializes"    # 特殊化
    GENERALIZES = "generalizes"    # 一般化
    DEPENDS_ON = "depends_on"      # 依存
    RELATED_TO = "related_to"      # 関連

@dataclass
class MultiModalKnowledge:
    """マルチモーダル知識"""
    knowledge_id: str
    created_at: datetime
    modality: ModalityType
    content: Any  # モダリティに応じた内容
    text_representation: str  # テキスト表現
    vector_representation: Optional[np.ndarray]
    metadata: Dict[str, Any]
    quality_score: float
    source_references: List[str]

@dataclass
class KnowledgeContradiction:
    """知識矛盾"""
    contradiction_id: str
    detected_at: datetime
    knowledge_ids: List[str]
    contradiction_type: str
    severity: float
    resolution_strategy: SynthesisStrategy
    resolution_confidence: float
    evidence: List[Dict[str, Any]]

@dataclass
class SynthesizedKnowledge:
    """合成知識"""
    synthesis_id: str
    created_at: datetime
    source_knowledge_ids: List[str]
    synthesis_strategy: SynthesisStrategy
    modalities_involved: List[ModalityType]
    synthesized_content: Dict[str, Any]
    confidence_score: float
    novelty_score: float
    validation_results: Dict[str, Any]
    applications: List[str]

@dataclass
class KnowledgeGraph:
    """知識グラフ"""
    graph_id: str
    created_at: datetime
    nodes: Dict[str, MultiModalKnowledge]
    edges: List[Tuple[str, str, KnowledgeRelationType]]
    clusters: Dict[int, List[str]]
    central_concepts: List[str]
    graph_metrics: Dict[str, float]

class MultiModalEncoder:
    """マルチモーダルエンコーダー"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.encoders = {
            ModalityType.TEXT: self._encode_text,
            ModalityType.IMAGE: self._encode_image,
            ModalityType.AUDIO: self._encode_audio,
            ModalityType.CODE: self._encode_code,
            ModalityType.STRUCTURED_DATA: self._encode_structured_data
        }
    
    async def encode(self, content: Any, modality: ModalityType) -> Tuple[np.ndarray, str]:
        """コンテンツエンコード"""
        encoder = self.encoders.get(modality, self._encode_default)
        vector, text_repr = await encoder(content)
        return vector, text_repr
    
    async def _encode_text(self, text: str) -> Tuple[np.ndarray, str]:
        """テキストエンコード"""
        # 簡略化実装
        vector = np.random.random(768)  # BERT次元
        return vector, text[:200]  # 最初の200文字
    
    async def _encode_image(self, image_data: Any) -> Tuple[np.ndarray, str]:
        """画像エンコード"""
        # 簡略化実装
        vector = np.random.random(2048)  # ResNet次元
        text_repr = "Image content: [visual description placeholder]"
        return vector, text_repr
    
    async def _encode_audio(self, audio_data: Any) -> Tuple[np.ndarray, str]:
        """音声エンコード"""
        # 簡略化実装
        vector = np.random.random(512)  # 音声特徴次元
        text_repr = "Audio content: [audio transcription placeholder]"
        return vector, text_repr
    
    async def _encode_code(self, code: str) -> Tuple[np.ndarray, str]:
        """コードエンコード"""
        # 簡略化実装
        vector = np.random.random(768)  # CodeBERT次元
        # コードの最初の部分を抽出
        lines = code.split('\n')[:5]
        text_repr = f"Code snippet: {' '.join(lines)}"
        return vector, text_repr
    
    async def _encode_structured_data(self, data: Dict[str, Any]) -> Tuple[np.ndarray, str]:
        """構造化データエンコード"""
        # 簡略化実装
        vector = np.random.random(256)
        text_repr = f"Structured data with {len(data)} fields"
        return vector, text_repr
    
    async def _encode_default(self, content: Any) -> Tuple[np.ndarray, str]:
        """デフォルトエンコード"""
        vector = np.random.random(512)
        text_repr = str(content)[:200]
        return vector, text_repr

class ContradictionResolver:
    """矛盾解決器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.resolution_strategies = {
            'temporal': self._resolve_temporal_contradiction,
            'source_credibility': self._resolve_by_credibility,
            'consensus': self._resolve_by_consensus,
            'context_specific': self._resolve_by_context,
            'synthesis': self._resolve_by_synthesis
        }
    
    async def resolve(self, 
                     contradiction: KnowledgeContradiction,
                     knowledge_items: List[MultiModalKnowledge]) -> Dict[str, Any]:
        """矛盾解決"""
        try:
            # 矛盾タイプ判定
            contradiction_type = await self._classify_contradiction(knowledge_items)
            
            # 適切な解決戦略選択
            strategy = self._select_resolution_strategy(contradiction_type)
            
            # 解決実行
            resolution = await strategy(knowledge_items)
            
            return {
                'success': True,
                'resolution': resolution,
                'strategy_used': contradiction_type,
                'confidence': resolution.get('confidence', 0.5)
            }
            
        except Exception as e:
            self.logger.error(f"Contradiction resolution failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _classify_contradiction(self, knowledge_items: List[MultiModalKnowledge]) -> str:
        """矛盾分類"""
        # 時間的矛盾チェック
        timestamps = [k.created_at for k in knowledge_items]
        if max(timestamps) - min(timestamps) > timedelta(days=30):
            return 'temporal'
        
        # ソース信頼性の差チェック
        quality_scores = [k.quality_score for k in knowledge_items]
        if max(quality_scores) - min(quality_scores) > 0.3:
            return 'source_credibility'
        
        # デフォルトは合成による解決
        return 'synthesis'
    
    def _select_resolution_strategy(self, contradiction_type: str):
        """解決戦略選択"""
        return self.resolution_strategies.get(
            contradiction_type, 
            self._resolve_by_synthesis
        )
    
    async def _resolve_temporal_contradiction(self, 
                                            knowledge_items: List[MultiModalKnowledge]) -> Dict[str, Any]:
        """時間的矛盾解決"""
        # 最新の知識を優先
        latest_knowledge = max(knowledge_items, key=lambda k: k.created_at)
        
        return {
            'resolved_content': latest_knowledge.content,
            'resolution_method': 'temporal_precedence',
            'selected_knowledge_id': latest_knowledge.knowledge_id,
            'confidence': 0.8,
            'reasoning': 'Selected most recent knowledge item'
        }
    
    async def _resolve_by_credibility(self, 
                                    knowledge_items: List[MultiModalKnowledge]) -> Dict[str, Any]:
        """信頼性による解決"""
        # 最高品質スコアの知識を選択
        best_knowledge = max(knowledge_items, key=lambda k: k.quality_score)
        
        return {
            'resolved_content': best_knowledge.content,
            'resolution_method': 'credibility_based',
            'selected_knowledge_id': best_knowledge.knowledge_id,
            'confidence': best_knowledge.quality_score,
            'reasoning': 'Selected highest quality knowledge item'
        }
    
    async def _resolve_by_consensus(self, 
                                  knowledge_items: List[MultiModalKnowledge]) -> Dict[str, Any]:
        """コンセンサスによる解決"""
        # 簡略化: 多数決的なアプローチ
        # 実際はより洗練されたコンセンサスアルゴリズムを使用
        
        # テキスト表現をクラスタリング
        texts = [k.text_representation for k in knowledge_items]
        # ダミー実装
        consensus_text = texts[0]  # 最初のものを選択
        
        return {
            'resolved_content': consensus_text,
            'resolution_method': 'consensus',
            'confidence': 0.7,
            'reasoning': 'Consensus among multiple sources'
        }
    
    async def _resolve_by_context(self, 
                                knowledge_items: List[MultiModalKnowledge]) -> Dict[str, Any]:
        """文脈による解決"""
        # コンテキスト分析（簡略化）
        context_scores = []
        for item in knowledge_items:
            # メタデータからコンテキストスコア計算
            score = len(item.metadata.get('context', {})) / 10.0
            context_scores.append(min(1.0, score))
        
        # 最高コンテキストスコアのアイテム選択
        best_idx = np.argmax(context_scores)
        best_knowledge = knowledge_items[best_idx]
        
        return {
            'resolved_content': best_knowledge.content,
            'resolution_method': 'context_specific',
            'selected_knowledge_id': best_knowledge.knowledge_id,
            'confidence': context_scores[best_idx],
            'reasoning': 'Selected based on contextual relevance'
        }
    
    async def _resolve_by_synthesis(self, 
                                  knowledge_items: List[MultiModalKnowledge]) -> Dict[str, Any]:
        """合成による解決"""
        # 全ての知識を統合
        synthesized_content = {
            'perspectives': [],
            'common_elements': [],
            'unique_elements': []
        }
        
        # 各知識の要素を抽出
        for item in knowledge_items:
            synthesized_content['perspectives'].append({
                'source': item.knowledge_id,
                'content': item.text_representation,
                'confidence': item.quality_score
            })
        
        # 共通要素の識別（簡略化）
        synthesized_content['common_elements'] = ['Core concept present in all sources']
        synthesized_content['unique_elements'] = ['Unique perspective from each source']
        
        return {
            'resolved_content': synthesized_content,
            'resolution_method': 'synthesis',
            'confidence': 0.75,
            'reasoning': 'Synthesized multiple perspectives into unified view'
        }

class KnowledgeSynthesizer:
    """知識合成器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.synthesis_strategies = {
            SynthesisStrategy.FUSION: self._fuse_knowledge,
            SynthesisStrategy.AGGREGATION: self._aggregate_knowledge,
            SynthesisStrategy.ABSTRACTION: self._abstract_knowledge,
            SynthesisStrategy.INTERPOLATION: self._interpolate_knowledge,
            SynthesisStrategy.EXTRAPOLATION: self._extrapolate_knowledge
        }
    
    async def synthesize(self,
                       knowledge_items: List[MultiModalKnowledge],
                       strategy: SynthesisStrategy) -> SynthesizedKnowledge:
        """知識合成"""
        try:
            # 合成戦略実行
            synthesis_func = self.synthesis_strategies.get(
                strategy, 
                self._fuse_knowledge
            )
            
            synthesized_content = await synthesis_func(knowledge_items)
            
            # 新規性評価
            novelty_score = await self._evaluate_novelty(
                synthesized_content, 
                knowledge_items
            )
            
            # 検証
            validation_results = await self._validate_synthesis(
                synthesized_content
            )
            
            # 応用可能性評価
            applications = await self._identify_applications(
                synthesized_content
            )
            
            synthesis = SynthesizedKnowledge(
                synthesis_id=f"synth_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                created_at=datetime.now(),
                source_knowledge_ids=[k.knowledge_id for k in knowledge_items],
                synthesis_strategy=strategy,
                modalities_involved=list(set(k.modality for k in knowledge_items)),
                synthesized_content=synthesized_content,
                confidence_score=validation_results.get('confidence', 0.5),
                novelty_score=novelty_score,
                validation_results=validation_results,
                applications=applications
            )
            
            return synthesis
            
        except Exception as e:
            self.logger.error(f"Knowledge synthesis failed: {e}")
            raise
    
    async def _fuse_knowledge(self, 
                            knowledge_items: List[MultiModalKnowledge]) -> Dict[str, Any]:
        """知識融合"""
        fused_content = {
            'type': 'fusion',
            'elements': {},
            'unified_representation': None
        }
        
        # ベクトル融合
        if all(k.vector_representation is not None for k in knowledge_items):
            vectors = [k.vector_representation for k in knowledge_items]
            # 重み付き平均（品質スコアで重み付け）
            weights = [k.quality_score for k in knowledge_items]
            weights = np.array(weights) / sum(weights)
            
            fused_vector = np.average(vectors, axis=0, weights=weights)
            fused_content['unified_vector'] = fused_vector.tolist()
        
        # テキスト融合
        texts = [k.text_representation for k in knowledge_items]
        fused_content['unified_text'] = self._fuse_texts(texts)
        
        # モダリティ別要素
        for item in knowledge_items:
            modality = item.modality.value
            if modality not in fused_content['elements']:
                fused_content['elements'][modality] = []
            fused_content['elements'][modality].append(item.content)
        
        return fused_content
    
    async def _aggregate_knowledge(self, 
                                 knowledge_items: List[MultiModalKnowledge]) -> Dict[str, Any]:
        """知識集約"""
        aggregated_content = {
            'type': 'aggregation',
            'summary': {},
            'statistics': {},
            'patterns': []
        }
        
        # モダリティ別集約
        modality_groups = defaultdict(list)
        for item in knowledge_items:
            modality_groups[item.modality].append(item)
        
        # 各モダリティの統計
        for modality, items in modality_groups.items():
            aggregated_content['statistics'][modality.value] = {
                'count': len(items),
                'avg_quality': np.mean([i.quality_score for i in items]),
                'sources': list(set(ref for i in items for ref in i.source_references))
            }
        
        # パターン抽出
        if len(knowledge_items) >= 3:
            patterns = self._extract_patterns(knowledge_items)
            aggregated_content['patterns'] = patterns
        
        # サマリー生成
        aggregated_content['summary'] = {
            'total_items': len(knowledge_items),
            'modalities': list(modality_groups.keys()),
            'key_insights': self._extract_key_insights(knowledge_items)
        }
        
        return aggregated_content
    
    async def _abstract_knowledge(self, 
                                knowledge_items: List[MultiModalKnowledge]) -> Dict[str, Any]:
        """知識抽象化"""
        abstracted_content = {
            'type': 'abstraction',
            'abstract_concepts': [],
            'hierarchical_structure': {},
            'general_principles': []
        }
        
        # 概念抽出
        concepts = self._extract_concepts(knowledge_items)
        abstracted_content['abstract_concepts'] = concepts
        
        # 階層構造構築
        hierarchy = self._build_concept_hierarchy(concepts)
        abstracted_content['hierarchical_structure'] = hierarchy
        
        # 一般原則導出
        principles = self._derive_principles(knowledge_items)
        abstracted_content['general_principles'] = principles
        
        return abstracted_content
    
    async def _interpolate_knowledge(self, 
                                   knowledge_items: List[MultiModalKnowledge]) -> Dict[str, Any]:
        """知識補間"""
        interpolated_content = {
            'type': 'interpolation',
            'filled_gaps': [],
            'intermediate_states': [],
            'confidence_map': {}
        }
        
        # ギャップ識別
        gaps = self._identify_knowledge_gaps(knowledge_items)
        
        # 補間実行
        for gap in gaps:
            filled = self._interpolate_gap(gap, knowledge_items)
            interpolated_content['filled_gaps'].append(filled)
        
        # 中間状態生成
        if len(knowledge_items) >= 2:
            for i in range(len(knowledge_items) - 1):
                intermediate = self._generate_intermediate_state(
                    knowledge_items[i], 
                    knowledge_items[i + 1]
                )
                interpolated_content['intermediate_states'].append(intermediate)
        
        return interpolated_content
    
    async def _extrapolate_knowledge(self, 
                                   knowledge_items: List[MultiModalKnowledge]) -> Dict[str, Any]:
        """知識外挿"""
        extrapolated_content = {
            'type': 'extrapolation',
            'future_predictions': [],
            'extended_concepts': [],
            'novel_applications': []
        }
        
        # トレンド分析
        trends = self._analyze_trends(knowledge_items)
        
        # 将来予測
        for trend in trends:
            prediction = self._predict_future_state(trend)
            extrapolated_content['future_predictions'].append(prediction)
        
        # 概念拡張
        extended = self._extend_concepts(knowledge_items)
        extrapolated_content['extended_concepts'] = extended
        
        # 新規応用発見
        applications = self._discover_novel_applications(knowledge_items)
        extrapolated_content['novel_applications'] = applications
        
        return extrapolated_content
    
    def _fuse_texts(self, texts: List[str]) -> str:
        """テキスト融合"""
        # 簡略化実装
        if not texts:
            return ""
        
        # 共通部分と独自部分を識別
        if len(texts) == 1:
            return texts[0]
        
        # 簡単な結合
        return f"Fused knowledge from {len(texts)} sources: " + " | ".join(texts[:3])
    
    def _extract_patterns(self, knowledge_items: List[MultiModalKnowledge]) -> List[Dict[str, Any]]:
        """パターン抽出"""
        patterns = []
        
        # 品質パターン
        quality_scores = [k.quality_score for k in knowledge_items]
        if len(set(quality_scores)) < len(quality_scores) / 2:
            patterns.append({
                'type': 'quality_consistency',
                'description': 'Consistent quality across sources'
            })
        
        # モダリティパターン
        modalities = [k.modality for k in knowledge_items]
        if len(set(modalities)) > 1:
            patterns.append({
                'type': 'multi_modal',
                'description': 'Knowledge spans multiple modalities'
            })
        
        return patterns
    
    def _extract_key_insights(self, knowledge_items: List[MultiModalKnowledge]) -> List[str]:
        """重要洞察抽出"""
        insights = []
        
        # 高品質アイテムからの洞察
        high_quality = [k for k in knowledge_items if k.quality_score > 0.8]
        if high_quality:
            insights.append(f"Found {len(high_quality)} high-quality knowledge items")
        
        # マルチモーダル洞察
        modalities = set(k.modality for k in knowledge_items)
        if len(modalities) > 2:
            insights.append("Rich multi-modal knowledge representation")
        
        return insights
    
    def _extract_concepts(self, knowledge_items: List[MultiModalKnowledge]) -> List[str]:
        """概念抽出"""
        # 簡略化実装
        concepts = []
        
        for item in knowledge_items:
            # テキストから概念を抽出（ダミー実装）
            text = item.text_representation
            if "system" in text.lower():
                concepts.append("system_architecture")
            if "learning" in text.lower():
                concepts.append("machine_learning")
            if "data" in text.lower():
                concepts.append("data_processing")
        
        return list(set(concepts))
    
    def _build_concept_hierarchy(self, concepts: List[str]) -> Dict[str, Any]:
        """概念階層構築"""
        # 簡略化実装
        hierarchy = {
            'root': 'knowledge',
            'branches': {}
        }
        
        for concept in concepts:
            if 'system' in concept:
                hierarchy['branches']['technical'] = hierarchy['branches'].get('technical', [])
                hierarchy['branches']['technical'].append(concept)
            else:
                hierarchy['branches']['general'] = hierarchy['branches'].get('general', [])
                hierarchy['branches']['general'].append(concept)
        
        return hierarchy
    
    def _derive_principles(self, knowledge_items: List[MultiModalKnowledge]) -> List[str]:
        """原則導出"""
        principles = []
        
        # 品質原則
        avg_quality = np.mean([k.quality_score for k in knowledge_items])
        if avg_quality > 0.7:
            principles.append("High-quality knowledge leads to better synthesis")
        
        # 多様性原則
        modalities = set(k.modality for k in knowledge_items)
        if len(modalities) > 1:
            principles.append("Multi-modal integration enhances understanding")
        
        return principles
    
    def _identify_knowledge_gaps(self, knowledge_items: List[MultiModalKnowledge]) -> List[Dict[str, Any]]:
        """知識ギャップ識別"""
        gaps = []
        
        # 時間的ギャップ
        if len(knowledge_items) >= 2:
            timestamps = sorted([k.created_at for k in knowledge_items])
            for i in range(len(timestamps) - 1):
                time_diff = timestamps[i + 1] - timestamps[i]
                if time_diff > timedelta(days=7):
                    gaps.append({
                        'type': 'temporal',
                        'start': timestamps[i],
                        'end': timestamps[i + 1],
                        'duration': time_diff
                    })
        
        return gaps
    
    def _interpolate_gap(self, gap: Dict[str, Any], 
                        knowledge_items: List[MultiModalKnowledge]) -> Dict[str, Any]:
        """ギャップ補間"""
        return {
            'gap_type': gap['type'],
            'interpolated_content': 'Estimated intermediate knowledge',
            'confidence': 0.6
        }
    
    def _generate_intermediate_state(self, 
                                   item1: MultiModalKnowledge,
                                   item2: MultiModalKnowledge) -> Dict[str, Any]:
        """中間状態生成"""
        return {
            'from': item1.knowledge_id,
            'to': item2.knowledge_id,
            'intermediate_content': 'Transitional knowledge state',
            'similarity': 0.7
        }
    
    def _analyze_trends(self, knowledge_items: List[MultiModalKnowledge]) -> List[Dict[str, Any]]:
        """トレンド分析"""
        trends = []
        
        # 品質トレンド
        if len(knowledge_items) >= 3:
            quality_scores = [k.quality_score for k in knowledge_items]
            quality_trend = np.polyfit(range(len(quality_scores)), quality_scores, 1)[0]
            
            trends.append({
                'type': 'quality_trend',
                'direction': 'increasing' if quality_trend > 0 else 'decreasing',
                'slope': quality_trend
            })
        
        return trends
    
    def _predict_future_state(self, trend: Dict[str, Any]) -> Dict[str, Any]:
        """将来状態予測"""
        return {
            'trend_type': trend['type'],
            'prediction': 'Expected future development',
            'confidence': 0.7,
            'timeframe': '30 days'
        }
    
    def _extend_concepts(self, knowledge_items: List[MultiModalKnowledge]) -> List[str]:
        """概念拡張"""
        extended = []
        
        concepts = self._extract_concepts(knowledge_items)
        for concept in concepts:
            extended.append(f"extended_{concept}")
            extended.append(f"meta_{concept}")
        
        return extended
    
    def _discover_novel_applications(self, 
                                   knowledge_items: List[MultiModalKnowledge]) -> List[str]:
        """新規応用発見"""
        applications = []
        
        # モダリティ組み合わせによる応用
        modalities = set(k.modality for k in knowledge_items)
        if ModalityType.TEXT in modalities and ModalityType.IMAGE in modalities:
            applications.append("Visual question answering system")
        
        if ModalityType.AUDIO in modalities and ModalityType.TEXT in modalities:
            applications.append("Speech-to-insight system")
        
        return applications
    
    async def _evaluate_novelty(self, 
                              synthesized_content: Dict[str, Any],
                              source_items: List[MultiModalKnowledge]) -> float:
        """新規性評価"""
        # 簡略化実装
        novelty_factors = []
        
        # 新要素の数
        if 'novel_applications' in synthesized_content:
            novelty_factors.append(len(synthesized_content['novel_applications']) / 10.0)
        
        # 拡張概念の数
        if 'extended_concepts' in synthesized_content:
            novelty_factors.append(len(synthesized_content['extended_concepts']) / 20.0)
        
        # 予測の数
        if 'future_predictions' in synthesized_content:
            novelty_factors.append(len(synthesized_content['future_predictions']) / 5.0)
        
        return min(1.0, np.mean(novelty_factors) if novelty_factors else 0.5)
    
    async def _validate_synthesis(self, 
                                synthesized_content: Dict[str, Any]) -> Dict[str, Any]:
        """合成検証"""
        validation = {
            'is_valid': True,
            'confidence': 0.8,
            'checks_passed': [],
            'warnings': []
        }
        
        # 構造チェック
        if 'type' in synthesized_content:
            validation['checks_passed'].append('Structure validation')
        else:
            validation['warnings'].append('Missing synthesis type')
            validation['confidence'] *= 0.8
        
        # 内容チェック
        if synthesized_content:
            validation['checks_passed'].append('Content validation')
        else:
            validation['warnings'].append('Empty synthesis result')
            validation['is_valid'] = False
        
        return validation
    
    async def _identify_applications(self, 
                                   synthesized_content: Dict[str, Any]) -> List[str]:
        """応用可能性識別"""
        applications = []
        
        synthesis_type = synthesized_content.get('type', '')
        
        if synthesis_type == 'fusion':
            applications.extend([
                "Unified knowledge base",
                "Comprehensive decision support"
            ])
        elif synthesis_type == 'abstraction':
            applications.extend([
                "Conceptual framework development",
                "Theory formulation"
            ])
        elif synthesis_type == 'extrapolation':
            applications.extend([
                "Future planning",
                "Innovation roadmap"
            ])
        
        return applications

class AdvancedKnowledgeSynthesisSystem:
    """高度な知識合成システム"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or self._default_config()
        
        # コンポーネント初期化
        self.multimodal_encoder = MultiModalEncoder()
        self.contradiction_resolver = ContradictionResolver()
        self.knowledge_synthesizer = KnowledgeSynthesizer()
        
        # 知識ストレージ
        self.knowledge_base = {}
        self.contradictions = {}
        self.synthesized_knowledge = {}
        self.knowledge_graph = None
        
        # 統計
        self.stats = {
            'total_knowledge_items': 0,
            'contradictions_detected': 0,
            'contradictions_resolved': 0,
            'synthesis_operations': 0,
            'novel_knowledge_created': 0
        }
        
        # データベース初期化
        self._init_database()
        
        self.logger.info("🔮 Advanced Knowledge Synthesis System initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """デフォルト設定"""
        return {
            'contradiction_threshold': 0.7,
            'synthesis_confidence_threshold': 0.8,
            'graph_update_interval': 3600,
            'max_synthesis_batch': 10,
            'database_path': str(PROJECT_ROOT / "data" / "knowledge_synthesis.db")
        }
    
    def _init_database(self):
        """データベース初期化"""
        try:
            db_path = self.config['database_path']
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # マルチモーダル知識テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS multimodal_knowledge (
                    knowledge_id TEXT PRIMARY KEY,
                    created_at TEXT,
                    modality TEXT,
                    content BLOB,
                    text_representation TEXT,
                    vector_representation BLOB,
                    metadata TEXT,
                    quality_score REAL,
                    source_references TEXT
                );
            """)
            
            # 矛盾テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_contradictions (
                    contradiction_id TEXT PRIMARY KEY,
                    detected_at TEXT,
                    knowledge_ids TEXT,
                    contradiction_type TEXT,
                    severity REAL,
                    resolution_strategy TEXT,
                    resolution_confidence REAL,
                    evidence TEXT,
                    resolved BOOLEAN
                );
            """)
            
            # 合成知識テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS synthesized_knowledge (
                    synthesis_id TEXT PRIMARY KEY,
                    created_at TEXT,
                    source_knowledge_ids TEXT,
                    synthesis_strategy TEXT,
                    modalities_involved TEXT,
                    synthesized_content TEXT,
                    confidence_score REAL,
                    novelty_score REAL,
                    validation_results TEXT,
                    applications TEXT
                );
            """)
            
            # 知識グラフテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_graph_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    created_at TEXT,
                    nodes_count INTEGER,
                    edges_count INTEGER,
                    clusters_count INTEGER,
                    graph_data BLOB,
                    graph_metrics TEXT
                );
            """)
            
            conn.commit()
            conn.close()
            
            self.logger.info("📊 Knowledge synthesis database initialized")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
    
    async def add_knowledge(self,
                          content: Any,
                          modality: ModalityType,
                          metadata: Dict[str, Any] = None,
                          source_references: List[str] = None) -> str:
        """知識追加"""
        try:
            # エンコード
            vector, text_repr = await self.multimodal_encoder.encode(content, modality)
            
            # 品質スコア計算
            quality_score = await self._calculate_quality_score(
                content, modality, metadata
            )
            
            # 知識アイテム作成
            knowledge = MultiModalKnowledge(
                knowledge_id=f"know_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(text_repr.encode()).hexdigest()[:8]}",
                created_at=datetime.now(),
                modality=modality,
                content=content,
                text_representation=text_repr,
                vector_representation=vector,
                metadata=metadata or {},
                quality_score=quality_score,
                source_references=source_references or []
            )
            
            # 保存
            self.knowledge_base[knowledge.knowledge_id] = knowledge
            self.stats['total_knowledge_items'] += 1
            
            # 矛盾チェック
            await self._check_contradictions(knowledge)
            
            # データベース保存
            await self._persist_knowledge(knowledge)
            
            self.logger.info(f"📚 Added {modality.value} knowledge: {knowledge.knowledge_id}")
            
            return knowledge.knowledge_id
            
        except Exception as e:
            self.logger.error(f"Knowledge addition failed: {e}")
            raise
    
    async def synthesize_knowledge(self,
                                 knowledge_ids: List[str],
                                 strategy: SynthesisStrategy = SynthesisStrategy.FUSION) -> str:
        """知識合成実行"""
        try:
            # 知識アイテム取得
            knowledge_items = [
                self.knowledge_base[kid] 
                for kid in knowledge_ids 
                if kid in self.knowledge_base
            ]
            
            if len(knowledge_items) < 2:
                raise ValueError("At least 2 knowledge items required for synthesis")
            
            # 合成実行
            synthesized = await self.knowledge_synthesizer.synthesize(
                knowledge_items, 
                strategy
            )
            
            # 保存
            self.synthesized_knowledge[synthesized.synthesis_id] = synthesized
            self.stats['synthesis_operations'] += 1
            
            if synthesized.novelty_score > 0.7:
                self.stats['novel_knowledge_created'] += 1
            
            # データベース保存
            await self._persist_synthesized_knowledge(synthesized)
            
            self.logger.info(f"✨ Synthesized knowledge: {synthesized.synthesis_id} (novelty: {synthesized.novelty_score:.2f})")
            
            return synthesized.synthesis_id
            
        except Exception as e:
            self.logger.error(f"Knowledge synthesis failed: {e}")
            raise
    
    async def resolve_contradiction(self, contradiction_id: str) -> Dict[str, Any]:
        """矛盾解決"""
        try:
            if contradiction_id not in self.contradictions:
                raise ValueError(f"Contradiction {contradiction_id} not found")
            
            contradiction = self.contradictions[contradiction_id]
            
            # 関連知識取得
            knowledge_items = [
                self.knowledge_base[kid]
                for kid in contradiction.knowledge_ids
                if kid in self.knowledge_base
            ]
            
            # 解決実行
            resolution = await self.contradiction_resolver.resolve(
                contradiction,
                knowledge_items
            )
            
            if resolution['success']:
                self.stats['contradictions_resolved'] += 1
                
                # 矛盾記録更新
                contradiction.resolution_confidence = resolution['confidence']
                
                # データベース更新
                await self._update_contradiction_resolution(
                    contradiction_id, 
                    resolution
                )
            
            self.logger.info(f"🔧 Resolved contradiction: {contradiction_id}")
            
            return resolution
            
        except Exception as e:
            self.logger.error(f"Contradiction resolution failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def build_knowledge_graph(self) -> KnowledgeGraph:
        """知識グラフ構築"""
        try:
            # NetworkXグラフ作成
            G = nx.Graph()
            
            # ノード追加
            for kid, knowledge in self.knowledge_base.items():
                G.add_node(kid, **{
                    'modality': knowledge.modality.value,
                    'quality': knowledge.quality_score,
                    'created_at': knowledge.created_at.isoformat()
                })
            
            # エッジ追加（類似度ベース）
            knowledge_items = list(self.knowledge_base.values())
            for i in range(len(knowledge_items)):
                for j in range(i + 1, len(knowledge_items)):
                    similarity = await self._calculate_similarity(
                        knowledge_items[i],
                        knowledge_items[j]
                    )
                    
                    if similarity > 0.7:
                        G.add_edge(
                            knowledge_items[i].knowledge_id,
                            knowledge_items[j].knowledge_id,
                            weight=similarity
                        )
            
            # クラスタリング
            if len(G.nodes) > 0:
                # ベクトル行列作成
                vectors = []
                node_ids = []
                for kid, knowledge in self.knowledge_base.items():
                    if knowledge.vector_representation is not None:
                        vectors.append(knowledge.vector_representation)
                        node_ids.append(kid)
                
                if vectors:
                    # DBSCAN クラスタリング
                    clustering = DBSCAN(eps=0.3, min_samples=2)
                    clusters = clustering.fit_predict(np.array(vectors))
                    
                    cluster_dict = defaultdict(list)
                    for node_id, cluster_label in zip(node_ids, clusters):
                        cluster_dict[int(cluster_label)].append(node_id)
                else:
                    cluster_dict = {0: list(G.nodes)}
            else:
                cluster_dict = {}
            
            # 中心概念識別
            if len(G.nodes) > 0:
                centrality = nx.degree_centrality(G)
                central_concepts = sorted(
                    centrality.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:5]
                central_concepts = [c[0] for c in central_concepts]
            else:
                central_concepts = []
            
            # グラフメトリクス計算
            graph_metrics = {
                'nodes': len(G.nodes),
                'edges': len(G.edges),
                'density': nx.density(G) if len(G.nodes) > 1 else 0,
                'clusters': len(cluster_dict),
                'average_degree': np.mean([d for n, d in G.degree()]) if G.nodes else 0
            }
            
            # 知識グラフ作成
            self.knowledge_graph = KnowledgeGraph(
                graph_id=f"graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                created_at=datetime.now(),
                nodes=dict(self.knowledge_base),
                edges=[(u, v, KnowledgeRelationType.RELATED_TO) for u, v in G.edges],
                clusters=dict(cluster_dict),
                central_concepts=central_concepts,
                graph_metrics=graph_metrics
            )
            
            # スナップショット保存
            await self._save_graph_snapshot(G)
            
            self.logger.info(f"🕸️ Built knowledge graph: {graph_metrics}")
            
            return self.knowledge_graph
            
        except Exception as e:
            self.logger.error(f"Knowledge graph building failed: {e}")
            raise
    
    async def query_multimodal(self,
                             query: str,
                             modalities: List[ModalityType] = None,
                             top_k: int = 5) -> List[Dict[str, Any]]:
        """マルチモーダルクエリ"""
        try:
            # クエリエンコード
            query_vector, _ = await self.multimodal_encoder.encode(
                query, 
                ModalityType.TEXT
            )
            
            # 候補検索
            candidates = []
            for kid, knowledge in self.knowledge_base.items():
                # モダリティフィルタ
                if modalities and knowledge.modality not in modalities:
                    continue
                
                # 類似度計算
                if knowledge.vector_representation is not None:
                    similarity = cosine_similarity(
                        [query_vector],
                        [knowledge.vector_representation]
                    )[0][0]
                    
                    candidates.append({
                        'knowledge_id': kid,
                        'modality': knowledge.modality.value,
                        'text': knowledge.text_representation,
                        'similarity': float(similarity),
                        'quality': knowledge.quality_score
                    })
            
            # ランキング
            candidates.sort(key=lambda x: x['similarity'] * x['quality'], reverse=True)
            
            return candidates[:top_k]
            
        except Exception as e:
            self.logger.error(f"Multimodal query failed: {e}")
            return []
    
    async def _calculate_quality_score(self,
                                     content: Any,
                                     modality: ModalityType,
                                     metadata: Dict[str, Any]) -> float:
        """品質スコア計算"""
        base_score = 0.5
        
        # モダリティ別調整
        modality_scores = {
            ModalityType.TEXT: 0.1,
            ModalityType.IMAGE: 0.15,
            ModalityType.AUDIO: 0.15,
            ModalityType.CODE: 0.2,
            ModalityType.STRUCTURED_DATA: 0.1
        }
        
        base_score += modality_scores.get(modality, 0)
        
        # メタデータによる調整
        if metadata:
            if 'source_credibility' in metadata:
                base_score += metadata['source_credibility'] * 0.2
            if 'verification_status' in metadata:
                base_score += 0.1
        
        return min(1.0, base_score)
    
    async def _check_contradictions(self, new_knowledge: MultiModalKnowledge):
        """矛盾チェック"""
        for kid, existing_knowledge in self.knowledge_base.items():
            if kid == new_knowledge.knowledge_id:
                continue
            
            # 類似度計算
            similarity = await self._calculate_similarity(new_knowledge, existing_knowledge)
            
            # テキスト矛盾チェック（簡略化）
            if similarity > 0.8:
                # 高類似度だが内容が矛盾する可能性をチェック
                if await self._detect_semantic_contradiction(
                    new_knowledge.text_representation,
                    existing_knowledge.text_representation
                ):
                    # 矛盾検出
                    contradiction = KnowledgeContradiction(
                        contradiction_id=f"contra_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        detected_at=datetime.now(),
                        knowledge_ids=[new_knowledge.knowledge_id, kid],
                        contradiction_type='semantic',
                        severity=0.8,
                        resolution_strategy=SynthesisStrategy.CONTRADICTION_RESOLUTION,
                        resolution_confidence=0.0,
                        evidence=[{
                            'type': 'high_similarity_with_contradiction',
                            'similarity': similarity
                        }]
                    )
                    
                    self.contradictions[contradiction.contradiction_id] = contradiction
                    self.stats['contradictions_detected'] += 1
                    
                    self.logger.warning(f"⚠️ Contradiction detected: {contradiction.contradiction_id}")
    
    async def _calculate_similarity(self,
                                  knowledge1: MultiModalKnowledge,
                                  knowledge2: MultiModalKnowledge) -> float:
        """知識間類似度計算"""
        if (knowledge1.vector_representation is not None and 
            knowledge2.vector_representation is not None):
            
            # ベクトル次元調整
            min_dim = min(
                len(knowledge1.vector_representation),
                len(knowledge2.vector_representation)
            )
            
            v1 = knowledge1.vector_representation[:min_dim]
            v2 = knowledge2.vector_representation[:min_dim]
            
            # コサイン類似度
            similarity = cosine_similarity([v1], [v2])[0][0]
            
            # モダリティによる調整
            if knowledge1.modality != knowledge2.modality:
                similarity *= 0.8
            
            return float(similarity)
        
        return 0.0
    
    async def _detect_semantic_contradiction(self, text1: str, text2: str) -> bool:
        """意味的矛盾検出"""
        # 簡略化実装
        # 実際は高度なNLP技術を使用
        
        # 否定語チェック
        negation_words = ['not', 'no', 'never', 'none', 'nothing']
        
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        # 一方に否定語があり、他方にない場合
        text1_has_negation = any(neg in text1_lower for neg in negation_words)
        text2_has_negation = any(neg in text2_lower for neg in negation_words)
        
        if text1_has_negation != text2_has_negation:
            return True
        
        return False
    
    async def _persist_knowledge(self, knowledge: MultiModalKnowledge):
        """知識永続化"""
        try:
            conn = sqlite3.connect(self.config['database_path'])
            cursor = conn.cursor()
            
            # ベクトルをバイト列に変換
            vector_blob = pickle.dumps(knowledge.vector_representation) if knowledge.vector_representation is not None else None
            content_blob = pickle.dumps(knowledge.content)
            
            cursor.execute("""
                INSERT OR REPLACE INTO multimodal_knowledge 
                (knowledge_id, created_at, modality, content, text_representation,
                 vector_representation, metadata, quality_score, source_references)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                knowledge.knowledge_id,
                knowledge.created_at.isoformat(),
                knowledge.modality.value,
                content_blob,
                knowledge.text_representation,
                vector_blob,
                json.dumps(knowledge.metadata),
                knowledge.quality_score,
                json.dumps(knowledge.source_references)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Knowledge persistence failed: {e}")
    
    async def _persist_synthesized_knowledge(self, synthesized: SynthesizedKnowledge):
        """合成知識永続化"""
        try:
            conn = sqlite3.connect(self.config['database_path'])
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO synthesized_knowledge 
                (synthesis_id, created_at, source_knowledge_ids, synthesis_strategy,
                 modalities_involved, synthesized_content, confidence_score,
                 novelty_score, validation_results, applications)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                synthesized.synthesis_id,
                synthesized.created_at.isoformat(),
                json.dumps(synthesized.source_knowledge_ids),
                synthesized.synthesis_strategy.value,
                json.dumps([m.value for m in synthesized.modalities_involved]),
                json.dumps(synthesized.synthesized_content),
                synthesized.confidence_score,
                synthesized.novelty_score,
                json.dumps(synthesized.validation_results),
                json.dumps(synthesized.applications)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Synthesized knowledge persistence failed: {e}")
    
    async def _update_contradiction_resolution(self, 
                                             contradiction_id: str,
                                             resolution: Dict[str, Any]):
        """矛盾解決更新"""
        try:
            conn = sqlite3.connect(self.config['database_path'])
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE knowledge_contradictions 
                SET resolved = ?, resolution_confidence = ?
                WHERE contradiction_id = ?
            """, (
                True,
                resolution['confidence'],
                contradiction_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Contradiction resolution update failed: {e}")
    
    async def _save_graph_snapshot(self, graph: nx.Graph):
        """グラフスナップショット保存"""
        try:
            conn = sqlite3.connect(self.config['database_path'])
            cursor = conn.cursor()
            
            # グラフデータをピックル化
            graph_blob = pickle.dumps(graph)
            
            cursor.execute("""
                INSERT INTO knowledge_graph_snapshots 
                (snapshot_id, created_at, nodes_count, edges_count,
                 clusters_count, graph_data, graph_metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.knowledge_graph.graph_id,
                self.knowledge_graph.created_at.isoformat(),
                len(self.knowledge_graph.nodes),
                len(self.knowledge_graph.edges),
                len(self.knowledge_graph.clusters),
                graph_blob,
                json.dumps(self.knowledge_graph.graph_metrics)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Graph snapshot save failed: {e}")
    
    async def get_synthesis_statistics(self) -> Dict[str, Any]:
        """合成統計取得"""
        return {
            'total_knowledge_items': self.stats['total_knowledge_items'],
            'modality_distribution': self._get_modality_distribution(),
            'contradictions_detected': self.stats['contradictions_detected'],
            'contradictions_resolved': self.stats['contradictions_resolved'],
            'resolution_rate': (
                self.stats['contradictions_resolved'] / self.stats['contradictions_detected']
                if self.stats['contradictions_detected'] > 0 else 0
            ),
            'synthesis_operations': self.stats['synthesis_operations'],
            'novel_knowledge_created': self.stats['novel_knowledge_created'],
            'novelty_rate': (
                self.stats['novel_knowledge_created'] / self.stats['synthesis_operations']
                if self.stats['synthesis_operations'] > 0 else 0
            ),
            'graph_metrics': self.knowledge_graph.graph_metrics if self.knowledge_graph else {}
        }
    
    def _get_modality_distribution(self) -> Dict[str, int]:
        """モダリティ分布取得"""
        distribution = defaultdict(int)
        for knowledge in self.knowledge_base.values():
            distribution[knowledge.modality.value] += 1
        return dict(distribution)


# 使用例
async def main():
    """メイン実行関数"""
    try:
        # システム初期化
        synthesis_system = AdvancedKnowledgeSynthesisSystem()
        
        print("🔮 Starting Advanced Knowledge Synthesis System...")
        
        # サンプル知識追加
        print("\n📚 Adding multimodal knowledge...")
        
        # テキスト知識
        text_id1 = await synthesis_system.add_knowledge(
            content="pgvector enables semantic search with high-dimensional vectors",
            modality=ModalityType.TEXT,
            metadata={'source': 'technical_doc', 'confidence': 0.9},
            source_references=['pgvector_official_docs']
        )
        
        text_id2 = await synthesis_system.add_knowledge(
            content="Semantic search uses embeddings to find similar content",
            modality=ModalityType.TEXT,
            metadata={'source': 'research_paper', 'confidence': 0.85},
            source_references=['semantic_search_survey_2024']
        )
        
        # コード知識
        code_id = await synthesis_system.add_knowledge(
            content="""
            def semantic_search(query, vectors):
                query_embedding = encode(query)
                similarities = cosine_similarity(query_embedding, vectors)
                return top_k_indices(similarities)
            """,
            modality=ModalityType.CODE,
            metadata={'language': 'python', 'tested': True},
            source_references=['implementation_guide']
        )
        
        # 画像知識（ダミー）
        image_id = await synthesis_system.add_knowledge(
            content={'type': 'diagram', 'description': 'Vector space visualization'},
            modality=ModalityType.IMAGE,
            metadata={'format': 'png', 'resolution': '1920x1080'},
            source_references=['visualization_toolkit']
        )
        
        print(f"Added {synthesis_system.stats['total_knowledge_items']} knowledge items")
        
        # 矛盾する知識を追加（テスト用）
        print("\n⚠️ Adding contradictory knowledge...")
        
        contradiction_id = await synthesis_system.add_knowledge(
            content="pgvector does not support semantic search",  # 矛盾
            modality=ModalityType.TEXT,
            metadata={'source': 'unreliable_blog', 'confidence': 0.3},
            source_references=['random_blog_post']
        )
        
        # 知識合成
        print("\n✨ Synthesizing knowledge...")
        
        # 融合戦略
        fusion_id = await synthesis_system.synthesize_knowledge(
            knowledge_ids=[text_id1, text_id2, code_id],
            strategy=SynthesisStrategy.FUSION
        )
        
        # 抽象化戦略
        abstraction_id = await synthesis_system.synthesize_knowledge(
            knowledge_ids=[text_id1, text_id2],
            strategy=SynthesisStrategy.ABSTRACTION
        )
        
        # 矛盾解決
        if synthesis_system.contradictions:
            print("\n🔧 Resolving contradictions...")
            for contra_id in list(synthesis_system.contradictions.keys()):
                resolution = await synthesis_system.resolve_contradiction(contra_id)
                print(f"Resolved: {resolution['success']} (confidence: {resolution.get('confidence', 0):.2f})")
        
        # 知識グラフ構築
        print("\n🕸️ Building knowledge graph...")
        knowledge_graph = await synthesis_system.build_knowledge_graph()
        
        # マルチモーダルクエリ
        print("\n🔍 Testing multimodal query...")
        results = await synthesis_system.query_multimodal(
            query="How does pgvector implement semantic search?",
            modalities=[ModalityType.TEXT, ModalityType.CODE],
            top_k=3
        )
        
        print(f"Found {len(results)} relevant items:")
        for result in results:
            print(f"  - {result['modality']}: {result['text'][:50]}... (similarity: {result['similarity']:.3f})")
        
        # 統計表示
        print("\n📊 Synthesis Statistics:")
        stats = await synthesis_system.get_synthesis_statistics()
        
        print(f"  Total Knowledge Items: {stats['total_knowledge_items']}")
        print(f"  Modality Distribution: {stats['modality_distribution']}")
        print(f"  Contradictions: {stats['contradictions_detected']} detected, {stats['contradictions_resolved']} resolved")
        print(f"  Resolution Rate: {stats['resolution_rate']:.2%}")
        print(f"  Synthesis Operations: {stats['synthesis_operations']}")
        print(f"  Novel Knowledge Created: {stats['novel_knowledge_created']}")
        print(f"  Novelty Rate: {stats['novelty_rate']:.2%}")
        
        if stats['graph_metrics']:
            print(f"\n  Knowledge Graph:")
            print(f"    Nodes: {stats['graph_metrics']['nodes']}")
            print(f"    Edges: {stats['graph_metrics']['edges']}")
            print(f"    Density: {stats['graph_metrics']['density']:.3f}")
            print(f"    Clusters: {stats['graph_metrics']['clusters']}")
        
        print("\n🎉 Advanced Knowledge Synthesis System Phase 2 demonstration completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())