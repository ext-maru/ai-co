# 契約書類アップロードシステム - サーバデプロイ情報

**プロジェクト名**: 契約書類アップロードシステム (Contract Upload System)
**作成日**: 2025年7月10日
**管理者**: エルダーズギルド開発チーム

---

## 🌐 **本番サーバ情報**

### **サーバ基本情報**
- **IP アドレス**: `57.181.4.111`
- **OS**: Ubuntu 24.04.2 LTS
- **アーキテクチャ**: x86_64
- **メモリ**: 2GB RAM
- **ストレージ**: 28GB SSD
- **リージョン**: AWS ap-northeast-1

### **🔐 SSH接続情報**
```bash
# SSH接続コマンド
ssh -i server-private.pem ubuntu@57.181.4.111

# SCP ファイル転送
scp -i server-private.pem -r ./local-files ubuntu@57.181.4.111:/remote/path/

# SSH キー場所
# ローカル: /home/aicompany/ai_co/deployment/server-private.pem
```

### **SSH秘密鍵**
```
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAqsMcTuTVT4vM7McAjjVXLs+CQiIwTvRZ7WfvWldg780Vs79t
ZqhCD2pXGeOv/LnZwbNa2pba5GTOFskHTo5rPEZB1NbECMNpMv8+/0gBcXMG9ZNq
OGTSLGiwGsHMeVbeRpoySHuohAGNXLmcanBo8mV1l2N7p2MpXUpqvSzt/sTCoLAQ
allLDT2phSbaaL2eEkTICiq+mJBQUq43VtVs2NXScaOAi9RdrLd6YmmA814mEuJ2
1k3CxuAi47uKtHbkve+tjitYVZ6W6DgIBfJGKgWkTpmAfsBg9EpukasrADW8+CZG
IahahNU5GaYVRpW+E4X2ZMQlxzVQKVrumrKFAQIDAQABAoIBACO+T3CcKaJK6wws
44rg02zy9psNOPtt3lz5Qnqwi5PmY8KKMUYpthov8idzJ2VJKbGH716N8SeZiiHu
1l61JPEq66C3i7Uh4iVQlEkvM04h+7TvtG41fGDbUPFo23oSmthAcoIFkFKBWKuu
FnWZLf5/Ckw0ALAa64+hghIzE2YeReYJ4ye2hdPapaO2p1zSPGfU5iF0EKVlzLid
aoZxC6qLTQM8FFb6ek0g/MlI7Qbf1rMzwHOKztwbPWt2BADMAD+odTvnIsPRQoov
r1aJnPwZp0pWksQtkMF9UuJ2ji3ftnuEbF1bkl0/TvhZLH6o51Mwwoa5Sw0ZRmb9
pQvE79kCgYEA1zPiWuRJ2sYZ2bGLthrEYyT1bqTxUuGG375mcrADQKdAl2JDhiMi
COYw3etlog6vYeMppvJh4jXPPTq4nCkEgDyof50C+Q758v9Vb5at4wKVhdImszPA
736p66EL3G4+SYGa3zeNSYXUE6JsyL28pnHLvWAveVK4I9/cau0MlNcCgYEAyyJ1
rbsHKVHEpaUFaxRHguwXXXUCJKleRfLHum2AIlkXFiMsVKySggTBxSRjCgFeOxQr
QGVMKePFvKqNX6f/wOLnBKfio9IoKSBq+79h4a9lAhVTsOnNTPmZtjBOYNAvulEh
ODoqTKkhPYIemN0ZBvvchy6vShBOrXUy5ZaLoecCgYEAjW504eVMwHIXRSHRPxIi
ZUJB5sCSNTUwzdU1QUR6LsB8y8DxvbNTR+P407BD8BiUnNGNa0G6oM9abtQrxb2T
TrAO0Segb4yvKksynA68IwhsujEd7AIkV4G4LLp/sBPn7ak23mKFAX/pnCnQMrG3
zO/WxZP0P1jk2fbixocaEKsCgYB3Q54wCFUmD1oTnxXVTqzF03PMbTx65e3xx584
d735bLE/UBthA4lpSP2zj6+OWktHCIp0XoUfOxoHsWMbvHlOeGoGs8M/R85Ihz4I
3M7NQLtfQ8JFZqAhB5MWArqh4NmE3MlSR+Q56jsX7+OjAH0HOqy5udE0/OoUsXDW
l1MYFQKBgC16BzYyK0eOTgwT4EzgkIcOCGfnf+ELxyNzIliouJHGsEzbDxvHQ4Yj
wUmltsem6yqBCthmmElnq2TDMNN1qw4POj4eqelZ8WrmN7ytWhQFukFnZpc9idst
QzcdJQfKNO9qw7HYwoSM5IDbxAvrOT/NpLG+PUpIXZmCj/6mfGXZ
-----END RSA PRIVATE KEY-----
```

---

## 🏗️ **インフラ構成**

### **Docker環境**
- **Docker**: v28.3.2
- **Docker Compose**: v2.38.2
- **サービス**: 自動起動設定済み

