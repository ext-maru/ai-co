#!/usr/bin/env python3
"""
Service Healer - 4賢者間の連携による高度な自動修復
インシデント賢者の最高レベル治癒能力
"""

import asyncio
import logging
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class ServiceHealer:
    """4賢者連携による自動修復システム"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ai_co_path = Path("/home/aicompany/ai_co")
        
        # 4賢者への参照（実際の実装では適切にインポート）
        self.knowledge_sage = None  # ナレッジベース
        self.task_oracle = None     # タスクトラッカー
        self.rag_mystic = None      # RAG検索
        self.crisis_sage = None     # インシデント管理（自分）
        
        # 治癒セッション履歴
        self.healing_sessions = []
        
        # 学習データ
        self.learned_patterns = {}
        
        self.logger.info("🧙‍♂️ ServiceHealer initialized - 4賢者連携治癒システム起動")
    
    async def sage_council_healing(self, incident_data: Dict) -> Dict:
        """4賢者会議による協調治癒"""
        session_id = f"HEAL-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        healing_session = {
            'session_id': session_id,
            'start_time': datetime.now().isoformat(),
            'incident': incident_data,
            'sage_contributions': {},
            'healing_plan': {},
            'execution_result': {},
            'final_status': 'pending'
        }
        
        self.logger.info(f"🧙‍♂️ Starting sage council for incident: {incident_data.get('incident_id')}")
        
        try:
            # Phase 1: 各賢者からの知見収集
            sage_inputs = await self._gather_sage_wisdom(incident_data)
            healing_session['sage_contributions'] = sage_inputs
            
            # Phase 2: 統合治癒計画立案
            healing_plan = await self._create_healing_plan(incident_data, sage_inputs)
            healing_session['healing_plan'] = healing_plan
            
            # Phase 3: 協調実行
            execution_result = await self._execute_healing_plan(healing_plan)
            healing_session['execution_result'] = execution_result
            
            # Phase 4: 結果評価と学習
            final_status = await self._evaluate_and_learn(healing_session)
            healing_session['final_status'] = final_status
            
        except Exception as e:
            healing_session['error'] = str(e)
            healing_session['final_status'] = 'error'
            self.logger.error(f"Sage council healing failed: {str(e)}")
        
        healing_session['end_time'] = datetime.now().isoformat()
        self.healing_sessions.append(healing_session)
        
        return healing_session
    
    async def _gather_sage_wisdom(self, incident_data: Dict) -> Dict:
        """各賢者から知見を収集"""
        sage_inputs = {}
        
        # ナレッジ賢者への相談
        sage_inputs['knowledge'] = await self._consult_knowledge_sage(incident_data)
        
        # タスク賢者への相談
        sage_inputs['tasks'] = await self._consult_task_oracle(incident_data)
        
        # RAG賢者への相談
        sage_inputs['search'] = await self._consult_rag_mystic(incident_data)
        
        # インシデント賢者（自分）の分析
        sage_inputs['crisis'] = await self._self_analysis(incident_data)
        
        return sage_inputs
    
    async def _consult_knowledge_sage(self, incident_data: Dict) -> Dict:
        """ナレッジ賢者への相談"""
        try:
            # 過去の類似インシデント検索
            similar_incidents = []
            incident_kb_path = self.ai_co_path / "knowledge_base" / "incident_management" / "incident_history.json"
            
            if incident_kb_path.exists():
                with open(incident_kb_path, 'r') as f:
                    kb_data = json.load(f)
                
                # 簡易類似性検索
                error_keywords = set(incident_data.get('description', '').lower().split())
                for past_incident in kb_data.get('incidents', []):
                    if past_incident.get('status') == 'resolved':
                        past_desc = past_incident.get('description', '').lower()
                        past_keywords = set(past_desc.split())
                        
                        common = len(error_keywords & past_keywords)
                        if common >= 2:
                            similar_incidents.append({
                                'incident': past_incident,
                                'similarity_score': common
                            })
            
            # ナレッジベースからのパターン情報
            patterns_found = []
            patterns_kb_path = self.ai_co_path / "knowledge_base" / "incident_management" / "INCIDENT_PATTERNS_KB.md"
            if patterns_kb_path.exists():
                with open(patterns_kb_path, 'r') as f:
                    content = f.read()
                    # 簡易パターンマッチング
                    for keyword in error_keywords:
                        if keyword in content.lower():
                            patterns_found.append(keyword)
            
            return {
                'similar_incidents': sorted(similar_incidents, 
                                          key=lambda x: x['similarity_score'], reverse=True)[:3],
                'relevant_patterns': patterns_found,
                'knowledge_confidence': len(similar_incidents) * 0.3,
                'recommended_actions': self._extract_recommended_actions(similar_incidents)
            }
            
        except Exception as e:
            return {'error': str(e), 'knowledge_confidence': 0}
    
    async def _consult_task_oracle(self, incident_data: Dict) -> Dict:
        """タスク賢者への相談"""
        try:
            # 現在のタスク状況と優先度評価
            task_analysis = {
                'current_priority': self._assess_incident_priority(incident_data),
                'resource_availability': self._check_resource_availability(),
                'estimated_effort': self._estimate_healing_effort(incident_data),
                'optimal_timing': self._determine_optimal_timing(),
                'parallel_tasks': self._identify_parallel_tasks(incident_data)
            }
            
            return task_analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _consult_rag_mystic(self, incident_data: Dict) -> Dict:
        """RAG賢者への相談"""
        try:
            # 関連ドキュメント検索
            search_queries = [
                incident_data.get('title', ''),
                incident_data.get('description', ''),
                ' '.join(incident_data.get('affected_components', []))
            ]
            
            relevant_docs = []
            for query in search_queries:
                if query.strip():
                    docs = await self._search_documentation(query)
                    relevant_docs.extend(docs)
            
            # 技術的解決策の提案
            technical_solutions = await self._find_technical_solutions(incident_data)
            
            return {
                'relevant_documentation': relevant_docs[:5],
                'technical_solutions': technical_solutions,
                'external_references': await self._find_external_references(incident_data),
                'confidence_score': min(len(relevant_docs) * 0.2, 1.0)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _self_analysis(self, incident_data: Dict) -> Dict:
        """インシデント賢者（自分）の分析"""
        try:
            category = incident_data.get('category', 'unknown')
            priority = incident_data.get('priority', 'medium')
            
            # 自動修復可能性評価
            auto_fix_probability = self._assess_auto_fix_probability(incident_data)
            
            # リスク評価
            risk_assessment = self._assess_risks(incident_data)
            
            # 即座の対応要否
            immediate_action_needed = priority in ['critical', 'high']
            
            return {
                'auto_fix_probability': auto_fix_probability,
                'risk_level': risk_assessment['level'],
                'risk_factors': risk_assessment['factors'],
                'immediate_action': immediate_action_needed,
                'confidence_level': 'high'  # 自分の分析なので高信頼度
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _create_healing_plan(self, incident_data: Dict, sage_inputs: Dict) -> Dict:
        """統合治癒計画立案"""
        plan = {
            'strategy': 'unknown',
            'phases': [],
            'estimated_duration': 0,
            'confidence': 0,
            'rollback_plan': []
        }
        
        # 各賢者の提案を統合
        knowledge_confidence = sage_inputs.get('knowledge', {}).get('knowledge_confidence', 0)
        crisis_confidence = sage_inputs.get('crisis', {}).get('confidence_level') == 'high'
        
        total_confidence = (knowledge_confidence + (1 if crisis_confidence else 0)) / 2
        
        if total_confidence > 0.7:
            plan['strategy'] = 'automated_healing'
            plan['phases'] = self._create_automated_phases(incident_data, sage_inputs)
        elif total_confidence > 0.4:
            plan['strategy'] = 'guided_healing'
            plan['phases'] = self._create_guided_phases(incident_data, sage_inputs)
        else:
            plan['strategy'] = 'manual_escalation'
            plan['phases'] = self._create_escalation_phases(incident_data, sage_inputs)
        
        plan['confidence'] = total_confidence
        plan['estimated_duration'] = sum(phase.get('duration', 5) for phase in plan['phases'])
        
        return plan
    
    async def _execute_healing_plan(self, healing_plan: Dict) -> Dict:
        """治癒計画実行"""
        execution_result = {
            'strategy_used': healing_plan['strategy'],
            'phases_executed': [],
            'successful_phases': [],
            'failed_phases': [],
            'overall_success': False
        }
        
        for i, phase in enumerate(healing_plan['phases']):
            phase_name = phase['name']
            execution_result['phases_executed'].append(phase_name)
            
            self.logger.info(f"🔧 Executing healing phase: {phase_name}")
            
            try:
                phase_success = await self._execute_phase(phase)
                
                if phase_success:
                    execution_result['successful_phases'].append(phase_name)
                    self.logger.info(f"✅ Phase {phase_name} successful")
                else:
                    execution_result['failed_phases'].append(phase_name)
                    self.logger.warning(f"⚠️ Phase {phase_name} failed")
                    
                    # クリティカルフェーズが失敗した場合は停止
                    if phase.get('critical', False):
                        break
                        
            except Exception as e:
                execution_result['failed_phases'].append(phase_name)
                self.logger.error(f"❌ Phase {phase_name} error: {str(e)}")
        
        # 全体成功判定
        total_phases = len(healing_plan['phases'])
        successful_phases = len(execution_result['successful_phases'])
        execution_result['overall_success'] = successful_phases / total_phases >= 0.7 if total_phases > 0 else False
        
        return execution_result
    
    async def _evaluate_and_learn(self, healing_session: Dict) -> str:
        """結果評価と学習"""
        try:
            execution_result = healing_session['execution_result']
            incident_data = healing_session['incident']
            
            # 成功度評価
            if execution_result['overall_success']:
                final_status = 'healed'
                
                # 成功パターンを学習
                pattern_key = f"{incident_data.get('category')}_{incident_data.get('priority')}"
                if pattern_key not in self.learned_patterns:
                    self.learned_patterns[pattern_key] = {'success_count': 0, 'strategies': []}
                
                self.learned_patterns[pattern_key]['success_count'] += 1
                strategy = healing_session['healing_plan']['strategy']
                if strategy not in self.learned_patterns[pattern_key]['strategies']:
                    self.learned_patterns[pattern_key]['strategies'].append(strategy)
            
            elif len(execution_result['successful_phases']) > 0:
                final_status = 'partially_healed'
            else:
                final_status = 'healing_failed'
            
            # 学習データ保存
            await self._save_learning_data()
            
            return final_status
            
        except Exception as e:
            self.logger.error(f"Evaluation failed: {str(e)}")
            return 'evaluation_error'
    
    # === ヘルパーメソッド ===
    
    def _extract_recommended_actions(self, similar_incidents: List[Dict]) -> List[str]:
        """類似インシデントから推奨アクションを抽出"""
        actions = []
        for incident_data in similar_incidents:
            incident = incident_data.get('incident', {})
            resolution = incident.get('resolution')
            if resolution:
                actions.extend(resolution.get('actions_taken', []))
        
        # 重複除去と頻度順ソート
        action_counts = {}
        for action in actions:
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return sorted(action_counts.keys(), key=lambda x: action_counts[x], reverse=True)[:3]
    
    def _assess_incident_priority(self, incident_data: Dict) -> int:
        """インシデント優先度数値化"""
        priority_map = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        return priority_map.get(incident_data.get('priority', 'medium'), 2)
    
    def _check_resource_availability(self) -> Dict:
        """リソース可用性確認"""
        # 簡易実装
        return {
            'cpu_available': True,
            'memory_available': True,
            'network_available': True,
            'external_services_available': True
        }
    
    def _estimate_healing_effort(self, incident_data: Dict) -> int:
        """治癒工数見積もり（分）"""
        category = incident_data.get('category', 'unknown')
        priority = incident_data.get('priority', 'medium')
        
        base_effort = {'error': 10, 'failure': 20, 'security': 30, 'performance': 15}.get(category, 15)
        priority_multiplier = {'critical': 2, 'high': 1.5, 'medium': 1, 'low': 0.8}.get(priority, 1)
        
        return int(base_effort * priority_multiplier)
    
    def _determine_optimal_timing(self) -> str:
        """最適実行タイミング判定"""
        current_hour = datetime.now().hour
        
        if 2 <= current_hour <= 6:
            return 'optimal'  # 深夜メンテ時間
        elif 9 <= current_hour <= 17:
            return 'business_hours'
        else:
            return 'acceptable'
    
    def _identify_parallel_tasks(self, incident_data: Dict) -> List[str]:
        """並行実行可能タスク特定"""
        # 簡易実装
        category = incident_data.get('category', 'unknown')
        
        parallel_tasks = {
            'error': ['log_collection', 'environment_check'],
            'failure': ['service_check', 'dependency_verification'],
            'performance': ['metrics_collection', 'profiling']
        }
        
        return parallel_tasks.get(category, ['system_check'])
    
    async def _search_documentation(self, query: str) -> List[Dict]:
        """ドキュメント検索"""
        # 簡易実装（実際はRAGシステムと連携）
        docs_path = self.ai_co_path / "knowledge_base"
        found_docs = []
        
        if docs_path.exists():
            for md_file in docs_path.rglob("*.md"):
                try:
                    with open(md_file, 'r') as f:
                        content = f.read()
                        if query.lower() in content.lower():
                            found_docs.append({
                                'file': str(md_file.name),
                                'relevance': content.lower().count(query.lower())
                            })
                except:
                    continue
        
        return sorted(found_docs, key=lambda x: x['relevance'], reverse=True)
    
    async def _find_technical_solutions(self, incident_data: Dict) -> List[Dict]:
        """技術的解決策検索"""
        # 簡易実装
        solutions = []
        category = incident_data.get('category', 'unknown')
        
        solution_templates = {
            'error': [
                {'type': 'restart_service', 'confidence': 0.8},
                {'type': 'clear_cache', 'confidence': 0.6},
                {'type': 'reinstall_dependencies', 'confidence': 0.4}
            ],
            'failure': [
                {'type': 'service_recovery', 'confidence': 0.9},
                {'type': 'failover_activation', 'confidence': 0.7}
            ]
        }
        
        return solution_templates.get(category, [])
    
    async def _find_external_references(self, incident_data: Dict) -> List[str]:
        """外部参考情報検索"""
        # 簡易実装
        return [
            "AI Company Documentation",
            "System Administration Guide",
            "Troubleshooting Manual"
        ]
    
    def _assess_auto_fix_probability(self, incident_data: Dict) -> float:
        """自動修復可能性評価"""
        category = incident_data.get('category', 'unknown')
        description = incident_data.get('description', '').lower()
        
        # カテゴリベース基本確率
        base_probability = {
            'error': 0.7,
            'failure': 0.5,
            'performance': 0.6,
            'security': 0.3,
            'change': 0.8
        }.get(category, 0.4)
        
        # キーワードベース調整
        if any(word in description for word in ['connection', 'timeout', 'network']):
            base_probability += 0.2
        
        if any(word in description for word in ['corruption', 'security', 'breach']):
            base_probability -= 0.3
        
        return max(0, min(1, base_probability))
    
    def _assess_risks(self, incident_data: Dict) -> Dict:
        """リスク評価"""
        priority = incident_data.get('priority', 'medium')
        category = incident_data.get('category', 'unknown')
        
        risk_level = 'low'
        risk_factors = []
        
        if priority == 'critical':
            risk_level = 'high'
            risk_factors.append('critical_priority')
        
        if category in ['security', 'failure']:
            risk_level = 'medium' if risk_level == 'low' else 'high'
            risk_factors.append(f'sensitive_category_{category}')
        
        return {'level': risk_level, 'factors': risk_factors}
    
    def _create_automated_phases(self, incident_data: Dict, sage_inputs: Dict) -> List[Dict]:
        """自動治癒フェーズ作成"""
        phases = [
            {'name': 'pre_healing_backup', 'duration': 2, 'critical': True},
            {'name': 'automated_diagnosis', 'duration': 3, 'critical': False},
            {'name': 'automated_fix_execution', 'duration': 10, 'critical': True},
            {'name': 'verification_and_testing', 'duration': 5, 'critical': True},
            {'name': 'post_healing_monitoring', 'duration': 5, 'critical': False}
        ]
        return phases
    
    def _create_guided_phases(self, incident_data: Dict, sage_inputs: Dict) -> List[Dict]:
        """ガイド付き治癒フェーズ作成"""
        phases = [
            {'name': 'guided_diagnosis', 'duration': 5, 'critical': False},
            {'name': 'solution_recommendation', 'duration': 3, 'critical': False},
            {'name': 'supervised_execution', 'duration': 15, 'critical': True},
            {'name': 'result_validation', 'duration': 5, 'critical': True}
        ]
        return phases
    
    def _create_escalation_phases(self, incident_data: Dict, sage_inputs: Dict) -> List[Dict]:
        """エスカレーションフェーズ作成"""
        phases = [
            {'name': 'incident_documentation', 'duration': 3, 'critical': True},
            {'name': 'expert_notification', 'duration': 2, 'critical': True},
            {'name': 'manual_intervention_preparation', 'duration': 5, 'critical': False}
        ]
        return phases
    
    async def _execute_phase(self, phase: Dict) -> bool:
        """フェーズ実行"""
        phase_name = phase['name']
        duration = phase.get('duration', 5)
        
        # 実際の実装では各フェーズに応じた処理を実行
        # ここでは簡易シミュレーション
        await asyncio.sleep(min(duration, 2))  # 実際の待機時間は短縮
        
        # 80%の確率で成功とする（デモ用）
        import random
        return random.random() > 0.2
    
    async def _save_learning_data(self):
        """学習データ保存"""
        try:
            learning_file = self.ai_co_path / "knowledge_base" / "incident_management" / "healing_patterns.json"
            with open(learning_file, 'w') as f:
                json.dump(self.learned_patterns, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save learning data: {str(e)}")
    
    def get_healing_statistics(self) -> Dict:
        """治癒統計取得"""
        if not self.healing_sessions:
            return {'total_sessions': 0}
        
        total_sessions = len(self.healing_sessions)
        successful_sessions = sum(1 for session in self.healing_sessions 
                                if session['final_status'] == 'healed')
        
        strategies_used = {}
        for session in self.healing_sessions:
            strategy = session.get('healing_plan', {}).get('strategy', 'unknown')
            strategies_used[strategy] = strategies_used.get(strategy, 0) + 1
        
        return {
            'total_sessions': total_sessions,
            'successful_sessions': successful_sessions,
            'success_rate': successful_sessions / total_sessions if total_sessions > 0 else 0,
            'strategies_used': strategies_used,
            'learned_patterns': len(self.learned_patterns)
        }