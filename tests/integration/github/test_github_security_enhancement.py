#!/usr/bin/env python3
"""
🛡️ GitHub Security Enhancement Tests
包括的セキュリティ強化システムテスト

Created: 2025-07-17
Author: Claude Elder
Version: 1.0.0 - Iron Will Testing Standards
Target: 95%+ Test Coverage
"""

import unittest
import asyncio
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys

# テスト対象モジュール
sys.path.insert(0, str(Path(__file__).parent.parent))
from libs.github_security_enhancement import (
    GitHubSecurityEnhancement,
    SecurityConfiguration,
    SecurityThreatLevel,
    SecurityEventType,
    CryptographicService,
    AuthenticationService,
    InputValidationService,
    SecurityMonitoringService,
    NetworkSecurityService,
    VulnerabilityManagementService
)

from libs.secure_github_flow_manager import (
    SecureGitHubFlowManager,
    SecureGitHubContext,
    SecurityError
)


class TestSecurityConfiguration(unittest.TestCase):
    """セキュリティ設定テスト"""
    
    def test_default_configuration(self):
        """デフォルト設定テスト"""
        config = SecurityConfiguration()
        
        self.assertEqual(config.token_expiry_minutes, 60)
        self.assertTrue(config.mfa_enabled)
        self.assertEqual(config.max_login_attempts, 5)
        self.assertEqual(config.encryption_algorithm, "AES-256-GCM")
        self.assertEqual(config.rate_limit_requests_per_minute, 100)
        self.assertTrue(config.real_time_monitoring)
    
    def test_custom_configuration(self):
        """カスタム設定テスト"""
        config = SecurityConfiguration(
            token_expiry_minutes=120,
            mfa_enabled=False,
            rate_limit_requests_per_minute=200,
            encryption_algorithm="AES-128-CBC"
        )
        
        self.assertEqual(config.token_expiry_minutes, 120)
        self.assertFalse(config.mfa_enabled)
        self.assertEqual(config.rate_limit_requests_per_minute, 200)
        self.assertEqual(config.encryption_algorithm, "AES-128-CBC")


class TestCryptographicService(unittest.TestCase):
    """暗号化サービステスト"""
    
    def setUp(self):
        """テスト前処理"""
        self.config = SecurityConfiguration()
        self.crypto_service = CryptographicService(self.config)
    
    def test_encrypt_decrypt_string(self):
        """文字列暗号化・復号化テスト"""
        original_data = "test_secret_data"
        context = "test_context"
        
        # 暗号化
        encrypted = self.crypto_service.encrypt_data(original_data, context)
        
        self.assertIn('encrypted_data', encrypted)
        self.assertIn('algorithm', encrypted)
        self.assertIn('context', encrypted)
        self.assertEqual(encrypted['algorithm'], self.config.encryption_algorithm)
        self.assertEqual(encrypted['context'], context)
        
        # 復号化
        decrypted = self.crypto_service.decrypt_data(encrypted, context)
        self.assertEqual(decrypted.decode('utf-8'), original_data)
    
    def test_encrypt_decrypt_dict(self):
        """辞書暗号化・復号化テスト"""
        original_data = {"key": "value", "number": 42}
        context = "test_context"
        
        # 暗号化
        encrypted = self.crypto_service.encrypt_data(original_data, context)
        
        # 復号化
        decrypted = self.crypto_service.decrypt_data(encrypted, context)
        decrypted_dict = json.loads(decrypted.decode('utf-8'))
        
        self.assertEqual(decrypted_dict, original_data)
    
    def test_generate_secure_token(self):
        """セキュアトークン生成テスト"""
        token1 = self.crypto_service.generate_secure_token()
        token2 = self.crypto_service.generate_secure_token()
        
        self.assertNotEqual(token1, token2)
        self.assertIsInstance(token1, str)
        self.assertIsInstance(token2, str)
        self.assertGreater(len(token1), 0)
        self.assertGreater(len(token2), 0)
    
    def test_signature_verification(self):
        """署名検証テスト"""
        data = b"test_data"
        secret = "test_secret"
        
        # 署名作成
        signature = self.crypto_service.create_signature(data, secret)
        
        # 署名検証
        self.assertTrue(self.crypto_service.verify_signature(data, signature, secret))
        
        # 間違った署名
        wrong_signature = "wrong_signature"
        self.assertFalse(self.crypto_service.verify_signature(data, wrong_signature, secret))
        
        # 間違ったデータ
        wrong_data = b"wrong_data"
        self.assertFalse(self.crypto_service.verify_signature(wrong_data, signature, secret))


