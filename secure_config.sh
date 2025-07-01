#!/bin/bash
# 設定ファイルのセキュリティ強化

cd /root/ai_co

echo "🔒 設定ファイルの権限を修正..."

# configディレクトリの権限を制限
chmod 700 config/
chmod 600 config/*.conf 2>/dev/null

# credentialsディレクトリも同様に
if [ -d "credentials" ]; then
    chmod 700 credentials/
    chmod 600 credentials/* 2>/dev/null
fi

# .gitignoreに確実に追加
grep -q "credentials/" .gitignore || echo "credentials/" >> .gitignore
grep -q "*.pem" .gitignore || echo "*.pem" >> .gitignore
grep -q "*.key" .gitignore || echo "*.key" >> .gitignore
grep -q ".env" .gitignore || echo ".env" >> .gitignore

echo "✅ 権限設定完了"

# サンプル設定ファイルを作成
echo "📝 サンプル設定ファイルを作成..."
for conf in config/*.conf; do
    sample="${conf}.sample"
    if [ -f "$conf" ] && [ ! -f "$sample" ]; then
        sed -E 's/(password|token|secret|key)\s*=.*/\1=YOUR_\U\1_HERE/gi' "$conf" > "$sample"
        echo "✅ 作成: $sample"
    fi
done

echo "🎯 完了！"

