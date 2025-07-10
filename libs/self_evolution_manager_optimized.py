#!/usr/bin/env python3
"""
Elders Guild 自己進化ファイル配置マネージャー (最適化版)
タイムアウト問題を解決するために段階的処理を実装
"""

import os
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
import logging
import shutil
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional
import sqlite3
import math
import time

logger = logging.getLogger(__name__)

class OptimizedSelfEvolutionManager:
    def __init__(self, timeout_seconds=180):
        """
        最適化版の初期化
        Args:
            timeout_seconds: 各処理のタイムアウト秒数（デフォルト3分）
        """
        self.timeout_seconds = timeout_seconds
        self.start_time = None
        
        # プロジェクトルートを相対パスで特定
        self.project_root = Path(__file__).parent.parent
        
        # 配置先マッピング（シンプル版）
        self.placement_rules = {
            # Pythonスクリプト系
            r'.*_worker\.py$': 'workers/',
            r'.*_manager\.py$': 'libs/',
            r'.*_notifier\.py$': 'libs/',
            r'.*_db\.py$': 'libs/',
            r'send_.*\.py$': 'scripts/',
            r'setup_.*\.py$': 'scripts/',
            r'test_.*\.py$': 'tests/',
            
            # 設定ファイル系
            r'.*\.conf$': 'config/',
            r'config\..*': 'config/',
            r'.*\.env$': 'config/',
            
            # シェルスクリプト系
            r'.*\.sh$': 'scripts/',
            
            # Web系
            r'.*\.html$': 'web/',
            r'.*\.css$': 'web/css/',
            r'.*\.js$': 'web/js/',
            
            # ドキュメント系
            r'.*\.md$': 'docs/',
            r'README.*': 'docs/',
            
            # データ系
            r'.*\.json$': 'data/',
            r'.*\.csv$': 'data/',
            r'.*\.sql$': 'data/',
        }
        
        # 内容ベースの簡易ルール
        self.content_based_rules = {
            'import pika': 'workers/',
            'import flask': 'web/',
            'import fastapi': 'api/',
            'class.*Worker': 'workers/',
            'class.*Manager': 'libs/',
            'class.*Notifier': 'libs/',
            'def send_task': 'scripts/',
            '#!/bin/bash': 'scripts/',
        }
        
    def _check_timeout(self):
        """タイムアウトチェック"""
        if self.start_time and (time.time() - self.start_time) > self.timeout_seconds:
            raise TimeoutError(f"Processing exceeded {self.timeout_seconds} seconds")
    
    def auto_place_file_fast(self, source_content, suggested_filename=None, task_id=None):
        """
        高速化されたファイル配置処理
        複雑なML処理を省略し、基本的なルールベースでの配置を実行
        """
        self.start_time = time.time()
        
        try:
            # Step 1: ファイル名決定（シンプル版）
            if suggested_filename:
                filename = suggested_filename
            else:
                filename = self._guess_filename_simple(source_content)
            
            self._check_timeout()
            
            # Step 2: ルールベースでの配置先決定
            target_relative_dir = self._determine_placement_simple(filename, source_content)
            
            self._check_timeout()
            
            # Step 3: ファイル配置実行
            target_dir = self.project_root / Path(target_relative_dir)
            target_file = target_dir / filename
            
            # ディレクトリ作成
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # バックアップ（既存ファイルがある場合）
            backup_info = None
            if target_file.exists():
                backup_info = self._create_simple_backup(target_file)
            
            # ファイル書き込み
            target_file.write_text(source_content, encoding='utf-8')
            
            return {
                'status': 'success',
                'filename': filename,
                'path': str(target_file),
                'relative_path': str(Path(target_relative_dir) / filename),
                'method': 'rule_based_fast',
                'backup': backup_info,
                'processing_time': time.time() - self.start_time
            }
            
        except TimeoutError as e:
            logger.error(f"Timeout error: {e}")
            return {
                'status': 'timeout',
                'error': str(e),
                'processing_time': time.time() - self.start_time
            }
        except Exception as e:
            logger.error(f"Error in auto_place_file_fast: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'processing_time': time.time() - self.start_time
            }
    
    def _guess_filename_simple(self, content: str) -> str:
        """シンプルなファイル名推測"""
        # クラス名から推測
        class_match = re.search(r'class\s+(\w+)', content)
        if class_match:
            class_name = class_match.group(1)
            # CamelCaseをsnake_caseに変換
            filename = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', class_name)
            filename = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', filename)
            return filename.lower() + '.py'
        
        # 関数名から推測
        func_match = re.search(r'def\s+(\w+)', content)
        if func_match:
            return func_match.group(1) + '.py'
        
        # デフォルト
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f'auto_generated_{timestamp}.py'
    
    def _determine_placement_simple(self, filename: str, content: str) -> str:
        """シンプルなルールベース配置決定"""
        # ファイル名ルールチェック
        for pattern, directory in self.placement_rules.items():
            if re.match(pattern, filename):
                return directory
        
        # 内容ベースルールチェック
        for pattern, directory in self.content_based_rules.items():
            if re.search(pattern, content, re.IGNORECASE):
                return directory
        
        # デフォルトはscripts/
        return 'scripts/'
    
    def _create_simple_backup(self, target_file: Path) -> Dict:
        """シンプルなバックアップ作成"""
        backup_dir = self.project_root / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f"{target_file.stem}_{timestamp}{target_file.suffix}"
        
        shutil.copy2(target_file, backup_file)
        
        return {
            'path': str(backup_file),
            'original': str(target_file),
            'timestamp': timestamp
        }
    
    def auto_place_file_chunked(self, source_content, suggested_filename=None, task_id=None, chunk_size=1000):
        """
        チャンク処理によるファイル配置
        大きなファイルでも段階的に処理
        """
        self.start_time = time.time()
        
        try:
            # ファイル名決定
            if suggested_filename:
                filename = suggested_filename
            else:
                # コンテンツの最初の部分だけで判断
                filename = self._guess_filename_simple(source_content[:chunk_size])
            
            # 配置先決定（最初のチャンクで判断）
            target_relative_dir = self._determine_placement_simple(
                filename, 
                source_content[:chunk_size]
            )
            
            # ファイル配置
            target_dir = self.project_root / Path(target_relative_dir)
            target_file = target_dir / filename
            
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # チャンク単位で書き込み
            with open(target_file, 'w', encoding='utf-8') as f:
                for i in range(0, len(source_content), chunk_size):
                    self._check_timeout()
                    chunk = source_content[i:i + chunk_size]
                    f.write(chunk)
            
            return {
                'status': 'success',
                'filename': filename,
                'path': str(target_file),
                'relative_path': str(Path(target_relative_dir) / filename),
                'method': 'chunked_processing',
                'processing_time': time.time() - self.start_time
            }
            
        except Exception as e:
            logger.error(f"Error in auto_place_file_chunked: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'processing_time': time.time() - self.start_time
            }


# オリジナルのマネージャーをラップする形で使用可能
def create_optimized_manager():
    """最適化版マネージャーのファクトリ関数"""
    return OptimizedSelfEvolutionManager()