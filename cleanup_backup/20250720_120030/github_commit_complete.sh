#!/bin/bash
# GitHub Flow コミットスクリプト

cd /home/aicompany/ai_co

# ブランチ作成
gf fix ai-commands-complete-bash

# 変更をステージング
git add scripts/ai_restart_new.sh
git add scripts/ai_start_new.sh
git add scripts/ai_stop_new.sh
git add scripts/start_company.sh
git add complete_fix.sh
git add final_execute.py

# コミット
git commit -m "🔧 [Commands] AI Companyコマンドを完全なbashスクリプトに変換

- ai-restart/ai-start/ai-stopをPython依存なしのbashスクリプトに変更
- base_commandインポートエラーを完全に解決
- tmuxウィンドウインデックス競合を解消
- TestGeneratorWorkerの起動を削除
- 再起動時の確認プロンプトを削除（--force不要）
- start_company.shをクリーンアップ"

echo -e "\n✅ コミット完了！"
echo "PRを作成する場合: gf pr"