class TestInputValidationService(unittest.TestCase):
    """入力検証サービステスト"""
    
    def setUp(self):
        """テスト前処理"""
        self.config = SecurityConfiguration()
        self.validation_service = InputValidationService(self.config)
    
    def test_validate_safe_string(self):
        """安全な文字列検証テスト"""
        safe_string = "safe_test_string"
        
        result = self.validation_service.validate_input(safe_string, "general")
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['sanitized_data'], safe_string)
        self.assertEqual(len(result['errors']), 0)
    
    def test_validate_dangerous_string(self):
        """危険な文字列検証テスト"""
        dangerous_strings = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "eval('malicious_code')",
            "../../../etc/passwd",
            "javascript:alert('xss')"
        ]
        
        for dangerous_string in dangerous_strings:
            result = self.validation_service.validate_input(dangerous_string, "general")
            
            self.assertFalse(result['valid'])
            self.assertGreater(len(result['errors']), 0)
    
    def test_validate_github_patterns(self):
        """GitHubパターン検証テスト"""
        # 有効なリポジトリ名
        valid_repo = "user/repository"
        result = self.validation_service.validate_input(valid_repo, "repository")
        self.assertTrue(result['valid'])
        
        # 無効なリポジトリ名
        invalid_repo = "user/../repository"
        result = self.validation_service.validate_input(invalid_repo, "repository")
        self.assertFalse(result['valid'])
        
        # 有効なブランチ名
        valid_branch = "feature/new-feature"
        result = self.validation_service.validate_input(valid_branch, "branch")
        self.assertTrue(result['valid'])
        
        # 有効なコミットSHA
        valid_commit = "a1b2c3d4e5f6789012345678901234567890abcd"
        result = self.validation_service.validate_input(valid_commit, "commit_sha")
        self.assertTrue(result['valid'])
    
    def test_validate_long_input(self):
        """長い入力検証テスト"""
        long_string = "a" * 20000  # 10000文字制限を超える
        
        result = self.validation_service.validate_input(long_string, "general")
        
        self.assertFalse(result['valid'])
        self.assertIn("Input too long", str(result['errors']))
    
    def test_validate_dict_input(self):
        """辞書入力検証テスト"""
        safe_dict = {"key": "value", "number": 42}
        
        result = self.validation_service.validate_input(safe_dict, "general")
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['sanitized_data'], safe_dict)
    
    def test_validate_nested_dict(self):
        """ネストした辞書検証テスト"""
        # 深すぎるネスト
        deep_dict = {"level1": {"level2": {"level3": {"level4": {}}}}}
        for i in range(15):  # 10レベル制限を超える
            deep_dict = {"level": deep_dict}
        
        result = self.validation_service.validate_input(deep_dict, "general")
        
        self.assertFalse(result['valid'])
        self.assertIn("nesting too deep", str(result['errors']))


