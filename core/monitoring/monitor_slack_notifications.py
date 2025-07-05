#!/usr/bin/env python3
"""
Slack通知の監視スクリプト
過去のログファイルからSlack通知の成功/失敗を分析
"""

import re
from datetime import datetime, timedelta
from collections import Counter
import os

def analyze_slack_logs(log_file="logs/result_worker.log", hours=24):
    """過去N時間のSlack通知状況を分析"""
    
    success_pattern = r"Slack通知送信成功"
    error_pattern = r"Slack通知送信(失敗|エラー)"
    warning_pattern = r"Slack通知送信失敗"
    
    success_count = 0
    error_count = 0
    warning_count = 0
    errors = []
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                # タイムスタンプを抽出
                timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if timestamp_match:
                    timestamp = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                    
                    if timestamp > cutoff_time:
                        if re.search(success_pattern, line):
                            success_count += 1
                        elif re.search(error_pattern, line):
                            error_count += 1
                            errors.append(line.strip())
                        elif re.search(warning_pattern, line):
                            warning_count += 1
                            errors.append(line.strip())
    
    except FileNotFoundError:
        print(f"ログファイル {log_file} が見つかりません")
        return
    
    print(f"=== Slack通知統計 (過去{hours}時間) ===")
    print(f"成功: {success_count}件")
    print(f"失敗: {error_count}件")
    print(f"警告: {warning_count}件")
    
    total = success_count + error_count + warning_count
    if total > 0:
        success_rate = (success_count / total) * 100
        print(f"成功率: {success_rate:.1f}%")
    else:
        print("通知履歴なし")
    
    if errors:
        print("\n最近のエラー/警告:")
        for error in errors[-5:]:  # 最新5件
            print(f"  - {error}")
    
    # タスク処理状況も確認
    print("\n=== タスク処理状況 ===")
    task_pattern = r"結果受信: (\S+) - (\w+)"
    task_counts = Counter()
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                match = re.search(task_pattern, line)
                if match:
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if timestamp_match:
                        timestamp = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                        if timestamp > cutoff_time:
                            status = match.group(2)
                            task_counts[status] += 1
    
        for status, count in task_counts.items():
            print(f"{status}: {count}件")
    
    except Exception as e:
        print(f"タスク処理状況の分析エラー: {e}")

if __name__ == "__main__":
    # コマンドライン引数で時間指定可能にする
    import sys
    
    hours = 24
    if len(sys.argv) > 1:
        try:
            hours = int(sys.argv[1])
        except ValueError:
            print(f"無効な時間指定: {sys.argv[1]}")
            sys.exit(1)
    
    analyze_slack_logs(hours=hours)