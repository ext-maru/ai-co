#!/bin/bash
# AI Company Command Aliases - Current Legacy Support
# This file provides backward compatibility during command migration

# Core system commands (most frequently used)
alias ai-send='python3 commands/ai_send.py'
alias ai-start='python3 commands/ai_start.py'
alias ai-stop='python3 commands/ai_stop.py'
alias ai-status='python3 commands/ai_status.py'
alias ai-health='python3 commands/ai_health.py'
alias ai-monitor='python3 commands/ai_monitor.py'
alias ai-backup='python3 commands/ai_backup.py'

# Task management
alias ai-tasks='python3 commands/ai_tasks.py'
alias ai-task-info='python3 commands/ai_task_info.py'
alias ai-task-retry='python3 commands/ai_task_retry.py'
alias ai-task-cancel='python3 commands/ai_task_cancel.py'
alias ai-queue='python3 commands/ai_queue.py'
alias ai-queue-clear='python3 commands/ai_queue_clear.py'

# Worker management
alias ai-workers='python3 commands/ai_workers.py'
alias ai-worker-add='python3 commands/ai_worker_add.py'
alias ai-worker-remove='python3 commands/ai_worker_rm.py'
alias ai-worker-restart='python3 commands/ai_worker_restart.py'
alias ai-worker-recover='python3 commands/ai_worker_recovery.py'
alias ai-worker-comm='python3 commands/ai_worker_comm.py'
alias ai-worker-scale='python3 commands/ai_worker_scale.py'

# Development tools
alias ai-logs='python3 commands/ai_logs.py'
alias ai-test='python3 commands/ai_test.py'
alias ai-debug='python3 commands/ai_debug.py'
alias ai-clean='python3 commands/ai_clean.py'

# Knowledge and AI
alias ai-knowledge='python3 commands/ai_knowledge.py'
alias ai-rag='python3 commands/ai_rag.py'
alias ai-rag-search='python3 commands/ai_rag_search.py'
alias ai-learn='python3 commands/ai_learn.py'
alias ai-evolve='python3 commands/ai_evolve.py'
alias ai-evolve-daily='python3 commands/ai_evolve_daily.py'
alias ai-evolve-test='python3 commands/ai_evolve_test.py'

# Elder Council and governance
alias ai-elder-council='python3 commands/ai_elder_council.py'
alias ai-elder-pm='python3 commands/ai_elder_pm.py'
alias ai-elder-proactive='python3 commands/ai_elder_proactive.py'
alias ai-grand-elder='python3 commands/ai_grand_elder.py'
alias ai-incident-knights='python3 commands/ai_incident_knights.py'

# Configuration and system
alias ai-config='python3 commands/ai_config.py'
alias ai-config-edit='python3 commands/ai_config_edit.py'
alias ai-config-reload='python3 commands/ai_config_reload.py'
alias ai-update='python3 commands/ai_update.py'
alias ai-version='python3 commands/ai_version.py'

# Documentation and reporting
alias ai-document='python3 commands/ai_document.py'
alias ai-report='python3 commands/ai_report.py'
alias ai-report-manager='python3 commands/ai_report_manager.py'
alias ai-stats='python3 commands/ai_stats.py'
alias ai-metrics='python3 commands/ai_metrics.py'

# Interface and web
alias ai-webui='python3 commands/ai_webui.py'
alias ai-help='python3 commands/ai_help.py'
alias ai-shell='python3 commands/ai_shell.py'

# Integration
alias ai-docker='python3 commands/ai_docker.py'

# Convenience shortcuts (ultra-short aliases)
alias ais='ai-status'          # ai status
alias ait='ai-send'            # ai task send
alias aiw='ai-workers'         # ai workers
alias ail='ai-logs'            # ai logs
alias aih='ai-help'            # ai help
alias aiq='ai-queue'           # ai queue
alias aie='ai-elder-council'   # ai elder
alias air='ai-report'          # ai report

# Domain command helpers (show available commands)
alias ai-system-help='echo "Available system commands: start stop status health monitor backup update config restart reset"'
alias ai-task-help='echo "Available task commands: send list info retry cancel queue simulate priority schedule"'
alias ai-worker-help='echo "Available worker commands: list add remove restart scale recover monitor comm health stats"'
alias ai-elder-help='echo "Available elder commands: council pm compliance proactive summon consult decision"'
alias ai-dev-help='echo "Available dev commands: test tdd coverage codegen debug logs clean lint format"'

# Script-based commands (existing in scripts/ directory)
alias ai-send-script='scripts/ai-send'
alias ai-start-script='scripts/ai-start'
alias ai-stop-script='scripts/ai-stop'
alias ai-status-script='scripts/ai-status'

# Load command completion if available
if [ -f "$AI_COMPANY_ROOT/ai_commands/completions.bash" ]; then
    source "$AI_COMPANY_ROOT/ai_commands/completions.bash"
fi

# Export functions for use in subshells
export -f ai-system-help ai-task-help ai-worker-help ai-elder-help ai-dev-help

# Migration status notification
echo "🔄 AI Company commands are being standardized. See 'docs/AI_COMPANY_COMMAND_NAMING_STANDARD.md' for details."
alias start_slack_diagnosis='bash /home/aicompany/ai_co/ai_commands/start_slack_diagnosis.sh'