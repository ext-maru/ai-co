import datetime
#!/usr/bin/env python3
"""
ResultWorker日本語化パッチ
Slack通知を日本語化し、より詳細な情報を表示
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def patch_result_worker():
    """ResultWorkerを日本語化"""
    
    result_worker_path = PROJECT_ROOT / 'workers' / 'result_worker.py'
    if not result_worker_path.exists():
        print("❌ result_worker.py が見つかりません")
        return False
    
    content = result_worker_path.read_text(encoding='utf-8')
    
    # 日本語メッセージ定義を追加
    japanese_messages = '''
# 日本語メッセージ定義
MESSAGES_JA = {
    'task_completed': '✅ タスク完了',
    'task_failed': '❌ タスク失敗',
    'task_id': 'タスクID',
    'task_type': '種別',
    'duration': '処理時間',
    'files': 'ファイル数',
    'request': '要求内容',
    'response': '応答',
    'error': 'エラー',
    'trace': 'トレース',
    'performance_metrics': '📊 パフォーマンス指標',
    'success_rate': '成功率',
    'average_duration': '平均処理時間',
    'quick_actions': '🚀 クイックアクション',
    'view_output': '出力を確認',
    'check_logs': 'ログを確認',
    'debug_commands': '🔧 デバッグコマンド',
    'check_full_logs': '詳細ログを確認',
    'retry_task': 'タスクを再試行',
    'files_created': '📁 作成されたファイル',
    'file_operations': '📝 ファイル操作',
    'list_files': 'ファイル一覧',
    'run_if_executable': '実行可能なら実行',
    'hourly_report': '📊 時間別パフォーマンスレポート',
    'period': '期間',
    'total_tasks': '総タスク数',
    'failed_tasks': '失敗タスク',
    'total_processing_time': '総処理時間',
    'worker_info': 'ワーカー',
    'rag_info': 'RAG',
    'rag_applied': '適用済み',
    'rag_not_applied': '未適用',
    'prompt': 'プロンプト',
    'ai_company_system': '*Elders Guild RAGシステム*'
}
'''
    
    # インポートセクションの後に日本語メッセージを追加
    import_section_end = "AICommandHelper = None"
    if import_section_end in content:
        content = content.replace(
            import_section_end,
            f"{import_section_end}\n\n{japanese_messages}"
        )
    
    # _format_success_messageメソッドを日本語化
    new_format_success = '''    def _format_success_message(self, **kwargs) -> str:
        """成功時のメッセージフォーマット（日本語）"""
        task_id = kwargs['task_id']
        task_type = kwargs['task_type']
        duration = kwargs['duration']
        files_count = len(kwargs.get('files_created', []))
        worker_id = kwargs.get('worker_id', 'worker-1')
        rag_applied = kwargs.get('rag_applied', False)
        
        # プロフェッショナルなヘッダー（日本語）
        message_parts = [
            f"✅ **Elders Guild タスク完了**",
            f"",
            f"**{MESSAGES_JA['task_id']}:** `{task_id}`",
            f"**{MESSAGES_JA['worker_info']}:** `{worker_id}`",
            f"**{MESSAGES_JA['rag_info']}:** `{MESSAGES_JA['rag_applied'] if rag_applied else MESSAGES_JA['rag_not_applied']}`",
            f"",
            f"**{MESSAGES_JA['task_type']}:** `{task_type}` | **{MESSAGES_JA['duration']}:** `{duration:.2f}秒` | **{MESSAGES_JA['files']}:** `{files_count}`",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
        
        # プロンプト（全文表示）
        if kwargs.get('prompt'):
            prompt_text = kwargs['prompt']
            if len(prompt_text) > 500:
                prompt_text = prompt_text[:497] + "..."
            message_parts.extend([
                "",
                f"**{MESSAGES_JA['prompt']}:**",
                f"{prompt_text}",
                ""
            ])
        
        # レスポンス（詳細表示）
        if kwargs.get('response'):
            response_text = kwargs['response']
            if len(response_text) > 1500:
                response_text = response_text[:1497] + "..."
            message_parts.extend([
                f"**{MESSAGES_JA['response']}:**",
                f"{response_text}",
                ""
            ])
        
        # 統計情報（日本語）
        if self.stats['total_tasks'] > 0:
            success_rate = (self.stats['successful_tasks'] / self.stats['total_tasks']) * 100
            avg_duration = self.stats['total_duration'] / self.stats['total_tasks']
            
            message_parts.extend([
                f"**{MESSAGES_JA['performance_metrics']}:**",
                f"• {MESSAGES_JA['success_rate']}: `{success_rate:.1f}%` ({self.stats['successful_tasks']}/{self.stats['total_tasks']})",
                f"• {MESSAGES_JA['average_duration']}: `{avg_duration:.2f}秒`",
                ""
            ])
        
        # 実行可能なコマンド（日本語コメント）
        if kwargs.get('output_file'):
            message_parts.extend([
                f"**{MESSAGES_JA['quick_actions']}:**",
                f"```bash",
                f"# {MESSAGES_JA['view_output']}",
                f"cat {kwargs['output_file']}",
                f"",
                f"# {MESSAGES_JA['check_logs']}",
                f"ai-logs {task_id}",
                f"```"
            ])
        
        # フッター
        message_parts.append(f"\n{MESSAGES_JA['ai_company_system']}")
        
        return "\\n".join(message_parts)'''
    
    # _format_error_messageメソッドも日本語化
    new_format_error = '''    def _format_error_message(self, **kwargs) -> str:
        """エラー時のメッセージフォーマット（日本語）"""
        task_id = kwargs['task_id']
        task_type = kwargs['task_type']
        error = kwargs.get('error', '不明なエラー')
        worker_id = kwargs.get('worker_id', 'worker-1')
        
        message_parts = [
            f"❌ **{MESSAGES_JA['task_failed']}: {task_id}**",
            f"",
            f"**{MESSAGES_JA['worker_info']}:** `{worker_id}`",
            f"**{MESSAGES_JA['task_type']}:** `{task_type}` | **ステータス:** `{kwargs['status']}`",
            "",
            f"**{MESSAGES_JA['error']}:** `{error}`"
        ]
        
        # エラートレース（最初の500文字）
        if kwargs.get('error_trace'):
            trace_preview = kwargs['error_trace'][:500] + "..." if len(kwargs['error_trace']) > 500 else kwargs['error_trace']
            message_parts.extend([
                "",
                f"**{MESSAGES_JA['trace']}:**",
                f"```",
                trace_preview,
                f"```"
            ])
        
        # デバッグコマンド（日本語）
        message_parts.extend([
            "",
            f"**{MESSAGES_JA['debug_commands']}:**",
            f"```bash",
            f"# {MESSAGES_JA['check_full_logs']}",
            f"ai-logs {task_id} --verbose",
            f"",
            f"# {MESSAGES_JA['retry_task']}",
            f"ai-retry {task_id}",
            f"",
            f"# DLQを確認",
            f"ai-dlq show {task_id}",
            f"```"
        ])
        
        # フッター
        message_parts.append(f"\n{MESSAGES_JA['ai_company_system']}")
        
        return "\\n".join(message_parts)'''
    
    # メソッドを置換
    # _format_success_message の置換
    start_marker = "    def _format_success_message(self, **kwargs) -> str:"
    end_marker = '        return "\\n".join(message_parts)'
    
    if start_marker in content:
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker, start_idx) + len(end_marker)
        content = content[:start_idx] + new_format_success + content[end_idx:]
    
    # _format_error_message の置換
    start_marker = "    def _format_error_message(self, **kwargs) -> str:"
    end_marker = '        return "\\n".join(message_parts)'
    
    if start_marker in content:
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker, start_idx) + len(end_marker)
        content = content[:start_idx] + new_format_error + content[end_idx:]
    
    # ファイル詳細も日本語化
    new_format_files = '''    def _format_file_details(self, files_created: list) -> str:
        """ファイル詳細のフォーマット（日本語）"""
        if not files_created:
            return ""
        
        message_parts = [f"{MESSAGES_JA['files_created']}:"]
        
        for file_path in files_created[:10]:  # 最大10ファイルまで表示
            file_name = Path(file_path).name
            file_type = Path(file_path).suffix or "file"
            
            # ファイルタイプ別の絵文字
            type_emoji = {
                '.py': '🐍',
                '.sh': '🔧',
                '.json': '📋',
                '.conf': '⚙️',
                '.html': '🌐',
                '.md': '📝'
            }.get(file_type, '📄')
            
            message_parts.append(f"{type_emoji} `{file_path}`")
        
        if len(files_created) > 10:
            message_parts.append(f"... 他 {len(files_created) - 10} ファイル")
        
        # ファイル操作コマンド（日本語）
        message_parts.extend([
            "",
            f"**{MESSAGES_JA['file_operations']}:**",
            f"```bash",
            f"# {MESSAGES_JA['list_files']}",
            f"ls -la {' '.join(files_created[:3])}",
            f"",
            f"# {MESSAGES_JA['run_if_executable']}",
            f"chmod +x {files_created[0]} && {files_created[0]}" if files_created else "",
            f"```"
        ])
        
        return "\\n".join(message_parts)'''
    
    # _format_file_details の置換
    start_marker = "    def _format_file_details(self, files_created: list) -> str:"
    end_marker = '        return "\\n".join(message_parts)'
    
    if start_marker in content:
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker, start_idx) + len(end_marker)
        content = content[:start_idx] + new_format_files + content[end_idx:]
    
    # 時間別レポートも日本語化
    hourly_report_section = '''                report = [
                    f"{MESSAGES_JA['hourly_report']}",
                    f"{MESSAGES_JA['period']}: {datetime.now().strftime('%Y-%m-%d %H:00')}",
                    "",
                    f"• {MESSAGES_JA['total_tasks']}: `{self.stats['total_tasks']}`",
                    f"• {MESSAGES_JA['success_rate']}: `{success_rate:.1f}%`",
                    f"• {MESSAGES_JA['failed_tasks']}: `{self.stats['failed_tasks']}`",
                    f"• {MESSAGES_JA['average_duration']}: `{avg_duration:.2f}秒`",
                    f"• {MESSAGES_JA['total_processing_time']}: `{self.stats['total_duration']:.1f}秒`"
                ]'''
    
    # 時間別レポートの置換
    old_report = '''                report = [
                    "📊 **Hourly Performance Report**",
                    f"Period: {datetime.now().strftime('%Y-%m-%d %H:00')}",
                    "",
                    f"• Total Tasks: `{self.stats['total_tasks']}`",
                    f"• Success Rate: `{success_rate:.1f}%`",
                    f"• Failed Tasks: `{self.stats['failed_tasks']}`",
                    f"• Average Duration: `{avg_duration:.2f}s`",
                    f"• Total Processing Time: `{self.stats['total_duration']:.1f}s`"
                ]'''
    
    content = content.replace(old_report, hourly_report_section)
    
    # 保存
    result_worker_path.write_text(content, encoding='utf-8')
    print("✅ ResultWorkerを日本語化しました")
    return True

def main():
    """メイン処理"""
    print("🌏 ResultWorker日本語化パッチを適用中...")
    
    if patch_result_worker():
        print("\n✅ 日本語化完了！")
        print("\n変更内容:")
        print("  - タスク完了/失敗メッセージを日本語化")
        print("  - プロンプト/レスポンスの表示を拡張（1500文字まで）")
        print("  - ワーカーID、RAG適用状況を表示")
        print("  - コマンドの説明を日本語化")
        print("  - 時間別レポートを日本語化")
        print("\n次の手順:")
        print("  1. ResultWorkerを再起動: ai-restart")
        print("  2. 新しいタスクを実行してSlack通知を確認")
    else:
        print("\n❌ 日本語化に失敗しました")

if __name__ == "__main__":
    main()
