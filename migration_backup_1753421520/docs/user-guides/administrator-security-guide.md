# 🔐 Auto Issue Processor A2A 管理者向けセキュリティ設定ガイド

## 🛡️ 概要

このガイドでは、Auto Issue Processor A2Aのセキュリティ設定と管理者向けの運用手順を説明します。

## 🔑 認証・認可設定

### GitHub Token管理

#### Personal Access Token（PAT）設定

```bash
# 1. 最小権限の原則
# 必要最小限のスコープのみ選択：
# ✅ repo
# ✅ workflow  
# ❌ admin:org (不要)
# ❌ delete_repo (危険)

# 2. Token有効期限設定
# 推奨: 90日間
# 定期的なローテーションスケジュール設定
```

#### GitHub App認証（推奨）

```yaml
# github_app_config.yaml
app_id: 123456
installation_id: 78910
private_key_path: /secure/path/to/private-key.pem
permissions:
  issues: write
  pull_requests: write
  contents: write
  metadata: read
```

### Claude API Key管理

```bash
# 1. 環境変数での管理（推奨）
export CLAUDE_API_KEY="sk-ant-api03-..."

# 2. 秘密管理システム使用（本番環境）
# HashiCorp Vault
vault kv get -field=api_key secret/claude/api

# AWS Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id claude-api-key \
  --query SecretString --output text

# 3. ローテーション設定
# 90日ごとの自動ローテーション
```

## 🔒 アクセス制御

### リポジトリレベル制御

```yaml
# .github/CODEOWNERS
# Auto Issue Processor関連ファイル
/libs/integrations/github/ @security-team @auto-issue-admins
/.env @security-team
/configs/ @security-team @auto-issue-admins

# ドキュメント
/docs/ @documentation-team @auto-issue-admins
```

### Branch Protection Rules

```bash
# GitHub CLI設定
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["quality-gate","security-scan"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":2,"dismiss_stale_reviews":true}' \
  --field restrictions=null
```

### IPアクセス制限（企業環境）

```yaml
# security_config.yaml
allowed_ip_ranges:
  - 10.0.0.0/8      # 社内ネットワーク
  - 172.16.0.0/12   # VPN範囲
  - 192.168.1.0/24  # 開発チーム

blocked_countries:
  - CN  # 必要に応じて
  - RU
```

## 🛡️ セキュリティ監視

### 自動セキュリティスキャン

```python
# security_scanner.py
from libs.security_audit_system import SecurityAuditor

def daily_security_scan():
    """日次セキュリティスキャン"""
    auditor = SecurityAuditor()
    
    # 1. 脆弱性スキャン
    vuln_results = auditor.scan_vulnerabilities()
    
    # 2. 権限監査
    perm_results = auditor.audit_permissions()
    
    # 3. コンプライアンスチェック
    compliance_results = auditor.check_compliance()
    
    # 4. 異常検知
    anomaly_results = auditor.detect_anomalies()
    
    # 5. レポート生成
    security_report = auditor.generate_security_report({
        'vulnerabilities': vuln_results,
        'permissions': perm_results,
        'compliance': compliance_results,
        'anomalies': anomaly_results
    })
    
    return security_report

# Cron設定: 毎日午前2時実行
# 0 2 * * * cd /path/to/ai-co && python3 security_scanner.py
```

### ログ監視とアラート

```bash
# security_monitor.sh
#!/bin/bash

# 1. 不審なアクセスパターン検知
grep -E "(failed|unauthorized|denied)" logs/auto_issue_processor.log | \
  awk '{print $1, $2, $NF}' | sort | uniq -c | sort -nr | head -10

# 2. API使用量監視
echo "=== API Usage Monitoring ==="
grep "API_CALL" logs/auto_issue_processor.log | \
  grep "$(date '+%Y-%m-%d')" | wc -l

# 3. 異常な処理時間検知
grep "PROCESSING_TIME" logs/auto_issue_processor.log | \
  awk '$3 > 300 {print "Long processing detected:", $0}'

# 4. セキュリティイベント監視
grep -i "security\|auth\|token\|key" logs/auto_issue_processor.log | \
  grep "$(date '+%Y-%m-%d')" | tail -20
```

## 🔐 データ保護

### 機密情報の取り扱い

```python
# secure_data_handler.py
import re
import hashlib

class SecureDataHandler:
    """機密情報の安全な取り扱い"""
    
    SENSITIVE_PATTERNS = [
        r'sk-ant-api03-[A-Za-z0-9-_]+',  # Claude API Key
        r'ghp_[A-Za-z0-9]{36}',          # GitHub Personal Access Token
        r'ghs_[A-Za-z0-9]{36}',          # GitHub OAuth Token
        r'github_pat_[A-Za-z0-9_]+',     # GitHub Fine-grained PAT
        r'-----BEGIN [A-Z ]+-----.*?-----END [A-Z ]+-----',  # Private Keys
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP Address
    ]
    
    def sanitize_log_data(self, data: str) -> str:
        """ログデータから機密情報を除去"""
        sanitized = data
        for pattern in self.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.DOTALL)
        return sanitized
    
    def hash_sensitive_data(self, data: str) -> str:
        """機密データのハッシュ化"""
        return hashlib.sha256(data.encode()).hexdigest()[:16]
```

### バックアップとリカバリ

