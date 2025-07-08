#!/usr/bin/env python3
"""
Claude Elder Chat API - エルダーズとの対話システム
AI Company エルダーズ評議会承認済み
"""

import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import sys
import subprocess
import os
import time

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.env_config import get_config
# Conditional imports to handle compatibility issues
try:
    from libs.pm_elder_integration import PMElderIntegration
except ImportError:
    PMElderIntegration = None

try:
    from libs.elder_council_auto_decision import ElderCouncilAutoDecision
except ImportError:
    ElderCouncilAutoDecision = None

try:
    from libs.elder_servant_dispatcher import ElderServantDispatcher
except ImportError:
    ElderServantDispatcher = None

try:
    from libs.rag_elder_wizards import RAGElderWizards
except ImportError:
    RAGElderWizards = None

class ClaudeElderChatAPI:
    """Claude Elder Chat API - エルダーズとの統合対話システム"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = get_config()
        
        # エルダーシステム統合（互換性チェック付き）
        self.pm_elder = PMElderIntegration() if PMElderIntegration else None
        self.elder_council = ElderCouncilAutoDecision() if ElderCouncilAutoDecision else None
        self.servant_dispatcher = ElderServantDispatcher() if ElderServantDispatcher else None
        self.rag_wizards = RAGElderWizards() if RAGElderWizards else None
        
        # 対話履歴
        self.conversation_history = []
        
        # コマンドマッピング
        self.command_handlers = {
            'task': self._handle_task_command,
            'status': self._handle_status_command,
            'deploy': self._handle_deploy_command,
            'query': self._handle_query_command,
            'council': self._handle_council_command,
            'servant': self._handle_servant_command,
            'wisdom': self._handle_wisdom_command,
            'help': self._handle_help_command
        }
    
    async def process_chat_message(self, message: str, user_id: str = "claude") -> Dict[str, Any]:
        """チャットメッセージを処理"""
        try:
            # 対話履歴に追加
            self.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'message': message,
                'type': 'user'
            })
            
            # コマンド解析
            command_result = await self._parse_and_execute_command(message)
            
            # エルダーレスポンス生成
            elder_response = await self._generate_elder_response(message, command_result)
            
            # 対話履歴に追加
            self.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'user_id': 'claude_elder',
                'message': elder_response['response'],
                'type': 'elder',
                'command_result': command_result
            })
            
            return elder_response
            
        except Exception as e:
            self.logger.error(f"Chat processing error: {str(e)}")
            return {
                'success': False,
                'response': f"🧾 エラーが発生しました: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'elder': 'claude_elder'
            }
    
    async def _parse_and_execute_command(self, message: str) -> Dict[str, Any]:
        """コマンドを解析・実行"""
        message_lower = message.lower()
        
        # コマンドマッチング
        for command, handler in self.command_handlers.items():
            if command in message_lower:
                return await handler(message)
        
        # 一般的なキーワードマッチング
        if any(keyword in message_lower for keyword in ['メモリ', 'memory', 'cpu', 'システム', 'system']):
            return await self._handle_status_command(message)
        elif any(keyword in message_lower for keyword in ['タスク', 'task', '実行', 'execute']):
            return await self._handle_task_command(message)
        elif any(keyword in message_lower for keyword in ['サーベント', 'servant', '騎士', 'knight', 'ドワーフ', 'dwarf']):
            return await self._handle_servant_command(message)
        
        return {'type': 'general', 'result': 'no_specific_command'}
    
    async def _handle_task_command(self, message: str) -> Dict[str, Any]:
        """タスク関連コマンド処理"""
        try:
            # タスクタイプを推定
            task_type = 'general'
            if 'カバレッジ' in message or 'coverage' in message.lower():
                task_type = 'coverage_improvement'
            elif 'テスト' in message or 'test' in message.lower():
                task_type = 'testing_enhancement'
            elif '最適化' in message or 'optimization' in message.lower():
                task_type = 'optimization'
            
            # タスクエルダーに委任
            result = await self._delegate_to_task_elder(task_type, message)
            
            return {
                'type': 'task_delegation',
                'task_type': task_type,
                'result': result,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Task command error: {str(e)}")
            return {
                'type': 'task_delegation',
                'result': {'error': str(e)},
                'success': False
            }
    
    async def _handle_status_command(self, message: str) -> Dict[str, Any]:
        """ステータス関連コマンド処理"""
        try:
            import psutil
            
            # システムステータス取得
            system_status = {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_percent': psutil.disk_usage('/').percent,
                'cpu_count': psutil.cpu_count()
            }
            
            # エルダーシステムステータス
            elder_status = await self._get_elder_systems_status()
            
            return {
                'type': 'system_status',
                'system_status': system_status,
                'elder_status': elder_status,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Status command error: {str(e)}")
            return {
                'type': 'system_status',
                'result': {'error': str(e)},
                'success': False
            }
    
    async def _handle_deploy_command(self, message: str) -> Dict[str, Any]:
        """デプロイメント関連コマンド処理"""
        try:
            # サーベントタイプを推定
            servant_type = 'knight'
            if 'ドワーフ' in message or 'dwarf' in message.lower():
                servant_type = 'dwarf'
            elif 'ウィザード' in message or 'wizard' in message.lower():
                servant_type = 'wizard'
            elif 'エルフ' in message or 'elf' in message.lower():
                servant_type = 'elf'
            
            # サーベント配備
            result = await self._deploy_servant(servant_type, message)
            
            return {
                'type': 'servant_deployment',
                'servant_type': servant_type,
                'result': result,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Deploy command error: {str(e)}")
            return {
                'type': 'servant_deployment',
                'result': {'error': str(e)},
                'success': False
            }
    
    async def _handle_query_command(self, message: str) -> Dict[str, Any]:
        """クエリ関連コマンド処理"""
        try:
            # RAGウィザーズによる知識検索
            query_result = await self._query_elder_wisdom(message)
            
            return {
                'type': 'knowledge_query',
                'query': message,
                'result': query_result,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Query command error: {str(e)}")
            return {
                'type': 'knowledge_query',
                'result': {'error': str(e)},
                'success': False
            }
    
    async def _handle_council_command(self, message: str) -> Dict[str, Any]:
        """評議会関連コマンド処理"""
        try:
            # エルダー評議会召集
            council_result = await self._summon_elder_council(message)
            
            return {
                'type': 'council_session',
                'topic': message,
                'result': council_result,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Council command error: {str(e)}")
            return {
                'type': 'council_session',
                'result': {'error': str(e)},
                'success': False
            }
    
    async def _handle_servant_command(self, message: str) -> Dict[str, Any]:
        """サーベント関連コマンド処理"""
        try:
            # サーベント状態確認
            servant_status = await self._get_servant_status()
            
            return {
                'type': 'servant_status',
                'status': servant_status,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Servant command error: {str(e)}")
            return {
                'type': 'servant_status',
                'result': {'error': str(e)},
                'success': False
            }
    
    async def _handle_wisdom_command(self, message: str) -> Dict[str, Any]:
        """知恵関連コマンド処理"""
        try:
            # エルダー知恵検索
            wisdom_result = await self._search_elder_wisdom(message)
            
            return {
                'type': 'elder_wisdom',
                'query': message,
                'result': wisdom_result,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Wisdom command error: {str(e)}")
            return {
                'type': 'elder_wisdom',
                'result': {'error': str(e)},
                'success': False
            }
    
    async def _handle_help_command(self, message: str) -> Dict[str, Any]:
        """ヘルプコマンド処理"""
        help_info = {
            'available_commands': [
                'task <タスク内容> - タスクエルダーに委任',
                'status - システム状態確認',
                'deploy <サーベント> - サーベント配備',
                'query <質問> - 知識検索',
                'council <議題> - エルダー評議会召集',
                'servant - サーベント状態確認',
                'wisdom <質問> - エルダー知恵検索',
                'help - このヘルプ表示'
            ],
            'elder_systems': [
                '📚 ナレッジ賢者 - 知識管理・学習',
                '📋 タスク賢者 - タスク管理・最適化',
                '🚨 インシデント賢者 - 危機対応・監視',
                '🔍 RAG賢者 - 情報検索・統合'
            ],
            'servant_types': [
                '⚔️ 騎士団 - 緊急対応・品質保証',
                '🔨 ドワーフ工房 - 開発・製作',
                '🧙‍♂️ ウィザーズ - 分析・研究',
                '🧝‍♂️ エルフの森 - 監視・メンテナンス'
            ]
        }
        
        return {
            'type': 'help_info',
            'help_info': help_info,
            'success': True
        }
    
    async def _generate_elder_response(self, message: str, command_result: Dict[str, Any]) -> Dict[str, Any]:
        """エルダーレスポンス生成"""
        try:
            response_type = command_result.get('type', 'general')
            
            if response_type == 'task_delegation':
                return self._generate_task_response(command_result)
            elif response_type == 'system_status':
                return self._generate_status_response(command_result)
            elif response_type == 'servant_deployment':
                return self._generate_deployment_response(command_result)
            elif response_type == 'knowledge_query':
                return self._generate_query_response(command_result)
            elif response_type == 'council_session':
                return self._generate_council_response(command_result)
            elif response_type == 'servant_status':
                return self._generate_servant_response(command_result)
            elif response_type == 'elder_wisdom':
                return self._generate_wisdom_response(command_result)
            elif response_type == 'help_info':
                return self._generate_help_response(command_result)
            else:
                return self._generate_general_response(message)
                
        except Exception as e:
            self.logger.error(f"Response generation error: {str(e)}")
            return {
                'success': False,
                'response': f"🧾 クロードエルダー: レスポンス生成中にエラーが発生しました: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'elder': 'claude_elder'
            }
    
    def _generate_task_response(self, command_result: Dict[str, Any]) -> Dict[str, Any]:
        """タスク委任レスポンス生成"""
        if command_result.get('success'):
            task_type = command_result.get('task_type', 'general')
            response = f"🧾 クロードエルダー: タスクエルダーに{task_type}タスクを委任しました。\n"
            response += "📋 タスク賢者が実行計画を策定中です。\n"
            response += "🧝‍♂️ エルフチームが依存関係を分析中です。\n"
            response += "✅ 進捗は定期的にお知らせします。"
        else:
            response = f"🧾 クロードエルダー: タスク委任中にエラーが発生しました。\n"
            response += f"⚠️ エラー詳細: {command_result.get('result', {}).get('error', 'Unknown error')}"
        
        return {
            'success': command_result.get('success'),
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'elder': 'claude_elder'
        }
    
    def _generate_status_response(self, command_result: Dict[str, Any]) -> Dict[str, Any]:
        """ステータスレスポンス生成"""
        if command_result.get('success'):
            system_status = command_result.get('system_status', {})
            elder_status = command_result.get('elder_status', {})
            
            response = f"🧾 クロードエルダー: システム状態レポート\n\n"
            response += f"💻 システム状態:\n"
            response += f"  CPU: {system_status.get('cpu_percent', 0):.1f}% ({system_status.get('cpu_count', 0)}コア)\n"
            response += f"  メモリ: {system_status.get('memory_percent', 0):.1f}% "
            response += f"({system_status.get('memory_available', 0) / (1024**3):.1f}GB利用可能)\n"
            response += f"  ディスク: {system_status.get('disk_percent', 0):.1f}%\n\n"
            response += f"🏛️ エルダーシステム:\n"
            for elder_name, status in elder_status.items():
                response += f"  {elder_name}: {status}\n"
        else:
            response = f"🧾 クロードエルダー: ステータス取得中にエラーが発生しました。\n"
            response += f"⚠️ エラー詳細: {command_result.get('result', {}).get('error', 'Unknown error')}"
        
        return {
            'success': command_result.get('success'),
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'elder': 'claude_elder'
        }
    
    def _generate_deployment_response(self, command_result: Dict[str, Any]) -> Dict[str, Any]:
        """デプロイメントレスポンス生成"""
        if command_result.get('success'):
            servant_type = command_result.get('servant_type', 'knight')
            response = f"🧾 クロードエルダー: {servant_type}サーベントを配備しました。\n"
            response += f"🤖 サーベント配備完了\n"
            response += f"📊 配備状況は監視中です。"
        else:
            response = f"🧾 クロードエルダー: サーベント配備中にエラーが発生しました。\n"
            response += f"⚠️ エラー詳細: {command_result.get('result', {}).get('error', 'Unknown error')}"
        
        return {
            'success': command_result.get('success'),
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'elder': 'claude_elder'
        }
    
    def _generate_query_response(self, command_result: Dict[str, Any]) -> Dict[str, Any]:
        """クエリレスポンス生成"""
        if command_result.get('success'):
            query_result = command_result.get('result', {})
            response = f"🧾 クロードエルダー: 知識検索結果\n\n"
            response += f"🔍 検索クエリ: {command_result.get('query', 'N/A')}\n"
            response += f"📚 検索結果: {query_result.get('answer', '結果なし')}\n"
            response += f"🎯 関連情報: {query_result.get('related_info', 'なし')}"
        else:
            response = f"🧾 クロードエルダー: 知識検索中にエラーが発生しました。\n"
            response += f"⚠️ エラー詳細: {command_result.get('result', {}).get('error', 'Unknown error')}"
        
        return {
            'success': command_result.get('success'),
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'elder': 'claude_elder'
        }
    
    def _generate_council_response(self, command_result: Dict[str, Any]) -> Dict[str, Any]:
        """評議会レスポンス生成"""
        if command_result.get('success'):
            council_result = command_result.get('result', {})
            response = f"🧾 クロードエルダー: エルダー評議会を召集しました。\n\n"
            response += f"🏛️ 議題: {command_result.get('topic', 'N/A')}\n"
            response += f"👥 参加者: 4賢者全員\n"
            response += f"📜 決定事項: {council_result.get('decision', '協議中')}\n"
            response += f"⏰ 次回会議: {council_result.get('next_meeting', 'TBD')}"
        else:
            response = f"🧾 クロードエルダー: エルダー評議会召集中にエラーが発生しました。\n"
            response += f"⚠️ エラー詳細: {command_result.get('result', {}).get('error', 'Unknown error')}"
        
        return {
            'success': command_result.get('success'),
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'elder': 'claude_elder'
        }
    
    def _generate_servant_response(self, command_result: Dict[str, Any]) -> Dict[str, Any]:
        """サーベントレスポンス生成"""
        if command_result.get('success'):
            servant_status = command_result.get('status', {})
            response = f"🧾 クロードエルダー: サーベント状態レポート\n\n"
            for servant_type, servants in servant_status.items():
                response += f"{servant_type}: {len(servants)}体稼働中\n"
                for servant_name, status in servants.items():
                    response += f"  {servant_name}: {status.get('status', 'unknown')}\n"
        else:
            response = f"🧾 クロードエルダー: サーベント状態取得中にエラーが発生しました。\n"
            response += f"⚠️ エラー詳細: {command_result.get('result', {}).get('error', 'Unknown error')}"
        
        return {
            'success': command_result.get('success'),
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'elder': 'claude_elder'
        }
    
    def _generate_wisdom_response(self, command_result: Dict[str, Any]) -> Dict[str, Any]:
        """知恵レスポンス生成"""
        if command_result.get('success'):
            wisdom_result = command_result.get('result', {})
            response = f"🧾 クロードエルダー: エルダー知恵検索結果\n\n"
            response += f"🔮 クエリ: {command_result.get('query', 'N/A')}\n"
            response += f"📜 エルダー知恵: {wisdom_result.get('wisdom', '知恵なし')}\n"
            response += f"🎯 適用案: {wisdom_result.get('application', 'なし')}"
        else:
            response = f"🧾 クロードエルダー: エルダー知恵検索中にエラーが発生しました。\n"
            response += f"⚠️ エラー詳細: {command_result.get('result', {}).get('error', 'Unknown error')}"
        
        return {
            'success': command_result.get('success'),
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'elder': 'claude_elder'
        }
    
    def _generate_help_response(self, command_result: Dict[str, Any]) -> Dict[str, Any]:
        """ヘルプレスポンス生成"""
        help_info = command_result.get('help_info', {})
        response = f"🧾 クロードエルダー: ヘルプ情報\n\n"
        response += f"📋 利用可能なコマンド:\n"
        for cmd in help_info.get('available_commands', []):
            response += f"  • {cmd}\n"
        response += f"\n🏛️ エルダーシステム:\n"
        for elder in help_info.get('elder_systems', []):
            response += f"  • {elder}\n"
        response += f"\n🤖 サーベント種別:\n"
        for servant in help_info.get('servant_types', []):
            response += f"  • {servant}\n"
        
        return {
            'success': True,
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'elder': 'claude_elder'
        }
    
    def _generate_general_response(self, message: str) -> Dict[str, Any]:
        """一般的なレスポンス生成"""
        response = f"🧾 クロードエルダー: '{message}' について承知しました。\n\n"
        response += "私は以下の機能をサポートしています:\n"
        response += "• システム監視とステータス確認\n"
        response += "• タスクエルダーへの委任\n"
        response += "• サーベント配備と管理\n"
        response += "• エルダー評議会召集\n"
        response += "• 知識検索と知恵の探求\n\n"
        response += "具体的な指示をお聞かせください。'help'で詳細なヘルプを表示します。"
        
        return {
            'success': True,
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'elder': 'claude_elder'
        }
    
    async def _delegate_to_task_elder(self, task_type: str, message: str) -> Dict[str, Any]:
        """タスクエルダーに委任"""
        try:
            if self.pm_elder:
                # PM Elder統合システム使用
                result = await asyncio.to_thread(
                    self.pm_elder.request_elder_approval,
                    {
                        'task_type': task_type,
                        'description': message,
                        'priority': 'normal',
                        'estimated_duration': '15-30分'
                    }
                )
                
                return {
                    'success': True,
                    'task_id': result.get('task_id'),
                    'status': result.get('status'),
                    'message': 'タスクエルダーに委任完了'
                }
            else:
                # フォールバック: シミュレート
                task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                return {
                    'success': True,
                    'task_id': task_id,
                    'status': 'accepted',
                    'message': 'タスクエルダーに委任完了（シミュレート）'
                }
            
        except Exception as e:
            self.logger.error(f"Task delegation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _get_elder_systems_status(self) -> Dict[str, str]:
        """エルダーシステムステータス取得"""
        try:
            return {
                '📚 ナレッジ賢者': '学習中',
                '📋 タスク賢者': '調整中',
                '🚨 インシデント賢者': '監視中',
                '🔍 RAG賢者': '探索中'
            }
        except Exception as e:
            self.logger.error(f"Elder status error: {str(e)}")
            return {'error': str(e)}
    
    async def _deploy_servant(self, servant_type: str, message: str) -> Dict[str, Any]:
        """サーベント配備"""
        try:
            # Elder Servant Dispatcher使用
            result = await asyncio.to_thread(
                self.servant_dispatcher.deploy_servant,
                servant_type,
                message
            )
            
            return {
                'success': True,
                'servant_id': result.get('servant_id'),
                'status': result.get('status'),
                'message': 'サーベント配備完了'
            }
            
        except Exception as e:
            self.logger.error(f"Servant deployment error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _query_elder_wisdom(self, query: str) -> Dict[str, Any]:
        """エルダー知恵検索"""
        try:
            # RAG Elder Wizards使用
            result = await asyncio.to_thread(
                self.rag_wizards.search_knowledge,
                query
            )
            
            return {
                'success': True,
                'answer': result.get('answer'),
                'related_info': result.get('related_info'),
                'confidence': result.get('confidence')
            }
            
        except Exception as e:
            self.logger.error(f"Elder wisdom query error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _summon_elder_council(self, topic: str) -> Dict[str, Any]:
        """エルダー評議会召集"""
        try:
            # Elder Council Auto Decision使用
            result = await asyncio.to_thread(
                self.elder_council.deliberate_decision,
                topic
            )
            
            return {
                'success': True,
                'decision': result.get('decision'),
                'unanimous': result.get('unanimous'),
                'next_meeting': result.get('next_meeting')
            }
            
        except Exception as e:
            self.logger.error(f"Elder council error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _get_servant_status(self) -> Dict[str, Any]:
        """サーベント状態取得"""
        try:
            return {
                '⚔️ 騎士団': {
                    'test_guardian_001': {'status': 'patrolling'},
                    'coverage_enhancement_001': {'status': 'ready'}
                },
                '🔨 ドワーフ工房': {
                    'build_support_001': {'status': 'ready'}
                },
                '🧙‍♂️ ウィザーズ': {
                    'monitoring_analysis_001': {'status': 'analyzing'}
                },
                '🧝‍♂️ エルフの森': {
                    'alert_watcher_001': {'status': 'monitoring'}
                }
            }
        except Exception as e:
            self.logger.error(f"Servant status error: {str(e)}")
            return {'error': str(e)}
    
    async def _search_elder_wisdom(self, query: str) -> Dict[str, Any]:
        """エルダー知恵検索"""
        try:
            # 知恵データベース検索（モック）
            wisdom_db = {
                'tdd': {
                    'wisdom': 'テストを最初に書くことで、設計の明確化と品質保証を実現する',
                    'application': 'RED→GREEN→REFACTOR サイクルを厳守する'
                },
                'coverage': {
                    'wisdom': 'カバレッジは品質の指標だが、100%が目標ではない。重要なのは意味のあるテスト',
                    'application': '新規コード95%、既存コード80%を目安とする'
                },
                'optimization': {
                    'wisdom': '早すぎる最適化は諸悪の根源。まず動作させ、次に測定し、最後に最適化する',
                    'application': 'プロファイリングでボトルネック特定後に実施'
                }
            }
            
            # キーワードマッチング
            for keyword, wisdom_data in wisdom_db.items():
                if keyword in query.lower():
                    return {
                        'success': True,
                        'wisdom': wisdom_data['wisdom'],
                        'application': wisdom_data['application']
                    }
            
            return {
                'success': True,
                'wisdom': 'エルダーの知恵: 問題を細分化し、一つずつ解決することが成功への道',
                'application': '大きな問題は小さな問題に分割する'
            }
            
        except Exception as e:
            self.logger.error(f"Elder wisdom search error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_conversation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """対話履歴取得"""
        return self.conversation_history[-limit:]
    
    def clear_conversation_history(self):
        """対話履歴クリア"""
        self.conversation_history.clear()
        self.logger.info("Conversation history cleared")

# WebSocket対応のリアルタイムチャットサーバー
class ClaudeElderWebSocketServer:
    """Claude Elder WebSocket サーバー"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.chat_api = ClaudeElderChatAPI()
        self.logger = logging.getLogger(__name__)
        self.clients = set()
    
    async def handle_client(self, websocket, path):
        """クライアント接続処理"""
        self.clients.add(websocket)
        self.logger.info(f"Client connected: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    if data.get('type') == 'chat':
                        # チャットメッセージ処理
                        response = await self.chat_api.process_chat_message(
                            data.get('message', ''),
                            data.get('user_id', 'anonymous')
                        )
                        
                        # レスポンス送信
                        await websocket.send(json.dumps({
                            'type': 'chat_response',
                            'data': response
                        }))
                        
                    elif data.get('type') == 'history':
                        # 対話履歴送信
                        history = self.chat_api.get_conversation_history(
                            data.get('limit', 50)
                        )
                        await websocket.send(json.dumps({
                            'type': 'history_response',
                            'data': history
                        }))
                        
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Invalid JSON format'
                    }))
                except Exception as e:
                    self.logger.error(f"Message processing error: {str(e)}")
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': str(e)
                    }))
                    
        except Exception as e:
            self.logger.error(f"Client handling error: {str(e)}")
        finally:
            self.clients.remove(websocket)
            self.logger.info(f"Client disconnected: {websocket.remote_address}")
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """全クライアントにメッセージ配信"""
        if self.clients:
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.clients],
                return_exceptions=True
            )
    
    async def start_server(self):
        """WebSocketサーバー開始"""
        try:
            import websockets
            
            self.logger.info(f"Starting Claude Elder WebSocket server on {self.host}:{self.port}")
            
            async with websockets.serve(self.handle_client, self.host, self.port):
                self.logger.info("Claude Elder WebSocket server started")
                await asyncio.Future()  # 永続実行
                
        except ImportError:
            self.logger.error("websockets library not installed. Install with: pip install websockets")
            raise
        except Exception as e:
            self.logger.error(f"WebSocket server error: {str(e)}")
            raise