class TestSecurityMonitoringService(unittest.IsolatedAsyncioTestCase):
    """セキュリティ監視サービステスト"""
    
    async def asyncSetUp(self):
        """テスト前処理"""
        self.config = SecurityConfiguration()
        self.monitoring_service = SecurityMonitoringService(self.config)
    
    async def test_log_security_event(self):
        """セキュリティイベントログテスト"""
        await self.monitoring_service.log_security_event(
            SecurityEventType.AUTHENTICATION,
            {
                'user_id': 'test_user',
                'result': 'success',
                'source_ip': '127.0.0.1'
            },
            SecurityThreatLevel.LOW
        )
        
        self.assertEqual(len(self.monitoring_service.audit_events), 1)
        
        event = self.monitoring_service.audit_events[0]
        self.assertEqual(event.event_type, SecurityEventType.AUTHENTICATION)
        self.assertEqual(event.threat_level, SecurityThreatLevel.LOW)
        self.assertEqual(event.user_id, 'test_user')
        self.assertEqual(event.source_ip, '127.0.0.1')
    
    async def test_high_threat_event_handling(self):
        """高脅威イベント処理テスト"""
        await self.monitoring_service.log_security_event(
            SecurityEventType.SECURITY_BREACH,
            {
                'user_id': 'attacker',
                'attack_type': 'brute_force',
                'source_ip': '10.0.0.1'
            },
            SecurityThreatLevel.CRITICAL
        )
        
        # インシデントが作成されることを確認
        self.assertGreater(len(self.monitoring_service.active_incidents), 0)
        
        incident = list(self.monitoring_service.active_incidents.values())[0]
        self.assertEqual(incident['severity'], 'CRITICAL')
        self.assertEqual(incident['status'], 'active')
    
    async def test_get_security_metrics(self):
        """セキュリティメトリクス取得テスト"""
        # いくつかのイベントをログ
        await self.monitoring_service.log_security_event(
            SecurityEventType.AUTHENTICATION,
            {'user_id': 'user1'},
            SecurityThreatLevel.LOW
        )
        await self.monitoring_service.log_security_event(
            SecurityEventType.AUTHORIZATION,
            {'user_id': 'user2'},
            SecurityThreatLevel.MEDIUM
        )
        
        metrics = self.monitoring_service.get_security_metrics()
        
        self.assertIn('total_events_24h', metrics)
        self.assertIn('threat_level_distribution', metrics)
        self.assertIn('event_type_distribution', metrics)
        self.assertEqual(metrics['total_events_24h'], 2)


class TestNetworkSecurityService(unittest.TestCase):
    """ネットワークセキュリティサービステスト"""
    
    def setUp(self):
        """テスト前処理"""
        self.config = SecurityConfiguration()
        self.config.allowed_ip_ranges = ['127.0.0.0/8', '192.168.0.0/16']
        self.config.blocked_ip_ranges = ['10.0.0.0/8']
        self.network_service = NetworkSecurityService(self.config)
    
    def test_validate_allowed_ip(self):
        """許可IP検証テスト"""
        result = self.network_service.validate_request_source('127.0.0.1', 'TestAgent/1.0')
        
        self.assertTrue(result['allowed'])
        self.assertIsNone(result['reason'])
    
    def test_validate_blocked_ip(self):
        """ブロックIP検証テスト"""
        result = self.network_service.validate_request_source('10.0.0.1', 'TestAgent/1.0')
        
        self.assertFalse(result['allowed'])
        self.assertIn('not in allowed ranges', result['reason'])
    
    def test_validate_invalid_ip(self):
        """無効IP検証テスト"""
        result = self.network_service.validate_request_source('invalid_ip', 'TestAgent/1.0')
        
        self.assertFalse(result['allowed'])
        self.assertIn('Invalid IP address', result['reason'])
    
    def test_validate_suspicious_user_agent(self):
        """疑わしいUser-Agent検証テスト"""
        suspicious_agents = [
            'curl/7.68.0',
            'python-requests/2.25.1',
            'Nikto/2.1.6',
            'sqlmap/1.5.2'
        ]
        
        for agent in suspicious_agents:
            result = self.network_service.validate_request_source('127.0.0.1', agent)
            
            self.assertFalse(result['allowed'])
            self.assertIn('Suspicious user agent', result['reason'])
    
    def test_rate_limiting(self):
        """レート制限テスト"""
        ip = '127.0.0.1'
        
        # 許可された回数まで
        for _ in range(self.config.rate_limit_requests_per_minute - 1):
            result = self.network_service.validate_request_source(ip, 'TestAgent/1.0')
            self.assertTrue(result['allowed'])
        
        # 制限を超える
        result = self.network_service.validate_request_source(ip, 'TestAgent/1.0')
        self.assertFalse(result['allowed'])
        self.assertIn('Rate limit exceeded', result['reason'])
    
    def test_ip_blocking(self):
        """IPブロック機能テスト"""
        ip = '192.168.1.100'
        
        # 最初は許可
        result = self.network_service.validate_request_source(ip, 'TestAgent/1.0')
        self.assertTrue(result['allowed'])
        
        # IPをブロック
        self.network_service.block_ip(ip, "Test block")
        
        # ブロック後は拒否
        result = self.network_service.validate_request_source(ip, 'TestAgent/1.0')
        self.assertFalse(result['allowed'])
        self.assertIn('IP address is blocked', result['reason'])
        
        # ブロック解除
        self.network_service.unblock_ip(ip)
        
        # 解除後は許可
        result = self.network_service.validate_request_source(ip, 'TestAgent/1.0')
        self.assertTrue(result['allowed'])