```bash
# secure_backup.sh
#!/bin/bash

# 1. 暗号化バックアップ
gpg --symmetric --cipher-algo AES256 \
  --compress-algo 1 \
  --output backup_$(date +%Y%m%d).tar.gz.gpg \
  backup_$(date +%Y%m%d).tar.gz

# 2. S3への安全なアップロード
aws s3 cp backup_$(date +%Y%m%d).tar.gz.gpg \
  s3://secure-backup-bucket/auto-issue-processor/ \
  --sse AES256 \
  --metadata retention="90days"

# 3. ローカルファイル削除
rm backup_$(date +%Y%m%d).tar.gz*

# 4. バックアップ検証
aws s3 ls s3://secure-backup-bucket/auto-issue-processor/ | tail -5
```

## 👤 ユーザー管理

### 役割ベースアクセス制御（RBAC）

```yaml
# rbac_config.yaml
roles:
  admin:
    permissions:
      - all
    users:
      - security-admin
      - system-admin
  
  operator:
    permissions:
      - read_logs
      - restart_services
      - view_metrics
    users:
      - ops-team
  
  developer:
    permissions:
      - read_code
      - create_pr
      - view_docs
    users:
      - dev-team
  
  readonly:
    permissions:
      - read_docs
      - view_status
    users:
      - stakeholders
```

### 監査ログ

```python
# audit_logger.py
import json
from datetime import datetime

class AuditLogger:
    """セキュリティ監査ログ"""
    
    def log_security_event(self, event_type: str, user: str, 
                          resource: str, action: str, result: str):
        """セキュリティイベントのログ記録"""
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user': user,
            'resource': resource,
            'action': action,
            'result': result,
            'source_ip': self._get_source_ip(),
            'user_agent': self._get_user_agent()
        }
        
        # セキュリティログファイルに記録
        with open('logs/security_audit.log', 'a') as f:
            f.write(json.dumps(audit_entry) + '\n')
        
        # 重要なイベントは即座にアラート
        if event_type in ['UNAUTHORIZED_ACCESS', 'PRIVILEGE_ESCALATION']:
            self._send_security_alert(audit_entry)
```

## 🚨 インシデント対応

### セキュリティインシデント対応手順

#### 1. 検知フェーズ

```bash
# 自動検知システム
python3 scripts/security_monitor.py --continuous

# 手動確認
./scripts/check_security_status.sh
```

#### 2. 対応フェーズ

```bash
# P1: 重大なセキュリティ侵害
# 1. 即座にシステム停止
sudo systemctl stop auto-issue-processor

# 2. ネットワーク分離
sudo iptables -A INPUT -j DROP
sudo iptables -A OUTPUT -j DROP

# 3. 証跡保全
cp -r logs/ incident_$(date +%Y%m%d%H%M%S)/
cp .env incident_$(date +%Y%m%d%H%M%S)/

# 4. トークン無効化
gh auth refresh  # GitHub Token
# Claude APIコンソールでAPIキー無効化
```

#### 3. 復旧フェーズ

```bash
# 1. セキュリティパッチ適用
git pull origin main
pip install --upgrade -r requirements.txt

# 2. 新しい認証情報生成
./scripts/rotate_credentials.sh

# 3. システム再起動
sudo systemctl start auto-issue-processor

# 4. 監視強化
./scripts/enhanced_monitoring.sh
```

## 📊 セキュリティメトリクス

### Key Performance Indicators (KPIs)

```python
# security_metrics.py
def generate_security_metrics():
    """セキュリティメトリクスの生成"""
    return {
        'authentication_success_rate': 99.8,
        'failed_login_attempts': 12,
        'api_abuse_incidents': 0,
        'vulnerability_scan_score': 95,
        'compliance_score': 98,
        'incident_response_time': 15,  # minutes
        'security_training_completion': 100,  # percent
        'patch_deployment_time': 24,  # hours
    }
```

### ダッシュボード

```html
<!-- security_dashboard.html -->
<div class="security-dashboard">
    <div class="metric-card">
        <h3>🔐 Authentication</h3>
        <p>Success Rate: 99.8%</p>
    </div>
    <div class="metric-card">
        <h3>🛡️ Vulnerabilities</h3>
        <p>Critical: 0, High: 2, Medium: 5</p>
    </div>
    <div class="metric-card">
        <h3>📊 Compliance</h3>
        <p>Score: 98/100</p>
    </div>
</div>
```

## 📋 セキュリティチェックリスト

### 初期設定
- [ ] 最小権限の原則でToken設定
- [ ] Branch Protection Rules有効化
- [ ] IP制限設定（企業環境）
- [ ] 暗号化通信設定
- [ ] 監査ログ有効化

### 日次チェック
- [ ] セキュリティログレビュー
- [ ] 不審なアクセス確認
- [ ] API使用量監視
- [ ] システムリソース確認

### 週次チェック
- [ ] 脆弱性スキャン実行
- [ ] 権限レビュー
- [ ] バックアップ検証
- [ ] インシデント対応訓練

### 月次チェック
- [ ] 認証情報ローテーション
- [ ] セキュリティポリシー更新
- [ ] コンプライアンス監査
- [ ] セキュリティ教育実施

## 🔗 関連ドキュメント

- [インシデント対応ガイド](../runbooks/incident-response-guide.md)
- [日常運用ガイド](../runbooks/daily-operations-guide.md)
- [コントリビューションガイド](../developer-guides/contribution-guide.md)

---
*最終更新: 2025年7月21日*