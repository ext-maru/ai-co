#!/usr/bin/env python3
"""
ai-health: AI Company 詳細ヘルスチェックコマンド
"""
import json
import psutil
import socket
from datetime import datetime, timedelta
from pathlib import Path
from commands.base_command import BaseCommand

class HealthCommand(BaseCommand):
    def __init__(self):
        super().__init__(
            name="health",
            description="AI Company システムの詳細なヘルスチェックを実行します"
        )
        
    def setup_arguments(self):
        self.parser.add_argument(
            '--json',
            action='store_true',
            help='JSON形式で出力'
        )
        self.parser.add_argument(
            '--fix',
            action='store_true',
            help='問題を自動修復する'
        )
        
    def check_system_resources(self):
        """システムリソースチェック"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # メモリ
            memory = psutil.virtual_memory()
            
            # ディスク
            disk = psutil.disk_usage(str(self.project_root))
            
            return {
                'cpu': {
                    'usage_percent': cpu_percent,
                    'cores': cpu_count,
                    'status': 'ok' if cpu_percent < 80 else 'warning' if cpu_percent < 95 else 'critical'
                },
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'percent': memory.percent,
                    'status': 'ok' if memory.percent < 80 else 'warning' if memory.percent < 95 else 'critical'
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'used_gb': round(disk.used / (1024**3), 2),
                    'percent': disk.percent,
                    'status': 'ok' if disk.percent < 80 else 'warning' if disk.percent < 95 else 'critical'
                }
            }
        except Exception as e:
            return {'error': str(e)}
            
    def check_services(self):
        """サービス状態チェック"""
        services = {}
        
        # RabbitMQ
        result = self.run_command(['systemctl', 'is-active', 'rabbitmq-server'])
        services['rabbitmq'] = {
            'status': 'running' if result and result.stdout.strip() == 'active' else 'stopped',
            'healthy': result and result.stdout.strip() == 'active'
        }
        
        # RabbitMQポート確認
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', 5672))
            sock.close()
            services['rabbitmq']['port_5672'] = 'open' if result == 0 else 'closed'
        except:
            services['rabbitmq']['port_5672'] = 'error'
            
        # PostgreSQL（もし使っている場合）
        result = self.run_command(['systemctl', 'is-active', 'postgresql'])
        if result:
            services['postgresql'] = {
                'status': 'running' if result.stdout.strip() == 'active' else 'stopped',
                'healthy': result.stdout.strip() == 'active'
            }
            
        return services
        
    def check_workers(self):
        """ワーカー詳細チェック"""
        worker_info = {
            'task_worker': {'name': 'タスクワーカー', 'expected': 2, 'processes': []},
            'pm_worker': {'name': 'PMワーカー', 'expected': 1, 'processes': []},
            'result_worker': {'name': '結果ワーカー', 'expected': 1, 'processes': []},
            'dialog_task_worker': {'name': '対話ワーカー', 'expected': 0, 'processes': []},
            'dialog_pm_worker': {'name': '対話PMワーカー', 'expected': 0, 'processes': []}
        }
        
        for worker_type, info in worker_info.items():
            processes = self.check_process(worker_type)
            info['actual'] = len(processes)
            info['healthy'] = info['actual'] >= info['expected'] if info['expected'] > 0 else True
            
            # プロセス詳細
            for proc in processes:
                try:
                    # psutilでより詳細な情報を取得
                    p = psutil.Process(int(proc['pid']))
                    info['processes'].append({
                        'pid': proc['pid'],
                        'cpu_percent': p.cpu_percent(),
                        'memory_mb': round(p.memory_info().rss / (1024*1024), 2),
                        'create_time': datetime.fromtimestamp(p.create_time()).isoformat(),
                        'status': p.status()
                    })
                except:
                    info['processes'].append(proc)
                    
        return worker_info
        
    def check_queues(self):
        """キュー詳細チェック"""
        queue_info = {}
        conn = self.get_rabbitmq_connection()
        
        if conn:
            try:
                channel = conn.channel()
                queues = [
                    ('task_queue', 10),  # 警告閾値
                    ('result_queue', 20),
                    ('pm_queue', 10),
                    ('dialog_task_queue', 5),
                    ('dialog_response_queue', 5),
                    ('user_input_queue', 5)
                ]
                
                for queue_name, threshold in queues:
                    try:
                        method = channel.queue_declare(queue=queue_name, passive=True)
                        count = method.method.message_count
                        queue_info[queue_name] = {
                            'messages': count,
                            'threshold': threshold,
                            'healthy': count < threshold,
                            'status': 'ok' if count < threshold else 'warning' if count < threshold * 2 else 'critical'
                        }
                    except:
                        queue_info[queue_name] = {
                            'messages': -1,
                            'healthy': False,
                            'status': 'error'
                        }
                        
                conn.close()
            except Exception as e:
                return {'error': str(e)}
                
        return queue_info
        
    def check_logs(self):
        """ログファイルチェック"""
        log_info = {}
        log_files = {
            'task_worker.log': 50,  # MB
            'pm_worker.log': 20,
            'result_worker.log': 20,
            'dialog_task_worker.log': 20,
            'dialog_pm_worker.log': 20
        }
        
        for log_file, max_size_mb in log_files.items():
            log_path = self.logs_dir / log_file
            if log_path.exists():
                size_mb = log_path.stat().st_size / (1024 * 1024)
                
                # 最新のエラーをチェック
                recent_errors = 0
                try:
                    with open(log_path, 'r', encoding='utf-8') as f:
                        # 最後の1000行をチェック
                        lines = f.readlines()[-1000:]
                        for line in lines:
                            if 'ERROR' in line or 'error' in line:
                                recent_errors += 1
                except:
                    pass
                    
                log_info[log_file] = {
                    'exists': True,
                    'size_mb': round(size_mb, 2),
                    'max_size_mb': max_size_mb,
                    'recent_errors': recent_errors,
                    'healthy': size_mb < max_size_mb and recent_errors < 10,
                    'status': 'ok' if size_mb < max_size_mb and recent_errors < 10 else 'warning'
                }
            else:
                log_info[log_file] = {
                    'exists': False,
                    'healthy': True,
                    'status': 'ok'
                }
                
        return log_info
        
    def check_database(self):
        """データベースチェック"""
        db_info = {}
        
        # conversations.db
        conv_db = self.project_root / "conversations.db"
        if conv_db.exists():
            size_mb = conv_db.stat().st_size / (1024 * 1024)
            
            # 接続テスト
            conn = self.get_db_connection("conversations.db")
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM conversations")
                    conv_count = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM conversation_messages")
                    msg_count = cursor.fetchone()[0]
                    
                    conn.close()
                    
                    db_info['conversations.db'] = {
                        'exists': True,
                        'size_mb': round(size_mb, 2),
                        'conversations': conv_count,
                        'messages': msg_count,
                        'healthy': True,
                        'status': 'ok'
                    }
                except Exception as e:
                    db_info['conversations.db'] = {
                        'exists': True,
                        'error': str(e),
                        'healthy': False,
                        'status': 'error'
                    }
            else:
                db_info['conversations.db'] = {
                    'exists': True,
                    'healthy': False,
                    'status': 'error'
                }
        else:
            db_info['conversations.db'] = {
                'exists': False,
                'healthy': True,
                'status': 'ok'
            }
            
        return db_info
        
    def calculate_overall_health(self, health_data):
        """全体的なヘルススコア計算"""
        scores = {
            'critical': 0,
            'warning': 0,
            'ok': 0,
            'total': 0
        }
        
        # 各チェック項目を確認
        for category, data in health_data.items():
            if isinstance(data, dict):
                for item, info in data.items():
                    if isinstance(info, dict) and 'status' in info:
                        scores['total'] += 1
                        status = info['status']
                        if status == 'critical' or status == 'error':
                            scores['critical'] += 1
                        elif status == 'warning':
                            scores['warning'] += 1
                        elif status == 'ok':
                            scores['ok'] += 1
                            
        # スコア計算（100点満点）
        if scores['total'] > 0:
            health_score = (scores['ok'] * 100 + scores['warning'] * 50) / scores['total']
        else:
            health_score = 0
            
        # 状態判定
        if scores['critical'] > 0:
            overall_status = 'critical'
        elif scores['warning'] > 2:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
            
        return {
            'score': round(health_score, 1),
            'status': overall_status,
            'summary': scores
        }
        
    def display_health_report(self, health_data):
        """ヘルスレポート表示"""
        overall = health_data['overall']
        
        # ヘッダー
        if overall['status'] == 'healthy':
            self.success(f"システムヘルススコア: {overall['score']}/100 - 正常")
        elif overall['status'] == 'warning':
            self.warning(f"システムヘルススコア: {overall['score']}/100 - 注意")
        else:
            self.error(f"システムヘルススコア: {overall['score']}/100 - 異常")
            
        # リソース
        self.section("システムリソース")
        resources = health_data['resources']
        if 'error' not in resources:
            self.info(f"CPU: {resources['cpu']['usage_percent']}% ({resources['cpu']['cores']}コア)")
            self.info(f"メモリ: {resources['memory']['used_gb']}GB / {resources['memory']['total_gb']}GB ({resources['memory']['percent']}%)")
            self.info(f"ディスク: {resources['disk']['used_gb']}GB / {resources['disk']['total_gb']}GB ({resources['disk']['percent']}%)")
            
        # サービス
        self.section("サービス")
        for service, info in health_data['services'].items():
            icon = "✅" if info['healthy'] else "❌"
            self.print(f"{icon} {service}: {info['status']}")
            
        # ワーカー
        self.section("ワーカー")
        for worker_type, info in health_data['workers'].items():
            if info['expected'] > 0 or info['actual'] > 0:
                icon = "✅" if info['healthy'] else "❌"
                self.print(f"{icon} {info['name']}: {info['actual']}/{info['expected']}")
                
        # キュー
        self.section("キュー")
        has_queue_issues = False
        for queue, info in health_data['queues'].items():
            if info.get('messages', -1) >= 0:
                if info['status'] != 'ok':
                    has_queue_issues = True
                    icon = "⚠️" if info['status'] == 'warning' else "❌"
                    self.print(f"{icon} {queue}: {info['messages']} メッセージ", color='yellow' if info['status'] == 'warning' else 'red')
                    
        if not has_queue_issues:
            self.success("全キュー正常")
            
        # 問題のサマリー
        if overall['summary']['critical'] > 0 or overall['summary']['warning'] > 0:
            self.section("問題サマリー")
            if overall['summary']['critical'] > 0:
                self.error(f"重大な問題: {overall['summary']['critical']}件")
            if overall['summary']['warning'] > 0:
                self.warning(f"警告: {overall['summary']['warning']}件")
                
    def auto_fix_issues(self, health_data):
        """問題の自動修復"""
        fixes_applied = []
        
        # サービスの起動
        if not health_data['services']['rabbitmq']['healthy']:
            self.info("RabbitMQを起動しています...")
            result = self.run_command(['sudo', 'systemctl', 'start', 'rabbitmq-server'])
            if result and result.returncode == 0:
                fixes_applied.append("RabbitMQを起動しました")
                
        # ログファイルのローテーション
        for log_file, info in health_data['logs'].items():
            if info.get('size_mb', 0) > info.get('max_size_mb', 100):
                log_path = self.logs_dir / log_file
                if log_path.exists():
                    # バックアップ作成
                    backup_path = log_path.with_suffix(f'.{datetime.now().strftime("%Y%m%d_%H%M%S")}.bak')
                    log_path.rename(backup_path)
                    log_path.touch()
                    fixes_applied.append(f"{log_file}をローテーションしました")
                    
        # キューのクリア（危険なので確認が必要）
        critical_queues = [q for q, info in health_data['queues'].items() 
                          if info.get('status') == 'critical']
        if critical_queues:
            self.warning(f"以下のキューが満杯です: {', '.join(critical_queues)}")
            self.info("手動でクリアするには: ai-queue-clear")
            
        return fixes_applied
        
    def execute(self, args):
        """メイン実行"""
        if not args.json:
            self.header("AI Company ヘルスチェック")
            
        # 各種チェック実行
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'resources': self.check_system_resources(),
            'services': self.check_services(),
            'workers': self.check_workers(),
            'queues': self.check_queues(),
            'logs': self.check_logs(),
            'database': self.check_database()
        }
        
        # 全体スコア計算
        health_data['overall'] = self.calculate_overall_health(health_data)
        
        # 自動修復
        if args.fix:
            fixes = self.auto_fix_issues(health_data)
            if fixes:
                health_data['fixes_applied'] = fixes
                if not args.json:
                    self.section("自動修復")
                    for fix in fixes:
                        self.success(fix)
                        
        # 結果表示
        if args.json:
            print(json.dumps(health_data, indent=2))
        else:
            self.display_health_report(health_data)
            
            # 推奨事項
            if health_data['overall']['status'] != 'healthy':
                self.section("推奨アクション")
                if health_data['overall']['summary']['critical'] > 0:
                    self.info("1. ai-restart --force で再起動")
                    self.info("2. ai-health --fix で自動修復")
                if health_data['overall']['summary']['warning'] > 0:
                    self.info("1. ai-logs --error で詳細確認")
                    self.info("2. ai-queue でキュー状態確認")

if __name__ == "__main__":
    cmd = HealthCommand()
    cmd.run()
