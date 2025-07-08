#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
chmod +x deep_cleanup_all.sh
./deep_cleanup_all.sh

# クリーンアップスクリプト自体も削除
rm -f cleanup_root_directory.sh deep_cleanup_all.sh execute_full_cleanup.py execute_cleanup.py
rm -f run_cleanup.py run_final_cleanup.py check_scripts_status.py check_final_result.py
rm -f execute_archive.py

echo ""
echo "=== 全てのクリーンアップが完了しました！ ==="
echo ""
echo "プロジェクトがクリーンになりました 🎉"
