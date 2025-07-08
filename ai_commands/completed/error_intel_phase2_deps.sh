#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "📦 必要なパッケージをチェック..."

# 必要に応じてパッケージをインストール
pip show colorama >/dev/null 2>&1 || pip install colorama

echo "✅ 依存関係確認完了"
