#!/usr/bin/env python3
"""
Elders Guild コマンド基底クラス（CommandResult追加版）
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import subprocess
import pika
import sqlite3
from dataclasses import dataclass

# プロジェクトルートを追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

@dataclass
class CommandResult:
    """コマンド実行結果"""
    success: bool
    message: str = ""
    data: Optional[Dict] = None

class BaseCommand:
    """コマンド基底クラス"""
    
    # カラーコード
    COLORS = {
        'GREEN': '\033[0;32m',
        'YELLOW': '\033[1;33m',
        'RED': '\033[0;31m',
        'BLUE': '\033[0;34m',
        'MAGENTA': '\033[0;35m',
        'CYAN': '\033[0;36m',
        'WHITE': '\033[0;37m',
        'BOLD': '\033[1m',
        'NC': '\033[0m'  # No Color
    }
    
    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        self.name = name
        self.description = description
        self.version = version
        self.project_root = PROJECT_ROOT
        self.config_dir = self.project_root / "config"
        self.logs_dir = self.project_root / "logs"
        self.output_dir = self.project_root / "output"
        self.db_dir = self.project_root / "db"
        
        # 設定ロード
        self.config = self.load_configs()
        
        # パーサー初期化
        self.parser = argparse.ArgumentParser(
            prog=f'ai-{name}',
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # デフォルトで --version オプションを追加
        self.parser.add_argument(
            '--version', '-v',
            action='version',
            version=f'%(prog)s {version}'
        )
        
        self.setup_arguments()
        
    def setup_arguments(self):
        """サブクラスでオーバーライドして引数を定義"""
        pass
        
    def load_configs(self) -> Dict[str, Dict]:
        """設定ファイルをロード"""
        configs = {}
        config_files = {
            'system': 'system.conf',
            'slack': 'slack.conf',
            'github': 'github.conf',
            'database': 'database.conf',
            'scaling': 'scaling.conf'
        }
        
        for name, filename in config_files.items():
            config_path = self.config_dir / filename
            if config_path.exists():
                configs[name] = self._parse_config_file(config_path)
            else:
                configs[name] = {}
                
        return configs
    
    def _parse_config_file(self, path: Path) -> Dict[str, str]:
        """設定ファイルをパース"""
        config = {}
        try:
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"')
        except Exception as e:
            self.error(f"設定ファイル読み込みエラー: {path} - {e}")
        return config
    
    def get_rabbitmq_connection(self):
        """RabbitMQ接続を取得"""
        try:
            return pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        except Exception as e:
            self.error(f"RabbitMQ接続エラー: {e}")
            return None
    
    def get_db_connection(self, db_name: str = "conversations.db"):
        """データベース接続を取得"""
        db_path = self.project_root / db_name
        if not db_path.exists():
            db_path = self.db_dir / db_name
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            self.error(f"データベース接続エラー: {db_path} - {e}")
            return None
    
    def check_process(self, pattern: str) -> List[Dict]:
        """プロセスチェック"""
        try:
            result = subprocess.run(
                ['ps', 'aux'], 
                capture_output=True, 
                text=True
            )
            processes = []
            for line in result.stdout.split('\n'):
                if pattern in line and 'grep' not in line:
                    parts = line.split()
                    if len(parts) >= 11:
                        processes.append({
                            'pid': parts[1],
                            'cpu': parts[2],
                            'mem': parts[3],
                            'cmd': ' '.join(parts[10:])
                        })
            return processes
        except Exception as e:
            self.error(f"プロセスチェックエラー: {e}")
            return []
    
    def run_command(self, cmd: List[str], **kwargs) -> subprocess.CompletedProcess:
        """コマンド実行"""
        try:
            return subprocess.run(cmd, capture_output=True, text=True, **kwargs)
        except Exception as e:
            self.error(f"コマンド実行エラー: {' '.join(cmd)} - {e}")
            return None
    
    # 出力メソッド
    def print(self, message: str, color: str = None, bold: bool = False):
        """カラー出力"""
        if color:
            color_code = self.COLORS.get(color.upper(), '')
        else:
            color_code = ''
        
        if bold:
            color_code += self.COLORS['BOLD']
            
        print(f"{color_code}{message}{self.COLORS['NC']}")
    
    def success(self, message: str):
        """成功メッセージ"""
        self.print(f"✅ {message}", color='green')
    
    def error(self, message: str):
        """エラーメッセージ"""
        self.print(f"❌ {message}", color='red')
    
    def warning(self, message: str):
        """警告メッセージ"""
        self.print(f"⚠️  {message}", color='yellow')
    
    def info(self, message: str):
        """情報メッセージ"""
        self.print(f"ℹ️  {message}", color='blue')
    
    def header(self, title: str, icon: str = "🏢"):
        """ヘッダー表示"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.print(f"\n{icon} {title} - {timestamp}", color='cyan', bold=True)
        self.print("=" * 50, color='cyan')
    
    def section(self, title: str):
        """セクション表示"""
        self.print(f"\n[{title}]", color='yellow', bold=True)
    
    # テーブル表示
    def print_table(self, headers: List[str], rows: List[List[str]], colors: List[str] = None):
        """テーブル表示"""
        # カラム幅計算
        col_widths = []
        for i in range(len(headers)):
            max_width = len(headers[i])
            for row in rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            col_widths.append(max_width + 2)
        
        # ヘッダー表示
        header_line = ""
        for i, header in enumerate(headers):
            header_line += str(header).ljust(col_widths[i])
        self.print(header_line, color='cyan', bold=True)
        self.print("-" * sum(col_widths), color='cyan')
        
        # 行表示
        for row_idx, row in enumerate(rows):
            row_line = ""
            for i, cell in enumerate(row):
                cell_str = str(cell).ljust(col_widths[i] if i < len(col_widths) else 0)
                if colors and row_idx < len(colors):
                    row_line += f"{self.COLORS.get(colors[row_idx].upper(), '')}{cell_str}{self.COLORS['NC']}"
                else:
                    row_line += cell_str
            print(row_line)
    
    def execute(self, args=None) -> Optional[CommandResult]:
        """
        コマンド実行（サブクラスでオーバーライド）
        CommandResult を返すか、直接出力して None を返す
        """
        raise NotImplementedError("サブクラスでexecuteメソッドを実装してください")
    
    def run(self) -> int:
        """メイン実行"""
        try:
            args = self.parser.parse_args()
            result = self.execute(args)
            
            # CommandResult が返された場合の処理
            if isinstance(result, CommandResult):
                if result.message:
                    if result.success:
                        print(result.message)
                    else:
                        self.error(result.message)
                return 0 if result.success else 1
            
            # 何も返されなかった場合は成功とみなす
            return 0
            
        except KeyboardInterrupt:
            self.warning("\n処理を中断しました")
            return 1
        except Exception as e:
            self.error(f"予期しないエラー: {e}")
            import traceback
            traceback.print_exc()
            return 1
