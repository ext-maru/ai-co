#!/bin/bash
# Issue #184 Phase 2: NLPライブラリのインストール

echo "🔧 Installing NLP libraries for Issue Understanding Engine..."

# Pythonバージョン確認
python3 --version

# pipのアップグレード
echo "📦 Upgrading pip..."
python3 -m pip install --upgrade pip

# spaCyのインストール
echo "🧠 Installing spaCy..."
python3 -m pip install spacy

# spaCyの英語モデルをダウンロード
echo "📥 Downloading spaCy English model..."
python3 -m spacy download en_core_web_sm

# transformersのインストール（軽量版）
echo "🤖 Installing transformers (lightweight)..."
python3 -m pip install transformers

# 追加の依存関係
echo "📚 Installing additional dependencies..."
python3 -m pip install nltk textblob

echo "✅ NLP libraries installation complete!"

# インストール確認
echo ""
echo "📋 Checking installations:"
python3 -c "import spacy; print(f'✓ spaCy version: {spacy.__version__}')"
python3 -c "import transformers; print(f'✓ transformers version: {transformers.__version__}')"
python3 -c "import nltk; print(f'✓ NLTK version: {nltk.__version__}')"
python3 -c "import textblob; print(f'✓ TextBlob version: {textblob.__version__}')"