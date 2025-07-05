#!/usr/bin/env python3
"""
ワーカーの健全性を監視し、必要に応じて再起動する
"""
import subprocess
import time
import os
import signal

def check_worker_health():
    """ワーカーの状態をチェック"""
    workers = {
        'task_worker': 2,  # 期待されるインスタンス数
        'result_worker': 1,
        'pm_worker': 1
    }
    
    problems = []
    
    for worker_type, expected_count in workers.items():
        # プロセス数をカウント
        cmd = f"ps aux | grep 'python3 workers/{worker_type}.py' | grep -v grep | wc -l"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        actual_count = int(result.stdout.strip())
        
        if actual_count < expected_count:
            problems.append(f"{worker_type}: {actual_count}/{expected_count} running")
    
    # エラーログをチェック
    error_cmd = "tail -100 /root/ai_co/logs/*.log | grep -c 'Connection reset by peer'"
    result = subprocess.run(error_cmd, shell=True, capture_output=True, text=True)
    recent_errors = int(result.stdout.strip())
    
    if recent_errors > 5:
        problems.append(f"Connection errors: {recent_errors} in recent logs")
    
    return problems

def restart_ai_company():
    """AI Companyを再起動"""
    print("🔄 AI Company を再起動します...")
    
    # 既存のプロセスを停止
    subprocess.run("pkill -f 'python3 workers/'", shell=True)
    time.sleep(2)
    
    # 再起動
    os.chdir('/root/ai_co')
    subprocess.run("bash scripts/start_company.sh", shell=True)
    
    print("✅ 再起動完了")

def main():
    """メイン監視ループ"""
    print("🔍 ワーカー監視を開始します...")
    check_interval = 300  # 5分ごとにチェック
    
    while True:
        problems = check_worker_health()
        
        if problems:
            print(f"⚠️ 問題を検出: {problems}")
            restart_ai_company()
            time.sleep(60)  # 再起動後は1分待機
        else:
            print("✅ すべてのワーカーが正常に動作中")
        
        time.sleep(check_interval)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n監視を終了します")