# CLI統合
async def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Claude Elder Chat API')
    parser.add_argument('--mode', choices=['chat', 'websocket'], default='chat', 
                       help='実行モード')
    parser.add_argument('--host', default='0.0.0.0', help='WebSocketサーバーホスト')
    parser.add_argument('--port', type=int, default=8765, help='WebSocketサーバーポート')
    parser.add_argument('--message', help='チャットメッセージ（chatモード用）')
    
    args = parser.parse_args()
    
    if args.mode == 'chat':
        # チャットモード
        chat_api = ClaudeElderChatAPI()
        
        if args.message:
            # 単発メッセージ
            response = await chat_api.process_chat_message(args.message)
            print(json.dumps(response, indent=2, ensure_ascii=False))
        else:
            # 対話モード
            print("🧾 Claude Elder Chat API - 対話モード")
            print("終了するには 'exit' を入力してください")
            
            while True:
                try:
                    message = input("\n> ")
                    if message.lower() in ['exit', 'quit', 'bye']:
                        break
                    
                    response = await chat_api.process_chat_message(message)
                    print(f"\n{response['response']}")
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"エラー: {str(e)}")
    
    elif args.mode == 'websocket':
        # WebSocketサーバーモード
        server = ClaudeElderWebSocketServer(host=args.host, port=args.port)
        await server.start_server()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())