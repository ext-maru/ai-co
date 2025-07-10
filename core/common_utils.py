#!/usr/bin/env python3
"""
Common Utilities - Elders Guild 共通ユーティリティ

プロジェクト全体で使用される共通関数群。
"""

import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from datetime import datetime, timedelta
import subprocess


def get_project_paths() -> Dict[str, Path]:
    """
    プロジェクトの標準パスを取得
    
    Returns:
        パスの辞書
    """
    # プロジェクトルートの検出（coreディレクトリの親）
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    paths = {
        'project': project_root,
        'output': project_root / 'output',
        'logs': project_root / 'logs',
        'config': project_root / 'config',
        'workers': project_root / 'workers',
        'libs': project_root / 'libs',
        'scripts': project_root / 'scripts',
        'web': project_root / 'web',
        'core': project_root / 'core',
        'db': project_root / 'db'
    }
    
    # 必要なディレクトリを作成
    for key in ['output', 'logs', 'db']:
        paths[key].mkdir(parents=True, exist_ok=True)
    
    return paths


def setup_logging(name: str, 
                 log_file: Optional[Path] = None,
                 level: int = logging.INFO,
                 format_string: Optional[str] = None) -> logging.Logger:
    """
    ログ設定のセットアップ
    
    Args:
        name: ロガー名
        log_file: ログファイルパス
        level: ログレベル
        format_string: ログフォーマット
        
    Returns:
        設定されたロガー
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 既存のハンドラーをクリア
    logger.handlers.clear()
    
    # フォーマット設定
    if format_string is None:
        format_string = f'%(asctime)s [{name}] %(levelname)s: %(message)s'
    
    formatter = logging.Formatter(format_string)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラー（指定された場合）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def load_json_file(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    JSONファイルの読み込み
    
    Args:
        file_path: ファイルパス
        
    Returns:
        読み込んだデータ（エラー時はNone）
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"JSONファイル読み込みエラー ({file_path}): {e}")
        return None


def save_json_file(data: Dict[str, Any], 
                  file_path: Union[str, Path],
                  indent: int = 2) -> bool:
    """
    JSONファイルの保存
    
    Args:
        data: 保存するデータ
        file_path: ファイルパス
        indent: インデント幅
        
    Returns:
        成功かどうか
    """
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        logging.error(f"JSONファイル保存エラー ({file_path}): {e}")
        return False


def generate_task_id(prefix: str = "task") -> str:
    """
    タスクIDの生成
    
    Args:
        prefix: IDのプレフィックス
        
    Returns:
        生成されたタスクID
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}"


def generate_hash(content: str, algorithm: str = 'sha256') -> str:
    """
    コンテンツのハッシュ生成
    
    Args:
        content: ハッシュ化する内容
        algorithm: ハッシュアルゴリズム
        
    Returns:
        ハッシュ値
    """
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(content.encode('utf-8'))
    return hash_obj.hexdigest()


