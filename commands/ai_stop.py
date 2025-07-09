#!/usr/bin/env python3
"""
ai-stop: AI Company システム停止コマンド
"""
import time
import os
from commands.base_command import BaseCommand

class StopCommand(BaseCommand):
    def __init__(self):
        super().__init__(
            name="stop",
            description="AI Company システムを停止します"
        )
        
    def setup_arguments(self):
        self.parser.add_argument(
            '--force',
            action='store_true',
            help='強制終了（プロセスをkillする）'
        )
        self.parser.add_argument(
            '--clear-queues',
            action='store_true',
            help='キューもクリアする'
        )
        
    def stop_tmux_session(self):
        """tmuxセッション停止"""
        result = self.run_command(['tmux', 'has-session', '-t', 'ai_company'])
        if result and result.returncode == 0:
            self.info("tmuxセッション停止中...")
            self.run_command(['tmux', 'kill-session', '-t', 'ai_company'])
            self.success("tmuxセッション停止完了")
            return True
        else:
            self.warning("tmuxセッションが見つかりません")
            return False
            

    def stop_command_executor(self):
        """Command Executor停止"""
        self.info("Command Executor停止中...")
        
        # PIDファイルから読み込み
        pid_file = '/tmp/ai_command_executor.pid'
        stopped = False
        
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    pid = f.read().strip()
                if pid:
                    self.run_command(['kill', pid])
                    os.remove(pid_file)
                    self.success(f"Command Executor停止 (PID: {pid})")
                    stopped = True
            except Exception as e:
                self.warning(f"PIDファイルからの停止失敗: {e}")
        
        # プロセスを直接検索
        if not stopped:
            processes = self.check_process('command_executor_worker')
            for proc in processes:
                self.run_command(['kill', proc['pid']])
                self.success(f"Command Executor停止 (PID: {proc['pid']})")
    
    def kill_processes(self):
        """プロセス強制終了"""
        patterns = [
            'task_worker',
            'pm_worker',
            'result_worker',
            'dialog_task_worker',
            'dialog_pm_worker'
        ]
        
        killed_count = 0
        for pattern in patterns:
            processes = self.check_process(pattern)
            for proc in processes:
                self.run_command(['kill', '-9', proc['pid']])
                killed_count += 1
                
        if killed_count > 0:
            self.success(f"{killed_count} 個のプロセスを終了しました")
        else:
            self.info("終了するプロセスが見つかりませんでした")
            
    def clear_queues(self):
        """キュークリア"""
        conn = self.get_rabbitmq_connection()
        if not conn:
            self.error("RabbitMQに接続できません")
            return
            
        try:
            channel = conn.channel()
            queues = [
                'task_queue',
                'result_queue',
                'pm_queue',
                'dialog_task_queue',
                'dialog_response_queue',
                'user_input_queue',
                'notification_queue'
            ]
            
            cleared = 0
            for queue in queues:
                try:
                    method = channel.queue_purge(queue)
                    if method.message_count > 0:
                        self.info(f"{queue}: {method.message_count} メッセージ削除")
                        cleared += method.message_count
                except Exception:
                    pass
                    
            if cleared > 0:
                self.success(f"合計 {cleared} メッセージをクリアしました")
            else:
                self.info("キューは既に空です")
                
            conn.close()
        except Exception as e:
            self.error(f"キュークリアエラー: {e}")
            
    def show_status_before_stop(self):
        """停止前の状態表示"""
        self.section("現在の状態")
        
        # プロセス確認
        all_processes = []
        patterns = ['task_worker', 'pm_worker', 'result_worker', 'dialog']
        for pattern in patterns:
            all_processes.extend(self.check_process(pattern))
            
        if all_processes:
            self.warning(f"{len(all_processes)} 個のプロセスが稼働中")
            
        # キュー確認
        conn = self.get_rabbitmq_connection()
        if conn:
            try:
                channel = conn.channel()
                queue_info = []
                for queue in ['task_queue', 'result_queue', 'pm_queue']:
                    try:
                        method = channel.queue_declare(queue=queue, passive=True)
                        if method.method.message_count > 0:
                            queue_info.append(f"{queue}: {method.method.message_count}")
                    except:
                        pass
                        
                if queue_info:
                    self.warning("未処理メッセージ: " + ", ".join(queue_info))
                    
                conn.close()
            except:
                pass
                
    def execute(self, args):
        """メイン実行"""
        self.header("AI Company システム停止")
        
        # 停止前の状態表示
        self.show_status_before_stop()
        
        # tmuxセッション停止
        self.section("停止処理")
        session_stopped = self.stop_tmux_session()
        
        # Command Executor停止
        self.stop_command_executor()
        
        # 強制終了モード
        if args.force:
            self.section("強制終了")
            self.kill_processes()
            
        # 残存プロセス確認
        time.sleep(1)
        remaining = []
        for pattern in ['task_worker', 'pm_worker', 'result_worker', 'dialog', 'command_executor', 'se_tester']:
            remaining.extend(self.check_process(pattern))
            
        if remaining:
            self.warning(f"\n{len(remaining)} 個のプロセスがまだ稼働中です")
            if not args.force:
                self.info("完全に停止するには --force オプションを使用してください")
                
        # キュークリア
        if args.clear_queues:
            self.section("キュークリア")
            self.clear_queues()
            
        # 最終確認
        if not remaining:
            self.success("\n✨ システムは完全に停止しました")
        else:
            self.warning("\n⚠️  一部のプロセスが残っています")

if __name__ == "__main__":
    cmd = StopCommand()
    cmd.run()
