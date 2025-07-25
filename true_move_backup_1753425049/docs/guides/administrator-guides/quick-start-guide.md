---
audience: administrators
author: claude-elder
category: guides
dependencies: []
description: No description available
difficulty: intermediate
last_updated: '2025-07-23'
related_docs: []
reviewers: []
status: approved
subcategory: administrator-guides
tags:
- docker
- python
- guides
title: 契約書アップロードシステム クイックスタートガイド
version: 1.0.0
---

# 契約書アップロードシステム クイックスタートガイド

## 🚀 システムアクセス

### ローカル環境（現在稼働中）
- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8000
- **APIドキュメント**: http://localhost:8000/docs

## ✅ システム状態

### 現在の稼働状況
- ✅ **フロントエンド**: React開発サーバー稼働中（ポート3000）
- ✅ **バックエンド**: FastAPIサーバー稼働中（ポート8000）
- ✅ **データベース**: SQLite（開発用）正常動作
- ⚠️ **Docker**: Buildxプラグインエラーのため未使用（開発サーバーで代替）

## 🎯 使い方

### 1. 契約書アップロードフロー
1. http://localhost:3000 にアクセス
2. 契約タイプを選択（個人 or 法人）
3. 必要書類をアップロード
4. 提出完了

### 2. 管理者機能
1. http://localhost:3000/admin にアクセス
2. アップロードされた契約書の確認・承認

## 📋 対応している契約タイプ

### 個人契約（individual）
- 住民票
- 印鑑登録証明書
- 確定申告書
- 運転免許証
- 通帳コピー

### 法人契約（corporate）
- 登記簿謄本
- 印鑑証明書
- 決算書
- 代表者関連書類

## 🔧 トラブルシューティング

### エラー: "SALES_CONTRACT" 422 Unprocessable Entity
**原因**: 無効な契約タイプ
**解決**: `individual` または `corporate` を使用

### システムが起動しない場合
```bash
# バックエンド再起動
cd /home/aicompany/ai_co/deployment/contract-upload-system/backend
pkill -f "uvicorn app.main:app"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > server.log 2>&1 &

# フロントエンド再起動
cd /home/aicompany/ai_co/deployment/contract-upload-system/frontend
pkill -f "npm start"
npm start > ../frontend.log 2>&1 &
```

## 📝 開発メモ

### 環境変数（.env）
```
DATABASE_URL=sqlite:///./contract_upload.db
SECRET_KEY=your-secret-key-here
FRONTEND_URL=http://localhost:3000
```

### 本番デプロイ
```bash
# デプロイスクリプト実行
cd /home/aicompany/ai_co/deployment/contract-upload-system
./deploy.sh
```

## 🛡️ セキュリティ注意事項
- 開発用の簡易認証を使用中
- 本番環境では適切な認証システムへの置き換えが必要
- アップロードファイルサイズ制限: 30MB
- 対応フォーマット: PDF, JPG, JPEG, PNG

---
**作成**: クロードエルダー
**日付**: 2025年7月12日
**承認**: Elder Flow完全デバッグ実行済み
