#!/usr/bin/env python3
"""
🏰 Knight Brigade System - 騎士団システム 🏰
ナレッジエルダー防衛騎士団 - ドワーフ工房との完璧な連携

4賢者システム統合:
📚 ナレッジ賢者: 戦術知識の継承と戦略立案
🔍 RAG賢者: 脅威情報の検索と分析
📋 タスク賢者: 作戦優先度と資源配分管理
🚨 インシデント賢者: 緊急事態対応と危機管理

🔨 ドワーフ工房連携:
⚒️ 武具供給: 最高の武器・防具を自動供給
📊 情報共有: リアルタイム戦場情報と最適化機会
🛡️ 共同防衛: 工房防護と生産継続保証
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import time
import threading
import logging
import uuid
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
import random

logger = logging.getLogger(__name__)


class KnightSquad:
    """⚔️ 騎士分隊
    
    特化した戦術能力を持つ騎士の精鋭部隊
    """
    
    def __init__(self, squad_id: str, squad_type: str):
        """KnightSquad 初期化"""
        self.squad_id = squad_id
        self.squad_type = squad_type  # guardian, assault, scout, specialist
        
        # 分隊構成
        self.knights = self._initialize_knights()
        self.equipment = {}
        self.current_mission = None
        
        # 戦闘能力
        self.combat_effectiveness = self._calculate_base_effectiveness()
        self.specialization_bonus = self._get_specialization_bonus()
        
        # 状態管理
        self.status = {
            'deployment_ready': True,
            'morale': 0.9,
            'fatigue_level': 0.1,
            'experience_points': 100
        }
        
        # 連携システム
        self.workshop_connection = None
        self.elder_communication = True
        self.weapon_requests = []
        
        logger.info(f"⚔️ {squad_type.title()} Squad '{squad_id}' formed - Ready for duty!")
    
    def _initialize_knights(self) -> List[Dict[str, Any]]:
        """騎士団員の初期化"""
        base_knights = 4 if self.squad_type != 'specialist' else 2
        
        knights = []
        for i in range(base_knights):
            knight = {
                'knight_id': f"{self.squad_id}_knight_{i+1}",
                'rank': 'knight' if i < 3 else 'sergeant',
                'specialization': self._get_knight_specialization(i),
                'combat_skill': random.uniform(0.7, 0.95),
                'equipment_proficiency': random.uniform(0.8, 0.98),
                'experience': random.randint(50, 200),
                'status': 'ready'
            }
            knights.append(knight)
        
        return knights
    
    def _get_knight_specialization(self, index: int) -> str:
        """騎士の専門分野を決定"""
        specializations = {
            'guardian': ['defense', 'protection', 'barrier', 'recovery'],
            'assault': ['offense', 'elimination', 'breakthrough', 'pursuit'],
            'scout': ['reconnaissance', 'surveillance', 'intelligence', 'stealth'],
            'specialist': ['technical', 'coordination']
        }
        
        spec_list = specializations.get(self.squad_type, ['general'])
        return spec_list[index % len(spec_list)]
    
    def _calculate_base_effectiveness(self) -> float:
        """基本戦闘効果を計算"""
        knight_skills = [knight['combat_skill'] for knight in self.knights]
        avg_skill = statistics.mean(knight_skills)
        
        squad_size_bonus = min(0.1, len(self.knights) * 0.02)
        return min(0.95, avg_skill + squad_size_bonus)
    
    def _get_specialization_bonus(self) -> float:
        """専門化ボーナスを取得"""
        bonuses = {
            'guardian': 0.15,    # 防御力+15%
            'assault': 0.12,     # 攻撃力+12%
            'scout': 0.10,       # 情報収集+10%
            'specialist': 0.20   # 専門技術+20%
        }
        return bonuses.get(self.squad_type, 0.05)
    
    def equip_weapons_from_workshop(self, workshop_weapons: List[Dict[str, Any]]) -> Dict[str, Any]:
        """ドワーフ工房からの武具装備"""
        equipped_weapons = []
        total_effectiveness_boost = 0
        
        for weapon_data in workshop_weapons:
            weapon_id = weapon_data.get('weapon_id', weapon_data.get('tool_id', 'unknown'))
            weapon_type = weapon_data.get('weapon_type', weapon_data.get('tool_type', 'unknown'))
            effectiveness = weapon_data.get('effectiveness', weapon_data.get('detection_accuracy', 0.8))
            
            # 装備適合性チェック
            compatibility = self._check_weapon_compatibility(weapon_type)
            
            if compatibility > 0.6:  # 60%以上の適合性が必要
                equipped_weapon = {
                    'weapon_id': weapon_id,
                    'weapon_type': weapon_type,
                    'effectiveness': effectiveness,
                    'compatibility': compatibility,
                    'equipped_at': datetime.now(),
                    'assigned_knights': self._assign_weapon_to_knights(weapon_type)
                }
                
                equipped_weapons.append(equipped_weapon)
                self.equipment[weapon_id] = equipped_weapon
                
                # 効果ブースト計算
                boost = effectiveness * compatibility * 0.1
                total_effectiveness_boost += boost
        
        # 分隊準備度更新
        self.combat_effectiveness = min(0.98, 
            self.combat_effectiveness + total_effectiveness_boost)
        
        logger.info(f"⚔️ Squad {self.squad_id} equipped {len(equipped_weapons)} weapons from workshop")
        
        return {
            'equipped_weapons': equipped_weapons,
            'squad_readiness': self.combat_effectiveness,
            'effectiveness_boost': total_effectiveness_boost,
            'equipment_synergy': self._calculate_equipment_synergy(),
            'knights_equipped': len(set().union(*[w['assigned_knights'] for w in equipped_weapons]))
        }
    
    def execute_defensive_maneuver(self, threat: Dict[str, Any]) -> Dict[str, Any]:
        """防御戦術実行"""
        threat_type = threat.get('threat_type', 'unknown')
        severity = threat.get('severity', 'medium')
        target_systems = threat.get('target_systems', [])
        
        # 戦術選定
        defensive_tactics = self._select_defensive_tactics(threat_type, severity)
        
        # 騎士配置
        knight_assignments = self._assign_knights_to_defense(target_systems)
        
        # 防御実行
        execution_start = datetime.now()
        
        # 防御効果計算
        base_success_rate = self.combat_effectiveness + self.specialization_bonus
        
        # 脅威に対する相性補正
        threat_compatibility = self._calculate_threat_compatibility(threat_type)
        final_success_rate = min(0.98, base_success_rate * threat_compatibility)
        
        # 武具効果適用
        equipment_bonus = self._apply_equipment_effects('defense', threat_type)
        final_success_rate = min(0.99, final_success_rate + equipment_bonus)
        
        # 結果判定
        maneuver_success = random.random() < final_success_rate
        threat_neutralized = maneuver_success and random.random() < 0.9
        
        execution_time = (datetime.now() - execution_start).total_seconds()
        
        # 経験値獲得
        self._gain_experience('defense', severity, maneuver_success)
        
        result = {
            'maneuver_success': maneuver_success,
            'threat_neutralized': threat_neutralized,
            'response_time': execution_time,
            'tactics_used': defensive_tactics,
            'knights_engaged': len(knight_assignments),
            'effectiveness_rating': final_success_rate,
            'threat_assessment': {
                'original_severity': severity,
                'neutralization_level': 0.9 if threat_neutralized else 0.3
            }
        }
        
        logger.info(f"🛡️ Squad {self.squad_id} defensive maneuver: {'SUCCESS' if maneuver_success else 'PARTIAL'}")
        
        return result
    
    def execute_offensive_strike(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """攻撃戦術実行"""
        target_type = target.get('target_type', 'unknown')
        location = target.get('location', 'unknown')
        weakness = target.get('weakness', None)
        priority = target.get('priority', 'medium')
        
        # 攻撃戦術選定
        strike_tactics = self._select_offensive_tactics(target_type, weakness)
        
        # 攻撃力計算
        base_attack_power = self.combat_effectiveness
        if self.squad_type == 'assault':
            base_attack_power += self.specialization_bonus
        
        # 弱点攻撃ボーナス
        weakness_bonus = 0.2 if weakness and self._can_exploit_weakness(weakness) else 0
        
        # 武具効果適用
        equipment_bonus = self._apply_equipment_effects('offense', target_type)
        
        total_attack_power = min(0.99, base_attack_power + weakness_bonus + equipment_bonus)
        
        # 攻撃実行
        execution_start = datetime.now()
        
        strike_success = random.random() < total_attack_power
        target_eliminated = strike_success and random.random() < 0.85
        
        # 副次的被害計算（最小化目標）
        collateral_damage = max(0, (1 - total_attack_power) * 0.1)
        if self.squad_type == 'specialist':
            collateral_damage *= 0.5  # 専門部隊は精密攻撃
        
        execution_time = (datetime.now() - execution_start).total_seconds()
        
        # 経験値獲得
        self._gain_experience('offense', priority, strike_success)
        
        result = {
            'strike_success': strike_success,
            'target_eliminated': target_eliminated,
            'collateral_damage': collateral_damage,
            'response_time': execution_time,
            'tactics_used': strike_tactics,
            'attack_power': total_attack_power,
            'precision_rating': 1 - collateral_damage,
            'target_analysis': {
                'weakness_exploited': weakness_bonus > 0,
                'elimination_confidence': 0.85 if target_eliminated else 0.3
            }
        }
        
        logger.info(f"⚔️ Squad {self.squad_id} offensive strike: {'SUCCESS' if strike_success else 'MISS'}")
        
        return result
    
    def conduct_reconnaissance(self, area: Dict[str, Any]) -> Dict[str, Any]:
        """偵察任務実行"""
        surveillance_area = area.get('surveillance_area', 'general')
        depth = area.get('depth', 'surface')
        duration = area.get('duration', 300)  # デフォルト5分
        stealth_required = area.get('stealth_required', False)
        
        # 偵察能力計算
        base_reconnaissance = self.combat_effectiveness
        if self.squad_type == 'scout':
            base_reconnaissance += self.specialization_bonus
        
        # ステルス要求への対応
        stealth_penalty = 0.1 if stealth_required and self.squad_type != 'scout' else 0
        
        # 深度による難易度調整
        depth_multiplier = {'surface': 1.0, 'medium': 0.8, 'deep_analysis': 0.6}.get(depth, 0.8)
        
        final_recon_ability = (base_reconnaissance - stealth_penalty) * depth_multiplier
        
        # 情報収集実行
        execution_start = datetime.now()
        
        # 情報収集量計算
        intel_gathered = []
        intel_quality = final_recon_ability
        
        # エリア別情報収集
        if surveillance_area == 'system_performance':
            intel_gathered.extend([
                {'type': 'performance_metrics', 'quality': intel_quality, 'confidence': 0.9},
                {'type': 'bottleneck_analysis', 'quality': intel_quality * 0.8, 'confidence': 0.8},
                {'type': 'resource_utilization', 'quality': intel_quality * 0.9, 'confidence': 0.85}
            ])
        
        if depth == 'deep_analysis':
            intel_gathered.extend([
                {'type': 'threat_prediction', 'quality': intel_quality * 0.7, 'confidence': 0.75},
                {'type': 'vulnerability_assessment', 'quality': intel_quality * 0.6, 'confidence': 0.7}
            ])
        
        # 脅威レベル評価
        threat_indicators = random.randint(0, 5)
        threat_level = 'low'
        if threat_indicators >= 4:
            threat_level = 'critical'
        elif threat_indicators >= 3:
            threat_level = 'high'
        elif threat_indicators >= 2:
            threat_level = 'medium'
        
        # 推奨アクション生成
        recommended_actions = self._generate_recon_recommendations(intel_gathered, threat_level)
        
        execution_time = (datetime.now() - execution_start).total_seconds()
        
        # 経験値獲得
        self._gain_experience('reconnaissance', depth, len(intel_gathered) > 2)
        
        result = {
            'intelligence_gathered': intel_gathered,
            'threat_level_assessment': threat_level,
            'recommended_actions': recommended_actions,
            'mission_duration': execution_time,
            'stealth_maintained': stealth_required,
            'reconnaissance_quality': intel_quality,
            'area_coverage': min(1.0, duration / 300 * final_recon_ability)
        }
        
        logger.info(f"🔍 Squad {self.squad_id} reconnaissance complete: {len(intel_gathered)} intel items")
        
        return result
    
    # プライベートヘルパーメソッド群
    def _check_weapon_compatibility(self, weapon_type: str) -> float:
        """武具適合性チェック"""
        compatibility_matrix = {
            'guardian': {
                'anomaly_detector': 0.9, 'resource_guardian': 0.95, 'memory_optimizer': 0.8,
                'performance_scout': 0.7, 'cpu_balancer': 0.75, 'cache_optimizer': 0.7
            },
            'assault': {
                'cpu_balancer': 0.9, 'performance_scout': 0.85, 'cache_optimizer': 0.8,
                'anomaly_detector': 0.7, 'memory_optimizer': 0.8, 'resource_guardian': 0.6
            },
            'scout': {
                'performance_scout': 0.95, 'anomaly_detector': 0.9, 'resource_guardian': 0.8,
                'memory_optimizer': 0.6, 'cpu_balancer': 0.7, 'cache_optimizer': 0.65
            },
            'specialist': {
                'memory_optimizer': 0.95, 'cpu_balancer': 0.9, 'cache_optimizer': 0.9,
                'anomaly_detector': 0.85, 'performance_scout': 0.8, 'resource_guardian': 0.85
            }
        }
        
        return compatibility_matrix.get(self.squad_type, {}).get(weapon_type, 0.5)
    
    def _assign_weapon_to_knights(self, weapon_type: str) -> List[str]:
        """武具を騎士に割り当て"""
        # 武具タイプに基づいて最適な騎士を選定
        specialized_knights = [
            knight['knight_id'] for knight in self.knights
            if knight['equipment_proficiency'] > 0.85
        ]
        
        # 最大2名まで割り当て
        return specialized_knights[:2] if specialized_knights else [self.knights[0]['knight_id']]
    
    def _calculate_equipment_synergy(self) -> float:
        """装備シナジー効果計算"""
        if len(self.equipment) < 2:
            return 0.0
        
        weapon_types = [eq['weapon_type'] for eq in self.equipment.values()]
        
        # 特定の組み合わせでシナジーボーナス
        synergy_combinations = {
            ('anomaly_detector', 'performance_scout'): 0.15,
            ('memory_optimizer', 'cpu_balancer'): 0.12,
            ('resource_guardian', 'anomaly_detector'): 0.18
        }
        
        max_synergy = 0
        for combo, bonus in synergy_combinations.items():
            if all(wtype in weapon_types for wtype in combo):
                max_synergy = max(max_synergy, bonus)
        
        return max_synergy
    
    def _select_defensive_tactics(self, threat_type: str, severity: str) -> List[str]:
        """防御戦術選定"""
        tactics_database = {
            'performance_degradation': ['resource_allocation', 'load_balancing', 'circuit_breaking'],
            'memory_leak': ['memory_isolation', 'garbage_collection', 'process_restart'],
            'cpu_overload': ['process_throttling', 'priority_adjustment', 'task_distribution'],
            'network_attack': ['traffic_filtering', 'rate_limiting', 'connection_dropping'],
            'storage_exhaustion': ['cleanup_procedures', 'compression', 'archive_migration']
        }
        
        base_tactics = tactics_database.get(threat_type, ['general_defense'])
        
        # 重要度に応じて戦術追加
        if severity in ['high', 'critical']:
            base_tactics.extend(['emergency_protocols', 'escalation_procedures'])
        
        return base_tactics
    
    def _assign_knights_to_defense(self, target_systems: List[str]) -> Dict[str, List[str]]:
        """防御への騎士配置"""
        assignments = {}
        available_knights = [k['knight_id'] for k in self.knights if k['status'] == 'ready']
        
        knights_per_system = max(1, len(available_knights) // max(len(target_systems), 1))
        
        for i, system in enumerate(target_systems):
            start_idx = i * knights_per_system
            end_idx = min((i + 1) * knights_per_system, len(available_knights))
            assignments[system] = available_knights[start_idx:end_idx]
        
        return assignments
    
    def _calculate_threat_compatibility(self, threat_type: str) -> float:
        """脅威相性計算"""
        compatibility_matrix = {
            'guardian': {
                'performance_degradation': 0.95, 'memory_leak': 0.9, 'resource_exhaustion': 0.9,
                'cpu_overload': 0.8, 'network_attack': 0.85
            },
            'assault': {
                'cpu_overload': 0.95, 'network_attack': 0.9, 'performance_degradation': 0.8,
                'memory_leak': 0.7, 'resource_exhaustion': 0.75
            },
            'scout': {
                'network_attack': 0.9, 'performance_degradation': 0.85, 'cpu_overload': 0.8,
                'memory_leak': 0.7, 'resource_exhaustion': 0.75
            },
            'specialist': {
                'memory_leak': 0.95, 'resource_exhaustion': 0.9, 'performance_degradation': 0.9,
                'cpu_overload': 0.85, 'network_attack': 0.8
            }
        }
        
        return compatibility_matrix.get(self.squad_type, {}).get(threat_type, 0.7)
    
    def _apply_equipment_effects(self, action_type: str, target_type: str) -> float:
        """装備効果適用"""
        total_bonus = 0
        
        for weapon_data in self.equipment.values():
            weapon_type = weapon_data['weapon_type']
            effectiveness = weapon_data['effectiveness']
            compatibility = weapon_data['compatibility']
            
            # アクションタイプと武具の相性
            action_bonus = 0
            if action_type == 'defense' and 'guardian' in weapon_type:
                action_bonus = 0.1
            elif action_type == 'offense' and 'balancer' in weapon_type:
                action_bonus = 0.08
            elif action_type == 'reconnaissance' and 'scout' in weapon_type:
                action_bonus = 0.12
            
            weapon_contribution = effectiveness * compatibility * action_bonus
            total_bonus += weapon_contribution
        
        return min(0.2, total_bonus)  # 最大20%ボーナス
    
    def request_weapon_from_workshop(self, weapon_type: str, quantity: int = 1, 
                                    priority: str = 'medium', purpose: str = '') -> Optional[str]:
        """ドワーフ工房に武具をリクエスト"""
        try:
            from libs.weapon_sharing_system import (
                weapon_coordinator, WeaponRequest, WeaponType, RequestPriority
            )
            
            # WeaponTypeに変換
            weapon_type_enum = WeaponType[weapon_type.upper()]
            priority_enum = RequestPriority[priority.upper()]
            
            # リクエスト作成
            request = WeaponRequest(
                request_id=f"req_{self.squad_id}_{uuid.uuid4().hex[:8]}",
                requester_id=self.squad_id,
                weapon_type=weapon_type_enum,
                priority=priority_enum,
                quantity=quantity,
                purpose=purpose or f"Squad {self.squad_id} operations",
                requested_at=datetime.now(),
                required_by=datetime.now() + timedelta(hours=1 if priority == 'high' else 6)
            )
            
            # リクエスト送信
            request_id = weapon_coordinator.submit_request(request)
            self.weapon_requests.append(request_id)
            
            logger.info(f"📤 Squad {self.squad_id} requested {quantity} {weapon_type} from workshop")
            return request_id
            
        except Exception as e:
            logger.error(f"Failed to request weapon: {e}")
            return None
    
    def receive_weapon_delivery(self, weapon_specs: List[Dict[str, Any]]) -> bool:
        """ドワーフ工房から武具を受け取る"""
        try:
            for weapon_spec in weapon_specs:
                weapon_id = weapon_spec['weapon_id']
                weapon_type = weapon_spec['weapon_type']
                specs = weapon_spec['specs']
                
                # 装備に追加
                self.equipment[weapon_id] = {
                    'weapon_id': weapon_id,
                    'weapon_type': weapon_type,
                    'effectiveness': specs.get('effectiveness', 0.8),
                    'durability': specs.get('durability', 100),
                    'compatibility': self._calculate_weapon_compatibility(weapon_type),
                    'equipped_at': datetime.now()
                }
                
                # 騎士に装備を割り当て
                available_knights = [k for k in self.knights if 'primary_weapon' not in k]
                if available_knights:
                    available_knights[0]['primary_weapon'] = weapon_id
                
            logger.info(f"📥 Squad {self.squad_id} received {len(weapon_specs)} weapons")
            return True
            
        except Exception as e:
            logger.error(f"Failed to receive weapons: {e}")
            return False
    
    def _calculate_weapon_compatibility(self, weapon_type: str) -> float:
        """武器との相性を計算"""
        compatibility_matrix = {
            'guardian': {
                'resource_guardian': 0.95, 'emergency_shield': 0.9,
                'anomaly_detector': 0.85, 'memory_optimizer': 0.8
            },
            'assault': {
                'cpu_balancer': 0.95, 'performance_scout': 0.9,
                'cache_optimizer': 0.85, 'tactical_analyzer': 0.8
            },
            'scout': {
                'anomaly_detector': 0.95, 'performance_scout': 0.9,
                'tactical_analyzer': 0.85, 'resource_guardian': 0.8
            },
            'specialist': {
                'memory_optimizer': 0.9, 'cpu_balancer': 0.9,
                'cache_optimizer': 0.85, 'rapid_recovery_kit': 0.95
            }
        }
        
        return compatibility_matrix.get(self.squad_type, {}).get(weapon_type, 0.7)
    
    def _select_offensive_tactics(self, target_type: str, weakness: Optional[str]) -> List[str]:
        """攻撃戦術選定"""
        tactics_database = {
            'system_bottleneck': ['targeted_elimination', 'bypass_maneuver', 'overload_attack'],
            'performance_issue': ['precision_strike', 'optimization_assault', 'efficiency_raid'],
            'resource_waste': ['resource_reclamation', 'wastage_elimination', 'cleanup_strike'],
            'security_vulnerability': ['vulnerability_exploitation', 'security_patch', 'hardening_assault']
        }
        
        base_tactics = tactics_database.get(target_type, ['general_assault'])
        
        # 弱点がある場合は弱点攻撃戦術追加
        if weakness:
            base_tactics.insert(0, f'exploit_{weakness}')
        
        return base_tactics
    
    def _can_exploit_weakness(self, weakness: str) -> bool:
        """弱点攻撃可能性判定"""
        exploitable_weaknesses = {
            'guardian': ['resource_allocation', 'load_distribution'],
            'assault': ['query_optimization', 'cpu_scheduling'],
            'scout': ['caching_strategy', 'network_routing'],
            'specialist': ['memory_management', 'algorithm_optimization']
        }
        
        squad_capabilities = exploitable_weaknesses.get(self.squad_type, [])
        return any(capability in weakness for capability in squad_capabilities)
    
    def _generate_recon_recommendations(self, intel_data: List[Dict[str, Any]], 
                                      threat_level: str) -> List[str]:
        """偵察結果に基づく推奨アクション生成"""
        recommendations = []
        
        # 脅威レベルに基づく基本推奨
        if threat_level == 'critical':
            recommendations.extend([
                'immediate_defensive_deployment',
                'emergency_workshop_communication',
                'escalate_to_tactical_coordinator'
            ])
        elif threat_level == 'high':
            recommendations.extend([
                'enhanced_monitoring',
                'prepare_defensive_positions',
                'request_additional_weapons'
            ])
        elif threat_level == 'medium':
            recommendations.extend([
                'increased_surveillance',
                'optimize_current_defenses'
            ])
        else:
            recommendations.append('maintain_standard_patrol')
        
        # 情報品質に基づく追加推奨
        high_quality_intel = [item for item in intel_data if item['quality'] > 0.8]
        if len(high_quality_intel) >= 3:
            recommendations.append('comprehensive_threat_analysis')
        
        return recommendations
    
    def _gain_experience(self, action_type: str, difficulty: str, success: bool):
        """経験値獲得"""
        base_exp = {'low': 5, 'medium': 10, 'high': 15, 'critical': 20}.get(difficulty, 10)
        success_multiplier = 1.5 if success else 0.8
        
        exp_gained = int(base_exp * success_multiplier)
        
        for knight in self.knights:
            knight['experience'] += exp_gained
            
            # スキル向上チェック
            if knight['experience'] % 100 == 0:
                knight['combat_skill'] = min(0.98, knight['combat_skill'] + 0.02)
                knight['equipment_proficiency'] = min(0.99, knight['equipment_proficiency'] + 0.01)


class BattlefieldScout:
    """🔍 戦場偵察システム
    
    戦場状況の監視・分析・予測システム
    """
    
    def __init__(self):
        """BattlefieldScout 初期化"""
        self.surveillance_zones = [
            'system_performance', 'resource_utilization', 'network_traffic',
            'error_patterns', 'user_behavior', 'external_threats'
        ]
        
        self.threat_database = {
            'performance_patterns': {},
            'attack_signatures': {},
            'anomaly_baselines': {}
        }
        
        self.active_monitoring = True
        self.scan_history = deque(maxlen=1000)
        self.threat_predictions = {}
        
        logger.info("🔍 BattlefieldScout deployed - Surveillance active")
    
    def scan_system_threats(self, system_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """システム脅威スキャン"""
        threats = []
        scan_timestamp = datetime.now()
        
        cpu_usage = system_state.get('cpu_usage', 0)
        memory_usage = system_state.get('memory_usage', 0)
        error_rate = system_state.get('error_rate', 0)
        response_time = system_state.get('response_time', 1.0)
        
        # CPU脅威分析
        if cpu_usage > 80:
            threat_severity = 'critical' if cpu_usage > 95 else 'high'
            threats.append({
                'threat_id': f"cpu_threat_{scan_timestamp.strftime('%H%M%S')}",
                'threat_type': 'cpu_overload',
                'severity': threat_severity,
                'current_value': cpu_usage,
                'threshold_exceeded': 80,
                'estimated_time_to_failure': max(5, (100 - cpu_usage) * 2),
                'recommended_response': 'deploy_cpu_balancer'
            })
        
        # メモリ脅威分析
        if memory_usage > 85:
            threat_severity = 'critical' if memory_usage > 95 else 'high'
            threats.append({
                'threat_id': f"memory_threat_{scan_timestamp.strftime('%H%M%S')}",
                'threat_type': 'memory_exhaustion',
                'severity': threat_severity,
                'current_value': memory_usage,
                'threshold_exceeded': 85,
                'estimated_impact': 'system_degradation',
                'recommended_response': 'deploy_memory_optimizer'
            })
        
        # エラー率脅威分析
        if error_rate > 0.02:  # 2%以上
            threat_severity = 'critical' if error_rate > 0.1 else 'high'
            threats.append({
                'threat_id': f"error_threat_{scan_timestamp.strftime('%H%M%S')}",
                'threat_type': 'error_rate_spike',
                'severity': threat_severity,
                'current_value': error_rate,
                'threshold_exceeded': 0.02,
                'trend_analysis': 'increasing',
                'recommended_response': 'deploy_anomaly_detector'
            })
        
        # レスポンス時間脅威分析
        if response_time > 3.0:
            threat_severity = 'high' if response_time > 5.0 else 'medium'
            threats.append({
                'threat_id': f"latency_threat_{scan_timestamp.strftime('%H%M%S')}",
                'threat_type': 'performance_degradation',
                'severity': threat_severity,
                'current_value': response_time,
                'threshold_exceeded': 3.0,
                'user_impact': 'high',
                'recommended_response': 'deploy_performance_scout'
            })
        
        # スキャン履歴に記録
        self.scan_history.append({
            'timestamp': scan_timestamp,
            'system_state': system_state,
            'threats_detected': len(threats),
            'threat_summary': threats
        })
        
        return threats
    
    def analyze_attack_patterns(self, incident_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """攻撃パターン分析"""
        if not incident_history:
            return {
                'pattern_type': 'no_pattern',
                'attack_frequency': 0,
                'escalation_trend': 'stable',
                'prediction_confidence': 0.5
            }
        
        # 時系列分析
        incident_times = [inc['timestamp'] for inc in incident_history]
        incident_types = [inc['type'] for inc in incident_history]
        incident_severities = [inc['severity'] for inc in incident_history]
        
        # 頻度分析
        time_deltas = []
        for i in range(1, len(incident_times)):
            delta = (incident_times[i] - incident_times[i-1]).total_seconds() / 60  # 分単位
            time_deltas.append(delta)
        
        avg_frequency = statistics.mean(time_deltas) if time_deltas else 0
        
        # パターン分類
        pattern_type = 'random'
        if len(set(incident_types)) == 1:
            pattern_type = 'repeated_single_type'
        elif avg_frequency < 30:  # 30分以内
            pattern_type = 'burst_attack'
        elif len(incident_history) > 5 and avg_frequency < 120:  # 2時間以内
            pattern_type = 'sustained_assault'
        
        # エスカレーション分析
        severity_scores = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        recent_severity = statistics.mean([severity_scores.get(s, 2) for s in incident_severities[-3:]])
        early_severity = statistics.mean([severity_scores.get(s, 2) for s in incident_severities[:3]])
        
        if recent_severity > early_severity + 0.5:
            escalation_trend = 'escalating'
        elif recent_severity < early_severity - 0.5:
            escalation_trend = 'de-escalating'
        else:
            escalation_trend = 'stable'
        
        # 予測信頼度
        confidence_factors = {
            'data_points': min(1.0, len(incident_history) / 10),
            'pattern_consistency': 0.8 if pattern_type != 'random' else 0.3,
            'time_consistency': 0.9 if time_deltas and len(time_deltas) > 1 and statistics.stdev(time_deltas) < avg_frequency else 0.5
        }
        
        prediction_confidence = statistics.mean(confidence_factors.values())
        
        return {
            'pattern_type': pattern_type,
            'attack_frequency': 60 / avg_frequency if avg_frequency > 0 else 0,  # 攻撃/時間
            'escalation_trend': escalation_trend,
            'prediction_confidence': prediction_confidence,
            'next_attack_prediction': {
                'estimated_time': avg_frequency if avg_frequency > 0 else None,
                'estimated_severity': incident_severities[-1] if incident_severities else 'medium',
                'confidence': prediction_confidence
            }
        }
    
    def start_real_time_monitoring(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """リアルタイム監視開始"""
        scan_interval = config.get('scan_interval', 30)
        alert_threshold = config.get('alert_threshold', 0.8)
        auto_response = config.get('auto_response', False)
        
        monitoring_config = {
            'monitoring_active': True,
            'scan_frequency': scan_interval,
            'alert_threshold': alert_threshold,
            'auto_response_enabled': auto_response,
            'surveillance_zones': self.surveillance_zones,
            'alert_channels': ['tactical_coordinator', 'squad_commanders', 'workshop_liaison']
        }
        
        # 監視スレッド開始（簡易実装）
        self.active_monitoring = True
        
        logger.info(f"🔍 Real-time monitoring started - Scan interval: {scan_interval}s")
        
        return monitoring_config


class WeaponryManager:
    """⚔️ 武具管理システム
    
    ドワーフ工房からの武具受領・管理・配備システム
    """
    
    def __init__(self):
        """WeaponryManager 初期化"""
        self.weapon_inventory = {}
        self.deployment_history = []
        self.maintenance_schedule = {}
        self.quality_standards = {
            'minimum_effectiveness': 0.75,
            'reliability_threshold': 0.90,
            'compatibility_requirement': 0.60
        }
        
        # ドワーフ工房連携
        self.workshop_connection = {
            'status': 'active',
            'last_delivery': None,
            'pending_requests': [],
            'quality_feedback': []
        }
        
        logger.info("⚔️ WeaponryManager initialized - Ready to receive workshop deliveries")
    
    def receive_weapons_from_workshop(self, workshop_delivery: Dict[str, Any]) -> Dict[str, Any]:
        """ドワーフ工房からの武具受領"""
        delivery_id = workshop_delivery.get('delivery_id', f"delivery_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        weapons = workshop_delivery.get('weapons', [])
        tools = workshop_delivery.get('tools', [])
        
        received_items = []
        quality_assessments = []
        
        # 武器処理
        for weapon in weapons:
            weapon_id = weapon['weapon_id']
            quality_assessment = self._assess_weapon_quality(weapon)
            
            if quality_assessment['meets_standards']:
                self.weapon_inventory[weapon_id] = {
                    **weapon,
                    'status': 'available',
                    'received_at': datetime.now(),
                    'delivery_id': delivery_id,
                    'quality_score': quality_assessment['overall_score']
                }
                received_items.append(weapon_id)
            
            quality_assessments.append(quality_assessment)
        
        # ツール処理
        for tool in tools:
            tool_id = tool['tool_id']
            quality_assessment = self._assess_tool_quality(tool)
            
            if quality_assessment['meets_standards']:
                self.weapon_inventory[tool_id] = {
                    **tool,
                    'status': 'available',
                    'received_at': datetime.now(),
                    'delivery_id': delivery_id,
                    'quality_score': quality_assessment['overall_score']
                }
                received_items.append(tool_id)
            
            quality_assessments.append(quality_assessment)
        
        # 品質統計
        avg_quality = statistics.mean([qa['overall_score'] for qa in quality_assessments])
        standards_met = sum(1 for qa in quality_assessments if qa['meets_standards'])
        
        # 工房へのフィードバック準備
        quality_feedback = {
            'delivery_id': delivery_id,
            'items_received': len(received_items),
            'items_rejected': len(weapons) + len(tools) - len(received_items),
            'average_quality': avg_quality,
            'quality_improvement_suggestions': self._generate_quality_suggestions(quality_assessments)
        }
        
        self.workshop_connection['quality_feedback'].append(quality_feedback)
        self.workshop_connection['last_delivery'] = datetime.now()
        
        logger.info(f"⚔️ Received {len(received_items)} weapons/tools from workshop (Quality: {avg_quality:.2f})")
        
        return {
            'received_count': len(received_items),
            'inventory_updated': True,
            'quality_assessment': {
                'average_quality': avg_quality,
                'standards_compliance_rate': standards_met / len(quality_assessments),
                'items_meeting_standards': standards_met
            },
            'workshop_feedback': quality_feedback
        }
    
    def deploy_weapon_to_squad(self, deployment_request: Dict[str, Any]) -> Dict[str, Any]:
        """分隊への武具配備"""
        squad_id = deployment_request['squad_id']
        weapon_type = deployment_request['weapon_type']
        mission_type = deployment_request.get('mission_type', 'general')
        duration = deployment_request.get('duration', 3600)
        
        # 適切な武具検索
        suitable_weapons = [
            (weapon_id, weapon_data) for weapon_id, weapon_data in self.weapon_inventory.items()
            if weapon_data.get('weapon_type', weapon_data.get('tool_type')) == weapon_type
            and weapon_data['status'] == 'available'
        ]
        
        if not suitable_weapons:
            return {
                'deployment_success': False,
                'error': f'No available {weapon_type} in inventory',
                'alternative_suggestions': self._suggest_alternative_weapons(weapon_type)
            }
        
        # 最高品質の武具選択
        best_weapon_id, best_weapon = max(suitable_weapons, key=lambda x: x[1]['quality_score'])
        
        # 配備実行
        deployment_record = {
            'deployment_id': f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'weapon_id': best_weapon_id,
            'squad_id': squad_id,
            'mission_type': mission_type,
            'deployed_at': datetime.now(),
            'expected_return': datetime.now() + timedelta(seconds=duration),
            'deployment_status': 'active'
        }
        
        # インベントリ更新
        self.weapon_inventory[best_weapon_id]['status'] = 'deployed'
        self.weapon_inventory[best_weapon_id]['current_deployment'] = deployment_record
        
        # 配備履歴記録
        self.deployment_history.append(deployment_record)
        
        # 効果見積もり
        effectiveness = best_weapon['quality_score']
        mission_compatibility = self._calculate_mission_compatibility(weapon_type, mission_type)
        estimated_effectiveness = effectiveness * mission_compatibility
        
        logger.info(f"⚔️ Deployed {weapon_type} to squad {squad_id} (Effectiveness: {estimated_effectiveness:.2f})")
        
        return {
            'deployment_success': True,
            'weapon_assigned': best_weapon_id,
            'estimated_effectiveness': estimated_effectiveness,
            'deployment_record': deployment_record,
            'mission_compatibility': mission_compatibility
        }
    
    def perform_maintenance_check(self) -> Dict[str, Any]:
        """武具メンテナンスチェック"""
        maintenance_needed = []
        overall_conditions = []
        
        for weapon_id, weapon_data in self.weapon_inventory.items():
            condition = weapon_data.get('condition', 1.0)
            usage_hours = weapon_data.get('usage_hours', 0)
            last_maintenance = weapon_data.get('last_maintenance', datetime.now())
            
            overall_conditions.append(condition)
            
            # メンテナンス必要性判定
            needs_maintenance = (
                condition < 0.8 or 
                usage_hours > 200 or 
                (datetime.now() - last_maintenance).days > 7
            )
            
            if needs_maintenance:
                maintenance_priority = 'high' if condition < 0.6 else 'medium'
                maintenance_needed.append({
                    'weapon_id': weapon_id,
                    'weapon_type': weapon_data.get('weapon_type', weapon_data.get('tool_type')),
                    'condition': condition,
                    'priority': maintenance_priority,
                    'recommended_actions': self._get_maintenance_actions(weapon_data)
                })
        
        avg_condition = statistics.mean(overall_conditions) if overall_conditions else 1.0
        
        # メンテナンス推奨事項
        recommendations = []
        if len(maintenance_needed) > len(self.weapon_inventory) * 0.3:
            recommendations.append('schedule_bulk_maintenance')
        if avg_condition < 0.7:
            recommendations.append('increase_maintenance_frequency')
        if any(item['priority'] == 'high' for item in maintenance_needed):
            recommendations.append('immediate_high_priority_maintenance')
        
        return {
            'weapons_needing_maintenance': maintenance_needed,
            'overall_fleet_condition': avg_condition,
            'maintenance_recommendations': recommendations,
            'total_weapons_in_inventory': len(self.weapon_inventory),
            'maintenance_rate': len(maintenance_needed) / max(len(self.weapon_inventory), 1)
        }
    
    # プライベートヘルパーメソッド群
    def _assess_weapon_quality(self, weapon: Dict[str, Any]) -> Dict[str, Any]:
        """武器品質評価"""
        detection_accuracy = weapon.get('detection_accuracy', 0.8)
        response_time = weapon.get('response_time', 5.0)
        false_positive_rate = weapon.get('false_positive_rate', 0.05)
        
        # 品質スコア計算
        accuracy_score = detection_accuracy
        speed_score = max(0, 1 - (response_time / 10))  # 10秒基準
        reliability_score = 1 - false_positive_rate
        
        overall_score = (accuracy_score * 0.4 + speed_score * 0.3 + reliability_score * 0.3)
        
        meets_standards = (
            detection_accuracy >= self.quality_standards['minimum_effectiveness']
        )
        
        return {
            'overall_score': overall_score,
            'meets_standards': meets_standards,
            'component_scores': {
                'accuracy': accuracy_score,
                'speed': speed_score,
                'reliability': reliability_score
            }
        }
    
    def _assess_tool_quality(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """ツール品質評価"""
        effectiveness = tool.get('effectiveness', 0.8)
        target_improvement = tool.get('target_improvement', 10.0)
        deployment_ready = tool.get('deployment_ready', True)
        
        # 品質スコア計算
        effectiveness_score = effectiveness
        improvement_score = min(1.0, target_improvement / 20.0)  # 20%改善を最高とする
        readiness_score = 1.0 if deployment_ready else 0.5
        
        overall_score = (effectiveness_score * 0.5 + improvement_score * 0.3 + readiness_score * 0.2)
        
        meets_standards = (
            effectiveness >= self.quality_standards['minimum_effectiveness']
        )
        
        return {
            'overall_score': overall_score,
            'meets_standards': meets_standards,
            'component_scores': {
                'effectiveness': effectiveness_score,
                'improvement_potential': improvement_score,
                'readiness': readiness_score
            }
        }
    
    def _generate_quality_suggestions(self, assessments: List[Dict[str, Any]]) -> List[str]:
        """品質改善提案生成"""
        suggestions = []
        
        avg_scores = {
            'accuracy': statistics.mean([a.get('component_scores', {}).get('accuracy', 0.8) for a in assessments]),
            'speed': statistics.mean([a.get('component_scores', {}).get('speed', 0.8) for a in assessments]),
            'reliability': statistics.mean([a.get('component_scores', {}).get('reliability', 0.8) for a in assessments])
        }
        
        if avg_scores['accuracy'] < 0.8:
            suggestions.append('improve_detection_algorithms')
        if avg_scores['speed'] < 0.7:
            suggestions.append('optimize_response_time')
        if avg_scores['reliability'] < 0.85:
            suggestions.append('reduce_false_positive_rate')
        
        return suggestions
    
    def _suggest_alternative_weapons(self, requested_type: str) -> List[str]:
        """代替武具提案"""
        alternatives = {
            'anomaly_detector': ['performance_scout', 'resource_guardian'],
            'memory_optimizer': ['cpu_balancer', 'cache_optimizer'],
            'performance_scout': ['anomaly_detector', 'resource_guardian']
        }
        
        return alternatives.get(requested_type, [])
    
    def _calculate_mission_compatibility(self, weapon_type: str, mission_type: str) -> float:
        """任務適合性計算"""
        compatibility_matrix = {
            ('anomaly_detector', 'surveillance'): 0.95,
            ('anomaly_detector', 'defense'): 0.85,
            ('performance_scout', 'reconnaissance'): 0.95,
            ('memory_optimizer', 'optimization'): 0.90,
            ('cpu_balancer', 'performance_tuning'): 0.95
        }
        
        return compatibility_matrix.get((weapon_type, mission_type), 0.75)
    
    def _get_maintenance_actions(self, weapon_data: Dict[str, Any]) -> List[str]:
        """メンテナンスアクション推奨"""
        actions = []
        condition = weapon_data.get('condition', 1.0)
        
        if condition < 0.6:
            actions.extend(['complete_overhaul', 'component_replacement'])
        elif condition < 0.8:
            actions.extend(['calibration_adjustment', 'performance_tuning'])
        
        usage_hours = weapon_data.get('usage_hours', 0)
        if usage_hours > 300:
            actions.append('heavy_usage_inspection')
        
        return actions


class TacticalCoordinator:
    """🎯 戦術調整システム
    
    複数分隊の協調作戦計画・実行・調整システム
    """
    
    def __init__(self):
        """TacticalCoordinator 初期化"""
        self.active_operations = {}
        self.strategy_database = {
            'defensive_strategies': {},
            'offensive_strategies': {},
            'coordination_patterns': {}
        }
        self.coordination_active = True
        self.operation_history = deque(maxlen=100)
        
        logger.info("🎯 TacticalCoordinator deployed - Strategic command ready")
    
    def plan_coordinated_response(self, threat_scenario: Dict[str, Any]) -> Dict[str, Any]:
        """協調対応計画立案"""
        threat_type = threat_scenario['threat_type']
        affected_systems = threat_scenario['affected_systems']
        severity = threat_scenario['severity']
        required_response_time = threat_scenario.get('required_response_time', 300)
        
        operation_id = f"op_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 分隊配置計画
        squad_assignments = self._plan_squad_assignments(threat_type, affected_systems, severity)
        
        # 実行タイムライン作成
        timeline = self._create_execution_timeline(squad_assignments, required_response_time)
        
        # 成功確率計算
        success_probability = self._calculate_operation_success_probability(
            squad_assignments, threat_type, severity
        )
        
        # リソース要求計算
        resource_requirements = self._calculate_resource_requirements(squad_assignments)
        
        response_plan = {
            'operation_id': operation_id,
            'threat_assessment': threat_scenario,
            'squad_assignments': squad_assignments,
            'execution_timeline': timeline,
            'success_probability': success_probability,
            'resource_requirements': resource_requirements,
            'coordination_requirements': {
                'communication_frequency': 30,  # 30秒間隔
                'synchronization_points': len(squad_assignments),
                'fallback_strategies': self._generate_fallback_strategies(threat_type)
            },
            'created_at': datetime.now()
        }
        
        self.active_operations[operation_id] = response_plan
        
        logger.info(f"🎯 Coordinated response planned: {operation_id} (Success rate: {success_probability:.2f})")
        
        return response_plan
    
    def coordinate_multi_squad_operation(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """複数分隊協調作戦実行"""
        operation_id = operation['operation_id']
        squads = operation['squads']
        objectives = operation['objectives']
        coordination_req = operation.get('coordination_requirements', {})
        
        # 作戦開始
        operation_start = datetime.now()
        
        # 分隊間通信確立
        communication_status = self._establish_squad_communication(squads)
        
        # 目標割り当て
        objective_assignments = self._assign_objectives_to_squads(squads, objectives)
        
        # 同期実行
        execution_results = {}
        for squad_id, assigned_objectives in objective_assignments.items():
            squad_result = self._execute_squad_objectives(squad_id, assigned_objectives)
            execution_results[squad_id] = squad_result
        
        # 結果集約
        objectives_achieved = []
        squad_performance = {}
        
        for squad_id, result in execution_results.items():
            squad_performance[squad_id] = {
                'objectives_completed': result['completed_objectives'],
                'success_rate': result['success_rate'],
                'response_time': result['execution_time']
            }
            objectives_achieved.extend(result['completed_objectives'])
        
        # 協調効果計算
        coordination_effectiveness = self._calculate_coordination_effectiveness(
            execution_results, coordination_req
        )
        
        operation_duration = (datetime.now() - operation_start).total_seconds()
        
        # 作戦記録
        operation_record = {
            'operation_id': operation_id,
            'duration': operation_duration,
            'objectives_achieved': objectives_achieved,
            'squad_performance': squad_performance,
            'coordination_effectiveness': coordination_effectiveness
        }
        
        self.operation_history.append(operation_record)
        
        if operation_id in self.active_operations:
            del self.active_operations[operation_id]
        
        logger.info(f"🎯 Multi-squad operation completed: {len(objectives_achieved)}/{len(objectives)} objectives")
        
        coordination_success = len(objectives_achieved) >= len(objectives) * 0.6  # 60%で成功とする
        
        return {
            'coordination_success': coordination_success,
            'objectives_achieved': objectives_achieved,
            'squad_performance': squad_performance,
            'operation_duration': operation_duration,
            'coordination_effectiveness': coordination_effectiveness
        }
    
    def execute_emergency_protocol(self, emergency: Dict[str, Any]) -> Dict[str, Any]:
        """緊急対応プロトコル実行"""
        alert_level = emergency['alert_level']
        threat_type = emergency['threat_type']
        time_to_critical = emergency.get('time_to_critical', 300)
        
        protocol_start = datetime.now()
        
        # 緊急プロトコル選定
        protocol_type = self._select_emergency_protocol(alert_level, threat_type, time_to_critical)
        
        # 分隊緊急動員
        mobilized_squads = self._emergency_squad_mobilization(alert_level, threat_type)
        
        # 緊急対応実行
        response_actions = []
        containment_success = True
        
        for squad_id in mobilized_squads:
            emergency_action = self._execute_emergency_action(squad_id, threat_type, time_to_critical)
            response_actions.append(emergency_action)
            
            if not emergency_action['success']:
                containment_success = False
        
        response_time = (datetime.now() - protocol_start).total_seconds()
        
        # 緊急プロトコル記録
        protocol_record = {
            'emergency_id': f"emg_{protocol_start.strftime('%Y%m%d_%H%M%S')}",
            'alert_level': alert_level,
            'threat_type': threat_type,
            'protocol_type': protocol_type,
            'response_time': response_time,
            'squads_mobilized': len(mobilized_squads),
            'containment_success': containment_success
        }
        
        logger.info(f"🚨 Emergency protocol executed: {protocol_type} ({response_time:.1f}s)")
        
        return {
            'protocol_activated': True,
            'response_time': response_time,
            'squads_mobilized': len(mobilized_squads),
            'containment_success': containment_success,
            'emergency_actions': response_actions,
            'protocol_record': protocol_record
        }
    
    # プライベートヘルパーメソッド群
    def _plan_squad_assignments(self, threat_type: str, affected_systems: List[str], 
                              severity: str) -> Dict[str, Dict[str, Any]]:
        """分隊配置計画"""
        assignments = {}
        
        # 基本分隊配置
        if severity in ['high', 'critical']:
            # 高重要度脅威 - 複数分隊配置
            assignments['guardian_alpha'] = {
                'role': 'primary_defense',
                'target_systems': affected_systems[:2],
                'priority': 'critical'
            }
            assignments['assault_bravo'] = {
                'role': 'threat_elimination', 
                'target_systems': affected_systems[1:],
                'priority': 'high'
            }
            assignments['scout_charlie'] = {
                'role': 'perimeter_surveillance',
                'target_systems': affected_systems,
                'priority': 'medium'
            }
        else:
            # 中低重要度脅威 - 単一分隊または部分配置
            assignments['guardian_alpha'] = {
                'role': 'primary_response',
                'target_systems': affected_systems,
                'priority': 'medium'
            }
        
        return assignments
    
    def _create_execution_timeline(self, squad_assignments: Dict[str, Dict[str, Any]], 
                                 response_time: int) -> List[Dict[str, Any]]:
        """実行タイムライン作成"""
        timeline = []
        current_time = datetime.now()
        
        # フェーズ1: 初期配置（最初の30秒）
        timeline.append({
            'phase': 'initial_deployment',
            'start_time': current_time,
            'duration': 30,
            'squads_involved': list(squad_assignments.keys()),
            'actions': ['position_deployment', 'communication_establishment']
        })
        
        # フェーズ2: 主要対応（30秒〜80%の時間）
        main_duration = int(response_time * 0.6)
        timeline.append({
            'phase': 'primary_response',
            'start_time': current_time + timedelta(seconds=30),
            'duration': main_duration,
            'squads_involved': [squad for squad, data in squad_assignments.items() 
                              if data['priority'] in ['critical', 'high']],
            'actions': ['threat_engagement', 'defense_execution', 'target_elimination']
        })
        
        # フェーズ3: 確認・安定化（残り時間）
        cleanup_duration = response_time - 30 - main_duration
        timeline.append({
            'phase': 'consolidation',
            'start_time': current_time + timedelta(seconds=30 + main_duration),
            'duration': cleanup_duration,
            'squads_involved': list(squad_assignments.keys()),
            'actions': ['threat_verification', 'system_stabilization', 'status_reporting']
        })
        
        return timeline
    
    def _calculate_operation_success_probability(self, squad_assignments: Dict[str, Dict[str, Any]], 
                                               threat_type: str, severity: str) -> float:
        """作戦成功確率計算"""
        base_probability = 0.7
        
        # 分隊数による信頼性向上
        squad_count_bonus = min(0.2, len(squad_assignments) * 0.05)
        
        # 脅威タイプによる補正
        threat_difficulty = {
            'performance_degradation': 0.85,
            'memory_leak': 0.8,
            'cpu_overload': 0.9,
            'network_attack': 0.75,
            'distributed_attack': 0.6
        }.get(threat_type, 0.8)
        
        # 重要度による補正
        severity_modifier = {
            'low': 1.1,
            'medium': 1.0,
            'high': 0.9,
            'critical': 0.8
        }.get(severity, 1.0)
        
        final_probability = (base_probability + squad_count_bonus) * threat_difficulty * severity_modifier
        
        return max(0.7, min(0.95, final_probability))
    
    def _calculate_resource_requirements(self, squad_assignments: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """リソース要求計算"""
        return {
            'total_squads_required': len(squad_assignments),
            'estimated_weapon_consumption': len(squad_assignments) * 2,
            'communication_bandwidth': 'high' if len(squad_assignments) > 2 else 'medium',
            'coordination_overhead': len(squad_assignments) * 0.1
        }
    
    def _generate_fallback_strategies(self, threat_type: str) -> List[str]:
        """代替戦略生成"""
        strategies = {
            'performance_degradation': ['graceful_degradation', 'service_isolation', 'backup_activation'],
            'memory_leak': ['process_restart', 'memory_dump', 'service_migration'],
            'cpu_overload': ['load_shedding', 'throttling', 'horizontal_scaling'],
            'network_attack': ['traffic_blocking', 'failover_routing', 'isolation_mode']
        }
        
        return strategies.get(threat_type, ['general_fallback', 'manual_intervention'])
    
    def _establish_squad_communication(self, squads: List[str]) -> Dict[str, bool]:
        """分隊間通信確立"""
        communication_status = {}
        
        for squad in squads:
            # 簡易通信確立チェック
            comm_success = random.random() > 0.05  # 95%成功率
            communication_status[squad] = comm_success
        
        return communication_status
    
    def _assign_objectives_to_squads(self, squads: List[str], 
                                   objectives: List[str]) -> Dict[str, List[str]]:
        """目標の分隊割り当て"""
        assignments = {}
        objectives_per_squad = max(1, len(objectives) // len(squads))
        
        for i, squad in enumerate(squads):
            start_idx = i * objectives_per_squad
            end_idx = min((i + 1) * objectives_per_squad, len(objectives))
            assignments[squad] = objectives[start_idx:end_idx]
        
        # 残り目標を最初の分隊に追加
        if len(objectives) % len(squads) != 0:
            remaining_objectives = objectives[len(squads) * objectives_per_squad:]
            assignments[squads[0]].extend(remaining_objectives)
        
        return assignments
    
    def _execute_squad_objectives(self, squad_id: str, objectives: List[str]) -> Dict[str, Any]:
        """分隊目標実行"""
        execution_start = datetime.now()
        completed_objectives = []
        
        for objective in objectives:
            # 簡易目標実行シミュレーション
            success_rate = 0.85  # 基本成功率
            
            if random.random() < success_rate:
                completed_objectives.append(objective)
        
        execution_time = (datetime.now() - execution_start).total_seconds()
        
        return {
            'completed_objectives': completed_objectives,
            'success_rate': len(completed_objectives) / len(objectives) if objectives else 1.0,
            'execution_time': execution_time
        }
    
    def _calculate_coordination_effectiveness(self, execution_results: Dict[str, Dict[str, Any]], 
                                            coordination_req: Dict[str, Any]) -> float:
        """協調効果計算"""
        individual_success_rates = [result['success_rate'] for result in execution_results.values()]
        avg_individual_success = statistics.mean(individual_success_rates)
        
        # 協調ボーナス計算
        if len(execution_results) > 1:
            coordination_bonus = 0.1 * (len(execution_results) - 1)
        else:
            coordination_bonus = 0
        
        # タイミング精度ボーナス
        timing_precision = coordination_req.get('timing_precision', 'medium')
        timing_bonus = {'high': 0.05, 'medium': 0.02, 'low': 0}.get(timing_precision, 0)
        
        total_effectiveness = min(0.98, avg_individual_success + coordination_bonus + timing_bonus)
        
        return total_effectiveness
    
    def _select_emergency_protocol(self, alert_level: str, threat_type: str, time_to_critical: int) -> str:
        """緊急プロトコル選定"""
        if alert_level == 'red' and time_to_critical < 60:
            return 'immediate_containment'
        elif alert_level == 'red':
            return 'rapid_response'
        elif threat_type == 'system_cascade_failure':
            return 'cascade_prevention'
        else:
            return 'standard_emergency'
    
    def _emergency_squad_mobilization(self, alert_level: str, threat_type: str) -> List[str]:
        """緊急分隊動員"""
        available_squads = ['guardian_alpha', 'assault_bravo', 'scout_charlie', 'specialist_delta']
        
        if alert_level == 'red':
            return available_squads  # 全分隊動員
        elif threat_type in ['system_cascade_failure', 'critical_infrastructure_threat']:
            return available_squads[:3]  # 主要3分隊
        else:
            return available_squads[:2]  # 基本2分隊
    
    def _execute_emergency_action(self, squad_id: str, threat_type: str, time_limit: int) -> Dict[str, Any]:
        """緊急アクション実行"""
        action_start = datetime.now()
        
        # 緊急対応成功率（時間制限による補正）
        base_success_rate = 0.9
        time_pressure_penalty = max(0, (300 - time_limit) / 300 * 0.2)  # 5分未満で最大20%ペナルティ
        
        final_success_rate = base_success_rate - time_pressure_penalty
        action_success = random.random() < final_success_rate
        
        action_time = (datetime.now() - action_start).total_seconds()
        
        return {
            'squad_id': squad_id,
            'action_type': f'emergency_{threat_type}_response',
            'success': action_success,
            'response_time': action_time,
            'effectiveness': final_success_rate if action_success else 0.3
        }


class KnightBrigade:
    """🏰 騎士団システム メインクラス
    
    ナレッジエルダー防衛騎士団 - ドワーフ工房との完璧な連携
    """
    
    def __init__(self):
        """KnightBrigade 初期化"""
        # 指揮システム初期化
        self.brigade_id = f"knight_brigade_{uuid.uuid4().hex[:8]}"
        self.brigade_name = "Knowledge Elder Defense Brigade"
        
        # サブシステム初期化
        self.battlefield_scout = BattlefieldScout()
        self.weaponry_manager = WeaponryManager()
        self.tactical_coordinator = TacticalCoordinator()
        
        # 分隊編成
        self.squads = {
            'guardian_alpha': KnightSquad('guardian_alpha', 'guardian'),
            'assault_bravo': KnightSquad('assault_bravo', 'assault'),
            'scout_charlie': KnightSquad('scout_charlie', 'scout'),
            'specialist_delta': KnightSquad('specialist_delta', 'specialist')
        }
        
        # ドワーフ工房連携
        self.workshop_integration = {
            'connection_status': 'pending',
            'communication_channel': None,
            'last_coordination': None,
            'shared_objectives': []
        }
        
        # 4賢者統合
        self.elder_coordination = {
            'knowledge_sage': True,
            'rag_sage': True,
            'task_sage': True,
            'incident_sage': True
        }
        
        # 運用状態
        self.operational_status = 'active'
        self.readiness_level = 'ready'
        self.current_threat_level = 'green'
        
        logger.info(f"🏰 Knight Brigade '{self.brigade_name}' assembled: {self.brigade_id}")
        logger.info(f"⚔️ {len(self.squads)} squads ready for deployment")
    
    def integrate_with_dwarf_workshop(self, workshop_connection: Dict[str, Any]) -> Dict[str, Any]:
        """ドワーフ工房との統合"""
        workshop_id = workshop_connection['workshop_id']
        communication_channel = workshop_connection['communication_channel']
        delivery_frequency = workshop_connection.get('delivery_frequency', 300)
        quality_requirements = workshop_connection.get('quality_requirements', {})
        
        # 工房との通信確立
        connection_test = self._test_workshop_communication(workshop_id, communication_channel)
        
        if connection_test['success']:
            self.workshop_integration = {
                'connection_status': 'connected',
                'workshop_id': workshop_id,
                'communication_channel': communication_channel,
                'delivery_frequency': delivery_frequency,
                'quality_requirements': quality_requirements,
                'established_at': datetime.now(),
                'connection_quality': connection_test['quality_score']
            }
            
            # 武具マネージャーとの連携設定
            workshop_config = {
                'workshop_id': workshop_id,
                'delivery_schedule': delivery_frequency,
                'quality_standards': quality_requirements
            }
            
            self.weaponry_manager.workshop_connection.update(workshop_config)
            
            # 初期情報交換
            initial_exchange = self._perform_initial_workshop_exchange()
            
            logger.info(f"🔗 Workshop integration successful: {workshop_id}")
            
            return {
                'integration_successful': True,
                'communication_established': True,
                'connection_quality': connection_test['quality_score'],
                'delivery_schedule': {
                    'frequency_minutes': delivery_frequency,
                    'next_delivery': datetime.now() + timedelta(seconds=delivery_frequency)
                },
                'initial_exchange': initial_exchange
            }
        else:
            logger.error(f"❌ Workshop integration failed: {connection_test['error']}")
            return {
                'integration_successful': False,
                'communication_established': False,
                'error': connection_test['error']
            }
    
    def receive_workshop_intelligence(self, workshop_intel: Dict[str, Any]) -> Dict[str, Any]:
        """工房からの情報受信・処理"""
        optimization_opportunities = workshop_intel.get('optimization_opportunities', [])
        threat_analysis = workshop_intel.get('threat_analysis', {})
        resource_status = workshop_intel.get('resource_status', {})
        
        # 情報処理・分析
        processed_intel = {
            'high_priority_opportunities': [
                opp for opp in optimization_opportunities 
                if opp.get('priority') == 'high'
            ],
            'new_threats': threat_analysis.get('new_vulnerabilities', []),
            'workshop_capacity': resource_status.get('production_capacity', 'unknown')
        }
        
        # 戦術調整
        tactical_adjustments = []
        
        # 高優先度機会への対応
        if processed_intel['high_priority_opportunities']:
            tactical_adjustments.append({
                'type': 'opportunity_exploitation',
                'target': 'system_optimization',
                'recommended_squads': ['specialist_delta', 'guardian_alpha']
            })
        
        # 新脅威への対応
        if processed_intel['new_threats']:
            tactical_adjustments.append({
                'type': 'threat_preparation',
                'target': 'vulnerability_mitigation',
                'recommended_squads': ['scout_charlie', 'assault_bravo']
            })
        
        # 武具要求生成
        weapon_requests = self._generate_weapon_requests(processed_intel)
        
        # 分隊への情報配布
        squad_briefings = self._distribute_intel_to_squads(processed_intel)
        
        logger.info(f"📡 Workshop intelligence processed: {len(tactical_adjustments)} adjustments")
        
        return {
            'intelligence_processed': True,
            'tactical_adjustments': tactical_adjustments,
            'weapon_requests': weapon_requests,
            'squad_briefings': squad_briefings,
            'next_coordination_time': datetime.now() + timedelta(minutes=30)
        }
    
    def execute_coordinated_defense(self, threat_scenario: Dict[str, Any]) -> Dict[str, Any]:
        """協調防御実行"""
        attack_type = threat_scenario['attack_type']
        attack_vectors = threat_scenario['attack_vectors']
        intensity = threat_scenario['intensity']
        priority_targets = threat_scenario.get('priority_targets', [])
        
        defense_start = datetime.now()
        
        # 脅威レベル評価
        threat_level = self._assess_threat_level(attack_type, attack_vectors, intensity)
        self.current_threat_level = threat_level
        
        # 戦術計画立案
        defense_plan = self.tactical_coordinator.plan_coordinated_response({
            'threat_type': attack_type,
            'affected_systems': priority_targets,
            'severity': intensity,
            'estimated_duration': 900,
            'required_response_time': 180  # 3分以内
        })
        
        # 分隊配備
        engaged_squads = []
        squad_results = {}
        
        for squad_id, assignment in defense_plan['squad_assignments'].items():
            if squad_id in self.squads:
                squad = self.squads[squad_id]
                
                # 工房武具で装備強化
                workshop_weapons = self._request_immediate_weapons(squad_id, attack_vectors)
                if workshop_weapons:
                    squad.equip_weapons_from_workshop(workshop_weapons)
                
                # 防御実行
                if assignment['role'] == 'primary_defense':
                    defense_result = squad.execute_defensive_maneuver({
                        'threat_type': attack_type,
                        'severity': intensity,
                        'target_systems': assignment['target_systems']
                    })
                elif assignment['role'] == 'threat_elimination':
                    defense_result = squad.execute_offensive_strike({
                        'target_type': 'attack_source',
                        'location': 'attack_vectors',
                        'priority': intensity
                    })
                else:
                    defense_result = squad.conduct_reconnaissance({
                        'surveillance_area': 'attack_perimeter',
                        'depth': 'deep_analysis',
                        'stealth_required': True
                    })
                
                engaged_squads.append(squad_id)
                squad_results[squad_id] = defense_result
        
        # 脅威中和評価
        threats_neutralized = []
        workshop_support_used = False
        
        for vector in attack_vectors:
            # 各攻撃ベクターの中和判定
            vector_neutralized = any(
                result.get('threat_neutralized', False) or result.get('target_eliminated', False)
                for result in squad_results.values()
            )
            
            if vector_neutralized:
                threats_neutralized.append(vector)
        
        # 工房サポート使用判定
        workshop_support_used = any(
            'workshop' in str(result).lower() 
            for result in squad_results.values()
        )
        
        defense_duration = (datetime.now() - defense_start).total_seconds()
        
        # 防御成功判定
        defense_success = len(threats_neutralized) >= len(attack_vectors) * 0.8
        
        logger.info(f"🛡️ Coordinated defense complete: {'SUCCESS' if defense_success else 'PARTIAL'}")
        
        return {
            'defense_success': defense_success,
            'threats_neutralized': threats_neutralized,
            'squads_engaged': len(engaged_squads),
            'workshop_support_used': workshop_support_used,
            'defense_duration': defense_duration,
            'threat_level_change': {
                'before': 'yellow',
                'after': 'green' if defense_success else 'yellow'
            },
            'squad_performance': squad_results
        }
    
    def request_emergency_weapons(self, emergency_request: Dict[str, Any]) -> Dict[str, Any]:
        """緊急武具要求"""
        urgency_level = emergency_request['urgency_level']
        required_weapons = emergency_request['required_weapons']
        deadline = emergency_request['deadline']
        justification = emergency_request['justification']
        
        request_id = f"emg_req_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 工房への緊急要求送信
        workshop_request = {
            'request_id': request_id,
            'request_type': 'emergency',
            'urgency_level': urgency_level,
            'deadline': deadline,
            'justification': justification,
            'requested_items': required_weapons,
            'requesting_brigade': self.brigade_id
        }
        
        # 工房応答シミュレーション
        workshop_response = self._simulate_workshop_emergency_response(workshop_request)
        
        # 配送時間見積もり
        time_to_deadline = (deadline - datetime.now()).total_seconds() / 60  # 分
        estimated_delivery = min(time_to_deadline * 0.8, 10)  # 最大10分
        
        # 要求記録
        request_record = {
            'request_id': request_id,
            'submitted_at': datetime.now(),
            'urgency': urgency_level,
            'items_requested': len(required_weapons),
            'deadline': deadline,
            'workshop_response': workshop_response
        }
        
        self.weaponry_manager.workshop_connection['pending_requests'].append(request_record)
        
        logger.info(f"🚨 Emergency weapon request submitted: {request_id}")
        
        return {
            'request_submitted': True,
            'request_id': request_id,
            'estimated_delivery_time': estimated_delivery,
            'workshop_response': workshop_response,
            'tracking_info': {
                'status': 'processing',
                'priority_level': urgency_level,
                'queue_position': 1 if urgency_level == 'critical' else 3
            }
        }
    
    def get_brigade_status(self) -> Dict[str, Any]:
        """騎士団状況報告"""
        # 分隊状況集約
        squad_status = {}
        total_readiness = 0
        
        for squad_id, squad in self.squads.items():
            squad_readiness = squad.combat_effectiveness
            total_readiness += squad_readiness
            
            squad_status[squad_id] = {
                'squad_type': squad.squad_type,
                'readiness': squad_readiness,
                'current_mission': squad.current_mission,
                'knight_count': len(squad.knights),
                'equipment_count': len(squad.equipment),
                'morale': squad.status['morale'],
                'experience_level': statistics.mean([k['experience'] for k in squad.knights])
            }
        
        brigade_readiness = total_readiness / len(self.squads)
        
        # 武具在庫状況
        weapon_inventory = {
            'total_weapons': len(self.weaponry_manager.weapon_inventory),
            'available_weapons': len([
                w for w in self.weaponry_manager.weapon_inventory.values() 
                if w['status'] == 'available'
            ]),
            'deployed_weapons': len([
                w for w in self.weaponry_manager.weapon_inventory.values() 
                if w['status'] == 'deployed'
            ])
        }
        
        # 最近の交戦記録
        recent_engagements = list(self.tactical_coordinator.operation_history)[-5:]
        
        # 工房連携状況
        workshop_coordination = {
            'connection_status': self.workshop_integration['connection_status'],
            'last_delivery': self.weaponry_manager.workshop_connection.get('last_delivery'),
            'pending_requests': len(self.weaponry_manager.workshop_connection['pending_requests']),
            'quality_feedback_pending': len(self.weaponry_manager.workshop_connection['quality_feedback'])
        }
        
        return {
            'brigade_id': self.brigade_id,
            'brigade_name': self.brigade_name,
            'status_timestamp': datetime.now(),
            'operational_status': self.operational_status,
            'current_threat_level': self.current_threat_level,
            'brigade_readiness': brigade_readiness,
            'active_operations': len(self.tactical_coordinator.active_operations),
            'squad_status': squad_status,
            'weapon_inventory': weapon_inventory,
            'recent_engagements': recent_engagements,
            'workshop_coordination': workshop_coordination,
            'elder_coordination_active': all(self.elder_coordination.values())
        }
    
    # プライベートヘルパーメソッド群
    def _test_workshop_communication(self, workshop_id: str, channel: str) -> Dict[str, Any]:
        """工房通信テスト"""
        # 簡易通信テスト
        test_success = random.random() > 0.05  # 95%成功率
        
        if test_success:
            quality_score = random.uniform(0.85, 0.98)
            return {
                'success': True,
                'quality_score': quality_score,
                'latency': random.uniform(10, 50),  # ms
                'reliability': random.uniform(0.95, 0.99)
            }
        else:
            return {
                'success': False,
                'error': 'Communication channel unavailable'
            }
    
    def _perform_initial_workshop_exchange(self) -> Dict[str, Any]:
        """初期工房情報交換"""
        # 騎士団の能力・要求を工房に送信
        brigade_capabilities = {
            'squad_count': len(self.squads),
            'specializations': [squad.squad_type for squad in self.squads.values()],
            'preferred_weapon_types': ['anomaly_detector', 'performance_scout', 'memory_optimizer'],
            'deployment_capacity': 'high'
        }
        
        # 工房からの初期情報（シミュレーション）
        workshop_info = {
            'current_production_capacity': 'high',
            'available_weapon_types': ['anomaly_detector', 'memory_optimizer', 'cpu_balancer'],
            'estimated_delivery_time': 120,  # 2分
            'quality_assurance_level': 'premium'
        }
        
        return {
            'brigade_capabilities_sent': brigade_capabilities,
            'workshop_information_received': workshop_info,
            'mutual_understanding_established': True
        }
    
    def _generate_weapon_requests(self, intel: Dict[str, Any]) -> List[Dict[str, Any]]:
        """武具要求生成"""
        requests = []
        
        # 高優先度機会への対応武具
        for opportunity in intel['high_priority_opportunities']:
            opp_type = opportunity.get('type', 'general')
            
            if 'memory' in opp_type:
                requests.append({
                    'weapon_type': 'memory_optimizer',
                    'quantity': 2,
                    'priority': 'high',
                    'justification': f"Memory optimization opportunity: {opp_type}"
                })
            elif 'cpu' in opp_type:
                requests.append({
                    'weapon_type': 'cpu_balancer',
                    'quantity': 1,
                    'priority': 'medium',
                    'justification': f"CPU optimization opportunity: {opp_type}"
                })
        
        # 新脅威への対応武具
        for threat in intel['new_threats']:
            requests.append({
                'weapon_type': 'anomaly_detector',
                'quantity': 1,
                'priority': 'high',
                'justification': f"New threat detection: {threat}"
            })
        
        return requests
    
    def _distribute_intel_to_squads(self, intel: Dict[str, Any]) -> Dict[str, List[str]]:
        """分隊への情報配布"""
        briefings = {}
        
        for squad_id, squad in self.squads.items():
            squad_briefing = []
            
            # 分隊タイプに応じた情報配布
            if squad.squad_type == 'scout':
                squad_briefing.extend([f"New threat: {t}" for t in intel['new_threats']])
            elif squad.squad_type == 'guardian':
                squad_briefing.extend([f"Defense priority: {opp['type']}" for opp in intel['high_priority_opportunities']])
            elif squad.squad_type == 'specialist':
                squad_briefing.extend([f"Optimization target: {opp['type']}" for opp in intel['high_priority_opportunities']])
            
            # 共通情報
            squad_briefing.append(f"Workshop capacity: {intel['workshop_capacity']}")
            
            briefings[squad_id] = squad_briefing
        
        return briefings
    
    def _assess_threat_level(self, attack_type: str, attack_vectors: List[str], intensity: str) -> str:
        """脅威レベル評価"""
        threat_score = 0
        
        # 攻撃タイプによる基本スコア
        attack_scores = {
            'single_vector_attack': 1,
            'multi_vector_attack': 3,
            'distributed_attack': 4,
            'cascade_attack': 5
        }
        threat_score += attack_scores.get(attack_type, 2)
        
        # 攻撃ベクター数による加算
        threat_score += len(attack_vectors)
        
        # 強度による乗数
        intensity_multipliers = {
            'low': 0.5,
            'medium': 1.0,
            'high': 1.5,
            'critical': 2.0
        }
        threat_score *= intensity_multipliers.get(intensity, 1.0)
        
        # 脅威レベル判定
        if threat_score >= 8:
            return 'red'
        elif threat_score >= 5:
            return 'orange'
        elif threat_score >= 3:
            return 'yellow'
        else:
            return 'green'
    
    def _request_immediate_weapons(self, squad_id: str, attack_vectors: List[str]) -> List[Dict[str, Any]]:
        """即座武具要求"""
        # 攻撃ベクターに基づく武具選択
        weapon_mapping = {
            'cpu_exhaustion': 'cpu_balancer',
            'memory_leak': 'memory_optimizer',
            'io_flooding': 'performance_scout',
            'network_congestion': 'anomaly_detector'
        }
        
        immediate_weapons = []
        for vector in attack_vectors:
            weapon_type = weapon_mapping.get(vector, 'anomaly_detector')
            
            # 在庫から適切な武具を検索
            available_weapons = [
                (wid, wdata) for wid, wdata in self.weaponry_manager.weapon_inventory.items()
                if wdata.get('weapon_type', wdata.get('tool_type')) == weapon_type
                and wdata['status'] == 'available'
            ]
            
            if available_weapons:
                weapon_id, weapon_data = available_weapons[0]
                immediate_weapons.append(weapon_data)
                
                # 在庫から除去
                self.weaponry_manager.weapon_inventory[weapon_id]['status'] = 'deployed'
        
        return immediate_weapons
    
    def _simulate_workshop_emergency_response(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """工房緊急応答シミュレーション"""
        urgency = request['urgency_level']
        
        # 緊急度に基づく応答
        if urgency == 'critical':
            response_time = random.uniform(30, 120)  # 30秒〜2分
            acknowledgment_status = 'immediate_processing'
        elif urgency == 'high':
            response_time = random.uniform(60, 300)  # 1〜5分
            acknowledgment_status = 'priority_processing'
        else:
            response_time = random.uniform(300, 600)  # 5〜10分
            acknowledgment_status = 'standard_processing'
        
        return {
            'status': 'acknowledged',
            'processing_status': acknowledgment_status,
            'estimated_completion': response_time,
            'workshop_capacity_allocation': f"{random.randint(20, 80)}%",
            'craftsman_assigned': random.randint(1, 4)
        }


if __name__ == "__main__":
    # テスト実行
    print("🏰 Knight Brigade System Test")
    print("=" * 50)
    
    # 騎士団初期化
    brigade = KnightBrigade()
    
    print(f"\n🏰 Brigade Status:")
    status = brigade.get_brigade_status()
    print(f"  Brigade Readiness: {status['brigade_readiness']:.2f}")
    print(f"  Active Squads: {len(status['squad_status'])}")
    print(f"  Threat Level: {status['current_threat_level']}")
    
    print(f"\n🔗 Workshop Integration Test:")
    integration = brigade.integrate_with_dwarf_workshop({
        'workshop_id': 'dwarf_workshop_test123',
        'communication_channel': 'secure_forge_link',
        'delivery_frequency': 300
    })
    print(f"  Integration: {'SUCCESS' if integration['integration_successful'] else 'FAILED'}")
    print(f"  Communication: {'ESTABLISHED' if integration['communication_established'] else 'FAILED'}")
    
    print(f"\n⚔️ Coordinated Defense Test:")
    defense_result = brigade.execute_coordinated_defense({
        'attack_type': 'multi_vector_performance_attack',
        'attack_vectors': ['cpu_exhaustion', 'memory_leak', 'io_flooding'],
        'intensity': 'high',
        'priority_targets': ['core_services', 'database_cluster']
    })
    print(f"  Defense Success: {'SUCCESS' if defense_result['defense_success'] else 'PARTIAL'}")
    print(f"  Threats Neutralized: {len(defense_result['threats_neutralized'])}")
    print(f"  Squads Engaged: {defense_result['squads_engaged']}")
    
    print(f"\n🚨 Emergency Weapon Request Test:")
    emergency_response = brigade.request_emergency_weapons({
        'urgency_level': 'critical',
        'required_weapons': [
            {'type': 'emergency_circuit_breaker', 'quantity': 2},
            {'type': 'auto_recovery_system', 'quantity': 1}
        ],
        'deadline': datetime.now() + timedelta(minutes=5),
        'justification': 'system_cascade_prevention'
    })
    print(f"  Request Submitted: {'SUCCESS' if emergency_response['request_submitted'] else 'FAILED'}")
    print(f"  Estimated Delivery: {emergency_response['estimated_delivery_time']:.1f} minutes")
    
    print("\n🎉 Knight Brigade System Test Complete!")
    print("🏰⚔️ Knights and Dwarfs, united we stand! 🔨🛡️")