class TestVulnerabilityManagementService(unittest.IsolatedAsyncioTestCase):
    """脆弱性管理サービステスト"""
    
    async def asyncSetUp(self):
        """テスト前処理"""
        self.config = SecurityConfiguration()
        self.vulnerability_service = VulnerabilityManagementService(self.config)
    
    async def test_scan_dependencies(self):
        """依存関係スキャンテスト"""
        # テスト用requirements.txtファイル作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("requests==2.25.1\nflask==1.1.2\npytest==6.2.2\n")
            requirements_file = f.name
        
        try:
            result = await self.vulnerability_service.scan_dependencies(requirements_file)
            
            self.assertIn('scan_id', result)
            self.assertIn('timestamp', result)
            self.assertIn('scan_type', result)
            self.assertIn('vulnerabilities', result)
            self.assertEqual(result['scan_type'], 'dependency_scan')
            
        finally:
            os.unlink(requirements_file)
    
    async def test_scan_code_security(self):
        """コードセキュリティスキャンテスト"""
        # テスト用Pythonファイル作成
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, 'test.py')
            with open(test_file, 'w') as f:
                f.write("""
import os
import subprocess

# 危険なコード例
def dangerous_function():
    eval("print('dangerous')")
    os.system("ls -la")
    subprocess.call(['rm', '-rf', '/tmp/test'])
    
def safe_function():
    print("This is safe")
""")
            
            result = await self.vulnerability_service.scan_code_security(temp_dir)
            
            self.assertIn('scan_id', result)
            self.assertIn('issues', result)
            self.assertGreater(result['issues_found'], 0)
            
            # 危険なパターンが検出されることを確認
            issues = result['issues']
            issue_descriptions = [issue['description'] for issue in issues]
            self.assertIn('Use of eval() function', issue_descriptions)
            self.assertIn('Use of os.system()', issue_descriptions)
    
    def test_get_vulnerability_report(self):
        """脆弱性レポート取得テスト"""
        # スキャン結果を追加
        scan_result = {
            'scan_id': 'test-123',
            'timestamp': datetime.utcnow().isoformat(),
            'scan_type': 'test_scan',
            'vulnerabilities_found': 3,
            'issues_found': 2
        }
        self.vulnerability_service.scan_results.append(scan_result)
        
        report = self.vulnerability_service.get_vulnerability_report()
        
        self.assertEqual(report['total_scans'], 1)
        self.assertEqual(report['total_vulnerabilities'], 5)
        self.assertEqual(report['last_scan'], scan_result['timestamp'])


