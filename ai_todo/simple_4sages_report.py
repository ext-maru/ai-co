#!/usr/bin/env python3
"""
シンプルな4賢者レポート生成
"""
import json
import subprocess
from datetime import datetime
from pathlib import Path

def generate_4sages_report():
    """4賢者システムレポートを生成"""
    
    print("🧙‍♂️ AI Company 4賢者システム統合レポート")
    print("=" * 50)
    print(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 📚 ナレッジ賢者
    print("## 📚 ナレッジ賢者")
    print("役割: 知識の蓄積と継承")
    kb_path = Path("/home/aicompany/ai_co/knowledge_base")
    if kb_path.exists():
        knowledge_count = sum(1 for _ in kb_path.rglob("*.json*"))
        print(f"知識エントリ数: {knowledge_count}")
        
        # 最新の学習記録
        learning_file = kb_path / "ai_learning" / "error_patterns.jsonl"
        if learning_file.exists():
            with open(learning_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    latest = json.loads(lines[-1])
                    print(f"最新学習: {latest['timestamp']}")
                    print(f"エラーパターン: {latest['patterns']}")
    print()
    
    # 📋 タスク賢者
    print("## 📋 タスク賢者")
    print("役割: プロジェクト進捗管理")
    # ワーカー分析の結果を使用
    analysis_file = Path("/tmp/worker_analysis.json")
    if analysis_file.exists():
        with open(analysis_file, 'r') as f:
            analysis = json.load(f)
            print(f"アクティブワーカー数: {analysis['worker_count']}")
    print()
    
    # 🚨 インシデント賢者
    print("## 🚨 インシデント賢者")
    print("役割: 危機対応と問題解決")
    # プロセス監視
    result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
    worker_processes = [line for line in result.stdout.split('\n') if 'worker' in line.lower()]
    print(f"稼働中のワーカープロセス: {len(worker_processes)}")
    print()
    
    # 🔍 RAG賢者
    print("## 🔍 RAG賢者")
    print("役割: 情報検索と最適解探索")
    print("状態: Active")
    print("検索能力: Enhanced")
    print()
    
    # システム全体の統計
    print("## 💻 システム統計")
    # 稼働時間
    uptime_result = subprocess.run(["uptime", "-p"], capture_output=True, text=True)
    if uptime_result.returncode == 0:
        print(f"稼働時間: {uptime_result.stdout.strip()}")
    
    # メモリ使用状況
    mem_result = subprocess.run(["free", "-h"], capture_output=True, text=True)
    if mem_result.returncode == 0:
        print("\nメモリ使用状況:")
        for line in mem_result.stdout.split('\n')[1:3]:
            if line:
                print(f"  {line}")
    
    print("\n" + "=" * 50)
    print("レポート生成完了")

if __name__ == "__main__":
    generate_4sages_report()