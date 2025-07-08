#!/usr/bin/env python3
"""
知的PM Worker - 内容判断してAIコマンド実行
BaseWorker版（シンプル）
"""

import json
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.base_worker import BaseWorker
from libs.env_config import get_config
import requests

# 絵文字定義
EMOJI = {
    'brain': '🧠',
    'success': '✅',
    'error': '❌',
    'analyze': '📊',
    'command': '⚡',
    'decision': '🎯'
}

class IntelligentPMWorkerSimple(BaseWorker):
    """知的PM Worker - 内容分析→AIコマンド選択→実行指示（シンプル版）"""
    
    def __init__(self, worker_id=None):
        super().__init__(worker_type='pm', worker_id=worker_id)
        
        # キュー設定をオーバーライド
        self.input_queue = 'ai_pm'
        self.output_queue = 'ai_results'
        
        self.config = get_config()
        
        # AI コマンド定義
        self.ai_commands = {
            'code_generation': {
                'patterns': ['コード', 'code', '実装', 'implement', '作成', 'create', 'function', '関数'],
                'description': 'コード生成・実装'
            },
            'project_management': {
                'patterns': ['プロジェクト', 'project', '管理', 'manage', 'タスク', 'task', '計画', 'plan'],
                'description': 'プロジェクト管理'
            },
            'documentation': {
                'patterns': ['ドキュメント', 'document', 'README', 'docs', '説明', 'explain'],
                'description': 'ドキュメント生成'
            },
            'general_conversation': {
                'patterns': ['こんにちは', 'hello', 'やっと', 'こんばんは', '会話', 'conversation'],
                'description': '一般的な会話'
            }
        }
        
        self.logger.info(f"{EMOJI['brain']} IntelligentPMWorker initialized")

    def process_message(self, ch, method, properties, body):
        """PMメッセージ処理 - 知的判断とAIコマンド実行"""
        try:
            # メッセージをパース
            message = json.loads(body.decode('utf-8'))
            task_id = message.get('task_id', 'unknown')
            output = message.get('output', '')
            original_prompt = message.get('original_prompt', '')
            task_type = message.get('task_type', 'general')
            is_slack_task = message.get('is_slack_task', False)
            status = message.get('status', 'completed')
            error = message.get('error', None)
            needs_pm_fallback = message.get('needs_pm_fallback', False)
            
            self.logger.info(f"{EMOJI['brain']} PM知的判断開始: {task_id}")
            
            # 1. 失敗時の代替処理チェック
            if status == 'failed' or needs_pm_fallback:
                self.logger.info(f"{EMOJI['brain']} TaskWorker失敗 - PM代替処理開始")
                final_result = self._generate_pm_fallback_response(original_prompt, error)
                analysis = {'fallback_mode': True, 'language': 'japanese' if any(ord(char) > 127 for char in original_prompt) else 'english'}
            else:
                # 1. 内容分析
                analysis = self._analyze_content(original_prompt, output)
                
                # 2. PM判断と応答生成
                final_result = self._pm_intelligent_response(analysis, original_prompt)
            
            # 3. Slack応答（Slackタスクの場合）
            if is_slack_task:
                self._send_slack_response(task_id, final_result, analysis)
            
            # 4. 結果送信（次のワーカーへ）
            self.send_result({
                'task_id': task_id,
                'status': 'pm_completed',
                'pm_analysis': analysis,
                'final_output': final_result,
                'processed_at': datetime.utcnow().isoformat(),
                'worker': 'intelligent_pm_worker'
            })
            
            self.logger.info(f"{EMOJI['success']} PM処理完了: {task_id}")
            
        except Exception as e:
            self.logger.error(f"{EMOJI['error']} PM処理エラー: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _analyze_content(self, prompt: str, claude_output: str) -> Dict[str, Any]:
        """内容分析 - ユーザー要求とClaude応答を分析"""
        
        # 日本語判定
        has_japanese = any(ord(char) > 127 for char in prompt)
        
        # ユーザー意図の分類
        user_intent = self._classify_user_intent(prompt)
        
        # Claude応答の分析
        response_quality = self._analyze_claude_response(claude_output)
        
        # 複雑度評価
        complexity = self._assess_complexity(prompt)
        
        analysis = {
            'user_intent': user_intent,
            'language': 'japanese' if has_japanese else 'english',
            'complexity': complexity,
            'response_quality': response_quality,
            'needs_enhancement': self._needs_pm_enhancement(prompt, claude_output, user_intent),
            'original_prompt': prompt,
            'claude_output': claude_output
        }
        
        self.logger.info(f"{EMOJI['analyze']} 分析結果: {user_intent} | 言語: {analysis['language']} | 複雑度: {complexity}")
        return analysis
    
    def _classify_user_intent(self, prompt: str) -> str:
        """ユーザー意図の分類"""
        prompt_lower = prompt.lower()
        
        for intent, config in self.ai_commands.items():
            if any(pattern in prompt_lower for pattern in config['patterns']):
                return intent
        
        return 'general_conversation'
    
    def _analyze_claude_response(self, output: str) -> Dict[str, Any]:
        """Claude応答の品質分析"""
        return {
            'has_code': '```' in output,
            'has_explanation': len(output.split('.')) > 3,
            'is_question': '?' in output or '？' in output,
            'word_count': len(output.split()),
            'appears_complete': len(output) > 50 and not output.endswith('...'),
            'is_helpful': len(output.split()) > 20
        }
    
    def _assess_complexity(self, prompt: str) -> str:
        """タスク複雑度評価"""
        complexity_indicators = {
            'high': ['システム', 'アーキテクチャ', 'プロジェクト全体', 'complex', 'system', 'architecture'],
            'medium': ['機能', 'feature', 'モジュール', 'module', 'クラス', 'class'],
            'low': ['関数', 'function', 'メソッド', 'method', '変数', 'variable', 'こんにちは', 'hello']
        }
        
        prompt_lower = prompt.lower()
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in prompt_lower for indicator in indicators):
                return level
        
        return 'medium'
    
    def _needs_pm_enhancement(self, prompt: str, claude_output: str, user_intent: str) -> bool:
        """PM強化が必要かどうかの判定"""
        
        # 基本的な挨拶は強化不要
        if user_intent == 'general_conversation' and any(word in prompt.lower() for word in ['こんにちは', 'hello', 'やっと', 'こんばんは']):
            return False
        
        # コード要求だがコードが含まれていない
        if user_intent == 'code_generation' and '```' not in claude_output:
            return True
        
        # プロジェクト管理要求で具体的な提案がない
        if user_intent == 'project_management' and len(claude_output.split()) < 100:
            return True
        
        # 質問で終わっている（不完全な応答）
        if claude_output.strip().endswith('?') or claude_output.strip().endswith('？'):
            return True
        
        # 短すぎる応答
        if len(claude_output.split()) < 30:
            return True
        
        return False
    
    def _pm_intelligent_response(self, analysis: Dict[str, Any], original_prompt: str) -> str:
        """PM知的応答生成"""
        
        user_intent = analysis['user_intent']
        language = analysis['language']
        claude_output = analysis['claude_output']
        needs_enhancement = analysis['needs_enhancement']
        
        # PM強化が不要な場合は元の応答を返す
        if not needs_enhancement:
            self.logger.info(f"{EMOJI['decision']} PM判定: 元応答で十分")
            return claude_output
        
        # PM強化応答を生成
        enhanced_response = self._generate_pm_enhanced_response(analysis, original_prompt)
        
        self.logger.info(f"{EMOJI['decision']} PM判定: 強化応答生成")
        return enhanced_response
    
    def _generate_pm_enhanced_response(self, analysis: Dict[str, Any], original_prompt: str) -> str:
        """PM強化応答生成"""
        
        user_intent = analysis['user_intent']
        language = analysis['language']
        complexity = analysis['complexity']
        
        if language == 'japanese':
            return self._generate_japanese_pm_response(user_intent, complexity, original_prompt)
        else:
            return self._generate_english_pm_response(user_intent, complexity, original_prompt)
    
    def _generate_japanese_pm_response(self, user_intent: str, complexity: str, prompt: str) -> str:
        """日本語PM応答生成"""
        
        # シンプルで実用的な応答形式
        base_response = ""
        
        if user_intent == 'code_generation':
            return f"コード生成が必要ですね。具体的な実装内容を教えてください。\n\n利用可能なコマンド:\n• ai-send: 一般コード生成\n• ai-tdd: テスト駆動開発"
        
        elif user_intent == 'general':
            return f"了解しました。お手伝いできることがあれば教えてください。"
        
        else:
            return f"承知いたしました。詳細をお聞かせください。"
    
    def _generate_english_pm_response(self, user_intent: str, complexity: str, prompt: str) -> str:
        """English PM response generation"""
        if user_intent == 'code_generation':
            return f"I can help with code generation. Please provide specific implementation details.\n\nAvailable commands:\n• ai-send: General code generation\n• ai-tdd: Test-driven development"
        elif user_intent == 'general':
            return f"Understood. How can I assist you?"
        else:
            return f"Got it. Please provide more details."
    
    def _generate_pm_fallback_response(self, prompt: str, error: str) -> str:
        """Generate fallback response when TaskWorker fails"""
        if any(ord(char) > 127 for char in prompt):
            return f"申し訳ございません。一時的な問題が発生しました。もう一度お試しください。"
        else:
            return f"Sorry, there was a temporary issue. Please try again."
    
    def _send_slack_response(self, task_id: str, response: str, analysis: Dict[str, Any]):
        """Slack応答送信"""
        try:
            bot_token = getattr(self.config, 'SLACK_BOT_TOKEN', None)
            channel_id = getattr(self.config, 'SLACK_POLLING_CHANNEL_ID', 'C0946R76UU8')
            
            if not bot_token:
                self.logger.warning("Slack bot token not found")
                return
            
            url = "https://slack.com/api/chat.postMessage"
            headers = {
                "Authorization": f"Bearer {bot_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "channel": channel_id,
                "text": response,
                "username": "PM-AI"
            }
            
            response_obj = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response_obj.status_code == 200:
                result = response_obj.json()
                if result.get('ok'):
                    self.logger.info(f"✅ PM-Slack応答送信成功: {task_id}")
                else:
                    self.logger.error(f"❌ Slack API error: {result.get('error', 'Unknown')}")
            else:
                self.logger.error(f"❌ HTTP error {response_obj.status_code}")
                
        except Exception as e:
            self.logger.error(f"❌ Slack応答送信エラー: {str(e)}")

    def initialize(self) -> None:
        """ワーカーの初期化処理"""
        # TODO: 初期化ロジックを実装してください
        logger.info(f"{self.__class__.__name__} initialized")
        pass

    def handle_error(self):
        """TODO: handle_errorメソッドを実装してください"""
        pass

    def get_status(self):
        """TODO: get_statusメソッドを実装してください"""
        pass

    def validate_config(self):
        """TODO: validate_configメソッドを実装してください"""
        pass

# File structure cleaned for proper Python syntax


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Intelligent PM Worker Simple")
    parser.add_argument("--worker-id", help="Worker ID", default="intelligent-pm")
    
    args = parser.parse_args()
    
    worker = IntelligentPMWorkerSimple(worker_id=args.worker_id)
    print(f"🧠 Intelligent PM Worker (Simple) starting...")
    print(f"📥 Input queue: {worker.input_queue}")
    print(f"📤 Output queue: {worker.output_queue}")
    
    try:
        worker.start()
    except KeyboardInterrupt:
        print(f"\n❌ Worker stopped by user")

