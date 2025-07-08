#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "=== AI Company クリーンアップ最終結果 ==="
echo ""
echo "📊 プロジェクト統計:"
echo ""
echo "主要ディレクトリ:"
echo "├─ workers/: $(ls -1 workers/*.py 2>/dev/null | grep -v _archived | wc -l) ワーカー"
echo "├─ libs/: $(ls -1 libs/*.py 2>/dev/null | grep -v _archived | wc -l) ライブラリ" 
echo "├─ scripts/: $(ls -1 scripts/*.sh scripts/*.py 2>/dev/null | grep -v _archived | wc -l) スクリプト"
echo "├─ bin/: $(ls -1 bin/ai-* 2>/dev/null | wc -l) コマンド"
echo "├─ core/: $(ls -1 core/*.py 2>/dev/null | wc -l) コアモジュール"
echo "├─ tests/: $(find tests -name "test_*.py" 2>/dev/null | wc -l) テストファイル"
echo "├─ docs/: $(ls -1 docs/*.md 2>/dev/null | wc -l) ドキュメント"
echo "└─ config/: $(ls -1 config/*.json config/*.conf 2>/dev/null | wc -l) 設定ファイル"

echo ""
echo "🗂️ アーカイブ統計:"
total=0
for dir in . workers scripts libs config; do
    if [ -d "$dir/_archived" ]; then
        count=$(find "$dir/_archived" -type f 2>/dev/null | wc -l)
        if [ $count -gt 0 ]; then
            echo "├─ $dir/_archived/: $count ファイル"
            total=$((total + count))
        fi
    fi
done
echo "└─ 合計: $total ファイルをアーカイブ"

echo ""
echo "💾 ディスク使用量:"
du -sh . 2>/dev/null | awk '{print "├─ 合計: " $1}'
du -sh venv 2>/dev/null | awk '{print "├─ venv: " $1}'
du -sh .git 2>/dev/null | awk '{print "├─ .git: " $1}'
du -sh output 2>/dev/null | awk '{print "└─ output: " $1}'

echo ""
echo "✅ クリーンアップ完了!"
echo ""
echo "削除されたもの:"
echo "- 一時的な修正・診断スクリプト"
echo "- 古いテスト関連ファイル"
echo "- 完了済みセットアップスクリプト"
echo "- キャッシュディレクトリ (__pycache__等)"
echo "- 重複したコマンド (bin/とscripts/)"
echo "- 自動生成された不要ファイル"

# Slackに通知
echo ""
echo "Slackに完了通知を送信中..."