### **Webサーバ**
- **Nginx**: v1.24.0 (Ubuntu)
- **設定ファイル**: `/etc/nginx/sites-available/elders-guild-contract-upload`
- **ポート**: 80 (HTTP), 443 (HTTPS)

### **ファイアウォール**
- **UFW**: 有効
- **許可ポート**: 22 (SSH), 80 (HTTP), 443 (HTTPS), 5000 (開発用)

### **セキュリティ**
- **Fail2Ban**: 侵入検知システム
- **SSH**: 鍵認証のみ、root無効
- **自動更新**: 有効

---

## 📦 **アプリケーション構成**

### **技術スタック**
- **Backend**: FastAPI (Python 3.11)
- **Frontend**: React 18 + TypeScript
- **Database**: PostgreSQL (予定) / SQLite (開発)
- **画像処理**: Pillow, OpenCV
- **認証**: JWT

### **主要機能**
1. **契約書アップロード**: PDF, JPEG, PNG対応
2. **文書分類**: AI自動分類システム
3. **承認ワークフロー**: 多段階承認プロセス
4. **検索・管理**: 全文検索、メタデータ管理
5. **セキュリティ**: 暗号化、アクセス制御

### **デプロイディレクトリ**
```
/opt/elders-guild/contract-upload-system/
├── backend/         # FastAPI アプリケーション
├── frontend/        # React フロントエンド
├── uploads/         # アップロードファイル
├── database/        # データベースファイル
├── logs/           # アプリケーションログ
├── config/         # 設定ファイル
└── docker-compose.yml
```

---

## 🚀 **デプロイ手順**

### **1. ローカルからファイル転送**
```bash
# プロジェクトルートから
scp -i /home/aicompany/ai_co/deployment/server-private.pem -r . ubuntu@57.181.4.111:/tmp/contract-upload-system
```

### **2. サーバでデプロイ実行**
```bash
ssh -i /home/aicompany/ai_co/deployment/server-private.pem ubuntu@57.181.4.111
cd /tmp/contract-upload-system
./deploy.sh
```

### **3. 動作確認**
```bash
# アプリケーション確認
curl http://57.181.4.111/

# コンテナ状態確認
docker ps
docker logs contract-upload-backend
docker logs contract-upload-frontend
```

---

## 🛠️ **管理・運用**

### **アプリケーション管理**
```bash
# サービス起動
cd /opt/elders-guild/contract-upload-system
docker compose up -d

# サービス停止
docker compose down

# ログ確認
docker compose logs -f

# 再起動
docker compose restart
```

### **Nginx管理**
```bash
# 設定テスト
sudo nginx -t

# 再読み込み
sudo systemctl reload nginx

# 状態確認
sudo systemctl status nginx
```

### **システム監視**
```bash
# システムリソース
htop
df -h
free -h

# Docker統計
docker stats

# ログ確認
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

---

## 🔧 **トラブルシューティング**

### **よくある問題**

#### **1. Docker権限エラー**
```bash
# 解決方法
sudo usermod -aG docker ubuntu
newgrp docker
# または
sg docker -c "docker compose up -d"
```

#### **2. ポート競合**
```bash
# ポート使用状況確認
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :5000

# プロセス終了
sudo kill $(sudo lsof -t -i:80)
```

#### **3. ディスク容量不足**
```bash
# 容量確認
df -h

# Docker クリーンアップ
docker system prune -a
docker volume prune
```

---

## 📊 **監視・ログ**

### **ログファイル場所**
- **Nginx アクセス**: `/var/log/nginx/access.log`
- **Nginx エラー**: `/var/log/nginx/error.log`
- **アプリケーション**: `docker compose logs`
- **システム**: `/var/log/syslog`

### **パフォーマンス監視**
```bash
# CPU・メモリ使用率
top
htop

# ディスクI/O
iotop

# ネットワーク
iftop
```

---

## 🔄 **バックアップ・復旧**

### **データバックアップ**
```bash
# アップロードファイル
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz /opt/elders-guild/contract-upload-system/uploads/

# データベース（PostgreSQL使用時）
pg_dump contract_upload > backup_$(date +%Y%m%d).sql

# 設定ファイル
cp -r /opt/elders-guild/contract-upload-system/config/ ./config_backup_$(date +%Y%m%d)/
```

### **復旧手順**
```bash
# データ復旧
tar -xzf uploads_backup_YYYYMMDD.tar.gz -C /

# データベース復旧
psql contract_upload < backup_YYYYMMDD.sql

# 設定復旧
cp -r ./config_backup_YYYYMMDD/* /opt/elders-guild/contract-upload-system/config/
```

---

## 📞 **緊急連絡先**

### **エルダーズギルド開発チーム**
- **技術責任者**: クロードエルダー
- **緊急対応**: インシデント賢者
- **運用サポート**: エルフの森チーム

### **インフラ管理**
- **サーバ管理**: AWS ap-northeast-1
- **ドメイン管理**: 未設定（IP直接アクセス）
- **SSL証明書**: 未設定（HTTP運用）

---

**📅 最終更新**: 2025年7月10日
**🏛️ エルダーズギルド**: 契約書類アップロードシステム運用ガイド
**📝 ドキュメント管理**: ナレッジ賢者