class TestGitHubSecurityEnhancement(unittest.IsolatedAsyncioTestCase):
    """GitHub セキュリティ強化システムテスト"""
    
    async def asyncSetUp(self):
        """テスト前処理"""
        self.config = SecurityConfiguration()
        self.security_system = GitHubSecurityEnhancement(self.config)
    
    async def test_validate_request(self):
        """リクエスト検証テスト"""
        # 有効なリクエスト
        valid_request = {
            "operation": "authenticate",
            "token": "ghp_test_token_1234567890123456789012345678"
        }
        
        result = await self.security_system.validate_request(valid_request)
        self.assertTrue(result)
        
        # 無効なリクエスト
        invalid_request = {
            "operation": "authenticate"
            # tokenがない
        }
        
        result = await self.security_system.validate_request(invalid_request)
        self.assertFalse(result)
    
    async def test_get_capabilities(self):
        """機能情報取得テスト"""
        capabilities = self.security_system.get_capabilities()
        
        self.assertEqual(capabilities['name'], 'GitHubSecurityEnhancement')
        self.assertEqual(capabilities['version'], '1.0.0')
        self.assertEqual(capabilities['domain'], 'EXECUTION')
        self.assertIn('security_features', capabilities)
        self.assertIn('operations', capabilities)
    
    async def test_input_validation_operation(self):
        """入力検証操作テスト"""
        request = {
            "operation": "validate_input",
            "input_data": "safe_test_string",
            "input_type": "general"
        }
        
        result = await self.security_system.process_request(request)
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('validation_result', result)
        self.assertTrue(result['validation_result']['valid'])
    
    async def test_encryption_operation(self):
        """暗号化操作テスト"""
        # 暗号化
        encrypt_request = {
            "operation": "encrypt_data",
            "data": "secret_message",
            "context": "test_context"
        }
        
        encrypt_result = await self.security_system.process_request(encrypt_request)
        
        self.assertEqual(encrypt_result['status'], 'success')
        self.assertIn('encrypted_data', encrypt_result)
        
        # 復号化
        decrypt_request = {
            "operation": "decrypt_data",
            "data": encrypt_result['encrypted_data'],
            "context": "test_context"
        }
        
        decrypt_result = await self.security_system.process_request(decrypt_request)
        
        self.assertEqual(decrypt_result['status'], 'success')
        self.assertEqual(decrypt_result['decrypted_data'], "secret_message")
    
    async def test_health_check_operation(self):
        """ヘルスチェック操作テスト"""
        request = {"operation": "health_check"}
        
        result = await self.security_system.process_request(request)
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('health_status', result)
        self.assertEqual(result['health_status']['status'], 'healthy')
    
    async def test_security_metrics_operation(self):
        """セキュリティメトリクス操作テスト"""
        request = {"operation": "get_security_metrics"}
        
        result = await self.security_system.process_request(request)
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('metrics', result)
        self.assertIn('system_stats', result['metrics'])
    
    async def test_compliance_check_operation(self):
        """コンプライアンスチェック操作テスト"""
        request = {"operation": "compliance_check"}
        
        result = await self.security_system.process_request(request)
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('compliance_results', result)
        self.assertIn('iron_will_compliance', result['compliance_results'])


class TestSecureGitHubFlowManager(unittest.IsolatedAsyncioTestCase):
    """セキュア GitHub Flow 管理システムテスト"""
    
    async def asyncSetUp(self):
        """テスト前処理"""
        self.security_config = SecurityConfiguration()
        self.manager = SecureGitHubFlowManager(
            repo_path=".",
            security_config=self.security_config
        )
    
    async def test_validate_request(self):
        """リクエスト検証テスト"""
        # 有効なリクエスト
        valid_request = {
            "operation": "authenticate",
            "token": "ghp_test_token_1234567890123456789012345678"
        }
        
        result = await self.manager.validate_request(valid_request)
        self.assertTrue(result)
        
        # 無効なリクエスト
        invalid_request = {
            "operation": "authenticate"
            # tokenがない
        }
        
        result = await self.manager.validate_request(invalid_request)
        self.assertFalse(result)
    
    async def test_get_capabilities(self):
        """機能情報取得テスト"""
        capabilities = self.manager.get_capabilities()
        
        self.assertEqual(capabilities['name'], 'SecureGitHubFlowManager')
        self.assertEqual(capabilities['version'], '1.0.0')
        self.assertEqual(capabilities['domain'], 'EXECUTION')
        self.assertIn('security_features', capabilities)
        self.assertIn('secure_operations', capabilities)
        self.assertIn('integrated_systems', capabilities)
    
    @patch('libs.github_security_enhancement.AuthenticationService.authenticate_token')
    async def test_secure_authentication(self, mock_authenticate):
        """セキュア認証テスト"""
        # モック設定
        mock_authenticate.return_value = {
            'authenticated': True,
            'session_id': 'test-session-123',
            'user_id': 'test-user',
            'scopes': ['repo', 'read:user'],
            'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        request = {
            "operation": "authenticate",
            "token": "ghp_test_token_1234567890123456789012345678",
            "source_ip": "127.0.0.1",
            "user_agent": "TestAgent/1.0"
        }
        
        result = await self.manager.process_request(request)
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('session_id', result)
        self.assertIn('user_id', result)
        self.assertIn('scopes', result)
        self.assertIn('authorized_operations', result)
    
    async def test_health_check(self):
        """ヘルスチェックテスト"""
        request = {"operation": "health_check"}
        
        result = await self.manager.process_request(request)
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('health_status', result)
        self.assertIn('components', result['health_status'])
    
    async def test_security_error_handling(self):
        """セキュリティエラーハンドリングテスト"""
        # 認証なしでセキュアな操作を試行
        request = {
            "operation": "create_branch",
            "branch_name": "test-branch",
            "session_id": "invalid-session"
        }
        
        result = await self.manager.process_request(request)
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error_type'], 'security_error')
        self.assertIn('Security validation failed', result['message'])
    
    def test_secure_github_context(self):
        """セキュアGitHubコンテキストテスト"""
        context = SecureGitHubContext(
            user_id="test-user",
            session_id="test-session",
            github_token="ghp_test_token",
            scopes=["repo", "read:user"]
        )
        
        self.assertEqual(context.user_id, "test-user")
        self.assertEqual(context.session_id, "test-session")
        self.assertEqual(context.github_token, "ghp_test_token")
        self.assertEqual(context.scopes, ["repo", "read:user"])
        self.assertFalse(context.authenticated)
        self.assertEqual(context.authorized_operations, [])


