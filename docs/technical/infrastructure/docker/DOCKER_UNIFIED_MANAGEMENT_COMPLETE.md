# Docker統合管理システム完全ガイド
**エルダーズギルド Docker完全統合管理システム**

## 📋 統合概要

**4つの重複Dockerシステムを統合統一**:
1. `libs/docker.py` - Docker権限管理システム
2. `libs/docker_template_manager.py` - テンプレート管理システム
3. `libs/docker_management_api.py` - Docker Management API
4. `libs/docker_redundancy_system.py` - 冗長化システム

## 🏗️ 統合アーキテクチャ

### 🎯 核心システム設計
```
📦 docker_unified_system.py (新規統合メインシステム)
├── 🔧 DockerPermissionManager - 権限管理
├── 🏗️ DockerTemplateManager - テンプレート管理
├── 🌐 DockerAPIManager - RESTful API
└── 🚀 DockerRedundancyManager - 冗長化・監視
```

## 🔧 1. Docker権限管理 (`libs/docker.py`)

### 🔒 権限管理機能
- **DockerStatus**: Docker状態詳細取得
- **権限自動修正**: dockerグループ追加、ソケット権限修正
- **sg docker実行**: `sg docker -c "command"` による権限コマンド実行

### 💻 主要API
```python
from libs.docker import get_docker_status, fix_docker_permissions, run_docker_command

# 状態確認
status = get_docker_status()
print(f"権限OK: {status.permission_ok}")

# 権限修正
result = fix_docker_permissions()

# Docker コマンド実行
result = run_docker_command("ps -a")
```

## 🏗️ 2. テンプレート管理 (`libs/docker_template_manager.py`)

### 📋 テンプレート機能
- **プロジェクト別テンプレート**: AI、Web、Data Science、Security
- **ランタイム環境**: Python 3.9/3.11、Node.js 18/20、Go 1.21
- **セキュリティレベル**: SANDBOX, DEVELOPMENT, PRODUCTION
- **リソース制限**: CPU/Memory制限設定

### 🔧 テンプレート例
```python
# AI プロジェクトテンプレート
template = DockerTemplate(
    name="ai_project",
    project_type=ProjectType.AI_RESEARCH,
    runtime=RuntimeEnvironment.PYTHON_39,
    security_level=SecurityLevel.DEVELOPMENT,
    base_image="python:3.9-slim",
    python_packages=["tensorflow", "pytorch", "pandas", "numpy"],
    ports=["8888:8888", "6006:6006"],
    resource_limits={"cpus": "2.0", "memory": "4g"}
)
```

## 🌐 3. Docker Management API (`libs/docker_management_api.py`)

### 🔗 RESTful API エンドポイント
```bash
# コンテナ管理
POST   /containers              # コンテナ作成
GET    /containers              # コンテナ一覧
GET    /containers/{id}         # コンテナ詳細
POST   /containers/{id}/actions # アクション実行
GET    /containers/{id}/stats   # 統計情報
DELETE /containers/{id}         # コンテナ削除

# 4賢者システム統合
GET    /sages/status            # 4賢者コンテナ状態
```

### ⚡ 使用例
```bash
# API サーバー起動
python3 libs/docker_management_api.py

# コンテナ作成
curl -X POST http://localhost:8080/containers \
  -H "Content-Type: application/json" \
  -d '{"name": "ai-project", "project_type": "AI_RESEARCH"}'
```

## 🚀 4. 冗長化システム (`libs/docker_redundancy_system.py`)

### 🔄 冗長化機能
- **自動フェイルオーバー**: 障害時の自動切替
- **スケーリング**: 負荷に応じた自動スケール
- **ヘルスモニタリング**: リアルタイム監視
- **Redis統合**: 状態管理・クラスタ連携

### 📊 監視項目
- **サービス状態**: running, exited, restarting
- **リソース使用率**: CPU, Memory, Network
- **ヘルスチェック**: 30秒間隔監視
- **フェイルオーバー**: 3回連続失敗で切替

## 🔧 統合使用方法

