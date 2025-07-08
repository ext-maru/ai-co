"""
API Key Rotation Manager
複数のAPIキーを管理し、レート制限時の自動切り替えを行う
"""

import os
import time
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import random
from anthropic import Anthropic, RateLimitError, APIError

class RotationStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    RATE_LIMIT_AWARE = "rate_limit_aware"
    RANDOM = "random"

class APIKeyStatus(Enum):
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    COOLDOWN = "cooldown"

class APIKeyInfo:
    def __init__(self, key: str, alias: str):
        self.key = key
        self.alias = alias
        self.status = APIKeyStatus.ACTIVE
        self.last_used = None
        self.last_error = None
        self.rate_limit_reset = None
        self.requests_count = 0
        self.error_count = 0
        self.cooldown_until = None
        
    def is_available(self) -> bool:
        """APIキーが使用可能かチェック"""
        if self.status == APIKeyStatus.COOLDOWN:
            if self.cooldown_until and datetime.now() > self.cooldown_until:
                self.status = APIKeyStatus.ACTIVE
                self.cooldown_until = None
                return True
            return False
        return self.status == APIKeyStatus.ACTIVE
        
    def set_rate_limited(self, reset_time: Optional[datetime] = None):
        """レート制限状態に設定"""
        self.status = APIKeyStatus.RATE_LIMITED
        self.rate_limit_reset = reset_time or datetime.now() + timedelta(minutes=60)
        
    def set_error(self, error_msg: str):
        """エラー状態に設定"""
        self.status = APIKeyStatus.ERROR
        self.last_error = error_msg
        self.error_count += 1
        
    def set_cooldown(self, minutes: int):
        """クールダウン状態に設定"""
        self.status = APIKeyStatus.COOLDOWN
        self.cooldown_until = datetime.now() + timedelta(minutes=minutes)

