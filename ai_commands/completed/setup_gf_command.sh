#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

# gfコマンドの権限設定
python3 setup_gf_command.py

# エイリアス設定
echo 'alias gf="/home/aicompany/ai_co/scripts/gf"' >> ~/.bashrc

# テスト実行
echo "テスト: gfコマンドのヘルプ表示"
/home/aicompany/ai_co/scripts/gf

echo "✅ gfコマンドのセットアップ完了"
