"""
専門特化サーバント基底クラス
ドワーフ工房、RAGウィザーズ、エルフの森の専門基底クラス
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, TypeVar, Generic
from datetime import datetime
from abc import abstractmethod

from .elder_servant import (
    ElderServant, ServantCategory, ServantCapability, 
    TaskResult, TaskStatus
)

# Generic type variables
T_Request = TypeVar('T_Request')
T_Response = TypeVar('T_Response')


class DwarfServant(ElderServant, Generic[T_Request, T_Response]):
    """
    ドワーフ工房専門サーバント基底クラス
    開発・製作・実装系タスクに特化
    """
    
    def __init__(self, servant_id: str, servant_name: str, 
                 specialization: str, capabilities: List[ServantCapability]):
        super().__init__(
            servant_id=servant_id,
            servant_name=servant_name,
            category=ServantCategory.DWARF,
            specialization=specialization,
            capabilities=capabilities
        )
        
        # ドワーフ工房固有の設定
        self.production_quality_threshold = 95.0  # 生産品質基準
        self.crafting_templates = {}  # 製作テンプレート
        self.tools_registry = {}  # 工具レジストリ
        
        self.logger.info(f"Dwarf Servant {servant_name} ready for crafting")
    
    @abstractmethod
    async def craft_artifact(self, specification: T_Request) -> T_Response:
        """
        製作品作成（各ドワーフサーバントで実装）
        
        Args:
            specification: 製作仕様
            
        Returns:
            T_Response: 製作品
        """
        pass
    
    async def validate_crafting_quality(self, artifact: T_Response) -> float:
        """製作品質検証"""
        quality_score = 50.0  # 基本スコア
        
        try:
            # 基本品質チェック
            if artifact is not None:
                quality_score += 30.0
            
            # ドワーフ工房品質基準チェック
            if hasattr(artifact, 'get'):
                # 辞書型の場合
                if artifact.get('success', False):
                    quality_score += 20.0
                
                # 完全性チェック
                if 'result' in artifact or 'data' in artifact:
                    quality_score += 15.0
                
                # エラーなしチェック
                if not artifact.get('error'):
                    quality_score += 15.0
            
            # 生産品質閾値チェック
            if quality_score >= self.production_quality_threshold:
                quality_score = min(100.0, quality_score + 5.0)
            
        except Exception as e:
            self.logger.error(f"Quality validation error: {e}")
            quality_score = 0.0
        
        return quality_score
    
    def register_crafting_tool(self, tool_name: str, tool_config: Dict[str, Any]):
        """工具登録"""
        self.tools_registry[tool_name] = tool_config
        self.logger.debug(f"Registered tool: {tool_name}")
    
    def get_crafting_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """製作テンプレート取得"""
        return self.crafting_templates.get(template_name)


class WizardServant(ElderServant, Generic[T_Request, T_Response]):
    """
    RAGウィザーズ専門サーバント基底クラス
    調査・研究・分析系タスクに特化
    """
    
    def __init__(self, servant_id: str, servant_name: str, 
                 specialization: str, capabilities: List[ServantCapability]):
        super().__init__(
            servant_id=servant_id,
            servant_name=servant_name,
            category=ServantCategory.WIZARD,
            specialization=specialization,
            capabilities=capabilities
        )
        
        # ウィザード固有の設定
        self.research_cache = {}  # 研究キャッシュ
        self.knowledge_sources = []  # 知識源リスト
        self.spell_book = {}  # 魔法書（アルゴリズム集）
        self.wisdom_threshold = 85.0  # 知恵の閾値
        
        self.logger.info(f"Wizard Servant {servant_name} ready for research")
    
    @abstractmethod
    async def cast_research_spell(self, query: T_Request) -> T_Response:
        """
        研究魔法詠唱（各ウィザードサーバントで実装）
        
        Args:
            query: 研究クエリ
            
        Returns:
            T_Response: 研究結果
        """
        pass
    
    async def validate_research_quality(self, research_result: T_Response) -> float:
        """研究品質検証"""
        quality_score = 40.0  # 基本スコア
        
        try:
            if research_result is not None:
                quality_score += 20.0
            
            if hasattr(research_result, 'get'):
                # 信頼性チェック
                confidence = research_result.get('confidence', 0)
                quality_score += confidence * 0.3
                
                # 完全性チェック
                if research_result.get('sources'):
                    quality_score += 15.0
                
                # 新規性チェック
                if research_result.get('novelty_score', 0) > 0.7:
                    quality_score += 10.0
                
                # 知恵の閾値チェック
                if quality_score >= self.wisdom_threshold:
                    quality_score = min(100.0, quality_score + 5.0)
            
        except Exception as e:
            self.logger.error(f"Research quality validation error: {e}")
            quality_score = 0.0
        
        return quality_score
    
    def register_knowledge_source(self, source_name: str, source_config: Dict[str, Any]):
        """知識源登録"""
        self.knowledge_sources.append({
            'name': source_name,
            'config': source_config,
            'registered_at': datetime.now()
        })
        self.logger.debug(f"Registered knowledge source: {source_name}")
    
    def cache_research_result(self, query_hash: str, result: T_Response, ttl_hours: int = 24):
        """研究結果キャッシュ"""
        expiry = datetime.now().timestamp() + (ttl_hours * 3600)
        self.research_cache[query_hash] = {
            'result': result,
            'expiry': expiry,
            'created_at': datetime.now()
        }
    
    def get_cached_research(self, query_hash: str) -> Optional[T_Response]:
        """キャッシュされた研究結果取得"""
        cached = self.research_cache.get(query_hash)
        if cached and cached['expiry'] > datetime.now().timestamp():
            return cached['result']
        elif cached:
            # 期限切れキャッシュを削除
            del self.research_cache[query_hash]
        return None


class ElfServant(ElderServant, Generic[T_Request, T_Response]):
    """
    エルフの森専門サーバント基底クラス
    監視・メンテナンス・最適化系タスクに特化
    """
    
    def __init__(self, servant_id: str, servant_name: str, 
                 specialization: str, capabilities: List[ServantCapability]):
        super().__init__(
            servant_id=servant_id,
            servant_name=servant_name,
            category=ServantCategory.ELF,
            specialization=specialization,
            capabilities=capabilities
        )
        
        # エルフ固有の設定
        self.monitoring_intervals = {}  # 監視間隔設定
        self.healing_protocols = {}  # 癒しプロトコル
        self.forest_wisdom = {}  # 森の知恵
        self.harmony_threshold = 90.0  # 調和の閾値
        
        self.logger.info(f"Elf Servant {servant_name} ready for watching")
    
    @abstractmethod
    async def perform_forest_duty(self, watch_target: T_Request) -> T_Response:
        """
        森の任務実行（各エルフサーバントで実装）
        
        Args:
            watch_target: 監視対象
            
        Returns:
            T_Response: 監視結果
        """
        pass
    
    async def validate_harmony_quality(self, harmony_result: T_Response) -> float:
        """調和品質検証"""
        quality_score = 45.0  # 基本スコア
        
        try:
            if harmony_result is not None:
                quality_score += 25.0
            
            if hasattr(harmony_result, 'get'):
                # 健全性チェック
                health_score = harmony_result.get('health_score', 0)
                quality_score += health_score * 0.2
                
                # 安定性チェック
                stability = harmony_result.get('stability', 0)
                quality_score += stability * 0.15
                
                # 効率性チェック
                efficiency = harmony_result.get('efficiency', 0)
                quality_score += efficiency * 0.1
                
                # 調和の閾値チェック
                if quality_score >= self.harmony_threshold:
                    quality_score = min(100.0, quality_score + 5.0)
            
        except Exception as e:
            self.logger.error(f"Harmony quality validation error: {e}")
            quality_score = 0.0
        
        return quality_score
    
    def register_monitoring_target(self, target_name: str, interval_seconds: int, 
                                  protocol: Dict[str, Any]):
        """監視対象登録"""
        self.monitoring_intervals[target_name] = {
            'interval': interval_seconds,
            'protocol': protocol,
            'last_check': None,
            'registered_at': datetime.now()
        }
        self.logger.debug(f"Registered monitoring target: {target_name}")
    
    def register_healing_protocol(self, condition_name: str, healing_steps: List[str]):
        """癒しプロトコル登録"""
        self.healing_protocols[condition_name] = {
            'steps': healing_steps,
            'success_rate': 0.0,
            'last_used': None,
            'registered_at': datetime.now()
        }
        self.logger.debug(f"Registered healing protocol: {condition_name}")
    
    async def apply_healing(self, condition: str, target: Any) -> Dict[str, Any]:
        """癒し適用"""
        protocol = self.healing_protocols.get(condition)
        if not protocol:
            return {
                'success': False,
                'error': f'No healing protocol for condition: {condition}'
            }
        
        try:
            healing_log = []
            for step in protocol['steps']:
                healing_log.append(f"Applied: {step}")
                # 実際のヒーリング処理はサブクラスで実装
                await asyncio.sleep(0.01)  # 象徴的な処理時間
            
            protocol['last_used'] = datetime.now()
            
            return {
                'success': True,
                'condition': condition,
                'healing_log': healing_log,
                'recovery_time': len(protocol['steps']) * 0.01
            }
            
        except Exception as e:
            self.logger.error(f"Healing application failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# 型エイリアス
ServantRequest = TypeVar('ServantRequest')
ServantResponse = TypeVar('ServantResponse')

# 専門特化サーバント基底クラスのエクスポート
__all__ = [
    'DwarfServant', 'WizardServant', 'ElfServant',
    'ServantRequest', 'ServantResponse'
]