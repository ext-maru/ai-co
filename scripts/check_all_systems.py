#!/usr/bin/env python3
"""
AI Company 全システムチェック
"""
import os
import sys
import subprocess
import json
from pathlib import Path
sys.path.append('/root/ai_co')

def check_mark(status):
    return "✅" if status else "❌"

def check_system():
    results = {
        "core": {},
        "features": {},
        "workers": {},
        "libraries": {}
    }
    
    # 1. コアシステム
    print("【コアシステム】")
    
    # RabbitMQ
    try:
        result = subprocess.run(['sudo', 'rabbitmqctl', 'status'], capture_output=True)
        results["core"]["RabbitMQ"] = result.returncode == 0
    except:
        results["core"]["RabbitMQ"] = False
    
    # Claude CLI
    try:
        result = subprocess.run(['which', 'claude'], capture_output=True)
        results["core"]["Claude CLI"] = result.returncode == 0
    except:
        results["core"]["Claude CLI"] = False
    
    # Git設定
    try:
        result = subprocess.run(['git', 'config', 'user.name'], capture_output=True, cwd='/root/ai_co')
        results["core"]["Git設定"] = bool(result.stdout.strip())
    except:
        results["core"]["Git設定"] = False
    
    for name, status in results["core"].items():
        print(f"{check_mark(status)} {name}")
    
    # 2. ワーカー稼働状態
    print("\n【ワーカー】")
    workers = ["task_worker", "pm_worker", "result_worker"]
    for worker in workers:
        ps_result = subprocess.run(['pgrep', '-f', f'{worker}.py'], capture_output=True)
        results["workers"][worker] = ps_result.returncode == 0
        print(f"{check_mark(results['workers'][worker])} {worker}")
    
    # 3. ライブラリ機能
    print("\n【ライブラリ機能】")
    libs_to_check = {
        "RAGマネージャー": "libs.rag_manager.RAGManager",
        "Slack通知": "libs.slack_notifier.SlackNotifier",
        "自己進化": "libs.self_evolution_manager.SelfEvolutionManager",
        "ワーカー監視": "libs.worker_monitor.WorkerMonitor",
        "スケーリング": "libs.scaling_policy.ScalingPolicy",
        "ヘルスチェック": "libs.health_checker.HealthChecker"
    }
    
    for name, module_path in libs_to_check.items():
        try:
            module_name, class_name = module_path.rsplit('.', 1)
            exec(f"from {module_name} import {class_name}")
            results["libraries"][name] = True
        except:
            results["libraries"][name] = False
        print(f"{check_mark(results['libraries'][name])} {name}")
    
    # 4. 機能確認
    print("\n【実装機能】")
    
    # データベース
    db_file = Path("/root/ai_co/task_history.db")
    results["features"]["SQLite DB"] = db_file.exists()
    
    # 設定ファイル
    configs = ["slack.conf", "system.conf", "scaling.conf"]
    config_ok = all(Path(f"/root/ai_co/config/{conf}").exists() for conf in configs)
    results["features"]["設定ファイル"] = config_ok
    
    # 出力ディレクトリ
    output_dir = Path("/root/ai_co/output")
    results["features"]["出力管理"] = output_dir.exists() and any(output_dir.iterdir())
    
    # Slack Webhook
    try:
        with open('/root/ai_co/config/slack.conf', 'r') as f:
            content = f.read()
            results["features"]["Slack設定"] = 'hooks.slack.com' in content
    except:
        results["features"]["Slack設定"] = False
    
    # 自己進化実績
    evolved_files = []
    for pattern in ["workers/*_worker_*.py", "libs/*_manager_*.py", "scripts/evolution_*.py"]:
        evolved_files.extend(Path("/root/ai_co").glob(pattern))
    results["features"]["自己進化実績"] = len(evolved_files) > 0
    
    for name, status in results["features"].items():
        print(f"{check_mark(status)} {name}")
    
    # 5. 統計情報
    print("\n【統計】")
    try:
        from libs.task_history_db import TaskHistoryDB
        db = TaskHistoryDB()
        stats = db.get_stats()
        print(f"📊 タスク総数: {stats.get('total_tasks', 0)}")
        print(f"📁 生成ファイル: {len(list(Path('/root/ai_co/output').rglob('*.py')))}個")
        print(f"🧬 進化ファイル: {len(evolved_files)}個")
    except:
        print("📊 統計取得失敗")
    
    # 総合評価
    total_checks = sum(len(v) for v in results.values())
    passed_checks = sum(sum(v.values()) for v in results.values())
    score = int(passed_checks / total_checks * 100) if total_checks > 0 else 0
    
    print(f"\n【総合評価】")
    print(f"🎯 完成度: {score}% ({passed_checks}/{total_checks})")
    
    if score >= 90:
        print("🎉 AI Company システム完全稼働中！")
    elif score >= 70:
        print("⚠️ 一部機能に問題があります")
    else:
        print("❌ システムに重大な問題があります")
    
    return results

if __name__ == "__main__":
    check_system()
