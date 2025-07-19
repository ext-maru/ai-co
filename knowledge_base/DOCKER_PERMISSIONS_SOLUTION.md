# Docker権限問題の根本解決方法

## 問題
aicompanyユーザーがDockerにアクセスできない

## 根本原因
- ユーザーがdockerグループに追加されているが、現在のセッションに反映されていない
- WSL環境では新しいグループメンバーシップが即座に反映されない

## 解決方法

### 1. 即座の解決 (現在のセッション)
```bash
# sgコマンドでdockerグループ権限を使用
sg docker -c "docker ps"
sg docker -c "docker compose -f docker-compose.projects.yml up -d"
```

### 2. 永続的解決 (新しいセッション用)
```bash
# ログアウト→ログインまたは
sudo su - aicompany

# または新しいシェル起動
exec $SHELL
```

### 3. 自動化スクリプト
- `/home/aicompany/ai_co/scripts/start_project_services.sh` - プロジェクト起動
- `/home/aicompany/ai_co/scripts/fix_docker_permissions.sh` - 権限確認

### 4. systemdユーザーサービス (推奨)
```bash
# サービス有効化
systemctl --user enable elders-guild-projects.service

# サービス起動
systemctl --user start elders-guild-projects.service

# 状態確認
systemctl --user status elders-guild-projects.service
```

## ポート確認

### プロジェクトサービス
- **9005**: Frontend Project Manager (Next.js)
- **9007**: Web Monitoring Dashboard (Flask)
- **9008**: Test Calculator (Flask)

### 統合ポートマップ
- **9000**: Projects Gateway (Nginx)
- **9001**: Projects Dashboard (Grafana)
- **9002**: Projects Monitor (Prometheus)
- **9003**: Elders Guild Web Frontend
- **9004**: Elders Guild Web Backend
- **5433**: Projects Database (PostgreSQL)

## トラブルシューティング

### 権限確認
```bash
# グループ確認
groups aicompany

# Docker socket権限
ls -la /var/run/docker.sock

# Docker デーモン状態
systemctl is-active docker
```

### エラー対応
1. **Permission denied**: `sg docker -c` を使用
2. **Group not found**: ログアウト→ログイン
3. **Service not found**: systemdサービス再登録

## 実装日
2025年7月10日 - エルダーズギルド開発実行責任者による根本解決