def format_filesize(size_bytes: int) -> str:
    """
    ファイルサイズを人間が読みやすい形式に変換
    
    Args:
        size_bytes: バイト単位のサイズ
        
    Returns:
        フォーマットされたサイズ
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_duration(seconds: float) -> str:
    """
    秒数を人間が読みやすい形式に変換
    
    Args:
        seconds: 秒数
        
    Returns:
        フォーマットされた時間
    """
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}時間"
    else:
        days = seconds / 86400
        return f"{days:.1f}日"


def truncate_text(text: str, max_length: int = 100, 
                 suffix: str = "...") -> str:
    """
    テキストを指定長で切り詰め
    
    Args:
        text: 切り詰めるテキスト
        max_length: 最大長
        suffix: 末尾に付ける文字列
        
    Returns:
        切り詰められたテキスト
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def run_command(command: List[str], 
               timeout: Optional[int] = None,
               cwd: Optional[Path] = None) -> Dict[str, Any]:
    """
    外部コマンドの実行
    
    Args:
        command: コマンドリスト
        timeout: タイムアウト秒数
        cwd: 作業ディレクトリ
        
    Returns:
        実行結果の辞書
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        
        return {
            'success': result.returncode == 0,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'command': ' '.join(command)
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'returncode': -1,
            'stdout': '',
            'stderr': f'Command timed out after {timeout} seconds',
            'command': ' '.join(command)
        }
    except Exception as e:
        return {
            'success': False,
            'returncode': -1,
            'stdout': '',
            'stderr': str(e),
            'command': ' '.join(command)
        }


def ensure_list(value: Any) -> List[Any]:
    """
    値をリストに変換（既にリストの場合はそのまま）
    
    Args:
        value: 変換する値
        
    Returns:
        リスト
    """
    if value is None:
        return []
    elif isinstance(value, list):
        return value
    else:
        return [value]


def safe_get(dictionary: Dict[str, Any], 
            key_path: str, 
            default: Any = None) -> Any:
    """
    ネストされた辞書から安全に値を取得
    
    Args:
        dictionary: 辞書
        key_path: キーパス（ドット区切り）
        default: デフォルト値
        
    Returns:
        取得した値またはデフォルト値
    """
    keys = key_path.split('.')
    value = dictionary
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value


def merge_dicts(base: Dict[str, Any], 
               update: Dict[str, Any]) -> Dict[str, Any]:
    """
    辞書の深いマージ
    
    Args:
        base: ベース辞書
        update: 更新する辞書
        
    Returns:
        マージされた辞書
    """
    result = base.copy()
    
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def clean_old_files(directory: Path, 
                   days: int = 7,
                   pattern: str = "*") -> int:
    """
    古いファイルのクリーンアップ
    
    Args:
        directory: 対象ディレクトリ
        days: 保持日数
        pattern: ファイルパターン
        
    Returns:
        削除されたファイル数
    """
    if not directory.exists():
        return 0
    
    cutoff_time = datetime.now() - timedelta(days=days)
    deleted_count = 0
    
    for file_path in directory.glob(pattern):
        if file_path.is_file():
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_time < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    logging.warning(f"ファイル削除失敗: {file_path} - {e}")
    
    return deleted_count


# 便利な定数
ALLOWED_EXTENSIONS = {
    'code': ['.py', '.js', '.html', '.css', '.json', '.yaml', '.yml'],
    'script': ['.sh', '.bash', '.zsh'],
    'config': ['.conf', '.ini', '.env'],
    'document': ['.md', '.txt', '.rst'],
    'data': ['.csv', '.tsv', '.xlsx', '.xls']
}

# エモジ定数（ログで使用）
EMOJI = {
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': '📋',
    'start': '🚀',
    'stop': '🛑',
    'process': '⚙️',
    'wait': '⏳',
    'complete': '🎯',
    'message': '📨',
    'file': '📁',
    'database': '🗄️',
    'network': '🌐',
    'security': '🔒',
    'ai': '🤖',
    'evolution': '🧬',
    'learn': '🧠',
    'mobile': '📱',
    'template': '📝',
    'list': '📋',
    'gear': '⚙️',
    'code': '💻',
    'create': '✨',
    'send': '📤',
    'receive': '📥',
    'party': '🎉',
    'rocket': '🚀',
    'star': '⭐',
    'link': '🔗',
    'monitor': '📊',
    'scaling': '📈',
    'test': '🧪',
    'arrow': '➡️',
    'debug': '🐛',
    'robot': '🤖',
    'image': '🖼️'
}


if __name__ == "__main__":
    # テスト実行
    paths = get_project_paths()
    print("プロジェクトパス:")
    for key, path in paths.items():
        print(f"  {key}: {path}")
    
    # タスクID生成テスト
    task_id = generate_task_id("test")
    print(f"\n生成されたタスクID: {task_id}")
    
    # ハッシュ生成テスト
    content_hash = generate_hash("Hello, Elders Guild!")
    print(f"ハッシュ値: {content_hash}")
