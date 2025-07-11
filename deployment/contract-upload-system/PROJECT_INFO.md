# 契約書類アップロードシステム - プロジェクト情報

## 📋 プロジェクト概要
- **名前**: 契約書類アップロードシステム (Contract Upload System)
- **技術**: FastAPI + React + PostgreSQL
- **目的**: 契約書類の安全なアップロード・管理・承認システム

## 🌐 デプロイ先
- **サーバ**: 57.181.4.111 (Ubuntu 24.04.2 LTS)
- **アクセス**: http://57.181.4.111/
- **SSH**: `ssh -i server-private.pem ubuntu@57.181.4.111`

## 🐳 Docker構成
- **Backend**: localhost:8000 (FastAPI)
- **Frontend**: localhost:3000 (React)
- **Proxy**: localhost:80 (Nginx)

## 📁 重要なディレクトリ
- **プロジェクト**: `/opt/elders-guild/contract-upload-system/`
- **アップロード**: `/opt/elders-guild/contract-upload-system/uploads/`
- **ログ**: `/opt/elders-guild/contract-upload-system/logs/`
- **設定**: `/opt/elders-guild/contract-upload-system/config/`

## 🔐 SSH情報
詳細は `SERVER_DEPLOYMENT_INFO.md` を参照
