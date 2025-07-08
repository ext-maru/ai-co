#!/bin/bash
# AI Company 日本語化 - AI Command Executor用

cd /home/aicompany/ai_co
source venv/bin/activate

echo "🌏 AI Company 日本語化セットアップ開始..."

# Pythonスクリプト実行
python3 setup_japanese.py

echo "✅ セットアップ完了！"
