"""
Claude Client with API Key Rotation
制限検知とフォールバック機能を持つClaude APIクライアント
"""

import logging
import time
from typing import Dict, List, Optional, Any
from anthropic import Anthropic, RateLimitError, APIError
from libs.api_key_manager import APIKeyManager, APIKeyInfo

class ClaudeClientWithRotation:
    """
    APIキーローテーション機能付きClaude APIクライアント
    """
    
    def __init__(self, config_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.api_key_manager = APIKeyManager(config_path)
        self.request_count = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
    def create_message(self, 
                      model: str = "claude-3-5-sonnet-20241022",
                      max_tokens: int = 4096,
                      messages: List[Dict[str, str]] = None,
                      temperature: float = 0.7,
                      **kwargs) -> Dict[str, Any]:
        """
        メッセージを作成（自動リトライ・フォールバック付き）
        """
        if not messages:
            messages = []
        
        max_retries = self.api_key_manager.config.get('max_retries', 3)
        retry_delay = 1
        
        for attempt in range(max_retries + 1):
            try:
                client, key_info = self.api_key_manager.create_client()
                
                self.logger.debug(f"Attempt {attempt + 1} using key {key_info.alias}")
                
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=messages,
                    temperature=temperature,
                    **kwargs
                )
                
                self.successful_requests += 1
                self.request_count += 1
                
                return {
                    'content': response.content[0].text if response.content else "",
                    'usage': {
                        'input_tokens': response.usage.input_tokens,
                        'output_tokens': response.usage.output_tokens,
                        'total_tokens': response.usage.input_tokens + response.usage.output_tokens
                    },
                    'model': response.model,
                    'key_used': key_info.alias,
                    'attempt': attempt + 1
                }
                
            except (RateLimitError, APIError) as e:
                self.failed_requests += 1
                can_retry = self.api_key_manager.handle_api_error(key_info, e)
                
                if not can_retry or attempt == max_retries:
                    self.logger.error(f"Request failed after {attempt + 1} attempts: {e}")
                    raise e
                
                self.logger.warning(f"Retrying request (attempt {attempt + 1}/{max_retries}) due to: {e}")
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数バックオフ
                
            except Exception as e:
                self.failed_requests += 1
                self.logger.error(f"Unexpected error: {e}")
                raise e
        
        raise Exception("Maximum retries exceeded")
    
    def stream_message(self, 
                      model: str = "claude-3-5-sonnet-20241022",
                      max_tokens: int = 4096,
                      messages: List[Dict[str, str]] = None,
                      temperature: float = 0.7,
                      **kwargs):
        """
        ストリーミングメッセージ作成（自動リトライ・フォールバック付き）
        """
        if not messages:
            messages = []
        
        max_retries = self.api_key_manager.config.get('max_retries', 3)
        retry_delay = 1
        
        for attempt in range(max_retries + 1):
            try:
                client, key_info = self.api_key_manager.create_client()
                
                self.logger.debug(f"Stream attempt {attempt + 1} using key {key_info.alias}")
                
                with client.messages.stream(
                    model=model,
                    max_tokens=max_tokens,
                    messages=messages,
                    temperature=temperature,
                    **kwargs
                ) as stream:
                    for text in stream.text_stream:
                        yield text
                
                self.successful_requests += 1
                self.request_count += 1
                return
                
            except (RateLimitError, APIError) as e:
                self.failed_requests += 1
                can_retry = self.api_key_manager.handle_api_error(key_info, e)
                
                if not can_retry or attempt == max_retries:
                    self.logger.error(f"Stream request failed after {attempt + 1} attempts: {e}")
                    raise e
                
                self.logger.warning(f"Retrying stream request (attempt {attempt + 1}/{max_retries}) due to: {e}")
                time.sleep(retry_delay)
                retry_delay *= 2
                
            except Exception as e:
                self.failed_requests += 1
                self.logger.error(f"Unexpected stream error: {e}")
                raise e
        
        raise Exception("Maximum retries exceeded for stream")
    
    def get_client_stats(self) -> Dict[str, Any]:
        """クライアントの統計情報を取得"""
        return {
            'request_count': self.request_count,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': self.successful_requests / max(self.request_count, 1) * 100,
            'api_key_status': self.api_key_manager.get_status()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック実行"""
        return {
            'client_stats': self.get_client_stats(),
            'api_key_health': self.api_key_manager.health_check()
        }
    
    def reset_api_key(self, key_alias: str) -> bool:
        """指定されたAPIキーをリセット"""
        return self.api_key_manager.reset_key_status(key_alias)
    
    def force_key_rotation(self) -> str:
        """強制的にキーローテーションを実行"""
        old_key = self.api_key_manager.get_current_key()
        self.api_key_manager.current_key_index = (self.api_key_manager.current_key_index + 1) % len(self.api_key_manager.api_keys)
        new_key = self.api_key_manager.get_current_key()
        
        self.logger.info(f"Forced rotation from {old_key.alias} to {new_key.alias}")
        return new_key.alias

# 便利関数
def create_claude_client(config_path: str = None) -> ClaudeClientWithRotation:
    """Claude Client with Rotationのインスタンスを作成"""
    return ClaudeClientWithRotation(config_path)

def test_api_keys(config_path: str = None) -> Dict[str, Any]:
    """全APIキーのテストを実行"""
    client = ClaudeClientWithRotation(config_path)
    
    test_message = [{"role": "user", "content": "Hello, this is a test message."}]
    
    results = {
        'total_keys': len(client.api_key_manager.api_keys),
        'test_results': {},
        'summary': {
            'working_keys': 0,
            'failed_keys': 0,
            'rate_limited_keys': 0
        }
    }
    
    for key in client.api_key_manager.api_keys:
        try:
            # 各キーで個別にテスト
            test_client = Anthropic(api_key=key.key)
            response = test_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                messages=test_message
            )
            
            results['test_results'][key.alias] = {
                'status': 'working',
                'response_length': len(response.content[0].text) if response.content else 0,
                'tokens_used': response.usage.input_tokens + response.usage.output_tokens
            }
            results['summary']['working_keys'] += 1
            
        except RateLimitError:
            results['test_results'][key.alias] = {
                'status': 'rate_limited',
                'error': 'Rate limit exceeded'
            }
            results['summary']['rate_limited_keys'] += 1
            
        except Exception as e:
            results['test_results'][key.alias] = {
                'status': 'failed',
                'error': str(e)
            }
            results['summary']['failed_keys'] += 1
    
    return results