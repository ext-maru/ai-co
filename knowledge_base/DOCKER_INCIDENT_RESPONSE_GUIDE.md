# Docker Incident Response Guide
# Docker インシデント対応ガイド

**作成者**: RAGエルダー (Search Mystic)
**対象**: エルダーズギルド全体
**最終更新**: 2025-07-10 23:26:02

## 🚨 緊急対応フローチャート

### Level 1: 権限問題
```bash
# 症状: Permission denied while trying to connect to Docker daemon
# 即座対応:
sg docker -c "docker ps"

# 根本解決:
sudo usermod -aG docker $USER
newgrp docker

# 検証:
docker ps
```

### Level 2: コンテナ起動失敗
```bash
# 症状: Service dependencies failed
# 診断:
docker compose logs service-name
docker compose ps -a

# 対応:
docker compose down
docker compose up -d --force-recreate
```

### Level 3: ネットワーク問題
```bash
# 症状: Network connectivity issues
# 診断:
docker network ls
docker network inspect network-name

# 対応:
docker network prune
docker compose down && docker compose up -d
```

### Level 4: ストレージ問題  
```bash
# 症状: Volume mount failures
# 診断:
docker volume ls
df -h

# 対応:
docker volume prune
docker system prune -a
```

## 🛠️ エルダーズギルド特化対応

### 4賢者システム障害
1. **ナレッジ賢者**: 知識ベースアクセス不可
   ```bash
   docker exec knowledge-sage ls /knowledge_base
   ```

2. **タスク賢者**: タスクトラッカー応答なし
   ```bash
   docker logs task-oracle --tail 50
   ```

3. **インシデント賢者**: アラート機能停止
   ```bash
   docker restart crisis-sage
   ```

4. **RAG賢者**: 検索機能エラー
   ```bash
   docker exec rag-elder python -c "import libs.rag_manager"
   ```

### プロジェクトポートフォリオ障害
```bash
# 9000-9008番台ポート競合
netstat -tulpn | grep :900

# サービス一括復旧
/home/aicompany/ai_co/scripts/start_project_services.sh
```

## 📊 監視・診断コマンド集

### システム状態確認
```bash
# Docker全体状況
docker system df
docker system events --since 1h

# リソース使用量
docker stats --no-stream
docker container ls --format "table {.Names}	{.Status}	{.Ports}"
```

### ログ分析
```bash
# エラーログ抽出
docker logs container-name 2>&1 | grep -i error

# リアルタイム監視
docker logs -f --tail 100 container-name
```

### パフォーマンス診断
```bash
# ボトルネック特定
docker exec container-name top
docker exec container-name df -h
docker exec container-name free -m
```

---
**作成完了**: 2025-07-10 23:26:02
**緊急連絡**: エルダー評議会チャンネル
**エスカレーション**: グランドエルダーmaru
