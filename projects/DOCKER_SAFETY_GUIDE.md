# 🛡️ Elders Guild Docker安全性ガイド

## なぜDocker化が必要なのか

### ❌ ローカル実行の危険性

#### 1. **環境破壊リスク**
```bash
# 危険な例：ローカルでのテスト実行
python -m pytest tests/  # システムPythonを汚染
rm -rf /tmp/*           # 他のプロセスのファイルも削除
sudo pip install ...    # システム全体に影響
```

#### 2. **実際に起きた問題**
- データベースロックエラー（今回発生）
- ファイル権限エラー（今回発生）
- テストファイルがシステムに残存
- 本番環境変数の誤使用

#### 3. **セキュリティインシデント例**
- テストコードが`~/.ssh`にアクセス
- 環境変数からAPIキーが漏洩
- ポート競合で他サービス停止

### ✅ Docker化による安全対策

#### 1. **完全な分離**
```yaml
# docker-compose.test.yml
services:
  test:
    user: testuser  # 非rootユーザー
    networks:
      - test-network  # 隔離されたネットワーク
    volumes:
      - ./test_results:/app/test_results  # 限定的なマウント
```

#### 2. **環境の一貫性**
- 同じOS、同じPythonバージョン
- 依存関係の固定
- 環境変数の明示的管理

#### 3. **自動クリーンアップ**
```bash
# テスト後の完全クリーンアップ
docker-compose down --volumes --remove-orphans
```

## 🚀 推奨される使用方法

### プロジェクト実行
```bash
# アプリケーション起動（Docker）
cd projects
./projects-start.sh start

# 個別プロジェクト起動
docker-compose -f docker-compose.projects.yml up image-upload-manager
```

### テスト実行
```bash
# テスト実行（Docker）
./test-runner.sh image-upload-manager all --build

# カバレッジ分析
./test-runner.sh image-upload-manager coverage --viewer
```

### 開発ワークフロー
```bash
# 1. コード変更
vim app/models.py

# 2. Dockerでテスト
./test-runner.sh image-upload-manager unit

# 3. 問題があればインタラクティブデバッグ
./test-runner.sh image-upload-manager --interactive

# 4. 全テスト実行
./test-runner.sh image-upload-manager all

# 5. アプリケーション確認
./projects-start.sh start
```

## 🔒 セキュリティベストプラクティス

### 1. **最小権限の原則**
- 非rootユーザーで実行
- 必要最小限のボリュームマウント
- 読み取り専用マウントの活用

### 2. **環境変数の管理**
```bash
# .env.localファイルの使用（gitignore済み）
cp .env.example .env.local
vim .env.local  # 秘密情報を設定

# Docker実行時に読み込み
docker-compose --env-file .env.local up
```

### 3. **ネットワーク分離**
- プロジェクト用ネットワーク
- テスト用ネットワーク
- 外部アクセスの制限

### 4. **リソース制限**
```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
```

## 📋 チェックリスト

開発時は以下を確認：

- [ ] ローカルでの直接実行を避ける
- [ ] Dockerイメージを定期的に更新
- [ ] テスト前にビルドする（--build）
- [ ] 環境変数は.env.localで管理
- [ ] テスト後はクリーンアップ
- [ ] 本番データを使用しない
- [ ] セキュリティ更新を適用

## 🎯 結論

**「ローカル実行 = リスク」「Docker実行 = 安全」**

Elders Guildでは、すべてのプロジェクト実行とテストをDocker環境で行うことを強く推奨します。これにより、環境破壊のリスクを排除し、安全で再現可能な開発環境を維持できます。
