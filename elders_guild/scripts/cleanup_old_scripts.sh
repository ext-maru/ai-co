#!/bin/bash
# 不要なスクリプトをアーカイブに移動

cd /home/aicompany/ai_co/scripts

# アーカイブディレクトリ作成（既存の場合はスキップ）
mkdir -p _archived

echo "=== 診断・修正系を移動 ==="
mv -f diagnose_tests.py _archived/ 2>/dev/null
mv -f fix_pm_worker_conflict.py _archived/ 2>/dev/null
mv -f fix_message_format.sh _archived/ 2>/dev/null
mv -f fix_ai_send.sh _archived/ 2>/dev/null
mv -f fix_conftest.py _archived/ 2>/dev/null
mv -f check_and_start_pm_worker.sh _archived/ 2>/dev/null
mv -f check_pm_test_details.sh _archived/ 2>/dev/null
mv -f monitor_task_processing.sh _archived/ 2>/dev/null

echo "=== 古いテスト関連を移動 ==="
mv -f test-system-check.sh _archived/ 2>/dev/null
mv -f test_enhanced_git.sh _archived/ 2>/dev/null
mv -f test_pm_direct.py _archived/ 2>/dev/null
mv -f test_pm_worker.py _archived/ 2>/dev/null
mv -f setup-and-test.sh _archived/ 2>/dev/null
mv -f setup-test-system.sh _archived/ 2>/dev/null
mv -f ai-test-fixed _archived/ 2>/dev/null
mv -f ai-test-autofix _archived/ 2>/dev/null
mv -f install-test-deps.sh _archived/ 2>/dev/null

echo "=== セットアップ・移行スクリプトを移動 ==="
mv -f setup_github.sh _archived/ 2>/dev/null
mv -f migrate_to_gitflow.sh _archived/ 2>/dev/null
mv -f update_pm_worker_with_tests.sh _archived/ 2>/dev/null
mv -f update_pm_gitflow.sh _archived/ 2>/dev/null
mv -f integrate_prompt_templates.sh _archived/ 2>/dev/null
mv -f apply_log_improvements.sh _archived/ 2>/dev/null
mv -f migrate_logs_gradually.sh _archived/ 2>/dev/null
mv -f evolution_code_20250630_151544_0.sh _archived/ 2>/dev/null

echo "=== Slack関連の古いスクリプトを移動 ==="
mv -f setup_slack_integration.sh _archived/ 2>/dev/null
mv -f slack_setup_interactive.py _archived/ 2>/dev/null
mv -f detect_slack_config.py _archived/ 2>/dev/null
mv -f debug_slack.py _archived/ 2>/dev/null
mv -f check_slack_status.py _archived/ 2>/dev/null

echo "=== 一時的なスクリプトを移動 ==="
mv -f quick_check_executor.sh _archived/ 2>/dev/null
mv -f send_test_task.py _archived/ 2>/dev/null
mv -f setup_dialog_queues.py _archived/ 2>/dev/null
mv -f conversation_health_check.py _archived/ 2>/dev/null
mv -f check_executor_status.py _archived/ 2>/dev/null

echo "=== 古い起動スクリプトを移動 ==="
mv -f start-quality-system.sh _archived/ 2>/dev/null
mv -f status.sh _archived/ 2>/dev/null

echo "=== その他未使用・重複を移動 ==="
mv -f review_all_commands.sh _archived/ 2>/dev/null
mv -f cleanup_commands.py _archived/ 2>/dev/null
mv -f notify_kb_update.sh _archived/ 2>/dev/null
mv -f create_prompt_template_docs.sh _archived/ 2>/dev/null
mv -f setup_new_commands.sh _archived/ 2>/dev/null

echo "=== すべての対象ファイルを確実に移動 ==="
# リストにあるファイルを再度確認して移動
for file in fix_conftest.py fix_message_format.sh fix_ai_send.sh check_and_start_pm_worker.sh check_pm_test_details.sh monitor_task_processing.sh test_enhanced_git.sh test_pm_direct.py test_pm_worker.py setup-and-test.sh setup-test-system.sh ai-test-fixed ai-test-autofix install-test-deps.sh setup_github.sh migrate_to_gitflow.sh update_pm_worker_with_tests.sh update_pm_gitflow.sh integrate_prompt_templates.sh apply_log_improvements.sh migrate_logs_gradually.sh evolution_code_20250630_151544_0.sh setup_slack_integration.sh slack_setup_interactive.py detect_slack_config.py debug_slack.py check_slack_status.py quick_check_executor.sh send_test_task.py setup_dialog_queues.py conversation_health_check.py check_executor_status.py start-quality-system.sh status.sh review_all_commands.sh cleanup_commands.py notify_kb_update.sh create_prompt_template_docs.sh setup_new_commands.sh; do
  [ -f "$file" ] && mv -f "$file" _archived/ 2>/dev/null && echo "Moved: $file"
done

echo ""
echo "=== 整理完了 ==="
echo "アーカイブされたファイル数:"
ls _archived/ | wc -l

echo ""
echo "現在のスクリプト数:"
ls -1 *.sh *.py 2>/dev/null | grep -v "_archived" | wc -l
