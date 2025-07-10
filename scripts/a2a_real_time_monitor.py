#!/usr/bin/env python3
"""
A2A（AI-to-AI通信）リアルタイム監視ダッシュボード
"""

import os
import sys
import time
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class A2ARealTimeMonitor:
    """A2Aリアルタイム監視"""
    
    def __init__(self):
        self.db_path = PROJECT_ROOT / "db" / "a2a_monitoring.db"
        self.running = True
        
    def get_real_time_status(self):
        """リアルタイム状態を取得"""
        status = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rabbitmq": "unknown",
            "agents": 0,
            "recent_communications": [],
            "system_health": {},
            "elder_council_activity": ""
        }
        
        # RabbitMQ状態
        try:
            result = subprocess.run(["systemctl", "is-active", "rabbitmq-server"], 
                                   capture_output=True, text=True)
            status["rabbitmq"] = result.stdout.strip()
        except:
            status["rabbitmq"] = "error"
        
        # エージェント数
        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            status["agents"] = len([line for line in result.stdout.split('\n') 
                                   if any(keyword in line.lower() for keyword in 
                                         ['elder', 'sage', 'council'])])
        except:
            pass
        
        # 最新通信記録
        if self.db_path.exists():
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT timestamp, source_agent, target_agent, message_type, status
                        FROM a2a_communications 
                        ORDER BY timestamp DESC LIMIT 5
                    """)
                    status["recent_communications"] = [
                        {
                            "time": row[0][-8:],  # 時刻のみ
                            "path": f"{row[1]} → {row[2]}",
                            "type": row[3],
                            "status": row[4]
                        }
                        for row in cursor.fetchall()
                    ]
            except:
                pass
        
        # エルダー評議会の最新活動
        try:
            council_files = list(PROJECT_ROOT.glob("knowledge_base/*council*request*.md"))
            if council_files:
                latest = max(council_files, key=lambda x: x.stat().st_mtime)
                mod_time = datetime.fromtimestamp(latest.stat().st_mtime)
                status["elder_council_activity"] = f"最新要請: {mod_time.strftime('%H:%M:%S')}"
            else:
                status["elder_council_activity"] = "評議会要請なし"
        except:
            status["elder_council_activity"] = "確認不可"
        
        return status
    
    def display_dashboard(self):
        """ダッシュボード表示"""
        while self.running:
            # 画面クリア
            os.system('clear' if os.name == 'posix' else 'cls')
            
            status = self.get_real_time_status()
            
            print("🤖 A2A（AI-to-AI通信）リアルタイム監視ダッシュボード")
            print("=" * 70)
            print(f"📅 更新時刻: {status['timestamp']}")
            print()
            
            # システム状態
            print("🔍 システム状態:")
            rabbitmq_emoji = "✅" if status["rabbitmq"] == "active" else "❌"
            print(f"  {rabbitmq_emoji} RabbitMQ: {status['rabbitmq']}")
            print(f"  👥 エージェント: {status['agents']}個")
            print(f"  🏛️ {status['elder_council_activity']}")
            print()
            
            # 最新通信
            print("📡 最新通信記録:")
            if status["recent_communications"]:
                for comm in status["recent_communications"]:
                    status_emoji = "✅" if comm["status"] == "success" else "❌"
                    print(f"  {status_emoji} [{comm['time']}] {comm['path']} ({comm['type']})")
            else:
                print("  📭 通信記録なし")
            print()
            
            # A2A実装状況
            print("📋 A2A実装状況:")
            a2a_files = [
                ("コア通信", "libs/a2a_communication.py"),
                ("管理コマンド", "commands/ai_a2a.py"),
                ("最適化", "libs/elder_servant_a2a_optimization.py"),
                ("デモ", "examples/four_sages_a2a_demo.py")
            ]
            
            for name, file_path in a2a_files:
                if (PROJECT_ROOT / file_path).exists():
                    print(f"  ✅ {name}: 実装済み")
                else:
                    print(f"  ❌ {name}: 未実装")
            print()
            
            # データベース状況
            if self.db_path.exists():
                try:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.execute("SELECT COUNT(*) FROM a2a_communications")
                        comm_count = cursor.fetchone()[0]
                        
                        cursor = conn.execute("SELECT COUNT(*) FROM system_health")
                        health_count = cursor.fetchone()[0]
                        
                        print("💾 監視データベース:")
                        print(f"  📊 通信記録: {comm_count}件")
                        print(f"  🏥 ヘルス記録: {health_count}件")
                except:
                    print("💾 監視データベース: エラー")
            else:
                print("💾 監視データベース: 未作成")
            print()
            
            # 推奨アクション
            recommendations = []
            if status["rabbitmq"] != "active":
                recommendations.append("RabbitMQを起動してください")
            if status["agents"] == 0:
                recommendations.append("エージェントプロセスを確認してください")
            if not status["recent_communications"]:
                recommendations.append("A2A通信テストを実行してください")
            
            if recommendations:
                print("💡 推奨アクション:")
                for rec in recommendations[:3]:  # 最大3件
                    print(f"  - {rec}")
            else:
                print("✅ システム正常動作中")
            
            print()
            print("🔄 10秒後に更新... (Ctrl+C で終了)")
            print("=" * 70)
            
            try:
                time.sleep(10)
            except KeyboardInterrupt:
                self.running = False
                print("\n监视停止中...")

def main():
    """メイン処理"""
    monitor = A2ARealTimeMonitor()
    
    print("A2Aリアルタイム監視を開始します...")
    print("Ctrl+C で終了できます。")
    time.sleep(2)
    
    try:
        monitor.display_dashboard()
    except KeyboardInterrupt:
        pass
    finally:
        print("A2Aリアルタイム監視を終了しました。")

if __name__ == "__main__":
    main()