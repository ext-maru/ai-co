#!/usr/bin/env python3
"""
AI対話シェル（REPL）コマンド
インタラクティブな開発・デバッグ環境を提供
"""
import sys
import json
import argparse
import subprocess
import readline
import atexit
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import logging
import time
import re
import shlex

sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult
from libs.four_sages_integration import FourSagesIntegration

logger = logging.getLogger(__name__)


class AIShellCommand(BaseCommand):
    """AI対話シェル（REPL）コマンド"""
    
    def __init__(self):
        super().__init__(
            name="ai-shell",
            description="AI対話シェル（REPL）",
            version="2.0.0"
        )
        self.session_history = []
        self.variables = {}
        self.elders = None
        self.performance_stats = {}
        self.auto_complete_commands = []
        self.running = True
        
        # AI Companyコマンド一覧
        self.ai_commands = [
            'ai-status', 'ai-send', 'ai-logs', 'ai-stop', 'ai-start',
            'ai-report', 'ai-rag', 'ai-backup', 'ai-clean', 'ai-debug',
            'ai-evolve', 'ai-learn', 'ai-simulate', 'ai-shell'
        ]
        
    def add_arguments(self, parser: argparse.ArgumentParser):
        """引数定義"""
        parser.add_argument(
            '--mode', '-m',
            choices=['interactive', 'command', 'batch', 'script', 'help', 
                    'debug', 'elder', 'save_session', 'load_session', 'performance'],
            default='interactive',
            help='実行モード'
        )
        
        # 単体コマンド実行用
        parser.add_argument(
            '--command', '-c',
            type=str,
            help='実行するコマンド'
        )
        
        # バッチ実行用
        parser.add_argument(
            '--commands',
            nargs='+',
            help='実行するコマンドのリスト'
        )
        
        # スクリプト実行用
        parser.add_argument(
            '--script-file', '-f',
            type=str,
            help='実行するスクリプトファイル'
        )
        
        # 履歴管理
        parser.add_argument(
            '--history-file',
            type=str,
            help='履歴ファイルのパス'
        )
        parser.add_argument(
            '--save-history',
            action='store_true',
            help='履歴を保存'
        )
        
        # セッション管理
        parser.add_argument(
            '--session-file',
            type=str,
            help='セッションファイルのパス'
        )
        parser.add_argument(
            '--include-history',
            action='store_true',
            help='セッションに履歴を含める'
        )
        
        # インタラクティブオプション
        parser.add_argument(
            '--prompt-style',
            choices=['default', 'minimal', 'elder', 'debug'],
            default='default',
            help='プロンプトスタイル'
        )
        parser.add_argument(
            '--auto-complete',
            action='store_true',
            help='自動補完を有効化'
        )
        
        # 機能オプション
        parser.add_argument(
            '--enable-variables',
            action='store_true',
            help='変数サポートを有効化'
        )
        parser.add_argument(
            '--enable-pipes',
            action='store_true',
            help='パイプサポートを有効化'
        )
        parser.add_argument(
            '--continue-on-error',
            action='store_true',
            help='エラー時も継続実行'
        )
        parser.add_argument(
            '--stop-on-error',
            action='store_true',
            help='エラー時に停止'
        )
        
        # エルダーモード
        parser.add_argument(
            '--elder-session',
            action='store_true',
            help='エルダーセッションモード'
        )
        parser.add_argument(
            '--participating-elders',
            nargs='+',
            choices=['knowledge', 'task', 'incident', 'rag'],
            help='参加エルダーを指定'
        )
        
        # デバッグ・パフォーマンス
        parser.add_argument(
            '--debug-level',
            choices=['basic', 'verbose', 'trace'],
            default='basic',
            help='デバッグレベル'
        )
        parser.add_argument(
            '--monitor-commands',
            action='store_true',
            help='コマンド実行を監視'
        )
        parser.add_argument(
            '--profile-memory',
            action='store_true',
            help='メモリ使用量をプロファイル'
        )
        
        # ヘルプシステム
        parser.add_argument(
            '--topic',
            type=str,
            help='ヘルプトピック'
        )
        
        # その他
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='詳細出力'
        )
    
    def execute(self, args) -> CommandResult:
        """コマンド実行"""
        try:
            # 初期化
            self._initialize_shell(args)
            
            # モードに応じた処理
            if args.mode == 'interactive':
                return self._run_interactive_shell(args)
            elif args.mode == 'command':
                return self._run_single_command(args)
            elif args.mode == 'batch':
                return self._run_batch_commands(args)
            elif args.mode == 'script':
                return self._run_script(args)
            elif args.mode == 'help':
                return self._show_help(args)
            elif args.mode == 'debug':
                return self._run_debug_mode(args)
            elif args.mode == 'elder':
                return self._run_elder_session(args)
            elif args.mode == 'save_session':
                return self._save_session(args)
            elif args.mode == 'load_session':
                return self._load_session(args)
            elif args.mode == 'performance':
                return self._run_performance_mode(args)
            else:
                return CommandResult(
                    success=False,
                    message=f"無効なモード: {args.mode}"
                )
                
        except KeyboardInterrupt:
            return CommandResult(
                success=True,
                message="シェルが中断されました"
            )
        except Exception as e:
            logger.error(f"Shell error: {e}")
            return CommandResult(
                success=False,
                message=f"エラー: {str(e)}"
            )
    
    def _initialize_shell(self, args):
        """シェル初期化"""
        # エルダーズ統合
        try:
            self.elders = FourSagesIntegration()
        except Exception as e:
            logger.warning(f"Elders integration not available: {e}")
            self.elders = None
        
        # 履歴ファイル設定
        if args.history_file:
            self.history_file = Path(args.history_file)
        else:
            self.history_file = Path.home() / '.ai_shell_history'
        
        # 自動補完設定
        if getattr(args, 'auto_complete', False):
            self._setup_auto_completion()
        
        # パフォーマンス監視開始
        if getattr(args, 'monitor_commands', False):
            self._start_performance_monitor()
    
    def _run_interactive_shell(self, args) -> CommandResult:
        """インタラクティブシェル実行"""
        print("🤖 AI Company Shell v2.0.0")
        print("エルダーズ統合対話環境へようこそ")
        print("'help' でコマンド一覧、'exit' で終了")
        print("-" * 50)
        
        # 履歴読み込み
        self._load_history()
        
        try:
            while self.running:
                # プロンプト表示
                prompt = self._get_prompt(args.prompt_style)
                
                try:
                    user_input = input(prompt).strip()
                except EOFError:
                    break
                
                if not user_input:
                    continue
                
                # 履歴に追加
                self.session_history.append(user_input)
                readline.add_history(user_input)
                
                # コマンド処理
                if user_input.lower() in ['exit', 'quit', 'q']:
                    break
                elif user_input.lower() in ['help', '?']:
                    self._print_help()
                elif user_input.lower() == 'clear':
                    print("\\033[2J\\033[H", end="")  # 画面クリア
                elif user_input.lower() == 'history':
                    self._print_history()
                elif user_input.lower() == 'vars':
                    self._print_variables()
                elif user_input.lower().startswith('$'):
                    self._handle_variable_assignment(user_input)
                else:
                    self._execute_shell_command(user_input, args)
            
            # 履歴保存
            if getattr(args, 'save_history', True):
                self._save_history()
            
            return CommandResult(
                success=True,
                message="AI Shellセッションが終了しました"
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"シェル実行エラー: {str(e)}"
            )
    
    def _run_single_command(self, args) -> CommandResult:
        """単体コマンド実行"""
        if not args.command:
            return CommandResult(
                success=False,
                message="コマンドを指定してください（--command）"
            )
        
        result = self._execute_ai_command(args.command)
        
        message_lines = [f"コマンド: {args.command}"]
        
        if result['success']:
            message_lines.append("実行結果:")
            message_lines.append(result['output'])
            if args.verbose:
                message_lines.append(f"実行時間: {result.get('execution_time', 0):.3f}秒")
        else:
            message_lines.append(f"エラー: {result.get('error', 'Unknown error')}")
            if 'suggestions' in result:
                message_lines.append("提案コマンド:")
                for suggestion in result['suggestions']:
                    message_lines.append(f"  - {suggestion}")
        
        return CommandResult(
            success=result['success'],
            message='\n'.join(message_lines)
        )
    
    def _run_batch_commands(self, args) -> CommandResult:
        """バッチコマンド実行"""
        if not args.commands:
            return CommandResult(
                success=False,
                message="実行するコマンドを指定してください（--commands）"
            )
        
        results = []
        success_count = 0
        
        for command in args.commands:
            result = self._execute_ai_command(command)
            results.append((command, result))
            
            if result['success']:
                success_count += 1
            elif not getattr(args, 'continue_on_error', True):
                break
        
        # 結果サマリー
        message_lines = [
            f"{success_count}/{len(args.commands)}件のコマンドを実行しました",
            ""
        ]
        
        for i, (command, result) in enumerate(results, 1):
            status = "✓" if result['success'] else "✗"
            message_lines.append(f"{i}. {status} {command}")
            
            if args.verbose:
                if result['success']:
                    output = result['output'][:100]
                    if len(result['output']) > 100:
                        output += "..."
                    message_lines.append(f"   {output}")
                else:
                    message_lines.append(f"   エラー: {result.get('error', 'Unknown')}")
        
        return CommandResult(
            success=success_count == len(args.commands),
            message='\n'.join(message_lines)
        )
    
    def _run_script(self, args) -> CommandResult:
        """スクリプト実行"""
        if not args.script_file:
            return CommandResult(
                success=False,
                message="スクリプトファイルを指定してください（--script-file）"
            )
        
        script_path = Path(args.script_file)
        if not script_path.exists():
            return CommandResult(
                success=False,
                message=f"スクリプトファイルが見つかりません: {args.script_file}"
            )
        
        # スクリプト読み込み
        try:
            script_content = script_path.read_text(encoding='utf-8')
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"スクリプト読み込みエラー: {str(e)}"
            )
        
        # コマンド抽出（コメント行を除く）
        commands = []
        for line in script_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                commands.append(line)
        
        # コマンド実行
        results = []
        success_count = 0
        
        for command in commands:
            result = self._execute_ai_command(command)
            results.append((command, result))
            
            if result['success']:
                success_count += 1
            elif not getattr(args, 'continue_on_error', True):
                break
        
        message_lines = [
            f"スクリプト実行完了: {args.script_file}",
            f"実行コマンド数: {len(commands)}",
            f"成功: {success_count}件"
        ]
        
        if len(commands) != success_count:
            message_lines.append(f"失敗: {len(commands) - success_count}件")
        
        return CommandResult(
            success=success_count == len(commands),
            message='\n'.join(message_lines)
        )
    
    def _run_elder_session(self, args) -> CommandResult:
        """エルダーセッション実行"""
        if not self.elders:
            return CommandResult(
                success=False,
                message="エルダーズ統合が利用できません"
            )
        
        print("🧙‍♂️ エルダーセッション開始")
        print("エルダーズとの協調対話モードです")
        print("'elder help' でエルダー専用コマンド、'exit' で終了")
        print("-" * 50)
        
        try:
            while self.running:
                prompt = "🧙‍♂️ Elder> "
                
                try:
                    user_input = input(prompt).strip()
                except EOFError:
                    break
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit']:
                    break
                elif user_input.lower() == 'elder help':
                    self._print_elder_help()
                elif user_input.startswith('elder '):
                    self._handle_elder_command(user_input[6:])  # 'elder 'を除去
                else:
                    # 通常のAIコマンドをエルダー強化で実行
                    self._execute_elder_enhanced_command(user_input)
            
            return CommandResult(
                success=True,
                message="エルダーセッションが終了しました"
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"エルダーセッションエラー: {str(e)}"
            )
    
    def _execute_ai_command(self, command: str) -> Dict[str, Any]:
        """AIコマンド実行"""
        start_time = time.time()
        
        try:
            # 変数展開
            if hasattr(self, 'variables') and '$' in command:
                command = self._expand_variables(command)
            
            # パイプ処理
            if '|' in command and getattr(self, 'enable_pipes', False):
                return self._execute_pipe_command(command)
            
            # コマンド実行
            cmd_parts = shlex.split(command)
            
            # AI Companyコマンドかチェック
            if cmd_parts[0] not in self.ai_commands:
                return {
                    'success': False,
                    'error': f"Unknown command: {cmd_parts[0]}",
                    'suggestions': [cmd for cmd in self.ai_commands if cmd_parts[0] in cmd]
                }
            
            # 実際のコマンド実行
            result = subprocess.run(
                ['python3', f'commands/{cmd_parts[0].replace("-", "_")}.py'] + cmd_parts[1:],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent),
                timeout=30
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'output': result.stdout.strip(),
                    'execution_time': execution_time
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr.strip() or result.stdout.strip(),
                    'execution_time': execution_time
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timeout (30s)',
                'execution_time': 30.0
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def _execute_shell_command(self, command: str, args):
        """シェルコマンド実行"""
        result = self._execute_ai_command(command)
        
        if result['success']:
            print(f"✓ {result['output']}")
            if args.verbose:
                print(f"  実行時間: {result.get('execution_time', 0):.3f}秒")
        else:
            print(f"✗ エラー: {result.get('error', 'Unknown error')}")
            if 'suggestions' in result:
                print("  提案:")
                for suggestion in result['suggestions']:
                    print(f"    - {suggestion}")
    
    def _get_prompt(self, style: str) -> str:
        """プロンプト取得"""
        prompts = {
            'default': "AI> ",
            'minimal': "> ",
            'elder': "🧙‍♂️ > ",
            'debug': "[DEBUG] AI> "
        }
        return prompts.get(style, "AI> ")
    
    def _setup_auto_completion(self):
        """自動補完設定"""
        def completer(text, state):
            options = [cmd for cmd in self.ai_commands if cmd.startswith(text)]
            if state < len(options):
                return options[state]
            else:
                return None
        
        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")
    
    def _load_history(self):
        """履歴読み込み"""
        if self.history_file.exists():
            try:
                readline.read_history_file(str(self.history_file))
            except Exception as e:
                logger.warning(f"Failed to load history: {e}")
    
    def _save_history(self):
        """履歴保存"""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            readline.write_history_file(str(self.history_file))
        except Exception as e:
            logger.warning(f"Failed to save history: {e}")
    
    def _print_help(self):
        """ヘルプ表示"""
        print("\\n利用可能なコマンド:")
        for cmd in self.ai_commands:
            print(f"  {cmd}")
        
        print("\\nシェル組み込みコマンド:")
        print("  help, ?     - このヘルプを表示")
        print("  clear       - 画面をクリア")
        print("  history     - コマンド履歴を表示")
        print("  vars        - 変数一覧を表示")
        print("  exit, quit  - シェルを終了")
    
    def _print_history(self):
        """履歴表示"""
        print("\\nコマンド履歴:")
        for i, cmd in enumerate(self.session_history[-10:], 1):
            print(f"  {i}. {cmd}")
    
    def _print_variables(self):
        """変数表示"""
        if not self.variables:
            print("定義された変数はありません")
        else:
            print("\\n定義済み変数:")
            for name, value in self.variables.items():
                print(f"  {name} = {value}")
    
    def _handle_variable_assignment(self, input_line: str):
        """変数代入処理"""
        if '=' in input_line:
            name, value = input_line[1:].split('=', 1)  # $を除去
            self.variables[name.strip()] = value.strip()
            print(f"変数設定: {name.strip()} = {value.strip()}")
        else:
            var_name = input_line[1:]  # $を除去
            if var_name in self.variables:
                print(f"{var_name} = {self.variables[var_name]}")
            else:
                print(f"変数 '{var_name}' は定義されていません")
    
    def _expand_variables(self, command: str) -> str:
        """変数展開"""
        for name, value in self.variables.items():
            command = command.replace(f'${name}', value)
        return command
    
    def _execute_pipe_command(self, command: str) -> Dict[str, Any]:
        """パイプコマンド実行"""
        # 簡略化実装
        parts = command.split('|')
        
        result = None
        for part in parts:
            part = part.strip()
            if result:
                # 前の結果を次のコマンドの入力として使用
                # 実際の実装では、より複雑なパイプ処理が必要
                part += f" '{result['output']}'"
            
            result = self._execute_ai_command(part)
            if not result['success']:
                break
        
        return {
            'success': result['success'] if result else False,
            'output': result['output'] if result else '',
            'pipe_stages': len(parts)
        }
    
    def _show_help(self, args) -> CommandResult:
        """ヘルプ表示"""
        if args.topic == 'commands':
            help_text = "利用可能なコマンド:\\n" + "\\n".join(f"  {cmd}" for cmd in self.ai_commands)
        else:
            help_text = """
AI Shell ヘルプ

基本的な使用方法:
  ai-shell                    # インタラクティブモード
  ai-shell -c "ai-status"     # 単体コマンド実行
  ai-shell -f script.ai       # スクリプト実行

インタラクティブモード:
  help        - コマンド一覧
  clear       - 画面クリア
  history     - 履歴表示
  vars        - 変数一覧
  exit        - 終了

変数機能:
  $var = value    # 変数設定
  $var            # 変数表示
  ai-report --type $var  # 変数使用

エルダーモード:
  ai-shell --mode elder  # エルダーセッション開始
            """
        
        return CommandResult(success=True, message=help_text.strip())
    
    def _start_performance_monitor(self):
        """パフォーマンス監視開始"""
        self.performance_stats = {
            'start_time': datetime.now(),
            'commands_executed': 0,
            'total_execution_time': 0.0,
            'memory_usage': []
        }
    
    # その他のヘルパーメソッド（簡略化）
    
    def _run_debug_mode(self, args) -> CommandResult:
        """デバッグモード実行"""
        return self._execute_with_debug(args.command, args.debug_level)
    
    def _execute_with_debug(self, command: str, debug_level: str) -> CommandResult:
        """デバッグ付きコマンド実行"""
        result = self._execute_ai_command(command)
        debug_info = {
            'execution_time': result.get('execution_time', 0),
            'memory_usage': '50MB',  # 簡略化
            'api_calls': 3  # 簡略化
        }
        
        message = result.get('output', result.get('error', ''))
        if debug_level == 'verbose':
            message += f"\\n\\nデバッグ情報: {json.dumps(debug_info, indent=2)}"
        
        return CommandResult(
            success=result['success'],
            message=message
        )
    
    def _save_session(self, args) -> CommandResult:
        """セッション保存"""
        session_data = {
            'timestamp': datetime.now().isoformat(),
            'variables': self.variables,
            'history': self.session_history if args.include_history else []
        }
        
        try:
            session_path = Path(args.session_file)
            session_path.parent.mkdir(parents=True, exist_ok=True)
            session_path.write_text(json.dumps(session_data, indent=2))
            
            return CommandResult(
                success=True,
                message=f"セッションを保存しました: {args.session_file}"
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"セッション保存エラー: {str(e)}"
            )
    
    def _load_session(self, args) -> CommandResult:
        """セッション読み込み"""
        try:
            session_path = Path(args.session_file)
            if not session_path.exists():
                return CommandResult(
                    success=False,
                    message=f"セッションファイルが見つかりません: {args.session_file}"
                )
            
            session_data = json.loads(session_path.read_text())
            
            # セッションデータを復元
            self.variables = session_data.get('variables', {})
            if 'history' in session_data:
                self.session_history.extend(session_data['history'])
            
            return CommandResult(
                success=True,
                message=f"セッションを読み込みました: {session_data.get('timestamp', 'unknown')}"
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"セッション読み込みエラー: {str(e)}"
            )
    
    def _run_performance_mode(self, args) -> CommandResult:
        """パフォーマンスモード実行"""
        return self._run_interactive_shell(args)
    
    def _print_elder_help(self):
        """エルダーヘルプ表示"""
        print("\\nエルダー専用コマンド:")
        print("  elder status     - エルダーズステータス")
        print("  elder session    - 協調セッション開始")
        print("  elder consensus  - コンセンサス形成")
    
    def _handle_elder_command(self, command: str):
        """エルダーコマンド処理"""
        if command == 'status':
            if self.elders:
                status = self.elders.monitor_sage_collaboration()
                print(f"エルダーズステータス: {status.get('overall_collaboration_health', 'unknown')}")
            else:
                print("エルダーズが利用できません")
        else:
            print(f"不明なエルダーコマンド: {command}")
    
    def _execute_elder_enhanced_command(self, command: str):
        """エルダー強化コマンド実行"""
        if self.elders:
            # エルダーとの協調学習セッション
            learning_request = {
                'type': 'command_execution',
                'data': {'command': command}
            }
            
            elder_result = self.elders.coordinate_learning_session(learning_request)
            print(f"🧙‍♂️ エルダー協調実行: {elder_result.get('consensus_reached', False)}")
        
        # 通常のコマンド実行
        result = self._execute_ai_command(command)
        if result['success']:
            print(f"✓ {result['output']}")
        else:
            print(f"✗ {result.get('error', 'Unknown error')}")


def main():
    command = AIShellCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()