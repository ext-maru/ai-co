#!/bin/bash

echo "🚀 FastAPIバックエンドセットアップ開始..."

# Python仮想環境作成
echo "📦 仮想環境を作成しています..."
python3 -m venv venv

# 仮想環境有効化
echo "🔧 仮想環境を有効化しています..."
source venv/bin/activate

# 依存関係インストール
echo "📚 依存関係をインストールしています..."
pip install -r requirements.txt

# データベース初期化
echo "🗄️ データベースを初期化しています..."
python init_db.py

# アップロードディレクトリ作成
echo "📁 アップロードディレクトリを作成しています..."
mkdir -p uploads

echo "✅ セットアップ完了！"
echo ""
echo "🏃 サーバーを起動するには:"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload --port 8001"