class TestSecurityIntegration(unittest.IsolatedAsyncioTestCase):
    """セキュリティ統合テスト"""
    
    async def asyncSetUp(self):
        """テスト前処理"""
        self.security_config = SecurityConfiguration()
        self.manager = SecureGitHubFlowManager(
            repo_path=".",
            security_config=self.security_config
        )
    
    async def test_end_to_end_security_workflow(self):
        """エンドツーエンドセキュリティワークフローテスト"""
        # 1. ヘルスチェック
        health_result = await self.manager.process_request({
            "operation": "health_check"
        })
        self.assertEqual(health_result['status'], 'success')
        
        # 2. セキュリティメトリクス取得
        metrics_result = await self.manager.process_request({
            "operation": "get_security_metrics"
        })
        self.assertEqual(metrics_result['status'], 'success')
        
        # 3. セキュリティスキャン
        scan_result = await self.manager.process_request({
            "operation": "security_scan",
            "scan_type": "comprehensive"
        })
        self.assertEqual(scan_result['status'], 'success')
    
    async def test_security_compliance_check(self):
        """セキュリティコンプライアンスチェックテスト"""
        # セキュリティシステムから直接コンプライアンスチェック
        compliance_result = await self.manager.security_system.process_request({
            "operation": "compliance_check"
        })
        
        self.assertEqual(compliance_result['status'], 'success')
        self.assertIn('compliance_results', compliance_result)
        
        compliance_data = compliance_result['compliance_results']
        self.assertIn('iron_will_compliance', compliance_data)
        self.assertIn('elder_legacy_compliance', compliance_data)
        self.assertIn('ancient_elder_approval', compliance_data)
        self.assertIn('compliance_score', compliance_data)
    
    async def test_multi_layer_security_validation(self):
        """多層セキュリティ検証テスト"""
        # 悪意のあるリクエストを作成
        malicious_request = {
            "operation": "create_branch",
            "branch_name": "../../../etc/passwd",
            "session_id": "'; DROP TABLE users; --",
            "source_ip": "10.0.0.1",  # ブロックされたIP範囲
            "user_agent": "sqlmap/1.5.2"  # 疑わしいUser-Agent
        }
        
        result = await self.manager.process_request(malicious_request)
        
        # セキュリティチェックで拒否されることを確認
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error_type'], 'security_error')


if __name__ == '__main__':
    # 非同期テストの実行
    unittest.main(verbosity=2)