### 1. 権限確認・修正
```bash
# スクリプト実行（推奨）
/home/aicompany/ai_co/scripts/fix_docker_permissions.sh

# Python直接実行
python3 -c "from libs.docker import *; print(get_docker_status())"
```

### 2. テンプレート利用
```python
from libs.docker_template_manager import DockerTemplateManager

manager = DockerTemplateManager()
template = manager.get_template(
    project_type=ProjectType.AI_RESEARCH,
    runtime=RuntimeEnvironment.PYTHON_39,
    security_level=SecurityLevel.DEVELOPMENT
)
manager.create_project_structure("my-ai-project", "/tmp/projects", template)
```

### 3. API利用
```bash
# APIサーバー起動
python3 libs/docker_management_api.py &

# コンテナ操作
curl -X GET http://localhost:8080/containers
```

### 4. 冗長化・監視
```python
from libs.docker_redundancy_system import DockerRedundancyManager

manager = DockerRedundancyManager()
await manager.start_monitoring()
```

## ⚙️ 設定・構成

### 🔧 環境変数
```bash
# API設定
DOCKER_API_HOST=0.0.0.0
DOCKER_API_PORT=8080

# Redis設定（冗長化用）
REDIS_HOST=localhost
REDIS_PORT=6379

# 監視設定
MONITORING_INTERVAL=10
HEALTH_CHECK_TIMEOUT=30
```

### 📋 設定ファイル
```yaml
# docker-config.yml
docker:
  permission_check: true
  auto_fix: true
  use_sg_docker: true
  
monitoring:
  interval: 10
  retention_hours: 24
  alert_threshold: 80
  
redundancy:
  min_replicas: 2
  max_replicas: 8
  scale_threshold: 80
```

## 🚨 トラブルシューティング

### ❌ 権限問題
```bash
# 問題: Permission denied
# 解決1: 自動修正
python3 libs/docker.py

# 解決2: 手動修正
sudo usermod -aG docker $USER
newgrp docker

# 解決3: sg コマンド使用
sg docker -c "docker ps"
```

### ⚠️ API接続問題
```bash
# ポート確認
ss -tlnp | grep 8080

# プロセス確認
ps aux | grep docker_management_api

# 再起動
pkill -f docker_management_api
python3 libs/docker_management_api.py &
```

### 🔄 冗長化問題
```bash
# Redis接続確認
redis-cli ping

# コンテナ状態確認
docker ps -a

# ログ確認
docker logs <container_id>
```

## 📊 モニタリング・ログ

### 📈 メトリクス
- **応答時間**: API レスポンス時間
- **成功率**: コンテナ操作成功率
- **リソース使用率**: CPU/Memory使用率
- **冗長化状態**: レプリカ数・ヘルス状態

### 📋 ログ出力
```bash
# システムログ
tail -f /var/log/docker-management.log

# アプリケーションログ
tail -f logs/docker_api.log
tail -f logs/docker_redundancy.log

# 冗長化ログ
tail -f logs/docker_monitoring.log
```

## 🔄 今後の拡張計画

### 🚀 Phase 2計画
1. **Kubernetes統合**: Docker → K8s移行対応
2. **GitOps連携**: Git push → 自動デプロイ
3. **マルチクラウド**: AWS、GCP、Azure対応
4. **セキュリティ強化**: 脆弱性スキャン・SAST統合

### 📋 優先度
- **High**: Kubernetes統合、セキュリティ強化
- **Medium**: GitOps連携、監視強化
- **Low**: マルチクラウド、UI ダッシュボード

---

## 🎯 まとめ

**Docker統合管理システム**により以下を実現：

✅ **権限問題の根本解決** - 自動権限修正・sg docker対応  
✅ **テンプレート標準化** - プロジェクト別最適化テンプレート  
✅ **RESTful API提供** - プログラマティックな操作  
✅ **冗長化・監視** - 24/7安定稼働・自動フェイルオーバー  

**エルダーズギルドのDocker運用が完全に標準化・自動化されました** 🏛️

**更新日**: 2025年7月22日  
**作成者**: Claude Elder - エルダーズギルド開発実行責任者
