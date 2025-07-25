# Docker コンテナ再起動ループ トラブルシューティングガイド

**作成日**: 2025年7月23日  
**作成者**: クロードエルダー（Claude Elder）  

## 🎯 このガイドの目的

Dockerコンテナが再起動ループに陥った際の診断と解決方法を提供します。

## 🔍 症状

```bash
docker-compose ps
```
実行時に以下のような状態：
- STATUS が "Restarting" を繰り返す
- コンテナが数秒で再起動

## 📋 診断手順

### Step 1: ログ確認
```bash
# 最新のログを確認
docker logs <container_name> --tail 50

# タイムスタンプ付きで確認
docker logs -t <container_name> --tail 50
```

### Step 2: エラーパターンの特定

#### パターン1: ImportError
```python
ImportError: cannot import name 'Agent' from 'python_a2a'
```
**原因**: ライブラリのバージョン不一致

#### パターン2: AttributeError
```python
AttributeError: 'MyClass' object has no attribute 'method'
```
**原因**: APIの変更

#### パターン3: ModuleNotFoundError
```python
ModuleNotFoundError: No module named 'mymodule'
```
**原因**: パッケージ構造の問題

### Step 3: コンテナ内部の確認
```bash
# ファイル構造確認
docker exec <container_name> ls -la /app/

# Pythonモジュール確認
docker exec <container_name> python -c "import sys; print(sys.path)"

# 環境変数確認
docker exec <container_name> env
```

## 🛠️ 解決方法

### 1. イメージの再ビルド
```bash
# キャッシュなしで再ビルド
docker-compose build --no-cache <service_name>

# 全サービスの再ビルド
docker-compose build --no-cache
```

### 2. コンテナの完全再作成
```bash
# 停止して削除
docker-compose down

# ビルドして起動
docker-compose up -d --build
```

### 3. 個別サービスの再起動
```bash
# 特定サービスのみ
docker-compose restart <service_name>

# 強制再作成
docker-compose up -d --force-recreate <service_name>
```

## 🚨 よくある原因と対策

### 原因1: ポート競合
**症状**: "bind: address already in use"
```bash
# 使用中のポート確認
sudo lsof -i :PORT_NUMBER

# プロセスを終了
kill -9 PID
```

### 原因2: 依存サービスの未起動
**対策**: docker-compose.ymlで依存関係を設定
```yaml
depends_on:
  postgres:
    condition: service_healthy
```

### 原因3: 環境変数の不足
**対策**: 必要な環境変数を確認
```bash
# .envファイルの確認
cat .env

# docker-compose.ymlでの設定確認
grep -A5 environment docker-compose.yml
```

### 原因4: ヘルスチェックの失敗
**対策**: ヘルスチェック設定を確認
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## 📊 デバッグチェックリスト

- [ ] エラーログを確認した
- [ ] 依存ライブラリのバージョンを確認した
- [ ] ポートの競合を確認した
- [ ] 環境変数が正しく設定されている
- [ ] ファイルパーミッションを確認した
- [ ] ディスク容量が十分ある
- [ ] メモリが十分ある
- [ ] ネットワーク設定を確認した

## 💡 予防策

1. **ログの充実**
   - 起動時の詳細ログ出力
   - エラーの詳細情報記録

2. **ヘルスチェック実装**
   - 各サービスにヘルスチェックエンドポイント
   - 適切なタイムアウト設定

3. **段階的起動**
   - depends_onで起動順序制御
   - 初期化完了の確認

4. **エラーハンドリング**
   - グレースフルシャットダウン
   - リトライロジック

## 🔧 緊急対応コマンド集

```bash
# 全コンテナ停止
docker-compose stop

# 全コンテナ削除（データは保持）
docker-compose down

# 全コンテナとボリューム削除（注意！）
docker-compose down -v

# ログをファイルに保存
docker logs <container_name> > container_debug.log 2>&1

# リソース使用状況確認
docker stats

# 不要なイメージ削除
docker image prune -a
```

---

**関連ドキュメント**:
- [Flask移行ノウハウ集](../migration/flask-migration-knowhow.md)
- [Docker環境構築ガイド](../setup/docker-setup-guide.md)