class APIKeyManager:
    def __init__(self, config_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.api_keys = self._load_api_keys()
        self.current_key_index = 0
        self.last_rotation_time = datetime.now()
        
    def _load_config(self, config_path: str) -> Dict:
        """設定ファイルを読み込み"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('claude', {}).get('api_key_rotation', {})
        
        # デフォルト設定
        return {
            'enabled': os.getenv('API_KEY_ROTATION_ENABLED', 'true').lower() == 'true',
            'strategy': os.getenv('API_KEY_ROTATION_STRATEGY', 'rate_limit_aware'),
            'cooldown_minutes': int(os.getenv('API_KEY_COOLDOWN_MINUTES', '60')),
            'max_retries': int(os.getenv('API_KEY_MAX_RETRIES', '3')),
            'health_check_interval': 30
        }
    
    def _load_api_keys(self) -> List[APIKeyInfo]:
        """環境変数からAPIキーを読み込み"""
        keys = []
        
        # プライマリキー
        primary_key = os.getenv('ANTHROPIC_API_KEY')
        if primary_key:
            keys.append(APIKeyInfo(primary_key, 'primary'))
        
        # 追加のキー (ANTHROPIC_API_KEY_1, ANTHROPIC_API_KEY_2, ...)
        for i in range(1, 10):  # 最大9個まで
            key = os.getenv(f'ANTHROPIC_API_KEY_{i}')
            if key:
                keys.append(APIKeyInfo(key, f'key_{i}'))
        
        if not keys:
            raise ValueError("No API keys found in environment variables")
        
        self.logger.info(f"Loaded {len(keys)} API keys")
        return keys
    
    def get_current_key(self) -> APIKeyInfo:
        """現在のAPIキーを取得"""
        if not self.config.get('enabled', False):
            return self.api_keys[0]  # ローテーション無効時は最初のキーを使用
        
        strategy = RotationStrategy(self.config.get('strategy', 'rate_limit_aware'))
        
        if strategy == RotationStrategy.ROUND_ROBIN:
            return self._get_round_robin_key()
        elif strategy == RotationStrategy.RATE_LIMIT_AWARE:
            return self._get_rate_limit_aware_key()
        elif strategy == RotationStrategy.RANDOM:
            return self._get_random_key()
        
        return self.api_keys[0]
    
    def _get_round_robin_key(self) -> APIKeyInfo:
        """ラウンドロビン方式でキーを選択"""
        attempts = 0
        while attempts < len(self.api_keys):
            key = self.api_keys[self.current_key_index]
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            
            if key.is_available():
                return key
            attempts += 1
        
        # 全てのキーが使用不可の場合は最初のキーを返す
        return self.api_keys[0]
    
    def _get_rate_limit_aware_key(self) -> APIKeyInfo:
        """レート制限を考慮してキーを選択"""
        available_keys = [key for key in self.api_keys if key.is_available()]
        
        if not available_keys:
            # 使用可能なキーがない場合は最も早くリセットされるキーを選択
            return min(self.api_keys, key=lambda k: k.rate_limit_reset or datetime.now())
        
        # エラー数が最も少ないキーを選択
        return min(available_keys, key=lambda k: k.error_count)
    
    def _get_random_key(self) -> APIKeyInfo:
        """ランダムにキーを選択"""
        available_keys = [key for key in self.api_keys if key.is_available()]
        
        if not available_keys:
            return self.api_keys[0]
        
        return random.choice(available_keys)
    
    def create_client(self) -> Tuple[Anthropic, APIKeyInfo]:
        """Anthropicクライアントを作成"""
        key_info = self.get_current_key()
        client = Anthropic(api_key=key_info.key)
        key_info.last_used = datetime.now()
        key_info.requests_count += 1
        
        return client, key_info
    
    def handle_api_error(self, key_info: APIKeyInfo, error: Exception) -> bool:
        """APIエラーを処理し、キーのステータスを更新"""
        if isinstance(error, RateLimitError):
            self.logger.warning(f"Rate limit hit for key {key_info.alias}")
            key_info.set_rate_limited()
            return True  # 他のキーで再試行可能
        
        elif isinstance(error, APIError):
            self.logger.error(f"API error for key {key_info.alias}: {error}")
            key_info.set_error(str(error))
            
            # 認証エラーの場合はクールダウン
            if "authentication" in str(error).lower():
                key_info.set_cooldown(self.config.get('cooldown_minutes', 60))
            
            return True  # 他のキーで再試行可能
        
        else:
            self.logger.error(f"Unexpected error for key {key_info.alias}: {error}")
            return False  # 再試行不可
    
    def get_status(self) -> Dict:
        """全APIキーのステータスを取得"""
        return {
            'total_keys': len(self.api_keys),
            'active_keys': len([k for k in self.api_keys if k.is_available()]),
            'rotation_enabled': self.config.get('enabled', False),
            'strategy': self.config.get('strategy', 'rate_limit_aware'),
            'keys': [
                {
                    'alias': key.alias,
                    'status': key.status.value,
                    'last_used': key.last_used.isoformat() if key.last_used else None,
                    'requests_count': key.requests_count,
                    'error_count': key.error_count,
                    'rate_limit_reset': key.rate_limit_reset.isoformat() if key.rate_limit_reset else None,
                    'cooldown_until': key.cooldown_until.isoformat() if key.cooldown_until else None
                }
                for key in self.api_keys
            ]
        }
    
    def reset_key_status(self, key_alias: str) -> bool:
        """指定されたキーのステータスをリセット"""
        for key in self.api_keys:
            if key.alias == key_alias:
                key.status = APIKeyStatus.ACTIVE
                key.last_error = None
                key.rate_limit_reset = None
                key.cooldown_until = None
                self.logger.info(f"Reset status for key {key_alias}")
                return True
        return False
    
    def health_check(self) -> Dict:
        """全APIキーのヘルスチェック"""
        results = {}
        
        for key in self.api_keys:
            try:
                client = Anthropic(api_key=key.key)
                # 軽量なリクエストでテスト
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "test"}]
                )
                results[key.alias] = {
                    'status': 'healthy',
                    'response_time': 0,  # 実際の実装では時間を測定
                    'last_check': datetime.now().isoformat()
                }
                key.status = APIKeyStatus.ACTIVE
                
            except Exception as e:
                results[key.alias] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'last_check': datetime.now().isoformat()
                }
                self.handle_api_error(key, e)
        
        return results