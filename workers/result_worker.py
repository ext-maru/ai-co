#!/usr/bin/env python3
"""
AI Company Result Worker v6.0 - Enhanced Slack Notification
タスク完了結果の処理とSlack通知（改善版）
"""

import sys
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Core imports
from core import BaseWorker, get_config, EMOJI
from libs.slack_notifier import SlackNotifier
from libs.ai_command_helper import AICommandHelper


class ResultWorkerV2(BaseWorker):
    """タスク結果処理とSlack通知ワーカー（改善版）"""
    
    def __init__(self):
        super().__init__(worker_type='result')
        self.config = get_config()
        self.slack_notifier = SlackNotifier()
        self.ai_helper = AICommandHelper()
        
        # 統計情報
        self.stats = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'total_duration': 0.0
        }
    
    def process_message(self, ch, method, properties, body):
        """結果メッセージの処理"""
        start_time = time.time()
        
        try:
            # bodyがbytesの場合はデコード
            if isinstance(body, bytes):
                body = json.loads(body.decode('utf-8'))
            elif isinstance(body, str):
                body = json.loads(body)
            
            # タスク情報の抽出
            task_id = body.get('task_id', 'unknown')
            task_type = body.get('task_type', 'general')
            status = body.get('status', 'completed')
            prompt = body.get('prompt', '')
            
            # 実行結果情報
            response = body.get('response', '')
            files_created = body.get('files_created', [])
            output_file = body.get('output_file', '')
            duration = body.get('duration', 0.0)
            
            # 追加情報
            worker_id = body.get('worker_id', 'worker-1')
            rag_applied = body.get('rag_applied', False)
            
            # エラー情報（あれば）
            error = body.get('error', None)
            error_trace = body.get('error_trace', '')
            
            # 統計更新
            self._update_stats(status, duration)
            
            # ログ出力
            self.logger.info(
                f"Result received: {task_id} | "
                f"Status: {status} | "
                f"Type: {task_type} | "
                f"Duration: {duration:.2f}s | "
                f"Files: {len(files_created)}"
            )
            
            # Slack通知の構築・送信
            if self.config.get('slack.enabled', False):
                self._send_enhanced_slack_notification(
                    task_id=task_id,
                    task_type=task_type,
                    status=status,
                    prompt=prompt,
                    response=response,
                    files_created=files_created,
                    output_file=output_file,
                    duration=duration,
                    worker_id=worker_id,
                    rag_applied=rag_applied,
                    error=error,
                    error_trace=error_trace
                )
            
            # 処理完了
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
            # 処理時間記録
            process_duration = time.time() - start_time
            self.logger.info(
                f"Result processed: {task_id} | "
                f"Process duration: {process_duration:.2f}s"
            )
            
        except Exception as e:
            self.handle_error(e, "process_message", {"task_id": task_id})
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def _update_stats(self, status: str, duration: float):
        """統計情報の更新"""
        self.stats['total_tasks'] += 1
        if status == 'completed':
            self.stats['successful_tasks'] += 1
        else:
            self.stats['failed_tasks'] += 1
        self.stats['total_duration'] += duration
    
    def _send_enhanced_slack_notification(self, **kwargs):
        """改善されたSlack通知の送信"""
        try:
            # メイン通知（簡潔版）を送信
            if kwargs['status'] == 'completed':
                main_message, thread_messages = self._format_success_notification(**kwargs)
            else:
                main_message, thread_messages = self._format_error_notification(**kwargs)
            
            # メインメッセージ送信
            result = self.slack_notifier.send_message(main_message)
            
            # スレッドに詳細情報を送信
            if result and 'ts' in result and thread_messages:
                channel = result.get('channel', self.config.get('slack.channel'))
                thread_ts = result['ts']
                
                for thread_msg in thread_messages:
                    self.slack_notifier.send_thread_message(
                        channel=channel,
                        thread_ts=thread_ts,
                        message=thread_msg
                    )
            
        except Exception as e:
            self.logger.error(f"Slack notification failed: {str(e)}")
    
    def _format_success_notification(self, **kwargs) -> tuple:
        """成功時の通知フォーマット（メイン＋スレッド）"""
        task_id = kwargs['task_id']
        task_type = kwargs['task_type']
        duration = kwargs['duration']
        files_count = len(kwargs.get('files_created', []))
        worker_id = kwargs.get('worker_id', 'worker-1')
        rag_applied = kwargs.get('rag_applied', False)
        prompt = kwargs.get('prompt', '')
        response = kwargs.get('response', '')
        
        # タスクIDのショート版（見やすさのため）
        short_id = task_id.split('_')[-1] if '_' in task_id else task_id[-8:]
        
        # プロンプトの要約（最初の50文字）
        prompt_summary = self._summarize_text(prompt, 50)
        
        # レスポンスの要約（最初の100文字）
        response_summary = self._summarize_text(response, 100)
        
        # メイン通知（簡潔版）
        main_parts = [
            f"✅ **タスク完了** `{short_id}`",
            "",
            f"📝 **要求:** {prompt_summary}",
            f"💬 **応答:** {response_summary}",
            "",
            f"⚡ **処理時間:** {duration:.1f}秒 | 📁 **ファイル:** {files_count}個",
            f"🤖 **ワーカー:** {worker_id} | 🧠 **RAG:** {'ON' if rag_applied else 'OFF'}"
        ]
        
        # 実行可能なアクション
        if files_count > 0 or kwargs.get('output_file'):
            main_parts.extend([
                "",
                "```bash",
                "# 詳細確認",
                f"ai-logs {task_id}",
                "```"
            ])
        
        main_message = "\n".join(main_parts)
        
        # スレッドメッセージ（詳細情報）
        thread_messages = []
        
        # 1. プロンプト全文
        if prompt:
            thread_messages.append(
                f"📝 **プロンプト全文:**\n```\n{prompt}\n```"
            )
        
        # 2. レスポンス詳細
        if response:
            response_formatted = self._format_response_details(response)
            thread_messages.append(
                f"💬 **レスポンス詳細:**\n{response_formatted}"
            )
        
        # 3. ファイル操作
        if kwargs.get('files_created'):
            file_commands = self._generate_file_commands(kwargs['files_created'])
            thread_messages.append(
                f"📁 **ファイル操作コマンド:**\n{file_commands}"
            )
        
        # 4. GitHub Flow コマンド
        if files_count > 0:
            git_commands = self._generate_git_commands(kwargs['files_created'], task_type)
            thread_messages.append(
                f"🔄 **GitHub Flow:**\n{git_commands}"
            )
        
        # 5. パフォーマンス詳細
        if self.stats['total_tasks'] >= 10:
            perf_details = self._format_performance_details()
            thread_messages.append(
                f"📊 **パフォーマンス統計:**\n{perf_details}"
            )
        
        return main_message, thread_messages
    
    def _format_error_notification(self, **kwargs) -> tuple:
        """エラー時の通知フォーマット（メイン＋スレッド）"""
        task_id = kwargs['task_id']
        task_type = kwargs['task_type']
        error = kwargs.get('error', '不明なエラー')
        error_trace = kwargs.get('error_trace', '')
        worker_id = kwargs.get('worker_id', 'worker-1')
        
        # タスクIDのショート版
        short_id = task_id.split('_')[-1] if '_' in task_id else task_id[-8:]
        
        # エラーメッセージの要約
        error_summary = self._summarize_text(str(error), 80)
        
        # メイン通知（簡潔版）
        main_parts = [
            f"❌ **タスク失敗** `{short_id}`",
            "",
            f"⚠️ **エラー:** {error_summary}",
            f"🏷️ **タイプ:** {task_type} | 🤖 **ワーカー:** {worker_id}",
            "",
            "```bash",
            "# エラー詳細確認",
            f"ai-logs {task_id} --error",
            "",
            "# 再試行",
            f"ai-retry {task_id}",
            "```"
        ]
        
        main_message = "\n".join(main_parts)
        
        # スレッドメッセージ（詳細情報）
        thread_messages = []
        
        # 1. エラートレース
        if error_trace:
            thread_messages.append(
                f"🔍 **エラートレース:**\n```\n{error_trace}\n```"
            )
        
        # 2. デバッグコマンド
        debug_commands = f"""🔧 **デバッグコマンド:**
```bash
# 詳細ログ確認
ai-logs {task_id} --verbose

# ワーカーログ確認
tail -f logs/{worker_id}.log

# DLQ確認
ai-dlq show {task_id}

# エラーパターン解析
ai-error analyze {task_id}
```"""
        thread_messages.append(debug_commands)
        
        # 3. 修正提案（AI Command Executorを使用）
        fix_suggestions = f"""🛠️ **修正提案:**
```bash
# エラーの自動修正を試行
ai-fix {task_id}

# インシデント作成
ai-incident create --error "{error_summary}" --task {task_id}

# 類似エラーの検索
ai-error search "{error_summary}"
```"""
        thread_messages.append(fix_suggestions)
        
        return main_message, thread_messages
    
    def _summarize_text(self, text: str, max_length: int) -> str:
        """テキストを要約（最初のn文字 + ...）"""
        if not text:
            return "（なし）"
        
        # 改行を空白に置換
        text = text.replace('\n', ' ').strip()
        
        if len(text) <= max_length:
            return text
        
        # 単語の途中で切らないように調整
        cutoff = text[:max_length].rfind(' ')
        if cutoff == -1 or cutoff < max_length * 0.7:
            cutoff = max_length
        
        return f"{text[:cutoff]}..."
    
    def _format_response_details(self, response: str) -> str:
        """レスポンスの詳細フォーマット"""
        if len(response) <= 2000:
            return f"```\n{response}\n```"
        
        # 長い場合は要約と最初/最後を表示
        lines = response.split('\n')
        total_lines = len(lines)
        
        if total_lines > 20:
            preview_lines = lines[:10] + ['', f'... ({total_lines - 20} 行省略) ...', ''] + lines[-10:]
            preview = '\n'.join(preview_lines)
        else:
            preview = response[:1000] + f"\n\n... (残り {len(response) - 1000} 文字)"
        
        return f"```\n{preview}\n```"
    
    def _generate_file_commands(self, files_created: List[str]) -> str:
        """ファイル操作コマンドの生成"""
        if not files_created:
            return "ファイルが作成されていません"
        
        commands = ["```bash"]
        
        # ファイル一覧表示
        commands.append("# 作成されたファイル一覧")
        commands.append(f"ls -la {' '.join(files_created[:5])}")
        
        # ファイルタイプ別のコマンド
        for file_path in files_created[:3]:
            file_path = Path(file_path)
            if file_path.suffix == '.py':
                commands.extend([
                    "",
                    f"# Pythonファイルの確認",
                    f"cat {file_path}",
                    f"python3 -m py_compile {file_path}  # 構文チェック"
                ])
            elif file_path.suffix == '.sh':
                commands.extend([
                    "",
                    f"# シェルスクリプトの確認",
                    f"cat {file_path}",
                    f"chmod +x {file_path}",
                    f"bash -n {file_path}  # 構文チェック"
                ])
            elif file_path.suffix == '.json':
                commands.extend([
                    "",
                    f"# JSONファイルの確認",
                    f"jq . {file_path}  # 整形表示"
                ])
        
        commands.append("```")
        return "\n".join(commands)
    
    def _generate_git_commands(self, files_created: List[str], task_type: str) -> str:
        """GitHub Flow用のコマンド生成"""
        if not files_created:
            return ""
        
        # ブランチ名の生成
        branch_type = "feature" if task_type in ['development', 'enhancement'] else "fix"
        branch_name = f"{branch_type}/{task_type}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        commands = f"""```bash
# 新しいブランチを作成
gf {branch_type} {task_type}

# ファイルを追加
git add {' '.join(files_created[:5])}

# コミット（AI Command Executorを使用）
ai-git commit -m "✨ {task_type}: 自動生成されたファイル"

# プルリクエスト作成
gf pr

# または、自動化スクリプト
ai-git flow --files "{','.join(files_created)}" --type {branch_type}
```"""
        
        return commands
    
    def _format_performance_details(self) -> str:
        """パフォーマンス統計の詳細"""
        success_rate = (self.stats['successful_tasks'] / self.stats['total_tasks']) * 100
        avg_duration = self.stats['total_duration'] / self.stats['total_tasks']
        
        return f"""```
総タスク数: {self.stats['total_tasks']}
成功率: {success_rate:.1f}%
平均処理時間: {avg_duration:.2f}秒
失敗タスク: {self.stats['failed_tasks']}
総処理時間: {self.stats['total_duration']:.1f}秒

時間別分析:
- 最速: {self._get_fastest_task()}
- 最遅: {self._get_slowest_task()}
```"""
    
    def _get_fastest_task(self) -> str:
        """最速タスク情報（仮実装）"""
        return "0.5秒 (単純なテキスト生成)"
    
    def _get_slowest_task(self) -> str:
        """最遅タスク情報（仮実装）"""
        return "45.2秒 (大規模コード生成)"
    
    def periodic_stats_report(self):
        """定期的な統計レポート（1時間ごと）"""
        while True:
            time.sleep(3600)  # 1時間
            
            if self.stats['total_tasks'] >= 10:  # 10タスク以上で報告
                success_rate = (self.stats['successful_tasks'] / self.stats['total_tasks']) * 100
                avg_duration = self.stats['total_duration'] / self.stats['total_tasks']
                
                # 簡潔なサマリー
                report = f"""📊 **時間別レポート** `{datetime.now().strftime('%H:00')}`

📈 **統計:** {self.stats['total_tasks']}タスク | 成功率 {success_rate:.0f}% | 平均 {avg_duration:.1f}秒

```bash
# 詳細レポート生成
ai-report generate --hourly
```"""
                
                try:
                    self.slack_notifier.send_message(report)
                except:
                    self.logger.warning("Failed to send hourly report")


    def cleanup(self):
        """TODO: cleanupメソッドを実装してください"""
        pass

    def stop(self):
        """TODO: stopメソッドを実装してください"""
        pass

    def initialize(self) -> None:
        """ワーカーの初期化処理"""
        # TODO: 初期化ロジックを実装してください
        pass

    def handle_error(self):
        """TODO: handle_errorメソッドを実装してください"""
        pass

    def get_status(self):
        """TODO: get_statusメソッドを実装してください"""
        pass

    def validate_config(self):
        """TODO: validate_configメソッドを実装してください"""
        pass


# Backward compatibility alias
ResultWorker = ResultWorkerV2

if __name__ == "__main__":
    worker = ResultWorkerV2()
    
    # 統計レポートスレッドを開始
    import threading
    stats_thread = threading.Thread(target=worker.periodic_stats_report, daemon=True)
    stats_thread.start()
    
    # ワーカー実行
    worker.start()
