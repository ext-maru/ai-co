# エルダーズギルド プロジェクトポートフォリオ一覧

**更新日**: 2025年7月10日
**管理者**: クロードエルダー
**承認**: グランドエルダーmaru

---

## 🏛️ **エルダーズギルド プロジェクト構成**

### **🌟 メインプロジェクト (ポート9000-9008)**

#### **1. 🏰 Elders Guild Web System**
- **場所**: `projects/elders-guild-web/`
- **技術**: Next.js 14 (Frontend) + FastAPI (Backend)
- **ポート**: 9003 (Frontend), 9004 (Backend)
- **機能**: 4賢者システム統合Web UI、リアルタイムダッシュボード
- **特徴**: WebSocket通信、4賢者との連携、エルダー評議会モード

#### **2. 📋 Frontend Project Manager**
- **場所**: `projects/frontend-project-manager/`
- **技術**: Next.js 14
- **ポート**: 9005 ✅ **現在稼働中**
- **機能**: プロジェクト管理ポータル、ドキュメント閲覧、統計表示
- **特徴**: テスト統合、API管理、プロジェクトスキャン

#### **3. 📸 Image Upload Manager**
- **場所**: `projects/image-upload-manager/`
- **技術**: Flask + SQLite
- **機能**: 画像アップロード、顧客管理、Google Drive統合
- **状態**: 完全テスト済み (100%カバレッジ)

#### **4. 📦 Upload Image Service**
- **場所**: `projects/upload-image-service/`
- **技術**: FastAPI (Backend) + React (Frontend)
- **機能**: 契約書アップロード、文書処理、承認ワークフロー
- **特徴**: Docker化完了、REST API

#### **5. 📊 Web Monitoring Dashboard**
- **場所**: `projects/web-monitoring-dashboard/`
- **技術**: Flask + React (Vite)
- **ポート**: 9007
- **機能**: システム監視、4賢者ステータス、分析ダッシュボード
- **特徴**: リアルタイム更新、認証システム

#### **6. 🧮 Test Calculator Project**
- **場所**: `projects/test-calculator-project/`
- **技術**: Python Flask
- **ポート**: 9008
- **機能**: 計算機能、テスト用プロジェクト
- **目的**: 開発・テスト環境検証

### **🛠️ インフラストラクチャ**

#### **7. 🌐 Projects Gateway**
- **場所**: `projects/gateway/`
- **技術**: Nginx リバースプロキシ
- **ポート**: 9000
- **機能**: 全プロジェクトへのルーティング、負荷分散

#### **8. 📈 Monitoring Stack**
- **Grafana Dashboard**: ポート9001 (統合ダッシュボード)
- **Prometheus Monitor**: ポート9002 (メトリクス収集)
- **PostgreSQL**: ポート5433 (共有データベース)

---

## 📊 **プロジェクト状態サマリー**

### **✅ 稼働中**
- **Frontend Project Manager** (9005) - Next.js
- **Flask Services** (9001) - 一部稼働中

### **🔧 Docker準備完了**
- **Elders Guild Web System** - フルスタック構成
- **Image Upload Manager** - テスト完備
- **Upload Image Service** - API + Frontend
- **Web Monitoring Dashboard** - 監視統合

### **⚙️ 設定要調整**
- **Projects Gateway** - Nginx設定
- **Monitoring Stack** - Prometheus + Grafana
- **Test Calculator** - シンプル検証用

---

## 🐳 **Docker統合状況**

### **完全Docker化済み**
1. **Upload Image Service**: `docker-compose.yml` + 本番設定
2. **Image Upload Manager**: テスト環境含む完全統合
3. **Elders Guild Web**: フロントエンド・バックエンド分離

### **Docker設定ファイル**
- **メイン**: `docker-compose.projects.yml` (全サービス統合)
- **開発**: `docker-compose.dev.yml` (開発環境用)
- **テスト**: `docker-compose.test.yml` (テスト専用)

### **ポートマッピング**
```yaml
9000: Projects Gateway (Nginx)
9001: Projects Dashboard (Grafana)
9002: Projects Monitor (Prometheus)
9003: Elders Guild Web Frontend (Next.js)
9004: Elders Guild Web Backend (FastAPI)
9005: Frontend Project Manager (Next.js) ✅
9007: Web Monitoring Dashboard (Flask)
9008: Test Calculator (Flask)
5433: Projects Database (PostgreSQL)
```

---

## 🚀 **技術スタック詳細**

### **Frontend**
- **Next.js 14**: Elders Guild Web, Frontend Project Manager
- **React 18**: Upload Image Service UI, Monitoring Dashboard
- **TypeScript**: 全フロントエンドプロジェクト
- **Tailwind CSS**: スタイリング統一

### **Backend**
- **FastAPI**: Elders Guild Web Backend, Upload Image Service
- **Flask**: Image Upload Manager, Web Monitoring, Test Calculator
- **Python 3.11**: 全バックエンドサービス
- **SQLite/PostgreSQL**: データ永続化

### **インフラ**
- **Docker + Docker Compose**: コンテナ統合
- **Nginx**: リバースプロキシ・ロードバランサー
- **Prometheus + Grafana**: 監視・メトリクス
- **Redis**: セッション・キャッシュ管理

---

## 📋 **開発・運用体制**

### **4賢者連携**
- **📚 ナレッジ賢者**: プロジェクト知識管理・ドキュメント更新
- **📋 タスク賢者**: 開発タスク管理・優先順位制御
- **🚨 インシデント賢者**: 監視・障害対応・自動復旧
- **🔍 RAG賢者**: 技術調査・最適化提案・新技術統合

### **品質管理**
- **TDD**: 全プロジェクトでテスト駆動開発
- **テストカバレッジ**: 90%以上維持
- **CI/CD**: GitHub Actions統合準備中
- **Docker**: 本番環境統一

---

## 🎯 **今後の展開**

### **短期目標 (1週間)**
1. **Docker権限問題完全解決**
2. **全サービスの統一起動**
3. **監視システム統合**

### **中期目標 (1ヶ月)**
1. **CI/CD パイプライン構築**
2. **4賢者システム完全統合**
3. **パフォーマンス最適化**

### **長期ビジョン (3ヶ月)**
1. **Kubernetes移行検討**
2. **マルチクラウド対応**
3. **AI機能強化統合**

---

**🏛️ エルダーズギルドは、技術とビジョンの調和により、持続可能で革新的なプロジェクトポートフォリオを構築している。**
