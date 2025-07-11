# 🏛️ Upload Image Service - エルダーズギルド専用知識ベース

## 📚 **ナレッジ賢者 - プロジェクト知識体系**

### 🎯 **プロジェクト概要**
- **名称**: Upload Image Service (契約書類アップロードシステム)
- **目的**: 2段階契約システムの簡素化 + Google Drive連携
- **アーキテクチャ**: React Frontend + FastAPI Backend + Google Drive API
- **ユーザー**: 管理者駆動型（セッション作成→URL送信→提出者アップロード）

### 🔧 **技術スタック詳細**

#### **Frontend実装完了** ✅
```
技術: React 18.2.0 + JavaScript
構造: SPA (Single Page Application)
ポート: 3002
状態管理: useState/useEffect hooks
CSS: モダンCSS Grid/Flexbox + カスタムスタイル
```

#### **Backend実装予定** 🚧
```
技術: FastAPI + SQLAlchemy
データベース: SQLite → PostgreSQL (本番)
認証: JWT (簡易開発用)
ポート: 8001 (本番), 8002 (モック)
```

### 🗂️ **データ構造設計**

#### **SubmissionSession テーブル**
```sql
CREATE TABLE submission_sessions (
    id VARCHAR PRIMARY KEY,
    submitter_name VARCHAR NOT NULL,
    submitter_email VARCHAR NOT NULL,
    submission_type ENUM('individual', 'corporate'),
    status ENUM('not_uploaded', 'needs_reupload', 'approved'),
    description TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### **UploadedFile テーブル**
```sql
CREATE TABLE uploaded_files (
    id VARCHAR PRIMARY KEY,
    session_id VARCHAR REFERENCES submission_sessions(id),
    filename VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR,
    uploaded_at TIMESTAMP
);
```

### 🔄 **ワークフロー設計**

#### **管理者フロー**
1. セッション作成 (name, email, type, description)
2. URL生成 (`/submission/{session_id}`)
3. 提出者にURL送信
4. アップロード状況監視
5. ファイル確認→ステータス更新

#### **提出者フロー**
1. URL受信・アクセス
2. 必要書類確認
3. ファイル選択（ドラッグ&ドロップ対応）
4. アップロード実行
5. 結果確認

### 🌐 **Google Drive連携仕様**

#### **フォルダ構造**
```
📁 契約書類アップロード (親フォルダ)
├── 📁 [session_001]_田中太郎
│   ├── 📄 住民票.pdf
│   └── 📄 身分証明書.jpg
├── 📁 [session_002]_佐藤商事株式会社
│   ├── 📄 登記簿謄本.pdf
│   └── 📄 代表者身分証.jpg
└── 📁 アーカイブ
```

#### **権限管理**
- **サービスアカウント**: 編集権限
- **提出者**: 読み取り権限（自動付与）
- **管理者**: 所有者権限

## 📋 **タスク賢者 - 開発管理**

### 🎯 **開発フェーズ計画**

#### **Phase 1: Backend基盤構築** (優先度: HIGH)
- [ ] FastAPI プロジェクト初期化
- [ ] SQLAlchemy モデル定義
- [ ] データベース マイグレーション
- [ ] 基本CRUD API実装
- [ ] モックから本格実装への移行

#### **Phase 2: Google Drive連携** (優先度: MEDIUM)
- [ ] Google Drive API認証実装
- [ ] フォルダ自動作成機能
- [ ] ファイルアップロード機能
- [ ] 権限管理システム

#### **Phase 3: 本番環境準備** (優先度: LOW)
- [ ] Docker化完了
- [ ] 環境変数管理
- [ ] ログ管理システム
- [ ] デプロイ自動化

### 📊 **進捗追跡**

#### **完了済みタスク**
- ✅ React Frontend完全実装
- ✅ Mock API Server構築
- ✅ Git管理システム確立
- ✅ Google Drive設定UI完成
- ✅ プロジェクト知識体系化

#### **現在のボトルネック**
- 🚧 FastAPI実装未着手
- 🚧 データベース設計未完成
- 🚧 Google Drive API未実装

## 🚨 **インシデント賢者 - 問題管理**

### 🔍 **既知の問題・解決済み**

#### **webpack html-webpack-plugin エラー**
- **発生**: 2025-07-11 初期実装時
- **原因**: 旧webpack構成の互換性問題
- **解決**: 新React構造での完全再構築
- **予防**: react-scripts 5.0.1使用

#### **Failed to fetch エラー**
- **発生**: 2025-07-11 ファイルアップロード時
- **原因**: multipart/form-data処理不完全
- **解決**: Mock API Server改良
- **予防**: 適切なCORS設定・エラーハンドリング

#### **セッション作成ループ**
- **発生**: 2025-07-11 「作成中...」状態
- **原因**: API接続エラー
- **解決**: Mock API実装
- **予防**: 接続テスト機能実装

### 🛡️ **予防策・監視項目**
- API接続状況の継続監視
- ファイルアップロード成功率追跡
- Google Drive接続ステータス確認
- メモリ使用量監視

## 🔍 **RAG賢者 - 技術調査**

### 📚 **技術選定根拠**

#### **FastAPI選定理由**
- **パフォーマンス**: 高速なAPI応答
- **型安全性**: Pydantic統合
- **開発効率**: 自動ドキュメント生成
- **エコシステム**: SQLAlchemy連携

#### **SQLAlchemy選定理由**
- **ORM機能**: データベース抽象化
- **マイグレーション**: Alembic統合
- **型安全性**: Python型ヒント対応
- **拡張性**: 複数DB対応

#### **Google Drive API選定理由**
- **利便性**: 使い慣れたインターフェース
- **権限管理**: 細かい権限制御
- **容量**: 大容量ファイル対応
- **検索性**: 高度な検索機能

### 🎯 **最適化提案**

#### **パフォーマンス最適化**
- **非同期処理**: ファイルアップロード並行処理
- **キャッシュ**: セッション情報キャッシュ
- **圧縮**: ファイル圧縮機能
- **CDN**: 静的ファイル配信最適化

#### **セキュリティ強化**
- **認証**: JWT + リフレッシュトークン
- **暗号化**: ファイル保存時暗号化
- **監査**: アクセスログ記録
- **バリデーション**: 入力値検証強化

## 🎮 **エルダーズ協調システム起動**

### 🤖 **4賢者連携フロー**

#### **開発タスク自動分散**
1. **ナレッジ賢者**: 技術文書・設計書自動更新
2. **タスク賢者**: 開発進捗自動追跡・優先度調整
3. **インシデント賢者**: エラー発生時自動対応・学習
4. **RAG賢者**: 最適化提案・技術調査自動実行

#### **品質保証システム**
- **コード品質**: 自動レビュー・リファクタリング提案
- **テスト**: 自動テスト生成・実行
- **パフォーマンス**: ベンチマーク・最適化提案
- **セキュリティ**: 脆弱性検出・修正提案

---

**🏛️ エルダーズギルド総合司令部**
**更新日**: 2025-07-11
**管理者**: Claude Elder
**プロジェクト**: Upload Image Service
**フェーズ**: Backend実装準備完了
