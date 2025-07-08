#!/usr/bin/env python3
"""
Claude CLI実行ユーティリティ
"""
import subprocess
import logging
import os
from typing import Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

class ClaudeCLIExecutor:
    """Claude CLIの実行を管理するクラス"""
    
    def __init__(self):
        self.check_claude_cli()
    
    def check_claude_cli(self):
        """Claude CLIがインストールされているかチェック"""
        try:
            result = subprocess.run(['claude', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Claude CLI確認: {result.stdout.strip()}")
            else:
                raise RuntimeError("Claude CLIが正しくインストールされていません")
        except FileNotFoundError:
            raise RuntimeError("Claude CLIがインストールされていません")
    
    def execute(self, prompt: str, model: str = "claude-sonnet-4-20250514", 
                working_dir: Optional[Path] = None) -> str:
        """
        Claude CLIを実行
        
        Args:
            prompt: 実行するプロンプト
            model: 使用するモデル
            working_dir: 作業ディレクトリ
            
        Returns:
            Claude CLIの出力
        """
        # Claude CLIコマンドを構築
        cmd = [
            'claude',
            '--model', model,
            '--allowedTools', 'Edit,Write,FileSystem',
            '--print',
            prompt  # --print フラグ使用時はプロンプトをコマンドライン引数として渡す
        ]
        
        # 環境変数設定
        env = os.environ.copy()
        # CLAUDE_CODE_ENTRYPOINT を削除（--print フラグと競合するため）
        env.pop('CLAUDE_CODE_ENTRYPOINT', None)
        env.pop('CLAUDECODE', None)
        
        # 作業ディレクトリ設定
        cwd = working_dir or os.getcwd()
        
        try:
            logger.info(f"Claude CLI実行開始 (モデル: {model})")
            logger.debug(f"プロンプト: {prompt[:200]}...")
            
            # --print フラグ使用時はstdinを使わない
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                env=env
            )
            
            if result.returncode != 0:
                error_msg = f"Claude CLI実行エラー: {result.stderr}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            logger.info("Claude CLI実行成功")
            return result.stdout
            
        except Exception as e:
            logger.error(f"Claude CLI実行中にエラー: {str(e)}")
            raise

# Alias for backward compatibility
ClaudeCliExecutor = ClaudeCLIExecutor
