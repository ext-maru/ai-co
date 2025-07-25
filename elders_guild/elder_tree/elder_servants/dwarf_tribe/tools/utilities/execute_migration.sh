#!/bin/bash
# 実際の移行実行スクリプト

set -e

echo "🚀 AI Company 移行実行"
echo "===================="

# 設定
NEW_USER="aicompany"
NEW_HOME="/home/$NEW_USER"
NEW_PROJECT_DIR="$NEW_HOME/ai_co"

# 1. ユーザー作成
echo "👤 ユーザー作成..."
if ! id "$NEW_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$NEW_USER"
    echo "$NEW_USER:$NEW_USER" | chpasswd
    usermod -aG sudo "$NEW_USER"
fi

# 2. ディレクトリコピー
echo "📁 プロジェクトコピー..."
cp -r /root/ai_co "$NEW_PROJECT_DIR"
chown -R "$NEW_USER:$NEW_USER" "$NEW_PROJECT_DIR"

# 3. 自動パス変換
echo "🔄 パス変換中..."
cd "$NEW_PROJECT_DIR"

# Pythonファイルのsys.path.appendを修正
find . -name "*.py" -type f | while read file; do
    if grep -q "sys.path.append.*root/ai_co" "$file"; then
        # バックアップ
        cp "$file" "${file}.bak"

        # sys.path.append を相対パスに変換
        sed -i "s|sys\.path\.append[^)]*'/root/ai_co'[^)]*)|sys.path.append(str(Path(__file__).parent.parent))|g" "$file"
        sed -i "s|sys\.path\.append[^)]*\"/root/ai_co\"[^)]*)|sys.path.append(str(Path(__file__).parent.parent))|g" "$file"

        # Path import を追加（まだない場合）
        if ! grep -q "from pathlib import Path" "$file"; then
            sed -i '1a from pathlib import Path' "$file"
        fi

        echo "✅ 変換: $file"
    fi
done

# 設定ファイルを修正
sed -i "s|/root/ai_co|$NEW_PROJECT_DIR|g" config/system.conf
echo "✅ 変換: config/system.conf"

# シェルスクリプトを修正
find scripts -name "*.sh" -type f | while read file; do
    if grep -q "/root/ai_co" "$file"; then
        sed -i "s|/root/ai_co|$NEW_PROJECT_DIR|g" "$file"
        echo "✅ 変換: $file"
    fi
done

# 4. 環境設定
echo "⚙️ 環境設定..."
cat << 'BASHRC' >> "$NEW_HOME/.bashrc"

# AI Company
export AI_COMPANY_ROOT="$HOME/ai_co"
export PATH="$AI_COMPANY_ROOT/scripts:$PATH"
alias ai-cd="cd $AI_COMPANY_ROOT"
alias ai-activate="source $AI_COMPANY_ROOT/venv/bin/activate"
alias ai-start="cd $AI_COMPANY_ROOT && ./scripts/ai-start"
alias ai-stop="cd $AI_COMPANY_ROOT && ./scripts/ai-stop"
alias ai-send="cd $AI_COMPANY_ROOT && ./scripts/ai-send"
alias ai-status="cd $AI_COMPANY_ROOT && ./scripts/ai-status"
BASHRC

# 5. Python環境再構築
echo "🐍 Python環境再構築..."
su - "$NEW_USER" -c "
cd $NEW_PROJECT_DIR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
"

# 6. 権限設定
chmod -R 755 "$NEW_PROJECT_DIR"
chmod 600 "$NEW_PROJECT_DIR/config/"*.conf

echo ""
echo "✅ 移行完了！"
echo ""
echo "確認コマンド:"
echo "su - $NEW_USER"
echo "cd ai_co"
echo "grep -r '/root/ai_co' . --exclude-dir=venv --exclude='*.bak' | wc -l  # 0であるべき"
